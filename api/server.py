"""FastAPI server for the wargame backend.

Provides endpoints for:
- New Game (session initialization)
- Game State (polling)
- Actions (decisions, questions)
- Streaming (narrative updates via SSE)
"""

import os
import sys
import asyncio
import json
import threading
import time
from typing import Dict, Optional, List, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.world import WorldState
from models.layers import Layer, layer_for_channel
from engine.game_manager import GameManager
from api import llm_relay

app = FastAPI(
    title="False Flag: The Wargame API",
    description="Headless engine for the crisis simulation",
    version="0.1.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Container
class GameSession:
    """One running campaign plus its tagged event stream.

    Every event carries a data layer (models/layers.py) stamped here at the
    bus - never inside the engine. ``facilitator`` sessions receive the
    REFEREE layer over /stream; player sessions have it filtered
    server-side (see stream_game_events), so the hidden-truth tag can never
    reach a player browser.
    """

    def __init__(self, manager: GameManager, facilitator: bool = False):
        self.manager = manager
        self.facilitator = facilitator
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.started_at = time.time()
        self._event_seq = 0
        # Serialises GameManager mutation. The demo driver's daemon thread
        # and the API endpoints can otherwise interleave read-then-write
        # engine calls (deliver_inject on world.metrics, decision
        # adjudication) on the same manager. Held only around engine
        # mutation calls - never across pacing sleeps or streaming.
        self.lock = threading.Lock()
        # The loop that owns event_queue, for thread-safe pushes from
        # worker threads (LLM relay, demo driver). Absent outside async
        # context (direct construction in tests).
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def _make_item(self, event_type: str, data: Any,
                   layer: Optional[Layer]) -> Dict[str, Any]:
        """Assemble one SSE queue item: stamp layer, turn, T+ and sequence.

        ``_layer`` is server-side only (the stream filter pops it before
        yielding); the same layer value also travels inside the JSON data
        so clients can filter and colour without parsing conventions.
        """
        layer = layer or Layer.SITREP
        payload = dict(data) if isinstance(data, dict) else {"value": data}
        payload.setdefault("layer", layer.value)
        payload.setdefault("turn", self.manager.world.turn)
        payload.setdefault("t_plus_s", round(time.time() - self.started_at, 3))
        self._event_seq += 1
        payload.setdefault("event_seq", self._event_seq)
        return {
            "event": event_type,
            "data": json.dumps(payload),
            "_layer": layer,
        }

    async def push_event(self, event_type: str, data: Any,
                         layer: Optional[Layer] = None):
        """Push an event to the SSE stream (async endpoints)."""
        await self.event_queue.put(self._make_item(event_type, data, layer))

    def push_event_threadsafe(self, event_type: str, data: Any,
                              layer: Optional[Layer] = None) -> None:
        """Push an event from a worker thread (LLM relay, demo driver)."""
        item = self._make_item(event_type, data, layer)
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self.event_queue.put_nowait, item)
        else:
            self.event_queue.put_nowait(item)

# Map: session_id -> GameSession
sessions: Dict[str, GameSession] = {}

# Every LLM call made while serving a session lands on that session's
# stream as a REFEREE llm_call event (no prompt/reply bodies).
llm_relay.install()


def _session_or_404(session_id: str) -> GameSession:
    """Look up a session and attribute this request's LLM calls to it."""
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    llm_relay.bind(session_id)
    return session


def _register_session(session_id: str, session: GameSession) -> None:
    sessions[session_id] = session
    llm_relay.register_session(session_id, session.push_event_threadsafe)
    llm_relay.bind(session_id)


# --- Event mapping (pure) -------------------------------------------------
# The async endpoints and the demo driver's worker thread must emit the
# same events for the same engine results; these mappers are the single
# source of that shape. Each returns [(event_type, data, layer), ...].

