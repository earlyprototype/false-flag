"""
Headless renderer for the l_shape_layout_demo_v3 dialogue animation.

Reproduces the terminal animation on a virtual character grid and
rasterises each frame to a Pillow Image, then saves the lot as an
animated GIF suitable for embedding in a README.

Usage:
    python scripts/render_animation_gif.py [--output dialogue_demo.gif]
                                           [--cols 120] [--rows 30]
                                           [--fps 10]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import random
import textwrap
from typing import List, Tuple, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PIL import Image, ImageDraw, ImageFont
from Graphics.Animations.tools.encode_halfblock import encode_halfblock
from Graphics.Animations.tools.palette_db16 import TERMINAL_16

# ---------------------------------------------------------------------------
# Terminal colour constants
# ---------------------------------------------------------------------------
BG_DEFAULT: Tuple[int, int, int] = (0xFF, 0xFF, 0xFF)
FG_DEFAULT: Tuple[int, int, int] = (0x1A, 0x1A, 0x1A)

TERM16 = list(TERMINAL_16)

RICH_COLOUR_NAMES = {
    "bright_blue": (0x00, 0x00, 0xFF),
    "white": (0x60, 0x60, 0x60),
    "bright_white": (0xFF, 0xFF, 0xFF),
    "red": (0xFF, 0x00, 0x00),
    "yellow": (0xFF, 0xFF, 0x00),
    "green": (0x00, 0xFF, 0x00),
    "cyan": (0x00, 0xFF, 0xFF),
    "bold_white": (0xFF, 0xFF, 0xFF),
}

# ---------------------------------------------------------------------------
# Character cell -- what lives in each grid position
# ---------------------------------------------------------------------------
class Cell:
    __slots__ = ("char", "fg", "bg")

    def __init__(
        self,
        char: str = " ",
        fg: Tuple[int, int, int] = FG_DEFAULT,
        bg: Tuple[int, int, int] = BG_DEFAULT,
    ):
        self.char = char
        self.fg = fg
        self.bg = bg

# ---------------------------------------------------------------------------
# Virtual character-grid framebuffer
# ---------------------------------------------------------------------------
class CharGrid:
    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.cells: List[List[Cell]] = []
        self.clear()

    def clear(self):
        self.cells = [
            [Cell() for _ in range(self.cols)] for _ in range(self.rows)
        ]

    def put(self, col: int, row: int, char: str,
            fg: Tuple[int, int, int] = FG_DEFAULT,
            bg: Tuple[int, int, int] = BG_DEFAULT):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            c = self.cells[row][col]
            c.char = char
            c.fg = fg
            c.bg = bg

    def put_str(self, col: int, row: int, text: str,
                fg: Tuple[int, int, int] = FG_DEFAULT,
                bg: Tuple[int, int, int] = BG_DEFAULT):
        for i, ch in enumerate(text):
            self.put(col + i, row, ch, fg, bg)

# ---------------------------------------------------------------------------
# ANSI SGR parser -- decode encoded halfblock strings into cell data
# ---------------------------------------------------------------------------
_SGR_RE = re.compile(r"\x1b\[([\d;]*)m")

def _sgr_to_colour(code: int, bright_offset: bool = False) -> Optional[Tuple[int, int, int]]:
    """Map an SGR colour code to an RGB tuple using the terminal-16 palette."""
    if 30 <= code <= 37:
        return TERM16[code - 30]
    if 90 <= code <= 97:
        return TERM16[code - 90 + 8]
    if 40 <= code <= 47:
        return TERM16[code - 40]
    if 100 <= code <= 107:
        return TERM16[code - 100 + 8]
    return None


def blit_ansi_line(grid: CharGrid, col: int, row: int, ansi_line: str):
    """Parse one ANSI-encoded halfblock line and write cells into the grid."""
    fg = FG_DEFAULT
    bg = BG_DEFAULT
    x = col
    i = 0
    while i < len(ansi_line):
        if ansi_line[i] == "\x1b":
            m = _SGR_RE.match(ansi_line, i)
            if m:
                params = m.group(1)
                if params == "" or params == "0":
                    fg = FG_DEFAULT
                    bg = BG_DEFAULT
                else:
                    codes = [int(p) for p in params.split(";") if p]
                    for c in codes:
                        if 30 <= c <= 37 or 90 <= c <= 97:
                            rgb = _sgr_to_colour(c)
                            if rgb:
                                fg = rgb
                        elif 40 <= c <= 47 or 100 <= c <= 107:
                            rgb = _sgr_to_colour(c)
                            if rgb:
                                bg = rgb
                i = m.end()
                continue
        ch = ansi_line[i]
        grid.put(x, row, ch, fg, bg)
        x += 1
        i += 1

# ---------------------------------------------------------------------------
# Sprite loading (mirrors l_shape_layout_demo_v3.py exactly)
# ---------------------------------------------------------------------------
PLAYER_SPRITE_PATH = os.path.join(project_root, "assets", "anchor_small")
PLAYER_FRAMES_CFG = {
    "neutral": "anchor_neutral_01.png",
    "blink": "anchor_blink_01.png",
    "talk": [
        "anchor_talk_a_01.png",
        "anchor_talk_e_01.png",
        "anchor_talk_o_01.png",
    ],
}

DIPLOMAT_SPRITE_PATH = os.path.join(project_root, "assets", "diplomat_female_senior")
DIPLOMAT_FRAMES_CFG = {
    "neutral": "diplomat_female_senior_neutral_01.png",
    "blink": "diplomat_female_senior_blink_01.png",
    "talk": [
        "diplomat_female_senior_talk_a_01.png",
        "diplomat_female_senior_talk_e_01.png",
        "diplomat_female_senior_talk_o_01.png",
    ],
}

CONVERSATION_SCRIPT = [
    {"speaker": "diplomat", "text": "Prime Minister. Your naval blockade is an unacceptable act of aggression. We demand you stand down your fleet."},
    {"speaker": "player", "text": "This is not a blockade. It is a defensive quarantine in response to your unannounced submarine movements. Stand down your assets."},
    {"speaker": "diplomat", "text": "These are routine patrols in international waters. Your response is disproportionate and will have severe consequences."},
    {"speaker": "player", "text": "Our intelligence on the Suwalki Gap suggests otherwise. The quarantine holds. End of discussion."},
]


def load_sprites(sprite_path: str, cfg: dict) -> dict:
    encoded = {"idle": [], "talk": []}
    neutral = encode_halfblock(os.path.join(sprite_path, cfg["neutral"]),
                               mode="16", palette="db16")
    blink = encode_halfblock(os.path.join(sprite_path, cfg["blink"]),
                             mode="16", palette="db16")
    for _ in range(60):
        encoded["idle"].append(neutral)
    for _ in range(4):
        encoded["idle"].append(blink)
    for fname in cfg["talk"]:
        frames = encode_halfblock(os.path.join(sprite_path, fname),
                                  mode="16", palette="db16")
        for _ in range(8):
            encoded["talk"].append(frames)
    return encoded

# ---------------------------------------------------------------------------
# Speech bubble drawing (box-drawing on the grid)
# ---------------------------------------------------------------------------
BOX_TL = "\u250c"
BOX_TR = "\u2510"
BOX_BL = "\u2514"
BOX_BR = "\u2518"
BOX_H  = "\u2500"
BOX_V  = "\u2502"


def draw_box(grid: CharGrid, x: int, y: int, w: int, h: int,
             title: str = "", border_colour: Tuple[int, int, int] = FG_DEFAULT):
    """Draw a box-drawing rectangle with optional centred title."""
    fg = border_colour
    bg = BG_DEFAULT

    grid.put(x, y, BOX_TL, fg, bg)
    grid.put(x + w - 1, y, BOX_TR, fg, bg)
    grid.put(x, y + h - 1, BOX_BL, fg, bg)
    grid.put(x + w - 1, y + h - 1, BOX_BR, fg, bg)

    for cx in range(x + 1, x + w - 1):
        grid.put(cx, y, BOX_H, fg, bg)
        grid.put(cx, y + h - 1, BOX_H, fg, bg)
    for cy in range(y + 1, y + h - 1):
        grid.put(x, cy, BOX_V, fg, bg)
        grid.put(x + w - 1, cy, BOX_V, fg, bg)

    if title:
        label = f" {title} "
        tx = x + (w - len(label)) // 2
        for i, ch in enumerate(label):
            grid.put(tx + i, y, ch, FG_DEFAULT, bg)


def wrap_and_fill(text: str, width: int, height: int) -> List[str]:
    """Word-wrap text to width, pad/truncate to exactly height lines."""
    clean = re.sub(r"\[/?[a-z_ ]*\]", "", text)
    lines = textwrap.wrap(clean, width=width) if clean else []
    while len(lines) < height:
        lines.append("")
    return lines[:height]

# ---------------------------------------------------------------------------
# Rasteriser -- convert CharGrid to a Pillow Image
# ---------------------------------------------------------------------------
CELL_W = 8
CELL_H = 16
HALF_BLOCK_CHARS = {"\u2580", "\u2584", "\u2588"}


def _try_load_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "consolas.ttf", "Consolas.ttf",
        "consolab.ttf",
        "cour.ttf", "Cour.ttf",
        "lucon.ttf",
        "DejaVuSansMono.ttf",
        "LiberationMono-Regular.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=14)
        except (OSError, IOError):
            pass

    win_fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name in candidates:
        path = os.path.join(win_fonts, name)
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size=14)
            except (OSError, IOError):
                pass

    return ImageFont.load_default()


def rasterise(grid: CharGrid, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> Image.Image:
    """Convert a CharGrid into an RGBA Pillow Image."""
    img = Image.new("RGB", (grid.cols * CELL_W, grid.rows * CELL_H), BG_DEFAULT)
    draw = ImageDraw.Draw(img)

    for row_idx in range(grid.rows):
        for col_idx in range(grid.cols):
            cell = grid.cells[row_idx][col_idx]
            px = col_idx * CELL_W
            py = row_idx * CELL_H

            draw.rectangle([px, py, px + CELL_W - 1, py + CELL_H - 1],
                           fill=cell.bg)

            if cell.char in HALF_BLOCK_CHARS:
                if cell.char == "\u2580":
                    draw.rectangle([px, py, px + CELL_W - 1, py + CELL_H // 2 - 1],
                                   fill=cell.fg)
                elif cell.char == "\u2584":
                    draw.rectangle([px, py + CELL_H // 2, px + CELL_W - 1, py + CELL_H - 1],
                                   fill=cell.fg)
                elif cell.char == "\u2588":
                    draw.rectangle([px, py, px + CELL_W - 1, py + CELL_H - 1],
                                   fill=cell.fg)
            elif cell.char != " ":
                draw.text((px + 1, py), cell.char, fill=cell.fg, font=font)

    return img

# ---------------------------------------------------------------------------
# Frame generation -- replicate the demo's animation logic
# ---------------------------------------------------------------------------
def generate_frames(cols: int, rows: int, fps: int) -> List[Image.Image]:
    print("Loading sprites...")
    player_frames = load_sprites(PLAYER_SPRITE_PATH, PLAYER_FRAMES_CFG)
    diplomat_frames = load_sprites(DIPLOMAT_SPRITE_PATH, DIPLOMAT_FRAMES_CFG)

    font = _try_load_font()
    grid = CharGrid(cols, rows)

    SPRITE_WIDTH = 32
    diplomat_sprite_x = 0
    player_sprite_x = cols - SPRITE_WIDTH

    frames: List[Image.Image] = []
    total_turns = len(CONVERSATION_SCRIPT)
    turn_duration = fps * 7

    random.seed(42)

    for script_turn in range(total_turns):
        turn_info = CONVERSATION_SCRIPT[script_turn]
        speaker = turn_info["speaker"]
        full_text = turn_info["text"]

        if speaker == "diplomat":
            title = "President | Russian Federation"
            border_rgb = RICH_COLOUR_NAMES["bright_blue"]
            bubble_x = diplomat_sprite_x + SPRITE_WIDTH + 2
            bubble_width = cols - bubble_x
        else:
            title = "You (Prime Minister)"
            border_rgb = RICH_COLOUR_NAMES["white"]
            bubble_x = diplomat_sprite_x
            bubble_width = player_sprite_x - 2

        bubble_y = 3
        inner_w = bubble_width - 4
        clean_text_for_wrap = re.sub(r"\[/?[a-z_ ]*\]", "", full_text)
        wrapped = textwrap.wrap(clean_text_for_wrap, width=inner_w) if clean_text_for_wrap else [""]
        bubble_height = len(wrapped) + 2

        text_reveal = 0

        for frame_tick in range(turn_duration):
            grid.clear()

            # -- sprites --
            p_state = "talk" if speaker == "player" else "idle"
            d_state = "talk" if speaker == "diplomat" else "idle"

            if p_state == "talk":
                p_frame = random.choice(player_frames["talk"])
            else:
                idx = (frame_tick * 2) % len(player_frames["idle"])
                p_frame = player_frames["idle"][idx]

            if d_state == "talk":
                d_frame = random.choice(diplomat_frames["talk"])
            else:
                idx = (frame_tick * 2) % len(diplomat_frames["idle"])
                d_frame = diplomat_frames["idle"][idx]

            if speaker == "player":
                # diplomat ducked (lower, cropped), player full height
                for i, line in enumerate(d_frame[:12]):
                    blit_ansi_line(grid, diplomat_sprite_x, 10 + i, line)
                for i, line in enumerate(p_frame):
                    blit_ansi_line(grid, player_sprite_x, 1 + i, line)
            else:
                for i, line in enumerate(d_frame):
                    blit_ansi_line(grid, diplomat_sprite_x, 1 + i, line)
                for i, line in enumerate(p_frame[:12]):
                    blit_ansi_line(grid, player_sprite_x, 10 + i, line)

            # -- speech bubble border --
            draw_box(grid, bubble_x, bubble_y, bubble_width, bubble_height,
                     title, border_rgb)

            # -- typewriter text reveal --
            clean_text = re.sub(r"\[/?[a-z_ ]*\]", "", full_text)
            chars_to_show = min(text_reveal, len(clean_text))
            revealed = clean_text[:chars_to_show]
            visible_lines = wrap_and_fill(revealed, inner_w, bubble_height - 2)

            text_fg = FG_DEFAULT
            for li, line_text in enumerate(visible_lines):
                for ci, ch in enumerate(line_text):
                    grid.put(bubble_x + 2 + ci, bubble_y + 1 + li, ch,
                             text_fg, BG_DEFAULT)

            if frame_tick % 2 == 0:
                text_reveal += 3

            frames.append(rasterise(grid, font))

            pct = ((script_turn * turn_duration + frame_tick + 1)
                   / (total_turns * turn_duration) * 100)
            print(f"\rRendering: {pct:5.1f}%  ({len(frames)} frames)", end="")

    print()
    return frames

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Render dialogue animation to GIF")
    ap.add_argument("--output", default="dialogue_demo.gif")
    ap.add_argument("--cols", type=int, default=120)
    ap.add_argument("--rows", type=int, default=30)
    ap.add_argument("--fps", type=int, default=10,
                    help="Frame rate (lower = fewer frames, smaller file)")
    args = ap.parse_args()

    frames = generate_frames(args.cols, args.rows, args.fps)

    if not frames:
        print("No frames generated.")
        return

    duration_ms = 1000 // args.fps
    out = args.output
    print(f"Saving {len(frames)} frames to {out} ({duration_ms}ms/frame)...")
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    size_kb = os.path.getsize(out) / 1024
    print(f"Done. {out} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
