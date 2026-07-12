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
