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
    handle_player_question_all,
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


def test_no_pushback_words_inside_bare_concern_are_not_a_sentinel():
    text = ("There is NO PUSHBACK from Washington yet, but unilateral "
            "action risks isolating us.")
    result = generate_advisor_pushback(
        make_world(), "strike without allies", "Unilateral strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert len(result) == 5
    assert all("isolating us" in message for _, message in result)


def test_multiline_bare_pushback_keeps_every_line():
    text = (
        "This risks isolating the UK.\n"
        "We must consult NATO before any strike.\n"
        "It could trigger Article 5 chaos."
    )
    result = generate_advisor_pushback(
        make_world(), "strike now", "Immediate strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    assert len(result) == 5
    for _role, message in result:
        assert "consult NATO" in message
        assert "Article 5" in message


def test_turn_references_are_rewritten_to_in_fiction_days():
    """The FLASH-tier model sometimes says 'in Turn 2' - game mechanics in
    the fiction. The prompt forbids it and this display-side belt rewrites
    any survivor: 'turn N' -> 'day N', case-insensitively, word-bounded."""
    text = ("We tried a blockade in Turn 2 and it failed; TURN 11 taught us "
            "the same lesson. The overturn 3 ruling and Saturn 5 files are "
            "unaffected, but turn 4's precedent stands.")
    result = generate_advisor_pushback(
        make_world(), "blockade again", "Blockade.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    message = result[0][1]
    assert "in day 2" in message
    assert "day 11" in message
    assert "Turn 2" not in message and "TURN 11" not in message
    # Word boundary: 'overturn 3' and 'Saturn 5' are not turn references.
    assert "overturn 3" in message
    assert "Saturn 5" in message
    assert "day 4's precedent" in message


def test_the_voice_instructions_forbid_turn_references():
    from llm.prompts import ADVISOR_VOICE_INSTRUCTIONS

    # Stated abstractly - the rule may not quote the forms it bans (#97) -
    # and illustrated only by the in-fiction clock this scrubber rewrites to.
    assert "no turn numbers" in ADVISOR_VOICE_INSTRUCTIONS
    assert "no turn-relative phrases" in ADVISOR_VOICE_INSTRUCTIONS
    assert "two days ago" in ADVISOR_VOICE_INSTRUCTIONS
    # The banned examples themselves must never come back into the rule text.
    lowered = ADVISOR_VOICE_INSTRUCTIONS.lower()
    for banned in ("in turn two", "last turn"):
        assert banned not in lowered


def test_pushback_roster_excludes_the_players_own_character():
    """The PM is the player: their office is never asked to object to itself.

    The roster used to be every character lacking a 'note' key, which put the
    Prime Minister (data/scenarios/war_game_2025/initial_conditions.yaml) in
    the list the model is told to speak for.
    """
    from engine.initial_conditions import get_all_uk_advisors, load_initial_conditions
    from llm.prompts import build_pushback_prompt

    conditions = load_initial_conditions("war_game_2025")
    assert "prime_minister" in conditions["characters"], "fixture guard"
    assert "prime_minister" not in get_all_uk_advisors(conditions)

    prompt = build_pushback_prompt(
        make_world(), "deploy the carrier group", "Naval shadowing operation.",
        conditions, "chief_defence_staff"
    )
    assert "Chief of the Defence Staff" in prompt
    assert "Attorney General" not in prompt


def test_pm_prefixed_reply_is_visible_as_malformed_not_attributed_to_player():
    """A model-written PM block never becomes the speaker or quoted advice."""
    text = (
        "Government Leader: I am confident this is the right call.\n"
        "PM: And we will not be deterred.\n"
        "Attorney General: There is no legal basis for this action."
    )
    result = generate_advisor_pushback(
        make_world(), "strike now", "Immediate strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )

    roles = [role for role, _ in result]
    assert "Government Leader" not in roles
    messages = " ".join(message for _, message in result)
    assert "right call" not in messages
    assert "not be deterred" not in messages


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


def test_overall_strategy_question_never_answers_as_the_prime_minister():
    roles = responding_roles("What is our overall strategy?")
    assert roles == ["Intelligence Coordinator"]


# --- handle_player_question_all (ask the whole room) ---

ALL_ROSTER_ROLES = [
    "Military Commander", "Intelligence Coordinator", "Domestic Security",
    "Diplomatic Lead", "Legal Advisor",
]


def test_ask_all_answers_once_per_advisor_in_roster_order():
    result = handle_player_question_all(
        make_world(), "Where do we stand?", INITIAL_CONDITIONS,
        make_llm("We hold, Prime Minister."), Random(42)
    )
    assert [role for role, _ in result] == ALL_ROSTER_ROLES
    assert all(text == "We hold, Prime Minister." for _, text in result)


def test_ask_all_excludes_the_player_seat():
    """The Prime Minister is the player: the room answers, the chair asks."""
    result = handle_player_question_all(
        make_world(), "Thoughts?", INITIAL_CONDITIONS,
        make_llm("Noted."), Random(42)
    )
    assert all(role != "Government Leader" for role, _ in result)


def test_ask_all_fans_out_as_one_batched_group():
    calls = []

    def batch(prompts, rng, **kwargs):
        calls.append(list(prompts))
        return [f"answer {i}" for i in range(len(prompts))]

    result = handle_player_question_all(
        make_world(), "Options?", INITIAL_CONDITIONS,
        make_llm("unused - the batch path answers"), Random(1),
        llm_batch_fn=batch
    )
    assert len(calls) == 1, "the five prompts must go out as one group"
    assert len(calls[0]) == len(ALL_ROSTER_ROLES)
    assert [t for _, t in result] == [f"answer {i}"
                                      for i in range(len(ALL_ROSTER_ROLES))]


def test_ask_all_error_slot_and_empty_reply_become_in_fiction_deferrals():
    """A batch '[ERROR: ...]' slot or an empty reply is a failed call, not an
    advisor's line — it must never be quoted as one."""
    from llm import parse_health

    def batch(prompts, rng, **kwargs):
        out = ["A considered answer."] * len(prompts)
        out[1] = "[ERROR: HTTP 429 rate limited]"
        out[3] = "   "
        return out

    before = parse_health.total()
    result = handle_player_question_all(
        make_world(), "Options?", INITIAL_CONDITIONS,
        make_llm("unused"), Random(1), llm_batch_fn=batch
    )
    texts = [t for _, t in result]
    assert texts[1].startswith("Prime Minister, I want to verify")
    assert texts[3].startswith("Prime Minister, I want to verify")
    assert "[ERROR" not in "\n".join(texts)
    assert [role for role, _ in result] == ALL_ROSTER_ROLES
    assert parse_health.total() - before == 2, \
        "both substitutions must show in parse health"


def test_ask_all_with_no_advisors_says_so():
    result = handle_player_question_all(
        make_world(), "Anyone there?", {"characters": {}},
        make_llm("unused"), Random(1)
    )
    assert result[0][0] == "System"


# --- WorldState.recent_injects ---

def test_world_state_has_recent_injects_field():
    world = make_world()
    assert world.recent_injects == []
    world.recent_injects.append("Russian Submarine Surfaces Near UK Waters")
    assert world.recent_injects == ["Russian Submarine Surfaces Near UK Waters"]
