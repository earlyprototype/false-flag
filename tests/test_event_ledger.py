"""Event ledger: resolved threads must not be restaged (issue #25).

The #23 fix taught the inject generator to remember the previous event.
It then began *replaying* it — in live play the same Akula-class submarine
surfaced off Orkney on turns 5, 6 and 8, with turn 7 correctly resolving it
(escorted to the Norwegian Sea on the player's order). "Acknowledge, advance,
or resolve" is satisfiable by restating, and nothing recorded that a thread
was closed.

These tests cover the ledger that records dispositions, the context block
that states them outright, and the prompt rule that forbids restaging.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from engine.narrative_adjudication import infer_event_disposition
from llm.context_builder import (
    MAX_INJECT_CONTINUITY_LINES,
    render_event_ledger,
)
from models.narrative_state import NarrativeState, PlayedEvent
from models.world import Metrics, WorldState
from random import Random


def _state(turn=5):
    return NarrativeState(
        hidden_metrics=Metrics(escalation_risk=60, domestic_stability=40,
                               alliance_cohesion=50),
        turn=turn,
    )


def _world(turn=8):
    return WorldState(
        turn=turn, scene=turn,
        metrics=Metrics(escalation_risk=80, domestic_stability=30,
                        alliance_cohesion=50),
        flags={}, posture={}, narrative=None,
    )


# --- the ledger itself -------------------------------------------------------

def test_record_and_close_an_event():
    ns = _state()
    ns.record_played_event(5, "Akula surfaced off Orkney")
    assert ns.event_ledger[0].disposition == "open"

    ns.close_event(5, "resolved", "escorted to Norwegian Sea")
    assert ns.event_ledger[0].disposition == "resolved"
    assert ns.event_ledger[0].note == "escorted to Norwegian Sea"


def test_recording_the_same_turn_twice_does_not_duplicate():
    """A regenerated inject must leave one entry, not two."""
    ns = _state()
    ns.record_played_event(5, "First attempt")
    ns.record_played_event(5, "Regenerated inject")
    assert len(ns.event_ledger) == 1
    assert ns.event_ledger[0].title == "Regenerated inject"


def test_unknown_disposition_is_ignored_not_coerced():
    ns = _state()
    ns.record_played_event(5, "Akula surfaced off Orkney")
    ns.close_event(5, "sort-of-dealt-with", "hand-wave")
    assert ns.event_ledger[0].disposition == "open"


def test_recent_played_events_is_oldest_first_and_limited():
    ns = _state()
    for turn in range(1, 11):
        ns.record_played_event(turn, f"event {turn}")
    recent = ns.recent_played_events(3)
    assert [e.turn for e in recent] == [8, 9, 10]
    assert ns.recent_played_events(0) == []


def test_the_generator_gets_the_whole_ledger_not_a_window():
    """The default must stay uncapped.

    It used to return the last six, which re-opened the bug the ledger
    exists to close: an event older than the window is invisible to the
    generator and can be restaged as fresh. The ledger is one line per
    event - it is already the compression - so there is nothing to save by
    truncating it.
    """
    ns = _state()
    for turn in range(1, 31):
        ns.record_played_event(turn, f"event {turn}")
        ns.close_event(turn, "resolved", "dealt with")

    everything = ns.recent_played_events()
    assert len(everything) == 30, "the default must not window the ledger"
    assert everything[0].turn == 1, "turn 1 must still be visible at turn 30"

    # And it must stay affordable, which is the whole reason it can be whole.
    block = render_event_ledger(everything)
    assert len(block) < 4000, f"30 turns of ledger should be tiny, got {len(block)} chars"


def test_ledger_round_trips_and_old_saves_load_clean():
    ns = _state()
    ns.record_played_event(5, "Akula surfaced off Orkney")
    ns.close_event(5, "resolved", "escorted out")

    payload = ns.model_dump()
    assert NarrativeState(**payload).event_ledger[0].disposition == "resolved"

    # A save written before this feature has no ledger key at all
    payload.pop("event_ledger")
    assert NarrativeState(**payload).event_ledger == []


def test_consequence_fields_round_trip_and_old_saves_load_clean():
    """ER-077: outcome/effects_direction/objectors survive a save cycle, and
    a ledger entry written before they existed loads with empty defaults."""
    ns = _state()
    ns.record_played_event(5, "Akula surfaced off Orkney")
    ns.close_event(5, "resolved", "escorted out")
    ns.record_event_consequences(
        5, outcome="A measured escort that held the line.",
        effects_direction={"escalation_risk": "down",
                           "alliance_cohesion": "up"},
        objectors=["Chief of the Defence Staff"])

    payload = ns.model_dump()
    loaded = NarrativeState(**payload).event_ledger[0]
    assert loaded.outcome == "A measured escort that held the line."
    assert loaded.effects_direction == {"escalation_risk": "down",
                                        "alliance_cohesion": "up"}
    assert loaded.objectors == ["Chief of the Defence Staff"]

    # An entry from a pre-ER-077 save carries none of the fields.
    old_entry = {"turn": 3, "title": "Cable cut", "disposition": "open",
                 "note": ""}
    payload["event_ledger"] = [old_entry]
    entry = NarrativeState(**payload).event_ledger[0]
    assert entry.outcome == ""
    assert entry.effects_direction == {}
    assert entry.objectors == []


# --- disposition inference ---------------------------------------------------

def test_closure_language_resolves_only_the_matching_event():
    title = "Akula-class submarine surfaces off Orkney"
    escort = "The Royal Navy escorts the Akula submarine out of UK waters."
    assert infer_event_disposition(title, escort) == "resolved"

    # Engaged but not closed
    hail = "Northwood signals the submarine on the distress frequency."
    assert infer_event_disposition(title, hail) == "advanced"

    # A decision about something else must not touch this thread
    unrelated = "We publish the interim finding at midday to all four capitals."
    assert infer_event_disposition(title, unrelated) == "open"


def test_inference_defaults_open_when_it_cannot_tell():
    """A false 'resolved' silently suppresses a live thread — worse than
    the repetition this ledger exists to prevent."""
    assert infer_event_disposition("", "escort everything out") == "open"
    assert infer_event_disposition("Some event", "") == "open"


# --- rendering ---------------------------------------------------------------

def test_ledger_block_states_dispositions():
    block = render_event_ledger([
        PlayedEvent(turn=5, title="Akula surfaced off Orkney",
                    disposition="resolved", note="escorted to Norwegian Sea"),
        PlayedEvent(turn=6, title="Drax substation sabotage",
                    disposition="open", note="forensics pending"),
    ])
    assert "EVENTS ALREADY PLAYED - do not re-introduce these" in block
    assert "Turn 5 | Akula surfaced off Orkney | RESOLVED - escorted to Norwegian Sea" in block
    assert "OPEN - forensics pending" in block


def test_empty_or_absent_ledger_renders_nothing():
    assert render_event_ledger(None) == ""
    assert render_event_ledger([]) == ""


def test_always_renders_a_placeholder_over_an_empty_ledger():
    """ER-001: the generation prompt's rule 8 names this block
    unconditionally, so the generation path renders it even when empty."""
    for empty in (None, []):
        block = render_event_ledger(empty, always=True)
        assert "EVENTS ALREADY PLAYED - do not re-introduce these" in block
        assert "(nothing has been staged yet)" in block


def test_long_titles_are_truncated_not_left_to_stretch_the_column():
    block = render_event_ledger([
        PlayedEvent(turn=1, title="A" * 200, disposition="open"),
        PlayedEvent(turn=2, title="short", disposition="open"),
    ])
    assert "..." in block
    assert max(len(line) for line in block.splitlines()) < 110


def test_dicts_work_as_well_as_played_events():
    """The renderer is duck-typed so callers aren't forced to import models."""
    block = render_event_ledger([
        {"turn": 3, "title": "Cable cut", "disposition": "advanced",
         "note": "survey vessel tasked"},
    ])
    assert "Turn 3 | Cable cut | ADVANCED - survey vessel tasked" in block


