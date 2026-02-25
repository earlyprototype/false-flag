# LucasArts-style CLI Animations — Research Brief (Draft)

## Goal
Produce LucasArts-style, low-bitrate character animations in the terminal (Windows Terminal/PowerShell), and define automation (MCP/APIs) to go from prompt/sprite assets → palette-quantised frames → terminal runtime with minimal flicker.

## Rendering decision (default + fallbacks)
- Default: Half-block rendering (▀/▄) with ANSI colours.
  - Pros: Clean, retro block aesthetic; 2 vertical pixels per cell; readable at small sizes; widely supported.
  - Technique: Compose each terminal cell from top/bottom pixel colours using a single glyph with FG (top) and BG (bottom).
- Optional: Braille (Drawille) for curves, gauges, waveforms.
  - Pros: 8 dots per cell gives higher perceived resolution for line art.
  - Cons: Monochrome unless you layer colour carefully; font-dependent.
- Fallback import path: Image-in-terminal playback (e.g., term-image or chafa via WSL) for pre-rendered frames, if needed.

Terminal target: Windows Terminal with a monospaced font (Cascadia Mono/Consolas). Use buffered, partial redraws (dirty regions) and single flush per frame. Target 12–18 FPS.

References (rendering):
- Windows Console VT sequences (ANSI, colours): `https://learn.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences`
- Classic console vs VT: `https://learn.microsoft.com/en-us/windows/console/classic-vs-vt`

## Palette and sprite sizing
- Palette: LucasArts-adjacent 16-colour set (DB16/EGA-like). Map to terminal 16-colour SGR codes; optionally support 24-bit truecolour when available.
- Mapping: Quantise in perceptual space (CIELAB ΔE) to nearest terminal colour; add ordered/Floyd–Steinberg dithering for ramps. Our encoder exposes `nearest_terminal_index(rgb)`.
- Sizes: 24×24 (faces) and 32×32 (busts) look crisp with half-blocks; outline 1px dark stroke; use simple shadows under hair/neck.

DB16 palette (hex):
`140C1C, 442434, 30346D, 4E4A4E, 854C30, 346524, D04648, 757161, 597DCE, D27D2C, 8595A1, 6DAA2C, D2AA99, 6DC2CA, DAD45E, DEEEDE`

Terminal mapping (produced by quantiser at runtime):
- Method: for each DB16 colour, choose nearest terminal 16-colour index; prefer 24-bit if terminal supports truecolour.
- Example (Python):
```python
from Graphics.Animations.tools.palette_db16 import DB16_PALETTE, nearest_terminal_index
mapping = [nearest_terminal_index(rgb) for rgb in DB16_PALETTE]
print(mapping)
```

## Asset pipeline (Aseprite → PNG/JSON → terminal frames)
- Author sprites in Aseprite with tags per animation (blink, talk, idle).
- Export spritesheet + metadata via CLI:
```bash
aseprite -b sprite.aseprite \
  --sheet out/sheet.png \
  --data out/sheet.json \
  --format json-array \
  --list-tags --list-slices \
  --ignore-empty --trim
```
- Alternatively, export individual frames:
```bash
aseprite -b sprite.aseprite --save-as out/{tag}_{frame}.png
```
- Quantise PNG to target palette (if authored in 24-bit), then encode to half-block cells (2 rows → 1 cell). Store as rows of SGR-coloured strings per frame.

References (Aseprite CLI):
- CLI docs: `https://www.aseprite.org/docs/cli/`
- Sprite sheet docs: `https://www.aseprite.org/docs/sprite-sheet/`
- Slices/export meta: `https://www.aseprite.org/docs/slices/`

Useful CLI options:
- `--sheet-pack` to pack frames tightly; `--sheet-type rows` to preserve order
- `--filename-format {tag}_{frame}` for predictable names
- `--tag TAGNAME` to export a specific sequence only

## Half-block encoder (summary)
- Read image as RGBA; for each 2-row×1-col block, compute topColour, bottomColour.
- Map RGBA → terminal colour index (0–15) or 24-bit; choose glyph:
  - both = '▀' with FG=top, BG=bottom
  - top-only = '▀' (FG=top, BG=black)
  - bottom-only = '▄' (FG=bottom, BG=black)
  - none = ' '
