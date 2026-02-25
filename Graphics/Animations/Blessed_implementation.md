# Blessed Implementation Guide

## Overview
Blessed provides simple, cross‑platform terminal control (cursor movement, colours, input). This guide shows how to build a tiny animation loop for a news‑anchor style character plus a ticker.

## Install
```bash
pip install blessed
```

## Basics
```python
from blessed import Terminal
term = Terminal()

print(term.clear)
print(term.move_xy(10, 5) + term.bold + 'Hello')
```

## Runnable Demo: Anchor (blink/mouth/bob) + Ticker
```python
from blessed import Terminal
import time

term = Terminal()

ANCHOR_FRAMES = [
    ["  O  ", " /|\\ ", " / \\"],       # neutral
    ["  -  ", " /|\\ ", " / \\"],       # blink
    ["  O  ", " -|\\ ", " / \\"],       # mouth/gesture A
    ["  O  ", " /|/ ", " / \\"],        # mouth/gesture B
]

TICKER = " BREAKING: Low-bitrate CLI animations with Blessed demo "

def draw_block(x, y, lines, colour):
    for i, line in enumerate(lines):
        print(term.move_xy(x, y + i) + colour + line)

with term.fullscreen(), term.hidden_cursor():
    w, h = term.width, term.height
    t0 = time.time()
    tick = 0
    while True:
        print(term.home + term.clear)

        # Timings
        elapsed = time.time() - t0
        blink = (int(elapsed * 2) % 12 == 0)
        mouth = (tick // 6) % 2
        idx = 1 if blink else (2 if mouth else 0)

        # Bobbing
        base_y = h // 2 - 1
        y = base_y + ((tick // 8) % 2)
        x = w // 2 - 3

        # Anchor
        draw_block(x, y, ANCHOR_FRAMES[idx], term.white)

        # Ticker
        off = (tick % (len(TICKER) + w))
        vis = (TICKER + " " * w)[off:off + w]
        print(term.move_xy(0, h - 2) + term.yellow + vis)

        time.sleep(0.06)
        tick += 1
```

## Input Handling (optional)
```python
with term.cbreak(), term.hidden_cursor():
    val = ''
    while val.lower() != 'q':
        val = term.inkey(timeout=0.05)
        # update your state here
```

## Flicker Reduction
- Keep FPS modest (12–18)
- Only redraw changed rows (maintain a back buffer and diff)
- Avoid frequent full clears; overwrite selectively

## Composing With Other Tools
- For fancy text effects (typewriter/tickers), combine with TerminalTextEffects
- For multiple moving entities and scenes, consider Asciimatics
- For curves/waveforms, pair with Drawille


