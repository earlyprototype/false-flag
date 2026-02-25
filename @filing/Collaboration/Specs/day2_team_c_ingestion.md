# Day‑2 Spec — Team C (Scenario & Ingestion)

Status: Draft
Owner: Team C

## Purpose
Add one more early-scene media inject and a role brief stub; keep assets consistent and validated by gates.

## Inputs and outputs
- Inputs: public transcript references (use if available; not required for Day 2)
- Outputs: `data/scenarios/war_game_2025/events.yaml` (append), `data/scenarios/war_game_2025/role_briefs/uk_pm.md` (new), `assets/placeholders/*.md`

## Allowed tools and permissions
- Edit YAML under `data/scenarios/war_game_2025/`
- Add `.md` assets under `assets/placeholders/`

## Interfaces touched
- `events.yaml` fields: `when`, `trigger`, `channel`, `effects`, `image`

## Steps (60–90 minutes)
- Add `media_leak_02` for scene 2 with a small domestic stability effect
- Create `assets/placeholders/media_leak_02.md` and reference it
- Create `role_briefs/uk_pm.md` with a short objective/red lines stub

## Acceptance tests
- Gate Runner passes (asset is `.md` and exists)
- `events.yaml` loads; new id present

## Prompt contract
- None

## Budgets and limits
- Time: 60 minutes

## Self‑check rubric
- Paths and ids consistent; no duplicate ids

## Handoff triggers
- If role brief requires policy changes, propose and pause
