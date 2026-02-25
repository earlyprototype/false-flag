from __future__ import annotations

from pathlib import Path
from typing import List


def get_intro_lines(max_lines: int = 12) -> List[str]:
    root = Path(__file__).resolve().parents[1]
    intro_path = root / "assets" / "placeholders" / "intro_stage.md"
    try:
        if intro_path.exists():
            # Keep ALL lines including blank ones for proper spacing
            intro_lines = intro_path.read_text(encoding="utf-8").splitlines()
            return intro_lines[:max_lines]
    except Exception:
        pass
    return []


