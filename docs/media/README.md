# FALSE FLAG — terminal UI reference media

Visual reference for the Operation Tuman aesthetic language
(`cli/aesthetics.py`) and its choreographed cinematics layer
(`cli/cinematics.py`). Everything here is generated from the real
in-game frame generators — no mockups — via a recording Rich console
(80 columns, defcon theme unless stated), exported per frame as SVG and
rasterised with headless Chromium at 2x scale. All content is seeded, so
regeneration is deterministic.

Regenerate everything:

```
.venv/bin/python dev-scripts/render_media.py
```

Regenerate a subset by asset stem, e.g.:

```
.venv/bin/python dev-scripts/render_media.py title_sequence gameplay_collage
```

## Animated (GIF frame durations match the choreography timings in `cli/cinematics.py`)

| Asset | Description |
| --- | --- |
| `title_sequence.gif` | The full title choreography (`title_frames`, seed 42): fog rolls in, the FALSE FLAG masthead condenses out of it cell by cell, breathes, wipes clean, then the classification strip stamps in, the tagline types word by word and the boot log ticks its `···· OK` lines. |
| `debrief_reveal.gif` | Campaign-ending condense (`condense_frames` with `play_debrief_reveal` tuning) of a plausible defeat frame: "THE GUNS OF OCTOBER — DEFEAT". |
| `turn_transition.gif` | A dense fog front sweeps left-to-right through the TURN 3 banner region (`turn_transition_frames`). |

Each GIF ends on a short presentational hold of the final resolved frame
(1.2–2.0 s) before looping; in the game the final frame simply persists.

## Static

| Asset | Description |
| --- | --- |
| `masthead.png` | The block-letter FALSE FLAG masthead between fog bands (`masthead`). |
| `boot_screen.png` | Completed secure-terminal boot over the resolved masthead (`boot_screen`). |
| `scene_card.png` | Scene I — Severomorsk Naval Base intro card with classification strip, coordinates and fog underline (`scene_card`). |
| `turn_phase_banners.png` | Heavy TURN 3 banner plus the four phase banners (BRIEFING / DISCUSSION / DECISION / ADJUDICATION) stacked (`turn_banner`, `phase_banner`). |
| `fog_densities.png` | `fog_band` at densities 0.2 / 0.5 / 0.9 — the escalation-weather ramp. |
| `sonar_dividers.png` | Five seeds of the sonar-trace section divider (`sonar_divider`). |
| `themes.png` | Masthead + Scene I card rendered in all five themes (defcon, standard, defcon1, retro, slate), stacked. |
| `gameplay_collage.png` | In-context recreation of live-game panels from the committed aesthetics vocabulary: BRIEFING banner + classification-strip intel header, the YOUR DECISION and OPERATIONAL ORDER panels, and SITUATION ASSESSMENT with ●○ vibe rows and a sonar divider. |

Notes:

- Rasters use the DejaVu Sans Mono / Liberation Mono stack so the full
  box-drawing and block-element set (`▄ ▀ █ ░ ▒ ▓ ● ○`) renders exactly.
- Pillow merges consecutive identical GIF frames on save (durations are
  preserved), so on-disk frame counts can be slightly below the
  choreography's frame count.
- `debrief_reveal.gif` is encoded at 1x scale (the 2x encode exceeded the
  8 MB per-GIF budget); the other GIFs and all PNGs are 2x.
