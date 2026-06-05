# Day‑2 Spec — Team A (Engine & Rules)

Status: Draft
Owner: Team A

## Purpose
Consume `events.yaml` during the scene loop, display the referenced panel, and apply a single inject effect to metrics deterministically.

## Inputs and outputs
- Inputs: `data/scenarios/war_game_2025/events.yaml`, `assets/placeholders/*.md`
- Outputs: `engine/events.py` (loader + matcher), `engine/sim_loop.py` (call loader, log inject, apply effect)

## Allowed tools and permissions
- Edit Python under `engine/`

## Interfaces touched
- Read‑only world snapshot → event match
- Effect application: clamp updated metrics using `engine/utils.py`

## Steps (60–90 minutes)
- Implement `engine/events.py`:
  - `load_events(path) -> list[dict]`
  - `match_events(world, events) -> list[dict]` (match `scene_eq` == `world.scene`)
- In `engine/sim_loop.py`:
  - Load scenario events for `scenario_id`
  - Match and pick the first inject for the current scene
  - Log: `Inject: <id>`; display the panel by printing the first line of the `.md` file
  - Apply one effect deterministically:
    - If `delta: -4..-2`, choose the midpoint (−3)
    - Update the metric and clamp to [0,100]

## Acceptance tests
- CLI: `python -m cli.main --leader llm --seed 42`
  - Output contains `Inject: media_leak_01`
  - `domestic_stability` decreased by 3 from baseline
- Deterministic: same output with seed=42 across runs
- Gate Runner passes

## Prompt contract
- None

## Budgets and limits
- Time: 60 minutes

## Self‑check rubric
- No schema drift; functions local to `engine/`
- Handles missing files gracefully (log and continue)

## Handoff triggers
- If YAML structure needs schema, prepare a proposal and pause

