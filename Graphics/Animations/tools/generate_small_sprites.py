
import os
from typing import Tuple
from PIL import Image, ImageDraw

# This script is a modified version of generate_anchor_zero_placeholders.py
# It creates smaller 32x48 sprites.

# --- Color Palette (Unchanged) ---
HEX = {
    "outline": 0x140C1C, "hair": 0x854C30, "skin_light": 0xDEEEDE, "skin_mid": 0xD2AA99,
    "shadow": 0x8595A1, "suit": 0x30346D, "suit_shadow": 0x4E4A4E, "shirt": 0xDEEEDE, "tie": 0xD04648,
}
def hx(x: int) -> Tuple[int, int, int]:
    return (x >> 16 & 0xFF, x >> 8 & 0xFF, x & 0xFF)
COL = {k: hx(v) for k, v in HEX.items()}

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# --- Drawing Functions (Modified for 32x48) ---
def draw_anchor_base(draw: ImageDraw.ImageDraw) -> None:
    """Draw a 32x48 news anchor bust."""
    # Head bounds (scaled to 32x48)
    head_left, head_top, head_right, head_bottom = 7, 6, 24, 26
    draw.rectangle((head_left, head_top, head_right, head_bottom), fill=COL["skin_light"])
    draw.rectangle((head_left, head_top, head_right, head_top + 3), fill=COL["hair"])
    draw.rectangle((head_left, head_top, head_right, head_bottom), outline=COL["outline"], width=1)

    # Neck
    draw.rectangle((14, 26, 18, 31), fill=COL["skin_mid"])
    draw.rectangle((14, 26, 18, 31), outline=COL["outline"], width=1)
    # Suit shoulders
    draw.rectangle((5, 31, 27, 36), fill=COL["suit"])
    draw.rectangle((5, 31, 27, 36), outline=COL["outline"], width=1)
    # Torso
    draw.rectangle((5, 36, 27, 45), fill=COL["suit"])
    draw.rectangle((5, 36, 27, 45), outline=COL["outline"], width=1)
    # Shirt and tie
    draw.rectangle((11, 32, 21, 45), fill=COL["shirt"])
    draw.rectangle((15, 31, 17, 45), fill=COL["tie"])

def draw_eyes(draw: ImageDraw.ImageDraw, closed: bool = False) -> None:
    """Draw eyes scaled for 32x48."""
    if closed:
        draw.line((11, 14, 13, 14), fill=(0, 0, 0))
        draw.line((19, 14, 21, 14), fill=(0, 0, 0))
    else:
        draw.rectangle((11, 14, 13, 15), fill=(0, 0, 0))
        draw.rectangle((19, 14, 21, 15), fill=(0, 0, 0))

def draw_mouth_viseme(draw: ImageDraw.ImageDraw, viseme: str) -> None:
    """Draw visemes scaled for 32x48 (mouth around y=20)."""
    y0 = 20
    if viseme == "a":
        draw.rectangle((13, y0 - 1, 19, y0 + 2), fill=COL["tie"])
    elif viseme == "o":
        draw.rectangle((14, y0, 18, y0 + 1), fill=COL["tie"])
    elif viseme == "e":
        draw.rectangle((12, y0, 20, y0), fill=COL["tie"])

# --- Main Frame Generation ---
def make_frame(name: str, eyes_closed: bool, viseme: str | None) -> None:
    im = Image.new("RGBA", (32, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_anchor_base(d)
    draw_eyes(d, closed=eyes_closed)
    if viseme:
        draw_mouth_viseme(d, viseme)
    
    # Save to a new directory to avoid conflicts
    out_dir = os.path.join("assets", "anchor_small")
    ensure_dir(out_dir)
    im.save(os.path.join(out_dir, name), "PNG")

def main() -> None:
    make_frame("anchor_neutral_01.png", eyes_closed=False, viseme=None)
    make_frame("anchor_blink_01.png", eyes_closed=True, viseme=None)
    make_frame("anchor_talk_a_01.png", eyes_closed=False, viseme="a")
    make_frame("anchor_talk_e_01.png", eyes_closed=False, viseme="e")
    make_frame("anchor_talk_o_01.png", eyes_closed=False, viseme="o")
    print("Generated SMALL (32x48) placeholder frames in assets/anchor_small/")

if __name__ == "__main__":
    main()

