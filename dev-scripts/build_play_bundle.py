#!/usr/bin/env python3
"""Build ``docs/game.zip`` — the game code the browser build runs.

The browser build is a Web Worker running the *real* engine under Pyodide.
This script packs everything that engine touches at runtime into one zip that
``pyodide.unpackArchive`` extracts to ``/game``, from where ``sys.path`` picks
it up and ``engine.persistence._default_root()`` resolves the YAML.

``cli/`` is deliberately excluded: the port rests on ``engine.game_manager``
needing no rich/typer/click, and ``tests/test_web_bridge.py`` enforces that.

Usage:
    python3 dev-scripts/build_play_bundle.py
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "game.zip"

# Package directories the engine imports or reads at runtime.
INCLUDE_DIRS = ["models", "engine", "llm", "agents", "data"]

# The browser's Python-side driver, flattened to a top-level module so the
# worker can `import bridge`.
EXTRA_FILES = {ROOT / "docs" / "py" / "bridge.py": "bridge.py"}

SKIP_SUFFIXES = (".pyc", ".pyo")
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache"}


def build() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files: list[tuple[Path, str]] = []

    for top in INCLUDE_DIRS:
        base = ROOT / top
        if not base.is_dir():
            print(f"  MISSING {top}/ — aborting", file=sys.stderr)
            return 1
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith(SKIP_SUFFIXES):
                    continue
                full = Path(dirpath) / name
                files.append((full, str(full.relative_to(ROOT))))

    for src, arc in EXTRA_FILES.items():
        if not src.is_file():
            print(f"  MISSING {src} — aborting", file=sys.stderr)
            return 1
        files.append((src, arc))

    raw = 0
    # Fixed timestamps keep the zip byte-identical across rebuilds, so a
    # committed artifact only churns when the game actually changes.
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for full, arc in files:
            info = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            data = full.read_bytes()
            raw += len(data)
            z.writestr(info, data)

    size = OUT.stat().st_size
    print(f"  {len(files)} files, {raw:,} raw -> {size:,} bytes")
    print(f"  {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
