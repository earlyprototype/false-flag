"""API tests for the observability + control dashboard surface:

- layer tagging at the event bus (GameSession.push_event)
- server-side REFEREE filtering per /stream viewer
- the llm_call relay (call_log listener -> session queue)
- /routing, /prompts, /game/{id}/inject, /dashboard, /demo endpoints

Driven through FastAPI's TestClient against the deterministic mock driver,
same conventions as tests/test_api_server.py.
"""

import asyncio
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sse_starlette")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")
    monkeypatch.delenv("WARGAME_CALL_LOG", raising=False)


@pytest.fixture(autouse=True)
def clean_routing_and_prompts():
    from llm import routing_overrides, prompt_templates
    routing_overrides.clear_all()
    yield
    routing_overrides.clear_all()
    for family in prompt_templates.FAMILIES:
        prompt_templates.reset_template(family)


@pytest.fixture()
def client():
    from api import server

    with TestClient(server.app) as test_client:
        yield test_client
    server.sessions.clear()


def _new_game(client, facilitator=False):
    response = client.post("/game/new", json={
        "scenario_id": "war_game_2025",
        "variant": "standard",
        "play_mode": "immersive",
        "facilitator": facilitator,
    })
    assert response.status_code == 200
    return response.json()


def _facilitator_headers(created):
    return {
        "X-Facilitator-Capability": created["facilitator_capability"],
    }


def _drain_queue(session):
    """All queued SSE items (server-side shape, _layer still present)."""
    items = []
    while not session.event_queue.empty():
        items.append(session.event_queue.get_nowait())
    return items


def _drain_llm_calls(session, minimum=1, deadline_s=5.0):
    """The queue's llm_call items, polling until ``minimum`` arrive.

    Relay pushes ride loop.call_soon_threadsafe, so a record can land on
    the queue a beat after the HTTP response returns; draining immediately
    races the scheduled callbacks and flakes."""
    items = []
    deadline = time.time() + deadline_s
    while True:
        items += [item for item in _drain_queue(session)
                  if item["event"] == "llm_call"]
        if len(items) >= minimum or time.time() >= deadline:
            return items
        time.sleep(0.05)


# --- facilitator capability -----------------------------------------------

def test_facilitator_creation_issues_an_explicit_capability(client):
    response = client.post("/game/new", json={"facilitator": True})
    facilitator = response.json()
    player_response = client.post("/game/new", json={})
    player = player_response.json()

    capability = facilitator.get("facilitator_capability")
    assert isinstance(capability, str) and len(capability) >= 32
    assert capability != facilitator["session_id"]
    assert player.get("facilitator_capability") is None
    assert response.cookies.get("false_flag_facilitator") == capability
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert f"Path=/stream/{facilitator['session_id']}/facilitator" in cookie
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in player_response.headers


def test_non_ascii_facilitator_capability_fails_closed():
    from api import server

    session = server.GameSession(
        server.GameManager(), facilitator_capability="ascii-token")
    assert server._has_facilitator_capability(session, "snowman-☃") is False


# --- layer tagging at the bus ---------------------------------------------

def test_events_carry_layer_turn_and_tplus_stamps(client):
    from api import server
    from models.layers import Layer

    created = _new_game(client)
    session = server.sessions[created["session_id"]]
    items = _drain_queue(session)
    assert items, "session creation queued no events"

    for item in items:
        assert isinstance(item.get("_layer"), Layer)
        data = json.loads(item["data"])
        assert data["layer"] == item["_layer"].value
        assert "turn" in data and "t_plus_s" in data and "event_seq" in data

    # The opening scenes and briefing are player-visible SITREP material.
    layers = {item["_layer"] for item in items}
    assert Layer.SITREP in layers


