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


def test_ledger_round_trips_and_old_saves_load_clean():
    ns = _state()
    ns.record_played_event(5, "Akula surfaced off Orkney")
    ns.close_event(5, "resolved", "escorted out")

    payload = ns.model_dump()
    assert NarrativeState(**payload).event_ledger[0].disposition == "resolved"

    # A save written before this feature has no ledger key at all
    payload.pop("event_ledger")
    assert NarrativeState(**payload).event_ledger == []


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


def test_prompt_without_a_ledger_is_unchanged(monkeypatch):
    prompt = _prompt_with(None, monkeypatch)
    assert "EVENTS ALREADY PLAYED" not in prompt
    assert "CONTINUITY IS MANDATORY" in prompt


def test_generator_window_is_widened_beyond_the_advisor_starvation_default():
    """The generator ran on 120 lines while advisors got 500 — it is the
    component most responsible for continuity (issue #25)."""
    from llm.context_builder import MAX_ADVISOR_TRANSCRIPT_LINES
    assert MAX_INJECT_CONTINUITY_LINES == 400
    assert MAX_INJECT_CONTINUITY_LINES > 120
    # Still bounded: full transcripts exceed the play models' context window
    assert MAX_INJECT_CONTINUITY_LINES <= MAX_ADVISOR_TRANSCRIPT_LINES


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
