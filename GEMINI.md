# GEMINI.md — Agent Context

FALSE FLAG: THE WARGAME — a political-military crisis simulation. The player is
the UK Prime Minister facing a Russian false flag operation; LLM-driven cabinet
advisors respond in character. Python, Typer CLI, Rich terminal UI.

Note for agents: the maintainer is a systems-thinking developer on a learning
journey — explain clearly, avoid jargon walls, and don't run code unless asked.

## Entry points

- `python -m cli.main play` — the game. All CLI logic lives in `cli/main.py`
  (`wargame_cli.py` at the root is a 4-line shim that just imports `cli.main:app`).
- `python -m cli.main batch` — batch runs for testing.
- `dev-scripts/play_campaign.py` — scripted campaign runner (dev tooling).

## Layout

- `engine/` — core simulation. `sim_loop.py` is module functions, not a class:
  `run_full_turn()` drives `run_turn_briefing/discussion/decision/adjudication()`.
  `scenario_loader.py` loads YAML from `data/scenarios/`; `persistence.py` is save/load.
- `agents/conversation.py` — advisor Q&A; integrated into the main loop (imported
  by `engine/sim_loop.py` and `engine/decision_phase.py`), not experimental.
- `llm/` — provider integration. `router.py` selects the driver
  (`gemini_driver`, `openai_compat_driver`, `mock_driver`, `offline_driver`);
  `prompts.py` and `context_builder.py` build the prompts. No config = mock mode.
- `models/world.py` — Pydantic state. `Metrics` persists exactly:
  `escalation_risk`, `domestic_stability`, `alliance_cohesion`, casualties.
  ("Influence" shown in `/status` is derived for display only, never stored.)
- `data/scenarios/war_game_2025/` — initial conditions + `episodes/turn_NNN.yaml` injects.
- `docs/` — the GitHub Pages browser build (engine compiled to WebAssembly).
- `audits/` — engineering-review (ER) register, measurement runs, handover notes.
  Check here first for known issues and prior investigation.

## Dev commands

```
python -m pytest tests/        # set PYTHONIOENCODING=utf-8 on Windows
python -m ruff check .
```

Setup: `python -m venv .venv`, install `requirements.txt`, optionally copy
`config.example.py` → `config.py` for a real LLM provider (see README).
