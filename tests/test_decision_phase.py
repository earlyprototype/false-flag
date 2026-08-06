"""Tests for the three-round decision pipeline (ER-023).

What is under test:

- **Determinism**: child seeds are pre-drawn per round in a fixed order, so
  a fixed-seed pipeline run is byte-identical however the threads are
  scheduled. The stub below makes its answers depend on the rng it is
  handed, so a scheduling-dependent draw order would show up as different
  transcripts, effects or trust.
- **Concurrency**: with every call held at a fixed latency, the wall clock
  is three serialized waits, not seven.
- **Failure isolation**: an exploding family degrades to that family's
  fallback and records a decision_phase fallback; the round survives.
- **The preview round**: pushback ∥ omissions returns exactly what the old
  serial order returned under the same seed discipline.
"""

import sys
import time
from pathlib import Path
from random import Random

import pytest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from engine.decision_phase import run_decision_pipeline, run_preview_round
from engine.initial_conditions import load_initial_conditions
from models.narrative_state import create_initial_narrative_state
from models.state_actors import load_actors_from_yaml
from models.world import Metrics, WorldState

ACTION = "Convene NATO allies and deploy defensive patrols over the North Sea."


@pytest.fixture(autouse=True)
def mock_provider(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")


def _world():
    world = WorldState(
        turn=2, scene=2, phase="discussion",
        metrics=Metrics(escalation_risk=60, domestic_stability=50,
                        alliance_cohesion=40, casualties_mil=0,
                        casualties_civ=0),
        flags={}, posture={}, narrative=None,
    )
    world.actor_system = load_actors_from_yaml(
        str(root / "data" / "state_actors.yaml"))
    return world


def _state():
    state = create_initial_narrative_state(
        metrics=Metrics(escalation_risk=60, domestic_stability=50,
                        alliance_cohesion=40, casualties_mil=0,
                        casualties_civ=0),
        play_mode="immersive",
    )
    state.record_played_event(2, "Akula-class boat surfaced off Orkney")
    return state


def seeded_llm(prompt, rng, **kwargs):
    """A stand-in whose answers depend on the rng it was handed.

    If the pipeline's draw order depended on thread scheduling, two runs of
    the same master seed would hand different seeds to the same task and
    every rng-derived number below would move.
    """
    p = prompt.lower()
    # Deterministic per-seed jitter, to shuffle thread completion order.
    time.sleep(0.001 * rng.randint(0, 5))
    if "assess this action" in p:
        return (f"QUALITY: good\n\nREASONING: Reading {rng.randint(0, 999)}.\n\n"
                f"EFFECTS:\nescalation_risk: {rng.randint(-5, 5)}\n"
                f"alliance_cohesion: {rng.randint(-5, 5)}\n\n"
                "QUALITY MULTIPLIER: 1.0")
    if "public_response:" in p:
        return (f"PUBLIC_RESPONSE: Noted, ref {rng.randint(0, 999)}.\n\n"
                f"PRIVATE_ASSESSMENT: Watching.\n\n"
                f"TRUST_CHANGE: {rng.randint(-5, 5)}\n\n"
                "WILL_SUPPORT: conditional\n\nCONDITIONS: none\n\n"
                "INTEL_SHARED: none")
    if "summarise the current situation" in p:
        return f"The campaign so far, take {rng.randint(0, 999)}."
    if "pushback" in p:
        return f"Foreign Secretary: Concern number {rng.randint(0, 999)}."
    if "critical omissions check" in p:
        return (f"CONCERN: Gap {rng.randint(0, 999)}.\n"
                f"RECOMMENDATION: Fix {rng.randint(0, 999)}.")
    if "respond to the pm's action" in p:
        return f"Understood, Prime Minister ({rng.randint(0, 999)})."
    return f"INTERPRETATION: reading {rng.randint(0, 999)}"


def seeded_batch(prompts, rng, **kwargs):
    return [seeded_llm(p, rng, **kwargs) for p in prompts]


def _run_pipeline(seed=42):
    world = _world()
    state = _state()
    result = run_decision_pipeline(
        world, "war_game_2025", ACTION, Random(seed),
        root_path=root, full_transcript=[], narrative_state=state,
        llm_generate_fn=seeded_llm, llm_batch_fn=seeded_batch,
    )
    return result, state, world


# --- determinism -------------------------------------------------------------

def test_fixed_seed_pipeline_replays_identically():
    """Two runs of the same seed: identical DecisionResult and trust."""
    first, state_a, world_a = _run_pipeline(seed=42)
    second, state_b, world_b = _run_pipeline(seed=42)

    assert first.transcript == second.transcript
    assert first.interpretation == second.interpretation
    assert first.pushback == second.pushback
    assert first.critical_concerns == second.critical_concerns
    assert first.final_effects == second.final_effects
    assert first.reasoning == second.reasoning
    assert first.character_responses == second.character_responses
    assert [r.dict() for r in first.actor_responses] == \
        [r.dict() for r in second.actor_responses]

    trust_a = {cid: c.trust for cid, c in state_a.characters.items()}
    trust_b = {cid: c.trust for cid, c in state_b.characters.items()}
    assert trust_a == trust_b
    assert state_a.situation_summary == state_b.situation_summary
    assert state_a.hidden_metrics.dict() == state_b.hidden_metrics.dict()

    # The rng-derived numbers actually reached the record - the stub's
    # answers were not scheduling-invariant by construction.
    assert "ref" in (first.reasoning or "") or first.actor_responses


def test_a_different_seed_actually_changes_the_answers():
    """Guard against the determinism test passing vacuously."""
    first, _, _ = _run_pipeline(seed=42)
    other, _, _ = _run_pipeline(seed=7)
    assert (first.transcript != other.transcript
            or first.final_effects != other.final_effects)


# --- concurrency -------------------------------------------------------------

LATENCY = 0.2


def test_wall_clock_is_three_waits_not_seven():
    """Every dispatch held at 0.2s: the pipeline finishes in ~3 waits.

    The serial shape was seven dispatch rounds (interpretation, pushback,
    omissions, actors, quality, reactions, summary) = 7 waits. The pipeline
    needs one wait per round = 3. Asserted with a generous margin: under
    5 waits' worth.
    """
    from llm.mock_driver import MockDeterministicDriver

    inner = MockDeterministicDriver()

    def slow_llm(prompt, rng, **kwargs):
        time.sleep(LATENCY)
        return inner.generate_text(prompt, rng)

    def slow_batch(prompts, rng, **kwargs):
        # One concurrent fan-out per group, the way the live drivers work.
        time.sleep(LATENCY)
        return [inner.generate_text(p, rng) for p in prompts]

    world = _world()
    state = _state()
    started = time.monotonic()
    result = run_decision_pipeline(
        world, "war_game_2025", ACTION, Random(42),
        root_path=root, full_transcript=[], narrative_state=state,
        llm_generate_fn=slow_llm, llm_batch_fn=slow_batch,
    )
    elapsed = time.monotonic() - started

    assert result.interpretation
    assert result.final_effects
    # Three rounds cannot finish faster than three waits...
    assert elapsed >= 3 * LATENCY
    # ...and concurrency must keep it well under five (serial took seven).
    assert elapsed < 5 * LATENCY, (
        f"pipeline took {elapsed:.2f}s = {elapsed / LATENCY:.1f} waits; "
        "expected ~3 (was 7 serially)")
    print(f"\n[decision-pipeline] wall clock {elapsed:.2f}s = "
          f"{elapsed / LATENCY:.1f} waits of {LATENCY}s (serial shape: 7)")


# --- failure isolation -------------------------------------------------------

def test_exploding_quality_assessment_degrades_not_kills(monkeypatch):
    """A quality-assessment explosion yields the heuristic assessment,
    actor-derived effects still land, and a fallback is recorded."""
    import engine.decision_phase as dp
    from llm import parse_health
    from llm.mock_driver import MockDeterministicDriver

    def boom(*args, **kwargs):
        raise RuntimeError("assessor down")

    monkeypatch.setattr(dp, "assess_action_quality", boom)
    parse_health.reset()

    inner = MockDeterministicDriver()
    world = _world()
    state = _state()
    result = run_decision_pipeline(
        world, "war_game_2025", ACTION, Random(42),
        root_path=root, full_transcript=[], narrative_state=state,
        llm_generate_fn=inner.generate_text,
        llm_batch_fn=inner.batch_generate_text,
    )

    # The round survived: actor answers arrived and the blend still moved
    # the metrics.
    assert result.actor_responses, "actor simulation must survive the blast"
    assert result.final_effects, "actor-derived effects must still land"
    assert result.quality_assessment["quality"] in {
        "exceptional", "good", "adequate", "poor", "catastrophic"}

    fallbacks = parse_health.snapshot()["fallbacks"]
    assert fallbacks.get("decision_phase", 0) >= 1, \
        "the degraded family must be recorded"
    parse_health.reset()


# --- the preview round -------------------------------------------------------

def test_preview_round_matches_the_old_serial_order():
    """run_preview_round returns exactly what the serial calls return under
    the documented child-seed order (pushback first, omissions second)."""
    from agents.conversation import (
        check_critical_omissions,
        generate_advisor_pushback,
    )

    world = _world()
    initial_conditions = load_initial_conditions("war_game_2025", root)
    interpretation = "INTERPRETATION: hold and consult."

    master = Random(9)
    pushback, concerns = run_preview_round(
        world, ACTION, interpretation, initial_conditions, master,
        full_transcript=[], event_ledger=None,
        llm_generate_fn=seeded_llm, llm_batch_fn=None,
    )

    # Serial reference: same seed discipline, no threads.
    mirror = Random(9)
    seed_pushback = mirror.randint(0, 2**31 - 1)
    seed_omissions = mirror.randint(0, 2**31 - 1)
    expected_pushback = generate_advisor_pushback(
        world, ACTION, interpretation, initial_conditions,
        seeded_llm, Random(seed_pushback), [], event_ledger=None)
    expected_concerns = check_critical_omissions(
        world, ACTION, interpretation, initial_conditions,
        seeded_llm, Random(seed_omissions), [], llm_batch_fn=None,
        event_ledger=None)

    assert pushback == expected_pushback
    assert pushback, "the seeded stub raises real pushback"
    assert concerns == expected_concerns
    assert concerns, "the seeded stub raises real omissions"


def test_preview_round_task_failure_degrades_to_empty(monkeypatch):
    """A dead omissions scan must not take the pushback with it."""
    import engine.decision_phase as dp
    from llm import parse_health

    def boom(*args, **kwargs):
        raise RuntimeError("omissions scan down")

    monkeypatch.setattr(dp, "check_critical_omissions", boom)
    parse_health.reset()

    world = _world()
    initial_conditions = load_initial_conditions("war_game_2025", root)
    pushback, concerns = run_preview_round(
        world, ACTION, "reading", initial_conditions, Random(3),
        llm_generate_fn=seeded_llm, llm_batch_fn=None,
    )

    assert pushback, "pushback must survive the omissions failure"
    assert concerns == []
    assert parse_health.snapshot()["fallbacks"].get("decision_phase", 0) >= 1
    parse_health.reset()
