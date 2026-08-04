#!/usr/bin/env python3
"""Vendor the Pyodide runtime + the wheels the game needs into docs/play/pyodide.

The browser build loads Pyodide from the jsDelivr CDN by default. Running this
script drops a complete local copy next to the worker; ``worker.js`` probes for
it and prefers it automatically, which restores the site's "zero external
requests" property at the cost of ~16.5 MB in the repository.

    python3 dev-scripts/fetch_pyodide.py            # -> docs/play/pyodide/
    python3 dev-scripts/fetch_pyodide.py 0.27.7 DIR

The directory is gitignored by default. To actually ship a self-hosted build
you must force-add it (``git add -f docs/play/pyodide``); see the tradeoff
note at the top of docs/play/worker.js.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

DEFAULT_VERSION = "0.27.7"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "docs" / "play" / "pyodide"

RUNTIME = [
    "pyodide.js",
    "pyodide.mjs",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
]

# Everything the game imports in the browser. Dependencies are resolved from
# the lock file, so this list only names the top-level requirements.
WANT = ["pydantic", "pyyaml", "requests", "pyodide-http"]


def _get(base: str, out: Path, name: str) -> int:
    """Fetch one file, resumably-safe: a partial download is never mistaken
    for a finished one.

    These are multi-megabyte files. Writing straight to the destination means
    an interrupted run (Ctrl-C, a dropped connection, a full disk) leaves a
    truncated file that every later run then skips as "already fetched" — and
    the breakage only shows up in the browser. Download to a ``.part``
    sibling and rename into place only once the whole body has arrived;
    ``os.replace`` is atomic on the same filesystem.
    """
    dest = out / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest.stat().st_size
    part = dest.with_name(dest.name + ".part")
    try:
        with urllib.request.urlopen(base + name, timeout=300) as r:
            data = r.read()
        part.write_bytes(data)
        os.replace(part, dest)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    return len(data)


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VERSION
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    base = f"https://cdn.jsdelivr.net/pyodide/v{version}/full/"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Pyodide {version} -> {out}")
    for name in RUNTIME:
        try:
            print(f"  {name:26} {_get(base, out, name):>10,} bytes")
        except Exception as e:  # noqa: BLE001
            print(f"  {name:26} FAILED ({e})", file=sys.stderr)
            return 1

    lock = json.loads((out / "pyodide-lock.json").read_text())
    pkgs = lock["packages"]

    # Lock keys are normalised ("pydantic-core") but `depends` uses import
    # names ("pydantic_core"); normalise or the Rust extension is silently
    # missed and pydantic import fails at runtime.
    def norm(k: str) -> str:
        return k.lower().replace("_", "-")

    # A top-level requirement the lock file does not know about must be loud.
    # Silently skipping one is exactly how a bundle shipped without pydantic's
    # Rust extension: everything looked fine until the browser tried to import
    # it. Missing *dependencies* are a different matter — the lock file is the
    # authority on those, and a name it does not carry is not a package.
    missing = [w for w in WANT if norm(w) not in pkgs]
    if missing:
        print(f"\n  ABORT: not in pyodide-lock.json for {version}: "
              f"{', '.join(missing)}", file=sys.stderr)
        print("  Refusing to write an incomplete bundle. Check the names in "
              "WANT against the lock file.", file=sys.stderr)
        return 1

    resolved: set[str] = set()
    queue = [norm(w) for w in WANT]
    while queue:
        key = queue.pop()
        if key in resolved or key not in pkgs:
            continue
        resolved.add(key)
        queue.extend(norm(d) for d in pkgs[key].get("depends", []))

    total = 0
    for key in sorted(resolved):
        pkg = pkgs[key]
        n = _get(base, out, pkg["file_name"])
        total += n
        print(f"  {pkg['name']:20} {pkg['version']:10} {n:>10,} bytes")

    runtime_total = sum((out / f).stat().st_size for f in RUNTIME if (out / f).exists())
    print(f"\n  wheels   {total:,} bytes")
    print(f"  runtime  {runtime_total:,} bytes")
    print(f"  TOTAL    {total + runtime_total:,} bytes")
    print("\n  worker.js will now prefer this local copy over the CDN.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
