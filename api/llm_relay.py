"""Relay every LLM call record onto the active session's event stream.

llm/call_log.py already sees every call the router dispatches (family,
tier, provider, model, latency, fallback). This module subscribes to it and
forwards each record to whichever GameSession the current request (or demo
thread) is working for, as a REFEREE-layer ``llm_call`` event - so the
dashboard's per-call feed is the same pipeline as the JSONL log, minus the
prompt/reply bodies, which never go over the wire.

Attribution is a contextvar: endpoints (and the demo driver's thread) call
``bind(session_id)`` before touching the GameManager; the listener reads it
back on whatever thread the router logged from. Contextvars follow the
request task, and a worker thread that binds explicitly gets its own
context - so concurrent sessions cannot cross-attribute calls.
"""

from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional

_current_session: ContextVar[Optional[str]] = ContextVar(
    "wargame_llm_relay_session", default=None)

# session_id -> push callable (GameSession.push_event_threadsafe).
# Registered at session creation, dropped when a session is removed.
_pushers: Dict[str, Callable[..., None]] = {}

#: Record fields forwarded to the stream. Prompt and reply bodies are
#: deliberately absent; their sizes stand in for them.
_FORWARD_FIELDS = (
    "seq", "ts", "turn", "family", "tier", "provider", "model",
    "finish_reason", "latency_ms", "fallback", "batch_index", "batch_size",
)


def register_session(session_id: str, pusher: Callable[..., None]) -> None:
    """Attach a session's thread-safe push callable to the relay."""
    _pushers[session_id] = pusher


def unregister_session(session_id: str) -> None:
    _pushers.pop(session_id, None)


def bind(session_id: Optional[str]) -> None:
    """Attribute subsequent LLM calls on this task/thread to a session."""
    _current_session.set(session_id)


def bound_session() -> Optional[str]:
    return _current_session.get()


def on_call_record(entry: Dict[str, Any]) -> None:
    """call_log listener: forward one sanitised record to the bound session.

    Runs on whatever thread made the LLM call; must never raise (call_log
    contains listener errors, but staying quiet here keeps the log clean).
    """
    session_id = _current_session.get()
    if not session_id:
        return
    pusher = _pushers.get(session_id)
    if pusher is None:
        return

    payload = {k: entry.get(k) for k in _FORWARD_FIELDS}
    payload["prompt_chars"] = len(entry.get("prompt") or "")
    payload["reply_chars"] = len(entry.get("reply") or "")

    from models.layers import Layer
    pusher("llm_call", payload, layer=Layer.REFEREE)


def install() -> None:
    """Subscribe the relay to the call log (idempotent)."""
    from llm import call_log
    call_log.add_listener(on_call_record)