def test_briefing_inject_layer_follows_channel(client):
    """Turn 1's scripted inject has channel: briefing -> SITREP; the data
    payload carries the channel for the ledger's colour-coding."""
    from api import server
    from models.layers import Layer

    created = _new_game(client)
    session = server.sessions[created["session_id"]]
    inject_items = [
        item for item in _drain_queue(session)
        if json.loads(item["data"]).get("type") == "inject"
    ]
    assert inject_items
    data = json.loads(inject_items[0]["data"])
    assert data["channel"] == "briefing"
    assert inject_items[0]["_layer"] is Layer.SITREP


def test_discussion_lines_are_cabinet_layer(client):
    from api import server
    from models.layers import Layer

    created = _new_game(client)
    session_id = created["session_id"]
    client.post(f"/game/{session_id}/briefing/ack")
    session = server.sessions[session_id]
    _drain_queue(session)

    response = client.post("/game/discussion", json={
        "session_id": session_id,
        "question": "What is the current threat assessment?",
    })
    assert response.status_code == 200

    items = _drain_queue(session)
    advisor_items = [
        item for item in items
        if json.loads(item["data"]).get("type") == "advisor"
    ]
    assert advisor_items, "no advisor lines streamed"
    assert all(item["_layer"] is Layer.CABINET for item in advisor_items)


def test_adjudication_streams_referee_record_and_state_update(client):
    from api import server
    from models.layers import Layer

    created = _new_game(client)
    session_id = created["session_id"]
    client.post(f"/game/{session_id}/briefing/ack")
    session = server.sessions[session_id]
    _drain_queue(session)

    response = client.post("/game/decision", json={
        "session_id": session_id,
        "action_text": "Hold the deployment and convene the North Atlantic Council.",
    })
    assert response.status_code == 200

    items = _drain_queue(session)
    by_event = {}
    for item in items:
        by_event.setdefault(item["event"], []).append(item)

    # The referee's raw record of the turn, REFEREE-tagged.
    assert "adjudication" in by_event
    assert by_event["adjudication"][0]["_layer"] is Layer.REFEREE
    assert "effects" in json.loads(by_event["adjudication"][0]["data"])

    # Parse health relayed for the facilitator feed.
    assert "parse_health" in by_event
    assert by_event["parse_health"][0]["_layer"] is Layer.REFEREE

    # Player-visible turn advance still present, SITREP-tagged.
    assert "state_update" in by_event
    state = json.loads(by_event["state_update"][0]["data"])
    assert state["turn"] == 2
    assert "metrics" in state
    assert by_event["state_update"][0]["_layer"] is Layer.SITREP


# --- REFEREE stream filtering ----------------------------------------------

def test_subscribers_receive_independent_copies_and_preconnect_events():
    """Every live observer gets each event; filtering one cannot alter another.

    The first observer must also receive events emitted before EventSource can
    attach, which is how a newly-created game delivers its cold open.
    """
    from api import server
    from models.layers import Layer

    session = server.GameSession(server.GameManager())
    asyncio.run(session.push_event(
        "transcript", {"content": "cold open"}, layer=Layer.SITREP))

    first = session.subscribe()
    preconnect = first.get_nowait()
    assert preconnect["event"] == "transcript"
    assert json.loads(preconnect["data"])["content"] == "cold open"

    second = session.subscribe()
    asyncio.run(session.push_event(
        "llm_call", {"family": "advisor_qa"}, layer=Layer.REFEREE))
    session.push_event_threadsafe(
        "state_update", {"phase": "discussion"}, layer=Layer.SITREP)

    first_items = [first.get_nowait(), first.get_nowait()]
    second_items = [second.get_nowait(), second.get_nowait()]
    assert [item["event"] for item in first_items] == [
        "llm_call", "state_update"]
    assert [item["event"] for item in second_items] == [
        "llm_call", "state_update"]
    assert [json.loads(item["data"])["event_seq"] for item in first_items] == \
        [json.loads(item["data"])["event_seq"] for item in second_items]
    assert first_items[0] is not second_items[0]

    assert server._stream_filter(first_items[0], include_referee=False) is None
    assert second_items[0]["_layer"] is Layer.REFEREE
    assert server._stream_filter(first_items[1], include_referee=False)["event"] == \
        "state_update"
    assert server._stream_filter(second_items[1], include_referee=False)["event"] == \
        "state_update"


