## Drawille — Implementation Overview

### Purpose
Terminal "pixel" graphics via Unicode braille characters (2×4 dot matrix per cell). Enables smoother curves, arcs, and simple raster‑like drawings in pure text terminals.

### Best Fit
- Low‑bitrate line art, icons, and waveform/graph displays
- Simple motion paths (orbiting dot, spinning arc, progress dials)
- Combining with `blessed` for cursor control and timing

### Pros
- Higher apparent resolution than ASCII (8 dots per cell)
- Very small API; fast to prototype
- Works in most modern terminals with Unicode support

### Cons
- Monochrome by default; colour requires extra handling
- No sprites/effects; you draw points/lines each frame
- Rendering relies on terminal font/Unicode correctness

### Install
```bash
pip install drawille
```

### Minimal Example (orbiting dot)
```python
import math, time
from drawille import Canvas

c = Canvas()
radius = 10
t = 0.0

def render():
    global t
    c.clear()
    for i in range(64):
        a = i * (2 * math.pi / 64)
        x = int(radius * math.cos(a))
        y = int(radius * math.sin(a))
        c.set(x, y)
    # moving dot
    x = int(radius * math.cos(t))
    y = int(radius * math.sin(t))
    c.set(x, y)
    t += 0.15
    print("\x1b[H\x1b[2J" + c.frame())  # ANSI clear + draw

while True:
    render()
    time.sleep(0.05)
```

### With Blessed (positioning/colour)
```python
from blessed import Terminal
from drawille import Canvas
import time

term = Terminal()
canvas = Canvas()

with term.fullscreen(), term.hidden_cursor():
    for tick in range(9999):
        canvas.clear()
        for x in range(-8, 9):
            canvas.set(x, int((x*x)/16))
        frame = canvas.frame()
        print(term.home + term.clear + term.move_xy(5, 3) + term.cyan + frame)
        time.sleep(0.06)
```

### When Not To Use
- Need text effects or sprite logic → use `terminaltexteffects` or `asciimatics`
- Heavy colour usage or complex layering

### Notes
- For colour, render multiple canvases or post‑process lines with ANSI colour codes using `blessed`.


