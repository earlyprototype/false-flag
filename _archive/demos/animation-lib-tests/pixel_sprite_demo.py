from blessed import Terminal
import sys
import time

"""
LucasArts-style minimal pixel sprite using half-blocks (▀/▄).
Each terminal cell carries 2 vertical pixels by colouring foreground/background
and selecting the appropriate half-block glyph.
"""

term = Terminal()

# 16-colour index mapping for foreground/background
COLOUR_INDEX = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3,
    'blue': 4,
    'magenta': 5,
    'cyan': 6,
    'white': 7,
    'bright_black': 8,
    'bright_red': 9,
    'bright_green': 10,
    'bright_yellow': 11,
    'bright_blue': 12,
    'bright_magenta': 13,
    'bright_cyan': 14,
    'bright_white': 15,
}


def cell(top: str | None, bottom: str | None) -> str:
    """Return a coloured half-block for a 2-pixel column.
    top/bottom are palette keys or None (transparent).
    - Both: use '▀' with FG=top, BG=bottom
    - Top only: '▀' with FG=top, BG=black
    - Bottom only: '▄' with FG=bottom, BG=black
    - None: space
    """
    if top is None and bottom is None:
        return term.normal + ' '
    if top is not None and bottom is not None:
        return term.color(COLOUR_INDEX[top]) + term.on_color(COLOUR_INDEX[bottom]) + '▀'
    if top is not None:
        return term.color(COLOUR_INDEX[top]) + term.on_color(COLOUR_INDEX['black']) + '▀'
    return term.color(COLOUR_INDEX['black']) + term.on_color(COLOUR_INDEX[bottom]) + '▄'


def blit_sprite(x: int, y: int, sprite_top: list[list[str | None]], sprite_bottom: list[list[str | None]]):
    """Draw a sprite defined by two rasters (top/bottom pixels). Dimensions must match.
    sprite_top/ bottom: rows of palette keys or None.
    """
    height = len(sprite_top)
    width = len(sprite_top[0]) if height else 0
    for row in range(0, height, 2):
        for col in range(width):
            t = sprite_top[row][col]
            b = None
            if row + 1 < height:
                b = sprite_top[row + 1][col]
            # allow alternate raster in sprite_bottom to animate mouth/eyes
            if sprite_bottom:
                bt = sprite_bottom[row][col] if row < len(sprite_bottom) else None
                bb = sprite_bottom[row + 1][col] if (row + 1) < len(sprite_bottom) else None
                # if provided, prefer bottom raster entries when not None
                if bt is not None:
                    t = bt
                if bb is not None:
                    b = bb
            print(term.move_xy(x + col, y + (row // 2)) + cell(t, b), end='')


# Tiny 16x16 head (palette keys); keep it abstract but blocky
HEAD_BASE = [[None]*16 for _ in range(16)]

def fill_rect(buf, x0, y0, w, h, colour):
    for yy in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            if 0 <= xx < 16 and 0 <= yy < 16:
                buf[yy][xx] = colour

# Face background
fill_rect(HEAD_BASE, 2, 2, 12, 12, 'bright_yellow')
# Hair band (fallback to yellow if brown unavailable)
fill_rect(HEAD_BASE, 2, 2, 12, 3, 'yellow')
# Eyes (2x2 blocks for visibility)
HEAD_EYES_OPEN = [row[:] for row in HEAD_BASE]
fill_rect(HEAD_EYES_OPEN, 5, 6, 2, 2, 'black')
fill_rect(HEAD_EYES_OPEN, 9, 6, 2, 2, 'black')

HEAD_EYES_CLOSED = [row[:] for row in HEAD_BASE]
fill_rect(HEAD_EYES_CLOSED, 5, 7, 2, 1, 'bright_yellow')
fill_rect(HEAD_EYES_CLOSED, 9, 7, 2, 1, 'bright_yellow')

# Mouth frames
MOUTH_NEUTRAL = [row[:] for row in HEAD_BASE]
fill_rect(MOUTH_NEUTRAL, 6, 10, 4, 1, 'red')

MOUTH_OPEN = [row[:] for row in HEAD_BASE]
fill_rect(MOUTH_OPEN, 6, 10, 4, 2, 'red')


def main() -> None:
    with term.fullscreen(), term.hidden_cursor():
        w, h = term.width, term.height
        tick = 0
        last_xy = None
        # Prepaint caption line to fixed width
        sys.stdout.write(term.move_xy(0, h - 2) + " " * w)
        sys.stdout.flush()
        while True:
            # Choose frames
            eyes = HEAD_EYES_CLOSED if (tick % 40 == 0) else HEAD_EYES_OPEN
            mouth = MOUTH_OPEN if ((tick // 6) % 2 == 0) else MOUTH_NEUTRAL

            # Bob and position
            y = h // 2 - 4 + ((tick // 8) % 2)
            x = w // 2 - 8

            buf = []
            # Erase previous sprite area if moved
            if last_xy is not None and last_xy != (x, y):
                lx, ly = last_xy
                # 16x16 sprite → 8 terminal rows (half-blocks) x 16 cols
                blanks = " " * 16
                for rr in range(8):
                    buf.append(term.move_xy(lx, ly + rr) + blanks)

            # Draw sprite with coloured half-block cells
            height = 16
            for row in range(0, height, 2):
                seg = []
                for col in range(16):
                    t = eyes[row][col]
                    b = eyes[row + 1][col] if row + 1 < height else None
                    # overlay mouth
                    bt = mouth[row][col]
                    bb = mouth[row + 1][col] if row + 1 < height else None
                    if bt is not None:
                        t = bt
                    if bb is not None:
                        b = bb
                    seg.append(cell(t, b))
                buf.append(term.move_xy(x, y + (row // 2)) + "".join(seg))

            # Caption
            caption = "LucasArts-style half-block sprite (Ctrl+C to quit)"
            buf.append(term.move_xy(max(0, (w - len(caption)) // 2), h - 2) + caption)

            sys.stdout.write("".join(buf))
            sys.stdout.flush()
            last_xy = (x, y)

            time.sleep(0.07)
            tick += 1


if __name__ == "__main__":
    main()


