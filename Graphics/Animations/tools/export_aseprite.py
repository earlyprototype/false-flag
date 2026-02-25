from __future__ import annotations

"""
Export tagged frames from an Aseprite file into assets/ with consistent naming.

Usage (PowerShell):
  python -m Graphics.Animations.tools.export_aseprite assets/anchor_zero.aseprite \
    --tags neutral blink talk --out-dir assets/anchor_zero/frames --prefix anchor_ --aseprite "C:/Program Files/Aseprite/aseprite.exe"

If Aseprite is not installed, the script exits gracefully.
"""

import argparse
import os
import shutil
import subprocess
import sys
from typing import List


def which(path: str) -> str | None:
    return path if path and os.path.exists(path) else shutil.which(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("aseprite_file", help="Path to .aseprite file")
    ap.add_argument("--tags", nargs="+", default=["neutral", "blink", "talk"])
    ap.add_argument("--out-dir", default=os.path.join("assets", "anchor_zero", "frames"))
    ap.add_argument("--prefix", default="anchor_")
    ap.add_argument("--aseprite", default="aseprite")
    args = ap.parse_args()

    aseprite_bin = which(args.aseprite)
    if not aseprite_bin:
        print("Aseprite not found; skipping export.")
        sys.exit(0)

    os.makedirs(args.out_dir, exist_ok=True)

    for tag in args.tags:
        pattern = os.path.join(args.out_dir, f"{args.prefix}{tag}_{{frame}}.png")
        cmd = [
            aseprite_bin,
            "-b",
            args.aseprite_file,
            "--tag",
            tag,
            "--save-as",
            pattern,
        ]
        subprocess.run(cmd, check=False)

    print(f"Exported tags {args.tags} to {args.out_dir}")


if __name__ == "__main__":
    main()




