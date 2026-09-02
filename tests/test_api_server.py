"""API tests for the FastAPI server (api/server.py), driven through
FastAPI's TestClient against the deterministic mock LLM driver.

The HTTP path used to serve no briefing after turn one (ER-022): the only
call to get_turn_briefing sat inside POST /game/new, so turns two and later
had no inject, no inject effects, no narrator bridge and no mandatory
diplomatic encounter. POST /game/{session_id}/briefing closes that gap with
the same payload shape /game/new returns.
"""

import asyncio
import hashlib
import json
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
    # The briefing has been delivered in this response, so the phase has
    # already moved on - a save taken now must resume as a replay (F2).
    assert created["phase"] == "discussion"

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
    assert payload["phase"] == "discussion"
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


def test_interpret_decision_returns_each_parsed_field(client, monkeypatch):
    """The HTTP preview must return the engine's complete parsed result."""
    from api import server
    import engine.game_manager as game_manager_module

    created = _new_game(client)
    forces = ["force-1", "force-2", "force-3",
              "force-4", "force-5", "force-6"]
    resources = ["resource-1", "resource-2", "resource-3",
                 "resource-4", "resource-5", "resource-6"]
    interpretation = (
        "INTERPRETATION: Sustain maritime patrols and consult NATO.\n"
        f"FORCES INVOLVED: {', '.join(forces)}\n"
        f"RESOURCES CONSUMED: {', '.join(resources)}\n"
        "TIMELINE: Within six hours\n"
        "FEASIBILITY: Feasible at current readiness"
    )
    pushback_pairs = [
        ("Chief of the Defence Staff", "Fleet concern."),
        ("Attorney General", "Legal concern."),
    ]
    pushback = [
        {"role": "Chief of the Defence Staff", "concern": "Fleet concern."},
        {"role": "Attorney General", "concern": "Legal concern."},
    ]
    decision_lines = [
        "Prime Minister's Decision: Test the transport.",
        f"Interpretation: {interpretation}",
    ]

    monkeypatch.setattr(
        game_manager_module,
        "run_turn_decision",
        lambda *args, **kwargs: (
            interpretation,
            pushback_pairs,
            [],
            decision_lines,
        ),
    )

    response = client.post("/game/decision/interpret", json={
        "session_id": created["session_id"],
        "action_text": "Test the transport.",
    })

    assert response.status_code == 200
    assert response.json() == {
        "interpretation": interpretation,
        "critical_concerns": [],
        "pushback": pushback,
        "forces_involved": forces,
        "resources_consumed": resources,
        "timeline": "Within six hours",
        "feasibility": "Feasible at current readiness",
        "raw_transcript": decision_lines,
    }


def test_direct_commit_returns_each_advisor_pushback(client, monkeypatch):
    """Skipping preview must not hide the committed per-advisor results."""
    from api import server

    created = _new_game(client)
    manager = server.sessions[created["session_id"]].manager
    pushback = [
        {"role": "Chief of the Defence Staff", "concern": "Fleet concern."},
        {"role": "Attorney General", "concern": "Legal concern."},
    ]
    result = {
        "interpretation": "A test interpretation.",
        "reasoning": "",
        "effects": {},
        "pushback": pushback,
        "critical_concerns": [],
        "advisor_reactions": [],
        "international_reactions": [],
        "ending": None,
        "error": None,
    }
    monkeypatch.setattr(manager, "resolve_decision", lambda _action: result)

    response = client.post("/game/decision/commit", json={
        "session_id": created["session_id"],
        "action_text": "Test the direct commit transport.",
        "user_choice": "confirm",
    })

    assert response.status_code == 200
    assert response.json()["pushback"] == pushback


# --- Scene-setting probe -------------------------------------------------

def _drain_events(session):
    """Pop everything push_event queued during the request, decoded.

    push_event stores {"event": <SSE event name>, "data": <json string>};
    the tests care about the decoded data payloads, in push order.
    """
    events = []
    while True:
        try:
            raw = session.event_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        events.append({"event": raw["event"], "data": json.loads(raw["data"])})
    return events