def test_ledger_block_renders_consequences_compactly():
    """ER-077: an adjudicated entry carries one extra indented line with the
    outcome sentence, the effect directions and the objectors; an entry
    without them renders exactly as before."""
    block = render_event_ledger([
        PlayedEvent(turn=5, title="Akula surfaced off Orkney",
                    disposition="resolved", note="escorted to Norwegian Sea",
                    outcome="A firm but measured escort.",
                    effects_direction={"escalation_risk": "down",
                                       "domestic_stability": "steady"},
                    objectors=["Foreign Secretary", "Attorney General"]),
        PlayedEvent(turn=6, title="Drax substation sabotage",
                    disposition="open", note="forensics pending"),
    ])
    assert ("outcome: A firm but measured escort.; "
            "effects: risk down, stability steady; "
            "objectors: Foreign Secretary, Attorney General") in block
    # The unadjudicated entry stays a single line with nothing under it.
    lines = block.splitlines()
    turn6 = next(i for i, l in enumerate(lines) if "Drax substation" in l)
    assert turn6 == len(lines) - 1
    # The dict duck-typing survives fields the dict does not carry.
    assert "Cable cut" in render_event_ledger(
        [{"turn": 3, "title": "Cable cut", "disposition": "open"}])


# --- the prompt --------------------------------------------------------------

