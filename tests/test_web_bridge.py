"""Tests for the browser build's engine side.

Two things are under test here:

* ``engine.game_manager`` now owns campaign termination. Before this, a
  headless session could never finish: ``engine.endings.check_ending`` was
  only ever called from ``cli/main.py``, so the browser and API front ends
  had no way to reach a verdict.
* ``docs/py/bridge.py`` — the Python half of the Web Worker. It is
  plain Python with an injected ``emit`` callback, so the whole page<->worker
  protocol can be driven from pytest without a browser.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from engine.endings import Ending
from engine.game_manager import GameManager

REPO = Path(__file__).resolve().parents[1]
BRIDGE_PATH = REPO / "docs" / "py" / "bridge.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("ff_web_bridge", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ff_web_bridge"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")
    import llm.router as router
    router._driver_cache.clear()
    yield
    router._driver_cache.clear()


DECISION = "Reinforce air defence, hold the line, and seek allied consultation."


# ---------------------------------------------------------------------------
# GameManager: endings
# ---------------------------------------------------------------------------

def test_campaign_final_turn_matches_cli_formula():
    gm = GameManager(variant="fast_start", play_mode="classic")
    cfg = gm.scenario_config
    expected = (cfg["stochastic_from"] - 1) + cfg["epilogue_turns"]
    assert gm.campaign_final_turn == expected


def test_endings_default_to_classic_only():
    """Default behaviour must not change for existing (CLI/API) callers."""
    assert GameManager(play_mode="immersive").endings_enabled is False
    assert GameManager(play_mode="emergent").endings_enabled is False
    assert GameManager(play_mode="classic").endings_enabled is True
    assert GameManager(play_mode="immersive", endings=True).endings_enabled is True


def test_threshold_ending_fires_from_resolve_decision():
    gm = GameManager(variant="fast_start", play_mode="classic", seed=5, endings=True)
    gm.get_turn_briefing()
    # Push escalation over the top; the check runs inside resolve_decision.
    gm.world.metrics.escalation_risk = 100
    gm.narrative_state.hidden_metrics.escalation_risk = 100
    result = gm.resolve_decision("Authorise strikes on the Northern Fleet.")

    assert result["ending"] is not None
    assert result["ending"]["ending_id"] == "war"
    assert result["ending"]["verdict"] == "defeat"
    assert gm.is_over()
    assert any("CAMPAIGN OVER" in line for line in gm.get_debrief_lines())


def test_campaign_reaches_an_ending_by_the_final_turn():
    """A whole game, played start to finish, must actually terminate."""
    gm = GameManager(variant="fast_start", play_mode="classic", seed=3, endings=True)
    for _ in range(gm.campaign_final_turn + 3):
        gm.get_turn_briefing()
        gm.resolve_decision(DECISION)
        if gm.is_over():
            break

    assert gm.is_over(), "campaign never reached a terminal ending"
    assert gm.ending.verdict in {"victory", "partial", "defeat"}
    debrief = gm.get_debrief_lines()
    assert any(gm.ending.title in line for line in debrief)
    assert any("YOUR DECISIONS" in line for line in debrief)


def test_debrief_deltas_measure_from_campaign_start():
    gm = GameManager(variant="fast_start", play_mode="classic", seed=9, endings=True)
    start = dict(gm.initial_metrics_snapshot)
    for _ in range(3):
        gm.get_turn_briefing()
        gm.resolve_decision(DECISION)
        if gm.is_over():
            break

    # The snapshot must still describe the start of the campaign, not
    # wherever the campaign happens to be now.
    assert gm.initial_metrics_snapshot == start
    assert gm.world.metrics.escalation_risk != start["escalation_risk"]

    gm.ending = gm.ending or Ending("t", "TEST", "partial", "n")
    debrief = "\n".join(gm.get_debrief_lines())
    expected = gm.world.metrics.escalation_risk - start["escalation_risk"]
    assert f"({expected:+d})" in debrief


def test_mystery_mode_draws_a_hidden_narrative():
    plain = GameManager(seed=11)
    assert plain.world.narrative is None

    mystery = GameManager(seed=11, mystery_mode=True)
    assert mystery.world.narrative is not None
    assert mystery.world.narrative.narrative_id

    # Deterministic for a given seed.
    again = GameManager(seed=11, mystery_mode=True)
    assert again.world.narrative.narrative_id == mystery.world.narrative.narrative_id


def test_session_round_trips_through_to_dict():
    gm = GameManager(variant="fast_start", play_mode="classic", seed=4,
                     mystery_mode=True, endings=True)
    gm.get_turn_briefing()
    gm.resolve_decision(DECISION)

    import json
    blob = json.dumps(gm.to_dict("unit-test"), default=str)
    restored = GameManager.from_dict(json.loads(blob))

    assert restored.world.turn == gm.world.turn
    assert restored.play_mode == gm.play_mode
    assert restored.variant == gm.variant
    assert restored.mystery_mode is True
    assert restored.endings_enabled is True
    assert restored.world.narrative.narrative_id == gm.world.narrative.narrative_id
    assert restored.initial_metrics_snapshot == gm.initial_metrics_snapshot
    assert restored.world.metrics.escalation_risk == gm.world.metrics.escalation_risk
    # An unfinished campaign must not come back looking finished.
    assert restored.ending is None
    assert restored.is_over() is False


def test_ended_campaign_round_trips_as_ended():
    """A finished campaign must load as finished.

    to_dict persists only ``ending_id``; if from_dict does not rebuild the
    Ending from it, is_over() answers False on the restored session and the
    browser build resumes a graded game instead of showing the ending.
    """
    import json

    gm = GameManager(variant="fast_start", play_mode="classic", seed=3,
                     endings=True)
    for _ in range(30):
        gm.get_turn_briefing()
        gm.resolve_decision(DECISION)
        if gm.is_over():
            break
    assert gm.is_over(), "campaign never reached an ending — test is vacuous"

    blob = json.dumps(gm.to_dict("unit-test"), default=str)
    restored = GameManager.from_dict(json.loads(blob))

    assert restored.is_over() is True
    assert restored.ending is not None
    assert restored.ending.ending_id == gm.ending.ending_id
    assert restored.ending.verdict == gm.ending.verdict
    assert restored.ending.title == gm.ending.title
    # The debrief must be reproducible from the restored session too.
    assert any(restored.ending.title in line
               for line in restored.get_debrief_lines())


def test_unknown_ending_id_loads_as_a_playable_session():
    """A save naming an ending this build does not have must still load."""
    import json

    gm = GameManager(variant="fast_start", play_mode="classic", seed=4,
                     endings=True)
    gm.get_turn_briefing()
    gm.resolve_decision(DECISION)
    data = json.loads(json.dumps(gm.to_dict("unit-test"), default=str))
    data["state"]["ending_id"] = "an_ending_from_the_future"

    restored = GameManager.from_dict(data)
    assert restored.ending is None
    assert restored.is_over() is False


# ---------------------------------------------------------------------------
# bridge.WebGame: the page<->worker protocol
# ---------------------------------------------------------------------------

class Recorder:
    def __init__(self):
        self.msgs = []

    def __call__(self, msg):
        self.msgs.append(msg)

    def of(self, kind):
        return [m for m in self.msgs if m["type"] == kind]

    def last(self, kind):
        got = self.of(kind)
        assert got, f"no {kind!r} message emitted"
        return got[-1]

    def ansi(self):
        return "\n".join(m["ansi"] for m in self.of("output"))

    def clear(self):
        self.msgs.clear()


def play_through_pauses(game, rec, limit=20):
    """Advance past any paced beats to whatever the player can act on next.

    The opening and each briefing arrive a beat at a time (engine/opening.py);
    most tests here are about what happens once the player can act again.
    """
    for _ in range(limit):
        if rec.last("awaiting")["kind"] != "pause":
            return
        game.handle({"type": "continue"})
    raise AssertionError(f"still paused after {limit} beats")


def make_game(**config):
    rec = Recorder()
    game = bridge.WebGame(rec)
    cfg = {"scenario": "fast_start", "playMode": "classic", "seed": 3}
    cfg.update(config)
    game.handle({"type": "newGame", "config": cfg})
    play_through_pauses(game, rec)
    return game, rec


def test_new_game_emits_output_state_and_awaiting():
    game, rec = make_game()

    assert rec.of("output"), "no game text emitted"
    assert rec.last("awaiting")["kind"] == "decision"
    state = rec.last("state")
    assert state["turn"] == 1
    assert state["metricsVisible"] is True
    assert state["metrics"]["escalation_risk"] > 0
    assert state["finalTurn"] == game.gm.campaign_final_turn


def make_unpaced_game(**config):
    """A game parked on the first beat of the cold open, as the page finds it."""
    rec = Recorder()
    game = bridge.WebGame(rec)
    cfg = {"scenario": "fast_start", "playMode": "classic", "seed": 3}
    cfg.update(config)
    game.handle({"type": "newGame", "config": cfg})
    return game, rec


def test_the_cold_open_plays_before_the_first_briefing():
    """The campaign used to open on the briefing: five crises, no lead-in."""
    game, rec = make_unpaced_game()

    assert rec.last("awaiting")["kind"] == "pause"
    opening = rec.ansi()
    assert "SEVEROMORSK" in opening, "the cold open did not play"
    assert "TURN 1" not in opening, "the briefing arrived before the cold open"


def test_each_continue_advances_exactly_one_beat():
    game, rec = make_unpaced_game()
    seen = [rec.ansi()]

    for _ in range(3):
        game.handle({"type": "continue"})
        seen.append(rec.ansi())

    assert "NORTHWOOD" in seen[1]
    assert "COBRA" in seen[2]
    assert "YOUR ROLE" in seen[3]
    assert rec.last("awaiting")["kind"] == "pause", "still mid-opening"
    assert "TURN 1" not in seen[3], "the briefing must wait its turn"


def test_the_briefing_pauses_between_the_room_and_the_report():
    """The room is set, then the news — not both at once."""
    game, rec = make_unpaced_game()
    for _ in range(4):           # through the four cold-open beats
        game.handle({"type": "continue"})

    assert "TURN 1" in rec.ansi()
    assert rec.last("awaiting")["kind"] == "pause"
    assert "YOUR MOVE" not in rec.ansi(), "the turn opened before the report"

    game.handle({"type": "continue"})
    assert rec.last("awaiting")["kind"] == "decision"
    assert "YOUR MOVE" in rec.ansi()


def test_loading_mid_cold_open_does_not_leak_beats_into_the_resumed_game():
    """Beats queued by the abandoned campaign must not fire into the new one."""
    donor, donor_rec = make_game()
    donor.handle({"type": "save"})
    blob = donor_rec.last("save")["data"]

    game, rec = make_unpaced_game()          # parked on the first beat
    assert rec.last("awaiting")["kind"] == "pause"
    game.handle({"type": "load", "data": blob})

    rec.clear()
    game.handle({"type": "continue"})
    assert "SEVEROMORSK" not in rec.ansi(), "a stale beat fired into the resumed game"
    assert "NORTHWOOD" not in rec.ansi(), "a stale beat fired into the resumed game"


def test_ask_all_puts_the_question_to_the_whole_room():
    game, rec = make_game()
    rec.clear()
    game.handle({"type": "ask", "advisor": "all",
                 "text": "Where do we actually stand?"})

    out = rec.ansi()
    # The question renders once, as the Prime Minister speaking.
    assert out.count("PRIME MINISTER") == 1
    # Every seated advisor answers as their own speaker block.
    for role in ("MILITARY COMMANDER", "INTELLIGENCE COORDINATOR",
                 "DOMESTIC SECURITY", "DIPLOMATIC LEAD", "LEGAL ADVISOR"):
        assert role in out, f"{role} did not answer"
    assert rec.last("awaiting")["kind"] == "decision"


def test_state_offers_the_whole_room_option():
    game, rec = make_game()
    advisors = rec.last("state")["advisors"]
    assert advisors[-1]["id"] == "all", \
        "the picker must offer asking the whole room"
    assert {a["id"] for a in advisors} > {"all"}, "and the advisors themselves"


def _instant_outputs(rec):
    """The 'output' messages marked for the page to show whole (no typewriter)."""
    return [m for m in rec.of("output") if m.get("instant") is True]


def _typed_outputs(rec):
    """The 'output' messages the page's typewriter reveal paces."""
    return [m for m in rec.of("output") if m.get("instant") is not True]