def test_discussion_advisor_all_gets_an_answer_from_every_advisor(client):
    """advisor="all" puts the one question to the whole room (one PM line,
    one answer per seated advisor) instead of keyword-routing it."""
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]

    response = client.post("/game/discussion", json={
        "session_id": session_id,
        "question": "Give me your read: where do we actually stand?",
        "advisor": "all",
    })
    assert response.status_code == 200

    manager = server.sessions[session_id].manager
    tail = manager.transcript[-6:]
    pm_lines = [l for l in tail if l.startswith("Prime Minister:")]
    assert len(pm_lines) == 1, "the room was addressed once, not per advisor"
    answers = [l for l in tail if not l.startswith("Prime Minister:")]
    assert len(answers) == 5
    assert len({l.split(":", 1)[0] for l in answers}) == 5


def test_discussion_without_advisor_keeps_the_routed_behaviour(client):
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]

    response = client.post("/game/discussion", json={
        "session_id": session_id,
        "question": "Is this legal?",
    })
    assert response.status_code == 200

    manager = server.sessions[session_id].manager
    answers = [l for l in manager.transcript
               if l.split(":", 1)[0] == "Attorney General"]
    assert answers, "the keyword router should have picked the Attorney General"


def test_call_initiates_without_a_message_and_hangs_up_clean(client):
    """The two-stage outbound flow over HTTP: initiation takes no message and
    returns the counterpart's opening lines; hanging up before saying
    anything closes the call with a zero outcome delta."""
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]
    manager = server.sessions[session_id].manager
    cohesion_before = manager.world.metrics.alliance_cohesion

    opened = client.post("/game/action/call", json={
        "session_id": session_id,
        "country_name": "US",
    })
    assert opened.status_code == 200
    data = opened.json()
    assert data["active"] is True
    assert any(line.startswith(f"{data['title']}:")
               for line in data["transcript"]), "the counterpart speaks first"
    assert not any("Prime Minister:" in line for line in data["transcript"])

    hung_up = client.post("/game/action/diplomacy/reply", json={
        "session_id": session_id,
        "message": "end",
    })
    assert hung_up.status_code == 200
    closed = hung_up.json()
    assert closed["active"] is False
    assert closed["outcome"]["cohesion_delta"] == 0
    assert manager.world.metrics.alliance_cohesion == cohesion_before


def test_new_game_opens_with_scene_setting_before_the_inject(client):
    """POST /game/new plays the cold open before the first briefing.

    The engine authored the opening beats (engine/opening.py) precisely so
    no front end starts a player on a bare inject; the HTTP path was the
    one consumer that never adopted them. The scenes must arrive on the
    event queue before the inject, carry real intro text, and carry it as
    plain text - GameManager.get_opening_scenes strips the Rich console
    markup that only the terminal CLI can render.
    """
    from api import server

    created = _new_game(client)
    session = server.sessions[created["session_id"]]

    events = _drain_events(session)
    transcript = [e["data"] for e in events if e["event"] == "transcript"]
    types = [d["type"] for d in transcript]

    assert "scene" in types, "no scene-setting events reached the queue"
    assert "inject" in types, "the turn-1 briefing never reached the queue"

    # Every beat of the cold open plays out before the situation report.
    last_scene = max(i for i, t in enumerate(types) if t == "scene")
    first_inject = min(i for i, t in enumerate(types) if t == "inject")
    assert last_scene < first_inject, (
        "a scene event arrived after the inject - the cold open must "
        "finish before the briefing starts"
    )

    scenes = [d for d in transcript if d["type"] == "scene"]
    for scene in scenes:
        assert scene["content"].strip(), "scene event with empty body"
        for token in ("[cyan", "[/", "[bold"):
            assert token not in scene["content"], (
                f"Rich markup {token!r} leaked into scene content"
            )
            assert token not in (scene.get("title") or ""), (
                f"Rich markup {token!r} leaked into a scene title"
            )


# --- Restored-session readability ---------------------------------------

