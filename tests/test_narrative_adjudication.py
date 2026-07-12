"""Regression tests for the narrative adjudication pipeline.

Covers the bugs fixed in the mode-sanity pass:
- LLM calls must receive the rng argument (router.generate_text requires it;
  a missing rng used to raise TypeError inside a bare except, silently
  disabling LLM adjudication in every game).
- The catastrophic quality multiplier must amplify penalties, not invert them.
- The situation summary must update after adjudication (emergent mode's
  primary display used to stay frozen at its initial value).
- Vibe trends must track the real Metrics attributes.
"""

from random import Random

from models.narrative_state import create_initial_narrative_state
from models.world import Metrics


def make_state(play_mode="classic", **overrides):
    metrics = Metrics(
        escalation_risk=overrides.get("escalation_risk", 60),
        domestic_stability=overrides.get("domestic_stability", 50),
        alliance_cohesion=overrides.get("alliance_cohesion", 40),
        casualties_mil=0,
        casualties_civ=0,
    )
    return create_initial_narrative_state(
        metrics=metrics, play_mode=play_mode, game_time="Turn 1"
    )


def strict_llm_recorder(calls):
    """A stand-in with router.generate_text's signature: rng is required."""

    def fn(prompt, rng, **kwargs):
        assert isinstance(rng, Random), "rng must be a Random instance"
        calls.append(prompt)
        if "ASSESS THIS ACTION" in prompt:
            return (
                "QUALITY: good\n\nREASONING: Sensible move.\n\nEFFECTS:\n"
                "escalation_risk: -3\nalliance_cohesion: 4\n\nQUALITY MULTIPLIER: 1.5"
            )
        if "Summarise the current situation" in prompt:
            return "Fresh summary after the decision."
        return "In-character advisor reaction."

    return fn


def test_adjudication_calls_llm_with_rng():
    from engine.narrative_adjudication import adjudicate_with_narrative

    state = make_state()
    calls = []
    effects, character_responses, reasoning = adjudicate_with_narrative(
        state,
        "Request NATO Article 4 consultations",
        "interpretation",
        Random(42),
        llm_generate_fn=strict_llm_recorder(calls),
    )

    # Quality assessment, at least one character response, and the summary
    # must all have gone through the LLM function without a TypeError.
    assert len(calls) >= 3
    assert reasoning == "Sensible move."
    assert character_responses, "expected at least one advisor reaction"
    assert all(text == "In-character advisor reaction." for _, text in character_responses)


def test_quality_assessment_falls_back_without_rng():
    from engine.narrative_adjudication import assess_action_quality

    state = make_state()

    def rejecting_fn(prompt, rng, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("should not be called without rng")

    result = assess_action_quality(
        "Do nothing", state, "interp", llm_generate_fn=rejecting_fn, rng=None
    )
    assert result["quality"] in {"exceptional", "good", "adequate", "poor", "catastrophic"}


def test_catastrophic_multiplier_amplifies_not_inverts():
    from engine.narrative_adjudication import (
        _heuristic_quality_assessment,
        _parse_quality_response,
        apply_quality_scaling,
    )

    state = make_state(escalation_risk=70)

    heuristic = _heuristic_quality_assessment("launch a nuclear attack", state)
    assert heuristic["quality"] == "catastrophic"
    assert heuristic["multiplier"] > 0

    parsed = _parse_quality_response("QUALITY: catastrophic\n\nREASONING: Bad.\n")
    assert parsed["multiplier"] > 0

    scaled = apply_quality_scaling({"escalation_risk": 20}, heuristic, state)
    assert scaled["escalation_risk"] > 0, "penalty must not flip into a reward"


def test_situation_summary_updates_after_adjudication():
    from engine.narrative_adjudication import adjudicate_with_narrative

    state = make_state(play_mode="emergent")
    initial_summary = state.situation_summary

    adjudicate_with_narrative(
        state, "Hold a press conference", "interp", Random(1),
        llm_generate_fn=strict_llm_recorder([]),
    )
    assert state.situation_summary == "Fresh summary after the decision."
    assert state.situation_summary != initial_summary


def test_situation_summary_fallback_is_state_aware():
    from engine.narrative_adjudication import update_situation_summary

    state = make_state(escalation_risk=90, alliance_cohesion=20, domestic_stability=25)
    update_situation_summary(state, "some action", llm_generate_fn=None, rng=None)
    summary = state.situation_summary
    assert "threshold of open war" in summary
    assert "fracturing" in summary


def test_vibe_trends_track_real_metrics():
    state = make_state()
    state.previous_metrics = state.hidden_metrics.copy()
    state.previous_metrics.escalation_risk -= 10   # risk rose since last turn
    state.previous_metrics.alliance_cohesion += 10  # cohesion fell since last turn

    vibes = {v.name: v.trend for v in state.get_situation_vibes()}
    assert vibes["Crisis Intensity"] == "rising"
    assert vibes["Allied Unity"] == "falling"
    assert vibes["Domestic Support"] == "stable"


def test_update_hidden_metrics_snapshots_previous():
    state = make_state()
    before = state.hidden_metrics.escalation_risk
    state.update_hidden_metrics({"escalation_risk": before + 8})
    assert state.previous_metrics.escalation_risk == before
    assert state.hidden_metrics.escalation_risk == before + 8


def test_strip_effect_boxes_removes_numbers_keeps_narrative():
    from cli.display_utils import strip_effect_boxes

    lines = [
        "Some narrative line.",
        "┌───────────────────────────────────┐",
        "│ Effect: escalation_risk +3 (→ 63) │",
        "└───────────────────────────────────┘",
        "More narrative.",
        "│ Effect: domestic_stability -2 (-> 48) │",
        "Final line.",
    ]
    out = strip_effect_boxes(lines)
    assert out == ["Some narrative line.", "More narrative.", "Final line."]
