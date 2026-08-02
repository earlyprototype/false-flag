"""Tests for the mock driver's per-advisor voices and display helpers.

Covers the playtest defects around mock-mode identity collapse:
- each advisor answers in their own voice (no shared canned line);
- variant selection is deterministic per question but varies across questions;
- post-decision reactions reference the assessed action quality;
- international actors return structured, per-country responses instead of
  "<ISO> acknowledges the action";
- ISO codes map to player-facing country names;
- markdown emphasis converts to Rich markup instead of leaking asterisks;
- vibes render with themed glyphs, not emoji;
- foreign leaders on /call speak with distinct national voices and react to
  the shape of the PM's ask (troops vs statement vs support);
- Mystery mode narratives colour mock output with subtle deterministic tells
  (present under the matching narrative, absent otherwise).
"""

from pathlib import Path
from random import Random

import pytest

from llm.mock_driver import MockDeterministicDriver
from engine.actor_simulation import display_country_name, simulate_actor_response
from cli.display_utils import markdown_to_rich, format_vibe_line, parse_interpretation_simple
from models.narrative_state import VibeLevel

ROOT = Path(__file__).resolve().parents[1]
RNG = Random(42)


def _qa_prompt(role: str, question: str) -> str:
    """Minimal replica of build_advisor_context's persona framing, including
    the cross-advisor context that used to collapse every voice into one."""
    return (
        f"You are the {role} in a UK government COBRA meeting during a crisis.\n"
        "\n"
        "Context: the Chief of the Defence Staff, National Security Advisor, "
        "Foreign Secretary, Home Secretary and Attorney General are present.\n"
        "\n"
        f'The Prime Minister asks: "{question}"\n'
        "\n"
        "Your response:"
    )


def _reaction_prompt(name: str, quality: str) -> str:
    """Minimal replica of the adjudication character-reaction prompt."""
    return (
        "Character Relationships:\n"
        "- Chief of the Defence Staff: ALLIED\n"
        "- Foreign Secretary: ALLIED\n"
        "\n"
        "PLAYER ACTION: Deploy destroyers and call NATO\n"
        f"ACTION QUALITY: {quality}\n"
        "\n"
        f"You are {name}.\n"
        "Respond to the PM's action.\n"
        "\n"
        "Response:"
    )


def test_mock_advisors_have_distinct_voices():
    driver = MockDeterministicDriver()
    question = "What are our options?"
    roles = {
        "Military Commander": "military",
        "Intelligence Coordinator": "intelligence",
        "Diplomatic Lead": "diplomatic",
        "Domestic Security": "domestic",
        "Legal Advisor": "legal",
    }
    responses = {
        role: driver.generate_text(_qa_prompt(role, question), RNG)
        for role in roles
    }
    # All five advisors must produce different answers to the same question
    assert len(set(responses.values())) == len(roles), (
        "Advisor voices collapsed: " + repr(responses)
    )


def test_mock_variant_selection_deterministic_and_varies():
    driver = MockDeterministicDriver()
    role = "Military Commander"

    # Same question twice -> identical answer (deterministic)
    first = driver.generate_text(_qa_prompt(role, "What are our options?"), RNG)
    second = driver.generate_text(_qa_prompt(role, "What are our options?"), RNG)
    assert first == second

    # Across many different questions the advisor uses more than one variant
    questions = [f"Question number {i}, what do you advise?" for i in range(12)]
    answers = {driver.generate_text(_qa_prompt(role, q), RNG) for q in questions}
    assert len(answers) > 1, "Repeated questions never vary the canned response"


