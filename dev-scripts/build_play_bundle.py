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
    """Write docs/game.zip and stamp docs/index.html to match it.

    Returns:
        0 on success, 1 if the deploy would be incomplete — a missing bundle
        source, page asset, or index.html, or a page that cannot carry the
        stamp. Nothing is written in that case.
    """
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Everything the deploy needs is read and checked before a byte is
    # written. A build that succeeds having quietly skipped a missing app.js —
    # or having left index.html unstamped — publishes exactly the incoherent
    # deploy this stamp exists to prevent, and says it went fine.
    try:
        files = collect_files()
        # Read once. The hash and the archive must describe the same bytes:
        # reading each file twice leaves a window, however small, in which an
        # edit lands between them and ships a game.zip whose contents are not
        # the ones its own build_id.txt claims.
        packed = [(arc, full.read_bytes()) for full, arc in files]
        stamp = compute_stamp(files, packed=packed)
    except FileNotFoundError as e:
        print(f"  MISSING {e} — aborting", file=sys.stderr)
        return 1
    if not PAGE.is_file():
        print(f"  MISSING {PAGE} — aborting: there is no page to stamp, so "
              f"nothing would tell a browser which build this is",
              file=sys.stderr)
        return 1

    # Stamp the page first: if it cannot carry the stamp, there is no point
    # writing an archive whose id nothing will ever quote.
    try:
        stamped_page = stamp_page(stamp)
    except ValueError as e:
        print(f"  {e} — aborting", file=sys.stderr)
        return 1

    raw = 0
    # Fixed timestamps keep the zip byte-identical across rebuilds, so a
    # committed artifact only churns when the game actually changes.
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arc, data in packed:
            info = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            raw += len(data)
            z.writestr(info, data)
        info = zipfile.ZipInfo(BUILD_STAMP_ARCNAME, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, stamp + "\n")

    size = OUT.stat().st_size
    print(f"  {len(files)} files, {raw:,} raw -> {size:,} bytes")
    print(f"  {OUT.relative_to(ROOT)}")
    print(f"  build {stamp}"
          f"{'' if stamped_page else '  (index.html already current)'}")
    return 0


def compute_stamp(files: list[tuple[Path, str]],
                  packed: "list[tuple[str, bytes]] | None" = None) -> str:
    """A short content hash over everything a browser has to agree about.

    Covers the bundle's own files and the page assets beside it, so changing
    any one of them changes the stamp — and therefore every asset URL — at
    once. A browser then either has the whole build or fetches the whole
    build; it cannot end up running half of each.

    Args:
        files: The bundle's sources, from ``collect_files``.
        packed: Their bytes, if the caller has already read them. Passing
            these keeps the hash and the archive describing the same bytes;
            reading twice leaves a window for an edit to land between.

    Raises:
        FileNotFoundError: if a configured page asset is missing. Skipping it
            would hash as though the deploy were complete and hand back a
            stamp that says so.
    """
    h = hashlib.sha256()

    def entry(name: str, data: bytes) -> None:
        """Frame one entry so its bounds survive concatenation.

        Names and contents used to be hashed as two flat runs, which let a
        byte move from the end of one file to the start of the next without
        changing the stream: ``[b"X", b"YZ"]`` and ``[b"XY", b"Z"]`` hash
        alike. A stamp that misses a real change is worse than no stamp,
        because every asset URL then keeps asserting a build the browser no
        longer has. Length-delimiting each entry closes that.
        """
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)

    contents = ({arc: data for arc, data in packed} if packed is not None
                else {arc: full.read_bytes() for full, arc in files})
    for _, arc in sorted(files, key=lambda pair: pair[1]):
        entry(arc, contents[arc])
    for name in sorted(STAMPED_ASSETS + UNSTAMPED_IN_HASH):
        asset = ROOT / "docs" / name
        if not asset.is_file():
            raise FileNotFoundError(str(asset))
        entry(name, asset.read_bytes())
    return h.hexdigest()[:12]


def stamp_page(stamp: str) -> bool:
    """Write the stamp into index.html. Returns True if the file changed.

    Idempotent: an existing stamp is replaced rather than accumulated, so the
    script is safe to run repeatedly. False means the page already declared
    this build, never that there was no page — ``build`` refuses to get this
    far without one.

    Raises:
        FileNotFoundError: if index.html is missing.
        ValueError: if the page cannot carry the stamp — no place to put the
            build id, or a configured asset it never references.
    """
    if not PAGE.is_file():
        raise FileNotFoundError(str(PAGE))
    text = original = PAGE.read_text(encoding="utf-8")

    # Every rewrite below is checked. A regex that matches nothing is a no-op,
    # and a no-op here is silent: the build would report success having left
    # the page with no build id, or with asset URLs a browser is free to serve
    # from an older deploy. That is the failure this whole change exists to
    # stop, so it must not be reachable through the tool that prevents it.
    meta = f'<meta name="ff-build" content="{stamp}">'
    text, replaced = re.subn(r'<meta name="ff-build" content="[^"]*">', meta, text)
    if not replaced:
        anchor = '<meta name="color-scheme" content="dark">'
        if anchor not in text:
            raise ValueError(
                f"{PAGE} carries no ff-build meta and no {anchor!r} to insert "
                f"one after — the page could not declare which build it is")
        text = text.replace(anchor, anchor + "\n" + meta, 1)

    for name in STAMPED_ASSETS:
        # `asset` binds this iteration's name into the replacement rather than
        # closing over the loop variable. re.subn consumes it before the next
        # iteration either way, but a late-binding closure in a rewrite that
        # edits URLs is not a thing to leave resting on call order.
        text, hits = re.subn(
            r'((?:href|src)=")' + re.escape(name) + r'(?:\?v=[^"]*)?(")',
            lambda m, asset=name: m.group(1) + asset + "?v=" + stamp + m.group(2),
            text)
        if not hits:
            raise ValueError(
                f"{PAGE} does not reference {name}, so it cannot be stamped "
                f"and a browser may serve a cached copy against a new engine")

    if text == original:
        return False
    PAGE.write_text(text, encoding="utf-8")
    return True


if __name__ == "__main__":
    raise SystemExit(build())
