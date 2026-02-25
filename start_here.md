# Start Here — Collaborative Development Onboarding

Use this page to spin up a new session (human or model) and continue development.

## Read these first
- war.plan.md (overall plan and flags)
- Collaboration/methodology.md (teams, stage gates, workflow)
- Collaboration/icd_v0_1.md (interfaces and schemas)

## Your role
- Teams: A (Engine & Rules), B (Agents & Large Language Models), C (Scenario & Ingestion)
- You will be assigned a task file under `Collaboration/tasks/` and a Spec under `Collaboration/specs/`.

## What to follow (any team, any time)
1) Open your task file in `Collaboration/tasks/<task-id>.yaml` and its Spec in `Collaboration/specs/<task-id>.md`.
2) Follow the Spec exactly; keep outputs reproducible (seed=42) and pass acceptance tests.
3) Run gate checks before opening a pull request.
4) If you pause or hand over, fill a Handover Capsule in `Collaboration/handover/<task-id>.md`.

### Gate checks (one command)
- Setup (first time): `python -m pip install -r requirements.txt`
- Run: `python scripts/gate_runner.py`
- Output: see `Collaboration/gate_report.json` — all sections should be empty arrays.

## Constraints
- Follow the Interface Control Document types; do not change schemas without approval.
- Log any model calls with prompt/response hashes (if used); keep seeds stable.
- Store sources under @filing/ for provenance.

## Leader modes (for quick demo)
- `python -m cli.main --leader human`
- `python -m cli.main --leader llm --seed 42`
- `python -m cli.main --leader mixed`

### LLM provider selection (Team B)
- Environment variable `WARGAME_LLM` selects the provider used by the router.
  - `mock` (default): deterministic, local driver (no external API calls)
  - `offline`: returns no actions (simulates no model access)
- PowerShell examples:
  - Use default mock: `Remove-Item Env:WARGAME_LLM -ErrorAction SilentlyContinue`
  - Explicit mock: `$env:WARGAME_LLM = 'mock'`
  - Offline: `$env:WARGAME_LLM = 'offline'`

## Need a new task?
- Copy `Collaboration/spec_template.md` → `Collaboration/specs/<task-id>.md` and fill in.
- Create `Collaboration/tasks/<task-id>.yaml` describing id, team, status, branch, dependencies, and acceptance tests.
- Start a branch: `feat/<short-name>` and begin.

## Reporting
- Update your task YAML status (pending → in_progress → completed).
- Add short progress notes in your Handover Capsule when pausing.
- Coordinators check gate reports and merge readiness in daily review.

## Decision Charter
- See `Collaboration/decision_charter.md` for pre‑approved actions and when to escalate.


