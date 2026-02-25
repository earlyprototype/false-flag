from __future__ import annotations

"""
Compile a scene YAML into a runtime JSON with pre-encoded half-block frames.

Usage:
  python -m Graphics.Animations.tools.compile_scene scene.yaml \
    --width 80 --height 28 --mode 16 --palette db16 --dither \
    --out compiled_scene.json

Scene YAML supports either explicit glob patterns per sequence:

sprites:
  hero:
    frames:
      idle: assets/hero/idle_*.png
      blink: assets/hero/blink_*.png

or a folder + tag list (expects files like tag_*.png):

sprites:
  hero:
    path: assets/hero
    tags: [idle, blink]
    pattern: "{tag}_*.png"  # optional, default shown
"""

import argparse
import glob
import json
import math
import os
from typing import Dict, List, Tuple

import yaml

from .encode_halfblock import encode_halfblock
from .palette_db16 import nearest_terminal_index, quantise_to_palette, DB16_PALETTE


def natural_sort_key(s: str):
    import re
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def load_sequence_frames(pattern: str) -> List[str]:
    files = glob.glob(pattern)
    files.sort(key=natural_sort_key)
    return files


def center_offsets(width: int, height: int, sprite_w: int, sprite_h_cells: int) -> tuple[int, int]:
    x = max(0, width // 2 - sprite_w // 2)
    y = max(0, height // 2 - sprite_h_cells // 2)
    return x, y


def _parse_sgr_indices(seq: str) -> Tuple[int | None, int | None]:
    """Parse a single CSI SGR like \x1b[31m or \x1b[100m and return (fg_index, bg_index) in 0..15.

    Returns (None, None) if not an SGR color code we care about.
    """
    if not (seq.startswith("\x1b[") and seq.endswith("m")):
        return None, None
    try:
        code = seq[2:-1]
        parts = code.split(";")
        # We only expect simple single number SGR here from our encoder
        if len(parts) != 1:
            return None, None
        n = int(parts[0])
        # foreground 30-37 -> 0-7, 90-97 -> 8-15
        if 30 <= n <= 37:
            return (n - 30), None
        if 90 <= n <= 97:
            return (n - 90 + 8), None
        # background 40-47 -> 0-7, 100-107 -> 8-15
        if 40 <= n <= 47:
            return None, (n - 40)
        if 100 <= n <= 107:
            return None, (n - 100 + 8)
        # reset
        if n == 0:
            return -1, -1
    except Exception:
        return None, None
    return None, None


def _line_to_cells(encoded_line: str) -> List[Tuple[int | None, int | None, str]]:
    """Convert one encoded half-block line into per-column cells as (fg_idx, bg_idx, ch).

    fg_idx/bg_idx are in 0..15 for 16-colour; may be None if unset; -1 indicates reset.
    """
    cells: List[Tuple[int | None, int | None, str]] = []
    i = 0
    cur_fg: int | None = None
    cur_bg: int | None = None
    while i < len(encoded_line):
        ch = encoded_line[i]
        if ch == "\x1b":
            # parse CSI until final byte
            j = i + 1
            if j < len(encoded_line) and encoded_line[j] == '[':
                j += 1
                while j < len(encoded_line) and not ('@' <= encoded_line[j] <= '~'):
                    j += 1
                if j < len(encoded_line):
                    seq = encoded_line[i:j+1]
                    fg, bg = _parse_sgr_indices(seq)
                    if fg is not None:
                        if fg == -1:
                            cur_fg = None
                            cur_bg = None
                        else:
                            cur_fg = fg
                    if bg is not None:
                        if bg == -1:
                            cur_fg = None
                            cur_bg = None
                        else:
                            cur_bg = bg
                    i = j + 1
                    continue
            # not CSI; skip
            i += 1
            continue
        # printable
        cells.append((cur_fg, cur_bg, ch))
        i += 1
    # Trim any trailing reset cell introduced by encoder's "\x1b[0m" after spaces
    return cells


def _cells_to_line(cells: List[Tuple[int | None, int | None, str]]) -> str:
    """Rebuild an encoded line from cells, emitting minimal SGR transitions and trailing reset."""
    out_parts: List[str] = []
    last_fg: int | None = None
    last_bg: int | None = None

    def sgr16(i: int, bg: bool = False) -> str:
        base = (40 if bg else 30)
        if i >= 8:
            base += 60
            ii = i - 8
        else:
            ii = i
        return f"\x1b[{base + ii}m"

    for fg, bg, ch in cells:
        if fg is not None and fg != last_fg:
            out_parts.append(sgr16(fg, False))
            last_fg = fg
        if bg is not None and bg != last_bg:
            out_parts.append(sgr16(bg, True))
            last_bg = bg
        out_parts.append(ch)
    out_parts.append("\x1b[0m")
    return "".join(out_parts)


def _build_bg_rows_from_tile(tile_path: str, width: int, height: int, frame_index: int, mode: str, palette: str | None, dither: bool, vx: float, vy: float) -> List[str]:
    """Create background rows of width/height by tiling a tile image with horizontal/vertical offsets.

    Offsets advance by vx/vy columns/rows per frame.
    """
    # Encode the tile into half-block lines using existing encoder (string rows)
    tile_lines = encode_halfblock(tile_path, mode=mode, palette=palette, dither=dither)
    tile_cells_rows = [_line_to_cells(ln) for ln in tile_lines]
    if not tile_cells_rows:
        return [" " * width for _ in range(height)]
    tile_h = len(tile_cells_rows)
    tile_w = len(tile_cells_rows[0])  # visible columns
    if tile_w <= 0:
        return [" " * width for _ in range(height)]

    # Compute offsets (allow fractional speeds; convert to integer shift per frame)
    hoff = (int(math.floor(frame_index * float(vx))) % tile_w) if vx != 0 else 0
    voff = (int(math.floor(frame_index * float(vy))) % tile_h) if vy != 0 else 0

    rows_out: List[str] = []
    for y in range(height):
        src_row = tile_cells_rows[(y + voff) % tile_h]
        # rotate horizontally by hoff
        rot = src_row[hoff:] + src_row[:hoff]
        # build exactly width cells by repeating rotated row
        line_cells: List[Tuple[int | None, int | None, str]] = [rot[x % tile_w] for x in range(width)]
        rows_out.append(_cells_to_line(line_cells))
    return rows_out


def _build_bg_rows_from_tile_cells(tile_cells_rows: List[List[Tuple[int | None, int | None, str]]], width: int, height: int, frame_index: int, vx: float, vy: float) -> List[str]:
    """Same as _build_bg_rows_from_tile but uses pre-encoded tile cells for speed."""
    if not tile_cells_rows:
        return [" " * width for _ in range(height)]
    tile_h = len(tile_cells_rows)
    tile_w = len(tile_cells_rows[0]) if tile_h > 0 else 0
    if tile_w <= 0:
        return [" " * width for _ in range(height)]

    hoff = (int(math.floor(frame_index * float(vx))) % tile_w) if vx != 0 else 0
    voff = (int(math.floor(frame_index * float(vy))) % tile_h) if vy != 0 else 0

    rows_out: List[str] = []
    for y in range(height):
        src_row = tile_cells_rows[(y + voff) % tile_h]
        rot = src_row[hoff:] + src_row[:hoff]
        line_cells: List[Tuple[int | None, int | None, str]] = [rot[x % tile_w] for x in range(width)]
        rows_out.append(_cells_to_line(line_cells))
    return rows_out


def _sprite_line_to_segments(line: str, base_x: int, base_y: int, row_index: int) -> List[Dict[str, object]]:
    """Convert one encoded sprite line into sparse overlay segments.

    A cell is considered "visible" if it contains a non-space character OR it
    has a foreground or background colour set. This prevents background layers
    from bleeding through areas encoded as coloured spaces.

    Returns a list of {"x": int, "y": int, "s": str} segments.
    """
    cells = _line_to_cells(line)
    segs: List[Dict[str, object]] = []
    run_start: int | None = None
    run_cells: List[Tuple[int | None, int | None, str]] = []
    for idx, (fg, bg, ch) in enumerate(cells):
        visible = (ch != ' ') or (fg is not None) or (bg is not None)
        if visible:
            if run_start is None:
                run_start = idx
            run_cells.append((fg, bg, ch))
        else:
            if run_start is not None:
                segs.append({
                    "x": base_x + run_start,
                    "y": base_y + row_index,
                    "s": _cells_to_line(run_cells),
                })
                run_start = None
                run_cells = []
    if run_start is not None:
        segs.append({
            "x": base_x + run_start,
            "y": base_y + row_index,
            "s": _cells_to_line(run_cells),
        })
    return segs


def compile_scene(schema_path: str, width: int, height: int, mode: str, out_path: str, palette: str | None, dither: bool) -> None:
    with open(schema_path, "r", encoding="utf-8") as f:
        sc = yaml.safe_load(f)

    layers = sc.get("layers", [])
    sprites = sc.get("sprites", {})
    default_palette = sc.get("palette")  # e.g., "db16"
    frames_out: List[Dict[str, object]] = []

    # Background layers (zero or more): type "tile"
    bg_layers = [l for l in layers if l.get("type") == "tile"]

    # Preload sequences for first sprite only (PoC)
    if not layers:
        raise SystemExit("No layers in scene")
    char_layer = next((l for l in layers if l.get("id") == "character"), layers[0])
    sprite_name = char_layer.get("sprite")
    sp = sprites.get(sprite_name)
    if not sp:
        raise SystemExit(f"Sprite not found: {sprite_name}")

    seq_map: Dict[str, List[str]] = {}
    # Option A: explicit frames mapping
    if "frames" in sp:
        for seq_name, pattern in sp.get("frames", {}).items():
            seq_map[seq_name] = load_sequence_frames(pattern)
    else:
        # Option B: folder + tags (pattern defaults to "{tag}_*.png")
        base_path = sp.get("path")
        tags = sp.get("tags", [])
        patt = sp.get("pattern", "{tag}_*.png")
        if not base_path or not tags:
            raise SystemExit("Sprite requires either 'frames' map or 'path'+'tags'.")
        for tag in tags:
            pattern = os.path.join(base_path, patt.format(tag=tag))
            seq_map[tag] = load_sequence_frames(pattern)

    # Determine sprite dimensions from first frame
    any_seq = next(iter(seq_map.values())) if seq_map else []
    if not any_seq:
        raise SystemExit("No frames found for sprite")
    # Infer half-block cell height
    from PIL import Image
    im0 = Image.open(any_seq[0]).convert("RGBA")
    sprite_w, sprite_h = im0.size
    sprite_h_cells = (sprite_h + 1) // 2
    x_off, y_off = center_offsets(width, height, sprite_w, sprite_h_cells)

    # Timeline assembly
    timeline = char_layer.get("timeline", [])
    bob = char_layer.get("bob", {"amplitude": 0, "period": 1})
    guides = bool(char_layer.get("guides", False))
    amp = int(bob.get("amplitude", 0))
    per = max(1, int(bob.get("period", 1)))

    frame_index = 0
    for item in timeline:
        seq = item.get("seq")
        count = int(item.get("frames", 1))
        files = seq_map.get(seq, [])
        if not files:
            continue
        for i in range(count):
            png = files[i % len(files)]
            # palette precedence: CLI > scene default > none
            pal = palette if palette is not None else (default_palette if default_palette else None)
            encoded_lines = encode_halfblock(png, mode=mode, palette=pal, dither=dither)  # list of strings

            # Build background rows by composing multiple tile layers in order
            # Start with fully transparent/empty cells
            bg_cells_rows: List[List[Tuple[int | None, int | None, str]]] = [[(None, None, ' ') for _ in range(width)] for _ in range(height)]
            for bl in bg_layers:
                if bl.get("type") != "tile":
                    continue
                tile_path = bl.get("image") or bl.get("tile")
                vx = float(bl.get("vx", 0))
                vy = float(bl.get("vy", 0))
                bob_cfg = bl.get("bob", {}) if isinstance(bl.get("bob"), dict) else None
                # Encode tile only once per layer (cache per layer path if needed in future)
                tile_lines = encode_halfblock(tile_path, mode=mode, palette=pal, dither=dither)
                tile_cells_rows = [_line_to_cells(ln) for ln in tile_lines]
                layer_rows = _build_bg_rows_from_tile_cells(tile_cells_rows, width, height, frame_index, vx, vy)
                # Apply optional vertical bob by rotating rows
                if bob_cfg:
                    amp = int(bob_cfg.get("amplitude", 0))
                    per = max(1, int(bob_cfg.get("period", 1)))
                    axis = str(bob_cfg.get("axis", "y")).lower()
                    if amp != 0 and axis == "y":
                        phase = (frame_index % per) / float(per)
                        yshift = int(round(amp * math.sin(2 * math.pi * phase)))
                        if yshift != 0 and height > 0:
                            n = yshift % height
                            layer_rows = layer_rows[n:] + layer_rows[:n]
                # Alpha-blend like: non-space chars overwrite below; treat space as transparent
                for y in range(height):
                    lcells = _line_to_cells(layer_rows[y])
                    base = bg_cells_rows[y]
                    for x in range(min(width, len(lcells))):
                        if lcells[x][2] != ' ':
                            base[x] = lcells[x]
                    bg_cells_rows[y] = base
            bg_rows = [_cells_to_line(row) for row in bg_cells_rows]

            overlays: List[Dict[str, object]] = []
            # Reserve overlay row at top and ticker rows at bottom
            # Note: 64×96 sprite = 48 rows; may exceed 28-row terminal (will clip gracefully)
            reserved_top = 1
            reserved_bottom = 3
            # symmetric bob around baseline
            phase = (frame_index // max(1, per)) % 2
            y_bob = (amp if phase == 0 else -amp)
            yy = min(height - reserved_bottom - sprite_h_cells,
                     max(reserved_top, y_off + y_bob))
            # place lines
            for li, line in enumerate(encoded_lines):
                y_row = yy + li
                if 0 <= y_row < height:
                    overlays.extend(_sprite_line_to_segments(line, x_off, 0, y_row))
            # Optional simple landmark guides (crosshair on head centre)
            if guides:
                guide_y = yy + sprite_h_cells // 2
                if 0 <= guide_y < height:
                    cx = min(width - 1, x_off + sprite_w // 2)
                    if cx < width:
                        overlays.append({"x": cx, "y": guide_y, "s": "+"})
            # ticker layer
            for lyr in layers:
                if lyr.get("type") == "text_scroll":
                    text = lyr.get("text", "") + " "
                    off = frame_index % (len(text) + width)
                    vis = (text + " " * width)[off:off + width]
                    row_cfg = int(lyr.get("row", -2))
                    if row_cfg < 0:
                        row_idx = max(0, height + row_cfg)
                    else:
                        row_idx = min(height - 1, row_cfg)
                    overlays.append({"x": 0, "y": row_idx, "s": vis})

            frames_out.append({"bg_rows": bg_rows, "overlays": overlays})
            frame_index += 1

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"frames": frames_out}, f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", help="scene YAML path")
    ap.add_argument("--width", type=int, default=80)
    ap.add_argument("--height", type=int, default=52)  # Increased for 64×96 sprite (48 rows + overlay + ticker)
    ap.add_argument("--mode", choices=["16", "24"], default="16")
    ap.add_argument("--palette", choices=["none", "db16"], default="db16")
    ap.add_argument("--dither", action="store_true")
    ap.add_argument("--out", default="compiled_scene.json")
    args = ap.parse_args()
    pal = None if args.palette == "none" else args.palette
    compile_scene(args.scene, args.width, args.height, args.mode, args.out, pal, args.dither)


if __name__ == "__main__":
    main()


