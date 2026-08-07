"""Tolerant-parsing regression tests.

Every demonstrated input below is taken verbatim from the audit register
(audits/ENGINE-ROUTING-ISSUES.md): decorated labels, worded refusals,
annotated numbers, bulleted objections. The register entries these close are
ER-006, ER-015, ER-016, ER-029, ER-030, ER-031, ER-034, ER-035, ER-036,
ER-039, ER-042, ER-044 and ER-045.
"""

import sys
from pathlib import Path
from random import Random

import pytest

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from llm import parse_health  # noqa: E402
from llm.parsing import (  # noqa: E402
    extract_label,
    find_float,
    find_signed_int,
    is_sentinel_line,
    match_enum,
    strip_decoration,
)
from engine.narrative_adjudication import _parse_quality_response  # noqa: E402
from engine.actor_simulation import _parse_actor_response  # noqa: E402
from engine.diplomacy import assess_diplomatic_outcome  # noqa: E402
from engine.sim_loop import apply_inject_effects  # noqa: E402
from agents.conversation import (  # noqa: E402
    check_critical_omissions,
    generate_advisor_pushback,
)
from models.world import Metrics, WorldState  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_parse_health():
    """Counts must not bleed between tests (or into the wider suite)."""
    parse_health.reset()
    yield
    parse_health.reset()


# Roles mirror data/scenarios/war_game_2025/initial_conditions.yaml
INITIAL_CONDITIONS = {
    "characters": {
        "prime_minister": {"role": "Government Leader"},
        "chief_defence_staff": {"role": "Military Commander"},
        "national_security_advisor": {"role": "Intelligence Coordinator"},
        "home_secretary": {"role": "Domestic Security"},
        "foreign_secretary": {"role": "Diplomatic Lead"},
        "attorney_general": {"role": "Legal Advisor"},
    }
}


def make_world(**overrides) -> WorldState:
    return WorldState(
        metrics=Metrics(
            escalation_risk=overrides.get("escalation_risk", 40),
            domestic_stability=overrides.get("domestic_stability", 60),
            alliance_cohesion=overrides.get("alliance_cohesion", 70),
        )
    )


def make_llm(text: str):
    def fake_llm(prompt, rng, **kwargs):
        return text

    return fake_llm


# --- shared utilities --------------------------------------------------------

def test_extract_label_tolerates_decoration():
    for line in [
        "QUALITY: poor",
        "**QUALITY:** poor",
        "**QUALITY**: poor",
        "- quality: poor",
        "> QUALITY: poor",
        "2. QUALITY: **poor**",
    ]:
        assert extract_label(line, "QUALITY") in ("poor", "**poor"), line
        assert strip_decoration(extract_label(line, "QUALITY")) == "poor", line


def test_extract_label_rejects_other_labels():
    assert extract_label("QUALITY MULTIPLIER: 0.5", "QUALITY") is None
    assert extract_label("Plain prose with no label", "QUALITY") is None


def test_find_signed_int_recovers_annotated_numbers():
    assert find_signed_int("+8 (sharp rise)") == 8
    assert find_signed_int("-12") == -12
    assert find_signed_int("no number here") is None


def test_find_float():
    assert find_float("0.5") == 0.5
    assert find_float("1.0 (neutral)") == 1.0
    assert find_float("nothing") is None


def test_is_sentinel_line_variants():
    assert is_sentinel_line("NO_CONCERN", "NO_CONCERN")
    assert is_sentinel_line("NO CONCERN", "NO_CONCERN")
    assert is_sentinel_line("**NO_CONCERN.**", "NO_CONCERN")
    assert not is_sentinel_line(
        "NO_CONCERN was my first thought but NATO was not consulted.",
        "NO_CONCERN",
    )


def test_match_enum_word_boundaries_and_negation():
    allowed = ("yes", "no", "conditional")
    assert match_enum("yes", allowed, refusal_value="no") == "yes"
    assert match_enum("Yes, with conditions attached", allowed, refusal_value="no") == "yes"
    assert match_enum("conditional", allowed, refusal_value="no") == "conditional"
    assert match_enum("unclear", allowed, refusal_value="no") is None