def test_stream_ready_follows_registration_and_disconnect_unsubscribes():
    """Ready is first, and a closed stream cannot retain its queue."""
    from api import server
    from models.layers import Layer

    session = server.GameSession(server.GameManager())
    session_id = "disconnect-probe"
    server.sessions[session_id] = session

    class DisconnectedRequest:
        headers = {}
        cookies = {}
        query_params = {}

        async def is_disconnected(self):
            return True

    async def disconnect_then_publish():
        response = await server.stream_game_events(
            session_id, DisconnectedRequest())
        iterator = response.body_iterator
        ready = await iterator.__anext__()
        assert ready == {
            "event": "stream_ready", "data": '{"viewer":"public"}'}
        assert len(session._subscribers) == 1
        with pytest.raises(StopAsyncIteration):
            await iterator.__anext__()
        assert not session._subscribers
        await session.push_event(
            "state_update", {"phase": "discussion"}, layer=Layer.SITREP)

    try:
        asyncio.run(disconnect_then_publish())
    finally:
        server.sessions.pop(session_id, None)

    replacement = session.subscribe()
    assert replacement.get_nowait()["event"] == "state_update"


def test_one_session_filters_referee_per_stream_request():
    """A shared session is public by default; only the capable viewer gets
    its REFEREE event, while both viewers still get every public event."""
    from api import server
    from models.layers import Layer

    capability = "facilitator-capability-for-stream-test"
    session = server.GameSession(
        server.GameManager(), facilitator_capability=capability)
    session_id = "shared-stream-probe"
    server.sessions[session_id] = session

    class ConnectedRequest:
        def __init__(self, query_capability=None, cookie_capability=None):
            self.headers = {}
            self.cookies = {}
            if cookie_capability:
                self.cookies["false_flag_facilitator"] = cookie_capability
            self.query_params = {}
            if query_capability:
                self.query_params["facilitator_capability"] = query_capability

        async def is_disconnected(self):
            return False

    async def observe():
        public_response = await server.stream_game_events(
            session_id, ConnectedRequest(query_capability=capability))
        facilitator_response = await server.stream_game_events(
            session_id, ConnectedRequest(cookie_capability=capability))
        public = public_response.body_iterator
        facilitator = facilitator_response.body_iterator

        await public.__anext__()
        await facilitator.__anext__()
        await session.push_event(
            "system", {"content": "public one"}, layer=Layer.SITREP)
        await session.push_event(
            "inject_fired", {"title": "private"}, layer=Layer.REFEREE)
        await session.push_event(
            "system", {"content": "public two"}, layer=Layer.SITREP)

        try:
            public_events = [await public.__anext__(), await public.__anext__()]
            facilitator_events = [
                await facilitator.__anext__(),
                await facilitator.__anext__(),
                await facilitator.__anext__(),
            ]
        except StopAsyncIteration:
            pytest.fail("a shared stream stopped while filtering one viewer")
        finally:
            await public.aclose()
            await facilitator.aclose()
        return public_events, facilitator_events

    try:
        public_events, facilitator_events = asyncio.run(observe())
    finally:
        server.sessions.pop(session_id, None)

    assert [item["event"] for item in public_events] == ["system", "system"]
    assert [item["event"] for item in facilitator_events] == [
        "system", "inject_fired", "system"]


