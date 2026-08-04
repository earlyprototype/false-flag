from __future__ import annotations

from pathlib import Path
from typing import List

INTRO_ASSET = Path("assets") / "placeholders" / "intro_stage.md"


def get_intro_lines(max_lines: int = 12) -> List[str]:
    """The cold-open script, as lines. Blank lines are kept, for spacing.

    Raises ``FileNotFoundError`` if the asset is missing. It used to return
    ``[]``, which is indistinguishable from an empty intro: the browser build
    shipped without ``assets/`` bundled and silently dropped the entire cold
    open, opening straight onto the turn 1 briefing. A packaging mistake
    should not read as an editorial choice.
    """
    root = Path(__file__).resolve().parents[1]
    intro_path = root / INTRO_ASSET
    if not intro_path.exists():
        raise FileNotFoundError(
            f"intro asset missing: {intro_path}. The opening sequence cannot "
            f"play without it. If this is the browser build, {INTRO_ASSET.parts[0]}/ "
            f"is not in the bundle — check INCLUDE_DIRS in "
            f"dev-scripts/build_play_bundle.py and rebuild docs/game.zip."
        )
    return intro_path.read_text(encoding="utf-8").splitlines()[:max_lines]