def test_chrome_output_carries_the_instant_marker():
    """Masthead and prompts are chrome: the page must not typewrite them."""
    game, rec = make_game()

    instant = "\n".join(m["ansi"] for m in _instant_outputs(rec))
    assert "FALSE FLAG" in instant, "the masthead must be marked instant"
    assert "YOUR MOVE" in instant, "the prompt must be marked instant"


def test_narrative_output_is_not_marked_instant():
    """Scene beats and briefing prose are what the typewriter exists for."""
    game, rec = make_unpaced_game()
    for _ in range(4):
        game.handle({"type": "continue"})

    typed = "\n".join(m["ansi"] for m in _typed_outputs(rec))
    assert "SEVEROMORSK" in typed, "the cold open must stay revealable"
    assert "TURN 1" in typed, "the briefing must stay revealable"
    # And the marker, when present, is only ever boolean True — the page
    # tests `m.instant === true`, so any other truthy value would lie.
    for m in rec.of("output"):
        assert m.get("instant") in (None, True)


def test_set_key_note_is_marked_instant():
    rec = Recorder()
    game = bridge.WebGame(rec)
    game.handle({"type": "setKey", "key": "", "source": ""})

    # Picked out by content, not position: handle()'s finally can append a
    # fault report left behind by an earlier test in the same process.
    notes = [m for m in rec.of("output") if "OFFLINE MODE" in m["ansi"]]
    assert notes, "no provider note emitted"
    assert notes[0].get("instant") is True


