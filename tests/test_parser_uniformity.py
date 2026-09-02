"""Parser-uniformity regression tests.

Repro inputs are taken verbatim from the LLM-reply parser audit: the
pending-field mechanism (a structured label whose value sits on the next
line), sentinel tolerance for quoted/punctuated "none", match_enum's
multi-word negation lookback, the parse-first NO PUSHBACK rule, empty-reply
and fallback recording on every fallback path, residue accounting, the
inject YAML fence/schema fixes, the API discussion role roster, and the
decision-interpretation leak into the diplomatic context.
"""

import sys
from pathlib import Path
from random import Random

import pytest

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from llm import parse_health  # noqa: E402
from llm.model_config import LLMContext  # noqa: E402
from llm.parsing import extract_label, is_sentinel_line, match_enum  # noqa: E402
from engine.actor_simulation import _parse_actor_response  # noqa: E402
from engine.narrative_adjudication import _parse_quality_response  # noqa: E402
from engine.diplomacy import DiplomaticEncounter, assess_diplomatic_outcome  # noqa: E402
from engine.sim_loop import apply_inject_effects  # noqa: E402
from agents.conversation import (  # noqa: E402
    check_critical_omissions,
    generate_advisor_pushback,
    handle_player_question,
    interpret_player_action,
)
from cli.display_utils import parse_interpretation_simple  # noqa: E402
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


def make_narrative_state():
    from models.narrative_state import create_initial_narrative_state

    return create_initial_narrative_state(
        metrics=Metrics(escalation_risk=60, domestic_stability=50,
                        alliance_cohesion=40, casualties_mil=0,
                        casualties_civ=0),
        play_mode="classic", game_time="Turn 1",
    )


# --- registry: record_residue ------------------------------------------------

def test_record_residue_registers_and_zero_is_a_noop():
    parse_health.record_residue("some_component", 2, "first line")
    parse_health.record_residue("some_component", 1)
    parse_health.record_residue("other", 0)
    snap = parse_health.snapshot()
    assert snap["residue"] == {"some_component": 3}
    assert parse_health.total() == 3


# --- P1: pending structured fields + quoted sentinels ------------------------

def test_conditions_on_own_line_are_kept():
    r = _parse_actor_response("DEU", (
        "WILL_SUPPORT: conditional\n"
        "CONDITIONS:\n"
        "NATO consultation first; parliamentary approval\n"
    ))
    assert r.will_support == "conditional"
    assert r.conditions == ["NATO consultation first", "parliamentary approval"]


def test_intel_shared_on_own_line_is_kept():
    r = _parse_actor_response("USA", (
        "WILL_SUPPORT: yes\n"
        "INTEL_SHARED:\n"
        "Satellite imagery of the staging area\n"
    ))
    assert r.intel_shared == "Satellite imagery of the staging area"


def test_quoted_none_sentinel_means_no_intel():
    r = _parse_actor_response("USA", (
        "WILL_SUPPORT: yes\n"
        'CONDITIONS: None.\n'
        'INTEL_SHARED: "none"\n'
    ))
    assert r.conditions == []
    assert r.intel_shared is None


def test_trust_change_on_own_line_is_parsed():
    r = _parse_actor_response("USA", (
        "TRUST_CHANGE:\n"
        "-8 (a sharp fall)\n"
        "WILL_SUPPORT: no\n"
    ))
    assert r.trust_change == -8
    assert r.will_support == "no"


def test_extract_label_strips_symmetric_quotes_only():
    assert extract_label('INTEL_SHARED: "none"', "INTEL_SHARED") == "none"
    assert extract_label("CONDITIONS: 'none'", "CONDITIONS") == "none"
    # A quote inside the value is content, not decoration
    assert extract_label('SUMMARY: He said "no" today', "SUMMARY") == \
        'He said "no" today'


def test_is_sentinel_line_tolerates_quotes_and_trailing_period():
    assert is_sentinel_line('"none"', "none")
    assert is_sentinel_line("None.", "none")
    assert not is_sentinel_line("none of the conditions hold", "none")


def test_actor_residue_is_recorded():
    _parse_actor_response("USA", (
        "TRUST_CHANGE: -2\n"
        "WILL_SUPPORT: no\n"
        "Some stray commentary the parser cannot place.\n"
    ))
    assert parse_health.snapshot()["residue"] == {"actor_simulation": 1}


# --- P2: QUALITY via match_enum, pending fields, EFFECTS inline value --------

def test_quality_on_own_line_is_parsed():
    parsed = _parse_quality_response(
        "QUALITY:\n"
        "poor\n"
        "REASONING: Overreach.\n"
    )
    assert parsed["quality"] == "poor"
    assert parsed["multiplier"] == 0.5
    assert "Overreach." in parsed["reasoning"]


