"""Save/load completeness by construction, not by hand-kept field lists.

ER-047 (a live call dropped by save) and F1 (the pending-pushback memory
dropped by save) share one cause: a field added to the live object with
nobody remembering to serialize it. These tests introspect the LIVE
object's ``vars()`` against a restored copy, so the next such field fails
CI at feature-add time - the author either serializes it or adds it to
the ephemeral whitelist below with a stated reason.

Also here: the F2 regression (a save taken after the briefing but before
the first question used to resume as NOT-a-replay, re-applying the
inject's effects and re-opening the mandatory call) and the F4 regression
(a graded campaign's CLI autosave resumed as a playable game).
"""

import json
from random import Random

import pytest

from engine.game_manager import GameManager

# Attributes DELIBERATELY not serialized. Adding an attribute to
# GameManager without serializing it or whitelisting it here fails
# test_every_live_manager_attribute_survives_a_round_trip.
EPHEMERAL_MANAGER_FIELDS = {
    "root_path",           # machine-local; recomputed in __init__
    "initial_conditions",  # static scenario data, reloaded from disk
    "scenario_config",     # static scenario data, reloaded from disk
    "_resume_replay",      # derived by from_dict from world.phase
}

# DiplomaticEncounter attributes that are re-wired or re-derived on load.
EPHEMERAL_ENCOUNTER_FIELDS = {
    "world", "narrative_state", "full_transcript",       # re-wired refs
    "root_path",                                          # machine-local
    "profiles", "profile", "access_level",                # re-derived from world
    "title", "max_exchanges",                             # re-derived
    "active",                                             # by construction: only live calls saved
    "outcome",                                            # ended calls deliberately unsaved
}

_MISSING = object()


def _equivalent(a, b):
    if hasattr(a, "dict") and callable(getattr(a, "dict", None)):
        try:
            return a.dict() == b.dict()
        except Exception:
            pass
    if isinstance(a, Random):
        return a.getstate() == b.getstate()
    return a == b


def played_manager() -> GameManager:
    """A session with every stateful feature exercised.

    The fixture must populate the optional fields - a dropped field whose
    live value is still its default compares equal and hides.
    """
    gm = GameManager(seed=7, play_mode="classic", mystery_mode=True)
    gm.world.turn = 6                 # turn with the scripted mandatory call
    gm.get_turn_briefing()            # inject applied, call opened
    gm.process_question("CDS, what are our options?")
    gm.interpret_decision("Blockade the strait.")     # arms _pending_pushback
    gm.process_diplomacy("We stand with NATO.")       # live-encounter state
    return gm


def roundtrip(gm: GameManager) -> GameManager:
    payload = json.loads(json.dumps(gm.to_dict(), default=str))
    return GameManager.from_dict(payload)


class TestCompletenessByConstruction:
    def test_every_live_manager_attribute_survives_a_round_trip(self):
        gm = played_manager()
        restored = roundtrip(gm)
        for name, value in vars(gm).items():
            if name in EPHEMERAL_MANAGER_FIELDS:
                continue
            if name == "active_encounter":
                continue  # compared field-by-field below
            restored_value = getattr(restored, name, _MISSING)
            assert restored_value is not _MISSING and _equivalent(value, restored_value), (
                f"GameManager.{name} does not survive to_dict/from_dict - "
                f"serialize it or whitelist it in EPHEMERAL_MANAGER_FIELDS "
                f"with a reason (live={value!r})")

    def test_every_live_encounter_attribute_survives_a_round_trip(self):
        gm = played_manager()
        assert gm.active_encounter is not None and gm.active_encounter.active
        restored = roundtrip(gm)
        live, back = gm.active_encounter, restored.active_encounter
        assert back is not None
        for name, value in vars(live).items():
            if name in EPHEMERAL_ENCOUNTER_FIELDS:
                continue
            restored_value = getattr(back, name, _MISSING)
            assert restored_value is not _MISSING and _equivalent(value, restored_value), (
                f"DiplomaticEncounter.{name} does not survive the round-trip - "
                f"serialize it in _encounter_state or whitelist it")

    def test_the_rng_is_anchored_and_draws_identically(self):
        gm = played_manager()
        restored = roundtrip(gm)
        assert restored.rng.getstate() == gm.rng.getstate()
        assert restored.rng.random() == gm.rng.random()

    def test_actor_system_state_survives(self):
        gm = played_manager()
        gm.world.actor_system.actors["RUS"].relationship_uk = 5
        gm.world.actor_system.actors["RUS"].recent_actions.append("Snap exercise")
        restored = roundtrip(gm)
        rus = restored.world.actor_system.actors["RUS"]
        assert rus.relationship_uk == 5
        assert "Snap exercise" in rus.recent_actions


class TestPendingPushbackSurvives:
    def test_the_trust_cost_survives_interpret_save_load_commit(self):
        gm = played_manager()
        if not gm._pending_pushback:
            gm._pending_pushback = ("Blockade the strait.", ["Foreign Secretary"])
        text, roles = gm._pending_pushback
        restored = roundtrip(gm)
        assert restored._pending_pushback == (text, list(roles))


class TestBriefingPhaseAdvance:
    """F2: a save taken right after the briefing must resume as a replay."""

    def test_phase_leaves_briefing_when_the_briefing_ends(self):
        gm = GameManager(seed=11)
        gm.get_turn_briefing()
        assert gm.world.phase == "discussion"

    def test_a_start_of_turn_save_does_not_double_apply_the_inject(self):
        gm = GameManager(seed=11)
        gm.get_turn_briefing()
        metrics_before = gm.world.metrics.dict()

        restored = roundtrip(gm)
        assert restored._resume_replay is True
        restored.get_turn_briefing()   # replay: must not re-apply effects
        assert restored.world.metrics.dict() == metrics_before

    def test_a_restored_mandatory_call_is_not_replaced_by_a_fresh_one(self):
        gm = GameManager(seed=42, play_mode="classic")
        gm.world.turn = 6
        gm.get_turn_briefing()
        gm.process_diplomacy("We are coordinating fully with NATO.")
        lines_before = list(gm.active_encounter.transcript)

        restored = roundtrip(gm)
        restored.get_turn_briefing()   # replay: must keep the restored call
        assert restored.active_encounter is not None
        assert restored.active_encounter.transcript == lines_before


class TestEndedCampaignAutosave:
    """F4: the CLI format now records the ending, and the resume offer
    treats a graded campaign as a record rather than a live game."""

    def test_ending_id_round_trips_through_the_cli_format(self, tmp_path):
        from engine.persistence import read_save_field, save_game

        gm = GameManager(seed=3)
        path = save_game(
            gm.world, ["line"], gm.scenario_id, "autosave",
            root_path=tmp_path, narrative_state=gm.narrative_state,
            rng=gm.rng, seed=3, ending_id="strategic_defeat")
        assert read_save_field(path, "ending_id") == "strategic_defeat"
        assert read_save_field(path, "seed") == 3

    def test_an_unfinished_save_stores_no_ending(self, tmp_path):
        from engine.persistence import read_save_field, save_game

        gm = GameManager(seed=3)
        path = save_game(
            gm.world, ["line"], gm.scenario_id, "autosave",
            root_path=tmp_path, narrative_state=gm.narrative_state,
            rng=gm.rng, seed=3)
        assert read_save_field(path, "ending_id") is None
