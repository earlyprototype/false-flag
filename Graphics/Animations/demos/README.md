# CLI Animation Demos

This folder contains runnable Python demos for low‑bitrate terminal animations using different libraries.

## Setup (PowerShell on Windows)

```powershell
# From repo root
cd Graphics/Animations/demos

# Create & activate a venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install deps
pip install -r requirements.txt
```

## Run

```powershell
# Blessed (talking head + ticker)
python blessed_demo.py

# Blessed half-block pixel sprite (LucasArts-style)
python pixel_sprite_demo.py

# Drawille (braille "pixel" graphics)
python drawille_demo.py

# Asciimatics (frame sequence)
python asciimatics_demo.py

# TerminalTextEffects (typewriter + slide)
python terminaltexteffects_demo.py

# Compile a YAML scene (DB16 + dither) and play it with loop/overlay
python -m Graphics.Animations.tools.compile_scene ..\tools\scene_schema.yaml --width 80 --height 28 --mode 16 --palette db16 --dither --out ..\..\..\compiled_scene.json
python -m Graphics.Animations.tools.runtime_player ..\..\..\compiled_scene.json --fps 14 --loop --overlay

# Background tiling + parallax is enabled via the background tile layer in the schema
# Quick compile + 12 FPS playback for 6s (no input)
python -m Graphics.Animations.tools.compile_scene ..\tools\scene_schema.yaml --width 80 --height 28 --mode 16 --palette db16 --out ..\..\..\compiled_scene.json
python -m Graphics.Animations.tools.runtime_player ..\..\..\compiled_scene.json --fps 12 --duration 6 --loop --overlay --noinput

# Benchmark pacing at 12–14 FPS for 60s
python -m Graphics.Animations.tools.benchmark_harness ..\..\..\compiled_scene.json --seconds 60 --fps 12 --loop
```

## Notes
- Stop a demo with Ctrl+C.
- For Drawille, use a monospaced font with good Unicode braille support.
- If output flickers, lower the frame rate (increase sleep) or avoid full clears.
- Asciimatics, Blessed, and TTE work in Windows Terminal/PowerShell.
- Runtime tips: `--duration 0` disables auto-close; use `--loop` to repeat and `--overlay` for a small HUD.