def test_a_continue_with_nothing_queued_does_not_strand_the_page():
    """A double space-press must not disable every control.

    handle() marks the session busy before dispatch, so a `continue` that
    finds an empty queue has to put the awaiting state back itself.
    """
    game, rec = make_game()      # already played through to the decision
    game.handle({"type": "continue"})
    assert rec.last("awaiting")["kind"] == "decision"


def _force_split_briefing(game):
    """Make the next briefing carry the NSA handover, as a real one would."""
    real = game.gm.get_turn_briefing

    def splitting(*args, **kwargs):
        inject = real(*args, **kwargs)
        inject["description"] = (
            "The room is windowless and tense.\n"
            "The National Security Advisor clears their throat and begins:\n"
            '"Prime Minister, in the past 48 hours..."'
        )
        return inject

    game.gm.get_turn_briefing = splitting


def test_a_split_briefing_from_end_turn_still_pauses():
    """run_briefing() must not be called directly, or the page strands.

    play_next() is the only thing that publishes AWAIT_PAUSE. A briefing that
    parks its report beat and is started outside the queue left the page on
    AWAIT_NONE with a beat pending — every control disabled, reload the only
    way out.
    """
    game, rec = make_game()
    _force_split_briefing(game)

    game.handle({"type": "decide", "text": "Hold current posture."})
    rec.clear()                  # turn 1's YOUR MOVE is already on the record
    game.handle({"type": "endTurn"})

    assert rec.last("awaiting")["kind"] == "pause"
    assert "YOUR MOVE" not in rec.ansi(), "the turn opened before the report"

    game.handle({"type": "continue"})
    assert rec.last("awaiting")["kind"] == "decision"