def briefing_events(inject: Dict[str, Any]):
    """Events for one turn briefing: the inject on its channel's layer
    (DATA_LAYERS.md par. D - `channel` is the authoring-side tag), then the
    ready prompt."""
    channel = inject.get("channel", "briefing")
    return [
        ("transcript", {
            "type": "inject",
            "title": inject.get("title", "SITUATION UPDATE"),
            "channel": channel,
            "content": inject.get("description", "") or
                       "\n".join(inject.get("description_lines", [])),
        }, layer_for_channel(channel)),
        ("system", {
            "content": "BRIEFING COMPLETE. AWAITING ACKNOWLEDGEMENT."
        }, Layer.SITREP),
    ]


def adjudication_events(result: Dict[str, Any], manager: GameManager):
    """Events for one adjudicated decision, layer-tagged per
    DATA_LAYERS.md par. D: player-facing prose on SITREP, advisor
    reactions on CABINET, cables on DIPLOMATIC, raw effects/verdicts and
    parse health on REFEREE (server-filtered from player streams)."""
    events = [
        ("transcript", {
            "type": "system",
            "content": f"INTERPRETATION: {result['interpretation']}"
        }, Layer.SITREP),
        ("transcript", {
            "type": "narrator",
            "content": result['reasoning']
        }, Layer.SITREP),
        ("transcript", {
            "type": "system",
            "content": "UPDATING STRATEGIC METRICS..."
        }, Layer.SITREP),
    ]

    if result['advisor_reactions']:
        for role, txt in result['advisor_reactions']:
            events.append(("transcript", {
                "type": "advisor",
                "role": role,
                "content": txt
            }, Layer.CABINET))

    if result['international_reactions']:
        for r in result['international_reactions']:
            events.append(("transcript", {
                "type": "inject",
                "title": f"DIPLOMATIC CABLE: {r['actor_id']}",
                "channel": "diplomatic",
                "content": r['public_response']
            }, Layer.DIPLOMATIC))

    # The referee's own record of the turn: applied metric deltas and the
    # advisory verdicts, raw. Never reaches a player stream.
    events.append(("adjudication", {
        "interpretation": result.get("interpretation"),
        "effects": result.get("effects") or {},
        "pushback": result.get("pushback") or [],
        "critical_concerns": result.get("critical_concerns") or [],
        "error": result.get("error"),
    }, Layer.REFEREE))

    if result.get("ending"):
        events.append(("ending", result["ending"], Layer.SITREP))

    events.append(("system", {
        "content": f"TURN {manager.world.turn} COMPLETE. ADVANCING..."
    }, Layer.SITREP))

    events.append(("state_update", {
        "phase": manager.world.phase,
        "turn": manager.world.turn,
        "metrics": manager.world.metrics.dict()
    }, Layer.SITREP))

    # LLM system health after the heaviest call cluster of the turn
    # (DATA_LAYERS.md par. D: facilitator feed).
    try:
        from llm.parse_health import snapshot
        events.append(("parse_health", snapshot(), Layer.REFEREE))
    except Exception:
        pass

    return events


class NewGameRequest(BaseModel):
    scenario_id: str = "war_game_2025"
    variant: str = "standard"
    difficulty: str = "standard"
    play_mode: str = "immersive"
    player_name: str = "Prime Minister"
    # Facilitator (EXCON) sessions receive REFEREE-layer events over
    # /stream: raw adjudication effects, llm_call records, parse health.
    # Player sessions (the default) have REFEREE filtered server-side.
    # Set here at create time - there is deliberately no way to raise a
    # live session to facilitator afterwards. `?facilitator=true` on the
    # POST /game/new query string works too (curl convenience).
    facilitator: bool = False


class DiscussionRequest(BaseModel):
    session_id: str
    question: str
    # "all" puts the question to every seated advisor at once (one LLM call
    # per advisor — see GameManager.process_question_all). Anything else,
    # None included, keeps the keyword-routed single-answer behaviour.
    advisor: Optional[str] = None


