# Drawille Implementation Guide

## Overview
Drawille renders points and lines using Unicode braille (2×4 dots per cell), giving higher apparent resolution than plain ASCII. Great for low‑bitrate curves, gauges, and icons in the terminal.

## Install
```bash
pip install drawille
```

## Basics
```python
from drawille import Canvas

c = Canvas()
c.set(0, 0)
print(c.frame())
```

## Runnable Demo: Orbiting Dot + Ring
```python
import math, time
from drawille import Canvas

c = Canvas()
radius = 12
t = 0.0

def render():
    global t
    c.clear()
    # draw ring
    for i in range(96):
        a = i * (2 * math.pi / 96)
        x = int(radius * math.cos(a))
        y = int(radius * math.sin(a))
        c.set(x, y)
    # moving dot
    x = int(radius * math.cos(t))
    y = int(radius * math.sin(t))
    c.set(x, y)
    t += 0.12
    print("\x1b[H\x1b[2J" + c.frame())

while True:
    render()
    time.sleep(0.05)
```

## With Blessed: Positioning & Colour
```python
from blessed import Terminal
from drawille import Canvas
import time

term = Terminal()
canvas = Canvas()

with term.fullscreen(), term.hidden_cursor():
    w, h = term.width, term.height
    for tick in range(2000):
        canvas.clear()
        # Parabola sample
        for x in range(-16, 17):
            y = int((x*x)/8)
            canvas.set(x, y)
        frame = canvas.frame()
        print(term.home + term.clear)
        print(term.move_xy(4, 3) + term.cyan + frame)
        print(term.move_xy(4, h - 2) + term.yellow + "Drawille + Blessed demo (press Ctrl+C to quit)")
        time.sleep(0.06)
```

## Tips
- Keep frame rate moderate (10–18 FPS)
- For colour layers, split primitives by colour and print with ANSI codes
- Use a stable monospaced font with good braille support

## When To Pair With Others
- Use **Blessed** for input, cursor control, and layout
- Use **TerminalTextEffects** for textual titles/tickers
- Use **ASCIIMatics** if you need sprite logic and scene timing