@pytest.mark.parametrize("value", [
    "**Poor** — hasty and escalatory",
    "poor (borderline)",
    "Poor — hasty",
])
def test_decorated_or_annotated_quality_resolves(value):
    parsed = _parse_quality_response(
        f"QUALITY: {value}\nREASONING: Weak.\nEFFECTS:\nescalation_risk: 2\n"
    )
    assert parsed["quality"] == "poor", value
    assert parsed["multiplier"] == 0.5


def test_quality_multiplier_on_own_line_is_parsed():
    parsed = _parse_quality_response(
        "QUALITY: poor\n"
        "REASONING: Weak.\n"
        "QUALITY MULTIPLIER:\n"
        "1.0\n"
    )
    assert parsed["multiplier"] == 1.0


def test_metric_value_on_own_line_is_parsed():
    parsed = _parse_quality_response(
        "QUALITY: adequate\n"
        "REASONING: Fine.\n"
        "EFFECTS:\n"
        "escalation_risk:\n"
        "+4\n"
        "alliance_cohesion: -2\n"
    )
    assert parsed["suggested_effects"] == {
        "escalation_risk": 4,
        "alliance_cohesion": -2,
    }


def test_effects_inline_value_is_not_discarded():
    parsed = _parse_quality_response(
        "QUALITY: adequate\n"
        "REASONING: Fine.\n"
        "EFFECTS: escalation_risk: -5\n"
    )
    assert parsed["suggested_effects"] == {"escalation_risk": -5}


def test_quality_residue_is_recorded():
    _parse_quality_response(
        "A paragraph of preamble the format never asked for.\n"
        "QUALITY: adequate\n"
        "REASONING: Fine.\n"
        "EFFECTS:\nescalation_risk: 1\n"
    )
    assert parse_health.snapshot()["residue"] == {"quality_assessment": 1}


# --- P5: OUTCOME pending + negation lookback ---------------------------------

def run_outcome(text):
    return assess_diplomatic_outcome(
        make_world(), "US",
        [("US President", "Well?"), ("UK PM", "We are sure.")],
        make_llm(text), Random(42)
    )


def test_outcome_on_own_line_is_parsed():
    assessment, delta = run_outcome(
        "OUTCOME:\n"
        "SUCCESS\n"
        "ALLIANCE_COHESION_DELTA: +8\n"
    )
    assert "SUCCESS" in assessment
    assert delta == 8
    assert "diplomacy_outcome.outcome" not in parse_health.snapshot()["misses"]


def test_not_a_failure_is_not_read_as_failure():
    assessment, delta = run_outcome(
        "OUTCOME: Not a failure, all told\n"
        "ALLIANCE_COHESION_DELTA: 0\n"
        "SUMMARY: The channel stays open.\n"
    )
    assert "FAILURE" not in assessment
    assert "NEUTRAL" in assessment


def test_match_enum_negation_lookback_both_directions():
    allowed = ("SUCCESS", "NEUTRAL", "FAILURE")
    # A negator a couple of words back negates the token...
    assert match_enum("Not a failure", allowed) is None
    assert match_enum("not quite a success", allowed) is None
    # ...without breaking plain and decorated matches...
    assert match_enum("FAILURE", allowed) == "FAILURE"
    assert match_enum("**failure**", allowed) == "FAILURE"
    # ...and without breaking the refusal_value priority.
    assert match_enum("no, we will not assist",
                      ("yes", "no", "conditional"), refusal_value="no") == "no"
    assert match_enum("we will not support this action",
                      ("yes", "no", "conditional"), refusal_value="no") == "no"
    assert match_enum("Yes, with conditions attached",
                      ("yes", "no", "conditional"), refusal_value="no") == "yes"


def test_diplomacy_residue_is_recorded():
    run_outcome(
        "Let me reflect first.\n"
        "OUTCOME: NEUTRAL\n"
        "ALLIANCE_COHESION_DELTA: 0\n"
        "SUMMARY: Fine.\n"
    )
    assert parse_health.snapshot()["residue"] == {"diplomacy_outcome": 1}


# --- P9: a leading sentinel accepts only bounded absence rationale ----------


@pytest.mark.parametrize("sentinel", ["NO PUSHBACK", "**NO PUSHBACK**",
                                      "no pushback."])
def test_standalone_no_pushback_still_returns_empty(sentinel):
    result = generate_advisor_pushback(
        make_world(), "hold position", "Hold.",
        INITIAL_CONDITIONS, make_llm(sentinel), Random(42)
    )
    assert result == []


