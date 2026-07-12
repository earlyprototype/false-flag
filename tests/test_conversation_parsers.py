"""Tests for conversation parsing: pushback, critical omissions, and routing."""

import sys
from pathlib import Path
from random import Random

# Add project root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from agents.conversation import (  # noqa: E402
    check_critical_omissions,
    generate_advisor_pushback,
    handle_player_question,
)
from models.world import Metrics, WorldState  # noqa: E402


# Minimal initial conditions mirroring the roles in
# data/scenarios/war_game_2025/initial_conditions.yaml
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


def make_world() -> WorldState:
    return WorldState(
        metrics=Metrics(
            escalation_risk=40,
            domestic_stability=60,
            alliance_cohesion=70,
        )
    )


def make_llm(text: str):
    """Build a fake llm_generate_fn returning fixed text."""

    def fake_llm(prompt, rng, **kwargs):
        return text

    return fake_llm


# --- generate_advisor_pushback ---

def test_no_pushback_standalone_line_drops_pushback():
    result = generate_advisor_pushback(
        make_world(), "monitor the situation", "PM waits.",
        INITIAL_CONDITIONS, make_llm("NO PUSHBACK"), Random(42)
    )
    assert result == []


def test_no_pushback_decorated_standalone_line_drops_pushback():
    result = generate_advisor_pushback(
        make_world(), "monitor the situation", "PM waits.",
        INITIAL_CONDITIONS, make_llm("**NO PUSHBACK**"), Random(42)
    )
    assert result == []


def test_no_pushback_embedded_mid_sentence_is_not_dropped():
    text = (
        "Foreign Secretary: There is NO PUSHBACK from Washington yet, "
        "but unilateral action risks isolating us."
    )
    result = generate_advisor_pushback(
        make_world(), "strike without allies", "Unilateral strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert len(result) == 1
    role, message = result[0]
    assert role == "Foreign Secretary"
    assert "isolating us" in message


def test_multiline_pushback_keeps_continuation_lines():
    text = (
        "Foreign Secretary: This risks isolating the UK.\n"
        "We must consult NATO before any strike.\n"
        "**Escalation Risk**: this could trigger Article 5 chaos.\n"
        "Attorney General: There is no legal basis for this action."
    )
    result = generate_advisor_pushback(
        make_world(), "strike now", "Immediate strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    roles = [role for role, _ in result]
    assert roles == ["Foreign Secretary", "Attorney General"]
    # Markdown emphasis must not become a phantom advisor
    assert "Escalation Risk" not in roles
    fs_message = result[0][1]
    assert "consult NATO" in fs_message
    assert "Article 5" in fs_message
    assert "no legal basis" in result[1][1]


# --- check_critical_omissions ---

def test_markdown_bold_concern_and_recommendation_parse():
    text = (
        "**CONCERN:** Military action without NATO consultation.\n"
        "**RECOMMENDATION**: Convene the North Atlantic Council immediately."
    )
    result = check_critical_omissions(
        make_world(), "strike the submarine", "Unilateral strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert result, "Markdown-bold CONCERN/RECOMMENDATION should be parsed"
    for _role, concern, recommendation in result:
        assert concern == "Military action without NATO consultation."
        assert recommendation == "Convene the North Atlantic Council immediately."


def test_multiline_recommendation_appends_to_recommendation():
    text = (
        "CONCERN: Military action without legal authority.\n"
        "This exposes ministers to personal liability.\n"
        "RECOMMENDATION: Obtain Attorney General sign-off first.\n"
        "Then notify the UN Security Council."
    )
    result = check_critical_omissions(
        make_world(), "strike the submarine", "Unilateral strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert result
    for _role, concern, recommendation in result:
        # Continuation before RECOMMENDATION belongs to the concern
        assert "personal liability" in concern
        # Continuation after RECOMMENDATION belongs to the recommendation
        assert "UN Security Council" in recommendation
        assert "UN Security Council" not in concern


def test_no_concern_response_yields_no_omissions():
    result = check_critical_omissions(
        make_world(), "consult everyone", "PM consults widely.",
        INITIAL_CONDITIONS, make_llm("NO_CONCERN"), Random(42)
    )
    assert result == []


# --- advisor routing (handle_player_question) ---

def responding_roles(question: str):
    responses = handle_player_question(
        make_world(), question, INITIAL_CONDITIONS,
        make_llm("Understood, Prime Minister."), Random(42)
    )
    return [role for role, _ in responses]


def test_russia_status_does_not_route_to_foreign_secretary_via_us():
    roles = responding_roles("What is Russia's status?")
    assert "Diplomatic Lead" not in roles


def test_us_as_word_routes_to_foreign_secretary():
    roles = responding_roles("Will the US back us?")
    assert "Diplomatic Lead" in roles


def test_flaw_does_not_route_to_attorney_general_via_law():
    roles = responding_roles("Is there any flaw in the plan?")
    assert "Legal Advisor" not in roles


def test_legal_question_routes_to_attorney_general():
    roles = responding_roles("Is this legal?")
    assert "Legal Advisor" in roles


# --- WorldState.recent_injects ---

def test_world_state_has_recent_injects_field():
    world = make_world()
    assert world.recent_injects == []
    world.recent_injects.append("Russian Submarine Surfaces Near UK Waters")
    assert world.recent_injects == ["Russian Submarine Surfaces Near UK Waters"]
