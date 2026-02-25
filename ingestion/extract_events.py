from __future__ import annotations

from typing import Any, Dict, List


def extract_events_from_segments(segments: list[str]) -> List[Dict[str, Any]]:
    """Placeholder extractor returning an empty list.

    Later versions may pattern-match segments into event stubs.
    """
    if not segments:
        return []
    # For Day-3, we don't infer events automatically; keep deterministic.
    return []



