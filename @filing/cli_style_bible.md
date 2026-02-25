# LucasArts‑style CLI Art Direction (Style Bible)

## Vision
- Retro LucasArts adventure vibe in a terminal: bold shapes, flat shading, tiny palette, strong silhouette.
- Readable at low resolution (24×24 or 32×32); expressive with 2–6 frames.

## Core principles
- Palette: DB16/EGA‑like. Use high‑contrast pairs; avoid near‑neighbours.
- Outlines: 1‑pixel dark outline around forms; break outline only at strong light edges.
- Shading: 2–3 tones per material (flat + shadow + small highlight). Prefer clusters over noise.
- Silhouette first: design the head/bust shape to be recognisable in 3/4 view.
- Feature scale: eyes/mouth ≥ 2×2 pixels at source resolution; keep pupils simple.
- Backgrounds: plain or single gradient band; never compete with foreground.

## Sprite specs
- Sizes: Faces 24×24; Busts 32×32. Keep to even heights to pair with half‑blocks.
- Grid: Align features to a 2‑pixel vertical grid (half‑block pair) to survive terminal encoding.
- Contrast: Face vs hair vs clothing must be separable on grayscale.

## Animation vocabulary (economy)
- Idle/bob: 2‑frame vertical bob ±1 pixel; period ~16 frames.
- Blink: 1–2 frames (open → closed → open). Trigger every 50–90 frames with variance.
- Talk: 2–4 visemes (closed / small open / wide open [/ side]). Keep jaw motion small.
- Holds: Use holds between changes; snap into extremes for clarity.

## Palette discipline
- DB16 swatches; lock ramps per material. Use palette swaps for quick variants.
- Dithering only for broad ramps; avoid single‑pixel noise in faces.

## Acceptance criteria (readability)
- Eyes and mouth state distinguishable at 80–120 cols.
- Silhouette recognisable in grayscale thumbnail.
- No shimmering/fizz in hair/face under half‑block encoding.

## References
- See `@filing/cli_lucasarts_research.md` for DB16 and terminal mapping.
- Precedents: `@filing/precedents_and_influences.md`.
