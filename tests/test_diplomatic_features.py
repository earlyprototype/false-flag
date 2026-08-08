"""Tests for the diplomatic channel and Mystery Mode context fixes.

Covers the PR-2 register entries:

- ER-012: stance lookup canonicalises country codes, so `USA` in the
  scenario data and `US` from the engine resolve to the same stance, and
  state actors are played from their own authored stance.
- ER-021: the deceive-the-UK instruction block renders for roleplay
  audiences only; briefing audiences get judge-don't-deceive instructions.
- ER-033 / ER-041: the scripted mandatory call is left live for the player
  on headless front ends (pending, drivable, capped, premise attached,
  delta applied exactly once) instead of answering itself.
- ER-018 / ER-038: the diplomatic transcript filter is a structural
  fail-closed whitelist and the UK's private metrics stay out of it.
- ER-040: the counterpart is told the real exchange number.
"""

import logging
from random import Random

import pytest

from engine.game_manager import GameManager
from engine.scenario_loader import load_narrative_configs


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Force the deterministic mock LLM driver for all tests."""
    monkeypatch.setenv("WARGAME_LLM", "mock")


def _narrative():
    configs = load_narrative_configs("war_game_2025")
    assert configs, "scenario narratives must load"
    return configs[0]  # RUSSIA_AGGRESSION


# ---------------------------------------------------------------------------
# ER-012: country-code canonicalisation
# ---------------------------------------------------------------------------

def test_stance_lookup_accepts_engine_and_iso_codes():
    narrative = _narrative()

    iso = narrative.to_llm_context("USA")
    engine_code = narrative.to_llm_context("US")

    assert "SECRET MOTIVE" in iso
    assert "SECRET MOTIVE" in engine_code
    # Stance-wise identical: only the echoed code in the role header differs.
    assert engine_code == iso.replace("YOUR ROLE (USA)", "YOUR ROLE (US)")


@pytest.mark.parametrize("code,expected_fragment", [
    ("Russia", "Operation Tuman"),
    ("RUS", "Operation Tuman"),
    ("China", "Taiwan"),
    ("Ireland", "neutrality"),
])
def test_stance_lookup_resolves_profile_keys(code, expected_fragment):
    assert expected_fragment in _narrative().to_llm_context(code)


def test_missing_stance_logs_a_parse_miss(caplog):
    narrative = _narrative()
    with caplog.at_level(logging.WARNING):
        context = narrative.to_llm_context("FJI")
    assert "SECRET MOTIVE" not in context
    assert any("[PARSE-MISS] narrative_stance.FJI" in rec.getMessage()
               for rec in caplog.records)


def test_actor_prompt_carries_the_actors_own_stance():
    from engine.actor_simulation import build_actor_prompt

    gm = GameManager(seed=11, mystery_mode=True)
    narrative = gm.world.narrative
    actor = gm.world.actor_system.actors["USA"]

    prompt = build_actor_prompt(actor, "Deploy a Type-45.", "world context",
                                world_narrative=narrative)
    usa_stance = next(s for s in narrative.stances if s.country_code == "USA")
    assert usa_stance.secret_motive in prompt

    # Without the narrative the prompt is unchanged in kind.
    bare = build_actor_prompt(actor, "Deploy a Type-45.", "world context")
    assert usa_stance.secret_motive not in bare


def test_adjudication_passes_the_narrative_per_actor(monkeypatch):
    """The actor path hands the narrative to each actor's prompt rather than
    concatenating one global block into the shared world context."""
    import engine.decision_phase as decision_phase
    import engine.narrative_adjudication as adjudication

    captured = {}

    def fake_simulate(actors, action, world_context, llm_generate_fn, rng,
                      llm_batch_fn=None, world_narrative=None):
        captured["world_context"] = world_context
        captured["world_narrative"] = world_narrative
        return []

    # resolve_decision routes through the decision pipeline (ER-023); the
    # CLIs' adjudication path is patched too so either route is covered.
    monkeypatch.setattr(decision_phase, "simulate_actor_responses", fake_simulate)
    monkeypatch.setattr(adjudication, "simulate_actor_responses", fake_simulate)

    gm = GameManager(seed=11, mystery_mode=True)
    gm.get_turn_briefing()
    gm.resolve_decision("Convene the North Atlantic Council under Article 4.")

    assert captured["world_narrative"] is gm.world.narrative
    assert "SECRET NARRATIVE TRUTH" not in captured["world_context"]
    assert "SECRET MOTIVE" not in captured["world_context"]


# ---------------------------------------------------------------------------
# ER-021: audience-gated instruction block
# ---------------------------------------------------------------------------

def test_briefing_audience_is_never_told_to_deceive():
    narrative = _narrative()

    briefing = narrative.to_llm_context(audience="briefing")
    assert "Provide plausible deniability" not in briefing
    assert "Act according to your secret motive" not in briefing
    assert "never to deceive the Prime Minister" in briefing

    roleplay = narrative.to_llm_context(audience="roleplay")
    assert "Provide plausible deniability" in roleplay
    assert "Act according to your secret motive" in roleplay


def test_shared_dossier_and_inject_context_use_briefing_audience():
    from llm.context_builder import (build_shared_context_prefix,
                                     get_stochastic_inject_context)

    gm = GameManager(seed=11, mystery_mode=True)
    dossier = build_shared_context_prefix(["a line"], gm.world)
    inject_ctx = get_stochastic_inject_context("summary", ["a line"], gm.world)

    for context in (dossier, inject_ctx):
        assert "SECRET NARRATIVE CONTEXT" in context
        assert "Provide plausible deniability" not in context
        assert "never to deceive the Prime Minister" in context


def test_diplomat_context_keeps_the_roleplay_block():
    from llm.context_builder import get_diplomatic_context

    gm = GameManager(seed=11, mystery_mode=True)
    context = get_diplomatic_context(["a line"], gm.world, "US")
    assert "Provide plausible deniability" in context


# ---------------------------------------------------------------------------
# ER-040: exchange counter
# ---------------------------------------------------------------------------

def test_exchange_counter_counts_exchanges_not_lines():
    from engine.diplomacy import DiplomaticEncounter

    gm = GameManager(seed=42)
    encounter = DiplomaticEncounter(gm.world, "US", None)
    encounter.start(Random(1))

    prompts = []

    def capture(prompt, rng, **kwargs):
        prompts.append(prompt)
        return "Understood."

    encounter.process_turn("First: we are coordinating with NATO.", capture, gm.rng)
    assert "exchange 1 of" in prompts[0]

    encounter.process_turn("Second: the deployment plan follows.", capture, gm.rng)
    assert "exchange 2 of" in prompts[1]

    # The player's line is rendered exactly once per prompt.
    assert prompts[0].count("First: we are coordinating with NATO.") == 1


def test_encounter_context_reaches_the_prompt():
    from engine.diplomacy import DiplomaticEncounter

    gm = GameManager(seed=42)
    premise = "The US President wants assurances before committing to Article 5."
    encounter = DiplomaticEncounter(gm.world, "US", premise)
    encounter.start(Random(1))

    prompts = []

    def capture(prompt, rng, **kwargs):
        prompts.append(prompt)
        return "Understood."

    encounter.process_turn("We hear your concerns.", capture, gm.rng)
    assert "=== WHY YOU ARE CALLING ===" in prompts[0]
    assert premise in prompts[0]

    # A player-initiated call has no premise and no premise block.
    plain = DiplomaticEncounter(gm.world, "US", None)
    plain.start(Random(1))
    prompts.clear()
    plain.process_turn("We hear your concerns.", capture, gm.rng)
    assert "WHY YOU ARE CALLING" not in prompts[0]


# ---------------------------------------------------------------------------
# ER-033 / ER-041: the scripted call is played by the player
# ---------------------------------------------------------------------------

def _open_scripted_encounter(gm):
    """Advance the session to the scripted turn-6 encounter."""
    gm.world.turn = 6
    return gm.get_turn_briefing()


def test_headless_scripted_encounter_is_pending_not_auto_answered():
    gm = GameManager(seed=42, play_mode="classic")
    inject = _open_scripted_encounter(gm)

    pending = inject.get("pending_encounter")
    assert pending is not None
    assert pending["country"] == "US"
    assert "Article 5" in pending["context"]

    assert gm.active_encounter is not None
    assert gm.active_encounter.active
    assert gm.active_encounter.required
    assert gm.active_encounter.context == pending["context"]

    # The marker and the call's opening are on the record; nobody has spoken
    # for the player.
    assert any("MANDATORY DIPLOMATIC ENCOUNTER" in line for line in gm.transcript)
    assert any(line.startswith("=== DIPLOMATIC CALL") for line in gm.transcript)
    assert not any(line.startswith("Prime Minister:") for line in
                   gm.active_encounter.transcript)
    assert gm.active_encounter.outcome is None


def test_scripted_encounter_is_drivable_capped_and_applies_delta_once(monkeypatch):
    import engine.diplomacy as diplomacy

    monkeypatch.setattr(
        diplomacy, "assess_diplomatic_outcome",
        lambda *args, **kwargs: ("Diplomatic Outcome: SUCCESS\nWell handled.", 8),
    )

    gm = GameManager(seed=42, play_mode="classic")
    _open_scripted_encounter(gm)

    cap = gm.active_encounter.max_exchanges
    cohesion_before = gm.world.metrics.alliance_cohesion
    assert cohesion_before <= 92, "headroom needed to observe the delta"

    turns_taken = 0
    for _ in range(cap + 5):
        result = gm.process_diplomacy("We are coordinating fully with NATO.")
        turns_taken += 1
        if not result["active"]:
            break

    assert turns_taken == cap, "the exchange cap must end a headless call"
    assert result["outcome"]["cohesion_delta"] == 8
    # Applied exactly once, and mirrored into the narrative state so the
    # next adjudication does not revert it.
    assert gm.world.metrics.alliance_cohesion == cohesion_before + 8
    assert gm.narrative_state.hidden_metrics.alliance_cohesion == cohesion_before + 8
    # The call is part of the campaign record.
    assert any("CALL ENDED" in line for line in gm.transcript)


def test_scripted_encounter_ends_on_a_closer():
    gm = GameManager(seed=42, play_mode="classic")
    _open_scripted_encounter(gm)

    gm.process_diplomacy("We are coordinating fully with NATO.")
    result = gm.process_diplomacy("Thank you, goodbye.")
    assert result["active"] is False
    assert result["outcome"] is not None


# ---------------------------------------------------------------------------
# Two-stage outbound calls: open the line, counterpart speaks first
# ---------------------------------------------------------------------------

def test_outbound_call_opens_with_the_counterpart_speaking_first():
    """start_diplomacy is the no-message entry point: the line opens and the
    counterpart's opening line is already on the transcript before the
    player has said anything."""
    gm = GameManager(seed=42, play_mode="classic")
    result = gm.start_diplomacy("US")

    assert result["active"] is True
    assert any(line.startswith(f"{result['title']}:")
               for line in result["transcript"]), "the counterpart speaks first"
    assert not any("Prime Minister:" in line for line in result["transcript"]), \
        "nobody has spoken in the player's name"


def test_zero_exchange_hangup_pays_for_no_assessment_and_moves_nothing():
    """Open the line, say nothing, hang up: no LLM assessment, no delta."""
    from engine.diplomacy import DiplomaticEncounter

    gm = GameManager(seed=42, play_mode="classic")
    encounter = DiplomaticEncounter(gm.world, "US", None)
    encounter.start(gm.rng)

    def must_not_be_called(*args, **kwargs):
        raise AssertionError(
            "a zero-exchange hang-up must not pay for an outcome assessment")

    cohesion_before = gm.world.metrics.alliance_cohesion
    transcript = encounter.process_turn("end", must_not_be_called, gm.rng)

    assert encounter.active is False
    assert encounter.outcome is not None, "front ends read outcome as call-over"
    assert encounter.outcome["cohesion_delta"] == 0
    assert gm.world.metrics.alliance_cohesion == cohesion_before
    assert any("CALL ENDED" in line for line in transcript)
    assert not any(str(line).startswith("Prime Minister:")
                   for line in transcript), \
        "'end' is a hang-up, not a line spoken on the call"


def test_zero_exchange_hangup_through_the_manager_leaves_no_metric_trace():
    gm = GameManager(seed=42, play_mode="classic")
    world_before = gm.world.metrics.alliance_cohesion
    hidden_before = gm.narrative_state.hidden_metrics.alliance_cohesion

    opened = gm.start_diplomacy("US")
    assert opened["active"] is True
    result = gm.process_diplomacy("end")

    assert result["active"] is False
    assert result["outcome"]["cohesion_delta"] == 0
    assert gm.world.metrics.alliance_cohesion == world_before
    assert gm.narrative_state.hidden_metrics.alliance_cohesion == hidden_before


def test_hangup_after_speaking_is_still_assessed(monkeypatch):
    """The quiet close is only for zero-exchange calls: once anything has
    been said, hanging up runs the normal outcome assessment."""
    import engine.diplomacy as diplomacy

    monkeypatch.setattr(
        diplomacy, "assess_diplomatic_outcome",
        lambda *args, **kwargs: ("Diplomatic Outcome: SUCCESS\nWell handled.", 5),
    )

    gm = GameManager(seed=42, play_mode="classic")
    before = gm.world.metrics.alliance_cohesion
    assert before <= 95, "headroom needed to observe the delta"

    gm.start_diplomacy("US")
    gm.process_diplomacy("We are coordinating fully with NATO.")
    result = gm.process_diplomacy("end")

    assert result["active"] is False
    assert result["outcome"]["cohesion_delta"] == 5
    assert gm.world.metrics.alliance_cohesion == before + 5


def test_walking_out_on_a_required_call_is_still_assessed(monkeypatch):
    """Hanging up on the scripted caller without a word is an act, not a
    quiet close — the assessment must still run."""
    import engine.diplomacy as diplomacy

    called = {}

    def assess(*args, **kwargs):
        called["ran"] = True
        return ("Diplomatic Outcome: FAILURE\nYou hung up on the President.", -5)

    monkeypatch.setattr(diplomacy, "assess_diplomatic_outcome", assess)

    gm = GameManager(seed=42, play_mode="classic")
    _open_scripted_encounter(gm)

    result = gm.process_diplomacy("end")
    assert result["active"] is False
    assert called.get("ran"), "the required call's walk-out went unassessed"
    assert result["outcome"]["cohesion_delta"] == -5


def test_scripted_encounter_hides_the_number_outside_classic():
    gm = GameManager(seed=42, play_mode="immersive")
    _open_scripted_encounter(gm)
    assert gm.active_encounter.show_metrics is False

    classic = GameManager(seed=42, play_mode="classic")
    _open_scripted_encounter(classic)
    assert classic.active_encounter.show_metrics is True


def test_interactive_briefing_still_plays_the_call_inline():
    """A caller with a keyboard keeps the blocking flow: no pending inject key,
    the premise reaches the encounter, and the call is answered in full."""
    from engine.sim_loop import run_turn_briefing

    gm = GameManager(seed=42, play_mode="classic")
    gm.world.turn = 6
    answers = iter(["", "We are coordinating fully with NATO.", "Thank you."])

    inject, lines = run_turn_briefing(
        gm.world, "war_game_2025", False, gm.rng, gm.root_path, gm.transcript,
        get_player_input=lambda prompt: next(answers),
        suppress_display=True, silent_effects=True,
        narrative_state=gm.narrative_state,
    )

    assert "_pending_encounter" not in inject
    assert "pending_encounter" not in inject
    assert any("CALL ENDED" in line for line in lines)


# ---------------------------------------------------------------------------
# ER-018 / ER-038: the diplomatic context whitelist
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def played_session():
    """A real session: turn one played in full, then the scripted US call."""
    import os
    os.environ["WARGAME_LLM"] = "mock"

    gm = GameManager(seed=42, play_mode="classic")
    gm.get_turn_briefing()
    gm.process_question("Where does NATO stand on this?")
    gm.resolve_decision("Hold posture and consult NATO allies first.")

    gm.world.turn = 6
    gm.get_turn_briefing()
    gm.process_diplomacy("We are coordinating fully with NATO.")
    gm.process_diplomacy("Thank you, goodbye.")
    return gm


def test_filter_excludes_every_internal_uk_line(played_session):
    from llm.context_builder import get_diplomatic_context

    gm = played_session
    context = get_diplomatic_context(gm.transcript, gm.world, "US")

    # Zero advisor answers reach the counterpart.
    for line in gm.transcript:
        first = str(line).strip().split("\n", 1)[0]
        for role in ("Government Leader", "Military Commander",
                     "Intelligence Coordinator", "Domestic Security",
                     "Diplomatic Lead", "Legal Advisor"):
            if first.startswith(f"{role}:"):
                assert first not in context

    assert "Prime Minister: Where does NATO stand on this?" not in context
    assert "Prime Minister's Decision:" not in context
    assert "INTERPRETATION:" not in context


def test_filter_keeps_public_material(played_session):
    from llm.context_builder import get_diplomatic_context

    gm = played_session
    context = get_diplomatic_context(gm.transcript, gm.world, "US")

    # Inject prose (no speaker prefix) passes.
    assert "coordinated campaign of coercion" in context
    assert "TURN 1" in context


def test_filter_shares_a_call_with_its_own_country_only(played_session):
    from llm.context_builder import get_diplomatic_context

    gm = played_session
    us_context = get_diplomatic_context(gm.transcript, gm.world, "US")
    fr_context = get_diplomatic_context(gm.transcript, gm.world, "France")

    assert "=== DIPLOMATIC CALL" in us_context
    assert "Prime Minister: We are coordinating fully with NATO." in us_context
    assert "CALL ENDED" in us_context

    assert "DIPLOMATIC CALL" not in fr_context
    assert "We are coordinating fully with NATO." not in fr_context


def test_filter_excludes_private_metric_numbers(played_session):
    from llm.context_builder import get_diplomatic_context

    gm = played_session
    context = get_diplomatic_context(gm.transcript, gm.world, "US")

    assert "UK Escalation Risk" not in context
    assert "UK Domestic Stability" not in context
    assert "NATO Alliance Cohesion" not in context
    assert "Effect: escalation_risk" not in context
    assert f"Turn: {gm.world.turn}" in context
    assert "A serious security crisis involving Russia and NATO is under way." in context


def test_filter_output_is_bounded():
    from llm.context_builder import (MAX_DIPLOMATIC_CONTEXT_CHARS,
                                     get_diplomatic_context)

    gm = GameManager(seed=42)
    # Prose lines with no speaker prefix, so the whitelist keeps them all.
    transcript = [f"The situation develops further, hour {i}. " + "x" * 400
                  for i in range(500)]
    context = get_diplomatic_context(transcript, gm.world, "US")
    assert len(context) <= MAX_DIPLOMATIC_CONTEXT_CHARS + 2_000
    assert "elided for length" in context


# ---------------------------------------------------------------------------
# ER-047: a live call survives a save/load round-trip
# ---------------------------------------------------------------------------

def test_live_encounter_survives_save_and_load():
    gm = GameManager(seed=42, play_mode="classic")
    gm.world.turn = 6
    gm.get_turn_briefing()
    gm.process_diplomacy("We are coordinating fully with NATO.")
    exchanges_before = gm.active_encounter._player_exchanges
    call_lines_before = list(gm.active_encounter.transcript)

    restored = GameManager.from_dict(gm.to_dict())

    enc = restored.active_encounter
    assert enc is not None and enc.active
    assert enc.required
    assert enc.country == "US"
    assert enc._player_exchanges == exchanges_before
    assert enc.transcript == call_lines_before

    # The restored call is drivable, and its lines still mirror into the
    # session transcript.
    grew_from = len(restored.transcript)
    result = restored.process_diplomacy("Our frigates join the patrol line tomorrow.")
    assert result.get("error") is None
    assert len(restored.transcript) > grew_from


def test_ended_encounter_is_not_resurrected_by_a_round_trip(monkeypatch):
    import engine.diplomacy as diplomacy

    monkeypatch.setattr(
        diplomacy, "assess_diplomatic_outcome",
        lambda *args, **kwargs: ("Diplomatic Outcome: SUCCESS\nWell handled.", 8),
    )

    gm = GameManager(seed=42, play_mode="classic")
    gm.world.turn = 6
    gm.get_turn_briefing()
    gm.process_diplomacy("We are coordinating fully with NATO.")
    gm.process_diplomacy("Thank you, goodbye.")
    assert not gm.active_encounter.active

    restored = GameManager.from_dict(gm.to_dict())
    assert restored.active_encounter is None
