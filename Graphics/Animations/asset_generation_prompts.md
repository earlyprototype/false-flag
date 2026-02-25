# CLI War Game - Asset Generation Prompts

Complete prompt collection for generating pixel art assets via AI image generation services (ChatGPT Plus, Midjourney, Stable Diffusion, etc.).

**Target Specifications:**
- Character sprites: 64×96 pixels
- Background tiles: 16×16 pixels
- Palette: DB16 (DawnBringer 16)
- Style: LucasArts adventure games (1990-1995)
- Format: PNG with transparency

---

## 🎨 UNIVERSAL STYLE PROMPT (Prepend to ALL Asset Prompts)

**CRITICAL: Include this style guide at the start of EVERY prompt below to ensure consistency.**

```
STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate, exact dimensions as specified.

---

[YOUR SPECIFIC ASSET PROMPT FOLLOWS BELOW]
```

**How to Use:**
1. Copy the STYLE REQUIREMENTS block above
2. Paste it at the START of each individual asset prompt below
3. Add "---" separator
4. Then add the specific asset prompt

**Example Combined Prompt:**
```
STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate, exact dimensions as specified.

---

64x96 pixel art character, professional news anchor, neutral expression, front-facing view, business suit with tie, clean professional appearance, upper body visible from waist up, suitable for terminal CLI rendering
```

---

## 1. NEWS ANCHOR CHARACTER (64×96)

### Priority: CRITICAL
**Folder:** `assets/anchor_zero/frames/`

### 1.1 Neutral Expression (Base)
**Filename:** `anchor_neutral_01.png`

```
64x96 pixel art character, professional news anchor, neutral expression, front-facing view, DB16 palette (DawnBringer 16 colors), LucasArts adventure game style circa 1990-1995, clean flat color fills with strong black outlines, no gradients or shadows, business suit with tie, clean professional appearance, upper body visible from waist up, suitable for terminal CLI rendering, retro gaming aesthetic, sharp pixel-perfect edges, no anti-aliasing
```

---

### 1.2 Serious/Concerned Expression
**Filename:** `anchor_serious_01.png`

```
64x96 pixel art character, professional news anchor, serious concerned expression, slightly furrowed brow, front-facing view, DB16 palette (DawnBringer 16 colors), LucasArts SCUMM engine style (Monkey Island, Day of the Tentacle), flat color blocking with black outlines, business suit with tie, broadcasting breaking news, upper body from waist up, retro adventure game aesthetic, no anti-aliasing, clean pixel art, sharp edges
```

---

### 1.3 Blink Frame
**Filename:** `anchor_blink_01.png`

```
64x96 pixel art character, professional news anchor, eyes closed blinking, neutral expression otherwise, front-facing view, DB16 palette (DawnBringer 16 colors), LucasArts adventure game aesthetic, flat color fills with black pixel outlines, business suit with tie, natural blink expression, upper body from waist up, classic 90s point-and-click style, clean pixel art, no gradients
```

---

### 1.4 Talk Viseme - "A" Sound (Wide Open)
**Filename:** `anchor_talk_a_01.png`

```
64x96 pixel art news anchor, mouth wide open "A" sound, speaking animation frame, DB16 palette (DawnBringer 16 colors), LucasArts style flat colors with black outlines, business suit with tie, front-facing view, upper body visible, retro gaming pixel art, no anti-aliasing, sharp pixel-perfect edges
```

---

### 1.5 Talk Viseme - "E" Sound (Horizontal)
**Filename:** `anchor_talk_e_01.png`

```
64x96 pixel art news anchor, mouth horizontal "E" sound, slight smile, speaking frame, DB16 palette (DawnBringer 16 colors), LucasArts adventure game style, flat colors with black outlines, business suit with tie, front-facing view, upper body, retro pixel art, clean edges, no gradients
```

---

### 1.6 Talk Viseme - "O" Sound (Rounded)
**Filename:** `anchor_talk_o_01.png`

```
64x96 pixel art news anchor, mouth rounded "O" sound, speaking animation, DB16 palette (DawnBringer 16 colors), LucasArts SCUMM style, flat color fills with black pixel outlines, business suit with tie, front-facing view, upper body from waist up, classic adventure game aesthetic, sharp pixel art
```

---

