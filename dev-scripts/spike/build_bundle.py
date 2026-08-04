"""Bundle the headless game (no cli/) into game.zip for Pyodide's unpackArchive.

Deliberately excludes cli/ — the spike proves the engine never needs it.
Run from the repo root:  python3 dev-scripts/spike/build_bundle.py
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "game.zip")

# everything GameManager's import graph actually touches, plus runtime YAML
INCLUDE = ["models", "engine", "llm", "agents", "data"]


def main():
    # A missing INCLUDE directory means the zip would be silently incomplete —
    # os.walk over a path that does not exist yields nothing and raises
    # nothing, so the build "succeeds" and the failure surfaces as an
    # ImportError inside the browser. Check before writing anything.
    missing = [top for top in INCLUDE
               if not os.path.isdir(os.path.join(ROOT, top))]
    if missing:
        print(f"ABORT: missing source directories under {ROOT}: "
              f"{', '.join(missing)}", file=sys.stderr)
        print("Run this from a full checkout; refusing to write an "
              "incomplete bundle.", file=sys.stderr)
        return 1

    n = raw = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for top in INCLUDE:
            for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, top)):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for fn in filenames:
                    if fn.endswith(".pyc"):
                        continue
                    full = os.path.join(dirpath, fn)
                    arc = os.path.relpath(full, ROOT)
                    z.write(full, arc)
                    n += 1
                    raw += os.path.getsize(full)
    print(f"{n} files, {raw:,} raw -> {os.path.getsize(OUT):,} bytes at {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