def test_parse_health_registry_is_deterministic():
    parse_health.record_miss("b_component", "field")
    parse_health.record_miss("a_component", "field")
    parse_health.record_miss("a_component", "field")
    parse_health.record_fallback("router")
    snap = parse_health.snapshot()
    assert list(snap["misses"]) == ["a_component.field", "b_component.field"]
    assert snap["misses"]["a_component.field"] == 2
    assert snap["fallbacks"] == {"router": 1}
    assert parse_health.total() == 4
    parse_health.reset()
    assert parse_health.total() == 0


# --- ER-015: decorated labels must not drop the decision's metric effects ----

_ER015_EXPECTED_EFFECTS = {
    "escalation_risk": 8,
    "alliance_cohesion": -6,
    "domestic_stability": -3,
}

_ER015_FORM_1 = """QUALITY: poor

REASONING: The deployment escalates without allied cover.

EFFECTS:
escalation_risk: 8
alliance_cohesion: -6
domestic_stability: -3

QUALITY MULTIPLIER: 0.5"""

_ER015_FORM_2 = """**QUALITY:** poor

**REASONING:** The deployment escalates without allied cover.

**EFFECTS:**
- escalation_risk: 8
- alliance_cohesion: -6
- domestic_stability: -3

**QUALITY MULTIPLIER:** 0.5"""

_ER015_FORM_3 = """**QUALITY:** poor

**REASONING:** The deployment escalates without allied cover.

**EFFECTS:**
- **escalation_risk:** 8
- **alliance_cohesion:** -6
- **domestic_stability:** -3

**QUALITY MULTIPLIER:** 0.5"""


@pytest.mark.parametrize("form", [_ER015_FORM_1, _ER015_FORM_2, _ER015_FORM_3])
def test_er015_all_three_forms_parse_identically(form):
    parsed = _parse_quality_response(form)
    assert parsed["quality"] == "poor"
    assert parsed["multiplier"] == 0.5
    assert parsed["suggested_effects"] == _ER015_EXPECTED_EFFECTS
    assert "escalates without allied cover" in parsed["reasoning"]


# --- ER-034: an annotated number recovers instead of dropping ----------------

def test_er034_annotated_delta_is_recovered():
    response = (
        "QUALITY: adequate\n"
        "REASONING: Reasonable.\n"
        "EFFECTS:\n"
        "escalation_risk: +8 (sharp rise)\n"
        "alliance_cohesion: -6\n"
        "domestic_stability: -3\n"
    )
    parsed = _parse_quality_response(response)
    assert parsed["suggested_effects"] == {
        "escalation_risk": 8,
        "alliance_cohesion": -6,
        "domestic_stability": -3,
    }


# --- ER-031: an explicit multiplier of 1.0 survives --------------------------

def test_er031_explicit_multiplier_one_survives_poor_quality():
    response = (
        "QUALITY: poor\n"
        "REASONING: Weak, but the model chose a neutral multiplier.\n"
        "EFFECTS:\n"
        "escalation_risk: 4\n"
        "QUALITY MULTIPLIER: 1.0\n"
    )
    parsed = _parse_quality_response(response)
    assert parsed["quality"] == "poor"
    assert parsed["multiplier"] == 1.0


def test_er031_absent_multiplier_still_maps_from_quality():
    parsed = _parse_quality_response(
        "QUALITY: poor\nREASONING: Weak.\nEFFECTS:\nescalation_risk: 4\n"
    )
    assert parsed["multiplier"] == 0.5


# --- ER-006: prose in the delta shape must not move a metric -----------------

def test_er006_wrapped_reasoning_line_moves_nothing():
    response = (
        "QUALITY: adequate\n"
        "REASONING: Tensions continue to build, and with public\n"
        "escalation: rising sentiment leaves little room to manoeuvre.\n"
        "EFFECTS:\n"
        "alliance_cohesion: 2\n"
    )
    parsed = _parse_quality_response(response)
    assert parsed["suggested_effects"] == {"alliance_cohesion": 2}
    assert "escalation: rising sentiment" in parsed["reasoning"]