def test_threadsafe_events_keep_emission_time_and_loop_sequence(monkeypatch):
    """Worker metadata is captured at emission; sequence follows delivery."""
    from api import server
    from models.layers import Layer

    now = [100.0]
    monkeypatch.setattr(server.time, "time", lambda: now[0])

    async def publish_worker_then_loop_event():
        session = server.GameSession(server.GameManager())
        first = session.subscribe()
        second = session.subscribe()
        session.manager.world.turn = 4
        now[0] = 101.25
        worker = threading.Thread(
            target=session.push_event_threadsafe,
            args=("transcript", {"content": "worker"}),
            kwargs={"layer": Layer.SITREP},
        )

        worker.start()
        # Keep the loop occupied until the worker has queued its callback.
        worker.join(timeout=2)
        assert not worker.is_alive()
        session.manager.world.turn = 5
        now[0] = 103.5
        await session.push_event(
            "state_update", {"phase": "discussion"}, layer=Layer.SITREP)
        await asyncio.sleep(0)

        def events(queue):
            return [queue.get_nowait() for _ in range(2)]

        return events(first), events(second)

    first_events, second_events = asyncio.run(
        publish_worker_then_loop_event())
    assert first_events == second_events

    payloads = [json.loads(item["data"]) for item in first_events]
    assert [payload["event_seq"] for payload in payloads] == [1, 2]
    by_event = {item["event"]: payload
                for item, payload in zip(first_events, payloads)}
    assert (by_event["transcript"]["turn"],
            by_event["transcript"]["t_plus_s"]) == (4, 1.25)
    assert (by_event["state_update"]["turn"],
            by_event["state_update"]["t_plus_s"]) == (5, 3.5)


def test_stream_filter_drops_referee_for_players_only():
    from api.server import _stream_filter
    from models.layers import Layer

    referee_item = {"event": "llm_call", "data": "{}", "_layer": Layer.REFEREE}
    assert _stream_filter(dict(referee_item), include_referee=False) is None
    passed = _stream_filter(dict(referee_item), include_referee=True)
    assert passed == {"event": "llm_call", "data": "{}"}  # _layer stripped

    sitrep_item = {"event": "system", "data": "{}", "_layer": Layer.SITREP}
    assert _stream_filter(dict(sitrep_item), include_referee=False) == \
        {"event": "system", "data": "{}"}

    # Legacy/untagged items pass for everyone.
    untagged = {"event": "system", "data": "{}"}
    assert _stream_filter(dict(untagged), include_referee=False) == untagged


def test_facilitator_query_param_works_too(client):
    response = client.post("/game/new?facilitator=true", json={})
    assert response.status_code == 200
    created = response.json()
    assert isinstance(created.get("facilitator_capability"), str)
    injected = client.post(
        f"/game/{created['session_id']}/inject",
        headers=_facilitator_headers(created),
        json={"headline": "QUERY CAPABILITY", "content": "works"},
    )
    assert injected.status_code == 200


# --- llm_call relay --------------------------------------------------------

def test_llm_calls_land_on_session_queue_as_referee_events(client):
    """A discussion question dispatches LLM calls; each lands on the
    session's queue as a REFEREE llm_call event without prompt/reply
    bodies."""
    from api import server
    from models.layers import Layer

    created = _new_game(client)
    session_id = created["session_id"]
    client.post(f"/game/{session_id}/briefing/ack")
    session = server.sessions[session_id]
    _drain_queue(session)

    client.post("/game/discussion", json={
        "session_id": session_id,
        "question": "Where does NATO stand on this?",
    })

    llm_items = _drain_llm_calls(session)
    assert llm_items, "no llm_call events relayed"
    for item in llm_items:
        assert item["_layer"] is Layer.REFEREE
        data = json.loads(item["data"])
        assert data["provider"] == "mock"
        assert "family" in data and "latency_ms" in data
        assert "prompt" not in data and "reply" not in data
        assert data["prompt_chars"] > 0


