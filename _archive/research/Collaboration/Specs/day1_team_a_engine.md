# Day‑1 Spec — Team A (Engine & Rules)

Status: Draft
Owner: Team A

## Purpose
Create a minimal scene loop with deterministic seed handling and apply small illustrative effects, passing acceptance tests.

## Inputs and outputs
- Inputs: models/world.py, agents/advisors.py, agents/leader.py
- Outputs: engine/sim_loop.py (updated if needed), tests (later)

## Allowed tools and permissions
- Edit Python files under models/, engine/, agents/

## Interfaces touched
- WorldState(scene, metrics, flags, posture)

## Steps (60–90 minutes)
- Ensure engine/sim_loop.py applies chosen actions and logs metrics.
- Add clamp utilities for metrics (0–100) and use them.
- Add a simple gate function to assert determinism under seed=42.

## Acceptance tests
- Given seed=42 and leader=llm, transcript shows exactly one action and updated metrics.
- Metrics stay within [0,100].

## Prompt contract
- None (no model calls required for Day‑1).

## Budgets and limits
- Time: 60 minutes

## Retry/backoff and cache key
- Not applicable for Day‑1

## Self-check rubric
- Deterministic output under seed=42.
- No schema drift.

## Risks and rollback
- Keep edits small; revert if determinism breaks.

## Handoff triggers
- If determinism fails or schema change is needed, create a Handover Capsule.


