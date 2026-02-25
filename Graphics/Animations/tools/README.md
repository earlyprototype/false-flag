# Automated Asset Generation System

Automated pixel art generation using Google Gemini 2.5 Flash Image API.

## Overview

This system automatically generates pixel art assets from prompt files, with post-processing to ensure exact dimensions and DB16 palette compliance.

## Files

- **`generate_assets.py`** - Main script for automated generation
- **`image_processor.py`** - Image post-processing utilities (resize, palette conversion)
- **`../asset_generation_prompts.md`** - Prompts for main game assets (anchor frames, tiles, UI)
- **`../intro_sequence_prompts.md`** - Prompts for cinematic intro sequence

## Features

- ✅ Parses markdown prompt files to extract:
  - Asset prompts
  - Target dimensions (64×96, 16×16, 320×180, etc.)
  - Output filenames
  - Folder organization
- ✅ Prepends universal LucasArts style requirements to all prompts
- ✅ Generates images via Gemini 2.5 Flash Image API
- ✅ Post-processes images:
  - Resizes to exact pixel dimensions (nearest-neighbor)
  - Converts to DB16 palette (DawnBringer 16 colors)
  - Preserves PNG transparency
- ✅ Auto-organizes into correct folder structure
- ✅ Progress tracking with retry logic
- ✅ Logs failed generations for manual retry

## Requirements

```bash
pip install python-dotenv requests pillow numpy
```

## Setup

1. Ensure you have a `GOOGLE_API_KEY` in your `.env` file at project root:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. Verify API access to `gemini-2.5-flash-image` model

## Usage

### Run Full Generation

```bash
cd Graphics/Animations/tools
python generate_assets.py
```

This will:
1. Parse both prompt files
2. Display total asset count (32 assets)
3. Ask for confirmation
4. Generate all assets sequentially
5. Save to `assets/` directory with proper folder structure

### Output Structure

```
assets/
├── backgrounds/
│   ├── bg_war_room.png
│   └── bg_news_studio.png
├── ui/
│   ├── title_the_war_game.png
│   ├── episode_title_false_flag.png
│   ├── news_ticker_bg.png
│   └── lower_third_template.png
├── ui/icons/
│   ├── icon_map_marker.png
│   └── icon_clock.png
└── intro/
    ├── scene1_severomorsk/
    │   ├── bg_barents_sea_dark.png
    │   ├── sprite_submarine_silhouette.png
    │   ├── sprite_moon_crescent.png
    │   └── sprite_observer_binoculars.png
    ├── scene2_northwood/
    │   ├── bg_map_north_atlantic.png
    │   ├── bg_operations_room.png
    │   ├── sprite_commander_navy.png
    │   ├── icon_force_blue.png
    │   ├── icon_force_red.png
    │   └── icon_phone_ringing.png
    ├── scene3_cobra/
    │   ├── sprite_pm_stern.png
    │   ├── sprite_pm_back_of_head.png
    │   ├── sprite_pm_face_closeup.png
    │   ├── sprite_sweat_drop.png
    │   ├── sprite_advisor_seated_small.png
    │   ├── bg_uk_gov_iconography.png
    │   └── bg_war_room_table_perspective.png
    └── ui/
        ├── title_false_flag.png
        ├── subtitle_you_are_pm.png
        ├── ui_location_timestamp.png
        └── ui_dialogue_box.png
```

## Asset Statistics

- **Total Assets:** 32
- **From asset_generation_prompts.md:** 8 assets
  - 4× UI elements (320×64, 320×48, 640×32)
  - 2× Icons (16×16)
  - 2× Backgrounds (320×180)
- **From intro_sequence_prompts.md:** 24 assets
  - Scene I (Severomorsk): 4 assets
  - Scene II (Northwood): 6 assets
  - Scene III (COBRA): 7 assets
  - UI elements: 4 assets
  - Effects: 3 assets

## API Details

- **Model:** `gemini-2.5-flash-image` (stable)
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent`
- **Method:** `generateContent` with text prompt
- **Response:** Base64-encoded PNG image
- **Rate Limiting:** 1 second delay between generations

## Post-Processing Details

### Resizing Algorithm
- Uses PIL `Image.NEAREST` (no anti-aliasing)
- Scales to fit within target dimensions
- Centers on transparent canvas
- Crops/pads as needed

### DB16 Palette Conversion
- Euclidean distance color matching
- Maps each pixel to nearest of 16 colors
- Preserves full transparency (alpha=0)
- No dithering

### DB16 Palette Colors
```python
#140c1c  #442434  #30346d  #4e4a4e
#854c30  #346524  #d04648  #757161
#597dce  #d27d2c  #8595a1  #6daa2c
#d2aa99  #6dc2ca  #dad45e  #deeed6
```

## Error Handling

- Retries failed generations (2 attempts per asset)
- Logs failures to `failed_assets.txt`
- Continues on errors (doesn't stop entire batch)
- Displays summary at completion

## Timing

- Average: ~5-10 seconds per asset (API call + processing)
- Total estimated time: **~5-10 minutes** for all 32 assets
- Includes 1-second delays between generations

## Universal Style Prompt

All prompts automatically include:

> STYLE REQUIREMENTS: Classic LucasArts SCUMM engine adventure game aesthetic (1990-1995 era: The Secret of Monkey Island, Day of the Tentacle, Sam & Max Hit the Road, Full Throttle). MANDATORY specifications: DB16 palette ONLY (DawnBringer 16 colors - no other colors permitted), flat color fills with NO gradients, strong black pixel-perfect outlines on ALL shapes, NO anti-aliasing, NO blur, NO soft edges, sharp geometric forms, hand-drawn cartoon quality with bold readable silhouettes, expressive character design, clean composition suitable for VGA-era displays and modern CLI terminal rendering. Art style: comedic yet dramatic, exaggerated proportions, clear visual hierarchy, high contrast for readability. Technical: pixel-perfect edges, transparent PNG background where appropriate, exact dimensions as specified.

## Troubleshooting

### API Key Issues
```
ERROR: GOOGLE_API_KEY not found in .env file
```
- Verify `.env` file exists in project root
- Check key name is exactly `GOOGLE_API_KEY`
- Ensure no quotes around the key value

### Generation Failures
- Check API quota/rate limits
- Verify internet connection
- Review `failed_assets.txt` for specific failures
- Re-run script (already-generated files will be overwritten)

### Image Quality Issues
- Manually adjust specific prompts in markdown files
- Re-run generation for specific assets
- Post-process manually with `image_processor.py` functions

## Manual Re-processing

To re-process an existing image:

```python
from image_processor import process_generated_image, save_with_transparency
from PIL import Image

# Load image
img = Image.open('generated_image.png')

# Process
processed = process_generated_image(img, target_width=64, target_height=96, apply_db16=True)

# Save
save_with_transparency(processed, 'output_path.png')
```

## Notes

- Asset generation is **non-deterministic** - each run produces different results
- Some manual curation may be needed for final quality
- Generated images may require iteration on prompts for best results
- 3 assets have "unknown" folders (optional enhancement effects not in file organization)

---

**Last Updated:** 2025-10-27  
**Version:** 1.0  
**Compatible with:** Gemini 2.5 Flash Image API
