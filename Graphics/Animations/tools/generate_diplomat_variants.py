import os
from typing import Tuple
from PIL import Image, ImageDraw

"""
Generate multiple diplomat sprite variants including male and female versions.
Creates different combinations of suits, hair, and skin tones.
"""

# --- Color Palettes ---
HEX = {
    # Original colors
    "outline": 0x140C1C,
    "hair_brown": 0x854C30,
    "hair_black": 0x2C2137,
    "hair_blonde": 0xD2AA99,
    "hair_grey": 0x8595A1,
    "skin_light": 0xDEEEDE,
    "skin_mid": 0xD2AA99,
    "skin_tan": 0xC79A7C,
    "skin_dark": 0x8B5A3C,
    "shadow": 0x8595A1,
    "suit_blue": 0x30346D,
    "suit_grey": 0x6C6B6E,
    "suit_black": 0x2C2137,
    "suit_navy": 0x243356,
    "suit_shadow": 0x4E4A4E,
    "shirt": 0xDEEEDE,
    "tie_red": 0xD04648,
    "tie_blue": 0x4B5B9E,
    "tie_purple": 0x6C3B77,
    "dress_teal": 0x45929B,
    "dress_burgundy": 0x8E3B46,
}

def hx(x: int) -> Tuple[int, int, int]:
    return (x >> 16 & 0xFF, x >> 8 & 0xFF, x & 0xFF)

COL = {k: hx(v) for k, v in HEX.items()}

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# --- Male Diplomat Drawing Functions ---
def draw_male_diplomat(draw: ImageDraw.ImageDraw, suit_color: str, tie_color: str, 
                       hair_color: str, skin_color: str) -> None:
    """Draw a male diplomat bust (32x48)."""
    # Head bounds
    head_left, head_top, head_right, head_bottom = 7, 6, 24, 26
    draw.rectangle((head_left, head_top, head_right, head_bottom), fill=COL[skin_color])
    
    # Short professional hair
    draw.rectangle((head_left, head_top, head_right, head_top + 3), fill=COL[hair_color])
    draw.rectangle((head_left, head_top, head_right, head_bottom), outline=COL["outline"], width=1)

    # Neck
    draw.rectangle((14, 26, 18, 31), fill=COL[skin_color])
    draw.rectangle((14, 26, 18, 31), outline=COL["outline"], width=1)
    
    # Suit shoulders
    draw.rectangle((5, 31, 27, 36), fill=COL[suit_color])
    draw.rectangle((5, 31, 27, 36), outline=COL["outline"], width=1)
    
    # Torso
    draw.rectangle((5, 36, 27, 45), fill=COL[suit_color])
    draw.rectangle((5, 36, 27, 45), outline=COL["outline"], width=1)
    
    # Shirt and tie
    draw.rectangle((11, 32, 21, 45), fill=COL["shirt"])
    draw.rectangle((15, 31, 17, 45), fill=COL[tie_color])

# --- Female Diplomat Drawing Functions ---
def draw_female_diplomat(draw: ImageDraw.ImageDraw, outfit_color: str, 
                         hair_color: str, skin_color: str) -> None:
    """Draw a female diplomat bust (32x48) - pear-shaped face (flat top, softer jaw)."""
    # Head bounds
    head_left, head_top, head_right, head_bottom = 7, 6, 24, 26
    
    # Draw face FIRST - pear-shaped with rounded top
    # Rounded top of head (more natural)
    draw.ellipse((head_left, head_top, head_right, head_top + 6), fill=COL[skin_color])
    
    # Middle portion (forehead/cheeks area) - rectangular
    draw.rectangle((head_left, head_top + 3, head_right, head_top + 10), fill=COL[skin_color])
    
    # Lower portion (jaw/chin area) - more pronounced taper
    # Draw as trapezoid: wider at top, narrower at bottom (2px inset)
    jaw_top = head_top + 10
    draw.polygon([
        (head_left, jaw_top),           # Top left
        (head_right, jaw_top),          # Top right
        (head_right - 2, head_bottom),  # Bottom right (2px inset for more taper)
        (head_left + 2, head_bottom)    # Bottom left (2px inset)
    ], fill=COL[skin_color])
    
    # Outline the face with rounded top and taper
    # Rounded top arc
    draw.arc((head_left, head_top, head_right, head_top + 6), 180, 360, fill=COL["outline"], width=1)
    # Left side with taper
    draw.line([(head_left, head_top + 3), (head_left, jaw_top)], fill=COL["outline"], width=1)
    draw.line([(head_left, jaw_top), (head_left + 2, head_bottom)], fill=COL["outline"], width=1)
    # Right side with taper
    draw.line([(head_right, head_top + 3), (head_right, jaw_top)], fill=COL["outline"], width=1)
    draw.line([(head_right, jaw_top), (head_right - 2, head_bottom)], fill=COL["outline"], width=1)
    # Bottom
    draw.line([(head_left + 2, head_bottom), (head_right - 2, head_bottom)], fill=COL["outline"], width=1)
    
    # NOW draw hair OVER the face to cover parts of it
    # Top of head/crown - covers entire top and rounded head area (DRAW FIRST)
    draw.ellipse((head_left - 1, head_top - 1, head_right + 1, head_top + 8), fill=COL[hair_color])
    
    # Left side hair - covers left edge of face and connects to crown
    draw.rectangle((head_left - 2, head_top + 4, head_left + 1, 30), fill=COL[hair_color])
    
    # Right side hair - covers right edge of face and connects to crown
    draw.rectangle((head_right - 1, head_top + 4, head_right + 2, 31), fill=COL[hair_color])
    
    # Diagonal sweep/bangs across forehead - higher up so she can see!
    # Sweeps from upper left down across to right side, but stays above eyes
    draw.polygon([
        (head_left - 1, head_top + 2),      # Start left upper
        (head_right + 1, head_top + 6),     # End right (above eyes)
        (head_right + 1, head_top + 8),     # Thickness
        (head_left - 1, head_top + 5)       # Back to left
    ], fill=COL[hair_color])

    # Neck (same as male)
    draw.rectangle((14, 26, 18, 31), fill=COL[skin_color])
    draw.rectangle((14, 26, 18, 31), outline=COL["outline"], width=1)
    
    # Professional suit shoulders (same as male)
    draw.rectangle((5, 31, 27, 36), fill=COL[outfit_color])
    draw.rectangle((5, 31, 27, 36), outline=COL["outline"], width=1)
    
    # Torso (same as male)
    draw.rectangle((5, 36, 27, 45), fill=COL[outfit_color])
    draw.rectangle((5, 36, 27, 45), outline=COL["outline"], width=1)
    
    # Shirt/blouse (same as male)
    draw.rectangle((11, 32, 21, 45), fill=COL["shirt"])
    
    # Brooch instead of tie (small decorative pin at collar)
    brooch_x, brooch_y = 16, 33
    # Small circular brooch
    draw.ellipse((brooch_x - 1, brooch_y - 1, brooch_x + 1, brooch_y + 1), fill=COL["tie_purple"])
    draw.point((brooch_x, brooch_y), fill=COL["shirt"])  # Center highlight