def test_decision_relays_llm_calls_from_round_workers(client):
    """The decision pipeline fans most of its LLM calls out across
    thread-pool rounds (engine/decision_phase.run_round). Raw executor
    threads do not inherit contextvars, so without explicit context
    propagation at submit the round workers lose the llm_relay session
    binding and their call records silently vanish - only the few calls
    made on the endpoint's own thread relayed. One committed decision
    dispatches up to seven calls; at least five must reach the queue."""
    from api import server

    created = _new_game(client, facilitator=True)
    session_id = created["session_id"]
    client.post(f"/game/{session_id}/briefing/ack")
    session = server.sessions[session_id]
    _drain_queue(session)

    response = client.post("/game/decision", json={
        "session_id": session_id,
        "action_text": "Raise readiness across home commands and brief "
                       "the Cabinet in full.",
    })
    assert response.status_code == 200

    llm_items = _drain_llm_calls(session, minimum=5)
    assert len(llm_items) >= 5, (
        f"decision pipeline relayed only {len(llm_items)} llm_call events; "
        "round-worker calls are being dropped")


def test_concurrent_sessions_do_not_cross_attribute_llm_calls(client):
    """Two live sessions: a question asked in session A must relay its
    llm_call events onto A's queue only."""
    from api import server

    a = _new_game(client)
    b = _new_game(client)
    for sid in (a["session_id"], b["session_id"]):
        client.post(f"/game/{sid}/briefing/ack")
        _drain_queue(server.sessions[sid])

    client.post("/game/discussion", json={
        "session_id": a["session_id"],
        "question": "What do the forces need from me?",
    })

    # Wait for A's records first: relay pushes are scheduled callbacks, and
    # they land in order - once A's are in, a mis-attributed B record
    # scheduled alongside them would be in too.
    a_calls = _drain_llm_calls(server.sessions[a["session_id"]])
    b_calls = [i for i in _drain_queue(server.sessions[b["session_id"]])
               if i["event"] == "llm_call"]
    assert a_calls and not b_calls


# --- dashboard page --------------------------------------------------------