class DecisionRequest(BaseModel):
    session_id: str
    action_text: str


class InterpretDecisionRequest(BaseModel):
    session_id: str
    action_text: str


class CommitDecisionRequest(BaseModel):
    session_id: str
    action_text: str
    user_choice: str = "confirm"  # confirm | override | apply_recommendations


class CriticalConcern(BaseModel):
    role: str
    concern: str
    recommendation: str


class InterpretationResponse(BaseModel):
    interpretation: str
    critical_concerns: List[CriticalConcern]
    forces_involved: List[str] = []
    timeline: str = "Immediate"
    raw_transcript: List[str] = []


class DiplomaticCallRequest(BaseModel):
    session_id: str
    country_name: str


class DiplomacyReplyRequest(BaseModel):
    session_id: str
    message: str


class DiplomacyResponse(BaseModel):
    transcript: List[str]
    active: bool
    title: Optional[str] = None
    outcome: Optional[Dict[str, Any]] = None


class SaveGameRequest(BaseModel):
    session_id: str
    save_name: str


class LoadGameRequest(BaseModel):
    save_path: str


class SaveResponse(BaseModel):
    success: bool
    save_path: str
    timestamp: str


class SaveListResponse(BaseModel):
    saves: List[Dict[str, Any]]


class ScenarioInfo(BaseModel):
    id: str
    name: str
    description: str
    variants: List[str]


class ScenarioListResponse(BaseModel):
    scenarios: List[ScenarioInfo]


class LLMConfigResponse(BaseModel):
    provider: str
    contexts: Dict[str, str]
    models: Dict[str, str]


class LLMConfigUpdateRequest(BaseModel):
    provider: Optional[str] = None
    contexts: Optional[Dict[str, str]] = None


class SessionResponse(BaseModel):
    session_id: str
    turn: int
    phase: str
    metrics: Dict[str, int]
    advisors: List[Dict[str, str]] = []
    # A scripted mandatory diplomatic call left live by the briefing
    # (ER-033): {"country", "context", "title"}. The client answers it via
    # /game/action/diplomacy/reply before any decision is accepted.
    pending_encounter: Optional[Dict[str, Any]] = None


class ForceUnit(BaseModel):
    id: str
    branch: str
    unit_type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    readiness_turns: Optional[int] = None
    notes: Optional[str] = None


class StockpileItem(BaseModel):
    category: str
    name: str
    count: int
    note: Optional[str] = None


class ResourceSummary(BaseModel):
    forces: List[ForceUnit]
    stockpiles: List[StockpileItem]


class DiplomaticContact(BaseModel):
    country_code: str
    title: Optional[str] = None
    access_level: str
    disposition: Optional[str] = None
    notes: Optional[str] = None


class VibesResponse(BaseModel):
    vibes: List[str]
    dominant: str
    intensity: int


class AdvisorState(BaseModel):
    role: str
    name: str
    trust: int
    relationship: str
    status: str
    notes: Optional[str] = None


class AdvisorsResponse(BaseModel):
    advisors: List[AdvisorState]


class FlagItem(BaseModel):
    key: str
    label: str
    severity: str
    turn_activated: Optional[int] = None


class FlagsResponse(BaseModel):
    active_flags: List[FlagItem]
    inactive_flags: List[FlagItem]


class IntelActor(BaseModel):
    code: str
    name: str
    category: str
    last_updated: Optional[str] = None


class IntelListResponse(BaseModel):
    available_actors: List[IntelActor]


class IntelDetailResponse(BaseModel):
    actor: str
    code: str
    assessment: Dict[str, Any]
    confidence: str
    last_updated: int


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "sessions_active": len(sessions)}


