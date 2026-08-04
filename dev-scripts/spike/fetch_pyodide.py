"""Vendor the Pyodide runtime + only the wheels this spike needs, into ./pyodide.

Mirrors what a real static GitHub Pages deploy would ship, and lets the spike
run without depending on a CDN reachable from the browser.
"""
import json
import os
import sys
import urllib.request

VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.27.7"
BASE = f"https://cdn.jsdelivr.net/pyodide/v{VERSION}/full/"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pyodide")

RUNTIME = [
    "pyodide.js",
    "pyodide.mjs",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
]

# packages we want available offline; deps resolved from the lock file
WANT = ["pydantic", "pyyaml", "micropip", "requests", "pyodide-http"]


def get(name):
    # Download to a .part sibling and rename into place, so an interrupted
    # run cannot leave a truncated multi-MB file that every later run then
    # skips as "already fetched".
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return os.path.getsize(dest)
    part = dest + ".part"
    try:
        with urllib.request.urlopen(BASE + name, timeout=180) as r:
            data = r.read()
        with open(part, "wb") as f:
            f.write(data)
        os.replace(part, dest)
    except BaseException:
        if os.path.exists(part):
            os.remove(part)
        raise
    return len(data)


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in RUNTIME:
        try:
            print(f"  {f:26} {get(f):>10,} bytes")
        except Exception as e:
            print(f"  {f:26} SKIP ({e})")

    lock = json.load(open(os.path.join(OUT, "pyodide-lock.json")))
    pkgs = lock["packages"]

    # lock keys are normalised (pydantic-core) but `depends` uses the import
    # name (pydantic_core) — normalise or the Rust extension is silently missed
    def norm(k):
        return k.lower().replace("_", "-")

    resolved, queue = set(), [norm(w) for w in WANT]
    while queue:
        k = queue.pop()
        if k in resolved or k not in pkgs:
            continue
        resolved.add(k)
        queue.extend(norm(d) for d in pkgs[k].get("depends", []))

    total = 0
    for k in sorted(resolved):
        fn = pkgs[k]["file_name"]
        n = get(fn)
        total += n
        print(f"  {pkgs[k]['name']:20} {pkgs[k]['version']:10} {n:>10,} bytes")
    print(f"\n  wheels total: {total:,} bytes")
    runtime_total = sum(
        os.path.getsize(os.path.join(OUT, f))
        for f in RUNTIME
        if os.path.exists(os.path.join(OUT, f))
    )
    print(f"  runtime total: {runtime_total:,} bytes")
    print(f"  GRAND TOTAL:  {total + runtime_total:,} bytes")


if __name__ == "__main__":
    main()
