"""
Generate news studio/broadcast setting background tiles.
Creates a professional news broadcast aesthetic with:
- Background: City skyline silhouette at night
- Midground: Studio lighting effects and depth
"""

import os
from typing import Tuple
from PIL import Image, ImageDraw

# DB16 Palette
HEX = {
    "black": 0x140C1C,
    "dark_purple": 0x442434,
    "navy": 0x30346D,
    "dark_grey": 0x4E4A4E,
    "brown": 0x854C30,
    "dark_green": 0x346524,
    "red": 0xD04648,
    "grey": 0x757161,
    "blue": 0x597DCE,
    "orange": 0xD27D2C,
    "light_grey": 0x8595A1,
    "lime": 0x6DAA2C,
    "tan": 0xD2AA99,
    "cyan": 0x6DC2CA,
    "yellow": 0xDAD45E,
    "cream": 0xDEEED6,
}

def hx(x: int) -> Tuple[int, int, int]:
    return (x >> 16 & 0xFF, x >> 8 & 0xFF, x & 0xFF)

COL = {k: hx(v) for k, v in HEX.items()}

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def make_news_studio_background() -> None:
    """Create 16x16 background tile: City skyline at night through studio window."""
    bg_dir = os.path.join("assets", "news_studio_bg")
    ensure_dir(bg_dir)
    
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    # Night sky gradient (dark purple to navy)
    for y in range(8):
        color = COL["dark_purple"] if y < 4 else COL["navy"]
        d.rectangle((0, y, 15, y), fill=color + (255,))
    
    # City skyline silhouette (buildings of varying heights)
    buildings = [
        (0, 12, 2, 15),    # Building 1 - short
        (3, 10, 5, 15),    # Building 2 - medium
        (6, 13, 8, 15),    # Building 3 - short
        (9, 9, 11, 15),    # Building 4 - tall
        (12, 11, 14, 15),  # Building 5 - medium
        (15, 14, 15, 15),  # Building 6 - very short (edge)
    ]
    
    for x1, y1, x2, y2 in buildings:
        # Building body
        d.rectangle((x1, y1, x2, y2), fill=COL["black"] + (255,))
        # Window lights (tiny yellow pixels)
        if y2 - y1 > 2:  # Only if building tall enough
            for wy in range(y1 + 1, y2, 2):
                if (x1 + wy) % 3 == 0:  # Random-ish windows
                    d.point((x1, wy), fill=COL["yellow"] + (200,))
    
    # Horizon line
    d.rectangle((0, 8, 15, 8), fill=COL["dark_grey"] + (255,))
    
    im.save(os.path.join(bg_dir, "tile_16x16.png"), "PNG")
    print(f"Created: {os.path.join(bg_dir, 'tile_16x16.png')}")


def make_news_studio_midground() -> None:
    """Create 16x16 midground tile: Studio lighting effects and subtle depth."""
    bg_dir = os.path.join("assets", "news_studio_bg")
    ensure_dir(bg_dir)
    
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    # Vertical light beams / studio lighting (semi-transparent)
    # Create subtle vertical bands suggesting studio depth
    for x in range(16):
        if x % 5 == 0:  # Vertical light beam every 5 pixels
            for y in range(16):
                # Gradient effect - lighter at top
                alpha = 60 if y < 8 else 30
                d.point((x, y), fill=COL["blue"] + (alpha,))
        elif x % 5 == 1:
            for y in range(16):
                alpha = 40 if y < 8 else 20
                d.point((x, y), fill=COL["cyan"] + (alpha,))
    
    # Subtle horizontal bands suggesting studio floor/ceiling
    d.rectangle((0, 0, 15, 0), fill=COL["light_grey"] + (40,))  # Ceiling line
    d.rectangle((0, 15, 15, 15), fill=COL["dark_grey"] + (60,))  # Floor line
    
    # Diagonal light rays (studio lights)
    for i in range(0, 16, 4):
        d.line((i, 0, i + 8, 16), fill=COL["blue"] + (20,))
    
    im.save(os.path.join(bg_dir, "mid_tile_16x16.png"), "PNG")
    print(f"Created: {os.path.join(bg_dir, 'mid_tile_16x16.png')}")


def make_alternative_backgrounds() -> None:
    """Create alternative background variations for different moods."""
    bg_dir = os.path.join("assets", "news_studio_bg", "variants")
    ensure_dir(bg_dir)
    
    # Variant 1: Breaking news (more dramatic red tones)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    # Dark red/orange gradient
    for y in range(8):
        color = COL["red"] if y < 4 else COL["dark_purple"]
        d.rectangle((0, y, 15, y), fill=color + (180,))
    
    # Same skyline
    buildings = [(0, 12, 2, 15), (3, 10, 5, 15), (6, 13, 8, 15), 
                 (9, 9, 11, 15), (12, 11, 14, 15), (15, 14, 15, 15)]
    for x1, y1, x2, y2 in buildings:
        d.rectangle((x1, y1, x2, y2), fill=COL["black"] + (255,))
        if y2 - y1 > 2:
            for wy in range(y1 + 1, y2, 2):
                if (x1 + wy) % 3 == 0:
                    d.point((x1, wy), fill=COL["orange"] + (220,))
    
    d.rectangle((0, 8, 15, 8), fill=COL["dark_grey"] + (255,))
    im.save(os.path.join(bg_dir, "tile_breaking_news_16x16.png"), "PNG")
    print(f"Created variant: Breaking News background")
    
    # Variant 2: Daytime studio (lighter, blue tones)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    # Light blue sky
    for y in range(8):
        color = COL["cyan"] if y < 4 else COL["blue"]
        d.rectangle((0, y, 15, y), fill=color + (200,))
    
    # Same skyline but lighter
    for x1, y1, x2, y2 in buildings:
        d.rectangle((x1, y1, x2, y2), fill=COL["dark_grey"] + (255,))
        if y2 - y1 > 2:
            for wy in range(y1 + 1, y2, 2):
                if (x1 + wy) % 3 == 0:
                    d.point((x1, wy), fill=COL["yellow"] + (180,))
    
    d.rectangle((0, 8, 15, 8), fill=COL["grey"] + (255,))
    im.save(os.path.join(bg_dir, "tile_daytime_16x16.png"), "PNG")
    print(f"Created variant: Daytime background")


def main() -> None:
    print("Generating News Studio Background Tiles...\n")
    make_news_studio_background()
    make_news_studio_midground()
    make_alternative_backgrounds()
    print("\nAll tiles generated successfully!")
    print("\nFiles created:")
    print("  - assets/news_studio_bg/tile_16x16.png (background layer)")
    print("  - assets/news_studio_bg/mid_tile_16x16.png (midground layer)")
    print("  - assets/news_studio_bg/variants/tile_breaking_news_16x16.png (red tones)")
    print("  - assets/news_studio_bg/variants/tile_daytime_16x16.png (blue tones)")
    print("\nTo use with the parallax demo, copy tiles to the run's assets folder.")


if __name__ == "__main__":
    main()


