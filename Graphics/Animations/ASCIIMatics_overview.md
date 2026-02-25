## ASCIIMatics — Implementation Overview

### Purpose
Terminal animation and TUI framework for Python. Good for simple character/sprite motion, scene timing, and text effects in the terminal.

### Best Fit
- Simple sprite/character animations (blink, mouth, bob, move on a path)
- Mixed text + character scenes (ticker, lower-thirds, title cards)
- Low-bitrate CLI visuals that need basic timing and layering

### Pros
- Built-in scenes/effects/renderers; supports sprites and paths
- Cross-platform; works in Windows Terminal/PowerShell
- Minimal dependencies; easy to prototype

### Cons
- ASCII only; no true raster graphics
- Performance depends on terminal; heavy scenes can flicker
- Learning curve for scene/effect timing

### Install
```bash
pip install asciimatics
```

### Minimal Example (character frames)
```python
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Print
from asciimatics.renderers import StaticRenderer

frames = [
    r"""
     O
    /|\
    / \
    """,
    r"""
     O
    -|\
    / \
    """,
]

def demo(screen):
    effects = [
        Print(screen, StaticRenderer(images=[f]), x=10, y=5, start_frame=i*20, stop_frame=(i+1)*20)
        for i, f in enumerate(frames)
    ]
    screen.play([Scene(effects, -1)])

Screen.wrapper(demo)
```

### When Not To Use
- Need true pixel graphics or image playback → consider `chafa` (WSL) or image-to-ASCII playback tools
- Complex game loops/physics → consider a game engine or curses-based custom loop

### Notes
- See `ASCIIMatics_implementation.md` for full guide and extended examples.