def test_mock_reactions_follow_action_quality():
    driver = MockDeterministicDriver()
    name = "Foreign Secretary"
    good = driver.generate_text(_reaction_prompt(name, "good"), RNG)
    adequate = driver.generate_text(_reaction_prompt(name, "adequate"), RNG)
    poor = driver.generate_text(_reaction_prompt(name, "poor"), RNG)

    assert len({good, adequate, poor}) == 3, "Reaction tone ignores action quality"
    # Reactions must differ from the Q&A voice and stay in character
    qa = driver.generate_text(_qa_prompt("Diplomatic Lead", "Status?"), RNG)
    assert good != qa

    # Different advisors react differently to the same quality
    cds = driver.generate_text(_reaction_prompt("Chief of the Defence Staff", "good"), RNG)
    assert cds != good


def test_mock_actor_simulation_per_country_responses():
    from models.state_actors import load_actors_from_yaml

    system = load_actors_from_yaml(str(ROOT / "data" / "state_actors.yaml"))
    driver = MockDeterministicDriver()

    responses = {}
    for code in ["USA", "POL", "DEU", "RUS"]:
        actor = system.get_actor(code)
        assert actor is not None
        response = simulate_actor_response(
            actor, "Deploy destroyers and call NATO", "World context here.",
            driver.generate_text, RNG
        )
        responses[code] = response
        # The structured mock response must parse: no generic fallback line
        assert response.public_response != f"{code} acknowledges the action."
        assert response.will_support in ("yes", "no", "conditional")

    # Countries answer differently, and Russia is hostile
    publics = {r.public_response for r in responses.values()}
    assert len(publics) == len(responses)
    assert responses["RUS"].will_support == "no"
    assert responses["RUS"].trust_change < 0


def test_country_display_names():
    assert display_country_name("POL") == "Poland"
    assert display_country_name("USA") == "United States"
    assert display_country_name("DEU") == "Germany"
    # Unknown codes pass through unchanged
    assert display_country_name("XYZ") == "XYZ"


def test_markdown_to_rich_conversion():
    assert markdown_to_rich("**GCHQ Assessment:**") == "[bold]GCHQ Assessment:[/bold]"
    assert markdown_to_rich("plain text") == "plain text"
    converted = markdown_to_rich("We must act **immediately** and *carefully*.")
    assert "**" not in converted
    assert "[bold]immediately[/bold]" in converted
    assert "[italic]carefully[/italic]" in converted
    # A lone bullet asterisk is not italicised
    assert markdown_to_rich("* bullet item") == "* bullet item"


def test_vibes_use_themed_glyphs_not_emoji():
    vibe = VibeLevel(name="Crisis Intensity", level=3, trend="rising", descriptor="ELEVATED")
    visual = vibe.to_visual()
    assert visual == "●●●○○"
    assert "🔴" not in vibe.to_string() and "⚪" not in vibe.to_string()

    colors = {"danger": "red", "warning": "yellow", "success": "green", "muted": "dim"}
    line = format_vibe_line(vibe, colors)
    assert "●●●" in line and "○○" in line
    assert "ELEVATED" in line and "↗" in line


def test_parse_interpretation_handles_inline_fields():
    interpretation = (
        "INTERPRETATION: Deploy destroyers and call NATO\n"
        "FORCES INVOLVED: Type-45 destroyers, combat air patrols, P-8 reconnaissance\n"
        "RESOURCES CONSUMED: Minimal (patrol operations)\n"
        "TIMELINE: Immediate (within 1 turn)\n"
        "FEASIBILITY: Feasible within current constraints"
    )
    parsed = parse_interpretation_simple(interpretation)
    assert parsed["summary"] == "Deploy destroyers and call NATO"
    assert parsed["forces"] == ["Type-45 destroyers", "combat air patrols", "P-8 reconnaissance"]
    assert parsed["timeline"] == "Immediate (within 1 turn)"

    # Unstructured text parses to nothing (display falls back to raw text)
    empty = parse_interpretation_simple("The PM's plan is broadly sensible.")
    assert not any([empty["summary"], empty["forces"], empty["timeline"], empty["concerns"]])


# --- Diplomatic call voices (/call) -----------------------------------------

from models.world import WorldState, Metrics