def test_a_split_briefing_after_a_load_still_pauses():
    donor, donor_rec = make_game()
    donor.handle({"type": "save"})
    blob = donor_rec.last("save")["data"]

    game, rec = make_game()
    _force_split_briefing(game)
    game.handle({"type": "load", "data": blob})

    assert rec.last("awaiting")["kind"] == "pause"
    game.handle({"type": "continue"})
    assert rec.last("awaiting")["kind"] == "decision"


def test_output_is_raw_ansi_not_html():
    _, rec = make_game()
    text = rec.ansi()
    assert "\x1b[" in text, "output carries no ANSI escapes"
    assert "<span" not in text and "<div" not in text


def test_immersive_mode_hides_metrics():
    _, rec = make_game(playMode="immersive")
    state = rec.last("state")
    assert state["metricsVisible"] is False
    assert state["metrics"] is None
    assert state["vibes"], "qualitative read-out should still be provided"


def test_immersive_output_never_prints_the_numbers():
    game, rec = make_game(playMode="immersive")
    rec.clear()
    game.handle({"type": "decide", "text": DECISION})
    text = rec.ansi()
    m = game.gm.world.metrics
    assert "Escalation Risk" not in text
    assert f"escalation_risk: {m.escalation_risk}" not in text
    assert "THE MOOD IN THE ROOM" in text