### 1.7 Talk Viseme - "F/V" Sound (Teeth/Lip)
**Filename:** `anchor_talk_fv_01.png`

```
64x96 pixel art news anchor, mouth showing teeth for "F" or "V" sound, lower lip against upper teeth, DB16 palette (DawnBringer 16 colors), LucasArts style flat colors with black outlines, business suit with tie, front view, upper body, retro pixel art, no anti-aliasing
```

---

### 1.8 Talk Viseme - "TH" Sound (Tongue)
**Filename:** `anchor_talk_th_01.png`

```
64x96 pixel art news anchor, tongue visible for "TH" sound, mouth slightly open, DB16 palette (DawnBringer 16 colors), LucasArts adventure game style, flat colors with black pixel outlines, business suit with tie, front-facing view, upper body, retro gaming aesthetic, clean pixel art
```

---

## 2. BACKGROUND TILES (16×16)

### Priority: HIGH
**Folder:** `assets/anchor_zero/bg/`

### 2.1 Far Background Tile (News Studio)
**Filename:** `tile_16x16.png`

```
16x16 pixel art tileable background texture, professional news studio wall, DB16 palette (DawnBringer 16 colors), dark blue-grey tones with subtle geometric panel pattern, seamless repeating tile on all four edges, LucasArts adventure game style, flat colors with minimal detail, suitable for parallax scrolling background layer, retro gaming aesthetic, no gradients, high contrast, broadcast environment theme
```

**Alternative (Bunker Theme):**
```
16x16 pixel art seamless tile, concrete military bunker wall texture with subtle panel lines and rivets, DB16 palette (DawnBringer 16 colors), dark grey and blue tones, geometric grid pattern, tileable on all edges, LucasArts SCUMM style, flat pixel art, Cold War command center aesthetic, high contrast, background layer for terminal CLI game
```

---

### 2.2 Midground Tile (Technical Overlay)
**Filename:** `mid_tile_16x16.png`

```
16x16 pixel art tileable texture, semi-transparent technical overlay pattern, diagonal stripes or subtle grid, DB16 palette (DawnBringer 16 colors), lighter grey tones with low contrast, seamless repeating tile on all edges for parallax midground layer, LucasArts style, subtle depth effect, retro pixel art, terminal-friendly, less detailed than background
```

**Alternative (Studio Equipment):**
```
16x16 pixel art seamless tile, broadcast studio equipment silhouettes, abstract monitor screens or control panel elements, DB16 palette (DawnBringer 16 colors), medium grey tones with blue accents, tileable pattern on all edges, LucasArts adventure game aesthetic, midground parallax layer, flat colors, lower contrast than far layer, retro gaming style
```

---

## 3. TITLE CARDS & UI ELEMENTS

### Priority: MEDIUM
**Folder:** `assets/ui/`

### 3.1 Main Title Logo
**Filename:** `title_the_war_game.png`
**Suggested size:** 320×64 pixels

```
Pixel art title logo "THE WAR GAME", bold military stencil font, DB16 palette (DawnBringer 16 colors), LucasArts adventure game title screen style, strong black outlines, red and grey color scheme, retro gaming aesthetic, suitable for terminal CLI display, clean pixel-perfect lettering, no anti-aliasing, dramatic presentation
```

---

### 3.2 Episode Title Card
**Filename:** `episode_title_false_flag.png`
**Suggested size:** 320×48 pixels

```
Pixel art text "Episode 1: False Flag", clean readable font, DB16 palette (DawnBringer 16 colors), LucasArts style subtitle text, white or light grey text on dark background, retro gaming aesthetic, terminal-friendly, pixel-perfect lettering, no gradients
```

---

### 3.3 News Ticker Background
**Filename:** `news_ticker_bg.png`
**Suggested size:** 640×32 pixels (or tileable 32×32)

```
Pixel art news ticker banner background, red breaking news bar, DB16 palette (DawnBringer 16 colors), flat solid color with subtle texture, suitable for scrolling text overlay, LucasArts style, retro broadcast graphics, terminal CLI compatible, clean pixel art
```

---

### 3.4 Lower Third Name Plate
**Filename:** `lower_third_template.png`
**Suggested size:** 320×48 pixels

