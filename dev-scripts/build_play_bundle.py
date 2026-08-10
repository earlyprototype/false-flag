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

import hashlib
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "game.zip"
PAGE = ROOT / "docs" / "index.html"

# Files the page fetches by name. They are cached independently of the bundle,
# so without a shared stamp a browser can serve a fresh page alongside a
# months-old engine — which is not a hypothetical failure: it shipped a build
# whose every batched call died inside Pyodide, answered the player from the
# offline stand-in, and told them the network was at fault. Each of these is
# fetched with the stamp below, so a changed build changes every URL at once.
#
# index.html is absent deliberately: it is the file that *carries* the stamp,
# so hashing it would be circular, and it is the one file a browser always
# revalidates anyway.
STAMPED_ASSETS = ["play.css", "ansi.js", "assets.js", "app.js"]
UNSTAMPED_IN_HASH = ["worker.js", "stub-worker.js", "stub-data.js"]

# Where the stamp is written inside the bundle, for the worker to report back.
BUILD_STAMP_ARCNAME = "build_id.txt"

# Package directories the engine imports or reads at runtime.
#
# assets/placeholders holds the intro script that engine/intro.py reads. It
# was omitted originally, and because the reader returned [] on a missing
# file the browser lost the whole cold open without saying so. Only the
# placeholders subtree is packed: the rest of assets/ is authoring material
# the engine never opens.
INCLUDE_DIRS = ["models", "engine", "llm", "agents", "data",
                "assets/placeholders"]

# The browser's Python-side driver, flattened to a top-level module so the
# worker can `import bridge`.
EXTRA_FILES = {ROOT / "docs" / "py" / "bridge.py": "bridge.py"}

SKIP_SUFFIXES = (".pyc", ".pyo")
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache"}


def collect_files() -> list[tuple[Path, str]]:
    """Every source file the bundle ships, as (path on disk, name in the zip).

    Shared with the freshness test in ``tests/test_play_bundle.py``, which
    checks the committed artifact against these same sources rather than
    trusting that somebody remembered to rebuild.

    Raises:
        FileNotFoundError: if a packed directory or extra file is missing.
    """
    files: list[tuple[Path, str]] = []

    for top in INCLUDE_DIRS:
        base = ROOT / top
        if not base.is_dir():
            raise FileNotFoundError(f"{top}/ is not a directory")
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith(SKIP_SUFFIXES):
                    continue
                full = Path(dirpath) / name
                files.append((full, str(full.relative_to(ROOT))))

    for src, arc in EXTRA_FILES.items():
        if not src.is_file():
            raise FileNotFoundError(str(src))
        files.append((src, arc))

    return files


def build() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        files = collect_files()
    except FileNotFoundError as e:
        print(f"  MISSING {e} — aborting", file=sys.stderr)
        return 1

    stamp = compute_stamp(files)

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
        info = zipfile.ZipInfo(BUILD_STAMP_ARCNAME, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, stamp + "\n")

    stamped_page = stamp_page(stamp)

    size = OUT.stat().st_size
    print(f"  {len(files)} files, {raw:,} raw -> {size:,} bytes")
    print(f"  {OUT.relative_to(ROOT)}")
    print(f"  build {stamp}"
          f"{'' if stamped_page else '  (index.html already current)'}")
    return 0


def compute_stamp(files: list[tuple[Path, str]]) -> str:
    """A short content hash over everything a browser has to agree about.

    Covers the bundle's own files and the page assets beside it, so changing
    any one of them changes the stamp — and therefore every asset URL — at
    once. A browser then either has the whole build or fetches the whole
    build; it cannot end up running half of each.
    """
    h = hashlib.sha256()
    for _, arc in sorted(files, key=lambda pair: pair[1]):
        h.update(arc.encode("utf-8"))
        h.update(b"\0")
    for full, arc in sorted(files, key=lambda pair: pair[1]):
        h.update(full.read_bytes())
    for name in sorted(STAMPED_ASSETS + UNSTAMPED_IN_HASH):
        asset = ROOT / "docs" / name
        if asset.is_file():
            h.update(name.encode("utf-8"))
            h.update(asset.read_bytes())
    return h.hexdigest()[:12]


def stamp_page(stamp: str) -> bool:
    """Write the stamp into index.html. Returns True if the file changed.

    Idempotent: an existing stamp is replaced rather than accumulated, so the
    script is safe to run repeatedly.
    """
    if not PAGE.is_file():
        print(f"  MISSING {PAGE} — page not stamped", file=sys.stderr)
        return False
    text = original = PAGE.read_text(encoding="utf-8")

    meta = f'<meta name="ff-build" content="{stamp}">'
    if re.search(r'<meta name="ff-build" content="[^"]*">', text):
        text = re.sub(r'<meta name="ff-build" content="[^"]*">', meta, text)
    else:
        text = text.replace('<meta name="color-scheme" content="dark">',
                            '<meta name="color-scheme" content="dark">\n' + meta,
                            1)

    for name in STAMPED_ASSETS:
        text = re.sub(
            r'((?:href|src)=")' + re.escape(name) + r'(?:\?v=[^"]*)?(")',
            lambda m: m.group(1) + name + "?v=" + stamp + m.group(2),
            text)

    if text == original:
        return False
    PAGE.write_text(text, encoding="utf-8")
    return True


if __name__ == "__main__":
    raise SystemExit(build())