def test_empty_pushback_message_is_recorded_and_visible():
    result = generate_advisor_pushback(
        make_world(), "hold position", "Hold.",
        INITIAL_CONDITIONS, make_llm(""), Random(42)
    )
    assert len(result) == 5
    assert all("unavailable" in message.lower() for _, message in result)
    assert parse_health.snapshot()["fallbacks"] == {"advisor_pushback": 5}


# --- P10: an empty omissions reply is not an all-clear -----------------------

def test_empty_omissions_reply_is_recorded_not_all_clear():
    result = check_critical_omissions(
        make_world(), "deploy into the Barents", "Deployment north.",
        INITIAL_CONDITIONS, make_llm(""), Random(42)
    )
    assert result == []
    # All five scanning advisors returned nothing: five recorded misses.
    assert parse_health.snapshot()["misses"] == {
        "critical_omissions.empty_reply": 5
    }


def test_genuine_no_concern_sentinel_records_nothing():
    result = check_critical_omissions(
        make_world(), "deploy into the Barents", "Deployment north.",
        INITIAL_CONDITIONS, make_llm("NO_CONCERN"), Random(42)
    )
    assert result == []
    assert parse_health.snapshot()["misses"] == {}


# --- P11: INTERPRETATION on its own line + FEASIBILITY continuation ----------

def test_interpretation_summary_below_bare_label_is_kept():
    parsed = parse_interpretation_simple(
        "INTERPRETATION:\n"
        "Deploy two Type-45s to the North Sea under NATO command.\n"
        "FORCES INVOLVED: Type-45 destroyers\n"
    )
    assert parsed["summary"] == \
        "Deploy two Type-45s to the North Sea under NATO command."
    assert parsed["forces"] == ["Type-45 destroyers"]


def test_feasibility_wrapped_clause_is_captured():
    parsed = parse_interpretation_simple(
        "INTERPRETATION: Deploy the destroyers.\n"
        "FEASIBILITY: Requires\n"
        "clarification on the rules of engagement.\n"
    )
    assert parsed.get("feasibility") == \
        "Requires clarification on the rules of engagement."
    assert parsed["concerns"] == \
        "Requires clarification on the rules of engagement."


def test_interpretation_resources_are_parsed_as_a_list():
    parsed = parse_interpretation_simple(
        "INTERPRETATION: Sustain maritime patrols.\n"
        "FORCES INVOLVED: P-8 patrols\n"
        "RESOURCES CONSUMED: aviation fuel, sonobuoys\n"
        "TIMELINE: Within six hours\n"
        "FEASIBILITY: Feasible at current readiness\n"
    )
    assert parsed.get("resources") == ["aviation fuel", "sonobuoys"]


def test_interpretation_list_continuations_require_list_markers():
    parsed = parse_interpretation_simple(
        "FORCES INVOLVED: Type-45 destroyer\n"
        "This explanatory sentence is not another force.\n"
        "- P-8 patrol\n"
        "2. Type 23 frigate: screen the group\n"
        "RESOURCES CONSUMED: aviation fuel\n"
        "This explanatory sentence is not another resource.\n"
        "* sonobuoys\n"
        "2) runway slots\n"
        "TIMELINE: Within six hours\n"
    )

    assert parsed["forces"] == [
        "Type-45 destroyer", "P-8 patrol", "Type 23 frigate"]
    assert parsed["resources"] == [
        "aviation fuel", "sonobuoys", "runway slots"]
    assert parse_health.snapshot()["residue"] == {
        "decision_interpretation": 2}


def test_interpretation_list_fields_are_not_capped():
    forces = ["force-1", "force-2", "force-3",
              "force-4", "force-5", "force-6"]
    resources = ["resource-1", "resource-2", "resource-3",
                 "resource-4", "resource-5", "resource-6"]

    parsed = parse_interpretation_simple(
        f"FORCES INVOLVED: {', '.join(forces)}\n"
        f"RESOURCES CONSUMED: {', '.join(resources)}\n"
    )

    assert parsed["forces"] == forces
    assert parsed["resources"] == resources


def test_decision_summary_keeps_the_cli_panel_to_five_forces(monkeypatch):
    from io import StringIO

    from rich.console import Console
    from cli import display_utils

    output = StringIO()
    monkeypatch.setattr(
        display_utils,
        "console",
        Console(file=output, width=120, force_terminal=False),
    )
    forces = ["force-1", "force-2", "force-3",
              "force-4", "force-5", "force-6"]

    display_utils.display_decision_summary(
        "Test decision",
        f"FORCES INVOLVED: {', '.join(forces)}",
    )

    rendered = output.getvalue()
    assert all(force in rendered for force in forces[:5])
    assert forces[5] not in rendered


