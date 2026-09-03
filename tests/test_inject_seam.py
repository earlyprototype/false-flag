"""Tests for GameManager.deliver_inject - the facilitator inject seam.

The one engine-boundary addition for the control surface: a manual inject
must behave like a scripted briefing inject (transcript lines, applied
effects, recent-injects memory, hidden-metrics sync) while leaving the
played-event ledger alone - adjudication closes the LAST staged ledger
entry, so a mid-turn second entry would misdirect the turn's verdict.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")


@pytest.fixture()
def manager():
    from engine.game_manager import GameManager
    gm = GameManager(seed=42)
    gm.get_turn_briefing()  # into discussion phase, ledger has turn 1's event
    return gm


def _inject(effects=None):
    return {
        "id": "manual_test",
        "title": "RUSSIAN AUXILIARY ALTERS COURSE",
        "channel": "intelligence",
        "description": "The auxiliary has turned south toward the cable corridor.\n\n"
                       "Defence intelligence assesses deliberate positioning.",
        "effects": effects or [],
    }


def test_deliver_inject_returns_lines_and_extends_transcript(manager):
    before = len(manager.transcript)
    result = manager.deliver_inject(_inject())

    assert result["title"] == "RUSSIAN AUXILIARY ALTERS COURSE"
    assert result["channel"] == "intelligence"
    assert result["lines"], "delivery produced no transcript lines"
    assert len(manager.transcript) > before
    joined = "\n".join(manager.transcript[before:])
    assert "RUSSIAN AUXILIARY ALTERS COURSE" in joined
    assert "cable corridor" in joined


def test_deliver_inject_records_recent_inject(manager):
    manager.deliver_inject(_inject())
    assert manager.world.recent_injects[-1] == "RUSSIAN AUXILIARY ALTERS COURSE"
    # The rolling window stays capped at 5, like the briefing path's.
    for i in range(7):
        manager.deliver_inject({**_inject(), "title": f"EVENT {i}"})
    assert len(manager.world.recent_injects) == 5
    assert manager.world.recent_injects[-1] == "EVENT 6"


def test_deliver_inject_applies_effects_with_difficulty_scaling(manager):
    """Effects go through apply_inject_effects: standard difficulty halves
    a +10 to +5, and the world metric moves."""
    before = manager.world.metrics.escalation_risk
    result = manager.deliver_inject(_inject(
        effects=[{"metric": "escalation_risk", "delta": 10}]))
    assert manager.world.metrics.escalation_risk == min(100, before + 5)
    assert any("Effect: " in line for line in result["lines"])


def test_deliver_inject_syncs_hidden_metrics(manager):
    """Adjudication copies hidden_metrics back over world.metrics at end of
    turn; an unsynced manual effect would be silently reverted."""
    manager.deliver_inject(_inject(
        effects=[{"metric": "escalation_risk", "delta": 10}]))
    assert (manager.narrative_state.hidden_metrics.escalation_risk
            == manager.world.metrics.escalation_risk)


def test_deliver_inject_without_effects_leaves_hidden_metrics_alone(manager):
    """A no-effect inject must not touch the vibes trend baseline
    (update_hidden_metrics snapshots previous_metrics)."""
    previous = manager.narrative_state.previous_metrics.copy()
    manager.deliver_inject(_inject())
    assert manager.narrative_state.previous_metrics == previous


def test_deliver_inject_does_not_touch_event_ledger(manager):
    """One ledger entry per turn is an adjudication invariant
    (record_event_disposition closes the LAST entry)."""
    ledger_before = list(manager.narrative_state.event_ledger)
    manager.deliver_inject(_inject(
        effects=[{"metric": "alliance_cohesion", "delta": -4}]))
    ledger_after = list(manager.narrative_state.event_ledger)
    assert len(ledger_after) == len(ledger_before)
    assert [e.title for e in ledger_after] == [e.title for e in ledger_before]


def test_delivered_inject_reaches_the_next_adjudication_unreverted(manager):
    """End to end through a real turn: the manual effect survives the
    decision's hidden->world metric copy-back."""
    manager.deliver_inject(_inject(
        effects=[{"metric": "casualties_civ", "delta": 3}]))
    assert manager.world.metrics.casualties_civ >= 3

    manager.resolve_decision("Hold the current posture and brief the Cabinet.")
    # Casualties only ever accumulate; the +3 must not have been reverted
    # by the adjudication copy-back.
    assert manager.world.metrics.casualties_civ >= 3
