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
        "Your knowledge domains: test domain\n"
        "\n"
        "Context: the Chief of the Defence Staff, National Security Advisor, "
        "Foreign Secretary, Home Secretary and Attorney General are present.\n"
        "\n"
        f'The Prime Minister asks: "{question}"\n'
        "\n"
        f"Respond in character as the {role}.\n"
        "\n"
        "Your response:\n"
        "\n"
        f"[ADVISOR ROLE: {role}]"
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
        "Your relationship with the PM: ALLIED\n"
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


def _parse_inject_yaml(raw):
    """Parse the fenced YAML an inject response is wrapped in."""
    import yaml as yaml_lib

    body = raw.strip().removeprefix("```yaml").removesuffix("```")
    data = yaml_lib.safe_load(body)
    assert isinstance(data, dict), f"inject did not parse as a mapping: {raw[:200]}"
    return data


def _inject_for(narrative, seed=42):
    """One generated inject for the given hidden narrative (or None)."""
    from llm.prompts import build_inject_generation_prompt

    driver = MockDeterministicDriver()
    prompt = build_inject_generation_prompt(_world(narrative), 2, {}, None,
                                            _TRANSCRIPT)
    return _parse_inject_yaml(driver.generate_text(prompt, Random(seed)))


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


def test_advisor_prompts_and_output_are_secret_free():
    """Advisors never see the narrative, so mock answers carry no tells.

    Deduction now runs on faction behaviour (diplomacy and actor lanes,
    covered above) - the cabinet is honestly ignorant of the hidden truth.
    """
    from llm.prompts import build_advisor_context

    narratives = _narratives()
    world = _world(narratives["CHINA_PROXY_WAR"])
    conditions = {"characters": {
        "national_security_advisor": {"role": "Intelligence Coordinator"}}}
    prompt = build_advisor_context(world, conditions,
                                   "national_security_advisor",
                                   "Who is behind this?", _TRANSCRIPT)
    assert "SECRET NARRATIVE CONTEXT" not in prompt
    assert "GLOBAL TRUTH" not in prompt

    china = " ".join(_advisor_responses(narratives["CHINA_PROXY_WAR"]))
    russia = " ".join(_advisor_responses(narratives["RUSSIA_AGGRESSION"]))
    assert "Hong Kong" not in china and "GRU tradecraft" not in china
    assert "Hong Kong" not in russia and "GRU tradecraft" not in russia


def test_foreign_secretary_carries_no_tells_either():
    narratives = _narratives()
    china = " ".join(_advisor_responses(narratives["CHINA_PROXY_WAR"],
                                        character_id="foreign_secretary"))
    assert "Beijing" not in china


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


def test_injects_are_secret_free_and_yaml_stays_valid():
    """Inject prompts carry no narrative, so no tells - and still parse."""
    from llm.prompts import build_inject_generation_prompt

    narratives = _narratives()
    prompt = build_inject_generation_prompt(
        _world(narratives["CHINA_PROXY_WAR"]), 2, {}, None, _TRANSCRIPT)
    assert "SECRET NARRATIVE CONTEXT" not in prompt
    assert "GLOBAL TRUTH" not in prompt

    china = _inject_for(narratives["CHINA_PROXY_WAR"])
    russia = _inject_for(narratives["RUSSIA_AGGRESSION"])
    plain = _inject_for(None)

    for inject in (china, russia, plain):
        assert inject["description"], "inject must still render a body"
    assert "Hong Kong" not in china["description"]
    assert "planning signatures" not in russia["description"]
    assert "Attribution note" not in china["description"]


def test_every_pool_inject_can_carry_a_tell():
    """The tell rides on whichever event is drawn, not on one hardcoded inject.

    Offline Mystery mode is only playable if the attribution hint survives
    the move to a pool, so every entry must render valid YAML with the tell
    appended and without it.
    """
    from llm.mock_driver import _INJECT_POOL, _INJECT_TELLS, _render_inject

    for entry in _INJECT_POOL:
        for tell in ("", _INJECT_TELLS["china"], _INJECT_TELLS["russia"]):
            data = _parse_inject_yaml(_render_inject(entry, 7, tell))
            assert data["title"] == entry["title"]
            assert data["channel"] == entry["channel"]
            assert data["effects"], f"{entry['id']} lost its effects"
            if tell:
                assert tell.split(":", 1)[1].strip()[:40] in data["description"]
            else:
                assert "Attribution note" not in data["description"]