def test_quality_parse_miss_is_recorded_not_silent():
    _parse_quality_response("Nothing structured at all.")
    snap = parse_health.snapshot()
    assert any(k.startswith("quality_assessment.") for k in snap["misses"])


# --- ER-030: worded refusals read as refusals --------------------------------

@pytest.mark.parametrize("refusal", [
    "no",
    "absolutely not",
    "not at this time",
    "no, we will not assist",
])
def test_er030_worded_refusals_read_as_no(refusal):
    response = (
        "PUBLIC_RESPONSE: We cannot follow London here.\n"
        "PRIVATE_ASSESSMENT: The UK is overextended.\n"
        "TRUST_CHANGE: -8\n"
        f"WILL_SUPPORT: {refusal}\n"
        "CONDITIONS: none\n"
        "INTEL_SHARED: none\n"
    )
    parsed = _parse_actor_response("USA", response)
    assert parsed.will_support == "no", refusal
    assert parsed.trust_change == -8


# --- ER-016: an emphasised actor reply parses the same as a bare one ---------

_ER016_BARE = (
    "PUBLIC_RESPONSE: The United States cannot support this action at this time.\n"
    "PRIVATE_ASSESSMENT: London is moving faster than the evidence.\n"
    "TRUST_CHANGE: -8\n"
    "WILL_SUPPORT: no\n"
    "CONDITIONS: none\n"
    "INTEL_SHARED: none\n"
)

_ER016_EMPHASISED = (
    "**PUBLIC_RESPONSE:** The United States cannot support this action at this time.\n"
    "**PRIVATE_ASSESSMENT:** London is moving faster than the evidence.\n"
    "**TRUST_CHANGE:** -8\n"
    "**WILL_SUPPORT:** no\n"
    "**CONDITIONS:** none\n"
    "**INTEL_SHARED:** none\n"
)


def test_er016_emphasised_reply_parses_same_as_bare():
    bare = _parse_actor_response("USA", _ER016_BARE)
    emphasised = _parse_actor_response("USA", _ER016_EMPHASISED)
    assert emphasised.public_response == bare.public_response
    assert bare.public_response == \
        "The United States cannot support this action at this time."
    assert emphasised.trust_change == bare.trust_change == -8
    assert emphasised.will_support == bare.will_support == "no"


def test_actor_reply_with_no_labels_records_a_miss():
    parsed = _parse_actor_response("USA", "Washington will consider its position.")
    assert parsed.will_support == "conditional"
    assert parse_health.snapshot()["misses"] == {"actor_simulation.all_fields": 1}


# --- ER-029 / ER-034: diplomatic outcome parser ------------------------------

def run_outcome(text):
    return assess_diplomatic_outcome(
        make_world(), "US", [("US President", "Well?"), ("UK PM", "We are sure.")],
        make_llm(text), Random(42)
    )


def test_er029_emphasised_outcome_parses_as_failure():
    assessment, delta = run_outcome(
        "**OUTCOME:** FAILURE\n"
        "**ALLIANCE_COHESION_DELTA:** -12\n"
        "**SUMMARY:** Washington refused.\n"
    )
    assert "FAILURE" in assessment
    assert "Washington refused." in assessment
    assert delta == -12


def test_er034_annotated_diplomatic_delta_is_recovered():
    assessment, delta = run_outcome(
        "OUTCOME: SUCCESS\n"
        "ALLIANCE_COHESION_DELTA: +8 (strong reassurance)\n"
        "SUMMARY: good\n"
    )
    assert "SUCCESS" in assessment
    assert delta == 8


def test_diplomatic_outcome_summary_accumulates_continuations():
    assessment, delta = run_outcome(
        "OUTCOME: NEUTRAL\n"
        "ALLIANCE_COHESION_DELTA: 0\n"
        "SUMMARY: The call kept the channel open\n"
        "and clarified positions on both sides.\n"
    )
    assert "kept the channel open and clarified positions" in assessment


def test_diplomatic_outcome_defaults_are_recorded():
    assessment, delta = run_outcome("The president hung up.")
    assert "NEUTRAL" in assessment
    assert delta == 0
    snap = parse_health.snapshot()
    assert snap["misses"] == {
        "diplomacy_outcome.delta": 1,
        "diplomacy_outcome.outcome": 1,
        "diplomacy_outcome.summary": 1,
    }


