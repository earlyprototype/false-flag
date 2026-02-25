from __future__ import annotations

"""
Archive a compiled scene and its scene YAML into a timestamped artifacts folder.

Usage (PowerShell):
  python -m Graphics.Animations.tools.archive_run compiled_scene.json \
    --scene Graphics/Animations/tools/scene_schema.yaml \
    --tag db16_nodither_32x32 --include-assets
"""

import argparse
import datetime as dt
import json
import os
import shutil
import sys
from typing import Optional


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def copy_if_exists(src: str, dst: str) -> Optional[str]:
    if os.path.exists(src):
        ensure_dir(os.path.dirname(dst))
        shutil.copy2(src, dst)
        return dst
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("compiled", help="Path to compiled_scene.json")
    ap.add_argument("--scene", default="Graphics/Animations/tools/scene_schema.yaml")
    ap.add_argument("--tag", default="")
    ap.add_argument("--include-assets", action="store_true", help="Copy assets/ folder snapshot")
    args = ap.parse_args()

    ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tag = ("_" + args.tag) if args.tag else ""
    base_dir = os.path.join("Graphics", "Animations", "artifacts", "runs", f"{ts}{tag}")
    ensure_dir(base_dir)

    # Copy compiled scene
    compiled_dst = os.path.join(base_dir, "compiled_scene.json")
    copy_if_exists(args.compiled, compiled_dst)

    # Copy scene YAML
    scene_dst = os.path.join(base_dir, "scene_schema.yaml")
    copy_if_exists(args.scene, scene_dst)

    # Optional assets snapshot (e.g., placeholder PNGs)
    assets_src = os.path.join("assets")
    assets_dst = os.path.join(base_dir, "assets")
    if args.include_assets and os.path.exists(assets_src):
        if os.path.exists(assets_dst):
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)

    # Meta file
    meta = {
        "timestamp": ts,
        "tag": args.tag,
        "compiled_src": os.path.abspath(args.compiled),
        "scene_src": os.path.abspath(args.scene),
        "include_assets": bool(args.include_assets),
        "python": sys.version,
    }
    with open(os.path.join(base_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Archived run to {base_dir}")


if __name__ == "__main__":
    main()




