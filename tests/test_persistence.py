"""Tests for save/load persistence: initial_metrics snapshot, variant, and
tolerance of old save formats."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.persistence import (  # noqa: E402
    load_game,
    read_save_field,
    read_save_variant,
    save_game,
)
from models.world import WorldState, Metrics  # noqa: E402


def make_world(turn=3):
    return WorldState(
        turn=turn,
        scene=turn,
        metrics=Metrics(
            escalation_risk=72,
            domestic_stability=44,
            alliance_cohesion=38,
            casualties_mil=2,
            casualties_civ=0,
        ),
        flags={},
        posture={},
    )


def test_save_round_trips_initial_metrics_and_variant(tmp_path):
    snapshot = {
        "escalation_risk": 60,
        "domestic_stability": 50,
        "alliance_cohesion": 40,
    }
    save_path = save_game(
        make_world(),
        transcript=["Turn 1 briefing"],
        scenario_id="war_game_2025",
        save_name="autosave",
        root_path=tmp_path,
        variant="fast_start",
        initial_metrics=snapshot,
    )

    assert read_save_field(save_path, "initial_metrics") == snapshot
    assert read_save_variant(save_path) == "fast_start"

    # The raw payload carries the snapshot and the bumped version
    raw = json.loads(save_path.read_text(encoding="utf-8"))
    assert raw["initial_metrics"] == snapshot
    assert raw["version"] == "2.2"

    # load_game still round-trips the world unchanged
    scenario_id, world, transcript, play_mode, narrative_state = load_game(save_path)
    assert scenario_id == "war_game_2025"
    assert world.turn == 3
    assert world.metrics.escalation_risk == 72
    assert transcript == ["Turn 1 briefing"]


def test_old_save_missing_keys_returns_defaults(tmp_path):
    # Pre-2.1 save: no variant, no initial_metrics
    old_save = tmp_path / "war_game_2025_old.json"
    old_save.write_text(json.dumps({
        "scenario_id": "war_game_2025",
        "world": make_world().model_dump(),
        "transcript": [],
        "version": "2.0",
    }), encoding="utf-8")

    assert read_save_variant(old_save) == "standard"
    assert read_save_field(old_save, "initial_metrics") is None
    assert read_save_field(old_save, "initial_metrics", {"escalation_risk": 60}) == {
        "escalation_risk": 60
    }

    # A stored explicit null also falls back to the default
    assert read_save_field(old_save, "narrative_state", "fallback") == "fallback"


def test_save_without_initial_metrics_reads_as_default(tmp_path):
    save_path = save_game(
        make_world(),
        transcript=[],
        scenario_id="war_game_2025",
        save_name="no_snapshot",
        root_path=tmp_path,
    )
    # Written as an explicit null; reader treats it as missing
    assert read_save_field(save_path, "initial_metrics") is None
    assert read_save_field(save_path, "initial_metrics", {"x": 1}) == {"x": 1}


def test_read_save_field_unreadable_file_returns_default(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    assert read_save_field(missing, "variant", "standard") == "standard"

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json", encoding="utf-8")
    assert read_save_field(corrupt, "initial_metrics", None) is None
    assert read_save_variant(corrupt) == "standard"