@app.post("/game/new", response_model=SessionResponse)
async def new_game(request: NewGameRequest, facilitator: bool = False):
    """Initialize a new game session.

    ``facilitator`` (body field or query param) opts the session's /stream
    into the REFEREE layer - see NewGameRequest.
    """
    import uuid
    session_id = str(uuid.uuid4())

    # Initialize game manager
    manager = GameManager(
        scenario_id=request.scenario_id,
        variant=request.variant,
        difficulty=request.difficulty,
        play_mode=request.play_mode
    )

    # Store session
    session = GameSession(manager,
                          facilitator=request.facilitator or facilitator)
    _register_session(session_id, session)

    # Generate initial briefing
    pending_encounter = None
    try:
        # The cold open. The engine authored these beats precisely so no
        # front end opens on a bare inject (engine/opening.py); this front
        # end was the one that never adopted them - its players started on
        # five simultaneous crises with no idea who anyone was.
        for scene in manager.get_opening_scenes():
            await session.push_event("transcript", {
                "type": "scene",
                "title": scene.title or "YOUR ROLE",
                "location": scene.location,
                "timestamp": scene.timestamp,
                "content": "\n".join(scene.body),
            }, layer=Layer.SITREP)

        inject = manager.get_turn_briefing()
        pending_encounter = inject.get("pending_encounter")

        # Push Briefing as event, on the layer its authored channel names
        for event_type, data, layer in briefing_events(inject):
            await session.push_event(event_type, data, layer=layer)

    except Exception as e:
        print(f"Error generating initial briefing: {e}")
        await session.push_event("transcript", {
            "type": "error",
            "content": "FAILED TO LOAD BRIEFING DATA"
        }, layer=Layer.SITREP)
    
    return SessionResponse(
        session_id=session_id,
        turn=manager.world.turn,
        phase=manager.world.phase,
        metrics=manager.world.metrics.dict(),
        pending_encounter=pending_encounter,
        advisors=[
            {"role": "NSA", "status": "online"},
            {"role": "CDS", "status": "online"},
            {"role": "Foreign Sec", "status": "online"},
            {"role": "Home Sec", "status": "online"},
            {"role": "Attorney General", "status": "online"}
        ]
    )


@app.get("/game/{session_id}/state")
async def get_game_state(session_id: str):
    """Get current world state."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return session.manager.world.dict()


@app.get("/game/{session_id}")
async def get_game_state(session_id: str):
    """Get full game state for session resumption."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    manager = sessions[session_id].manager
    return {
        "session_id": session_id,
        "turn": manager.world.turn,
        "phase": manager.world.phase,
        "metrics": manager.world.metrics.dict(),
        "advisors": manager.get_advisors_state(),
        # A restored session is unreadable without these: the transcript is
        # the game so far, and a live mandatory call blocks briefing and
        # decisions - the client needs to see the call it must answer.
        "transcript": manager.transcript,
        "active_call": _active_call_state(manager),
    }


def _active_call_state(manager) -> Optional[dict]:
    """The live diplomatic call a client must be able to render, else None."""
    enc = manager.active_encounter
    if enc is None or not enc.active:
        return None
    return {
        "country": enc.country,
        "title": enc.title,
        "required": enc.required,
        "transcript": list(enc.transcript),
    }


@app.get("/game/{session_id}/resources", response_model=ResourceSummary)
async def get_resources(session_id: str):
    """Get game resources (forces and stockpiles)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return session.manager.get_resources()


@app.get(
    "/game/{session_id}/diplomacy/contacts",
    response_model=List[DiplomaticContact]
)
async def get_diplomatic_contacts(session_id: str):
    """Get available diplomatic contacts."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return session.manager.get_diplomatic_contacts()


@app.get("/game/{session_id}/state/vibes", response_model=VibesResponse)
async def get_situation_vibes(session_id: str):
    """Get narrative atmosphere/vibes."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return sessions[session_id].manager.get_situation_vibes()
    except Exception as e:
        print(f"ERROR VIBES: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{session_id}/state/advisors", response_model=AdvisorsResponse)
async def get_advisors_state(session_id: str):
    """Get advisor trust and status."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return {"advisors": sessions[session_id].manager.get_advisors_state()}
    except Exception as e:
        print(f"ERROR ADVISORS: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{session_id}/state/flags", response_model=FlagsResponse)
