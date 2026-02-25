## TerminalTextEffects — Implementation Overview

### Purpose
Python library focused on animated text effects in the terminal (typewriter, slide, fade, colour transitions). Ideal for tickers, lower‑thirds, and animated headings.

### Best Fit
- News tickers and headlines
- Animated text splash/intro screens
- Low-bitrate text emphasis alongside other CLI elements

### Pros
- Simple API for common text animations
- Works well in Windows Terminal/PowerShell
- Low overhead and quick to script

### Cons
- Not a sprite/scene engine; no native character animation
- Limited frame-by-frame control vs. asciimatics/curses

### Install
```bash
pip install terminaltexteffects
```

### Minimal Example (typewriter)
```python
from terminaltexteffects.effects import typewriter

effect = typewriter.Typewriter("Good evening, I'm your AI news anchor...", speed=50)
effect.run()
```

### When Not To Use
- You need moving ASCII characters/sprites → use `asciimatics`
- You need layered scenes, z-ordering, or multiple concurrent animations

### Notes
- Pair with `asciimatics` for character animation; keep TTE for text.
- See `terminalTexteffects.md` for detailed implementation guidance.


