"""Tests for the data-layer enum and the channel->layer map (models/layers.py).

The map must canonicalise every channel value observed in the wild:
scripted episodes use briefing/intelligence/emergency/flash_alert/diplomatic,
the inject generator prompt requests briefing/intelligence/media/military,
and the legacy display path knew intel/breaking.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from models.layers import (
    CHANNEL_LAYER_MAP, Layer, PLAYER_LAYERS, layer_for_channel,
)


def test_six_layers_exactly():
    assert {layer.value for layer in Layer} == {
        "sitrep", "intel", "diplomatic", "domestic", "cabinet", "referee",
    }


def test_player_layers_exclude_referee_only():
    assert Layer.REFEREE not in PLAYER_LAYERS
    assert PLAYER_LAYERS == frozenset(Layer) - {Layer.REFEREE}


@pytest.mark.parametrize("channel,expected", [
    # Scripted episode vocabulary (data/scenarios/war_game_2025/episodes)
    ("briefing", Layer.SITREP),
    ("intelligence", Layer.INTEL),
    ("emergency", Layer.SITREP),
    ("flash_alert", Layer.SITREP),
    ("diplomatic", Layer.DIPLOMATIC),
    # Generator prompt vocabulary (llm/prompts.py)
    ("media", Layer.DOMESTIC),
    ("military", Layer.SITREP),
    # Legacy display vocabulary (engine/sim_loop.display_inject)
    ("intel", Layer.INTEL),
    ("breaking", Layer.SITREP),
])
def test_observed_channels_map(channel, expected):
    assert layer_for_channel(channel) is expected


@pytest.mark.parametrize("variant", [
    "BRIEFING", "  briefing  ", "Flash-Alert", "FLASH_ALERT", "flash-alert",
])
def test_canonicalisation_of_case_space_and_hyphens(variant):
    assert layer_for_channel(variant) in (Layer.SITREP,)


def test_unknown_and_missing_channels_default_to_sitrep():
    assert layer_for_channel("carrier_pigeon") is Layer.SITREP
    assert layer_for_channel(None) is Layer.SITREP
    assert layer_for_channel("") is Layer.SITREP
    assert layer_for_channel(42) is Layer.SITREP  # type: ignore[arg-type]


def test_custom_default_is_honoured():
    assert layer_for_channel("no_such_channel", default=Layer.INTEL) is Layer.INTEL


def test_map_values_are_layers():
    assert all(isinstance(layer, Layer) for layer in CHANNEL_LAYER_MAP.values())
    # REFEREE is never an authored channel: nothing maps to it.
    assert Layer.REFEREE not in CHANNEL_LAYER_MAP.values()


def test_layer_serialises_as_its_value():
    # str-enum: json payloads and SSE tags use the bare value.
    assert Layer.SITREP.value == "sitrep"
    assert f"{Layer.CABINET.value}" == "cabinet"
