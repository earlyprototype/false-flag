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
_misses: Dict[str, int] = {}       # "component.field" -> count
_fallbacks: Dict[str, int] = {}    # component -> count
_truncations: Dict[str, int] = {}  # component -> count
_residue: Dict[str, int] = {}      # component -> unconsumed line count


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


def record_truncation(component: str, detail: str = "") -> None:
    """Record one reply the model cut short on its output cap.

    A truncated reply is a defect wherever it lands: a parsed family loses
    trailing fields, a prose family ends mid-sentence in front of the player.
    The drivers surface the provider's finish reason and the router calls
    this when it says "length", so every call site is covered by one hook
    instead of each cap being audited by hand.
    """
    suffix = f" ({detail})" if detail else ""
    logger.warning("[PARSE-TRUNCATION] %s%s", component, suffix)
    with _lock:
        _truncations[component] = _truncations.get(component, 0) + 1


def record_residue(component: str, count: int, sample: str = "") -> None:
    """Record lines a parser neither consumed nor recognised.

    Residue is the text the tolerant parser walked past: not a label, not a
    continuation, not a sentinel. A little is normal (models editorialise);
    a lot means the reply held content the parser never saw - the
    early-warning signal for failure shapes nobody has imagined yet.
    """
    if count <= 0:
        return
    suffix = f" (first: {sample})" if sample else ""
    logger.warning("[PARSE-RESIDUE] %s x%d%s", component, count, suffix)
    with _lock:
        _residue[component] = _residue.get(component, 0) + count


def snapshot() -> Dict[str, Dict[str, int]]:
    """Current counts, with keys sorted so the report is deterministic."""
    with _lock:
        return {
            "misses": {k: _misses[k] for k in sorted(_misses)},
            "fallbacks": {k: _fallbacks[k] for k in sorted(_fallbacks)},
            "truncations": {k: _truncations[k] for k in sorted(_truncations)},
            "residue": {k: _residue[k] for k in sorted(_residue)},
        }


def total() -> int:
    """Total recorded events (misses, fallbacks, truncations, residue lines)."""
    with _lock:
        return (sum(_misses.values()) + sum(_fallbacks.values())
                + sum(_truncations.values()) + sum(_residue.values()))


def reset() -> None:
    with _lock:
        _misses.clear()
        _fallbacks.clear()
        _truncations.clear()
        _residue.clear()
