"""Headless demo campaign driver, so the dashboard can be watched unmanned.

POST /demo/start creates a facilitator session and drives it from a daemon
thread the way dev-scripts/play_campaign.py drives a campaign: briefing,
answer any mandatory call, one cabinet question, interpret + commit a
decision - pushing every event through the same tagged bus a human-driven
session uses, at a readable pace. Run the server with WARGAME_LLM=mock for
a free, deterministic demo; a real provider works too, just slower.
"""

import threading
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.layers import Layer

router = APIRouter()

# session_id -> DemoRun
_runs: Dict[str, "DemoRun"] = {}

QUESTIONS = [
    "What is the current threat assessment?",
    "Where does NATO stand on this?",
    "What are the legal constraints on a response?",
    "How exposed is domestic infrastructure?",
    "What do the forces need from me?",
]

DECISIONS = [
    "Raise readiness across home commands and brief the Cabinet in full.",
    "Open a direct diplomatic channel to Moscow and inform NATO allies first.",
    "Deploy the carrier strike group to shadow the vessel and make a public statement.",
    "Convene the North Atlantic Council under Article 4 and hold the deployment.",
    "Authorise defensive patrols only, and instruct the Attorney General to review the legal basis.",
]

CALL_REPLY = ("We are coordinating fully with NATO and will share our "
              "deployment plan within the hour.")


class DemoRun:
    def __init__(self, session_id: str, turns: int, pace_s: float):
        self.session_id = session_id
        self.turns = turns
        self.pace_s = pace_s
        self.stop_requested = False
        self.running = True
        self.error: Optional[str] = None
        self.thread: Optional[threading.Thread] = None


class DemoStartRequest(BaseModel):
    turns: int = Field(default=5, ge=1, le=30)
    pace_s: float = Field(default=2.0, ge=0.0, le=30.0,
                          description="Pause between beats, seconds")
    scenario_id: str = "war_game_2025"
    variant: str = "standard"
    play_mode: str = "immersive"
    # Mystery Mode: draw a hidden narrative truth, so the dataflow view can
    # demonstrate the secret->actor/adjudication paths live.
    mystery_mode: bool = False
    seed: int = 42


def _drive(run: DemoRun, session) -> None:
    """The worker loop. Every push goes through the session's tagged bus;
    LLM calls relay because this thread binds itself to the session.

    Engine mutation happens under ``session.lock``, the same lock the API's
    mutating endpoints take - a dashboard inject fired mid-turn lands
    between engine calls, never inside one. Pacing sleeps and event pushes
    stay outside the lock."""
    from api import llm_relay
    from api.server import adjudication_events, briefing_events

    llm_relay.bind(run.session_id)
    manager = session.manager
    push = session.push_event_threadsafe

    def pace():
        time.sleep(run.pace_s)

    try:
        push("system", {"content": f"DEMO CAMPAIGN STARTED - {run.turns} turns, "
                                   f"seed {manager.seed}"}, layer=Layer.SITREP)

        for scene in manager.get_opening_scenes():
            if run.stop_requested:
                break
            push("transcript", {
                "type": "scene",
                "title": scene.title or "YOUR ROLE",
                "location": scene.location,
                "timestamp": scene.timestamp,
                "content": "\n".join(scene.body),
            }, layer=Layer.SITREP)
            pace()

        for turn_index in range(run.turns):
            if run.stop_requested or manager.is_over():
                break

            # Briefing
            with session.lock:
                inject = manager.get_turn_briefing()
            for event_type, data, layer in briefing_events(inject):
                push(event_type, data, layer=layer)
            pace()

            # A scripted mandatory call cannot be left ringing
            while (manager.active_encounter is not None
                   and manager.active_encounter.active):
                if run.stop_requested:
                    return
                with session.lock:
                    mark = len(manager.active_encounter.transcript)
                    result = manager.process_diplomacy(CALL_REPLY)
                push("diplomacy", {
                    "type": "call_turn",
                    "lines": (result.get("transcript") or [])[mark:],
                    "active": result.get("active"),
                    "outcome": result.get("outcome"),
                }, layer=Layer.DIPLOMATIC)
                pace()

            # One cabinet question
            from api.server import classify_discussion_line
            question = QUESTIONS[turn_index % len(QUESTIONS)]
            with session.lock:
                answer_lines = manager.process_question(question)
            for line in answer_lines:
                msg_type, role, content = classify_discussion_line(line)
                push("transcript", {
                    "type": msg_type, "role": role, "content": content
                }, layer=Layer.CABINET if msg_type == "advisor" else Layer.SITREP)
            pace()

            if run.stop_requested:
                break

            # Preview then commit the identical text, like the play harness
            decision = DECISIONS[turn_index % len(DECISIONS)]
            with session.lock:
                manager.interpret_decision(decision)
                result = manager.resolve_decision(decision)
            for event_type, data, layer in adjudication_events(result, manager):
                push(event_type, data, layer=layer)
            pace()

            if result.get("ending"):
                break

        push("system", {"content": "DEMO CAMPAIGN COMPLETE"}, layer=Layer.SITREP)
    except Exception as e:  # surface, never crash the server thread silently
        import traceback; traceback.print_exc()
        run.error = f"{type(e).__name__}: {e}"
        try:
            push("system", {"content": f"DEMO ERROR: {run.error}"},
                 layer=Layer.REFEREE)
        except Exception:
            pass
    finally:
        run.running = False


@router.post("/demo/start")
async def start_demo(request: DemoStartRequest) -> Dict[str, Any]:
    """Create a facilitator session and drive a demo campaign through it.

    Returns the session_id to point the dashboard (or /stream) at.
    """
    import uuid
    from engine.game_manager import GameManager
    from api.server import GameSession, _register_session

    session_id = str(uuid.uuid4())
    try:
        manager = GameManager(
            scenario_id=request.scenario_id,
            variant=request.variant,
            play_mode=request.play_mode,
            mystery_mode=request.mystery_mode,
            seed=request.seed,
            endings=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo session failed: {e}")

    session = GameSession(manager, facilitator=True)
    _register_session(session_id, session)

    run = DemoRun(session_id, request.turns, request.pace_s)
    _runs[session_id] = run
    run.thread = threading.Thread(
        target=_drive, args=(run, session),
        name=f"demo-{session_id[:8]}", daemon=True)
    run.thread.start()

    return {
        "session_id": session_id,
        "facilitator": True,
        "turns": request.turns,
        "pace_s": request.pace_s,
        "stream": f"/stream/{session_id}",
    }


@router.post("/demo/{session_id}/stop")
async def stop_demo(session_id: str) -> Dict[str, Any]:
    run = _runs.get(session_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No demo run for that session")
    run.stop_requested = True
    return {"status": "stopping", "session_id": session_id}


@router.get("/demo/{session_id}/status")
async def demo_status(session_id: str) -> Dict[str, Any]:
    run = _runs.get(session_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No demo run for that session")
    return {
        "session_id": session_id,
        "running": run.running,
        "stop_requested": run.stop_requested,
        "error": run.error,
    }
