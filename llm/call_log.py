"""Env-gated JSONL record of every LLM call the router dispatches.

Set WARGAME_CALL_LOG=<path> and each call appends one JSON line:

    {"ts": ..., "seq": 1, "turn": 3, "family": "quality_assessment",
     "tier": "pro", "provider": "openai_compat", "model": "...",
     "prompt": "...", "reply": "...", "finish_reason": "stop",
     "latency_ms": 812, "fallback": false, "batch_index": null,
     "batch_size": null}

One log answers four different verification questions at once: what
context reached each call (grep the prompt), what the model actually said
versus what the engine parsed (re-parse the reply offline), which model
each family resolved to, and whether any reply was cut on its output cap.
Unset, the module is inert - no file handles, no measurable cost.

The turn number is annotation: the router does not know it, so whoever
drives the game (a play harness, a campaign script) calls set_field
("turn", n) as play advances and the value is merged into every record
until changed.

Thread-safe: batch drivers dispatch from a thread pool.
"""

import json
import os
import threading
import time
from typing import Callable, List, Optional

_lock = threading.Lock()
_seq = 0
_fields: dict = {}  # annotations merged into every record (e.g. turn)

# Listeners receive a copy of every record as it is made - the live relay
# behind the API dashboard's per-call feed. Independent of the JSONL file:
# either sink alone keeps record() running.
_listeners: List[Callable[[dict], None]] = []


def enabled() -> bool:
    """True when the JSONL file sink is configured (WARGAME_CALL_LOG)."""
    return bool(os.getenv("WARGAME_CALL_LOG"))


def add_listener(listener: Callable[[dict], None]) -> None:
    """Register a callable invoked with a copy of every call record.

    Listeners run on the calling thread (batch drivers dispatch from a
    thread pool) and must not raise; a raising listener is contained so it
    can never fail an LLM call.
    """
    with _lock:
        if listener not in _listeners:
            _listeners.append(listener)


def remove_listener(listener: Callable[[dict], None]) -> None:
    with _lock:
        if listener in _listeners:
            _listeners.remove(listener)


def has_listeners() -> bool:
    with _lock:
        return bool(_listeners)


def active() -> bool:
    """True when any sink (JSONL file or listener) wants call records."""
    return enabled() or has_listeners()


def set_field(name: str, value) -> None:
    """Annotate all subsequent records (e.g. set_field("turn", 4)).

    A value of None removes the annotation.
    """
    with _lock:
        if value is None:
            _fields.pop(name, None)
        else:
            _fields[name] = value


def record(*,
           family: Optional[str],
           tier: Optional[str],
           provider: str,
           model: Optional[str],
           prompt: str,
           reply: str,
           finish_reason: Optional[str] = None,
           latency_ms: Optional[int] = None,
           fallback: bool = False,
           batch_index: Optional[int] = None,
           batch_size: Optional[int] = None) -> None:
    """Append one call record. No-op unless a sink (file or listener) exists."""
    path = os.getenv("WARGAME_CALL_LOG")
    global _seq
    with _lock:
        if not path and not _listeners:
            return
        _seq += 1
        entry = {
            "ts": round(time.time(), 3),
            "seq": _seq,
            **_fields,
            "family": family,
            "tier": tier,
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "reply": reply,
            "finish_reason": finish_reason,
            "latency_ms": latency_ms,
            "fallback": fallback,
            "batch_index": batch_index,
            "batch_size": batch_size,
        }
        if path:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        listeners = list(_listeners)

    # Outside the lock: a slow listener must not serialise the thread pool,
    # and a raising one must never fail the LLM call it observed.
    for listener in listeners:
        try:
            listener(dict(entry))
        except Exception:
            pass


def reset() -> None:
    """Clear the sequence counter and annotations (for tests)."""
    global _seq
    with _lock:
        _seq = 0
        _fields.clear()