# --- Stochastic inject pool --------------------------------------------------
#
# The offline driver used to answer every "generate the next inject" prompt
# with the same submarine surfacing off Orkney, so a campaign's stochastic
# turns were one event on repeat (dev-scripts/play-verify/transcript.ansi,
# turns 4-7). These cover the contract, not the specific events: an inject is
# produced, it parses, it differs from the previous turn's, the event ledger
# is honoured, and the same seed still replays the same campaign.


def _pool_size():
    from llm.mock_driver import _INJECT_POOL
    return len(_INJECT_POOL)


def _gated_titles():
    """Events the pool reserves for a campaign that is already hot."""
    from llm.mock_driver import _INJECT_POOL
    return {e["title"] for e in _INJECT_POOL if e["min_escalation"] > 30}


def _campaign_titles(seed, turns=8, escalation=75, first_turn=4):
    """Titles drawn over consecutive stochastic turns, ledger and all.

    Mirrors what engine.sim_loop feeds the generator each turn: a growing
    transcript and the **whole** event ledger. It used to pass ``ledger[-6:]``,
    which stopped matching production at b5ef8f2: the window was removed
    because the ledger is one line per event, so truncating it makes an older
    event invisible to the generator and re-opens the restaging bug the ledger
    exists to close. A test that keeps the window tests a code path nothing
    runs — and hides the guarantee the removal bought (see
    ``test_stochastic_injects_move_the_story_on``).
    """
    from llm.prompts import build_inject_generation_prompt
    from models.narrative_state import PlayedEvent

    driver = MockDeterministicDriver()
    rng = Random(seed)
    ledger, transcript, titles = [], [], []
    for turn in range(first_turn, first_turn + turns):
        world = _world()
        world.turn = turn
        world.metrics.escalation_risk = escalation
        prompt = build_inject_generation_prompt(
            world, turn, {}, None, list(transcript),
            event_ledger=list(ledger) or None)
        data = _parse_inject_yaml(driver.generate_text(prompt, rng))
        titles.append(data["title"])
        ledger.append(PlayedEvent(turn=turn, title=data["title"],
                                  disposition="resolved"))
        transcript.extend(["", "=" * 60, f"TURN {turn}", "=" * 60, "",
                           f"=== {data['title'].upper()} ===",
                           *str(data["description"]).splitlines(),
                           "Prime Minister: hold the line."])
    return titles


def test_stochastic_injects_move_the_story_on():
    """No event is staged twice in a campaign shorter than the pool.

    With the whole ledger in the prompt this is a property of the selection
    contract, not luck on one seed. ``_select_inject``'s first two passes both
    exclude everything the prompt already mentions, and the ledger mentions
    every title staged so far — so while either pass has a candidate left, the
    draw cannot repeat. Both empty only when the prompt names all
    ``len(_INJECT_POOL)`` events, which needs that many prior turns.

    So the bound is exactly the pool size, and it is asserted here at the
    bound and across many seeds. (Beyond it the pigeonhole takes over and a
    repeat is correct behaviour; ``test_exhausted_pool_still_produces_an_inject``
    covers what happens then.)
    """
    pool = _pool_size()
    for seed in range(24):
        for turns in (8, pool):
            titles = _campaign_titles(seed=seed, turns=turns)
            assert len(set(titles)) == turns, (
                f"seed {seed} restaged an event in {turns} turns: {titles}")


def test_consecutive_injects_always_differ():
    """Whatever the seed, this turn's event is never last turn's event."""
    from itertools import pairwise

    for seed in range(12):
        titles = _campaign_titles(seed=seed, turns=6)
        repeats = [a for a, b in pairwise(titles) if a == b]
        assert not repeats, f"seed {seed} repeated back-to-back: {titles}"


def test_inject_sequence_is_reproducible_for_a_seed():
    assert _campaign_titles(seed=5) == _campaign_titles(seed=5)


def test_different_seeds_tell_different_stories():
    assert _campaign_titles(seed=3) != _campaign_titles(seed=99)


