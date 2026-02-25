## Blessed — Implementation Overview

### Purpose
Lightweight, cross‑platform terminal control for Python (cursor movement, colours, input). Ideal for building a tiny custom animation loop for simple ASCII characters and tickers.

### Best Fit
- Minimal “micro‑engine” animations (blink, mouth open/close, bob by ±1 row)
- Static stage with one or two independently timed elements
- Total control over draw order and timing with very small code

### Pros
- Extremely simple mental model; no scene graph
- Precise cursor positioning; good colour & style support
- Works reliably in Windows Terminal/PowerShell

### Cons
- You manage all timing, double‑buffering, and redraws yourself
- No built‑in effects or sprites

### Install
```bash
pip install blessed
```

### Minimal Example (blink + mouth + ticker)
```python
from blessed import Terminal
import time

term = Terminal()

anchor_frames = [
    [
        "  O  ",
        " /|\\ ",
        " / \\ "
    ],
    [
        "  -  ",  # blink (eyes closed)
        " /|\\ ",
        " / \\ "
    ],
    [
        "  O  ",
        " -|\\ ",  # mouth/gesture
        " / \\ "
    ],
]

ticker = " BREAKING: Demo ticker scrolling across the bottom "

with term.fullscreen(), term.hidden_cursor():
    w = term.width
    h = term.height
    t0 = time.time()
    tick = 0
    while True:
        # Compute frame indices
        blink_idx = int((time.time() - t0) * 2) % 12 == 0  # rare blink
        mouth_idx = (tick // 6) % 2  # slow mouth open/close
        idx = 1 if blink_idx else (2 if mouth_idx else 0)

        # Clear screen
        print(term.home + term.clear)

        # Anchor position & bob
        base_y = h // 2
        bob = (tick // 8) % 2  # subtle bob
        y = base_y - 1 + bob
        x = w // 2 - 3

        # Draw anchor
        for i, line in enumerate(anchor_frames[idx]):
            print(term.move_xy(x, y + i) + term.white + line)

        # Draw ticker
        offset = (tick % (len(ticker) + w))
        visible = (ticker + " " * w)[offset:offset + w]
        print(term.move_xy(0, h - 2) + term.yellow + visible)

        # Frame pacing
        time.sleep(0.06)
        tick += 1
```

### When Not To Use
- Need many independent moving entities → consider `asciimatics`
- Need prebuilt effects (typewriter, slide, fire) → use `terminaltexteffects`

### Notes
- Add a simple back buffer (list of strings) if flicker occurs; only redraw changed cells.


