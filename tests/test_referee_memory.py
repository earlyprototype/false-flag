"""Referee memory: the calls that decide outcomes finally see the campaign.

Covers the PR-3 fix wave (ER-002, ER-003, ER-007, ER-010, ER-013 partial,
ER-014, ER-017, ER-020, ER-043):

- the quality-assessment prompt carries the rolling summary and the
  decisions-and-outcomes ledger, so by turn 3 it contains turn 2's decision;
- the critical-omissions prompt carries the structured interpretation;
- the narrator prompt carries the player's previous decision;
- the inject-generation prompt's STORY SO FAR block is the rolling synopsis;
- the state-actor context omits the UK cabinet's private trust scores;
- advisor trust moves on the actor-simulation path (the live path);
- pushback is returned as its own list, and overriding it unamended costs
  trust.

Campaign-driving tests run the real headless GameManager against the
deterministic mock driver, with a capturing wrapper recording every prompt
the router dispatches.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from engine.game_manager import GameManager

# Turn 2 of the standard variant stages "Russian Submarine Surfaces Near UK
# Waters"; this decision shares its significant words and uses a closure
# verb, so record_event_disposition marks the event RESOLVED and attaches
# the decision text as the ledger note.
TURN_2_DECISION = "Escort the Russian submarine out of UK waters and brief NATO allies"

DECISIONS = [
    "Convene COBRA and task the investigation into the pilot murders",
    TURN_2_DECISION,
    "Hold current posture and await NATO consultations",
]


def _capturing_campaign(mp, variant="standard", decisions=DECISIONS,
                        extra_briefing=False):
    """Drive a mock campaign through GameManager, recording every prompt."""
    from llm.mock_driver import MockDeterministicDriver

    mp.setenv("WARGAME_LLM", "mock")

    captured = []
    original = MockDeterministicDriver.generate_text

    def capturing(self, prompt, rng):
        captured.append(prompt)
        return original(self, prompt, rng)

    mp.setattr(MockDeterministicDriver, "generate_text", capturing)

    gm = GameManager(scenario_id="war_game_2025", variant=variant, seed=42)
    turn_slices = {}
    for turn, decision in enumerate(decisions, start=1):
        gm.get_turn_briefing()
        mark = len(captured)
        gm.resolve_decision(decision)
        turn_slices[turn] = (mark, len(captured))

    if extra_briefing:
        mark = len(captured)
        gm.get_turn_briefing()
        turn_slices["extra_briefing"] = (mark, len(captured))

    return SimpleNamespace(gm=gm, prompts=captured, turn_slices=turn_slices)


@pytest.fixture(scope="module")
def campaign():
    """Three standard-variant turns, prompts captured."""
    mp = pytest.MonkeyPatch()
    try:
        yield _capturing_campaign(mp)
    finally:
        mp.undo()


@pytest.fixture(scope="module")
def fast_campaign():
    """Three fast_start turns plus the turn-4 briefing, which is generated
    (fast_start's stochastic_from is 4), prompts captured."""
    mp = pytest.MonkeyPatch()
    try:
        yield _capturing_campaign(mp, variant="fast_start", extra_briefing=True)
    finally:
        mp.undo()


def _prompts_in(campaign_ns, turn, marker):
    start, stop = campaign_ns.turn_slices[turn]
    return [p for p in campaign_ns.prompts[start:stop] if marker in p]


# --- the deciding calls see the campaign -------------------------------------

def test_quality_prompt_carries_previous_decisions_by_turn_3(campaign):
    """ER-010/ER-017: by turn 3 the referee knows what the player did on
    turn 2, via the ledger note and the rolling summary blocks."""
    quality_prompts = _prompts_in(campaign, 3, "ASSESS THIS ACTION")
    assert quality_prompts, "no quality-assessment prompt captured on turn 3"
    prompt = quality_prompts[-1]

    assert "DECISIONS AND OUTCOMES" in prompt
    assert TURN_2_DECISION[:60] in prompt, \
        "turn 2's decision never reached the turn-3 quality assessment"
    assert "RESOLVED" in prompt, "the escorted submarine was not marked resolved"
    assert "SITUATION SUMMARY:" in prompt


def test_quality_prompt_no_longer_carries_the_frozen_clock(campaign):
    """The 'Game Time: 17:00 (Turn 9)' string never advanced; it is gone."""
    for turn in (1, 2, 3):
        for prompt in _prompts_in(campaign, turn, "ASSESS THIS ACTION"):
            assert "Game Time:" not in prompt


def test_omissions_prompt_carries_the_interpretation(campaign):
    """ER-002: the five-advisor scan reads the structured interpretation,
    not just the raw typed sentence."""
    omissions_prompts = _prompts_in(campaign, 2, "CRITICAL OMISSIONS CHECK")
    assert omissions_prompts, "no omissions prompt captured on turn 2"
    for prompt in omissions_prompts:
        assert "HOW THE CABINET OFFICE READS IT" in prompt
        # The mock interpreter's structured reading, not the decision echo
        assert "FORCES INVOLVED" in prompt


def test_narrator_prompt_carries_the_previous_decision(campaign):
    """ER-043: the bridge between turns is told what the player decided."""
    narrator_prompts = [p for p in campaign.prompts if "atmospheric bridge" in p]
    assert narrator_prompts, "no narrator prompt captured"
    # The first bridge runs at the turn-2 briefing, after turn 1's decision.
    prompt = narrator_prompts[0]
    assert "THE PLAYER'S LAST DECISION:" in prompt
    assert DECISIONS[0] in prompt


def test_inject_prompt_story_so_far_is_the_rolling_summary(fast_campaign):
    """ER-020: the generated turn's STORY SO FAR block holds the synopsis
    maintained by update_situation_summary, not the mechanical digest."""
    start, stop = fast_campaign.turn_slices["extra_briefing"]
    inject_prompts = [p for p in fast_campaign.prompts[start:stop]
                      if "generate the next inject" in p.lower()]
    assert inject_prompts, "turn 4 of fast_start should be generated"
    prompt = inject_prompts[-1]

    rolling = fast_campaign.gm.narrative_state.situation_summary
    assert rolling, "three adjudicated turns must have produced a synopsis"
    assert rolling[:80] in prompt
    assert "STORY SO FAR" in prompt
    assert "STORY DIGEST:" not in prompt, \
        "the mechanical digest should only be the fallback"


def test_advisor_dossier_carries_the_event_ledger(campaign):
    """ER-003: the transcript-carrying prompts hold the ledger too."""
    omissions_prompts = _prompts_in(campaign, 3, "CRITICAL OMISSIONS CHECK")
    assert omissions_prompts
    for prompt in omissions_prompts:
        assert "EVENTS ALREADY PLAYED" in prompt
        assert TURN_2_DECISION[:60] in prompt


def test_diplomatic_outcome_assessment_sees_the_campaign(campaign):
    """ER-017: the third deciding call family gets the summary + ledger."""
    from random import Random

    from engine.diplomacy import assess_diplomatic_outcome

    gm = campaign.gm
    captured = {}

    def fake_llm(prompt, rng, **kwargs):
        captured["prompt"] = prompt
        return "OUTCOME: NEUTRAL\nALLIANCE_COHESION_DELTA: 0\nSUMMARY: Fine."

    assess_diplomatic_outcome(
        gm.world, "US", [("Prime Minister", "Hello")], fake_llm, Random(1),
        narrative_state=gm.narrative_state,
    )
    prompt = captured["prompt"]
    assert "THE CAMPAIGN SO FAR" in prompt
    assert "DECISIONS AND OUTCOMES" in prompt
    assert TURN_2_DECISION[:60] in prompt

    # Default None keeps old callers working, without the memory blocks.
    assess_diplomatic_outcome(
        gm.world, "US", [("Prime Minister", "Hello")], fake_llm, Random(1),
    )
    assert "THE CAMPAIGN SO FAR" not in captured["prompt"]


# --- actor context and trust -------------------------------------------------

def _fresh_state():
    from models.narrative_state import create_initial_narrative_state
    from models.world import Metrics

    return create_initial_narrative_state(
        metrics=Metrics(escalation_risk=60, domestic_stability=50,
                        alliance_cohesion=40, casualties_mil=0, casualties_civ=0),
        play_mode="immersive",
    )


def test_actor_context_lacks_uk_trust_lines():
    """ER-014: a foreign government must not reason from cabinet trust."""
    state = _fresh_state()
    state.record_played_event(1, "Submarine Incident")
    state.close_event(1, "resolved", "Escorted it out of UK waters")

    full = state.to_llm_context()
    actor = state.to_actor_context()

    assert "Character Relationships:" in full
    assert "trust:" in full
    assert "Character Relationships:" not in actor
    assert "trust:" not in actor

    # Everything else is shared: metrics, summary, and the ledger.
    for fragment in ("Escalation Risk:", "SITUATION SUMMARY:",
                     "DECISIONS AND OUTCOMES", "Escorted it out of UK waters"):
        assert fragment in full
        assert fragment in actor


def test_actor_path_adjudication_moves_advisor_trust():
    """ER-007: trust responds to decision quality on the live (actor) path,
    for every uk_ character; the usa_nsa seed stays static by design."""
    from random import Random

    from engine.narrative_adjudication import adjudicate_with_actor_simulation
    from models.state_actors import load_actors_from_yaml

    state = _fresh_state()
    seeds = {cid: char.trust for cid, char in state.characters.items()}
    actor_system = load_actors_from_yaml(str(root / "data" / "state_actors.yaml"))

    def fake_llm(prompt, rng, **kwargs):
        if "ASSESS THIS ACTION" in prompt:
            return ("QUALITY: poor\n\nREASONING: Rash and premature.\n\n"
                    "EFFECTS:\nescalation_risk: 6\n\nQUALITY MULTIPLIER: 0.5")
        if "PUBLIC_RESPONSE" in prompt:
            return ("PUBLIC_RESPONSE: We note the UK's action with concern.\n\n"
                    "PRIVATE_ASSESSMENT: Unhelpful.\n\nTRUST_CHANGE: -4\n\n"
                    "WILL_SUPPORT: conditional\n\nCONDITIONS: none\n\n"
                    "INTEL_SHARED: none")
        if "Summarise the current situation" in prompt:
            return "The campaign continues."
        return "Understood, Prime Minister."

    adjudicate_with_actor_simulation(
        state, actor_system,
        "Surge the carrier group forward immediately",
        "interpretation", Random(42), fake_llm,
    )

    uk_ids = [cid for cid in state.characters if cid.startswith("uk_")]
    assert uk_ids, "the seeded roster must contain uk_ advisors"
    for cid in uk_ids:
        assert state.characters[cid].trust == seeds[cid] - 3, \
            f"{cid} trust did not move with a poor decision"
    assert state.characters["usa_nsa"].trust == seeds["usa_nsa"], \
        "usa_nsa is static by design"


# --- pushback as its own key, with a cost when overridden --------------------

def test_pushback_is_its_own_key_and_override_costs_trust(monkeypatch):
    """ER-013 (partial): the preview separates pushback from omissions, and
    committing the identical text unamended costs the objectors a point of
    trust through the existing attitude machinery."""
    monkeypatch.setenv("WARGAME_LLM", "mock")

    gm = GameManager(scenario_id="war_game_2025", seed=42)
    gm.get_turn_briefing()

    nuclear = "Authorise a nuclear strike on the Russian northern fleet"
    preview = gm.interpret_decision(nuclear)

    assert preview["pushback"], "the mock cabinet objects to nuclear first-use"
    roles = {p["role"] for p in preview["pushback"]}
    assert "Foreign Secretary" in roles
    # No more flattening: the canned pushback recommendation is gone from
    # critical_concerns, and every entry there is a real omissions triple.
    assert all(c["recommendation"] != "Consider revising your approach."
               for c in preview["critical_concerns"])

    before = gm.narrative_state.characters["uk_foreign_sec"].trust
    gm.resolve_decision(nuclear)
    after = gm.narrative_state.characters["uk_foreign_sec"].trust
    # Mock quality is "adequate" (attitude delta 0), so the only movement is
    # the override cost.
    assert after == before - 1, "overriding pushback verbatim must cost trust"


def test_amended_decision_pays_no_pushback_cost(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")

    gm = GameManager(scenario_id="war_game_2025", seed=42)
    gm.get_turn_briefing()

    preview = gm.interpret_decision(
        "Authorise a nuclear strike on the Russian northern fleet")
    assert preview["pushback"]

    before = gm.narrative_state.characters["uk_foreign_sec"].trust
    gm.resolve_decision("Stand the strike down and pursue NATO consultations")
    after = gm.narrative_state.characters["uk_foreign_sec"].trust
    assert after == before, "an amended decision must not pay the override cost"


# ---------------------------------------------------------------------------
# ER-048: the synopsis seed is grounded and the fold defends attribution
# ---------------------------------------------------------------------------

def test_summary_seed_grounds_each_founding_event():
    from models.narrative_state import create_initial_narrative_state
    from models.world import Metrics

    ns = create_initial_narrative_state(
        Metrics(escalation_risk=60, domestic_stability=50, alliance_cohesion=40),
        play_mode="emergent")
    seed = ns.situation_summary
    assert "Norfolk" in seed
    assert "Dagestani" in seed
    assert "falsely blames the United Kingdom" in seed
    # The murders and the naval-base attack are separate sentences: the
    # culprit of one must not be readable as the culprit of the other.
    murder_sentence = next(s for s in seed.split(". ") if "Norfolk" in s)
    assert "Dagestani" not in murder_sentence


def test_fold_prompt_carries_fidelity_rules_and_pro_tier():
    from engine.narrative_adjudication import compute_situation_summary
    from models.narrative_state import create_initial_narrative_state
    from models.world import Metrics
    from llm.model_config import LLMContext, ModelTier, get_model_config

    captured = {}

    def fake_generate(prompt, rng, **kwargs):
        captured["prompt"] = prompt
        captured["context"] = kwargs.get("context")
        return "A grounded synopsis."

    from random import Random

    ns = create_initial_narrative_state(
        Metrics(escalation_risk=60, domestic_stability=50, alliance_cohesion=40),
        play_mode="emergent")
    out = compute_situation_summary(ns, "Hold and consult allies.",
                                    fake_generate, Random(0))
    assert out == "A grounded synopsis."
    assert "never merge two events" in captured["prompt"]
    assert "who accuses whom" in captured["prompt"]
    assert get_model_config().get_tier_for_context(captured["context"]) is ModelTier.PRO
