# Decision Charter — Pre‑approved Actions and Escalation Rules

Status: Active
Owner: Coordinator

## Purpose
Reduce unnecessary approval requests. Empower teams to act within clear guardrails. Escalate only when decisions change shared contracts or incur risk/cost.

## Pre‑approved (no prior permission required)
- Docs: edit/update files within your task/spec scope.
- Tests: add/adjust unit/integration tests that don’t change public APIs.
- Scripts: add small helper scripts under `scripts/` that don’t alter gate behaviour.
- Refactors: internal refactors that keep function/class/module public signatures stable.
- CI/Gates: fix flaky tests or typos that do not change acceptance criteria.
- Ingestion: add sources to `@filing/` with provenance; no external API keys beyond allowed list.

## Must ask first
- ICD changes: any modification to types, schemas, or cross‑team contracts.
- Gate changes: altering gate logic, acceptance thresholds, or required checks.
- Deps: adding new dependencies not listed in `requirements.txt`.
- External services/tokens: introducing a new provider, key, or paid service.
- Repo structure: moving/renaming top‑level files or directories.

## Escalation cadence
- If blocked > 15 minutes: post blocker in handover capsule and tag Coordinator.
- If acceptance tests can’t pass without contract change: open a short ADR note and request review.

## Definition of “small”
- A change touching ≤ 3 files, ≤ 150 LOC, no public API change.

## Communication
- Record decisions in PR description. No prior approval needed for pre‑approved items.