def test_metric_deltas_are_coloured_by_metric_not_by_sign():
    """A rise is not automatically an alert.

    Escalation risk and casualties going up is bad news; domestic stability
    and alliance cohesion going up is good news. Colouring every '+N' the
    same way tells a classic-mode player the opposite of the truth for half
    the board, and disagrees with the terminal build.
    """
    from engine.utils import delta_is_good

    assert bridge._delta("escalation_risk", 7) == bridge._c(bridge.ACCENT, "+7")
    assert bridge._delta("escalation_risk", -7) == bridge._c(bridge.TEAL, "-7")
    assert bridge._delta("casualties_civ", 3) == bridge._c(bridge.ACCENT, "+3")

    assert bridge._delta("domestic_stability", 5) == bridge._c(bridge.TEAL, "+5")
    assert bridge._delta("domestic_stability", -5) == bridge._c(bridge.ACCENT, "-5")
    assert bridge._delta("alliance_cohesion", 4) == bridge._c(bridge.TEAL, "+4")

    assert bridge._delta("escalation_risk", 0) == bridge._c(bridge.DIM, "0")
    # A metric with no declared polarity claims nothing.
    assert delta_is_good("some_new_metric", 3) is None
    assert bridge._delta("some_new_metric", 3) == bridge._c(bridge.AMBER, "+3")


def test_decide_then_end_turn_advances():
    game, rec = make_game()
    rec.clear()

    game.handle({"type": "decide", "text": DECISION})
    assert rec.last("awaiting")["kind"] == "confirm"
    assert rec.last("state")["turn"] == 2

    rec.clear()
    game.handle({"type": "endTurn"})
    assert rec.last("awaiting")["kind"] == "decision"
    assert "TURN 2" in rec.ansi()


def test_end_turn_without_a_decision_still_resolves_the_turn():
    game, rec = make_game()
    turn = game.gm.world.turn
    rec.clear()
    game.handle({"type": "endTurn"})
    assert game.gm.world.turn == turn + 1
    assert rec.last("awaiting")["kind"] == "confirm"


def test_ask_routes_to_the_named_advisor():
    game, rec = make_game()
    rec.clear()
    game.handle({"type": "ask", "advisor": "chief_defence_staff",
                 "text": "What can we put to sea tonight?"})
    text = rec.ansi()
    assert "DISCUSSION" in text
    assert "PRIME MINISTER" in text
    assert rec.last("awaiting")["kind"] == "decision"
    assert any("Prime Minister: CDS," in line for line in game.gm.transcript)


def test_call_opens_a_line_and_stays_open():
    game, rec = make_game()
    rec.clear()
    game.handle({"type": "call", "country": "USA", "text": "We need Article 5 clarity."})
    assert rec.last("awaiting")["kind"] == "question"
    assert "DIPLOMATIC CALL" in rec.ansi()

    rec.clear()
    game.handle({"type": "call", "country": "USA", "text": "Thank you"})
    assert rec.last("awaiting")["kind"] == "decision"
    assert "CALL ENDED" in rec.ansi()


def test_mandatory_call_puts_the_player_on_the_line():
    """The scripted turn-6 encounter must be played BY the player (ER-033):
    the briefing lands in awaiting-question with the incoming-call header,
    decisions are refused until the call ends, and the call is drivable
    through the ordinary `call` message."""
    game, rec = make_game(scenario="standard")
    game.gm.world.turn = 6
    rec.clear()
    game.start_briefing()
    play_through_pauses(game, rec)

    assert rec.last("awaiting")["kind"] == "question"
    text = rec.ansi()
    assert "INCOMING CALL" in text
    assert "YOU MUST TAKE THIS" in text
    assert "DIPLOMATIC CALL" in text
    # Nobody answered in the player's name.
    assert not any(line.startswith("Prime Minister:")
                   for line in game.gm.active_encounter.transcript)

    # The turn is not open while the President is waiting.
    rec.clear()
    game.handle({"type": "decide", "text": DECISION})
    assert "waiting on the line" in rec.last("error")["message"]
    assert rec.last("awaiting")["kind"] == "question"

    rec.clear()
    game.handle({"type": "ask", "advisor": "chief_defence_staff",
                 "text": "Can we stall him?"})
    assert "waiting on the line" in rec.last("error")["message"]
    assert rec.last("awaiting")["kind"] == "question"

    # The player takes the call and hangs up; the turn opens.
    rec.clear()
    game.handle({"type": "call", "text": "We are coordinating fully with NATO."})
    assert rec.last("awaiting")["kind"] == "question"
    game.handle({"type": "call", "text": "Thank you, goodbye."})
    assert "CALL ENDED" in rec.ansi()
    assert rec.last("awaiting")["kind"] == "decision"
    assert game.gm.active_encounter.outcome is not None