def draw_eyes(draw: ImageDraw.ImageDraw, closed: bool = False) -> None:
    """Draw eyes scaled for 32x48."""
    if closed:
        draw.line((11, 14, 13, 14), fill=(0, 0, 0), width=1)
        draw.line((19, 14, 21, 14), fill=(0, 0, 0), width=1)
    else:
        draw.rectangle((11, 14, 13, 15), fill=(0, 0, 0))
        draw.rectangle((19, 14, 21, 15), fill=(0, 0, 0))

def draw_mouth_viseme(draw: ImageDraw.ImageDraw, viseme: str) -> None:
    """Draw visemes scaled for 32x48 (mouth around y=20)."""
    y0 = 20
    if viseme == "a":
        draw.rectangle((13, y0 - 1, 19, y0 + 2), fill=COL["tie_red"])
    elif viseme == "o":
        draw.ellipse((14, y0 - 1, 18, y0 + 2), fill=COL["tie_red"])
    elif viseme == "e":
        draw.rectangle((12, y0, 20, y0), fill=COL["tie_red"])

# --- Frame Generation ---
def make_character_frames(character_name: str, is_female: bool, **colors) -> None:
    """Generate a complete sprite pack for a character."""
    out_dir = os.path.join("assets", character_name)
    ensure_dir(out_dir)
    
    frames = [
        ("neutral_01.png", False, None),
        ("blink_01.png", True, None),
        ("talk_a_01.png", False, "a"),
        ("talk_e_01.png", False, "e"),
        ("talk_o_01.png", False, "o"),
    ]
    
    for filename, eyes_closed, viseme in frames:
        im = Image.new("RGBA", (32, 48), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        
        if is_female:
            draw_female_diplomat(d, colors["outfit"], colors["hair"], colors["skin"])
        else:
            draw_male_diplomat(d, colors["suit"], colors["tie"], colors["hair"], colors["skin"])
        
        draw_eyes(d, closed=eyes_closed)
        if viseme:
            draw_mouth_viseme(d, viseme)
        
        full_name = f"{character_name}_{filename}"
        im.save(os.path.join(out_dir, full_name), "PNG")
    
    print(f"* Generated {character_name} sprite pack in assets/{character_name}/")

def main() -> None:
    print("Generating diplomat sprite variants...\n")
    
    # Variant 1: Distinguished grey-haired male diplomat (grey suit, blue tie)
    make_character_frames(
        "diplomat_grey",
        is_female=False,
        suit="suit_grey",
        tie="tie_blue",
        hair="hair_grey",
        skin="skin_light"
    )
    
    # Variant 2: Dark-suited male diplomat (black suit, purple tie)
    make_character_frames(
        "diplomat_dark",
        is_female=False,
        suit="suit_black",
        tie="tie_purple",
        hair="hair_black",
        skin="skin_tan"
    )
    
    # Variant 3: Navy-suited male diplomat (navy suit, red tie)
    make_character_frames(
        "diplomat_navy",
        is_female=False,
        suit="suit_navy",
        tie="tie_red",
        hair="hair_brown",
        skin="skin_mid"
    )
    
    # Variant 4: Female diplomat (teal dress/blazer, blonde hair)
    make_character_frames(
        "diplomat_female_blonde",
        is_female=True,
        outfit="dress_teal",
        hair="hair_blonde",
        skin="skin_light"
    )
    
    # Variant 5: Female diplomat (burgundy suit, dark hair)
    make_character_frames(
        "diplomat_female_dark",
        is_female=True,
        outfit="dress_burgundy",
        hair="hair_black",
        skin="skin_tan"
    )
    
    # Variant 6: Female diplomat (navy blazer, grey hair - senior diplomat)
    make_character_frames(
        "diplomat_female_senior",
        is_female=True,
        outfit="suit_navy",
        hair="hair_grey",
        skin="skin_light"
    )
    
    print(f"\n{'='*60}")
    print("Generated 6 diplomat variants:")
    print("  * diplomat_grey (male, grey suit)")
    print("  * diplomat_dark (male, black suit)")
    print("  * diplomat_navy (male, navy suit)")
    print("  * diplomat_female_blonde (female, teal outfit)")
    print("  * diplomat_female_dark (female, burgundy outfit)")
    print("  * diplomat_female_senior (female, navy outfit)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

