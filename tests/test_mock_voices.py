"""Tests for the mock driver's per-advisor voices and display helpers.

Covers the playtest defects around mock-mode identity collapse:
- each advisor answers in their own voice (no shared canned line);
- variant selection is deterministic per question but varies across questions;
- post-decision reactions reference the assessed action quality;
- international actors return structured, per-country responses instead of
  "<ISO> acknowledges the action";
- ISO codes map to player-facing country names;
- markdown emphasis converts to Rich markup instead of leaking asterisks;
- vibes render with themed glyphs, not emoji.
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