def test_load_returns_the_transcript_of_the_played_session(client, tmp_path):
    """POST /game/load hands back a readable session, not just metrics.

    A restored session used to arrive with turn/phase/metrics only: the
    client had no transcript to render, so the player resumed into a blank
    screen. Play a turn's discussion, save, load - the load response must
    carry the full transcript including the played lines, and active_call
    None (turn one has no scripted call).
    """
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]
    manager = server.sessions[session_id].manager

    question = "CDS, what are our immediate military options?"
    asked = client.post("/game/discussion", json={
        "session_id": session_id,
        "question": question,
    })
    assert asked.status_code == 200

    # Keep the save file out of the repo's saves/ directory.
    manager.root_path = tmp_path
    saved = client.post("/game/save", json={
        "session_id": session_id,
        "save_name": "api-probe",
    })
    assert saved.status_code == 200
    save_path = Path(saved.json()["save_path"])
    assert save_path.is_file()
    assert tmp_path in save_path.parents

    loaded = client.post("/game/load", json={"save_path": str(save_path)})
    assert loaded.status_code == 200
    body = loaded.json()

    assert body["session_id"] != session_id  # a fresh session was minted
    assert isinstance(body["transcript"], list) and body["transcript"]
    # The restored transcript is the played one, verbatim...
    assert body["transcript"] == manager.transcript
    # ...including the discussion exchange from the played turn.
    assert any(question in line for line in body["transcript"])
    assert body["active_call"] is None


