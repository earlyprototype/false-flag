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
from typing import Dict, Optional, List, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.world import WorldState
from engine.game_manager import GameManager

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
    def __init__(self, manager: GameManager):
        self.manager = manager
        self.event_queue: asyncio.Queue = asyncio.Queue()

    async def push_event(self, event_type: str, data: Any):
        """Push an event to the SSE stream."""
        await self.event_queue.put({
            "event": event_type,
            "data": json.dumps(data)
        })

# Map: session_id -> GameSession
sessions: Dict[str, GameSession] = {}


class NewGameRequest(BaseModel):
    scenario_id: str = "war_game_2025"
    variant: str = "standard"
    difficulty: str = "standard"
    play_mode: str = "immersive"
    player_name: str = "Prime Minister"


class DiscussionRequest(BaseModel):
    session_id: str
    question: str


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
async def new_game(request: NewGameRequest):
    """Initialize a new game session."""
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
    session = GameSession(manager)
    sessions[session_id] = session
    
    # Generate initial briefing
    try:
        inject = manager.get_turn_briefing()
        
        # Push Narrator Intro if available (from sim_loop integration)
        # Note: sim_loop might have added lines to transcript directly
        
        # Push Briefing as event
        await session.push_event("transcript", {
            "type": "inject",
            "title": inject.get("title", "SITUATION UPDATE"),
            "content": inject.get("description", "") or "\n".join(inject.get("description_lines", []))
        })
        
        # Push ready prompt
        await session.push_event("system", {
            "content": "BRIEFING COMPLETE. AWAITING ACKNOWLEDGEMENT."
        })
        
    except Exception as e:
        print(f"Error generating initial briefing: {e}")
        await session.push_event("transcript", {
            "type": "error",
            "content": "FAILED TO LOAD BRIEFING DATA"
        })
    
    return SessionResponse(
        session_id=session_id,
        turn=manager.world.turn,
        phase=manager.world.phase,
        metrics=manager.world.metrics.dict(),
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
        "advisors": manager.get_advisors_state()
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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # This might be slow, consider async execution if needed
    try:
        return sessions[session_id].manager.get_intel_detail(actor_code)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Intel generation failed: {e}")


@app.post("/game/action/call", response_model=DiplomacyResponse)
async def make_diplomatic_call(request: DiplomaticCallRequest):
    """Initiate a diplomatic call."""
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        return sessions[session_id].manager.start_diplomacy(request.country_name)
    except Exception as e:
        print(f"ERROR CALL INIT: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/action/diplomacy/reply", response_model=DiplomacyResponse)
async def reply_diplomatic_call(request: DiplomacyReplyRequest):
    """Reply to the active diplomatic call."""
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        return sessions[session_id].manager.process_diplomacy(request.message)
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
        sessions[new_session_id] = new_session
        
        return {
            "session_id": new_session_id,
            "turn": manager.world.turn,
            "phase": manager.world.phase,
            "metrics": manager.world.metrics.dict()
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


@app.get("/stream/{session_id}")
async def stream_game_events(session_id: str, request: Request):
    """SSE endpoint for streaming game events."""
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
                yield event
            except asyncio.TimeoutError:
                # Keep-alive comment
                yield {"comment": "keep-alive"}
            except Exception as e:
                print(f"Stream error: {e}")
                break
    
    return EventSourceResponse(event_generator())


@app.post("/game/{session_id}/briefing/ack")
async def acknowledge_briefing(session_id: str):
    """Acknowledge briefing and move to discussion phase."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    manager = session.manager
    
    if manager.world.phase != "briefing":
        if manager.world.phase == "discussion":
            return {"status": "success", "phase": "discussion"}
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    
    # Advance phase
    manager.world.phase = "discussion"
    
    # Push state update
    await session.push_event("state_update", {
        "phase": "discussion",
        "turn": manager.world.turn
    })
    
    return {"status": "success", "phase": "discussion"}


@app.post("/game/discussion")
async def post_discussion(request: DiscussionRequest):
    """Ask advisors a question."""
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    manager = session.manager
    
    if manager.world.phase != "discussion":
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    
    # Process question (blocking for now, could be async in future)
    responses = manager.process_question(request.question)
    
    # Push responses to stream
    for line in responses:
        # Parse role if present
        msg_type = "narrator"
        role = None
        content = line
        
        if ":" in line:
            parts = line.split(":", 1)
            potential_role = parts[0].strip()
            # Simple heuristic for advisor names
            if potential_role in ["NSA", "CDS", "Foreign Secretary", "Home Secretary", "Attorney General", "Prime Minister"]:
                msg_type = "advisor"
                role = potential_role
                content = parts[1].strip()
        
        await session.push_event("transcript", {
            "type": msg_type,
            "role": role,
            "content": content
        })
    
    return {"status": "processed"}


@app.post("/game/decision", summary="[LEGACY] Commit to a decision (One-shot)")
async def post_decision(request: DecisionRequest):
    """Commit to a decision (Legacy endpoint).
    
    Use /game/decision/interpret and /game/decision/commit for the new 2-step flow.
    """
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    manager = session.manager
    
    if manager.world.phase not in ["discussion", "decision"]:
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    
    manager.world.phase = "decision"
    
    # Process decision (legacy one-shot)
    result = manager.resolve_decision(request.action_text)
    
    # ... (rest of response handling identical to commit)
    await _stream_adjudication_results(session, result)
    
    return {"status": "processed"}


@app.post("/game/decision/interpret", response_model=InterpretationResponse)
async def interpret_decision(request: InterpretDecisionRequest):
    """Step 1: Interpret decision and get advisor feedback."""
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    manager = session.manager
    
    if manager.world.phase not in ["discussion", "decision"]:
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    
    # Interpret without committing
    try:
        print(f"DEBUG: calling manager.interpret_decision with '{request.action_text}'")
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
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    manager = session.manager
    
    # Allow 'discussion' phase too, as client might come straight from there if skipping interpret
    if manager.world.phase not in ["discussion", "decision"]:
        raise HTTPException(status_code=400, detail=f"Wrong phase: {manager.world.phase}")
    
    manager.world.phase = "decision"
    
    # Resolve decision
    result = manager.resolve_decision(request.action_text)
    
    # Stream results
    await _stream_adjudication_results(session, result)
    
    return {"status": "processed"}


async def _stream_adjudication_results(session: GameSession, result: Dict[str, Any]):
    """Helper to stream adjudication results to SSE."""
    manager = session.manager
    
    # Push interpretation
    await session.push_event("transcript", {
        "type": "system",
        "content": f"INTERPRETATION: {result['interpretation']}"
    })
    
    # Push reasoning
    await session.push_event("transcript", {
        "type": "narrator",
        "content": result['reasoning']
    })
    
    # Push effects (informational)
    await session.push_event("transcript", {
        "type": "system",
        "content": "UPDATING STRATEGIC METRICS..."
    })
    
    # Push advisor reactions
    if result['advisor_reactions']:
        for role, txt in result['advisor_reactions']:
            await session.push_event("transcript", {
                "type": "advisor",
                "role": role,
                "content": txt
            })
            
    # Push international reactions
    if result['international_reactions']:
        for r in result['international_reactions']:
            await session.push_event("transcript", {
                "type": "inject",
                "title": f"DIPLOMATIC CABLE: {r['actor_id']}",
                "content": r['public_response']
            })
    
    # Push turn advance
    await session.push_event("system", {
        "content": f"TURN {manager.world.turn} COMPLETE. ADVANCING..."
    })
    
    # Push new state
    await session.push_event("state_update", {
        "phase": manager.world.phase,
        "turn": manager.world.turn,
        "metrics": manager.world.metrics.dict()
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
