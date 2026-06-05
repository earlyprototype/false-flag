# Day‑4 Spec — Team A (Engine & Rules)

Status: Draft
Owner: Team A

## Purpose
Map key risk metrics onto boolean flags on `world.flags` and document the mapping. Keep determinism.

## Scope
- Add risk flag mapping derived from metrics thresholds (e.g., `escalation_risk >= 60 -> risk_escalation=true`).
- Keep adjudication deterministic; no behaviour change to selection.

## Acceptance tests
- Gate report stays clean.
- Determinism holds under seed 42.
- Flags present/absent consistently for threshold crossings.

## Notes
- Do not change public schemas; flags are additive.

## Implemented mapping (deterministic)
- `risk_escalation`: `metrics.escalation_risk >= 60`
- `risk_unrest`: `metrics.domestic_stability <= 40`
- `risk_alliance_fragile`: `metrics.alliance_cohesion <= 40`
- `risk_civilian_harm`: `metrics.casualties_civ > 0`
- `risk_military_losses`: `metrics.casualties_mil > 0`

Application points (post-clamp):
- After event inject effects are applied and clamped.
- After adjudication clamp before final transcript line.

Determinism: Flags are computed as pure functions of metrics with inclusive boundaries; no RNG used.


