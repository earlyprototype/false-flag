"""
Render a cutscene snapshot PNG from the pixel-art sprite assets.

Composites: tiled background, two characters, title bar, news ticker,
and dialogue text into a showcase image.

Usage:
    python scripts/render_cutscene_snapshot.py [--out cutscene_snapshot.png] [--scale 6]
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

DB16 = {
    "black":       (20,  12,  28),
    "dark_purple":  (68,  36,  52),
    "dark_blue":    (48,  52,  109),
    "dark_grey":    (78,  74,  78),
    "brown":        (133, 76,  48),
    "dark_green":   (52,  101, 36),
    "red":          (208, 70,  72),
    "mid_grey":     (117, 113, 97),
    "blue":         (89,  125, 206),
    "orange":       (210, 125, 44),
    "light_grey":   (133, 149, 161),
    "cyan":         (109, 194, 202),
    "skin":         (218, 212, 94),
    "green":        (109, 170, 44),
    "pink":         (210, 170, 153),
    "white":        (222, 238, 214),
}

GLYPH_5X7 = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'B': ["11110","10001","10001","11110","10001","10001","11110"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'D': ["11110","10001","10001","10001","10001","10001","11110"],
    'E': ["11111","10000","10000","11110","10000","10000","11111"],
    'F': ["11111","10000","10000","11110","10000","10000","10000"],
    'G': ["01110","10001","10000","10111","10001","10001","01110"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
    'I': ["11111","00100","00100","00100","00100","00100","11111"],
    'J': ["00111","00010","00010","00010","00010","10010","01100"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'Q': ["01110","10001","10001","10001","10101","10010","01101"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'S': ["01110","10001","10000","01110","00001","10001","01110"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'V': ["10001","10001","10001","10001","10001","01010","00100"],
    'W': ["10001","10001","10001","10101","10101","10101","01010"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'Z': ["11111","00001","00010","00100","01000","10000","11111"],
    '0': ["01110","10011","10101","10101","10101","11001","01110"],
    '1': ["00100","01100","00100","00100","00100","00100","11111"],
    '2': ["01110","10001","00001","00110","01000","10000","11111"],
    '3': ["01110","10001","00001","00110","00001","10001","01110"],
    '4': ["00010","00110","01010","10010","11111","00010","00010"],
    '5': ["11111","10000","11110","00001","00001","10001","01110"],
    '6': ["01110","10001","10000","11110","10001","10001","01110"],
    '7': ["11111","00001","00010","00100","01000","01000","01000"],
    '8': ["01110","10001","10001","01110","10001","10001","01110"],
    '9': ["01110","10001","10001","01111","00001","10001","01110"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    '.': ["00000","00000","00000","00000","00000","00000","00100"],
    ',': ["00000","00000","00000","00000","00000","00100","01000"],
    '!': ["00100","00100","00100","00100","00100","00000","00100"],
    '?': ["01110","10001","00001","00110","00100","00000","00100"],
    '-': ["00000","00000","00000","11111","00000","00000","00000"],
    ':': ["00000","00100","00000","00000","00000","00100","00000"],
    '|': ["00100","00100","00100","00100","00100","00100","00100"],
    '[': ["01110","01000","01000","01000","01000","01000","01110"],
    ']': ["01110","00010","00010","00010","00010","00010","01110"],
    '/': ["00001","00010","00010","00100","01000","01000","10000"],
    "'": ["00100","00100","00000","00000","00000","00000","00000"],
    '"': ["01010","01010","00000","00000","00000","00000","00000"],
}


def draw_text(img, text, x, y, colour, scale=1):
    """Draw text onto an image using the 5x7 bitmap font."""
    draw = ImageDraw.Draw(img)
    cx = x
    for ch in text.upper():
        glyph = GLYPH_5X7.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == '1':
                    px = cx + col_i * scale
                    py = y + row_i * scale
                    if scale == 1:
                        draw.point((px, py), fill=colour)
                    else:
                        draw.rectangle(
                            [px, py, px + scale - 1, py + scale - 1],
                            fill=colour,
                        )
        cx += 6 * scale


def tile_background(canvas, tile_path, region=None):
    """Tile a 16x16 image across the canvas (or a sub-region)."""
    tile = Image.open(tile_path).convert("RGBA")
    tw, th = tile.size
    if region:
        x0, y0, x1, y1 = region
    else:
        x0, y0 = 0, 0
        x1, y1 = canvas.size
    for ty in range(y0, y1, th):
        for tx in range(x0, x1, tw):
            canvas.paste(tile, (tx, ty), tile)


def text_width(text):
    """Width in native pixels for a string rendered in the 5x7 font."""
    return len(text) * 6 - 1


def draw_text_box(canvas, lines, x, y, fg, bg_colour=None, padding=2):
    """Draw one or more lines with an optional semi-transparent backdrop."""
    draw = ImageDraw.Draw(canvas)
    line_h = 8
    max_w = max(text_width(l) for l in lines)
    if bg_colour is not None:
        draw.rectangle(
            [x - padding, y - padding,
             x + max_w + padding, y + len(lines) * line_h + padding - 1],
            fill=bg_colour,
        )
    for i, line in enumerate(lines):
        draw_text(canvas, line, x, y + i * line_h, fg)


def render_cutscene(out_path: Path, scale: int = 6):
    """
    Faithful render of two_person_scene.yaml:
      - Tiled news-studio background + midground
      - Diplomat (talking) on the left   -- anchor_small talk_a
      - Player  (neutral) on the right   -- anchor_small neutral
      - Title: "LIVE | SECURE DIPLOMATIC CHANNEL"
      - Diplomat dialogue + Player dialogue
    """
    native_w, native_h = 224, 112
    canvas = Image.new("RGBA", (native_w, native_h), DB16["black"])

    tile_background(
        canvas,
        ROOT / "assets" / "news_studio_bg" / "tile_16x16.png",
    )
    tile_background(
        canvas,
        ROOT / "assets" / "news_studio_bg" / "mid_tile_16x16.png",
        region=(0, 40, native_w, 72),
    )

    sprites = ROOT / "assets" / "anchor_small"

    diplomat = Image.open(sprites / "anchor_talk_a_01.png").convert("RGBA")
    canvas.paste(diplomat, (8, 20), diplomat)

    player = Image.open(sprites / "anchor_neutral_01.png").convert("RGBA")
    canvas.paste(player, (180, 20), player)

    draw = ImageDraw.Draw(canvas)

    draw.rectangle([0, 0, native_w, 10], fill=DB16["dark_purple"])
    draw_text(canvas, "LIVE", 4, 2, DB16["red"])
    draw_text(canvas, "| SECURE DIPLOMATIC CHANNEL", 30, 2, DB16["white"])

    draw_text_box(
        canvas,
        ["MR. PRIME MINISTER,", "WE MUST DE-ESCALATE."],
        x=44, y=24,
        fg=DB16["cyan"],
        bg_colour=(*DB16["black"], 180),
    )

    draw_text_box(
        canvas,
        ["OUR MOVEMENTS ARE", "PURELY DEFENSIVE."],
        x=44, y=52,
        fg=DB16["green"],
        bg_colour=(*DB16["black"], 180),
    )

    draw.rectangle([0, native_h - 12, native_w, native_h], fill=DB16["red"])
    draw_text(
        canvas,
        "SUB ACTIVITY IS THE PROVOCATION",
        4, native_h - 10,
        DB16["white"],
    )

    final = canvas.resize(
        (native_w * scale, native_h * scale),
        Image.Resampling.NEAREST,
    )

    final.save(out_path, "PNG")
    print(f"Saved cutscene snapshot: {out_path}  ({final.size[0]}x{final.size[1]})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a cutscene snapshot PNG")
    parser.add_argument(
        "--out", default="cutscene_snapshot.png",
        help="Output file path (default: cutscene_snapshot.png)",
    )
    parser.add_argument(
        "--scale", type=int, default=6,
        help="Nearest-neighbour upscale factor (default: 6)",
    )
    args = parser.parse_args()
    render_cutscene(Path(args.out), args.scale)
