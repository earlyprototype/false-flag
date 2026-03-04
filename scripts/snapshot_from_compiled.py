"""
Render a true-to-terminal PNG snapshot from a compiled scene JSON,
or from the l_shape_layout_demo_v3 dialogue format.

Decodes ANSI half-block output back into pixels using the terminal
16-colour palette, then upscales with nearest-neighbour.

Usage:
    # From compiled scene JSON (single character + bg + ticker)
    python scripts/snapshot_from_compiled.py compiled.json --frame 40 --scale 8

    # L-shape dialogue mode (two characters + speech bubble)
    python scripts/snapshot_from_compiled.py --dialogue --frame 0 --scale 4
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Graphics.Animations.tools.encode_halfblock import encode_halfblock

TERMINAL_16_RGB = [
    (0x00, 0x00, 0x00),  # 0 black
    (0x80, 0x00, 0x00),  # 1 red
    (0x00, 0x80, 0x00),  # 2 green
    (0x80, 0x80, 0x00),  # 3 yellow
    (0x00, 0x00, 0x80),  # 4 blue
    (0x80, 0x00, 0x80),  # 5 magenta
    (0x00, 0x80, 0x80),  # 6 cyan
    (0xC0, 0xC0, 0xC0),  # 7 white (light grey)
    (0x80, 0x80, 0x80),  # 8 bright black (grey)
    (0xFF, 0x00, 0x00),  # 9 bright red
    (0x00, 0xFF, 0x00),  # 10 bright green
    (0xFF, 0xFF, 0x00),  # 11 bright yellow
    (0x00, 0x00, 0xFF),  # 12 bright blue
    (0xFF, 0x00, 0xFF),  # 13 bright magenta
    (0x00, 0xFF, 0xFF),  # 14 bright cyan
    (0xFF, 0xFF, 0xFF),  # 15 bright white
]

BG_COLOUR = (0x14, 0x0C, 0x1C)

Cell = Tuple[Optional[int], Optional[int], str]


def parse_sgr_index(seq: str) -> Tuple[Optional[int], Optional[int]]:
    if not (seq.startswith("\x1b[") and seq.endswith("m")):
        return None, None
    try:
        n = int(seq[2:-1])
    except ValueError:
        return None, None
    if 30 <= n <= 37:
        return (n - 30), None
    if 90 <= n <= 97:
        return (n - 90 + 8), None
    if 40 <= n <= 47:
        return None, (n - 40)
    if 100 <= n <= 107:
        return None, (n - 100 + 8)
    if n == 0:
        return -1, -1
    return None, None


def line_to_cells(s: str) -> List[Cell]:
    cells: List[Cell] = []
    i = 0
    fg: Optional[int] = None
    bg: Optional[int] = None
    while i < len(s):
        ch = s[i]
        if ch == "\x1b":
            j = i + 1
            if j < len(s) and s[j] == "[":
                j += 1
                while j < len(s) and not ("@" <= s[j] <= "~"):
                    j += 1
                if j < len(s):
                    seq = s[i : j + 1]
                    fgi, bgi = parse_sgr_index(seq)
                    if fgi is not None:
                        fg = None if fgi == -1 else fgi
                    if bgi is not None:
                        bg = None if bgi == -1 else bgi
                    if fgi == -1:
                        bg = None
                    if bgi == -1:
                        fg = None
                    i = j + 1
                    continue
            i += 1
            continue
        cells.append((fg, bg, ch))
        i += 1
    return cells


def cells_to_pixels(
    cells_rows: List[List[Cell]],
    palette: List[Tuple[int, int, int]],
    bg: Tuple[int, int, int],
) -> Image.Image:
    height_cells = len(cells_rows)
    width_cells = max((len(r) for r in cells_rows), default=0)
    img = Image.new("RGBA", (width_cells, height_cells * 2), (*bg, 255))

    for y, row in enumerate(cells_rows):
        for x, (fg_idx, bg_idx, ch) in enumerate(row):
            fg_col = palette[fg_idx] if fg_idx is not None else bg
            bg_col = palette[bg_idx] if bg_idx is not None else bg

            if ch == "\u2580":
                img.putpixel((x, y * 2), (*fg_col, 255))
                img.putpixel((x, y * 2 + 1), (*bg_col, 255))
            elif ch == "\u2584":
                img.putpixel((x, y * 2), (*bg_col, 255))
                img.putpixel((x, y * 2 + 1), (*fg_col, 255))
            elif ch == "\u2588":
                img.putpixel((x, y * 2), (*fg_col, 255))
                img.putpixel((x, y * 2 + 1), (*fg_col, 255))
            elif ch != " ":
                img.putpixel((x, y * 2), (*fg_col, 255))
                img.putpixel((x, y * 2 + 1), (*bg_col, 255))
            else:
                img.putpixel((x, y * 2), (*bg_col, 255))
                img.putpixel((x, y * 2 + 1), (*bg_col, 255))

    return img


def encode_sprite(sprite_path: str) -> Image.Image:
    """Encode a sprite PNG via the half-block pipeline and return as a pixel image."""
    lines = encode_halfblock(sprite_path, mode="16", palette="db16")
    cells_rows = [line_to_cells(l) for l in lines]
    return cells_to_pixels(cells_rows, TERMINAL_16_RGB, (0, 0, 0))


def render_dialogue_snapshot(out_path: str, scale: int, frame_idx: int):
    """
    Render a snapshot matching the l_shape_layout_demo_v3 layout:
    diplomat (left, talking) + player (right, ducked) + speech bubble.
    """
    TERM_W, TERM_H = 120, 30
    SPRITE_W_PX = 32

    diplomat_sprite = encode_sprite(
        "assets/diplomat_female_senior/diplomat_female_senior_talk_a_01.png"
    )
    player_sprite = encode_sprite(
        "assets/anchor_small/anchor_neutral_01.png"
    )

    canvas = Image.new("RGBA", (TERM_W, TERM_H * 2), (*BG_COLOUR, 255))

    diplomat_x = 0
    diplomat_y = 1 * 2
    canvas.paste(diplomat_sprite, (diplomat_x, diplomat_y), diplomat_sprite)

    player_x = TERM_W - SPRITE_W_PX
    player_y = 10 * 2
    player_cropped = player_sprite.crop((0, 0, player_sprite.width, min(24, player_sprite.height)))
    canvas.paste(player_cropped, (player_x, player_y), player_cropped)

    draw = ImageDraw.Draw(canvas)

    bubble_x = SPRITE_W_PX + 2
    bubble_y = 3 * 2
    bubble_w = TERM_W - bubble_x
    bubble_h = 10 * 2

    border_col = (0x55, 0x55, 0xFF, 255)
    draw.rectangle(
        [bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h],
        outline=border_col, width=1,
    )

    title = "President | United States"
    title_x = bubble_x + 2
    title_y = bubble_y + 1
    for i, ch in enumerate(title):
        if title_x + i < TERM_W:
            draw.point((title_x + i, title_y), fill=(255, 255, 255, 255))

    text = "Prime Minister. Your naval blockade is an unacceptable act of aggression. We demand you stand down your fleet."
    text_col = (0xC0, 0xC0, 0xC0, 255)
    text_x = bubble_x + 2
    text_y = bubble_y + 4
    col = 0
    for ch in text:
        px = text_x + col
        py = text_y
        if col >= bubble_w - 4:
            col = 0
            text_y += 2
            py = text_y
            px = text_x
        if px < TERM_W and py < bubble_y + bubble_h - 2:
            draw.point((px, py), fill=text_col)
        col += 1

    final = canvas.resize(
        (canvas.width * scale, canvas.height * scale),
        Image.Resampling.NEAREST,
    )
    final.save(out_path, "PNG")
    print(f"Saved dialogue snapshot: {out_path} ({final.width}x{final.height})")


def render_compiled_snapshot(compiled_path: str, out_path: str, scale: int, frame_idx: int):
    """Render from a compiled scene JSON."""
    with open(compiled_path, "r", encoding="utf-8") as f:
        scene = json.load(f)

    frames = scene["frames"]
    fi = min(frame_idx, len(frames) - 1)
    frame = frames[fi]

    bg_rows = frame.get("bg_rows", [])
    overlays = frame.get("overlays", [])
    width = max((len(line_to_cells(r)) for r in bg_rows), default=80)
    height = len(bg_rows) or 28

    grid: List[List[Cell]] = []
    for y in range(height):
        if y < len(bg_rows):
            row_cells = line_to_cells(bg_rows[y])
            while len(row_cells) < width:
                row_cells.append((None, None, " "))
            grid.append(row_cells[:width])
        else:
            grid.append([(None, None, " ")] * width)

    for ov in overlays:
        ox = int(ov.get("x", 0))
        oy = int(ov.get("y", 0))
        s = str(ov.get("s", ""))
        if 0 <= oy < height and s:
            ov_cells = line_to_cells(s)
            for j, cell in enumerate(ov_cells):
                cx = ox + j
                if 0 <= cx < width:
                    grid[oy][cx] = cell

    img = cells_to_pixels(grid, TERMINAL_16_RGB, BG_COLOUR)
    final = img.resize(
        (img.width * scale, img.height * scale),
        Image.Resampling.NEAREST,
    )
    final.save(out_path, "PNG")
    print(f"Saved frame {fi}/{len(frames)-1}: {out_path} ({final.width}x{final.height})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("compiled", nargs="?", help="Compiled scene JSON path")
    parser.add_argument("--dialogue", action="store_true", help="Render l_shape dialogue layout")
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--scale", type=int, default=8)
    parser.add_argument("--out", default="cutscene_snapshot.png")
    args = parser.parse_args()

    if args.dialogue:
        render_dialogue_snapshot(args.out, args.scale, args.frame)
    elif args.compiled:
        render_compiled_snapshot(args.compiled, args.out, args.scale, args.frame)
    else:
        parser.error("Provide a compiled JSON path or use --dialogue")


if __name__ == "__main__":
    main()
