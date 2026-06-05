# Benchmark Plan — CLI Rendering Techniques

## Purpose
Measure readability and performance for half‑blocks, braille, and image‑in‑terminal on Windows Terminal.

## Environment
- Windows Terminal; Cascadia Mono / Consolas
- Python 3.10+; venv; ANSI/Unicode enabled

## Metrics
- Median FPS; 95th percentile frame time
- CPU usage (rough), perceived flicker, artefacts
- Readability scores: eyes/mouth clarity; silhouette crispness

## Procedures
1) Half‑blocks
- Export 24×24 frames; compile:
  `python -m Graphics.Animations.tools.compile_scene Graphics/Animations/tools/scene_schema.yaml --width 100 --height 28 --mode 16 --out compiled_scene.json`
- Play:
  `python -m Graphics.Animations.tools.runtime_player compiled_scene.json`
- Record FPS (frame interval logs if added), visual notes.

2) Braille (Drawille)
- Run `Graphics/Animations/demos/drawille_demo.py` and note line quality, artefacts, CPU.

3) Image‑in‑terminal (optional)
- Evaluate a tiny GIF via term‑image or chafa/WSL; note clarity and latency.

## Acceptance thresholds
- FPS ≥ 12 median; <5% frames > 2× median frame time
- Readability pass on eyes/mouth and silhouette at 80–120 cols

## Reporting
- Save notes to `@filing/cli_research_log.md` with date, config, outcomes, decision.