def test_call_without_a_message_opens_the_line_counterpart_first():
    """The two-stage outbound flow: `call usa` with nothing to say opens the
    line, the counterpart speaks first, and the page is told the line is
    open — the same shape as the scripted required call."""
    game, rec = make_game()
    rec.clear()
    game.handle({"type": "call", "country": "USA", "text": ""})

    assert rec.last("awaiting")["kind"] == "question"
    text = rec.ansi()
    assert "DIPLOMATIC CALL" in text
    assert "The line is open" in text
    assert "PRIME MINISTER" not in text, "nobody has spoken for the player"
    assert not any(line.startswith("Prime Minister:")
                   for line in game.gm.active_encounter.transcript)

    # The next input is spoken on the call.
    rec.clear()
    game.handle({"type": "call", "country": "USA", "text": "Are you with us?"})
    assert rec.last("awaiting")["kind"] == "question"
    assert "PRIME MINISTER" in rec.ansi()


def test_open_line_then_hangup_without_speaking_costs_nothing():
    game, rec = make_game()
    game.handle({"type": "call", "country": "USA", "text": ""})
    cohesion = game.gm.world.metrics.alliance_cohesion

    rec.clear()
    game.handle({"type": "call", "country": "USA", "text": "end"})

    assert rec.last("awaiting")["kind"] == "decision"
    assert "CALL ENDED" in rec.ansi()
    assert game.gm.active_encounter.active is False
    assert game.gm.world.metrics.alliance_cohesion == cohesion, \
        "a zero-exchange call must not move the metrics"


def test_call_to_an_unknown_country_fails_in_fiction():
    game, rec = make_game()
    rec.clear()
    game.handle({"type": "call", "country": "ZZZ", "text": "Hello?"})
    assert "switchboard" in rec.ansi()
    assert rec.last("awaiting")["kind"] == "decision"


def test_full_playthrough_emits_an_ending():
    game, rec = make_game(seed=3)
    for _ in range(30):
        game.handle({"type": "decide", "text": DECISION})
        if rec.of("ending"):
            break
        game.handle({"type": "endTurn"})

    ending = rec.last("ending")
    assert ending["verdict"] in {"victory", "partial", "defeat"}
    assert ending["title"]
    assert "CAMPAIGN OVER" in ending["debrief"]
    assert rec.last("awaiting")["kind"] == "none"
    assert rec.last("state")["over"] is True


def test_save_and_load_round_trip():
    game, rec = make_game()
    game.handle({"type": "decide", "text": DECISION})
    game.handle({"type": "endTurn"})
    rec.clear()

    game.handle({"type": "save"})
    blob = rec.last("save")["data"]
    assert rec.of("saved"), "both save spellings should be emitted"

    rec2 = Recorder()
    fresh = bridge.WebGame(rec2)
    fresh.handle({"type": "load", "data": blob})
    assert fresh.gm.world.turn == game.gm.world.turn
    assert rec2.last("awaiting")["kind"] == "decision"


def test_set_key_switches_provider_and_back():
    game, rec = make_game()
    import llm.router as router

    game.handle({"type": "setKey", "key": "sk-or-v1-not-a-real-key",
                 "baseUrl": "http://127.0.0.1:9/v1", "model": "test/model"})
    assert router._get_provider() == "openai_compat"

    game.handle({"type": "setKey", "key": ""})
    assert router._get_provider() == "mock"
    import os
    assert "OPENAI_COMPAT_API_KEY" not in os.environ


def test_shared_key_source_cannot_be_pointed_at_another_endpoint(monkeypatch):
    """ER-028 hard rule: the shared key only ever talks to OpenRouter.

    A hostile baseUrl in the message is discarded, and so is a custom
    endpoint an earlier own-key session left in the environment. The model
    choice, by contrast, is honoured.
    """
    import os

    # A leftover from an earlier own-key session must not leak through.
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "http://leftover.example/v1")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "leftover/model")

    game, rec = make_game()
    game.handle({"type": "setKey", "key": "sk-or-v1-not-a-real-key",
                 "source": "shared",
                 "baseUrl": "https://evil.example/steal/v1",
                 "model": "openai/gpt-4o-mini"})

    assert os.environ["OPENAI_COMPAT_BASE_URL"] == bridge.OPENROUTER_BASE_URL
    assert os.environ["OPENAI_COMPAT_MODEL"] == "openai/gpt-4o-mini"

    game.handle({"type": "setKey", "key": ""})


