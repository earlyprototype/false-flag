# Team B — Day 4 Handover Capsule

Status: completed
Branch: feat/day4-team-b
Spec: Collaboration/Specs/day4_team_b_agents.md

## What changed
- Router honours `WARGAME_LLM` with `mock` (default) and `offline` stub.
- Added golden transcript for seed 42 (mock) at `Collaboration/golden/mock_seed42_scene1.txt`.
- Gate runner extended with golden transcript check; ICD check verifies file existence.
- `start_here.md` documents `WARGAME_LLM` with PowerShell examples.

## Acceptance tests
- Gate report clean with default environment.
- Determinism holds under seed 42; golden transcript passes.

## How to verify quickly (PowerShell)
- Setup: `python -m pip install -r requirements.txt`
- Run gates: `python scripts/gate_runner.py`
- Optional provider tests:
  - Default mock: `Remove-Item Env:WARGAME_LLM -ErrorAction SilentlyContinue`
  - Explicit mock: `$env:WARGAME_LLM = 'mock'`
  - Offline: `$env:WARGAME_LLM = 'offline'`

## Notes
- Unknown `WARGAME_LLM` values fall back to mock.
- Offline mode returns no actions; seed smoke will fail if used during gates.