def test_ledger_entries_are_not_restaged():
    """An event listed under EVENTS ALREADY PLAYED must not come back."""
    from llm.mock_driver import _INJECT_POOL
    from llm.prompts import build_inject_generation_prompt
    from models.narrative_state import PlayedEvent

    driver = MockDeterministicDriver()
    blocked = _INJECT_POOL[3]["title"]
    world = _world()
    world.turn = 9
    for seed in range(25):
        prompt = build_inject_generation_prompt(
            world, 9, {}, None, ["", "=" * 60, "TURN 8", "=" * 60, "",
                                 "An unrelated development."],
            event_ledger=[PlayedEvent(turn=8, title=blocked,
                                      disposition="resolved")])
        assert "EVENTS ALREADY PLAYED" in prompt
        data = _parse_inject_yaml(driver.generate_text(prompt, Random(seed)))
        assert data["title"] != blocked


def test_exhausted_pool_still_produces_an_inject():
    """A ledger naming every event must not leave the turn empty.

    An empty inject costs the player a whole turn, which is worse than a
    repeat, so the ledger block is the constraint that gets relaxed last.
    """
    from llm.mock_driver import _INJECT_POOL
    from llm.prompts import build_inject_generation_prompt
    from models.narrative_state import PlayedEvent

    driver = MockDeterministicDriver()
    previous = _INJECT_POOL[0]["title"]
    ledger = [PlayedEvent(turn=i, title=e["title"], disposition="resolved")
              for i, e in enumerate(_INJECT_POOL, start=1)]
    world = _world()
    world.turn = 20
    prompt = build_inject_generation_prompt(
        world, 20, {}, None,
        ["", "=" * 60, "TURN 19", "=" * 60, "", f"=== {previous.upper()} ==="],
        event_ledger=ledger)
    data = _parse_inject_yaml(driver.generate_text(prompt, Random(0)))
    assert data["title"] and data["description"].strip()
    assert data["title"] != previous


def test_calm_campaigns_are_not_handed_the_sharpest_events():
    """Escalation gates the events that only make sense in a hot crisis.

    Bounded deliberately: the gate holds for as long as there is an ungated
    event left to draw. A campaign longer than the ungated pool is a different
    contract, covered by the test below.
    """
    gated = _gated_titles()
    assert gated, "pool should reserve some events for a hot campaign"
    ungated_turns = _pool_size() - len(gated)

    drawn = set()
    for seed in range(12):
        drawn.update(_campaign_titles(seed=seed, turns=ungated_turns,
                                      escalation=25))
    assert not (drawn & gated), f"calm campaign drew {drawn & gated}"
    # The bound is worth stating: a calm campaign that long uses up every
    # ungated event, so this is the last turn at which the gate can hold.
    assert len(drawn) == ungated_turns

    hot = set()
    for seed in range(12):
        hot.update(_campaign_titles(seed=seed, turns=6, escalation=85))
    assert hot & gated, "a hot campaign should be able to draw them"


def test_escalation_is_the_first_constraint_relaxed_when_the_pool_runs_dry():
    """Past the ungated pool, a calm campaign is handed a sharp event anyway.

    ``_select_inject`` relaxes its constraints least-important-first, and the
    escalation gate is the least important of the three. So once a calm
    campaign has used every event its escalation admits, the next draw does
    NOT repeat and does NOT come back empty — it reaches past the gate.

    The previous test could never reach this: at six turns the first candidate
    pass still had three ungated events left, so the gate was never put under
    any pressure and the assertion held for free. This one runs the campaign
    past the ungated pool on purpose, which is the only way the relaxation
    branch is executed at all.
    """
    gated = _gated_titles()
    pool = _pool_size()
    ungated_turns = pool - len(gated)

    for seed in range(12):
        titles = _campaign_titles(seed=seed, turns=pool, escalation=25)
        # Nothing repeated, nothing empty — the gate gave way, not the ledger.
        assert len(set(titles)) == pool, f"seed {seed} repeated: {titles}"
        assert all(t.strip() for t in titles)
        # And it gave way only after the ungated events were spent.
        assert not (set(titles[:ungated_turns]) & gated)
        assert set(titles[ungated_turns:]) <= gated


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