- Prebuild each terminal line as one string. Retain a previous-frame buffer to update only changed segments.

## Minimal scene schema (YAML)
```yaml
version: 1
palette: db16
sprites:
  anchor:
    size: [24, 24]
    frames:
      neutral: frames/anchor_neutral_*.png
      blink:   frames/anchor_blink_*.png
      talk:    frames/anchor_talk_*.png
layers:
  - id: character
    sprite: anchor
    timeline:
      - { seq: neutral, frames: 24 }
      - { seq: blink,   frames: 2, every: 60 }
      - { seq: talk,    frames: 8, when: speaking }
    bob: { amplitude: 1, period: 16 }
  - id: ticker
    type: text_scroll
    text: "BREAKING: ..."
    row: -2
```

## Automation via MCP (endpoints)
- sprite.generate
  - in: { prompt, seed?, style: "lucasarts" }
  - out: { png|aseprite, meta }
- palette.quantise
  - in: { image(s), palette: "db16"|custom, dither: fs|ordered }
  - out: { image(s)_quantised, mapping }
- encode.halfblock
  - in: { image(s), colourMode: 16|24 }
  - out: { frames: [rows: [strings]], metrics }
- scene.build
  - in: { schema(yaml/json), assets }
  - out: { compiled_scene.json }
- runtime.emit_python
  - in: { compiled_scene.json }
  - out: { python_main.py + assets/strings }

Candidate providers
- Aseprite CLI (local) or Aseprite MCP server (community).
- Image generation: ComfyUI HTTP API (self-host) or Replicate models tuned for pixel-art.

References (automation):
- ComfyUI API patterns: `https://www.viewcomfy.com/blog/building-a-production-ready-comfyui-api`
- Classic ComfyUI API providers: `https://www.bentoml.com/blog/comfy-pack-serving-comfyui-workflows-as-apis`
- Replicate model example (sprites): `https://www.aimodels.fyi/models/replicate/flux-sprites-miike-ai`

Reference (palette):
- DB16 listing: `https://lospec.com/palette-list/dawnbringer-16`

## Performance and QA
- Redraw: Dirty-region updates + single flush; avoid full clears.
- FPS: Cap 12–18; pre-render frequent frames (blink/talk) to strings.
- Fonts: Recommend Cascadia Mono or Consolas; verify Unicode elements.
- Readability: High-contrast outlines; avoid 1px noise; keep mouth/eyes 2×2 px minimum.

Local benchmark procedure (Windows Terminal):
1. Ensure venv and install: `pip install -r Graphics/Animations/demos/requirements.txt`
2. Half-block path:
   - Export 24×24 head frames from Aseprite (neutral/blink/talk) to `frames/`.
   - Compile: `python -m Graphics.Animations.tools.compile_scene Graphics/Animations/tools/scene_schema.yaml --width 100 --height 28 --mode 16 --out compiled_scene.json`
   - Play: `python -m Graphics.Animations.tools.runtime_player compiled_scene.json`
3. Braille path: run `drawille_demo.py` and note perceived resolution and CPU.
4. Image-in-terminal fallback (optional): evaluate `term-image` or `chafa` via WSL with a tiny GIF.
5. Record: average frame time, visual artefacts, and flicker notes for each.

## Bench plan (Windows Terminal)
- Micro-demos: half-block vs braille vs image-in-terminal; measure average frame time, CPU, and artefacts.
- Config matrix: 16-colour vs 24-bit; font variants; 24×24 vs 32×32.

## Next steps
1) Implement encoder script (PNG → half-block frames) and palette quantiser.
2) Export one 24×24 head (neutral/blink/talk) from Aseprite; encode and play.
3) Finalise scene schema; build a minimal runtime that reads JSON/YAML and renders with Blessed.
4) Draft MCP server stubs for encode.halfblock and runtime.emit_python; add sprite.quantise later.

---
Notes: Windows Terminal and fonts differ in Unicode rendering; verify on target machines. Palette mapping to 16-colour SGR is approximate; include 24-bit mode as a switch where supported.