def _world(narrative=None):
    return WorldState(
        turn=2, scene=2,
        metrics=Metrics(escalation_risk=60, domestic_stability=50,
                        alliance_cohesion=70),
        flags={}, posture={}, narrative=narrative,
    )


def _narratives():
    from engine.scenario_loader import load_narrative_configs
    return {c.narrative_id: c for c in load_narrative_configs("war_game_2025", ROOT)}


def _diplo_prompt(country, message, world=None, level="leader", transcript=None):
    """Build the real diplomacy conversation prompt for a country/level."""
    from engine.diplomacy import build_diplomatic_conversation_prompt, load_diplomatic_profiles

    profiles = load_diplomatic_profiles(ROOT)
    profile = profiles["countries"][country][level]
    return build_diplomatic_conversation_prompt(
        world or _world(), country, profile, [], message,
        full_transcript=transcript,
    )


_GENERIC_FALLBACK = "Understood, Prime Minister. I'll provide my assessment based on the current situation."


def test_mock_diplomacy_leaders_have_distinct_voices():
    driver = MockDeterministicDriver()
    message = "Talk me through where your government stands right now."
    countries = ["Ireland", "US", "France", "Germany", "Poland"]
    responses = {
        c: driver.generate_text(_diplo_prompt(c, message), RNG)
        for c in countries
    }
    assert len(set(responses.values())) == len(countries), (
        "Leader voices collapsed: " + repr(responses)
    )
    for country, response in responses.items():
        assert response != _GENERIC_FALLBACK, f"{country} fell back to the generic line"


def test_mock_diplomacy_deterministic_and_varies():
    driver = MockDeterministicDriver()
    message = "Give me your honest read of the situation."

    first = driver.generate_text(_diplo_prompt("Ireland", message), RNG)
    second = driver.generate_text(_diplo_prompt("Ireland", message), RNG)
    assert first == second

    messages = [f"Message number {i} about the situation." for i in range(12)]
    answers = {driver.generate_text(_diplo_prompt("Ireland", m), RNG) for m in messages}
    assert len(answers) > 1, "Leader never varies the canned response"


def test_mock_diplomacy_reacts_to_common_asks():
    from llm import mock_driver

    driver = MockDeterministicDriver()

    # Ireland asked for military assets invokes neutrality constraints
    irl = driver.generate_text(
        _diplo_prompt("Ireland", "Can you send troops and open your ports to the Royal Navy?"),
        RNG)
    assert irl in mock_driver._DIPLOMACY_VOICES["ireland"]["military"]

    # Poland asked for military assets leans forward with basing
    pol = driver.generate_text(
        _diplo_prompt("Poland", "We need basing and airfields for allied aircraft."),
        RNG)
    assert pol in mock_driver._DIPLOMACY_VOICES["poland"]["military"]
    assert "airfields" in pol.lower()

    # The US hedges when asked for commitment
    usa = driver.generate_text(
        _diplo_prompt("US", "Will you commit to Article 5? We need America to stand with us."),
        RNG)
    assert usa in mock_driver._DIPLOMACY_VOICES["us"]["support"]


def test_mock_diplomacy_unknown_country_uses_default_diplomat():
    from engine.diplomacy import build_diplomatic_conversation_prompt
    from llm import mock_driver

    driver = MockDeterministicDriver()
    prompt = build_diplomatic_conversation_prompt(
        _world(), "Atlantis", {"title": "Foreign Minister"}, [],
        "Where does your government stand?")
    response = driver.generate_text(prompt, RNG)
    assert response in mock_driver._DIPLOMACY_DEFAULT["general"]
    assert response != _GENERIC_FALLBACK


def test_mock_diplomacy_outcome_assessment_is_structured():
    from engine.diplomacy import assess_diplomatic_outcome

    driver = MockDeterministicDriver()

    def llm(prompt, rng, **kwargs):
        return driver.generate_text(prompt, rng)

    assessment, delta = assess_diplomatic_outcome(
        _world(), "Ireland",
        [("Taoiseach", "Hello."), ("Prime Minister", "Thank you.")],
        llm, Random(42))
    assert "NEUTRAL" in assessment
    assert delta == 0


