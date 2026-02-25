from __future__ import annotations

"""
Generate placeholder 64×96 PNG frames for Anchor Zero (true LucasArts proportions).
Frames: neutral, blink, talk_a, talk_e, talk_o, talk_fv, talk_th

Run:
  python -m Graphics.Animations.tools.generate_anchor_zero_placeholders
Outputs to: assets/anchor_zero/frames/
"""

import os
from typing import Tuple
from PIL import Image, ImageDraw


RGB = Tuple[int, int, int]


# DB16-inspired colours (hex)
HEX = {
    "outline": 0x140C1C,
    "hair": 0x854C30,
    "skin_light": 0xDEEEDE,
    "skin_mid": 0xD2AA99,
    "shadow": 0x8595A1,
    "suit": 0x30346D,
    "suit_shadow": 0x4E4A4E,
    "shirt": 0xDEEEDE,
    "tie": 0xD04648,
}


def hx(x: int) -> RGB:
    return (x >> 16 & 0xFF, x >> 8 & 0xFF, x & 0xFF)


COL = {k: hx(v) for k, v in HEX.items()}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def draw_anchor_base(draw: ImageDraw.ImageDraw) -> None:
    """Draw a 64×96 news anchor bust (true LucasArts proportions).
    
    LucasArts style: flat colour fills with strong outlines, no gradient shadows.
    """
    # Head bounds (scaled proportionally from 48×48)
    head_left, head_top, head_right, head_bottom = 14, 12, 49, 52
    # Face base - single flat colour
    draw.rectangle((head_left, head_top, head_right, head_bottom), fill=COL["skin_light"])
    # Hair band fringe across top
    draw.rectangle((head_left, head_top, head_right, head_top + 5), fill=COL["hair"])
    # Outline for definition
    draw.rectangle((head_left, head_top, head_right, head_bottom), outline=COL["outline"], width=1)

    # Neck (taller for 96px height)
    draw.rectangle((28, 52, 36, 62), fill=COL["skin_mid"])
    draw.rectangle((28, 52, 36, 62), outline=COL["outline"], width=1)
    # Suit shoulders (wider, lower)
    draw.rectangle((10, 62, 54, 72), fill=COL["suit"])
    draw.rectangle((10, 62, 54, 72), outline=COL["outline"], width=1)
    # Torso continuation
    draw.rectangle((10, 72, 54, 90), fill=COL["suit"])
    draw.rectangle((10, 72, 54, 90), outline=COL["outline"], width=1)
    # Shirt and tie (taller)
    draw.rectangle((22, 63, 42, 90), fill=COL["shirt"])
    draw.rectangle((30, 62, 34, 90), fill=COL["tie"])


def draw_eyes(draw: ImageDraw.ImageDraw, closed: bool = False) -> None:
    """Draw eyes scaled for 64×96: larger, more expressive."""
    if closed:
        # Closed eyes line (scaled)
        draw.rectangle((22, 28, 26, 28), fill=(0, 0, 0))  # left
        draw.rectangle((38, 28, 42, 28), fill=(0, 0, 0))  # right
    else:
        # Open eyes as larger blocks
        draw.rectangle((22, 28, 26, 30), fill=(0, 0, 0))  # left
        draw.rectangle((38, 28, 42, 30), fill=(0, 0, 0))  # right


def draw_mouth_viseme(draw: ImageDraw.ImageDraw, viseme: str) -> None:
    """Draw visemes scaled for 64×96 (mouth around y=40)."""
    y0 = 40
    if viseme == "a":  # wide open vertical
        draw.rectangle((26, y0 - 2, 38, y0 + 4), fill=COL["tie"])
    elif viseme == "e":  # horizontal bar
        draw.rectangle((24, y0, 40, y0 + 1), fill=COL["tie"])
    elif viseme == "o":  # rounded-ish
        draw.rectangle((28, y0 - 2, 36, y0 + 2), fill=COL["tie"])
        draw.rectangle((29, y0, 35, y0), fill=COL["shirt"])  # hint of inner
    elif viseme == "fv":  # teeth/lip
        draw.rectangle((24, y0 - 2, 40, y0 - 1), fill=COL["shirt"])  # teeth
        draw.rectangle((24, y0, 40, y0 + 1), fill=COL["tie"])  # lower lip
    elif viseme == "th":  # tongue against teeth
        draw.rectangle((24, y0 - 2, 40, y0 - 1), fill=COL["shirt"])  # teeth
        draw.rectangle((28, y0, 36, y0 + 1), fill=(200, 100, 100))  # tongue tint
    elif viseme == "small":
        draw.rectangle((28, y0, 36, y0), fill=COL["tie"])


def make_frame(name: str, eyes_closed: bool, viseme: str | None) -> None:
    im = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_anchor_base(d)
    draw_eyes(d, closed=eyes_closed)
    if viseme:
        draw_mouth_viseme(d, viseme)
    out_dir = os.path.join("assets", "anchor_zero", "frames")
    ensure_dir(out_dir)
    im.save(os.path.join(out_dir, name), "PNG")


def make_bg_tile() -> None:
    """Create a simple 16x16 parallaxable background tile."""
    bg_dir = os.path.join("assets", "anchor_zero", "bg")
    ensure_dir(bg_dir)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Checker with horizontal band for motion sense
    for y in range(16):
        for x in range(16):
            if ((x // 4) + (y // 4)) % 2 == 0:
                d.point((x, y), fill=COL["suit_shadow"] + (255,))
            else:
                d.point((x, y), fill=COL["suit"] + (255,))
    # Horizontal lighter band
    d.rectangle((0, 6, 15, 8), fill=COL["suit"] + (255,))
    im.save(os.path.join(bg_dir, "tile_16x16.png"), "PNG")


def make_mid_tile() -> None:
    """Create a 16x16 midground tile with softer contrast for parallax depth."""
    bg_dir = os.path.join("assets", "anchor_zero", "bg")
    ensure_dir(bg_dir)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Diagonal stripes with lower contrast and semi-transparency
    for y in range(16):
        for x in range(16):
            if ((x + y) % 4) < 2:
                d.point((x, y), fill=COL["suit_shadow"] + (180,))
            else:
                d.point((x, y), fill=COL["suit"] + (160,))
    im.save(os.path.join(bg_dir, "mid_tile_16x16.png"), "PNG")


def main() -> None:
    make_frame("anchor_neutral_01.png", eyes_closed=False, viseme=None)
    make_frame("anchor_blink_01.png", eyes_closed=True, viseme=None)
    make_frame("anchor_talk_a_01.png", eyes_closed=False, viseme="a")
    make_frame("anchor_talk_e_01.png", eyes_closed=False, viseme="e")
    make_frame("anchor_talk_o_01.png", eyes_closed=False, viseme="o")
    make_frame("anchor_talk_fv_01.png", eyes_closed=False, viseme="fv")
    make_frame("anchor_talk_th_01.png", eyes_closed=False, viseme="th")
    make_bg_tile()
    make_mid_tile()
    print("Generated placeholder frames in assets/anchor_zero/frames/")


if __name__ == "__main__":
    main()