def test_mock_interpretation_reports_only_each_submitted_force_package():
    driver = MockDeterministicDriver()
    expected_by_action = {
        ("Consult NATO allies, deploy P-8 patrols and Type 23 frigates "
         "to track Russian submarines, strengthen cyber defences, reassure "
         "the public, and require verified intelligence and Attorney General "
         "approval before any use of force."):
            ["P-8 patrols and Type 23 frigates"],
        ("Use HMS Prince of Wales and Typhoon squadrons to reinforce "
         "the Norwegian Sea."):
            ["HMS Prince of Wales and Typhoon squadrons"],
    }

    actual = []
    for action, expected in expected_by_action.items():
        response = driver.generate_text(
            f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
            RNG,
        )
        forces = parse_interpretation_simple(response)["forces"]
        assert forces == expected
        assert all(force in action for force in forces)
        actual.append(forces)

    assert actual[0] != actual[1]


def test_mock_interpretation_is_honest_when_no_force_is_tasked():
    driver = MockDeterministicDriver()
    action = ("Require verified intelligence and Attorney General approval "
              "before any use of force.")

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["None specified"]


def test_mock_interpretation_keeps_a_multiline_force_package():
    driver = MockDeterministicDriver()
    action = ("Deploy P-8 patrols and\nType 23 frigates to track Russian "
              "submarines.")

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "P-8 patrols and Type 23 frigates"]


def test_mock_interpretation_keeps_comma_separated_force_packages():
    driver = MockDeterministicDriver()
    action = ("Deploy Type 45 destroyers, Type 23 frigates and P-8 patrols "
              "to monitor the GIUK gap.")

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "Type 45 destroyers", "Type 23 frigates and P-8 patrols"]


def test_mock_interpretation_keeps_an_oxford_comma_force_package():
    driver = MockDeterministicDriver()
    action = (
        "Deploy Type-45 destroyers, P-8 patrols, and Typhoons to the North "
        "Sea."
    )

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "Type-45 destroyers",
        "P-8 patrols",
        "and Typhoons",
    ]


def test_mock_interpretation_keeps_coordinated_force_directives():
    driver = MockDeterministicDriver()
    action = (
        "Deploy Type 45 destroyers to the GIUK gap and scramble Typhoons "
        "over the North Sea."
    )

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "Type 45 destroyers", "Typhoons"]


@pytest.mark.parametrize(("action", "expected"), [
    ("Ready or not, if necessary, deploy the carrier.", ["the carrier"]),
    ("Not, actually, deploy the carrier.", ["the carrier"]),
    ("No, on reflection, deploy the carrier.", ["the carrier"]),
    (
        "Send the frigates, no, on reflection, deploy the carrier.",
        ["the frigates", "the carrier"],
    ),
])
def test_mock_interpretation_keeps_a_directive_after_incidental_negation(
        action, expected):
    driver = MockDeterministicDriver()

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == expected


def test_mock_interpretation_does_not_task_a_negated_force():
    driver = MockDeterministicDriver()
    action = "Do not deploy the carrier; consult NATO allies."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["None specified"]


def test_mock_interpretation_excludes_a_negated_directive_after_a_comma():
    driver = MockDeterministicDriver()
    action = "Deploy P-8 patrols, but do not send the carrier."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["P-8 patrols"]


def test_mock_interpretation_keeps_a_positive_directive_after_a_negated_one():
    driver = MockDeterministicDriver()
    action = "Do not deploy the carrier, but send P-8 patrols to Iceland."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["P-8 patrols"]


@pytest.mark.parametrize("action", [
    "Use diplomatic channels to press Moscow.",
    "Order an intelligence review.",
    "Send aid to Norway.",
    "Authorise a nuclear strike on the Russian task force.",
    "Use force only in self-defence.",
    "Authorise force only if attacked.",
])
def test_mock_interpretation_rejects_directives_without_named_assets(action):
    driver = MockDeterministicDriver()

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["None specified"]


def test_mock_interpretation_accepts_an_authorised_named_asset():
    driver = MockDeterministicDriver()
    action = "Authorise HMS Prince of Wales to sail north."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "HMS Prince of Wales"]


@pytest.mark.parametrize(("action", "expected"), [
    (
        "Authorise defensive patrols only, and instruct the Attorney General "
        "to review the legal basis.",
        ["defensive patrols only"],
    ),
    (
        "Authorize P-8 coverage over the Norwegian Sea.",
        ["P-8 coverage"],
    ),
])
def test_mock_interpretation_accepts_canonical_authorise_forms(action, expected):
    driver = MockDeterministicDriver()

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == expected