# --- Mystery mode tells ------------------------------------------------------

_TRANSCRIPT = [f"TURN 1 line {i}" for i in range(12)]
_PROBE_MESSAGES = [f"Tell me candidly, item {i}, how you read this." for i in range(10)]


def _diplo_responses(narrative):
    driver = MockDeterministicDriver()
    world = _world(narrative)
    return [
        driver.generate_text(
            _diplo_prompt("France", m, world=world, transcript=_TRANSCRIPT), RNG)
        for m in _PROBE_MESSAGES
    ]


def test_narrative_reaches_diplomacy_prompt():
    narratives = _narratives()
    prompt = _diplo_prompt("France", "Where do you stand?",
                           world=_world(narratives["CHINA_PROXY_WAR"]),
                           transcript=_TRANSCRIPT)
    assert "SECRET NARRATIVE CONTEXT" in prompt
    assert "Crisis Protagonist: CHN" in prompt
    # Without a transcript the prompt must not crash, just omit the context
    bare = _diplo_prompt("France", "Where do you stand?")
    assert "SECRET NARRATIVE CONTEXT" not in bare


def test_diplomacy_tells_differ_by_narrative():
    narratives = _narratives()

    china = " ".join(_diplo_responses(narratives["CHINA_PROXY_WAR"]))
    russia = " ".join(_diplo_responses(narratives["RUSSIA_AGGRESSION"]))
    plain = " ".join(_diplo_responses(None))

    assert "Beijing" in china, "China-proxy runs must hint at Beijing's silence"
    assert "Beijing" not in russia
    assert "Moscow's hand" in russia, "Russia runs keep tells conventional"
    assert "Beijing" not in plain and "Moscow's hand" not in plain


def test_diplomacy_tells_are_deterministic():
    narratives = _narratives()
    first = _diplo_responses(narratives["CHINA_PROXY_WAR"])
    second = _diplo_responses(narratives["CHINA_PROXY_WAR"])
    assert first == second


def test_russian_ambassador_never_helps_with_attribution():
    driver = MockDeterministicDriver()
    narratives = _narratives()
    world = _world(narratives["CHINA_PROXY_WAR"])
    responses = [
        driver.generate_text(
            _diplo_prompt("Russia", m, world=world, level="diplomat",
                          transcript=_TRANSCRIPT), RNG)
        for m in _PROBE_MESSAGES
    ]
    assert all("Beijing" not in r for r in responses)


def _advisor_responses(narrative, character_id="national_security_advisor"):
    from llm.prompts import build_advisor_context

    driver = MockDeterministicDriver()
    world = _world(narrative)
    conditions = {
        "characters": {
            "national_security_advisor": {"role": "Intelligence Coordinator"},
            "foreign_secretary": {"role": "Diplomatic Lead"},
        }
    }
    return [
        driver.generate_text(
            build_advisor_context(world, conditions, character_id, q, _TRANSCRIPT),
            RNG)
        for q in _PROBE_MESSAGES
    ]


def test_advisor_tells_differ_by_narrative():
    narratives = _narratives()

    china = " ".join(_advisor_responses(narratives["CHINA_PROXY_WAR"]))
    russia = " ".join(_advisor_responses(narratives["RUSSIA_AGGRESSION"]))
    plain = " ".join(_advisor_responses(None))

    # Intelligence answers point east under the China proxy narrative...
    assert "Hong Kong" in china
    # ...stay conventional under Russia aggression...
    assert "Hong Kong" not in russia
    assert "GRU tradecraft" in russia
    # ...and carry no tells at all outside Mystery mode
    assert "Hong Kong" not in plain and "GRU tradecraft" not in plain