def test_own_key_source_honours_model_and_endpoint(monkeypatch):
    """The player's own key may go wherever they point it; the play page's
    model choice must reach OPENAI_COMPAT_MODEL for both sources."""
    import os

    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPAT_MODEL", raising=False)

    game, rec = make_game()
    game.handle({"type": "setKey", "key": "sk-or-v1-not-a-real-key",
                 "source": "own",
                 "baseUrl": "http://127.0.0.1:11434/v1",
                 "model": "llama3.1:8b"})
    assert os.environ["OPENAI_COMPAT_BASE_URL"] == "http://127.0.0.1:11434/v1"
    assert os.environ["OPENAI_COMPAT_MODEL"] == "llama3.1:8b"

    # Without an explicit endpoint or model, the defaults stand.
    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPAT_MODEL", raising=False)
    game.handle({"type": "setKey", "key": "sk-or-v1-not-a-real-key",
                 "source": "own"})
    assert os.environ["OPENAI_COMPAT_BASE_URL"] == bridge.OPENROUTER_BASE_URL
    assert os.environ["OPENAI_COMPAT_MODEL"] == "openai/gpt-4o-mini"

    game.handle({"type": "setKey", "key": ""})


def test_commands_before_new_game_error_instead_of_crashing():
    rec = Recorder()
    game = bridge.WebGame(rec)
    game.handle({"type": "decide", "text": "Do something"})
    assert rec.last("error")["message"].startswith("No game in progress")
    assert rec.last("error")["fatal"] is False


def test_unknown_message_type_is_reported_not_fatal():
    game, rec = make_game()
    rec.clear()
    game.handle({"type": "teleport"})
    assert "Unknown message type" in rec.last("error")["message"]
    # ...and it must not strand the player: the page blocks input on 'none'.
    assert rec.last("awaiting")["kind"] == "decision"


@pytest.mark.parametrize("msg, expected_error", [
    ({"type": "decide", "text": "   "}, "Empty decision."),
    ({"type": "ask", "advisor": "chief_defence_staff", "text": ""},
     "Empty question."),
    ({"type": "call", "country": "", "text": "hello"},
     "No country given for the diplomatic call."),
    ({"type": "teleport"}, "Unknown message type: 'teleport'"),
])
def test_a_rejected_message_does_not_lock_the_ui(msg, expected_error):
    """Every rejection path must restore the player's position.

    ``handle`` sets ``awaiting`` to 'none' (busy) before dispatching, so a
    rejection that re-emits ``self.awaiting`` emits 'none' — and worker.js
    blocks all input on 'none', making a page reload the only recovery.
    """
    game, rec = make_game()
    rec.clear()
    game.handle(msg)

    assert rec.last("error")["message"] == expected_error
    assert rec.last("awaiting")["kind"] == "decision"
    assert game.awaiting == "decision"

    # And the session is genuinely still playable afterwards.
    rec.clear()
    game.handle({"type": "decide", "text": DECISION})
    assert rec.last("awaiting")["kind"] in ("confirm", "none")
    assert not [m for m in rec.of("error")]


def test_a_rejection_mid_call_returns_to_the_call_not_the_turn():
    """A live diplomatic call is a distinct position; keep the player in it."""
    game, rec = make_game()
    game.handle({"type": "call", "country": "USA", "text": None})
    if rec.last("awaiting")["kind"] != "question":
        pytest.skip("no live encounter opened for USA in this seed")
    rec.clear()

    game.handle({"type": "teleport"})
    assert rec.last("awaiting")["kind"] == "question"


