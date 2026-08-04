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
"""

import argparse
import sys
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
    "Deploy a Type-45 to shadow the vessel and make a public statement.",
    "Convene the North Atlantic Council under Article 4 and hold the deployment.",
    "Authorise defensive patrols only, and instruct the Attorney General to review the legal basis.",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=18,
                        help="hard stop, in case no ending fires")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", default="emergent")
    parser.add_argument("--questions", type=int, default=1,
                        help="questions asked per turn")
    args = parser.parse_args()

    from engine.game_manager import GameManager
    from llm.router import _get_text_driver, _get_provider
    from llm.mock_driver import MockDeterministicDriver

    # The router answers a refused call from the mock driver, and the mock
    # driver returns a perfectly well-formed reply. A campaign can therefore
    # look flawless while no LLM answered any of it. Count the fallbacks so
    # the run cannot claim success it did not earn.
    fallbacks = {"single": 0, "batch": 0}
    real_single = MockDeterministicDriver.generate_text
    real_batch = MockDeterministicDriver.batch_generate_text

    def counted_single(self, prompt, rng, *a, **kw):
        fallbacks["single"] += 1
        return real_single(self, prompt, rng, *a, **kw)

    def counted_batch(self, prompts, rng, *a, **kw):
        fallbacks["batch"] += 1
        return real_batch(self, prompts, rng, *a, **kw)

    MockDeterministicDriver.generate_text = counted_single
    MockDeterministicDriver.batch_generate_text = counted_batch

    print(f"provider: {_get_provider()}")

    gm = GameManager(scenario_id="war_game_2025", play_mode=args.mode,
                     seed=args.seed, mystery_mode=True, endings=True)

    # Which driver actually answers is the thing most worth stating out loud:
    # a refused call falls back to the mock driver and still returns a
    # well-formed answer, so a campaign can look perfect while no LLM ran.
    print(f"driver:   {type(_get_text_driver(None)).__name__}")

    campaign_start = time.time()
    for turn in range(1, args.turns + 1):
        t0 = time.time()
        inject = gm.get_turn_briefing()
        t_brief = time.time() - t0

        for i in range(args.questions):
            gm.process_question(QUESTIONS[(turn + i) % len(QUESTIONS)])
        t_disc = time.time() - t0 - t_brief

        decision = DECISIONS[turn % len(DECISIONS)]
        result = gm.resolve_decision(decision)
        t_total = time.time() - t0

        m = gm.world.metrics
        print(f"T{turn:02d} {t_total:6.1f}s "
              f"(brief {t_brief:5.1f} / disc {t_disc:5.1f} / decide {t_total - t_brief - t_disc:5.1f})  "
              f"risk={m.escalation_risk:3d} stab={m.domestic_stability:3d} "
              f"coh={m.alliance_cohesion:3d}  "
              f"transcript={len(gm.transcript):5d} lines  "
              f"| {str(inject.get('title', '(none)'))[:44]}")

        if result.get("error"):
            print(f"     ADJUDICATION ERROR: {result['error']}")
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
              f"({fallbacks['single']} single, {fallbacks['batch']} batch) - "
              f"this campaign was not adjudicated by an LLM throughout ***")
    else:
        print("no calls fell back to the mock driver")


if __name__ == "__main__":
    main()
