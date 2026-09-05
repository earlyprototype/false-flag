"""Focused route proof; the browser journey verifies the live room."""

from fastapi.testclient import TestClient


def test_vr_page_observes_without_creating_a_session(monkeypatch):
    from api import server

    def forbid_game_creation(*args, **kwargs):
        raise AssertionError("Serving the room must not create a game")

    monkeypatch.setattr(server, "GameManager", forbid_game_creation)
    existing_sessions = dict(server.sessions)
    with TestClient(server.app) as client:
        response = client.get("/vr?game=route-check")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "False Flag — Operations Room" in response.text
    assert server.sessions == existing_sessions