def _prompt_with(ledger, monkeypatch, turn=8):
    import llm.context_builder as cb
    monkeypatch.setattr(cb, "generate_summary", lambda t, p: "summary stub")
    from llm.prompts import build_inject_generation_prompt
    transcript = ["", "=" * 60, "TURN 7", "=" * 60, ""] + [
        f"line {i}" for i in range(60)]
    return build_inject_generation_prompt(
        _world(turn), turn, {}, None, transcript, event_ledger=ledger)


def test_resolved_event_reaches_the_prompt_with_a_do_not_restage_rule(monkeypatch):
    """The exact Campaign IV failure: turn 7 resolved the submarine, so the
    turn 8 prompt must carry that fact and the instruction not to restage."""
    prompt = _prompt_with([
        PlayedEvent(turn=7, title="Akula-class submarine off Orkney",
                    disposition="resolved", note="escorted to Norwegian Sea"),
    ], monkeypatch)

    assert "EVENTS ALREADY PLAYED" in prompt
    assert "RESOLVED - escorted to Norwegian Sea" in prompt
    assert "DO NOT RESTAGE RESOLVED EVENTS" in prompt
    # #23's rule must survive alongside it
    assert "CONTINUITY IS MANDATORY" in prompt


def test_prompt_without_a_ledger_keeps_rule_8_and_an_empty_block(monkeypatch):
    """ER-001: an empty ledger used to remove rule 8 and the block it names
    together. Now the generation path always carries both — the block just
    says nothing has been staged yet."""
    prompt = _prompt_with(None, monkeypatch)
    assert "EVENTS ALREADY PLAYED" in prompt
    assert "(nothing has been staged yet)" in prompt
    assert "DO NOT RESTAGE RESOLVED EVENTS" in prompt
    assert "CONTINUITY IS MANDATORY" in prompt


def test_generator_window_is_widened_beyond_the_advisor_starvation_default():
    """The generator ran on 120 lines while advisors got 500 — it is the
    component most responsible for continuity (issue #25)."""
    from llm.context_builder import MAX_ADVISOR_TRANSCRIPT_CHARS
    assert MAX_INJECT_CONTINUITY_LINES == 400
    assert MAX_INJECT_CONTINUITY_LINES > 120
    # Still bounded, and still no wider than what the advisors carry. The
    # old form of this assertion multiplied the line cap by a campaign's
    # *average* line length, which proves nothing: lines run from empty to a
    # full unwrapped paragraph. Measured against a turn of long lines the
    # line cap alone returned 792,572 characters against a 320,000 budget.
    # So exercise the real slicer on the worst shape and assert the bound.
    from llm.context_builder import get_last_turn_slice
    fat = ["=" * 60, "TURN 1", "=" * 60] + ["X" * 2000] * 5000
    block = get_last_turn_slice(fat, max_lines=MAX_INJECT_CONTINUITY_LINES)
    assert len("\n".join(block)) <= MAX_ADVISOR_TRANSCRIPT_CHARS

    # The branch that does NOT elide is the one that got this wrong first
    # time: a turn inside the line cap skipped the character budget entirely
    # and returned 796,465 characters. Every return path is bounded now.
    within_cap = ["=" * 60, "TURN 1"] + ["X" * 2000] * 398
    block = get_last_turn_slice(within_cap, max_lines=MAX_INJECT_CONTINUITY_LINES)
    assert len("\n".join(block)) <= MAX_ADVISOR_TRANSCRIPT_CHARS

    # And the path with no TURN header at all.
    headerless = ["X" * 2000] * 1000
    block = get_last_turn_slice(headerless, max_lines=MAX_INJECT_CONTINUITY_LINES)
    assert len("\n".join(block)) <= MAX_ADVISOR_TRANSCRIPT_CHARS

    # And the ordinary shape still comes back whole, not trimmed.
    lean = ["=" * 60, "TURN 7", "=" * 60] + [f"line {i}" for i in range(40)]
    assert get_last_turn_slice(lean, max_lines=MAX_INJECT_CONTINUITY_LINES) == lean


