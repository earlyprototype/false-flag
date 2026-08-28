"""Play a full campaign headless, and report what the engine actually did.

The point is to watch a campaign rather than read one. It drives the real
``GameManager`` through every turn to a terminal ending, asking a question and
committing a decision each turn, and prints a per-turn account: which driver
answered, how many LLM calls the turn made, how long it took, and what the
metrics did.

Run it against ``dev-scripts/fake_openrouter.py`` to get call-level numbers,
or against ``WARGAME_LLM=mock`` to exercise the engine alone.

Usage:
    WARGAME_LLM=openai_compat \\
    OPENAI_COMPAT_BASE_URL=http://127.0.0.1:8099/v1 \\
    OPENAI_COMPAT_MODEL=fake OPENAI_COMPAT_API_KEY=x \\
    python3 dev-scripts/play_campaign.py --turns 18

With WARGAME_CALL_LOG set, a sibling state file (<log>.state.jsonl) records
advisor trust/relationship, actor relationships and world metrics after every
adjudicated turn, and each decision is previewed via interpret_decision before
being committed unamended - so dev-scripts/analyse_call_log.py can verify
attitude drift (ER-007) and the pushback-override trust cost (ER-013).

``--replay-check`` runs two same-seed 5-turn mock campaigns (one save/resumed
at turn 3) and exits non-zero if they diverge (ER-037/025).
"""

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

QUESTIONS = [
    "What is the current threat assessment?",
    "Where does NATO stand on this?",
    "What are the legal constraints on a response?",
    "How exposed is domestic infrastructure?",
    "What do the forces need from me?",
]

DECISIONS = [
    "Raise readiness across home commands and brief the Cabinet in full.",
    "Open a direct diplomatic channel to Moscow and inform NATO allies first.",
    # Deliberately deploys the carrier: a decision known to draw cabinet
    # pushback, so committing it unamended exercises the ER-013 trust cost
    # in every run (the mock driver's pushback trigger keys on it too).
    "Deploy the carrier strike group to shadow the vessel and make a public statement.",
    "Convene the North Atlantic Council under Article 4 and hold the deployment.",
    "Authorise defensive patrols only, and instruct the Attorney General to review the legal basis.",
]


def _state_dump_path() -> str:
    """The state file lives beside the call log: <WARGAME_CALL_LOG>.state.jsonl."""
    return os.environ["WARGAME_CALL_LOG"] + ".state.jsonl"


def _snapshot_state(gm, turn, pushback_roles=None):
    """One JSON-able line of observable engine state.

    Written after each adjudicated turn (plus a turn-0 baseline) so the
    analyzer can verify attitudes actually drift over a campaign (ER-007)
    and that committing text that drew pushback, unamended, cost the
    objectors trust that same turn (ER-013).
    """
    advisors = {}
    for char_id, char in gm.narrative_state.characters.items():
        # Both shapes survive save/load round-trips (see
        # GameManager.get_advisors_state): a live session holds pydantic
        # CharacterAttitude models, an old payload may hold plain dicts.
        if isinstance(char, dict):
            advisors[char_id] = {
                "name": char.get("name", char_id),
                "trust": char.get("trust", 50),
                "relationship": char.get("relationship", "professional"),
            }
        else:
            advisors[char_id] = {
                "name": getattr(char, "name", char_id),
                "trust": getattr(char, "trust", 50),
                "relationship": getattr(char, "relationship", "professional"),
            }
    actors = {}
    if gm.world.actor_system is not None:
        actors = {code: actor.relationship_uk
                  for code, actor in gm.world.actor_system.actors.items()}
    entry = {
        "turn": turn,
        "advisors": advisors,
        "actors": actors,
        "metrics": gm.world.metrics.dict(),
        # Real phase transitions observed this turn (engine _trace_phase);
        # feeds the interop phase_changed telemetry stream.
        "phases": [p for (t, p) in getattr(gm, "_phase_trace", []) if t == turn],
    }
    if pushback_roles is not None:
        entry["pushback_roles"] = pushback_roles
        # Who actually paid the ER-013 cost this commit: read directly off
        # the manager, because the same turn's attitude drift can mask a -1
        # in the net trust numbers (seen in the first verification run).
        entry["pushback_costs"] = list(getattr(gm, "_last_pushback_costs", []))
    return entry


