"""Regression tests for the headless GameManager (engine/game_manager.py).

Covers the drift between GameManager and the CLI play loop:
- resolve_decision must copy narrative_state.hidden_metrics back onto
  world.metrics, recompute world flags, and sync narrative_state.turn
  before the turn advances (world.metrics used to stay frozen at their
  initial values for API sessions).
- get_turn_briefing must sync inject effects into the narrative state,
  pass the variant turn filename through, and enable stochastic injects
  once the scenario's transition turn is reached.
- Adjudication failures must be surfaced to API callers via an "error"
  key instead of being silently swallowed.
- get_intel_actors must use the real country codes from
  data/state_actors.yaml (USA, not US), so the United States is
  categorized as an ally.
"""

import pytest

from engine.game_manager import GameManager

DECISION = "Request NATO Article 4 consultations and reinforce air policing"


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Force the deterministic mock LLM driver for all tests."""
    monkeypatch.setenv("WARGAME_LLM", "mock")


def make_manager(seed=42):
    return GameManager(scenario_id="war_game_2025", seed=seed)


def snapshot_metrics(metrics):
    return {
        "escalation_risk": metrics.escalation_risk,
        "domestic_stability": metrics.domestic_stability,
        "alliance_cohesion": metrics.alliance_cohesion,
        "casualties_mil": metrics.casualties_mil,
        "casualties_civ": metrics.casualties_civ,
    }


def test_briefing_syncs_inject_effects_into_narrative_state():
    gm = make_manager()
    inject = gm.get_turn_briefing()

    assert inject, "Turn 1 inject should load from the scripted scenario"
    # Inject effects land on world.metrics; the sync must copy them into
    # hidden_metrics so adjudication doesn't silently revert them.
    assert snapshot_metrics(gm.narrative_state.hidden_metrics) == snapshot_metrics(
        gm.world.metrics
    )


def test_resolve_decision_syncs_world_metrics_and_flags():
    gm = make_manager()
    initial = snapshot_metrics(gm.world.metrics)

    gm.get_turn_briefing()
    result = gm.resolve_decision(DECISION)

    assert result["error"] is None
    assert result["effects"], "Mock adjudication should produce effects"
    # World metrics must reflect adjudication, not stay frozen at the
    # initial values.
    assert snapshot_metrics(gm.world.metrics) != initial
    assert snapshot_metrics(gm.world.metrics) == snapshot_metrics(
        gm.narrative_state.hidden_metrics
    )
    # Flags must be recomputed from the synced metrics.
    from engine.flags import compute_risk_flags

    assert gm.world.flags == compute_risk_flags(gm.world.metrics)


def test_narrative_turn_advances_with_world_turn():
    gm = make_manager()

    gm.get_turn_briefing()
    gm.resolve_decision(DECISION)
    # Mirrors the CLI ordering: narrative_state.turn is set to the turn
    # just resolved, then world.turn advances.
    assert gm.world.turn == 2
    assert gm.narrative_state.turn == 1

    gm.get_turn_briefing()
    gm.resolve_decision(DECISION)
    assert gm.world.turn == 3
    assert gm.narrative_state.turn == 2


def test_resolve_decision_clears_discussion_transcript():
    gm = make_manager()
    gm.get_turn_briefing()
    gm.process_question("What are our options?")
    assert gm.world.discussion_transcript

    gm.resolve_decision(DECISION)
    assert gm.world.discussion_transcript == []


def test_resolve_decision_surfaces_adjudication_error(monkeypatch):
    import engine.narrative_adjudication as adjudication

    def boom(*args, **kwargs):
        raise RuntimeError("adjudication exploded")

    monkeypatch.setattr(adjudication, "adjudicate_with_actor_simulation", boom)
    monkeypatch.setattr(adjudication, "adjudicate_with_narrative", boom)

    gm = make_manager()
    gm.get_turn_briefing()
    before = snapshot_metrics(gm.world.metrics)
    result = gm.resolve_decision(DECISION)

    assert result["error"] is not None
    assert "adjudication exploded" in result["error"]
    assert result["effects"] == {}
    # The decision did not take effect on the metrics.
    assert snapshot_metrics(gm.world.metrics) == before


def test_briefing_passes_turn_filename_and_stochastic_flag(monkeypatch):
    import engine.game_manager as game_manager_module

    gm = make_manager()
    captured = {}

    def fake_run_turn_briefing(world, scenario_id, stochastic, rng, root_path,
                               transcript, **kwargs):
        captured["stochastic"] = stochastic
        captured["turn_filename"] = kwargs.get("turn_filename")
        return {}, []

    monkeypatch.setattr(game_manager_module, "run_turn_briefing", fake_run_turn_briefing)

    gm.get_turn_briefing()
    assert captured["turn_filename"], "Variant turn filename must be passed through"
    assert captured["stochastic"] is False

    stochastic_from = gm.scenario_config.get("stochastic_from", 7)
    gm.world.turn = stochastic_from
    gm.get_turn_briefing()
    assert captured["stochastic"] is True


def test_get_intel_actors_categorizes_usa_as_ally():
    gm = make_manager()
    actors = {a["code"]: a for a in gm.get_intel_actors()}

    assert "USA" in actors, "Codes must match data/state_actors.yaml"
    assert actors["USA"]["category"] == "ally"
    assert actors["RUS"]["category"] == "adversary"


def test_each_question_lands_in_the_transcript_exactly_once():
    """ER-024: process_question pre-appended the Prime Minister line and then
    extended the same line from run_turn_discussion, doubling every question
    in every history-carrying prompt."""
    gm = make_manager()
    gm.get_turn_briefing()

    question = "What is the Russian submarine actually doing?"
    gm.process_question(question)

    line = f"Prime Minister: {question}"
    assert gm.transcript.count(line) == 1


def _play_turn(gm, turn):
    gm.get_turn_briefing()
    gm.process_question(f"Turn {turn}: what changed overnight?")
    gm.resolve_decision(DECISION)


def test_save_load_resumes_the_draw_sequence(monkeypatch):
    """ER-037: a campaign saved after three turns and resumed must play turn
    four exactly as an uninterrupted campaign does — the restored generator
    continues from the saved position instead of replaying spent draws.

    fast_start puts the stochastic transition at turn 4, so the campaign has
    spent generation draws by the time it is saved and the turn played after
    the reload is itself a *generated* one. Both halves matter: the mock
    driver spends no randomness on scripted turns, so a save taken before
    the transition resumes identically with or without the stored position.
    With one generated turn behind the save, deleting rng_state from the
    payload fails this test (verified) — the fresh-seeded generator re-rolls
    the spent draws and stages a different turn-5 event.
    """
    monkeypatch.setenv("WARGAME_LLM", "mock")

    # Uninterrupted: five straight turns (4 and 5 generated).
    straight = GameManager(scenario_id="war_game_2025", variant="fast_start",
                           seed=42)
    for turn in range(1, 6):
        _play_turn(straight, turn)

    # Interrupted: four turns, a save/load round-trip, then turn five.
    interrupted = GameManager(scenario_id="war_game_2025", variant="fast_start",
                              seed=42)
    for turn in range(1, 5):
        _play_turn(interrupted, turn)
    resumed = GameManager.from_dict(interrupted.to_dict())
    _play_turn(resumed, 5)

    assert resumed.transcript == straight.transcript, (
        "a save/load round-trip changed the campaign"
    )
    assert snapshot_metrics(resumed.world.metrics) == snapshot_metrics(
        straight.world.metrics)


def test_old_payload_without_rng_state_still_loads():
    """A pre-ER-037 payload (no state.rng_state) restores exactly as before:
    fresh-seeded generator, no error."""
    gm = make_manager()
    gm.get_turn_briefing()
    payload = gm.to_dict()
    del payload["state"]["rng_state"]

    restored = GameManager.from_dict(payload)
    assert restored.world.turn == gm.world.turn
    # Fresh generator from the seed, the pre-2.3 behaviour.
    from random import Random
    assert restored.rng.getstate() == Random(gm.seed).getstate()


def test_mid_turn_load_replays_briefing_without_reapplying(monkeypatch):
    """ER-004: a save taken mid-turn (after the briefing ran) must replay the
    briefing for context on resume — same metrics, no re-applied effects, no
    duplicated ledger entry."""
    monkeypatch.setenv("WARGAME_LLM", "mock")

    gm = make_manager()
    gm.get_turn_briefing()
    gm.process_question("Who else knows about this?")  # phase -> discussion
    saved_metrics = snapshot_metrics(gm.world.metrics)
    saved_ledger = [e.dict() for e in gm.narrative_state.event_ledger]
    payload = gm.to_dict()

    resumed = GameManager.from_dict(payload)
    assert resumed._resume_replay is True

    resumed.get_turn_briefing()

    # Effects applied exactly once, not once per load.
    assert snapshot_metrics(resumed.world.metrics) == saved_metrics
    assert snapshot_metrics(resumed.narrative_state.hidden_metrics) == saved_metrics
    # The ledger entry was not re-recorded.
    assert [e.dict() for e in resumed.narrative_state.event_ledger] == saved_ledger
    # The replay flag is one-shot.
    assert resumed._resume_replay is False