def test_widened_window_is_actually_used(monkeypatch):
    import llm.context_builder as cb
    monkeypatch.setattr(cb, "generate_summary", lambda t, p: "stub")

    seen = {}
    real_slice = cb.get_last_turn_slice

    def spy(transcript, max_lines=120):
        seen["max_lines"] = max_lines
        return real_slice(transcript, max_lines)

    monkeypatch.setattr(cb, "get_last_turn_slice", spy)
    from llm.prompts import build_inject_generation_prompt
    transcript = ["", "=" * 60, "TURN 7", "=" * 60, ""] + [
        f"line {i}" for i in range(500)]
    build_inject_generation_prompt(_world(), 8, {}, None, transcript)
    assert seen["max_lines"] == MAX_INJECT_CONTINUITY_LINES


# --- scenario pool ------------------------------------------------------------

def test_used_scenarios_drop_out_of_the_inspiration_pool():
    """Re-offering the same naval set-piece every turn is part of why one
    kept coming back (issue #25)."""
    from llm.prompts import _drop_used_scenarios

    pool = ["submarine_incursion", "cable_cutting", "airspace_violation"]
    ledger = [PlayedEvent(turn=5, title="Akula submarine surfaces off Orkney")]
    remaining = _drop_used_scenarios(pool, ledger)
    assert "submarine_incursion" not in remaining
    assert "cable_cutting" in remaining


def test_scenario_pool_is_never_emptied():
    """Handing the generator nothing to work from is worse than repetition."""
    from llm.prompts import _drop_used_scenarios

    pool = ["submarine_incursion"]
    ledger = [PlayedEvent(turn=5, title="Submarine incursion off Orkney")]
    assert _drop_used_scenarios(pool, ledger) == pool


def test_scenario_library_path_executes(monkeypatch):
    """Covers the branch that builds library_context — it calls into
    _drop_used_scenarios, so an import error there would only surface here."""
    import llm.context_builder as cb
    monkeypatch.setattr(cb, "generate_summary", lambda t, p: "stub")
    from llm.prompts import build_inject_generation_prompt

    library = {
        "escalation_patterns": {"russian_strategy": {}, "uk_constraints": {}},
        "naval_scenarios": ["submarine_incursion", "carrier_shadowing"],
        "infrastructure_scenarios": ["cable_cutting"],
        "diplomatic_scenarios": ["ambassador_expulsion"],
    }
    transcript = ["", "=" * 60, "TURN 7", "=" * 60, "", "an event happened"]
    prompt = build_inject_generation_prompt(
        _world(), 8, {}, library, transcript,
        event_ledger=[PlayedEvent(turn=7, title="Submarine incursion",
                                  disposition="resolved")])
    assert "Potential scenarios:" in prompt
    assert "submarine_incursion" not in prompt.split("Potential scenarios:")[1][:200]
    assert "carrier_shadowing" in prompt


# --- disposition recording reaches every adjudication path -------------------

def test_disposition_closes_the_most_recently_staged_event():
    """Not a turn-keyed lookup: narrative_state.turn is synced to the world
    turn only *after* adjudication, so keying on it finds the previous
    turn's event and leaves the current one permanently open."""
    from engine.narrative_adjudication import record_event_disposition

    ns = _state(turn=1)          # still lagging: world is on turn 2
    ns.record_played_event(1, "Severomorsk accusation")
    ns.record_played_event(2, "Akula submarine surfaces off Orkney")

    record_event_disposition(
        ns, "The Royal Navy escorts the Akula submarine out of UK waters.")

    assert ns.event_ledger[1].disposition == "resolved"   # turn 2, the live one
    assert ns.event_ledger[0].disposition == "open"       # turn 1 untouched


