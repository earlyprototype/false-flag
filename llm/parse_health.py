"""Module-level registry of parse misses and driver fallbacks.

The tolerant parsers in this package recover most decorated model output;
when they still cannot read a field they default it - and until now they
did so silently. Every such default now passes through here, so a campaign
can report how much of what the player saw was actually the model's answer.

Thread-safe: the batch drivers parse responses from a thread pool.
"""

import logging
import threading
from typing import Dict

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_misses: Dict[str, int] = {}      # "component.field" -> count
_fallbacks: Dict[str, int] = {}   # component -> count


def record_miss(component: str, field: str, detail: str = "") -> None:
    """Record one field a parser could not read and had to default."""
    suffix = f" ({detail})" if detail else ""
    logger.warning("[PARSE-MISS] %s.%s%s", component, field, suffix)
    with _lock:
        key = f"{component}.{field}"
        _misses[key] = _misses.get(key, 0) + 1


def record_fallback(component: str, detail: str = "") -> None:
    """Record one reply that never reached a parser (error slot, mock stand-in)."""
    suffix = f" ({detail})" if detail else ""
    logger.warning("[PARSE-FALLBACK] %s%s", component, suffix)
    with _lock:
        _fallbacks[component] = _fallbacks.get(component, 0) + 1


def snapshot() -> Dict[str, Dict[str, int]]:
    """Current counts, with keys sorted so the report is deterministic."""
    with _lock:
        return {
            "misses": {k: _misses[k] for k in sorted(_misses)},
            "fallbacks": {k: _fallbacks[k] for k in sorted(_fallbacks)},
        }


def total() -> int:
    """Total recorded events (misses plus fallbacks)."""
    with _lock:
        return sum(_misses.values()) + sum(_fallbacks.values())


def reset() -> None:
    with _lock:
        _misses.clear()
        _fallbacks.clear()
