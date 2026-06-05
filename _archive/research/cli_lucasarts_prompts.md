# Prompt Kit — LucasArts‑style Pixel Art (for ComfyUI/SDXL/Flux)

## Style prompt (base)
"pixel art, LucasArts adventure game style, flat shading, bold 1px outlines, DB16 palette, bust portrait, 3/4 view, clean silhouette, plain background"

## Character anchor (append)
- Example: "male news anchor, brown hair, dark suit, red tie"
- Keep identity nouns constant across frames.

## Frame deltas (micro‑prompts)
- Neutral: "neutral expression"
- Blink: "eyes closed"
- Talk A: "mouth open small"
- Talk B: "mouth open wide"

## Negative prompt
"photorealistic, gradients, anti‑aliasing, high detail noise, bloom, lens effects, soft focus"

## Parameters (starting point)
- model: SDXL or Flux‑dev tuned for pixel art (add pixel‑art LoRA 0.5–0.8)
- steps: 20–30; sampler: Euler/Euler a; CFG: 3–5
- size: 24×24 (or 128×128 → nearest‑neighbour downscale to 24×24)
- seed: fixed; VAE fixed; IP‑Adapter/reference image weight 0.6–0.8

## ComfyUI JSON (illustrative overrides)
```json
{
  "workflow_api.json": "…",
  "overrides": {
    "positive": "pixel art, LucasArts adventure game style, flat shading, bold 1px outlines, DB16 palette, bust portrait, 3/4 view, clean silhouette, plain background, male news anchor, brown hair, dark suit, red tie",
    "negative": "photorealistic, gradients, anti-aliasing, high detail noise, bloom, lens effects, soft focus",
    "seed": 123456,
    "loras": [{"name": "pixel_art_lora", "weight": 0.7}],
    "ip_adapter": {"image": "ref.png", "weight": 0.7},
    "sampler": "euler_a",
    "steps": 24,
    "cfg": 4.0,
    "size": [128, 128]
  }
}
```

## Consistency checklist
- Fix: model, LoRA, seed, sampler, VAE, size.
- Keep base prompt constant; only vary micro‑prompt for expression.
- Use a single reference image via IP‑Adapter for identity.
- Batch generate all frames in one session to reduce drift.

## Troubleshooting
- Too many gradients/noise → raise LoRA weight; tighten negative prompt.
- Identity drift → increase IP‑Adapter weight; reduce CFG; reuse same seed.
- Blurry downscale → ensure nearest‑neighbour only; avoid bilinear/bicubic.

## Output spec
- PNG frames with alpha: neutral_*.png, blink_*.png, talk_*.png at 24×24/32×32.
- Next step: quantise to DB16 → half‑block encode → compile scene.

## References
- See ComfyUI API patterns in `@filing/cli_lucasarts_research.md`.