def _dump_state(gm, turn, pushback_roles=None):
    """Append one state line beside the call log. No-op unless logging."""
    with open(_state_dump_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(_snapshot_state(gm, turn, pushback_roles),
                           ensure_ascii=False) + "\n")


def replay_check(turns=5, seed=42, mode="emergent"):
    """Same-seed replay determinism probe (ER-037/025). Mock driver, free.

    Runs two campaigns with the same seed: one uninterrupted, one saved via
    to_dict() at the end of turn 3 and resumed via from_dict(). Under the
    deterministic mock driver the rng-driven surface must match exactly -
    world metrics and inject titles per turn, and the full transcript.
    Returns the number of mismatches (0 = deterministic).
    """
    os.environ["WARGAME_LLM"] = "mock"
    # Two interleaved campaigns would shred a call log and its state file;
    # this mode is a pure determinism probe, so logging is off.
    os.environ.pop("WARGAME_CALL_LOG", None)

    from engine.game_manager import GameManager

    def play(gm, first_turn, last_turn, record):
        """Drive turns [first_turn..last_turn]; same shape as the live loop."""
        for turn in range(first_turn, last_turn + 1):
            inject = gm.get_turn_briefing()
            while gm.active_encounter is not None and gm.active_encounter.active:
                gm.process_diplomacy(
                    "We are coordinating fully with NATO and will share our "
                    "deployment plan within the hour."
                )
            gm.process_question(QUESTIONS[turn % len(QUESTIONS)])
            decision = DECISIONS[turn % len(DECISIONS)]
            gm.interpret_decision(decision)
            gm.resolve_decision(decision)
            record.append({
                "turn": turn,
                "title": str(inject.get("title", "(none)")),
                "metrics": gm.world.metrics.dict(),
            })
        return gm

    print(f"replay-check: {turns} mock turns, seed {seed}, "
          f"save/resume at end of turn 3")

    # Run A: uninterrupted.
    run_a = []
    gm_a = GameManager(scenario_id="war_game_2025", play_mode=mode,
                       seed=seed, mystery_mode=True, endings=True)
    gm_a = play(gm_a, 1, turns, run_a)

    # Run B: same seed, saved at end of turn 3, resumed from the payload.
    run_b = []
    gm_b = GameManager(scenario_id="war_game_2025", play_mode=mode,
                       seed=seed, mystery_mode=True, endings=True)
    gm_b = play(gm_b, 1, 3, run_b)
    payload = json.loads(json.dumps(gm_b.to_dict(), default=str))
    gm_b = GameManager.from_dict(payload)
    gm_b = play(gm_b, 4, turns, run_b)

    mismatches = 0

    # Per-turn rng-driven surface: metrics and inject titles.
    for rec_a, rec_b in zip(run_a, run_b):
        turn = rec_a["turn"]
        if rec_a["title"] != rec_b["title"]:
            mismatches += 1
            print(f"  MISMATCH turn {turn} inject title:\n"
                  f"    uninterrupted: {rec_a['title']}\n"
                  f"    resumed:       {rec_b['title']}")
        if rec_a["metrics"] != rec_b["metrics"]:
            mismatches += 1
            diffs = {k: (rec_a["metrics"][k], rec_b["metrics"].get(k))
                     for k in rec_a["metrics"]
                     if rec_a["metrics"][k] != rec_b["metrics"].get(k)}
            print(f"  MISMATCH turn {turn} metrics (uninterrupted vs resumed): {diffs}")
    if len(run_a) != len(run_b):
        mismatches += 1
        print(f"  MISMATCH turn count: {len(run_a)} vs {len(run_b)}")

    # Model text is deterministic under the mock driver, so the transcripts
    # must be identical line for line - assert it, and say where they part.
    ta, tb = gm_a.transcript, gm_b.transcript
    if ta != tb:
        mismatches += 1
        print(f"  MISMATCH transcript: {len(ta)} vs {len(tb)} lines")
        for i, (la, lb) in enumerate(zip(ta, tb)):
            if la != lb:
                print(f"    first divergence at line {i}:\n"
                      f"      uninterrupted: {la!r}\n"
                      f"      resumed:       {lb!r}")
                break
        else:
            i = min(len(ta), len(tb))
            longer = ta if len(ta) > len(tb) else tb
            which = "uninterrupted" if len(ta) > len(tb) else "resumed"
            print(f"    transcripts identical up to line {i}; "
                  f"{which} run continues: {longer[i]!r}")
    else:
        print(f"  transcripts identical: {len(ta)} lines")

    if mismatches:
        print(f"replay-check: FAIL - {mismatches} divergence(s) between the "
              "uninterrupted and the save/resumed campaign (ER-037/025)")
    else:
        print("replay-check: PASS - save/resume replayed the identical "
              f"campaign over {turns} turns (metrics, inject titles, "
              "full transcript) (ER-037/025)")
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=18,
                        help="hard stop, in case no ending fires")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", default="emergent")
    parser.add_argument("--questions", type=int, default=1,
                        help="questions asked per turn")
    parser.add_argument("--replay-check", action="store_true",
                        help="run two same-seed 5-turn mock campaigns (one "
                             "save/resumed at turn 3) and exit non-zero if "
                             "they diverge (ER-037/025)")
    args = parser.parse_args()

    if args.replay_check:
        sys.exit(1 if replay_check(turns=5, seed=args.seed, mode=args.mode)
                 else 0)

    from engine.game_manager import GameManager
    from llm.router import _get_text_driver, _get_provider
    from llm.mock_driver import MockDeterministicDriver
    from llm import parse_health

    parse_health.reset()

    # The router answers a refused call from the mock driver, and the mock
    # driver returns a perfectly well-formed reply. A campaign can therefore
    # look flawless while no LLM answered any of it. Count the fallbacks so
    # the run cannot claim success it did not earn.
    fallbacks = {"single": 0, "batch": 0}
    _ctx = threading.local()  # the pool means this must be per-thread
    real_single = MockDeterministicDriver.generate_text
    real_batch = MockDeterministicDriver.batch_generate_text

    def counted_single(self, prompt, rng, *a, **kw):
        # The mock's batch_generate_text loops over generate_text, so without
        # this a batch of N would score N+1 - neither a count of batch calls
        # nor of logical prompts. Count prompts, once each.
        if not getattr(_ctx, "in_batch", False):
            fallbacks["single"] += 1
        return real_single(self, prompt, rng, *a, **kw)

    def counted_batch(self, prompts, rng, *a, **kw):
        fallbacks["batch"] += len(prompts)
        was = getattr(_ctx, "in_batch", False)
        _ctx.in_batch = True
        try:
            return real_batch(self, prompts, rng, *a, **kw)
        finally:
            _ctx.in_batch = was

    MockDeterministicDriver.generate_text = counted_single
    MockDeterministicDriver.batch_generate_text = counted_batch

    print(f"provider: {_get_provider()}")

    gm = GameManager(scenario_id="war_game_2025", play_mode=args.mode,
                     seed=args.seed, mystery_mode=True, endings=True)

    # Which driver actually answers is the thing most worth stating out loud:
    # a refused call falls back to the mock driver and still returns a
    # well-formed answer, so a campaign can look perfect while no LLM ran.
    print(f"driver:   {type(_get_text_driver(None)).__name__}")

    from engine.game_manager import GameManager as _GM
    from llm import call_log

    def _roundtrip(gm, label):
        """Live save/load probe: the campaign continues on the restored copy."""
        payload = json.loads(json.dumps(gm.to_dict(), default=str))
        restored = _GM.from_dict(payload)
        print(f"     [probe] {label}: session round-tripped through "
              f"to_dict/from_dict; call live={bool(restored.active_encounter and restored.active_encounter.active)}")
        return restored

    if call_log.enabled():
        # Turn-0 baseline, so the first turn's drift (and a first-turn
        # ER-013 trust cost) is measurable against the seeded attitudes.
        _dump_state(gm, 0)

    campaign_start = time.time()
    for turn in range(1, args.turns + 1):
        call_log.set_field("turn", turn)
        t0 = time.time()
        inject = gm.get_turn_briefing()
        # A scripted mandatory call is left live for the player rather than
        # answered in their name (ER-033). Play it the way a front end would:
        # through process_diplomacy, until the exchange cap or a closer ends it.
        probed_call = False
        while gm.active_encounter is not None and gm.active_encounter.active:
            gm.process_diplomacy(
                "We are coordinating fully with NATO and will share our "
                "deployment plan within the hour."
            )
            if (call_log.enabled() and not probed_call
                    and gm.active_encounter is not None
                    and gm.active_encounter.active):
                # ER-047/ER-056 live evidence: save mid-call, resume, finish
                gm = _roundtrip(gm, "mid-call")
                probed_call = True
        t_brief = time.time() - t0

        for i in range(args.questions):
            gm.process_question(QUESTIONS[(turn + i) % len(QUESTIONS)])
        t_disc = time.time() - t0 - t_brief

        decision = DECISIONS[turn % len(DECISIONS)]
        # Preview first, then commit the identical text: interpret_decision
        # arms _pending_pushback, so an unamended commit that drew objections
        # exercises the ER-013 trust cost live. Since ER-074 the commit also
        # REUSES the preview's advisory results, so a preview-then-commit
        # turn makes ONE interpretation call, ONE pushback call and ONE
        # omissions batch - not two of each; expect the per-turn call count
        # (and the decision-family rows in analyse_call_log.py) to reflect
        # the single run.
        interp = gm.interpret_decision(decision)
        pushback_roles = [p["role"] for p in interp.get("pushback", [])]
        if pushback_roles:
            print(f"     [pushback] interpretation drew pushback from "
                  f"{', '.join(pushback_roles)}; committing unamended (ER-013)")
        result = gm.resolve_decision(decision)
        t_total = time.time() - t0

        if call_log.enabled():
            _dump_state(gm, turn, pushback_roles)

        m = gm.world.metrics
        print(f"T{turn:02d} {t_total:6.1f}s "
              f"(brief {t_brief:5.1f} / disc {t_disc:5.1f} / decide {t_total - t_brief - t_disc:5.1f})  "
              f"risk={m.escalation_risk:3d} stab={m.domestic_stability:3d} "
              f"coh={m.alliance_cohesion:3d}  "
              f"transcript={len(gm.transcript):5d} lines  "
              f"| {str(inject.get('title', '(none)'))[:44]}")

        if result.get("error"):
            print(f"     ADJUDICATION ERROR: {result['error']}")
        if call_log.enabled() and turn == 9:
            # Start-of-turn save (the ER-056 window, now closed): resume and
            # play the back half of the campaign on the restored session
            gm = _roundtrip(gm, "start-of-turn-10")
        if result.get("ending"):
            print(f"\nENDING on turn {turn}: {result['ending']['title']} "
                  f"({result['ending']['verdict']})")
            break
    else:
        print(f"\nno ending fired within {args.turns} turns")

    print(f"campaign wall clock: {time.time() - campaign_start:.1f}s")
    print(f"final transcript: {len(gm.transcript)} lines, "
          f"{sum(len(line) for line in gm.transcript)} chars")

    provider = _get_provider()
    total = fallbacks["single"] + fallbacks["batch"]
    if provider in ("mock", "offline"):
        print(f"mock driver answered {total} calls (expected: it is the provider)")
    elif total:
        print(f"*** {total} calls FELL BACK to the mock driver "
              f"({fallbacks['single']} single, {fallbacks['batch']} batched prompts) - "
              f"this campaign was not adjudicated by an LLM throughout ***")
    else:
        print("no calls fell back to the mock driver")

    # Parse health: how much of what the player saw was the model's answer
    # rather than a tolerant parser's default.
    health = parse_health.snapshot()
    miss_count = sum(health["misses"].values())
    if miss_count:
        detail = ", ".join(f"{k} x{v}" for k, v in health["misses"].items())
        print(f"parse health: {miss_count} misses ({detail})")
    else:
        print("parse health: 0 misses")
    if health["fallbacks"]:
        detail = ", ".join(f"{k} x{v}" for k, v in health["fallbacks"].items())
        print(f"parse health: fallbacks recorded ({detail})")


if __name__ == "__main__":
    main()
