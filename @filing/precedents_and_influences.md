# Precedents and Influences for LucasArts‑style Pixel Art (CLI Context)

## Who came before
- Lucasfilm Games / LucasArts (1987–1998)
  - Engine: SCUMM; tools: Deluxe Paint (Amiga/PC).
  - Constraints: EGA 16‑colour → VGA 256‑colour; 320×200; palette swaps; dithering and clusters.
  - Techniques: bold 1px outlines, flat shading, high‑contrast shapes, 3/4 bust talk portraits, short loops (3–8 frames), viseme‑lite mouth cycles + blinks.
  - Notable titles: The Secret of Monkey Island, Day of the Tentacle, Full Throttle (later stylisation: Grim Fandango).

- Sierra On‑Line (SCI, late 80s–90s)
  - Painterly EGA/VGA scenes, realistic proportions; similar constraints; walk cycles and talk portraits.

- Console/8‑bit heritage (NES/Atari)
  - Tile/sprite composition, fixed palettes, 2bpp/4bpp limits, palette cycling; design for silhouette first.

- Demoscene, ANSI/ASCII art
  - Block elements, half‑blocks, shaded block characters, SAUCE metadata; techniques relevant to terminal rendering.

## What they were aiming for
- Readability at low resolution; mood via silhouette and colour contrast.
- Fast production under tight memory/CPU: small palettes, recycled frames, palette swaps, modular tiles.
- Expressiveness from minimal frames: blinks, mouth shapes, idle bobs, holds and anticipations.

## Techniques we can reuse (without reinventing wheels)
- Style bible: limited palette (e.g., DB16), outline rules, shadow rules, 3/4 bust camera, simplified backgrounds.
- Animation economy: 2–6 frames per action; viseme‑lite (open/closed/wide) + periodic blink; idle bob.
- Palette discipline: swatches, ramps, contrast pairs; palette swapping for variants.
- Pipeline: author → quantise to target palette → export frames → encode → runtime with dirty‑region updates.

## Practical lessons for CLI
- Half‑block (▀/▄) cells emulate “pixel” pairs; keep eyes/mouth ≥2×2 pixels; avoid noisy dithers at terminal scale.
- Strong outer silhouette; inner details only where contrast permits; prefer large clusters to single‑pixel noise.
- FPS 12–18 with single flush per frame; precompose lines; avoid full clears; benchmark on Windows Terminal.

## References
- Windows Console VT sequences (ANSI colours, control): `https://learn.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences`
- Classic Console vs VT: `https://learn.microsoft.com/en-us/windows/console/classic-vs-vt`
- Aseprite CLI: `https://www.aseprite.org/docs/cli/` · Sprite sheets: `https://www.aseprite.org/docs/sprite-sheet/` · Slices/meta: `https://www.aseprite.org/docs/slices/`
- DB16 palette (Lospec): `https://lospec.com/palette-list/dawnbringer-16`
- SCUMM overview: `https://en.wikipedia.org/wiki/SCUMM`
- Deluxe Paint: `https://en.wikipedia.org/wiki/Deluxe_Paint`
- Book: The Art of Point‑and‑Click Adventure Games (Bitmap Books)
- ANSI/ASCII art background: SAUCE spec / Blocktronics overview
- ComfyUI API patterns: `https://www.viewcomfy.com/blog/building-a-production-ready-comfyui-api` · `https://www.bentoml.com/blog/comfy-pack-serving-comfyui-workflows-as-apis`
- Replicate sprite model example: `https://www.aimodels.fyi/models/replicate/flux-sprites-miike-ai`
