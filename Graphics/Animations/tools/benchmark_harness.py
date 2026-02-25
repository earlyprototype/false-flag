from __future__ import annotations

"""
Simple benchmark harness to measure playback FPS and CPU time for the runtime.

Usage (PowerShell):
  python -m Graphics.Animations.tools.benchmark_harness compiled_scene.json --seconds 10
"""

import argparse
import os
import subprocess
import sys
import time


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("compiled", help="Path to compiled_scene.json")
    ap.add_argument("--seconds", type=int, default=8)
    ap.add_argument("--fps", type=float, default=14.0)
    ap.add_argument("--loop", action="store_true", help="Loop playback to honor full duration")
    args = ap.parse_args()

    # crude wall-clock based measurement running the runtime in a child process
    cmd = [
        sys.executable,
        "-m",
        "Graphics.Animations.tools.runtime_player",
        args.compiled,
        "--fps",
        str(args.fps),
        "--duration",
        str(args.seconds),
    ]
    if args.loop:
        cmd.append("--loop")
    cmd.append("--noinput")

    t0 = time.time()
    # Suppress child stdout to avoid filling the console with ANSI frames
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc.wait()
    t1 = time.time()

    elapsed = t1 - t0
    target_frames = int(args.fps * args.seconds)
    # We can't read actual frames drawn without IPC; report target vs wall-clock
    print(f"Ran for {elapsed:.2f}s targeting {target_frames} frames at {args.fps:.1f} FPS.")
    if abs(elapsed - args.seconds) < 0.5:
        print("Playback pacing appears stable within 0.5s tolerance.")
    else:
        print("Playback pacing deviated >0.5s; consider reducing FPS or workload.")


if __name__ == "__main__":
    main()