async def get_world_flags(session_id: str):
    """Get active world/crisis flags."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return sessions[session_id].manager.get_world_flags()
    except Exception as e:
        print(f"ERROR FLAGS: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{session_id}/intel", response_model=IntelListResponse)
async def get_intel_list(session_id: str):
    """List available intelligence targets."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return {"available_actors": sessions[session_id].manager.get_intel_actors()}
    except Exception as e:
        print(f"ERROR INTEL LIST: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{session_id}/intel/{actor_code}", response_model=IntelDetailResponse)
async def get_intel_detail(session_id: str, actor_code: str):
    """Get detailed intelligence assessment for an actor."""
    session = _session_or_404(session_id)

    # This might be slow, consider async execution if needed
    try:
        detail = session.manager.get_intel_detail(actor_code)
        # The dispatch box: an intelligence product was pulled (INTEL layer)
        await session.push_event("intel", {
            "type": "assessment_pulled",
            "actor": detail.get("actor"),
            "code": detail.get("code"),
            "confidence": detail.get("confidence"),
        }, layer=Layer.INTEL)
        return detail
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Intel generation failed: {e}")


@app.post("/game/action/call", response_model=DiplomacyResponse)
async def make_diplomatic_call(request: DiplomaticCallRequest):
    """Initiate a diplomatic call."""
    session = _session_or_404(request.session_id)

    try:
        with session.lock:
            result = session.manager.start_diplomacy(request.country_name)
        # The red phone: mirror the call opening onto the DIPLOMATIC layer
        await session.push_event("diplomacy", {
            "type": "call_started",
            "country": request.country_name,
            "title": result.get("title"),
            "transcript": result.get("transcript", []),
        }, layer=Layer.DIPLOMATIC)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR CALL INIT: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/action/diplomacy/reply", response_model=DiplomacyResponse)
async def reply_diplomatic_call(request: DiplomacyReplyRequest):
    """Reply to the active diplomatic call."""
    session = _session_or_404(request.session_id)

    try:
        with session.lock:
            mark = len(getattr(session.manager.active_encounter,
                               "transcript", []) or [])
            result = session.manager.process_diplomacy(request.message)
        # New exchange lines and (once the call ends) the outcome reading,
        # mirrored onto the DIPLOMATIC layer
        await session.push_event("diplomacy", {
            "type": "call_turn",
            "lines": (result.get("transcript") or [])[mark:],
            "active": result.get("active"),
            "outcome": result.get("outcome"),
        }, layer=Layer.DIPLOMATIC)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR CALL REPLY: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/save", response_model=SaveResponse)
async def save_game_endpoint(request: SaveGameRequest):
    """Save current game state."""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        path = sessions[request.session_id].manager.save_game(request.save_name)
        return {
            "success": True,
            "save_path": path,
            "timestamp": "now" 
        }
    except Exception as e:
        print(f"ERROR SAVE: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/load")
async def load_game_endpoint(request: LoadGameRequest):
    """Load game from file and create new session."""
    try:
        from engine.game_manager import GameManager
        manager = GameManager.load_game(request.save_path)
        
        import uuid
        new_session_id = str(uuid.uuid4())
        new_session = GameSession(manager)
        _register_session(new_session_id, new_session)
        
        return {
            "session_id": new_session_id,
            "turn": manager.world.turn,
            "phase": manager.world.phase,
            "metrics": manager.world.metrics.dict(),
            "transcript": manager.transcript,
            "active_call": _active_call_state(manager),
        }
    except Exception as e:
        print(f"ERROR LOAD: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/saves", response_model=SaveListResponse)
async def list_saves_endpoint():
    """List available save files."""
    try:
        from engine.game_manager import GameManager
        # Instantiate temp manager to access path logic
        gm = GameManager() 
        saves = gm.list_saves()
        return {"saves": saves}
    except Exception as e:
        print(f"ERROR LIST SAVES: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scenarios", response_model=ScenarioListResponse)