@pytest.mark.parametrize("sentinel", ["None", "None specified"])
def test_interpretation_list_sentinels_are_empty(sentinel):
    parsed = parse_interpretation_simple(
        f"FORCES INVOLVED: {sentinel}\n"
        f"RESOURCES CONSUMED: {sentinel}\n"
    )
    assert parsed["forces"] == []
    assert parsed.get("resources") == []


def test_malformed_interpretation_has_empty_field_fallbacks():
    parsed = parse_interpretation_simple("Unlabelled model reply")
    assert parsed["forces"] == []
    assert parsed.get("resources") == []
    assert parsed["timeline"] == ""
    assert parsed.get("feasibility") == ""


# --- P3/P4: situation summary + character responses record fallbacks ---------

def test_empty_situation_summary_records_fallback():
    from engine.narrative_adjudication import compute_situation_summary

    out = compute_situation_summary(
        make_narrative_state(), "hold position", make_llm(""), Random(1))
    assert out is None
    assert parse_health.snapshot()["fallbacks"] == {"situation_summary": 1}


def test_empty_character_response_records_fallback():
    from engine.narrative_adjudication import generate_character_responses

    responses = generate_character_responses(
        "hold position", {"quality": "adequate"}, {},
        make_narrative_state(), make_llm(""), Random(1))
    assert responses
    for _name, text in responses:
        assert "Understood, Prime Minister." in text
    fallbacks = parse_health.snapshot()["fallbacks"]
    assert fallbacks.get("character_response", 0) == len(responses)


# --- P6: diplomatic conversation empty-reply guard ---------------------------

def test_diplomatic_conversation_empty_reply_gets_canned_line():
    encounter = DiplomaticEncounter(make_world(), "US", None)
    encounter.start(Random(1))
    assert encounter.active
    transcript = encounter.process_turn(
        "We need your commitment.", make_llm(""), Random(1))
    assert any("Forgive me, Prime Minister" in line for line in transcript)
    assert parse_health.snapshot()["fallbacks"].get(
        "diplomacy_conversation", 0) >= 1


def test_diplomatic_conversation_error_slot_gets_canned_line():
    encounter = DiplomaticEncounter(make_world(), "US", None)
    encounter.start(Random(1))
    transcript = encounter.process_turn(
        "We need your commitment.", make_llm("[ERROR: HTTP 500]"), Random(1))
    assert not any("[ERROR:" in line for line in transcript)
    assert any("Forgive me, Prime Minister" in line for line in transcript)


# --- P7/P8: advisor QA + interpretation record their failures ----------------

def test_advisor_qa_empty_reply_stays_in_fiction():
    responses = handle_player_question(
        make_world(), "What is the military assessment?",
        INITIAL_CONDITIONS, make_llm(""), Random(42))
    assert responses
    for role, text in responses:
        assert role != "System"
        assert "Prime Minister" in text
    assert parse_health.snapshot()["fallbacks"].get("advisor_qa", 0) >= 1


def test_advisor_qa_exception_stays_in_fiction():
    def boom(prompt, rng, **kwargs):
        raise RuntimeError("provider down")

    responses = handle_player_question(
        make_world(), "What is the military assessment?",
        INITIAL_CONDITIONS, boom, Random(42))
    assert responses
    for role, text in responses:
        assert role != "System"
        assert "Error" not in text
    assert parse_health.snapshot()["fallbacks"].get("advisor_qa", 0) >= 1


def test_empty_interpretation_records_fallback():
    out = interpret_player_action(
        make_world(), "do the thing", INITIAL_CONDITIONS,
        make_llm(""), Random(42))
    assert out == ""
    assert parse_health.snapshot()["fallbacks"] == {
        "decision_interpretation": 1}


# --- P13: unknown metric names are recorded ----------------------------------

def test_unknown_metric_is_recorded():
    world = make_world()
    lines = apply_inject_effects(
        world, {"effects": [{"metric": "public_morale", "delta": 5}]})
    assert "Skipped: unknown metric 'public_morale'" in lines
    assert parse_health.snapshot()["misses"] == {
        "inject_effects.public_morale": 1}


# --- P14: inject YAML fence + schema + fallback records ----------------------

def _gen_inject(monkeypatch, reply):
    import llm.inject_generator as ig

    monkeypatch.setattr(ig, "generate_text",
                        lambda prompt, rng, **kwargs: reply)
    world = make_world()
    world.turn = 4
    return ig.generate_inject(world, 4, INITIAL_CONDITIONS, Random(1))


