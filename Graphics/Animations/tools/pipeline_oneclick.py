from __future__ import annotations

"""
One-click pipeline: export (if Aseprite available) -> compile -> play -> archive.

Usage (PowerShell):
  python -m Graphics.Animations.tools.pipeline_oneclick \
    --aseprite-file assets/anchor_zero.aseprite --tags neutral blink talk \
    --palette db16 --dither false --loop --overlay --duration 6 --tag quick
"""

import argparse
import os
import subprocess
import sys


def run(cmd: list[str]) -> int:
    print("$ ", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aseprite-file", default="")
    ap.add_argument("--tags", nargs="+", default=["neutral", "blink", "talk"])
    ap.add_argument("--palette", choices=["none", "db16"], default="db16")
    ap.add_argument("--dither", action="store_true")
    ap.add_argument("--width", type=int, default=80)
    ap.add_argument("--height", type=int, default=28)
    ap.add_argument("--mode", choices=["16", "24"], default="16")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--overlay", action="store_true")
    ap.add_argument("--duration", type=float, default=6.0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--scene", default="Graphics/Animations/tools/scene_schema.yaml")
    ap.add_argument("--aseprite-bin", default="aseprite")
    args = ap.parse_args()

    # Export if aseprite file exists
    if args.aseprite_file and os.path.exists(args.aseprite_file):
        run([
            sys.executable, "-m", "Graphics.Animations.tools.export_aseprite",
            args.aseprite_file, "--tags", *args.tags,
            "--out-dir", os.path.join("assets", "anchor_zero", "frames"),
            "--prefix", "anchor_", "--aseprite", args.aseprite_bin,
        ])

    # Compile
    compile_cmd = [
        sys.executable, "-m", "Graphics.Animations.tools.compile_scene",
        args.scene, "--width", str(args.width), "--height", str(args.height),
        "--mode", args.mode, "--palette", args.palette,
        "--out", "compiled_scene.json",
    ]
    if args.dither:
        compile_cmd.append("--dither")
    if run(compile_cmd) != 0:
        sys.exit(1)

    # Play
    play_cmd = [
        sys.executable, "-m", "Graphics.Animations.tools.runtime_player",
        "compiled_scene.json", "--fps", "14",
        "--duration", str(args.duration),
    ]
    if args.loop:
        play_cmd.append("--loop")
    if args.overlay:
        play_cmd.append("--overlay")
    run(play_cmd)

    # Archive
    tag = args.tag or ("db16_dither" if args.dither else "db16_nodither")
    run([
        sys.executable, "-m", "Graphics.Animations.tools.archive_run",
        "compiled_scene.json", "--scene", args.scene,
        "--tag", tag, "--include-assets",
    ])


if __name__ == "__main__":
    main()




