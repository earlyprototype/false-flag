"""Tests for the browser build's engine side.

Two things are under test here:

* ``engine.game_manager`` now owns campaign termination. Before this, a
  headless session could never finish: ``engine.endings.check_ending`` was
  only ever called from ``cli/main.py``, so the browser and API front ends
  had no way to reach a verdict.
* ``docs/play/py/bridge.py`` — the Python half of the Web Worker. It is
  plain Python with an injected ``emit`` callback, so the whole page<->worker
  protocol can be driven from pytest without a browser.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from engine.game_manager import GameManager

REPO = Path(__file__).resolve().parents[1]
BRIDGE_PATH = REPO / "docs" / "play" / "py" / "bridge.py"


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

    gm.ending = gm.ending or __import__(
        "engine.endings", fromlist=["Ending"]
    ).Ending("t", "TEST", "partial", "n")
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


def make_game(**config):
    rec = Recorder()
    game = bridge.WebGame(rec)
    cfg = {"scenario": "fast_start", "playMode": "classic", "seed": 3}
    cfg.update(config)
    game.handle({"type": "newGame", "config": cfg})
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
    assert "ENDING: None" not in out, out
    assert "ANSI: True" in out, out
