# Anchor Zero — Character Concept Sheet (LucasArts‑style, CLI)

## Art direction
- Style: LucasArts adventure vibe; bold 1‑px outlines; flat shading; DB16 palette; 3/4 bust; plain background.
- Sprite size: 24×24 px (faces); design on a 2‑pixel vertical grid (half‑block friendly).
- Readability: eyes/mouth ≥ 2×2 px; strong silhouette; high contrast.

## Palette (DB16 selection)
- Outline: 0x140C1C (very dark)
- Hair: 0x854C30 (brown)
- Skin light: 0xDEEEDE; skin mid: 0xD2AA99; shadow: 0x8595A1 (subtle cool)
- Suit: 0x30346D (navy) + shadow 0x4E4A4E
- Shirt: 0xDEEEDE (light)
- Tie: 0xD04648 (red)
- Accent highlight (sparingly): 0xDAD45E

Terminal mapping: use nearest 16‑colour index per `nearest_terminal_index(rgb)`; enable 24‑bit when available.

## Silhouette & features
- 3/4 view; rounded hair mass with slight parting; jaw and neck clean shape.
- Shoulders squared; V‑shape suit; centred red tie knot; plain background band at top if needed.

## Layers (Aseprite)
- line (outline)
- fill_skin, fill_hair, fill_suit, fill_shirt, fill_tie
- shadow (shared)
- eyes, mouth (switchable)

## Animation vocabulary (frames)
- Idle bob: 2 frames, vertical offset ±1 px; period ≈ 16 frames.
- Blink: 2 frames (open→closed); insert every 60±20 frames.
- Talk: 2 frames (mouth small open, mouth wide open). Optional hold ratios 2:1.

## Tag map (Aseprite)
- Tags: neutral, blink, talk
  - neutral: 1 frame (base)
  - blink: 2 frames (open, closed)
  - talk: 2 frames (small, wide)

## File naming
- Source: `assets/anchor_zero/anchor_zero.aseprite`
- Exports: `assets/anchor_zero/frames/{tag}_{frame}.png` (24×24, transparent)

## Aseprite CLI exports
```bash
aseprite -b assets/anchor_zero/anchor_zero.aseprite \
  --save-as assets/anchor_zero/frames/{tag}_{frame}.png
```
```bash
aseprite -b assets/anchor_zero/anchor_zero.aseprite \
  --sheet assets/anchor_zero/sheet.png \
  --data assets/anchor_zero/sheet.json \
  --format json-array --list-tags --ignore-empty --sheet-pack \
  --filename-format {tag}_{frame}
```

## Runtime pipeline
1) Quantise PNGs to DB16 (if needed), then encode half‑blocks:
```bash
python -m Graphics.Animations.tools.compile_scene Graphics/Animations/tools/scene_schema.yaml \
  --width 100 --height 28 --mode 16 --out compiled_scene.json
python -m Graphics.Animations.tools.runtime_player compiled_scene.json
```

## ComfyUI prompt kit (for generated variants)
- Base: "pixel art, LucasArts adventure game style, flat shading, bold 1px outlines, DB16 palette, bust portrait, 3/4 view, clean silhouette, plain background"
- Character: "male news anchor, brown hair, dark suit, red tie"
- Deltas: blink="eyes closed"; talk A="mouth open small"; talk B="mouth open wide"
- Negative: "photorealistic, gradients, anti‑aliasing, high detail noise, bloom, lens effects, soft focus"
- Params: steps 24, sampler euler_a, CFG 4.0, seed 123456, size 128×128 then nearest‑neighbour → 24×24, IP‑Adapter ref 0.7, pixel‑art LoRA 0.7.

## Consistency controls
- Fix: model/LoRA/seed/sampler/VAE/size. Use single ref image via IP‑Adapter.
- Keep base prompt constant; only change micro‑prompt for expression.
- Batch generate all frames in one session.

## Acceptance checklist
- Eyes/mouth state readable at 80–120 cols; silhouette crisp.
- DB16 quantisation + half‑blocks do not introduce fizzing.
- Runtime maintains ≥12 FPS with dirty‑region updates.

Links: see `@filing/cli_style_bible.md`, `@filing/cli_lucasarts_prompts.md`, `@filing/cli_lucasarts_research.md`.