def test_foreign_secretary_notes_beijing_quietness_under_china_proxy():
    narratives = _narratives()
    china = " ".join(_advisor_responses(narratives["CHINA_PROXY_WAR"],
                                        character_id="foreign_secretary"))
    plain = " ".join(_advisor_responses(None, character_id="foreign_secretary"))
    assert "Beijing" in china
    assert "Beijing" not in plain


def test_actor_simulation_tells_under_china_proxy():
    from models.state_actors import load_actors_from_yaml

    narratives = _narratives()
    system = load_actors_from_yaml(str(ROOT / "data" / "state_actors.yaml"))
    driver = MockDeterministicDriver()

    def responses_for(code, narrative):
        actor = system.get_actor(code)
        context = "World context here."
        if narrative:
            context += "\n" + narrative.to_llm_context()
        return [
            simulate_actor_response(
                actor, f"Action {i}: consult allies.", context,
                driver.generate_text, RNG).public_response
            for i in range(10)
        ]

    usa_china = " ".join(responses_for("USA", narratives["CHINA_PROXY_WAR"]))
    usa_plain = " ".join(responses_for("USA", None))
    rus_china = " ".join(responses_for("RUS", narratives["CHINA_PROXY_WAR"]))

    assert "Beijing" in usa_china
    assert "Beijing" not in usa_plain
    assert "Beijing" not in rus_china, "Russia's actor responses stay on script"


def test_inject_tells_present_and_yaml_stays_valid():
    import yaml as yaml_lib
    from llm.prompts import build_inject_generation_prompt

    narratives = _narratives()
    driver = MockDeterministicDriver()

    def inject_for(narrative):
        world = _world(narrative)
        prompt = build_inject_generation_prompt(world, 2, {}, None, _TRANSCRIPT)
        raw = driver.generate_text(prompt, RNG)
        body = raw.strip().removeprefix("```yaml").removesuffix("```")
        return yaml_lib.safe_load(body)

    china = inject_for(narratives["CHINA_PROXY_WAR"])
    russia = inject_for(narratives["RUSSIA_AGGRESSION"])
    plain = inject_for(None)

    assert "Hong Kong" in china["description"]
    assert "Hong Kong" not in russia["description"]
    assert "Northern Fleet planning signatures" in russia["description"]
    assert "Hong Kong" not in plain["description"]
    assert "planning signatures" not in plain["description"]


def test_mock_pushback_scoped_to_decision_text():
    driver = MockDeterministicDriver()
    base = (
        "You are simulating UK government advisors responding to a Prime Minister's decision.\n"
        "Context: carrier HMS Prince of Wales listed in force tables; deployment levels elevated.\n"
        'The PM has decided: "{action}"\n'
        "Advisors and their pushback triggers:\n"
        "- Chief of the Defence Staff: carrier readiness\n"
    )
    # Context mentions carrier/deploy, but the decision itself is benign
    benign = driver.generate_text(base.format(action="Open a diplomatic channel."), RNG)
    assert benign.strip() == "NO PUSHBACK"

    # Decision actually surging the carrier triggers the CDS warning
    carrier = driver.generate_text(base.format(action="Deploy the carrier group now."), RNG)
    assert "Prince of Wales" in carrier


def test_decision_extraction_survives_embedded_quotes():
    """A decision containing double quotes must not be truncated at the
    first embedded quote by the interpretation/pushback extractors."""
    from llm.mock_driver import MockDeterministicDriver
    from random import Random

    driver = MockDeterministicDriver()
    action = 'Tell the ally "stand by"; prepare a nuclear strike option'
    interp = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        Random(1))
    assert "stand by" in interp and "nuclear strike option" in interp
    pushback = driver.generate_text(
        f'Check pushback triggers. THE PM HAS DECIDED: "{action}"\n', Random(1))
    # 'nuclear' sits after the embedded quote - truncation would miss it
    assert "NO PUSHBACK" not in pushback
