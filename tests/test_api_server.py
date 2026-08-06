"""API tests for the FastAPI server (api/server.py), driven through
FastAPI's TestClient against the deterministic mock LLM driver.

The HTTP path used to serve no briefing after turn one (ER-022): the only
call to get_turn_briefing sat inside POST /game/new, so turns two and later
had no inject, no inject effects, no narrator bridge and no mandatory
diplomatic encounter. POST /game/{session_id}/briefing closes that gap with
the same payload shape /game/new returns.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

pytest.importorskip("fastapi")
pytest.importorskip("sse_starlette")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """Force the deterministic mock LLM driver for all tests."""
    monkeypatch.setenv("WARGAME_LLM", "mock")


@pytest.fixture()
def client():
    from api import server

    with TestClient(server.app) as test_client:
        yield test_client
    # Sessions are process-global; keep tests independent.
    server.sessions.clear()


def _new_game(client):
    response = client.post("/game/new", json={
        "scenario_id": "war_game_2025",
        "variant": "standard",
        "difficulty": "standard",
        "play_mode": "immersive",
    })
    assert response.status_code == 200
    return response.json()


def test_new_game_then_decide_then_next_turn_briefing(client):
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]
    assert created["turn"] == 1
    assert created["phase"] == "briefing"

    # Acknowledge the briefing and commit a decision; the turn advances.
    ack = client.post(f"/game/{session_id}/briefing/ack")
    assert ack.status_code == 200

    decided = client.post("/game/decision", json={
        "session_id": session_id,
        "action_text": "Request NATO Article 4 consultations and reinforce air policing.",
    })
    assert decided.status_code == 200

    manager = server.sessions[session_id].manager
    assert manager.world.turn == 2

    # ER-022: the new endpoint runs turn two's briefing.
    transcript_before = len(manager.transcript)
    briefing = client.post(f"/game/{session_id}/briefing")
    assert briefing.status_code == 200

    payload = briefing.json()
    # Same payload shape as POST /game/new.
    assert set(created.keys()) == set(payload.keys())
    assert payload["session_id"] == session_id
    assert payload["turn"] == 2
    assert payload["phase"] == "briefing"
    assert "escalation_risk" in payload["metrics"]
    # Turn 2 is scripted and has no mandatory call.
    assert payload["pending_encounter"] is None

    # The briefing actually ran: the transcript grew and names the new turn.
    new_lines = manager.transcript[transcript_before:]
    assert new_lines, "briefing endpoint added nothing to the transcript"
    assert any(line.strip() == "TURN 2" for line in new_lines)


def test_briefing_unknown_session_is_404(client):
    response = client.post("/game/no-such-session/briefing")
    assert response.status_code == 404


def test_briefing_refused_while_mandatory_call_is_live(client):
    """A live scripted mandatory call blocks the next briefing the same way
    it blocks a decision (409): running a new turn would abandon the
    counterpart mid-sentence."""
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]
    # Ack first: the decision endpoints test the phase before the call guard.
    client.post(f"/game/{session_id}/briefing/ack")

    manager = server.sessions[session_id].manager
    manager.active_encounter = SimpleNamespace(active=True, required=True)

    response = client.post(f"/game/{session_id}/briefing")
    assert response.status_code == 409
    assert "mandatory diplomatic call" in response.json()["detail"]

    # The decision endpoints refuse for the same reason.
    decided = client.post("/game/decision", json={
        "session_id": session_id,
        "action_text": "Proceed regardless.",
    })
    assert decided.status_code == 409