```
Pixel art lower third name plate template, professional broadcast style, DB16 palette (DawnBringer 16 colors), dark semi-transparent bar with accent stripe, suitable for character name and title text overlay, LucasArts adventure game UI style, retro gaming aesthetic, clean pixel art, terminal-friendly
```

---

## 4. ICONS & INDICATORS

### Priority: LOW
**Folder:** `assets/ui/icons/`

### 4.1 Breaking News Icon
**Filename:** `icon_breaking_news.png`
**Size:** 16×16 or 32×32 pixels

```
16x16 pixel art icon, breaking news alert symbol, exclamation mark in circle or urgent warning graphic, DB16 palette (DawnBringer 16 colors), red and white colors, LucasArts UI style, bold clear design, retro gaming aesthetic, suitable for terminal display
```

---

### 4.2 Map Marker Icon
**Filename:** `icon_map_marker.png`
**Size:** 16×16 pixels

```
16x16 pixel art icon, map location marker pin, simple geometric design, DB16 palette (DawnBringer 16 colors), red or blue color, LucasArts adventure game UI style, clear readable at small size, retro pixel art, no anti-aliasing
```

---

### 4.3 Clock/Timer Icon
**Filename:** `icon_clock.png`
**Size:** 16×16 pixels

```
16x16 pixel art icon, clock or stopwatch symbol, simple circular design with clock hands, DB16 palette (DawnBringer 16 colors), white and grey tones, LucasArts UI style, clear at small size, retro gaming aesthetic, pixel-perfect edges
```

---

## 5. OPTIONAL: CUTSCENE BACKGROUNDS

### Priority: LOW (Future Enhancement)
**Folder:** `assets/backgrounds/`

### 5.1 War Room Interior
**Filename:** `bg_war_room.png`
**Suggested size:** 320×180 pixels

```
Pixel art background, military war room interior, large table with maps, screens on walls, DB16 palette (DawnBringer 16 colors), LucasArts adventure game background style (Day of the Tentacle, Sam & Max quality), flat colors with strong outlines, Cold War command center aesthetic, detailed but not cluttered, retro gaming style, suitable for character overlay
```

---

### 5.2 News Studio Set
**Filename:** `bg_news_studio.png`
**Suggested size:** 320×180 pixels

```
Pixel art background, professional news broadcast studio, desk with monitors, blue and grey color scheme, DB16 palette (DawnBringer 16 colors), LucasArts adventure game background quality, flat colors with black outlines, modern broadcast environment, retro pixel art style, suitable for anchor character overlay
```

---

## TECHNICAL NOTES

### Post-Generation Checklist:
- ✅ Verify exact dimensions (64×96 for characters, 16×16 for tiles)
- ✅ Check transparency (PNG alpha channel)
- ✅ Ensure seamless tiling for background tiles (test by repeating 3×3)
- ✅ Validate DB16 palette compliance (may need quantisation)
- ✅ Test in CLI pipeline before finalising

### File Naming Convention:
- Characters: `anchor_{tag}_01.png` (e.g., `anchor_neutral_01.png`)
- Backgrounds: `tile_16x16.png`, `mid_tile_16x16.png`
- UI: Descriptive names (e.g., `title_the_war_game.png`)

### Palette Reference (DB16):
```
#140c1c, #442434, #30346d, #4e4a4e,
#854c30, #346524, #d04648, #757161,
#597dce, #d27d2c, #8595a1, #6daa2c,
#d2aa99, #6dc2ca, #dad45e, #deeed6
```

---

## GENERATION WORKFLOW

1. **Generate via AI service** (ChatGPT Plus, Midjourney, etc.)
2. **Download and rename** according to conventions above
3. **Place in correct folders** within `assets/`
4. **Run post-processing script** (optional, for dimension/palette verification)
5. **Compile scene** using existing pipeline
6. **Preview** via `run_preview.vbs` or `run_preview.bat`

---

## PRIORITY ORDER

**Phase 1 (Immediate):**
1. News anchor character (all 8 frames)
2. Background tiles (far + mid)

**Phase 2 (Next):**
3. Title cards
4. News ticker UI

**Phase 3 (Future):**
5. Icons
6. Cutscene backgrounds

---

**Last Updated:** 2025-10-27
**Pipeline Version:** 64×96 character, 16×16 tiles, DB16 palette

