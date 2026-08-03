# The Operation Tuman Aesthetic Language

`cli/aesthetics.py` is the single source for the game's shared visual
language. The cold open is Operation Tuman — "Fog" — so every surface speaks
**fog + signals-room**: drifting shade-character fog banks, classification
strips, sonar contact traces, and secure-terminal chrome. Same language,
different weather each scene.

Preview everything: `.venv/bin/python dev-scripts/aesthetics_demo.py [theme]`

## Conventions

- **Return type**: every public function returns a Rich renderable (`Text` or
  `Group`). Print with `console.print(...)`. No plain-string markup APIs.
- **Determinism**: every generator takes `seed` (int or str). The same seed
  always yields identical output; there is no unseeded randomness. String
  seeds are hashed with CRC32 (never Python's randomized `hash()`).
- **Theme-aware**: colors are read from `cli.theme.theme_manager.get_colors()`
  at render time — never cached at import — so `/theme` switches apply
  instantly. Only universal keys are used (`primary`, `secondary`, `accent`,
  `muted`, `danger`, `warning`, `success`, `highlight`, `emphasis`).
- **Character discipline**: box-drawing, block elements, and geometric shapes
  only (all ≤ U+25FF, all cell-width 1). No emoji, ever.
- **Width**: default content width is `DEFAULT_WIDTH = 78` (theme `WIDTH` −
  2). All lines are `no_wrap` + `overflow="crop"`, so narrow or non-TTY
  consoles clip cleanly instead of wrapping or crashing.

## Components

| Function | Purpose |
| --- | --- |
| `fog_band(width, height, density, seed)` | Drifting fog texture band. `density` 0.0–1.0 (wire to escalation risk later). Smoothed 1-D value noise, not per-cell static. |
| `classification_strip(code, label, width, seed, edge)` | `┌─[ TOP SECRET ── UK EYES ONLY ]───[ COBRA/TU/03 ]─┐`. `edge` = `"top"`, `"bottom"`, or `"bare"`. |
| `reference_code(seed, prefix)` | Deterministic fictional reference, e.g. `COBRA/TU/07`. |
| `sonar_divider(seed, width)` | Sparse section divider: faint returns, blips, one strong contact `───●───`. |
| `masthead(width, seed, tagline)` | Hand-crafted block-letter FALSE FLAG title between fog bands. |
| `scene_card(number, title, location, timestamp, seed, width)` | Intro scene frame: classification strip + `SCENE I ── ...` + coordinates/timestamp + fog band. Int scene numbers become roman numerals. |
| `turn_banner(turn, seed, width)` | Heavy `━━━━[ TURN 3 ]━━…━[ CODE ]━━` rule with per-turn seeded fog trim above/below. |
| `phase_banner(phase, turn, seed, width)` | Light `──●──[ DISCUSSION · TURN 3 ]──…` rule fading into sonar returns. Phase colors: BRIEFING accent, DISCUSSION primary, DECISION emphasis, ADJUDICATION success. |
| `boot_sequence_frames(seed, width)` | List of full frames (secure-terminal boot lines over thinning fog, resolving into the masthead) for animated use, e.g. `rich.live.Live`. |
| `boot_screen(seed, width)` | Single static render of the finished boot (final frame). |
| `animate_boot(console, seed, delay, width)` | Convenience: prints the boot line-by-line with `delay`; prints the static screen instantly when stdout is not a TTY. |
| `debrief_frame(title, subtitle, lines, seed, width)` | Heavy double-ruled frame for campaign endings, with interior fog trim. |

## How seeding works

- `seed` may be an `int`, a `str`, or `None` (treated as 0). Strings are
  CRC32-hashed; sub-elements derive their own streams via an internal salt
  (hashed as a combined string — XOR of CRCs is avoided because CRC32 is
  linear and related seeds would collide).
- Components pick natural default seeds when none is given: `scene_card`
  seeds from the scene number + title, `turn_banner` from the turn,
  `phase_banner` from phase + turn. So each turn's banner trim is subtly
  different — deterministically.
- Recommended practice for callers: seed from stable game state (turn
  number, scene id, campaign seed), never from time or unseeded random, so
  replays and saves render identically.

## Typical wiring

```python
from cli.aesthetics import (
    animate_boot, scene_card, turn_banner, phase_banner,
    sonar_divider, debrief_frame,
)
from cli.rich_ui import console

animate_boot(console)                          # title / loading
console.print(scene_card(1, "Severomorsk Naval Base, Russia",
                         location="69°04'N 033°25'E",
                         timestamp="02 OCT 25 │ 03:15 LOCAL"))
console.print(turn_banner(world.turn))         # start of turn
console.print(phase_banner("DISCUSSION", world.turn))
console.print(sonar_divider(seed=f"{world.turn}-adv"))  # section break
console.print(debrief_frame("Uneasy Peace",
                            subtitle="The fog lifts.",
                            lines=debrief_lines, seed=campaign_seed))
```

Escalation-driven weather: pass
`density=world.metrics.escalation_risk / 100` to `fog_band` (or thread it
through a wrapper) so the fog literally thickens as the crisis worsens.

## Cinematics (`cli/cinematics.py`)

The animated layer on top of these primitives. Preview:
`.venv/bin/python dev-scripts/cinematics_demo.py [title|scene|turn|debrief|spinner|record]`

| Function | Purpose |
| --- | --- |
| `play_title_sequence(console, seed)` | The centrepiece (~6s): fog banks roll in, the FALSE FLAG masthead **condenses out of the fog** cell by cell in seeded scatter order, holds with a residual breathing shimmer, wipes thin top-to-bottom, then the classification strip stamps in, the tagline types word by word, and the boot log ticks through its `····· OK` lines. |
| `play_scene_stamp(number, title, location, timestamp)` | Intro scene card assembles fast (~0.6s): chrome first, then title/coordinates type in, then the fog underline. |
| `play_turn_transition(turn)` | A dense fog band rolls left-to-right through the turn banner region and clears (~0.8s). |
| `play_debrief_reveal(title, subtitle, lines, seed)` | Heavier, slower condense of the after-action `debrief_frame` for endings (~4s). |
| `condense_frames(renderable, seed, ...)` | Generic engine: captures any renderable as a styled cell grid and condenses it out of drifting fog. |
| `setup_banner(title)` | Static compact classification-strip header for setup menus. |

Contracts:

- **Deterministic content** per seed (timing uses the wall clock; frame
  content never does).
- **Any keypress skips** to the final frame (`cli.keyboard.key_pressed`).
- **Non-TTY stdout prints the final frame instantly** - zero sleeps - so
  piped runs, tests and CI stay fast; the printed frame is identical to the
  animation's last frame.
- Rendering is cortex-style raw ANSI in-place redraw (cursor-up + rewrite
  with per-line clear-to-EOL), not `rich.live.Live` - the game console runs
  `force_interactive=False` for its keyboard model and Live suppresses
  per-frame refreshes on non-interactive consoles. Legacy Windows consoles
  fall back to the static final frame.
- The LLM-wait spinner (`cli/spinner.py`) speaks the same language: a sonar
  ping sweeping a short trace (`[·•●······]`), silent on non-TTY.

## Interstitials (`cli/interstitials.py`)

Between-turn vignettes: short (3–6s, skippable) LucasArts-style ASCII
scenes in the Tuman register — dry Whitehall wit, a character, a timing,
a punchline. Played by `cli/main.py` after `TURN N COMPLETE`, before the
next briefing. Preview:
`.venv/bin/python dev-scripts/interstitials_demo.py [name] [escalation]`;
approval GIFs: `docs/media/interstitials/*.gif`
(regenerate with `dev-scripts/render_interstitials.py`).

| Vignette | The bit |
| --- | --- |
| `tea_round` | The aide's trolley crosses under the classification strip; cups labelled CDS/NSA/FS/HS/AG; the CDS cup's rattle scales with `escalation` (0–100); a cup is left on the floor: *YOURS, PRIME MINISTER.* Above 80 the aide simply keeps walking — *THE TROLLEY DID NOT STOP.* |
| `periscope` | Rises from a fog bank, sweeps left, right — then the lens `(●)` points straight at the viewer for a beat before the crash-dive and expanding ripples. *SIGHTING REPORTED — BY BOTH PARTIES.* |
| `teleprinter` | A JIC memo chatters out (burst-burst-breath rhythm, carriage-return beats) under progressively heavier `█` redaction until the last paragraph is solid black — leaving *PM EYES ONLY* and a tea-ring `( )` stain. |
| `red_phone` | `[ MOSCOW DIRECT ]` blinks; the Downing Street cat is already sitting on it; a shooing hand secures a relocation of exactly two columns; the blinking stops the exact frame the handset lifts. *LINE OPEN. CAT UNMOVED.* |
| `radar_room` | Sweep and contact blips; the closing contact resolves to `~v~` and exits screen-left. *CONTACT RECLASSIFIED: GULL (FORMAL COMPLAINT LODGED).* |

API: `play_interstitial(console, seed, escalation, name, avoid)` — seeded
selection when `name` is None; pass the previous pick as `avoid` so the
same joke never plays twice in a row (the function returns what it
played). `build_interstitial(name, seed, escalation)` exposes the frames
and the characteristic final still for tests and recording. Same
contracts as the cinematics: deterministic content per seed, any-key
skip, non-TTY prints the single still instantly, raw-ANSI in-place
redraw via the cinematics player.