def test_actor_simulation_path_also_records_disposition(monkeypatch):
    """Campaigns with an actor system route through
    adjudicate_with_actor_simulation — recording only in the narrative path
    left the ledger permanently open in real play."""
    import engine.narrative_adjudication as na

    seen = []
    monkeypatch.setattr(na, "record_event_disposition",
                        lambda ns, action, **kwargs: seen.append(action))
    # Keep the rest of the pipeline cheap and offline
    monkeypatch.setattr(na, "identify_relevant_actors", lambda *a, **k: [])
    monkeypatch.setattr(na, "calculate_effects_from_responses", lambda *a, **k: {})
    monkeypatch.setattr(na, "generate_character_responses", lambda *a, **k: [])

    from models.state_actors import StateActorSystem
    ns = _state()
    ns.record_played_event(1, "Akula surfaced off Orkney")

    llm_calls = []

    def fake_llm(*args, **kwargs):
        llm_calls.append(args)
        return "QUALITY: good\n\nREASONING: fine.\n"

    # rng before llm_generate_fn — passing them swapped still satisfies the
    # assertion below, but silently routes quality assessment through the
    # heuristic fallback instead of the LLM path this test means to cover.
    na.adjudicate_with_actor_simulation(
        ns, StateActorSystem(), "escort the submarine out", "interp",
        Random(1), fake_llm)

    assert llm_calls, "quality assessment must reach the LLM path, not the fallback"
    assert seen, "actor path must record the event disposition"


def test_adjudication_writes_consequences_and_the_next_quality_prompt_sees_them():
    """ER-077 end to end: a mock adjudicated turn writes outcome,
    effects_direction and objectors into the ledger entry, and the next
    turn's quality-assessment prompt carries them."""
    from engine.narrative_adjudication import (
        adjudicate_with_narrative,
        assess_action_quality,
    )

    ns = _state(turn=1)
    ns.record_played_event(1, "Akula submarine surfaces off Orkney")

    def fake_llm(prompt, rng, **kwargs):
        return ("QUALITY: good\n\n"
                "REASONING: Escorting the submarine out was firm without "
                "being escalatory. It also reassured the allies watching.\n\n"
                "EFFECTS:\n"
                "escalation_risk: -5\n"
                "alliance_cohesion: +3\n"
                "domestic_stability: 0\n\n"
                "QUALITY MULTIPLIER: 1.5\n")

    adjudicate_with_narrative(
        ns, "The Royal Navy escorts the Akula submarine out of UK waters.",
        "interp", Random(1), llm_generate_fn=fake_llm,
        pushback=[("Foreign Secretary", "This risks a confrontation at sea."),
                  ("Attorney General", "Check the legal basis first.")])

    entry = ns.event_ledger[0]
    assert entry.disposition == "resolved"
    # First sentence of the parsed reasoning, plain text.
    assert entry.outcome == ("Escorting the submarine out was firm without "
                             "being escalatory.")
    # Directions of the APPLIED final effects, never numbers.
    assert entry.effects_direction == {"escalation_risk": "down",
                                       "alliance_cohesion": "up",
                                       "domestic_stability": "steady"}
    assert entry.objectors == ["Foreign Secretary", "Attorney General"]

    # And the next turn's quality prompt renders them.
    prompts = []

    def capture_llm(prompt, rng, **kwargs):
        prompts.append(prompt)
        return ("QUALITY: adequate\n\nREASONING: Fine.\n\n"
                "EFFECTS:\nescalation_risk: 0\n")

    assess_action_quality("Hold current posture.", ns, "interp",
                          capture_llm, None, Random(2))
    quality_prompt = prompts[0]
    assert "outcome: Escorting the submarine out was firm" in quality_prompt
    assert "risk down" in quality_prompt
    assert "cohesion up" in quality_prompt
    assert "objectors: Foreign Secretary, Attorney General" in quality_prompt


def test_ledger_renders_even_without_a_transcript(monkeypatch):
    """Rule 8 names the EVENTS ALREADY PLAYED block, so that block must
    exist whenever the rule is issued."""
    import llm.context_builder as cb
    monkeypatch.setattr(cb, "generate_summary", lambda t, p: "stub")
    from llm.prompts import build_inject_generation_prompt

    prompt = build_inject_generation_prompt(
        _world(), 8, {}, None, None,
        event_ledger=[PlayedEvent(turn=7, title="Akula off Orkney",
                                  disposition="resolved", note="escorted out")])
    assert "EVENTS ALREADY PLAYED" in prompt
    assert "DO NOT RESTAGE RESOLVED EVENTS" in prompt