@pytest.mark.parametrize("negation", [
    "will not",
    "won't",
    "cannot",
    "can't",
    "not to",
])
def test_mock_interpretation_excludes_common_negated_directives(negation):
    driver = MockDeterministicDriver()
    action = f"Deploy P-8 patrols, but {negation} send the carrier."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["P-8 patrols"]


@pytest.mark.parametrize("action", [
    "Order HMS Prince of Wales not to sail.",
    "Deploy no carriers.",
])
def test_mock_interpretation_rejects_negation_inside_a_tasking_object(action):
    driver = MockDeterministicDriver()

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["None specified"]


@pytest.mark.parametrize("action", [
    "Do not, under any circumstances, deploy the carrier.",
    "Never, under any circumstances, launch the SSBNs.",
    "They must not, under any circumstances, deploy the carrier.",
    (
        "Hold the fleet in port and not, under any circumstances, deploy "
        "the carrier."
    ),
    "Do not, for any reason, deploy the carrier.",
    "Do not, I repeat, deploy the carrier.",
    "Never, ever, launch the SSBNs.",
    "Do not, unless attacked, deploy the carrier.",
])
def test_mock_interpretation_rejects_emphatic_negated_directives(action):
    driver = MockDeterministicDriver()

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["None specified"]


@pytest.mark.parametrize(("action", "expected"), [
    ("Deploy the destroyers, but not the carrier.", ["the destroyers"]),
    ("Send the Typhoons, not the carrier.", ["the Typhoons"]),
    ("Send the Typhoons, and not the carrier.", ["the Typhoons"]),
    ("Send the Typhoons, other than the carrier.", ["the Typhoons"]),
    ("Send the Typhoons, except the carrier.", ["the Typhoons"]),
    ("Deploy the destroyers but not the carrier.", ["the destroyers"]),
    ("Send the Typhoons but no carriers.", ["the Typhoons"]),
    ("Deploy the destroyers but do not fire.", ["the destroyers"]),
    ("Deploy the carrier group without escorts.", ["the carrier group"]),
])
def test_mock_interpretation_drops_elided_force_exclusions(action, expected):
    driver = MockDeterministicDriver()

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == expected


def test_mock_interpretation_reports_forces_in_verify_play_decision():
    driver = MockDeterministicDriver()
    action = (
        "Reinforce the GIUK gap with P-8 coverage and keep the submarines "
        "at sea."
    )

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "the GIUK gap with P-8 coverage",
        "the submarines",
    ]


@pytest.mark.parametrize("connector", [
    " and instead ",
    ", and instead ",
    " and then ",
    ", and then ",
])
def test_mock_interpretation_keeps_a_follow_up_directive_after_a_negated_one(
        connector):
    driver = MockDeterministicDriver()
    action = (
        f"Do not deploy the carrier{connector}scramble Typhoons over the "
        "North Sea."
    )

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["Typhoons"]


def test_mock_interpretation_does_not_treat_task_force_as_a_tasking_verb():
    driver = MockDeterministicDriver()
    action = "Task force readiness remains unchanged."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == ["None specified"]


def test_mock_interpretation_ends_a_force_directive_at_a_newline():
    driver = MockDeterministicDriver()
    action = "Send the carrier group north\nBrief the Commons this afternoon."

    response = driver.generate_text(
        f'Interpret this action. THE PRIME MINISTER HAS DECIDED: "{action}"\n',
        RNG,
    )

    assert parse_interpretation_simple(response)["forces"] == [
        "the carrier group north"]


def test_pushback_decision_extraction_survives_newlines():
    driver = MockDeterministicDriver()
    action = "Authorise nuclear\nfirst use."

    pushback = driver.generate_text(
        f'Check pushback triggers. THE PM HAS DECIDED: "{action}"\n', RNG)

    assert "NO PUSHBACK" not in pushback
    assert "nuclear first-use" in pushback


def test_pushback_decision_extraction_failure_is_visible():
    driver = MockDeterministicDriver()

    pushback = driver.generate_text(
        "Check pushback triggers without a decision block.", RNG)

    assert pushback == "[ERROR: Advisor response unavailable]"
