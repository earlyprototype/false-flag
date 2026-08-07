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
_residues: Dict[str, int] = {}     # component -> replies with unparsed lines


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
    Drivers call this the moment the provider's finish reason says "length",
    so every call site is covered by one hook instead of each cap being
    audited by hand.
    """
    suffix = f" ({detail})" if detail else ""
    logger.warning("[PARSE-TRUNCATION] %s%s", component, suffix)
    with _lock:
        _truncations[component] = _truncations.get(component, 0) + 1


def record_residue(component: str, lines: int, sample: str = "") -> None:
    """Record one reply that carried non-empty lines no parser consumed.

    Residue is the early-warning signal for failure shapes nobody has
    imagined yet: a model phrasing the parser silently drops shows up here
    as a count instead of on screen as a missing voice.
    """
    suffix = f" [{sample[:80]}]" if sample else ""
    logger.warning("[PARSE-RESIDUE] %s: %d unparsed line(s)%s",
                   component, lines, suffix)
    with _lock:
        _residues[component] = _residues.get(component, 0) + 1


def snapshot() -> Dict[str, Dict[str, int]]:
    """Current counts, with keys sorted so the report is deterministic."""
    with _lock:
        return {
            "misses": {k: _misses[k] for k in sorted(_misses)},
            "fallbacks": {k: _fallbacks[k] for k in sorted(_fallbacks)},
            "truncations": {k: _truncations[k] for k in sorted(_truncations)},
            "residues": {k: _residues[k] for k in sorted(_residues)},
        }


def total() -> int:
    """Total recorded events (misses, fallbacks, truncations, residues)."""
    with _lock:
        return (sum(_misses.values()) + sum(_fallbacks.values())
                + sum(_truncations.values()) + sum(_residues.values()))


def reset() -> None:
    with _lock:
        _misses.clear()
        _fallbacks.clear()
        _truncations.clear()
        _residues.clear()
