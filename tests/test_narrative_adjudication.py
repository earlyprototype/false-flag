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


# --- Mystery-mode leak guard (issue #19) -----------------------------------

class _FakeNarrative:
    """Stand-in for NarrativeConfig carrying only what the scrubber reads."""
    narrative_id = "RUSSIA_AGGRESSION"
    description = (
        "The crisis is exactly as it appears: Russia is undertaking a major "
        "aggressive military operation to challenge NATO and assert dominance "
        "in the North Atlantic. Their motives are expansionist and "
        "opportunistic."
    )

    def to_llm_context(self, target_country_code=None):
        return (
            "SECRET NARRATIVE CONTEXT (DO NOT REVEAL DIRECTLY)\n"
            f"GLOBAL TRUTH: {self.description}"
        )


# Verbatim from live play — the two leaks that prompted issue #19.
_LEAK_GPT_OSS = (
    "The decision undercuts the opportunity to present a firm deterrent "
    "against the genuine Russian threat identified in the secret narrative."
)
_LEAK_LLAMA = (
    "The Prime Minister's behavior is consistent with someone who is either "
    "uninformed or unconcerned about the secret narrative, as this action "
    "plays directly into the hands of the hidden truth, which is that Russia "
    "is undertaking a major aggressive military operation to challenge NATO "
    "and assert dominance in the North Atlantic."
)


def test_historical_leaks_are_scrubbed():
    from engine.narrative_adjudication import _scrub_reasoning

    for leaked in (_LEAK_GPT_OSS, _LEAK_LLAMA):
        cleaned = _scrub_reasoning(leaked, _FakeNarrative())
        lowered = cleaned.lower()
        assert "secret narrative" not in lowered
        assert "hidden truth" not in lowered
        assert "assert dominance in the north atlantic" not in lowered
        assert "russia_aggression" not in lowered


def test_clean_reasoning_passes_through_unchanged():
    from engine.narrative_adjudication import _scrub_reasoning

    clean = (
        "The action addresses the most critical issues and is proportionate "
        "to the threat level. However, it leaves the domestic picture "
        "unattended."
    )
    assert _scrub_reasoning(clean, _FakeNarrative()) == clean


def test_only_the_offending_sentence_is_dropped():
    from engine.narrative_adjudication import _scrub_reasoning

    mixed = (
        "The decision is proportionate and buys time for verification. "
        "It also plays into the hidden truth of the crisis. "
        "Domestic messaging remains the weak point."
    )
    cleaned = _scrub_reasoning(mixed, _FakeNarrative())
    assert "proportionate and buys time" in cleaned
    assert "Domestic messaging remains the weak point." in cleaned
    assert "hidden truth" not in cleaned.lower()


def test_narrative_id_and_paraphrased_description_are_caught():
    from engine.narrative_adjudication import _scrub_reasoning

    by_id = "This aligns with the RUSSIA_AGGRESSION scenario as drawn."
    assert "russia_aggression" not in _scrub_reasoning(by_id, _FakeNarrative()).lower()

    # Paraphrase: leading clause altered, the identifying run intact
    paraphrased = (
        "In reality Russia is undertaking a major aggressive military "
        "operation to challenge NATO and assert dominance in the North "
        "Atlantic."
    )
    assert "assert dominance" not in _scrub_reasoning(
        paraphrased, _FakeNarrative()).lower()


def test_fully_leaked_reasoning_degrades_to_neutral_line():
    from engine.narrative_adjudication import _scrub_reasoning

    cleaned = _scrub_reasoning(_LEAK_GPT_OSS, _FakeNarrative())
    assert cleaned  # never empty — the panel still needs prose
    assert cleaned == "Your advisors take stock of the response."


def test_non_mystery_play_is_untouched():
    """Original Story Mode has no narrative; nothing should be scrubbed."""
    from engine.narrative_adjudication import _scrub_reasoning

    text = "A firm response to the hidden truth of the matter."
    # Static markers still apply (they are always a giveaway), but a
    # description-based match cannot fire without a narrative.
    assert _scrub_reasoning("A proportionate, well-evidenced response.", None) \
        == "A proportionate, well-evidenced response."
    assert "hidden truth" not in _scrub_reasoning(text, None).lower()


def test_parse_scrubs_reasoning_before_returning():
    """The leak must not reach the transcript or save, not just the screen."""
    from engine.narrative_adjudication import _parse_quality_response

    response = f"QUALITY: poor\n\nREASONING: {_LEAK_LLAMA}\n"
    parsed = _parse_quality_response(response, _FakeNarrative())
    assert "secret narrative" not in parsed["reasoning"].lower()
    assert "hidden truth" not in parsed["reasoning"].lower()
    assert parsed["quality"] == "poor"  # grading itself is unaffected


def test_assessment_prompt_no_longer_invites_the_leak():
    from engine.narrative_adjudication import assess_action_quality

    captured = {}

    def capture(prompt, rng, **kwargs):
        captured["prompt"] = prompt
        return "QUALITY: good\n\nREASONING: Sound under uncertainty.\n"

    assess_action_quality(
        "Hold position and gather evidence", make_state(), "interp",
        llm_generate_fn=capture, world_narrative=_FakeNarrative(),
        rng=Random(1),
    )
    prompt = captured["prompt"]
    assert "play into or against the hidden truth" not in prompt
    assert "REASONING is displayed to the player" in prompt
    assert "well-reasoned given what the player could actually know" in prompt