async def list_scenarios_endpoint():
    """List available game scenarios."""
    try:
        from engine.scenario_loader import list_all_scenarios
        scenarios = list_all_scenarios()
        return {"scenarios": scenarios}
    except Exception as e:
        print(f"ERROR LIST SCENARIOS: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/settings/llm", response_model=LLMConfigResponse)
async def get_llm_settings():
    """Get LLM configuration."""
    try:
        from llm.model_config import get_model_config, MODEL_NAMES
        config = get_model_config()
        summary = config.get_summary()
        
        models_map = {k.value: v for k, v in MODEL_NAMES.items()}
        
        return {
            "provider": "Google Gemini",
            "contexts": summary,
            "models": models_map
        }
    except Exception as e:
        print(f"ERROR GET LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/settings/llm")
async def update_llm_settings(request: LLMConfigUpdateRequest):
    """Update LLM configuration."""
    try:
        from llm.model_config import get_model_config
        config = get_model_config()
        
        if request.contexts:
            if "mode" in request.contexts:
                mode = request.contexts["mode"]
                if mode == "flash":
                    config.use_flash_for_all()
                elif mode == "pro":
                    config.use_pro_for_all()
        
        return {"status": "updated"}
    except Exception as e:
        print(f"ERROR SET LLM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _stream_filter(item: Dict[str, Any], facilitator: bool) -> Optional[Dict[str, Any]]:
    """Strip the server-side layer key; drop REFEREE items for players.

    The REFEREE tag (raw effects, verdicts, llm_call records, parse health)
    must never reach a player browser (DATA_LAYERS.md par. D); only a
    session created with the facilitator flag receives it.
    """
    layer = item.pop("_layer", None)
    if layer is Layer.REFEREE and not facilitator:
        return None
    return item


@app.get("/stream/{session_id}")
async def stream_game_events(session_id: str, request: Request):
    """SSE endpoint for streaming game events.

    REFEREE-layer events are filtered server-side unless the session was
    created with the facilitator flag - see _stream_filter.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    async def event_generator():
        while True:
            # Check for disconnection
            if await request.is_disconnected():
                break

            # Wait for event
            try:
                # Wait for event with timeout to allow checking connection status
                event = await asyncio.wait_for(session.event_queue.get(), timeout=1.0)
                event = _stream_filter(event, session.facilitator)
                if event is None:
                    continue  # server-side REFEREE filter
                yield event
            except asyncio.TimeoutError:
                # Keep-alive comment
                yield {"comment": "keep-alive"}
            except Exception as e:
                print(f"Stream error: {e}")
                break

    return EventSourceResponse(event_generator())


@app.post("/game/{session_id}/briefing", response_model=SessionResponse)
async def run_turn_briefing_endpoint(session_id: str):
    """Run the current turn's briefing and return it (ER-022).

    POST /game/new runs turn one's briefing itself; this endpoint is how
    every later turn gets its inject, inject effects, narrator bridge and
    mandatory diplomatic encounter — without it the HTTP path had no
    briefing after turn one. Same payload shape as /game/new. Refused while
    a scripted mandatory call is still live.
    """
    session = _session_or_404(session_id)
    manager = session.manager
    _require_no_mandatory_call(manager)

    pending_encounter = None
    try:
        with session.lock:
            inject = manager.get_turn_briefing()
        pending_encounter = inject.get("pending_encounter")

        # Push Briefing as event, on the layer its authored channel names
        for event_type, data, layer in briefing_events(inject):
            await session.push_event(event_type, data, layer=layer)

    except Exception as e:
        print(f"Error generating briefing: {e}")
        await session.push_event("transcript", {
            "type": "error",
            "content": "FAILED TO LOAD BRIEFING DATA"
        }, layer=Layer.SITREP)

    return SessionResponse(
        session_id=session_id,
        turn=manager.world.turn,
        phase=manager.world.phase,
        metrics=manager.world.metrics.dict(),
        pending_encounter=pending_encounter,
        advisors=[
            {"role": "NSA", "status": "online"},
            {"role": "CDS", "status": "online"},
            {"role": "Foreign Sec", "status": "online"},
            {"role": "Home Sec", "status": "online"},
            {"role": "Attorney General", "status": "online"}
        ]
    )


@app.post("/game/{session_id}/briefing/ack")
async def acknowledge_briefing(session_id: str):
    """Acknowledge briefing and move to discussion phase."""
    session = _session_or_404(session_id)
    manager = session.manager

    with session.lock:
        if manager.world.phase != "briefing":
            if manager.world.phase == "discussion":
                return {"status": "success", "phase": "discussion"}
            raise HTTPException(status_code=400,
                                detail=f"Wrong phase: {manager.world.phase}")

        # Advance phase
        manager.world.phase = "discussion"

    # Push state update
    await session.push_event("state_update", {
        "phase": "discussion",
        "turn": manager.world.turn
    }, layer=Layer.SITREP)

    return {"status": "success", "phase": "discussion"}


# Speaker prefixes that mark a discussion transcript line as an advisor's.
# handle_player_question emits the initial_conditions persona names
# ("Military Commander", not "CDS" - see agents/conversation.py and
# data/scenarios/war_game_2025/initial_conditions.yaml); the cabinet titles
# the fiction uses elsewhere (cli/display_utils._ROLE_DISPLAY_TITLES) and the
# legacy short forms are kept so older transcripts still classify.
_ADVISOR_STREAM_ROLES = {
    # initial_conditions persona names (what handle_player_question emits)
    "government leader", "military commander", "intelligence coordinator",
    "domestic security", "diplomatic lead", "legal advisor",
    # cabinet titles used by the fiction / display layer
    "prime minister", "chief of the defence staff", "national security advisor",
    "foreign secretary", "home secretary", "attorney general",
    "cabinet secretary",
    # legacy short forms
    "nsa", "cds",
}


def classify_discussion_line(line: str):
    """Split an engine transcript line into (msg_type, role, content).

    The candidate prefix is read decoration-tolerantly (strip_decoration), so
    a markdown-emphasised "**Military Commander:**" still classifies as an
    advisor line rather than streaming as narrator text.
    """
    from llm.parsing import strip_decoration

    if ":" in line:
        parts = line.split(":", 1)
        potential_role = strip_decoration(parts[0])
        if potential_role.lower() in _ADVISOR_STREAM_ROLES:
            return "advisor", potential_role, parts[1].strip()
    return "narrator", None, line


@app.post("/game/discussion")
async def post_discussion(request: DiscussionRequest):
    """Ask advisors a question."""
    session = _session_or_404(request.session_id)
    manager = session.manager

    if manager.world.phase != "discussion":
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")

    # Process question (blocking for now, could be async in future).
    # advisor == "all" asks the whole room: every advisor answers in role.
    with session.lock:
        if (request.advisor or "").strip().lower() == "all":
            responses = manager.process_question_all(request.question)
        else:
            responses = manager.process_question(request.question)

    # Push responses to stream. Advisor lines belong to the CABINET layer
    # (DATA_LAYERS.md par. D); narrator/other lines stay on SITREP.
    for line in responses:
        msg_type, role, content = classify_discussion_line(line)
        await session.push_event("transcript", {
            "type": msg_type,
            "role": role,
            "content": content
        }, layer=Layer.CABINET if msg_type == "advisor" else Layer.SITREP)

    return {"status": "processed"}


def _require_no_mandatory_call(manager: GameManager) -> None:
    """Refuse a decision while a scripted mandatory call is unanswered.

    The briefing leaves the encounter live on the manager (ER-033); the
    client drives it through /game/action/diplomacy/reply. Until it ends,
    deciding the turn would abandon the President mid-sentence.
    """
    encounter = manager.active_encounter
    if encounter is not None and encounter.active and \
            getattr(encounter, "required", False):
        raise HTTPException(
            status_code=409,
            detail="A mandatory diplomatic call is live; answer it via "
                   "/game/action/diplomacy/reply before deciding."
        )


@app.post("/game/decision", summary="[LEGACY] Commit to a decision (One-shot)")
async def post_decision(request: DecisionRequest):
    """Commit to a decision (Legacy endpoint).
    
    Use /game/decision/interpret and /game/decision/commit for the new 2-step flow.
    """
    session = _session_or_404(request.session_id)
    manager = session.manager

    if manager.world.phase not in ["discussion", "decision"]:
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    _require_no_mandatory_call(manager)

    with session.lock:
        manager.world.phase = "decision"
        # Process decision (legacy one-shot)
        result = manager.resolve_decision(request.action_text)

    # ... (rest of response handling identical to commit)
    await _stream_adjudication_results(session, result)
    
    return {"status": "processed"}


@app.post("/game/decision/interpret", response_model=InterpretationResponse)
async def interpret_decision(request: InterpretDecisionRequest):
    """Step 1: Interpret decision and get advisor feedback."""
    session = _session_or_404(request.session_id)
    manager = session.manager

    if manager.world.phase not in ["discussion", "decision"]:
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    _require_no_mandatory_call(manager)

    # Interpret without committing
    try:
        print(f"DEBUG: calling manager.interpret_decision with '{request.action_text}'")
        with session.lock:
            result = manager.interpret_decision(request.action_text)
        print(f"DEBUG: result keys: {result.keys()}")
        
        return InterpretationResponse(
            interpretation=result["interpretation"],
            critical_concerns=result["critical_concerns"],
            raw_transcript=result["raw_transcript"]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in interpret_decision: {e}")
        # If it's a validation error, it might be helpful to see it
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
    
    return InterpretationResponse(
        interpretation=result["interpretation"],
        critical_concerns=result["critical_concerns"],
        raw_transcript=result["raw_transcript"]
    )


@app.post("/game/decision/commit")
async def commit_decision(request: CommitDecisionRequest):
    """Step 2: Commit to a decision and run adjudication."""
    session = _session_or_404(request.session_id)
    manager = session.manager

    # Allow 'discussion' phase too, as client might come straight from there if skipping interpret
    if manager.world.phase not in ["discussion", "decision"]:
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    _require_no_mandatory_call(manager)

    with session.lock:
        manager.world.phase = "decision"
        # Resolve decision
        result = manager.resolve_decision(request.action_text)

    # Stream results
    await _stream_adjudication_results(session, result)
    
    return {"status": "processed"}


async def _stream_adjudication_results(session: GameSession, result: Dict[str, Any]):
    """Helper to stream adjudication results to SSE, layer-tagged."""
    for event_type, data, layer in adjudication_events(result, session.manager):
        await session.push_event(event_type, data, layer=layer)


_DASHBOARD_PATH = Path(__file__).resolve().parent / "dashboard.html"


@app.get("/dashboard")
async def dashboard_page():
    """The observability + control dashboard (self-contained, no build step).

    Panels: layer-tagged event ledger, metric traces, llm_call feed,
    reroute matrix, inject console, prompt editor, demo driver. Create or
    attach to a session from the page header; facilitator sessions show
    the REFEREE layer.
    """
    if not _DASHBOARD_PATH.exists():
        raise HTTPException(status_code=500, detail="dashboard.html missing")
    return FileResponse(_DASHBOARD_PATH, media_type="text/html")


# Control surface (reroute matrix, inject console, prompt editor) and the
# headless demo driver live in their own modules.
from api.control import router as control_router  # noqa: E402
from api.demo import router as demo_router  # noqa: E402

app.include_router(control_router)
app.include_router(demo_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
