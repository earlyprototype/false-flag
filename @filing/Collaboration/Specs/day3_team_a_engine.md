# Day‑3 Spec — Team A (Engine & Rules)

Status: Draft
Owner: Team A

## Purpose
Move action effects out of the scene loop into a proper adjudication layer. Apply advisor‑provided `expected_effects` deterministically and clamp metrics.

## Scope
- Implement adjudication in `engine/adjudicator.py`.
- Add a small helper in `engine/rules.py` for deterministic midpoints.
- Wire adjudication into `engine/sim_loop.py` and remove hardcoded deltas there.

## Interfaces
- Input: `WorldState`, `List[AdvisorProposal]`, `rng`.
- Output: updated `WorldState` and transcript lines summarising applied effects.

## Behaviour
- For each chosen action:
  - For each `EffectRange(metric, delta_min, delta_max)` compute midpoint = floor((min+max)/2) deterministically.
  - Apply to `world.metrics[metric]` and clamp to [0,100].
  - Emit transcript line: `Adjudicated: <action_id> -> <metric> <+d> (-> <val>)`.
- Unknown metrics or invalid ranges: skip and emit `Skipped ...` line.
- No actions: adjudicator returns unchanged world and no lines.

## Non‑goals
- Scenario injects remain as implemented on Day‑2.
- No probabilistic sampling; strictly deterministic.

## Acceptance tests
- Gate runner clean.
- `python -m cli.main --leader llm --seed 42`:
  - Contains `Inject:` from scenario.
  - Exactly one `Action taken:` line (unchanged selection logic).
  - Contains one or more `Adjudicated:` lines reflecting midpoint effects.
  - Final metrics reflect inject + adjudication; all clamped.
- Determinism: two runs with seed 42 produce identical transcripts.

## Constraints
- Do not change public schemas.
- Keep code local to `engine/`.

## Handoff
- If additional risk/flag mapping is needed, propose on Day‑4.