def test_restored_turn_six_session_exposes_the_live_mandatory_call(client):
    """GET /game/{id} renders the live scripted call a client must answer.

    Turn 6 opens a mandatory diplomatic call during the briefing (ER-033),
    and that call blocks briefings and decisions until answered - so a
    client resuming such a session is stuck unless the state endpoint shows
    the call. Driving the manager directly (the arrangement
    tests/test_saveload_completeness.py uses) and injecting it into the
    session table keeps this deterministic.
    """
    from api import server
    from engine.game_manager import GameManager

    manager = GameManager(seed=42, play_mode="classic")
    manager.world.turn = 6
    manager.get_turn_briefing()

    encounter = manager.active_encounter
    assert encounter is not None and encounter.active and encounter.required, (
        "arrangement failed: turn 6 briefing should open a mandatory call"
    )

    session_id = "probe-turn-six"
    server.sessions[session_id] = server.GameSession(manager)

    response = client.get(f"/game/{session_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["turn"] == 6
    assert isinstance(body["transcript"], list) and body["transcript"]

    call = body["active_call"]
    assert call is not None, "live mandatory call missing from state payload"
    assert call["country"] == encounter.country
    assert call["title"] == encounter.title
    assert call["required"] is True
    assert call["transcript"] == list(encounter.transcript)
    assert call["transcript"], "the opened call should have an opening line"


def test_dataflow_page_serves_the_operable_schema(client):
    """GET /dataflow returns the self-contained live data-flow view."""
    response = client.get("/dataflow")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    # The operable pieces the page is for: reroute + prompt endpoints and
    # the game-type selector's three modes.
    assert "/routing/" in body
    assert "/prompts/" in body
    for mode_name in ("classic", "immersive", "emergent"):
        assert mode_name in body


def test_facilitator_pages_describe_themselves_and_reset(client):
    """Demo affordances (issue #92): every dashboard panel carries a caption,
    both pages can be cleared between runs, and the engine map zooms."""
    dashboard = client.get("/dashboard").text
    panels = dashboard.split("<main>")[1].split("</main>")[0].split("<section")[1:]
    assert len(panels) == 7
    for panel in panels:
        assert '<p class="note"' in panel, "a dashboard panel carries no description"
    assert 'id="btnResetView"' in dashboard      # clears ledger, calls, charts
    assert "KIND_GLOSS" in dashboard             # raw stream event names glossed

    # The two hand-built charts are marks and axis text; role="img" mutes the
    # axis text and chartAlt() supplies the name and the spoken reading that
    # replace it, rebuilt on every redraw.
    for chart in ("chartMetrics", "chartCas"):
        opening_tag = dashboard.split(f'id="{chart}"')[1].split(">")[0]
        assert 'role="img"' in opening_tag, f"{chart} has no text alternative"
    assert "function chartAlt(" in dashboard
    assert "<title>" in dashboard and "<desc>" in dashboard

    dataflow = client.get("/dataflow").text
    for control in ("zoomOutBtn", "zoomInBtn", "zoomFitBtn", "resetViewBtn"):
        assert control in dataflow
    # role="img" makes the whole SVG subtree presentational, dropping every
    # node's aria-label while the node groups stay in the tab order.
    assert 'role: "img"' not in dataflow
    assert 'role: "group"' in dataflow


def test_new_game_mystery_mode_reaches_the_manager(client):
    """mystery_mode on /game/new must construct a mystery-mode manager."""
    from api import server

    response = client.post("/game/new", json={
        "scenario_id": "war_game_2025",
        "play_mode": "immersive",
        "mystery_mode": True,
    })
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    manager = server.sessions[session_id].manager
    assert manager.mystery_mode is True
    # The default path stays unchanged.
    plain = client.post("/game/new", json={"scenario_id": "war_game_2025"})
    plain_manager = server.sessions[plain.json()["session_id"]].manager
    assert plain_manager.mystery_mode is False


def test_dtdl_serves_the_full_interface_set_and_covers_the_page_mapping(client):
    """/dtdl returns all 13 interfaces, and every DTMI the dataflow page
    badges nodes with exists in the served set (guards mapping drift)."""
    import re

    response = client.get("/dtdl")
    assert response.status_code == 200
    data = response.json()
    assert data["counts"]["Interface"] == 13
    assert len(data["interfaces"]) == 13
    assert data["namespace"] == "dtmi:falseflag"
    served = {iface["@id"] for iface in data["interfaces"]}

    page = (Path(__file__).resolve().parents[1] / "api" / "dataflow.html")
    referenced = set(re.findall(r"dtmi:falseflag:[A-Za-z:]+;1", page.read_text(encoding="utf-8")))
    assert referenced, "dataflow page references no DTMIs — mapping missing?"
    missing = referenced - served
    assert not missing, f"page badges DTMIs absent from the model set: {missing}"


def test_dtdl_detail_returns_interface_with_captured_instance(client):
    """/dtdl/{dtmi} serves one interface's raw DTDL plus a real captured
    instance; unknown DTMIs are a 404, not an empty 200."""
    response = client.get("/dtdl/dtmi:falseflag:Inject;1")
    assert response.status_code == 200
    data = response.json()
    assert data["interface"]["@id"] == "dtmi:falseflag:Inject;1"
    assert data["instance"], "no captured instance served for Inject;1"
    assert data["instance"]["$metadata"]["$model"] == "dtmi:falseflag:Inject;1"

    assert client.get("/dtdl/dtmi:falseflag:Nonsense;1").status_code == 404


def test_dtdl_degrades_to_empty_set_when_models_are_absent(client, tmp_path, monkeypatch):
    """A clone without interop/ gets an empty model set, never a 500."""
    from api import server

    monkeypatch.setattr(server, "_DTDL_MODELS_PATH", tmp_path / "absent")
    response = client.get("/dtdl")
    assert response.status_code == 200
    assert response.json()["counts"]["Interface"] == 0


def test_dashboard_page_serves_the_twin_model_panel(client):
    """The facilitator dashboard carries the DTDL panel: Session;1 telemetry
    table wired to the live stream, interface list, /dtdl fetch."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    body = response.text
    assert "DTDL Dashboard" in body
    assert "dtdlTelemetry" in body and "dtdlIfaces" in body
    assert '"/dtdl"' in body or "'/dtdl'" in body
    assert "/dataflow" in body  # links to the full ◇ DTDL view


def test_theatre_snapshot_unknown_session_is_404(client):
    response = client.get("/game/no-such-session/theatre")

    assert response.status_code == 404


def test_theatre_snapshot_returns_versioned_player_view(client):
    created = _new_game(client)
    session_id = created["session_id"]

    response = client.get(f"/game/{session_id}/theatre")

    assert response.status_code == 200
    assert response.json() == {
        "schema_version": 1,
        "session_id": session_id,
        "turn": created["turn"],
        "phase": created["phase"],
        **client.get(f"/game/{session_id}/resources").json(),
    }
    assert response.headers["cache-control"] == "private, no-cache"
    etag = response.headers["etag"]
    assert etag.startswith('"') and etag.endswith('"') and len(etag) == 66


def test_theatre_snapshots_are_isolated_by_session(client):
    from api import server

    first = _new_game(client)
    second = _new_game(client)
    for created, unit_id in ((first, "first-unit"), (second, "second-unit")):
        manager = server.sessions[created["session_id"]].manager
        manager.initial_conditions["uk_forces"] = {
            "naval": [{"id": unit_id, "location": "Portsmouth"}],
        }

    first_response = client.get(f"/game/{first['session_id']}/theatre")
    second_response = client.get(f"/game/{second['session_id']}/theatre")

    assert first_response.json()["session_id"] == first["session_id"]
    assert second_response.json()["session_id"] == second["session_id"]
    assert [unit["id"] for unit in first_response.json()["forces"]] == ["first-unit"]
    assert [unit["id"] for unit in second_response.json()["forces"]] == ["second-unit"]
    assert first_response.headers["etag"] != second_response.headers["etag"]


def test_theatre_snapshot_excludes_hidden_and_legacy_state(client):
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]
    manager = server.sessions[session_id].manager
    manager.world.spatial_state = {"hidden-site": ["red-unit"]}
    manager.world.recent_injects = ["secret narrative"]
    manager.transcript.append("secret actor exchange")
    manager.initial_conditions["red_forces"] = {
        "hidden": [{"id": "red-unit", "location": "hidden-site"}],
    }

    response = client.get(f"/game/{session_id}/theatre")
    selected = client.get(f"/game/{session_id}/theatre?facilitator=true")

    assert set(response.json()) == {
        "schema_version", "session_id", "turn", "phase", "forces", "stockpiles",
    }
    for forbidden in (
        "timestamp", "event_seq", "spatial_state", "narrative", "actor_system",
        "actors", "world", "hidden-site", "red-unit", "secret narrative",
        "secret actor exchange",
    ):
        assert forbidden not in response.text
    assert selected.content == response.content
    assert selected.headers["etag"] == response.headers["etag"]


def test_theatre_snapshot_etag_revalidates_exact_canonical_body(client):
    created = _new_game(client)
    url = f"/game/{created['session_id']}/theatre"
    initial = client.get(url)
    etag = initial.headers["etag"]

    unchanged = client.get(url, headers={"If-None-Match": etag})
    weak_match = client.get(url, headers={"If-None-Match": f"W/{etag}"})

    canonical = json.dumps(
        initial.json(), ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")
    assert initial.content == canonical
    assert etag == f'"{hashlib.sha256(canonical).hexdigest()}"'
    assert unchanged.status_code == 304
    assert unchanged.content == b""
    assert unchanged.headers["etag"] == etag
    assert unchanged.headers["cache-control"] == "private, no-cache"
    assert weak_match.status_code == 200


def test_unrelated_sse_event_leaves_theatre_etag_stable(client):
    from api import server
    from models.layers import Layer

    created = _new_game(client)
    session_id = created["session_id"]
    session = server.sessions[session_id]
    url = f"/game/{session_id}/theatre"
    etag = client.get(url).headers["etag"]
    _drain_events(session)

    asyncio.run(session.push_event(
        "transcript", {"content": "display-only notice"}, layer=Layer.SITREP,
    ))

    event = _drain_events(session)
    response = client.get(url, headers={"If-None-Match": etag})
    assert event[0]["event"] == "transcript"
    assert event[0]["data"]["content"] == "display-only notice"
    assert response.status_code == 304
    assert response.headers["etag"] == etag


def test_visible_turn_change_replaces_theatre_etag(client):
    created = _new_game(client)
    session_id = created["session_id"]
    url = f"/game/{session_id}/theatre"
    initial = client.get(url)

    decided = client.post("/game/decision", json={
        "session_id": session_id,
        "action_text": "Convene NATO consultations and hold current positions.",
    })
    changed = client.get(url)

    assert decided.status_code == 200
    assert changed.json()["turn"] == initial.json()["turn"] + 1
    assert changed.headers["etag"] != initial.headers["etag"]


def test_visible_phase_change_replaces_theatre_etag(client):
    from api import server

    created = _new_game(client)
    session_id = created["session_id"]
    url = f"/game/{session_id}/theatre"
    initial = client.get(url)
    session = server.sessions[session_id]

    with session.lock:
        session.manager.world.phase = "decision"

    changed = client.get(url)
    assert changed.json()["phase"] == "decision"
    assert changed.headers["etag"] != initial.headers["etag"]


def test_theatre_snapshot_waits_for_session_lock(client):
    import threading

    from api import server

    created = _new_game(client)
    session = server.sessions[created["session_id"]]
    outcome = {}

    def fetch_snapshot():
        outcome["response"] = client.get(
            f"/game/{created['session_id']}/theatre")

    thread = threading.Thread(target=fetch_snapshot, daemon=True)
    with session.lock:
        thread.start()
        thread.join(0.3)
        assert thread.is_alive(), "snapshot read did not wait for the session lock"
    thread.join(5.0)

    assert not thread.is_alive(), "snapshot read never completed after lock release"
    assert outcome["response"].status_code == 200


def test_theatre_snapshot_lock_wait_runs_off_the_event_loop():
    import inspect

    from api import server

    assert not inspect.iscoroutinefunction(server.get_theatre_snapshot)


def test_globe_page_serves_the_exercise_marked_situation_globe(client):
    """GET /globe returns the self-contained situation globe: EXERCISE
    chrome, the theatre snapshot it plots from, and the one stream it
    consumes."""
    response = client.get("/globe")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "EXERCISE" in body
    assert "/theatre" in body and "/stream/" in body
    assert "data.turn" in body and "data.phase" in body
    assert "UNRESOLVED" in body.upper()  # the tray for unplaceable units
    # Manual zoom redundancy (#107): buttons and slider must keep shipping.
    assert "btnZoomIn" in body and "btnZoomOut" in body and "zoomSlider" in body


def test_globe_gazetteer_covers_every_order_of_battle_location():
    """Every named base in the scenario's order of battle has a gazetteer
    entry, so no unit is stranded in the UNRESOLVED tray by omission.

    'available' and 'classified' are force postures, not places (the SSBN
    on continuous patrol has no plottable position by design) - they are
    meant to reach the tray and are excluded here.
    """
    import re
    import yaml

    root = Path(__file__).resolve().parents[1]
    conditions = yaml.safe_load(
        (root / "data" / "scenarios" / "war_game_2025" / "initial_conditions.yaml")
        .read_text(encoding="utf-8")
    )
    not_places = {"available", "classified"}
    locations = {
        unit["location"]
        for units in conditions["uk_forces"].values()
        for unit in units
        if unit.get("location") and unit["location"] not in not_places
    }
    assert locations, "scenario carries no unit locations — recon drifted?"

    page = (root / "api" / "globe.html").read_text(encoding="utf-8")
    gazetteer = set(re.findall(r"^\s{2}([a-z_]+):\s*\{ lat:", page, re.MULTILINE))
    assert gazetteer, "globe page exposes no gazetteer entries"

    def key(name):
        return re.sub(r"[\s\-]+", "_", name.strip().lower())

    missing = {loc for loc in locations if key(loc) not in gazetteer}
    assert not missing, f"order-of-battle locations absent from the gazetteer: {missing}"


def test_globe_sensor_shader_is_served_with_its_licence(client):
    """The vendored FLIR shader ships with its MIT attribution intact."""
    response = client.get("/static/thermal.shader.js")
    assert response.status_code == 200
    body = response.text
    assert "MIT License" in body and "gods-eye-view" in body
    assert "window.thermalShader" in body
