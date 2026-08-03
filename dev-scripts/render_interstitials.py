"""Render the between-turn interstitial vignettes to approval-preview GIFs.

Reuses the docs/media pipeline from dev-scripts/render_media.py (frames ->
Rich SVG -> Chromium raster -> Pillow GIF with true choreography timings)
to produce one GIF per vignette in docs/media/interstitials/.

    .venv/bin/python dev-scripts/render_interstitials.py [names...]

The tea-round GIF plays two acts: the normal round (escalation 45, the CDS
cup rattling, the PM's cup left behind) and then the escalation>80 variant
in which the trolley does not stop.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "dev-scripts"))

from PIL import Image, ImageStat  # noqa: E402

from render_media import (  # noqa: E402
    Rasterizer, assemble_gif, record_svg,
)

from cli import interstitials as itl  # noqa: E402
from cli.cinematics import Frame  # noqa: E402
from cli.theme import theme_manager  # noqa: E402

OUT_DIR = REPO / "docs" / "media" / "interstitials"
SEED = "preview"
ESCALATION = 45      # rattle clearly visible; punchlines on the calm branch

# Presentation-only hold before the GIF loops (in the game the final frame
# simply persists until the next prompt).
LOOP_HOLD = 1.0


def vignette_frames(name: str) -> List[Frame]:
    if name == "tea_round":
        # Act one: the tea round. Act two: the trolley does not stop.
        calm, calm_final = itl.build_interstitial(name, seed=SEED,
                                                  escalation=ESCALATION)
        frames = list(calm)
        frames[-1] = (calm_final, frames[-1][1] + 0.8)
        hot, _hot_final = itl.build_interstitial(name, seed=SEED,
                                                 escalation=90)
        frames.extend(hot)
    else:
        frames, _final = itl.build_interstitial(name, seed=SEED,
                                                escalation=ESCALATION)
        frames = list(frames)
    renderable, hold = frames[-1]
    frames[-1] = (renderable, hold + LOOP_HOLD)
    return frames


def verify(produced: List[Path]) -> None:
    print("\n── VERIFY " + "─" * 50)
    for path in sorted(produced):
        size = path.stat().st_size
        img = Image.open(path)
        n = getattr(img, "n_frames", 1)
        assert n > 1, f"{path.name}: GIF does not animate ({n} frame)"
        durations = []
        for i in range(n):
            img.seek(i)
            durations.append(img.info.get("duration", 0))
        assert all(d >= 20 for d in durations), \
            f"{path.name}: zero/short frame durations"
        img.seek(n // 2)
        var = ImageStat.Stat(img.convert("L")).stddev[0]
        assert var > 3, f"{path.name}: mid frame looks blank (σ={var:.1f})"
        print(f"  {path.name:<22} {img.size[0]}x{img.size[1]}  "
              f"{n:3d} frames  {sum(durations) / 1000:.2f}s  "
              f"{size / 1024:.0f} KB")
    total = sum(p.stat().st_size for p in OUT_DIR.iterdir()
                if p.suffix == ".gif")
    print(f"  total {total / (1024 * 1024):.1f} MB")


def main(only: Optional[Iterable[str]] = None) -> None:
    wanted = set(only) if only else None
    if wanted is not None:
        # Without this, a typo renders nothing and then "verifies" the stale
        # GIFs already on disk — a silent success.
        unknown = wanted.difference(itl.VIGNETTE_NAMES)
        if unknown:
            raise ValueError(
                f"unknown interstitial(s): {', '.join(sorted(unknown))}"
            )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    theme_manager.set_theme("defcon")
    ras = Rasterizer()
    produced: List[Path] = []
    try:
        for name in itl.VIGNETTE_NAMES:
            if wanted is not None and name not in wanted:
                continue
            frames = vignette_frames(name)
            out = OUT_DIR / f"{name}.gif"
            print(f"render {out.name} ({len(frames)} frames)")
            with tempfile.TemporaryDirectory() as td:
                paths = []
                for i, (renderable, _hold) in enumerate(frames):
                    p = Path(td) / f"f{i:04d}.png"
                    ras.rasterize(record_svg(renderable), p)
                    paths.append(p)
                assemble_gif(paths, [hold for _, hold in frames], out)
            produced.append(out)
    finally:
        ras.close()
    verify(produced)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