def test_engine_exception_leaves_the_player_able_to_act(monkeypatch):
    game, rec = make_game()
    monkeypatch.setattr(game.gm, "resolve_decision",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    rec.clear()
    game.handle({"type": "decide", "text": DECISION})
    assert "RuntimeError: boom" in rec.last("error")["message"]
    assert rec.last("awaiting")["kind"] == "decision"


BUNDLE_SIM = r'''
import sys, os, importlib.util

# Simulate the browser bundle: cli/, rich, typer, click and the provider SDKs
# are simply not shipped. Anything the engine needs from them must already be
# behind a guard, or the whole port is a fiction.
BLOCKED = {"cli", "rich", "typer", "click", "google", "google.generativeai"}


class Blocker:
    def find_module(self, name, path=None):
        return self.find_spec(name, path)

    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCKED:
            raise ImportError(f"No module named {name!r} (not in the web bundle)")
        return None


sys.meta_path.insert(0, Blocker())
sys.path.insert(0, os.getcwd())
os.environ["WARGAME_LLM"] = "mock"

spec = importlib.util.spec_from_file_location("b", sys.argv[1])
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

msgs = []
game = b.WebGame(msgs.append)
game.handle({"type": "newGame",
             "config": {"scenario": "fast_start", "playMode": "classic", "seed": 3}})
for _ in range(30):
    game.handle({"type": "decide", "text": "Hold the line and consult allies."})
    if any(m["type"] == "ending" for m in msgs):
        break
    game.handle({"type": "endTurn"})

errors = [m["message"] for m in msgs if m["type"] == "error"]
ending = [m for m in msgs if m["type"] == "ending"]
leaked = sorted(m for m in sys.modules if m.split(".")[0] in BLOCKED)
print("ERRORS:", errors[:3])
print("LEAKED:", leaked)
print("ENDING:", ending[-1]["verdict"] if ending else None)
print("ANSI:", any("\x1b[" in m.get("ansi", "") for m in msgs))
'''


def test_full_game_plays_with_cli_and_rich_absent(tmp_path):
    """The port's whole basis: no cli/rich/typer anywhere in the play path."""
    import subprocess

    script = tmp_path / "bundle_sim.py"
    script.write_text(BUNDLE_SIM)
    proc = subprocess.run(
        [sys.executable, str(script), str(BRIDGE_PATH)],
        cwd=str(REPO), capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    out = proc.stdout
    assert "ERRORS: []" in out, out
    assert "LEAKED: []" in out, out
    # Assert the verdict positively: "ENDING: None" not in out would also pass
    # if the ENDING line never printed at all.
    verdict = next((ln.split(":", 1)[1].strip() for ln in out.splitlines()
                    if ln.startswith("ENDING:")), None)
    assert verdict in {"victory", "partial", "defeat"}, out
    assert "ANSI: True" in out, out


# ---------------------------------------------------------------------------
# bridge.describe_llm_faults: what the player is told when a call did not land
# ---------------------------------------------------------------------------
#
# The notice is the only account of a live failure a browser player ever gets,
# so naming the wrong cause is worse than saying nothing: it sends them to
# check an endpoint that was never contacted. A cached pre-bb55a91 bundle did
# exactly that — Pyodide cannot start threads, so every batched call died
# locally and five advisors at a time answered from the offline stand-in while
# the page blamed the network.


def test_threadless_batch_failure_is_not_reported_as_a_network_fault():
    """A call that never left the browser must not be blamed on the network."""
    message = bridge.describe_llm_faults(
        ["[ERROR: can't start new thread]"], "shared",
        model="deepseek/deepseek-chat-v3-0324:free")
    assert "never sent" in message
    assert "Nothing reached OpenRouter" in message
    # The two claims that sent a player hunting for a fault that was not there.
    assert "usually the network" not in message
    assert "never got an answer" not in message


def test_threadless_notice_names_the_fix_the_player_can_actually_apply():
    """Being right about the cause is only half of it; say what to do."""
    message = bridge.describe_llm_faults(
        ["RuntimeError: can't start new thread"], "shared")
    assert "hard refresh" in message.lower()
    assert "cached" in message


def test_missing_configuration_is_not_blamed_on_the_network_either():
    message = bridge.describe_llm_faults(
        [("ValueError: OPENAI_COMPAT_BASE_URL not found in environment or "
          "config.py")], "own")
    assert "no live endpoint is configured" in message
    assert "usually the network" not in message


def test_a_genuine_silent_failure_is_still_described_as_one():
    """The local-fault branch must not swallow real network faults."""
    message = bridge.describe_llm_faults(
        ["ConnectionError: Max retries exceeded with url: /chat/completions"],
        "shared", model="openai/gpt-4o-mini")
    assert "never got an answer" in message
    assert "usually the network" in message
    assert "openai/gpt-4o-mini" in message


def test_an_http_status_outranks_a_local_fault_in_a_mixed_batch():
    """A refusal that reached the wire is the more specific story."""
    message = bridge.describe_llm_faults(
        ["[ERROR: can't start new thread]", "HTTP 402 out of credit"],
        "shared")
    assert "out of credit" in message
    assert "never sent" not in message


@pytest.mark.parametrize("fault,expected", [
    ("can't start new thread", "threads"),
    ("cant start new thread", "threads"),
    ("RuntimeError: can not start new thread", "threads"),
    ("OPENAI_COMPAT_MODEL not set", "config"),
    ("HTTP 500 upstream exploded", ""),
    ("ConnectionError: connection reset by peer", ""),
])
def test_local_fault_classification(fault, expected):
    assert bridge.classify_local_fault([fault]) == expected
