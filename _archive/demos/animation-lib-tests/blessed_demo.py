from blessed import Terminal
import sys
import time

term = Terminal()

ANCHOR_FRAMES = [
    ["  O  ", " /|\\ ", " / \\"],
    ["  -  ", " /|\\ ", " / \\"],
    ["  O  ", " -|\\ ", " / \\"],
]
ANCHOR_WIDTH = max(max(len(line) for line in frame) for frame in ANCHOR_FRAMES)
ANCHOR_HEIGHT = len(ANCHOR_FRAMES[0])

TICKER = " BREAKING: Blessed demo — blink, mouth, bob, ticker (press Ctrl+C to quit) "

def draw_block_str(x: int, y: int, lines: list[str], colour: str) -> str:
    out = []
    for i, line in enumerate(lines):
        out.append(term.move_xy(x, y + i) + colour + line)
    return "".join(out)

def erase_block_str(x: int, y: int, width: int, height: int) -> str:
    blanks = " " * width
    out = []
    for i in range(height):
        out.append(term.move_xy(x, y + i) + blanks)
    return "".join(out)

def main() -> None:
    with term.fullscreen(), term.hidden_cursor():
        w, h = term.width, term.height
        t0 = time.time()
        tick = 0
        last_pos = None  # (x, y)
        # Initial paint of ticker (blank) to stabilise line width
        sys.stdout.write(term.move_xy(0, h - 2) + " " * w)
        sys.stdout.flush()
        while True:
            elapsed = time.time() - t0
            blink = (int(elapsed * 2) % 12 == 0)
            mouth = (tick // 6) % 2
            idx = 1 if blink else (2 if mouth else 0)

            base_y = h // 2 - 1
            y = base_y + ((tick // 8) % 2)
            x = w // 2 - (ANCHOR_WIDTH // 2)

            buf = []
            # Erase previous anchor area if we moved or frame changed
            if last_pos is not None and last_pos != (x, y):
                lx, ly = last_pos
                buf.append(erase_block_str(lx, ly, ANCHOR_WIDTH, ANCHOR_HEIGHT))

            # Draw current anchor
            buf.append(draw_block_str(x, y, ANCHOR_FRAMES[idx], term.white))

            # Draw ticker (fixed row, full width to avoid ghosting)
            off = (tick % (len(TICKER) + w))
            vis = (TICKER + " " * w)[off:off + w]
            buf.append(term.move_xy(0, h - 2) + term.yellow + vis)

            sys.stdout.write("".join(buf))
            sys.stdout.flush()

            last_pos = (x, y)
            time.sleep(0.06)
            tick += 1

if __name__ == "__main__":
    main()