# --- ER-035: a bulleted cabinet objection is real pushback -------------------

def test_er035_bulleted_roster_reply_returns_two_entries():
    text = (
        "- Military Commander: Two frigates leaves the approaches uncovered.\n"
        "- Legal Advisor: No Article 51 basis."
    )
    result = generate_advisor_pushback(
        make_world(), "deploy two frigates", "Two frigates north.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert [role for role, _ in result] == ["Military Commander", "Legal Advisor"]
    assert "approaches uncovered" in result[0][1]
    assert "Article 51" in result[1][1]


def test_orphan_leading_line_is_recorded_not_silent():
    text = (
        "The cabinet has reservations.\n"
        "Legal Advisor: No Article 51 basis."
    )
    result = generate_advisor_pushback(
        make_world(), "strike now", "Immediate strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert [role for role, _ in result] == ["Legal Advisor"]
    assert parse_health.snapshot()["misses"] == {"pushback.orphan_line": 1}


# --- ER-036: acceptance rules must not discard real omissions ----------------

def test_er036_sentinel_mid_sentence_keeps_the_concern():
    text = (
        "CONCERN: NO_CONCERN was my first thought but NATO was not consulted "
        "before deployment.\n"
        "RECOMMENDATION: Convene the NAC."
    )
    result = check_critical_omissions(
        make_world(), "deploy into the Barents", "Deployment north.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert result, "a concern mentioning the sentinel mid-sentence must survive"
    for _role, concern, recommendation in result:
        assert "NATO was not consulted" in concern
        assert recommendation == "Convene the NAC."


def test_er036_concern_without_recommendation_surfaces():
    text = "CONCERN: No NATO consultation before a deployment into the Barents."
    result = check_critical_omissions(
        make_world(), "deploy into the Barents", "Deployment north.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert result, "a concern with no recommendation must still surface"
    for _role, concern, recommendation in result:
        assert "No NATO consultation" in concern
        assert recommendation == "(no specific recommendation given)"
    assert parse_health.snapshot()["misses"] == {
        "critical_omissions.recommendation": len(result)
    }


def test_recommendation_without_concern_is_recorded_and_skipped():
    text = "RECOMMENDATION: Convene the NAC."
    result = check_critical_omissions(
        make_world(), "deploy into the Barents", "Deployment north.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert result == []
    assert parse_health.snapshot()["misses"] == {"critical_omissions.concern": 5}


# --- ER-045: a partial batch failure is visible ------------------------------

def test_er045_error_slot_counts_as_fallback_others_unaffected():
    concern_text = (
        "CONCERN: Military action without NATO consultation.\n"
        "RECOMMENDATION: Convene the North Atlantic Council."
    )

    def batch(prompts, rng, **kwargs):
        out = [concern_text] * len(prompts)
        out[0] = "[ERROR: HTTP 500 from provider]"
        return out

    result = check_critical_omissions(
        make_world(), "strike the submarine", "Unilateral strike.",
        INITIAL_CONDITIONS, make_llm(concern_text), Random(42),
        llm_batch_fn=batch,
    )
    # Five advisors scan; the failed slot is lost as a failed call, not
    # silently converted into "no concern". The other four still surface.
    assert len(result) == 4
    snap = parse_health.snapshot()
    assert snap["fallbacks"] == {"critical_omissions": 1}


# --- ER-042: non-integer inject deltas land ----------------------------------

def test_er042_coercible_deltas_land_and_garbage_is_reported():
    world = make_world()
    world.difficulty = "brutal"  # 1.0 multiplier: deltas land at face value
    inject = {
        "effects": [
            {"metric": "escalation_risk", "delta": "5"},
            {"metric": "alliance_cohesion", "delta": 3.5},
            {"metric": "domestic_stability", "delta": "-4 (initial)"},
            {"metric": "escalation_risk", "delta": "substantial"},
        ]
    }
    lines = apply_inject_effects(world, inject)
    assert world.metrics.escalation_risk == 45          # 40 + 5
    assert world.metrics.alliance_cohesion == 74        # 70 + round(3.5)
    assert world.metrics.domestic_stability == 56       # 60 - 4
    assert "Skipped: unreadable delta for 'escalation_risk'" in lines
    assert parse_health.snapshot()["misses"] == {
        "inject_effects.escalation_risk": 1
    }


def test_er042_range_delta_still_works():
    world = make_world()
    world.difficulty = "brutal"
    inject = {"effects": [{"metric": "escalation_risk", "delta": "4..6"}]}
    apply_inject_effects(world, inject)
    assert world.metrics.escalation_risk == 45  # 40 + midpoint 5


# --- ER-039: the quality multiplier applies once -----------------------------

def _quality_reply(multiplier):
    return (
        "QUALITY: poor\n"
        "REASONING: Overreach.\n"
        "EFFECTS:\n"
        "escalation_risk: 10\n"
        f"QUALITY MULTIPLIER: {multiplier}\n"
    )


def _adjudicate_at(multiplier):
    from engine.narrative_adjudication import adjudicate_with_narrative
    from models.narrative_state import create_initial_narrative_state

    state = create_initial_narrative_state(
        metrics=Metrics(escalation_risk=60, domestic_stability=50,
                        alliance_cohesion=40, casualties_mil=0, casualties_civ=0),
        play_mode="classic", game_time="Turn 1",
    )
    effects, _responses, _reasoning = adjudicate_with_narrative(
        state, "Escalate patrols", "interp", Random(42),
        llm_generate_fn=make_llm(_quality_reply(multiplier)),
    )
    return effects


def test_er039_suggested_ten_at_half_multiplier_lands_as_five():
    assert _adjudicate_at(0.5)["escalation_risk"] == 5


def test_er039_suggested_ten_at_max_multiplier_clamps_to_twenty():
    assert _adjudicate_at(2.5)["escalation_risk"] == 20


# --- ER-044: the decision summary panel reads decorated output ---------------

def test_er044_decorated_interpretation_parses():
    from cli.display_utils import parse_interpretation_simple

    interpretation = (
        "**INTERPRETATION:** Deploy a destroyer to shadow the vessel.\n"
        "**FORCES INVOLVED:**\n"
        "- HMS Daring: Type-45 destroyer\n"
        "• P-8 Poseidon patrols\n"
        "**TIMELINE:** Immediate\n"
        "**FEASIBILITY:** Feasible within current constraints\n"
    )
    parsed = parse_interpretation_simple(interpretation)
    assert parsed["summary"] == "Deploy a destroyer to shadow the vessel."
    assert parsed["forces"] == ["HMS Daring", "P-8 Poseidon patrols"]
    assert parsed["timeline"] == "Immediate"


# ---------------------------------------------------------------------------
# ER-049: actor text fields accumulate continuation lines
# ---------------------------------------------------------------------------

def test_actor_reply_with_labels_on_their_own_lines_keeps_the_text():
    from engine.actor_simulation import _parse_actor_response

    r = _parse_actor_response("USA", (
        "PUBLIC_RESPONSE:\n"
        "The United States stands shoulder to shoulder with the United Kingdom.\n"
        "We will review the evidence with our NATO allies.\n"
        "PRIVATE_ASSESSMENT:\n"
        "London is handling this well but Congress needs the evidence.\n"
        "TRUST_CHANGE: +5\n"
        "WILL_SUPPORT: yes\n"
        "CONDITIONS: none"
    ))
    assert "shoulder to shoulder" in r.public_response
    assert "NATO allies" in r.public_response
    assert "acknowledges the action" not in r.public_response
    assert "Congress needs the evidence" in r.private_assessment
    assert r.trust_change == 5
    assert r.will_support == "yes"


def test_actor_reply_with_no_public_response_records_a_miss():
    from engine.actor_simulation import _parse_actor_response
    from llm import parse_health

    parse_health.reset()
    r = _parse_actor_response("USA", "TRUST_CHANGE: -2\nWILL_SUPPORT: conditional")
    assert "acknowledges the action" in r.public_response
    assert parse_health.snapshot()["misses"].get(
        "actor_simulation.public_response") == 1
