"""Tests for classic-mode terminal conditions and debrief."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.endings import check_ending, build_debrief_lines  # noqa: E402
from models.world import WorldState, Metrics  # noqa: E402


def make_world(turn=3, escalation=60, stability=50, cohesion=40):
    return WorldState(
        turn=turn,
        scene=turn,
        metrics=Metrics(
            escalation_risk=escalation,
            domestic_stability=stability,
            alliance_cohesion=cohesion,
            casualties_mil=2,
            casualties_civ=0,
        ),
        flags={},
        posture={},
    )


def test_no_ending_mid_campaign():
    assert check_ending(make_world(turn=3), final_turn=10) is None


def test_escalation_threshold_ends_in_war():
    ending = check_ending(make_world(escalation=100), final_turn=10)
    assert ending is not None and ending.ending_id == "war" and ending.verdict == "defeat"


def test_stability_collapse():
    ending = check_ending(make_world(stability=0), final_turn=10)
    assert ending is not None and ending.ending_id == "collapse"


def test_alliance_collapse():
    ending = check_ending(make_world(cohesion=0), final_turn=10)
    assert ending is not None and ending.ending_id == "isolation"


def test_scenario_end_graded_victory():
    ending = check_ending(make_world(turn=10, escalation=40, cohesion=60), final_turn=10)
    assert ending is not None and ending.verdict == "victory"


def test_scenario_end_graded_partial():
    ending = check_ending(make_world(turn=10, escalation=60, cohesion=40), final_turn=10)
    assert ending is not None and ending.ending_id == "uneasy_peace" and ending.verdict == "partial"


def test_scenario_end_graded_defeat():
    ending = check_ending(make_world(turn=10, escalation=80, cohesion=20), final_turn=10)
    assert ending is not None and ending.ending_id == "weakness" and ending.verdict == "defeat"


def test_debrief_includes_deltas_and_decisions():
    world = make_world(turn=10, escalation=75, stability=42, cohesion=35)
    ending = check_ending(world, final_turn=10)
    transcript = [
        "Prime Minister's Decision: Request NATO Article 4 consultations",
        "some other line",
        "Prime Minister's Decision: Deploy Type-45 destroyers",
    ]
    lines = build_debrief_lines(
        world, ending,
        initial_metrics={"escalation_risk": 60, "domestic_stability": 50, "alliance_cohesion": 40},
        transcript=transcript,
    )
    text = "\n".join(lines)
    assert "CAMPAIGN OVER" in text
    assert "(+15)" in text  # escalation 60 -> 75
    assert "Request NATO Article 4 consultations" in text
    assert "Deploy Type-45 destroyers" in text