def test_dashboard_page_serves_selfcontained_html(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    page = response.text
    assert "FACILITATOR DASHBOARD" in page
    # Self-contained: no external scripts, stylesheets or CDNs.
    assert "http://" not in page.replace("http://localhost", "")
    assert "https://" not in page
    assert "<script src" not in page and "link rel=\"stylesheet\"" not in page.lower()


# --- routing endpoints -----------------------------------------------------

def test_routing_matrix_lists_all_twelve_contexts(client):
    from llm.model_config import LLMContext

    response = client.get("/routing")
    assert response.status_code == 200
    payload = response.json()
    contexts = {row["context"] for row in payload["contexts"]}
    assert contexts == {c.value for c in LLMContext}
    assert len(payload["contexts"]) == 12
    assert all(row["override"] is None for row in payload["contexts"])


def test_routing_override_set_and_clear_roundtrip(client):
    set_response = client.post("/routing/advisor_qa", json={"tier": "flash"})
    assert set_response.status_code == 200

    matrix = {row["context"]: row
              for row in client.get("/routing").json()["contexts"]}
    assert matrix["advisor_qa"]["effective_tier"] == "flash"
    assert matrix["advisor_qa"]["default_tier"] == "pro"
    assert matrix["advisor_qa"]["override"] == {
        "tier": "flash", "provider": None, "model": None}
    # Neighbours untouched.
    assert matrix["quality_assessment"]["override"] is None

    clear_response = client.delete("/routing/advisor_qa")
    assert clear_response.status_code == 200
    matrix = {row["context"]: row
              for row in client.get("/routing").json()["contexts"]}
    assert matrix["advisor_qa"]["effective_tier"] == "pro"
    assert matrix["advisor_qa"]["override"] is None


def test_routing_rejects_unknown_context_tier_and_provider(client):
    assert client.post("/routing/not_a_context",
                       json={"tier": "flash"}).status_code == 404
    assert client.post("/routing/advisor_qa",
                       json={"tier": "turbo"}).status_code == 422
    assert client.post("/routing/advisor_qa",
                       json={"provider": "banana"}).status_code == 422
    assert client.post("/routing/advisor_qa", json={}).status_code == 422


# --- prompt endpoints ------------------------------------------------------

def test_prompt_family_list_get_put_reset_roundtrip(client):
    listing = client.get("/prompts").json()["families"]
    assert {f["family"] for f in listing} == {
        "advisor_qa", "advisor_qa_fanout", "decision_interpretation",
        "advisor_pushback"}
    assert all(f["edited"] is False for f in listing)

    got = client.get("/prompts/advisor_qa").json()
    assert "You are the {role}" in got["text"]

    edited_text = got["text"] + "\n\nAnswer in one paragraph."
    put_response = client.put("/prompts/advisor_qa", json={"text": edited_text})
    assert put_response.status_code == 200
    assert client.get("/prompts/advisor_qa").json()["edited"] is True

    reset_response = client.delete("/prompts/advisor_qa")
    assert reset_response.status_code == 200
    assert client.get("/prompts/advisor_qa").json()["edited"] is False


def test_prompt_put_rejects_bad_placeholders(client):
    response = client.put("/prompts/advisor_qa",
                          json={"text": "Hello {not_a_field}"})
    assert response.status_code == 422
    assert client.get("/prompts/no_such_family").status_code == 404


def test_edited_prompt_reaches_the_next_llm_call(client):
    """Hot edit end to end: save an edited advisor template, ask a
    question, and the assembled prompt (visible via the llm_call relay's
    prompt_chars growth is too weak - assert through the builder) uses it."""
    from tests.prompt_parity_fixtures import (
        build_initial_conditions, build_transcript, build_world,
    )
    from llm.prompts import build_advisor_context

    marker = "ALWAYS MENTION THE WEATHER."
    original = client.get("/prompts/advisor_qa").json()["text"]
    client.put("/prompts/advisor_qa", json={"text": original + "\n" + marker})

    prompt = build_advisor_context(
        build_world(), build_initial_conditions(), "chief_defence_staff",
        "What are our options?", build_transcript())
    # Trusted role attribution intentionally remains last after editable text.
    assert prompt.endswith(
        f"{marker}\n\n[ADVISOR ROLE: Chief of the Defence Staff]"
    )


# --- inject console --------------------------------------------------------

def test_manual_inject_delivers_streams_and_applies_effects(client):
    from api import server
    from models.layers import Layer

    created = _new_game(client, facilitator=True)
    session_id = created["session_id"]
    session = server.sessions[session_id]
    _drain_queue(session)
    manager = session.manager
    risk_before = manager.world.metrics.escalation_risk

    response = client.post(f"/game/{session_id}/inject", headers={
        **_facilitator_headers(created),
    }, json={
        "channel": "intelligence",
        "headline": "AUXILIARY ALTERS COURSE",
        "content": "The vessel has turned toward the cable corridor.",
        "target": "North Sea",
        "effects": [{"metric": "escalation_risk", "delta": 10}],
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "delivered"
    assert payload["layer"] == "intel"

    # Engine state moved through the real seam (+10 halves to +5 on
    # standard difficulty).
    assert manager.world.metrics.escalation_risk == min(100, risk_before + 5)
    assert manager.world.recent_injects[-1] == "AUXILIARY ALTERS COURSE"

    items = _drain_queue(session)
    transcript_items = [i for i in items if i["event"] == "transcript"]
    assert transcript_items
    data = json.loads(transcript_items[0]["data"])
    assert data["manual"] is True
    assert data["channel"] == "intelligence"
    assert "[North Sea]" in data["content"]
    assert transcript_items[0]["_layer"] is Layer.INTEL

    referee_items = [i for i in items if i["event"] == "inject_fired"]
    assert referee_items and referee_items[0]["_layer"] is Layer.REFEREE


def test_manual_inject_unknown_session_is_404(client):
    response = client.post("/game/no-such-session/inject", json={
        "channel": "briefing", "headline": "X", "content": "Y",
    })
    assert response.status_code == 404


def test_manual_inject_requires_matching_facilitator_capability(client):
    """A shared session id alone cannot authorize its EXCON lever."""
    created = _new_game(client, facilitator=True)
    session_id = created["session_id"]
    from api import server
    manager = server.sessions[session_id].manager
    risk_before = manager.world.metrics.escalation_risk
    injects_before = list(manager.world.recent_injects)

    payload = {
        "channel": "briefing", "headline": "NOT FOR PLAYERS",
        "content": "This must never be delivered.",
        "effects": [{"metric": "escalation_risk", "delta": 10}],
    }
    try:
        bare = client.post(f"/game/{session_id}/inject", json=payload)
        wrong = client.post(
            f"/game/{session_id}/inject",
            headers={"X-Facilitator-Capability": session_id}, json=payload)
    except AttributeError:
        pytest.fail("inject authority is still read from the whole session")
    assert bare.status_code == 403
    assert wrong.status_code == 403

    assert manager.world.metrics.escalation_risk == risk_before
    assert list(manager.world.recent_injects) == injects_before


def test_session_lock_serialises_inject_with_other_mutators(client):
    """GameSession.lock: while another mutator holds the session's lock,
    an inject waits; it delivers once the lock is released."""
    import threading

    created = _new_game(client, facilitator=True)
    session_id = created["session_id"]
    from api import server
    session = server.sessions[session_id]

    outcome = {}

    def fire():
        outcome["response"] = client.post(
            f"/game/{session_id}/inject",
            headers=_facilitator_headers(created), json={
            "channel": "briefing", "headline": "WAITS", "content": "held",
        })

    thread = threading.Thread(target=fire, daemon=True)
    with session.lock:
        thread.start()
        thread.join(0.3)
        assert thread.is_alive(), "inject did not wait for the session lock"
    thread.join(5.0)
    assert not thread.is_alive(), "inject never completed after release"
    assert outcome["response"].status_code == 200


# --- demo driver -----------------------------------------------------------

def test_demo_start_runs_a_short_campaign(client):
    from api import server

    response = client.post("/demo/start", json={"turns": 1, "pace_s": 0.0})
    assert response.status_code == 200
    payload = response.json()
    session_id = payload["session_id"]
    assert isinstance(payload.get("facilitator_capability"), str)
    assert response.cookies.get("false_flag_facilitator") == \
        payload["facilitator_capability"]
    assert payload["stream"] == f"/stream/{session_id}/facilitator"
    assert session_id in server.sessions

    # Mock-driven single turn: finishes fast; poll status.
    deadline = time.time() + 30
    while time.time() < deadline:
        status = client.get(f"/demo/{session_id}/status").json()
        if not status["running"]:
            break
        time.sleep(0.2)
    else:
        pytest.fail("demo run did not finish inside 30s")

    assert status["error"] is None
    manager = server.sessions[session_id].manager
    assert manager.world.turn >= 2, "demo did not adjudicate a turn"
    assert len(manager.transcript) > 0


def test_demo_stop_requires_its_facilitator_capability(client):
    started = client.post(
        "/demo/start", json={"turns": 1, "pace_s": 0.0}).json()
    session_id = started["session_id"]

    try:
        bare = client.post(f"/demo/{session_id}/stop")
    except (AttributeError, TypeError):
        pytest.fail("demo control still has no request-scoped capability")
    allowed = client.post(
        f"/demo/{session_id}/stop",
        headers=_facilitator_headers(started))

    assert bare.status_code == 403
    assert allowed.status_code == 200


def test_demo_status_unknown_session_is_404(client):
    assert client.get("/demo/nope/status").status_code == 404
    assert client.post("/demo/nope/stop").status_code == 404
