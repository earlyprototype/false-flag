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


def test_turn_references_are_rewritten_to_in_fiction_days():
    """The FLASH-tier model sometimes says 'in Turn 2' - game mechanics in
    the fiction. The prompt forbids it and this display-side belt rewrites
    any survivor: 'turn N' -> 'day N', case-insensitively, word-bounded."""
    text = (
        "Foreign Secretary: We tried a blockade in Turn 2 and it failed; "
        "TURN 11 taught us the same lesson.\n"
        "Attorney General: The overturn 3 ruling and Saturn 5 files are "
        "unaffected, but turn 4's precedent stands."
    )
    result = generate_advisor_pushback(
        make_world(), "blockade again", "Blockade.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )
    fs_message = result[0][1]
    assert "in day 2" in fs_message
    assert "day 11" in fs_message
    assert "Turn 2" not in fs_message and "TURN 11" not in fs_message
    ag_message = result[1][1]
    # Word boundary: 'overturn 3' and 'Saturn 5' are not turn references.
    assert "overturn 3" in ag_message
    assert "Saturn 5" in ag_message
    assert "day 4's precedent" in ag_message


def test_the_voice_instructions_forbid_turn_references():
    from llm.prompts import ADVISOR_VOICE_INSTRUCTIONS

    # Stated abstractly - the rule may not quote the forms it bans (#97) -
    # and illustrated only by the in-fiction clock this scrubber rewrites to.
    assert "no turn numbers" in ADVISOR_VOICE_INSTRUCTIONS
    assert "no turn-relative phrases" in ADVISOR_VOICE_INSTRUCTIONS
    assert "two days ago" in ADVISOR_VOICE_INSTRUCTIONS


def test_pushback_roster_excludes_the_players_own_character():
    """The PM is the player: their office is never asked to object to itself.

    The roster used to be every character lacking a 'note' key, which put the
    Prime Minister (data/scenarios/war_game_2025/initial_conditions.yaml) in
    the list the model is told to speak for.
    """
    from engine.initial_conditions import load_initial_conditions
    from llm.prompts import build_pushback_prompt

    conditions = load_initial_conditions("war_game_2025")
    assert "prime_minister" in conditions["characters"], "fixture guard"

    prompt = build_pushback_prompt(
        make_world(), "deploy the carrier group", "Naval shadowing operation.",
        conditions
    )
    roster = prompt.split("Advisors and their pushback triggers:")[1]
    roster = roster.split("For each advisor")[0]

    assert "Prime Minister" not in roster
    # The advisors who do push back are still listed.
    assert "Chief of the Defence Staff" in roster
    assert "Attorney General" in roster


def test_pm_prefixed_reply_line_yields_no_prime_minister_pushback():
    """A PM-attributed line is dropped, not credited and not glued on.

    The parser accepts 'prime minister'/'pm' prefixes, so a model that
    ignores the roster could still put the player's own office in the
    pushback list. Such a line takes the orphan path: recorded and dropped.
    """
    text = (
        "Prime Minister: I am confident this is the right call.\n"
        "PM: And we will not be deterred.\n"
        "Attorney General: There is no legal basis for this action."
    )
    result = generate_advisor_pushback(
        make_world(), "strike now", "Immediate strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )

    roles = [role for role, _ in result]
    assert roles == ["Attorney General"]
    messages = " ".join(message for _, message in result)
    assert "right call" not in messages
    assert "not be deterred" not in messages


def test_wrapped_pm_line_does_not_leak_into_the_previous_advisor():
    """The tail of a dropped PM line is dropped too, not glued on.

    Dropping only the prefixed line leaves its wrapped continuation to the
    continuation branch, which appends it to the previous advisor - the same
    "player's words in an advisor's mouth" leak, one line deeper.
    """
    text = (
        "Attorney General: There is no legal basis for this action.\n"
        "Prime Minister: I am confident this is right\n"
        "and we will not be deterred.\n"
        "Chief of the Defence Staff: The carrier group is not ready."
    )
    result = generate_advisor_pushback(
        make_world(), "strike now", "Immediate strike.",
        INITIAL_CONDITIONS, make_llm(text), Random(42)
    )

    roles = [role for role, _ in result]
    assert roles == ["Attorney General", "Chief of the Defence Staff"]
    messages = " ".join(message for _, message in result)
    assert "not be deterred" not in messages
    assert "confident" not in messages
    # The advisor after the dropped block still parses normally.
    assert "carrier group is not ready" in messages


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