def test_unclosed_yaml_fence_takes_the_rest_of_the_reply(monkeypatch):
    inject = _gen_inject(monkeypatch, (
        "```yaml\n"
        "title: Convoy shadowed\n"
        "description: A tanker is shadowed through the North Sea.\n"
    ))  # note: no closing fence
    assert inject is not None
    assert inject["title"] == "Convoy shadowed"
    assert inject["description"].endswith("North Sea.")


def test_inject_missing_title_or_description_is_a_recorded_fallback(monkeypatch):
    inject = _gen_inject(monkeypatch, "```yaml\ntitle: Only a title\n```")
    assert inject is None
    assert parse_health.snapshot()["fallbacks"] == {"inject_generation": 1}


def test_inject_empty_reply_is_a_recorded_fallback(monkeypatch):
    assert _gen_inject(monkeypatch, "") is None
    assert parse_health.snapshot()["fallbacks"] == {"inject_generation": 1}


def test_inject_non_mapping_is_a_recorded_fallback(monkeypatch):
    assert _gen_inject(monkeypatch, "- just\n- a\n- list\n") is None
    assert parse_health.snapshot()["fallbacks"] == {"inject_generation": 1}


# --- P15: narrator records its silent drops ----------------------------------

def test_narrator_empty_reply_records_fallback(monkeypatch):
    import engine.narrator as narrator

    monkeypatch.setattr(narrator, "generate_text",
                        lambda *args, **kwargs: "")
    out = narrator.generate_narrator_bridge(
        make_world(), ["line"] * 6, "Next inject", Random(1))
    assert out == ""
    assert parse_health.snapshot()["fallbacks"] == {"narrator": 1}


def test_narrator_exception_records_fallback(monkeypatch):
    import engine.narrator as narrator

    def boom(*args, **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(narrator, "generate_text", boom)
    out = narrator.generate_narrator_bridge(
        make_world(), ["line"] * 6, "Next inject", Random(1))
    assert "Time passes" in out
    assert parse_health.snapshot()["fallbacks"] == {"narrator": 1}


# --- P19: fanout records its empty slots -------------------------------------

def test_fanout_sequential_failure_records_fallback_per_slot():
    from llm.fanout import generate_group

    def boom(prompt, rng, **kwargs):
        raise RuntimeError("provider down")

    out = generate_group(["a", "b"], boom, Random(1),
                         context=LLMContext.CRITICAL_OMISSIONS)
    assert out == ["", ""]
    assert parse_health.snapshot()["fallbacks"] == {"critical_omissions": 2}


def test_fanout_short_batch_records_fallback_per_padded_slot():
    from llm.fanout import generate_group

    def short_batch(prompts, rng, **kwargs):
        return ["only one"]

    out = generate_group(["a", "b", "c"], make_llm("x"), Random(1),
                         llm_batch_fn=short_batch,
                         context=LLMContext.ACTOR_SIMULATION)
    assert out == ["only one", "", ""]
    assert parse_health.snapshot()["fallbacks"] == {"actor_simulation": 2}


# --- P17: the discussion stream recognises the real advisor roster -----------

def test_discussion_stream_roster_matches_real_advisor_names():
    pytest.importorskip("fastapi")
    pytest.importorskip("sse_starlette")
    from api.server import classify_discussion_line

    msg_type, role, content = classify_discussion_line(
        "Military Commander: We can deploy within six hours.")
    assert (msg_type, role) == ("advisor", "Military Commander")
    assert content == "We can deploy within six hours."

    # Decorated prefixes classify too
    msg_type, role, _content = classify_discussion_line(
        "**Intelligence Coordinator:** Signals confirm the contact.")
    assert (msg_type, role) == ("advisor", "Intelligence Coordinator")

    # Non-speaker lines stream as narrator text, unchanged
    line = "The morning briefing begins."
    assert classify_discussion_line(line) == ("narrator", None, line)


# --- P20: the interpretation must not reach foreign leaders ------------------

def test_interpretation_is_excluded_from_diplomatic_context():
    from engine.decision_phase import format_decision_transcript
    from llm.context_builder import get_diplomatic_context

    interpretation = (
        "INTERPRETATION: Deploy two Type-45s to the North Sea under NATO "
        "command.\nFORCES INVOLVED: Type-45 destroyers"
    )
    entries = format_decision_transcript(
        "Shadow the vessel", interpretation,
        [("Military Commander", "The approaches are uncovered.")], [])
    context = get_diplomatic_context(entries, make_world(), "us")
    assert "Type-45" not in context
    assert "Deploy two" not in context
    assert "approaches are uncovered" not in context
