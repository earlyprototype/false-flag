# 29 August 2026 Claude Session — Historical Record

> [!IMPORTANT]
> **Historical and superseded.** This file preserves the provenance and settled
> decisions of the 29 August Claude session. It is not a resume point, status
> report, task map or build plan. For current work, start with
> [`PLAN.md`](../../PLAN.md), [`docs/BUILD_STATE.md`](../BUILD_STATE.md),
> [`docs/OWNERS_BRIEF.md`](../OWNERS_BRIEF.md) and the
> [historical handover index](README.md).

## Provenance and sanitisation

- **Session date:** 29 August 2026.
- **Record date:** 30 August 2026.
- **Repository snapshot discussed:**
  [`42bf968`](https://github.com/earlyprototype/false-flag/commit/42bf968).
- **Sanitised recovery source:**
  [`fe344ec`](https://github.com/earlyprototype/false-flag/commit/fe344ec).
- **Session identifier:** `session_015NPEdfpJtAXR7sqKXHxQAQ`
  (Anthropic-hosted; requires the owner's account and is not independently
  retrievable).

The owner's reconciliation of the shared session states that all 213 visible
entries were reviewed; that reconciliation is not tracked in this repository.
The session identifier is provenance, not durable project memory. Any
credential text present in the source material has been excluded.

The workspace-local Claude transcript named
`b667bdbc-13f1-4187-bc39-e4b372908fd4.jsonl` covers earlier DTDL and
control-surface work from 27–28 August; it is not the 29 August session. Local
transcript summaries are not guaranteed to exist in a fresh clone. The tracked
planning snapshot from 29 August is
[`2026-08-29-SITUATION-GLOBE.md`](2026-08-29-SITUATION-GLOBE.md).

## Settled decisions preserved from the session

These decisions are historical design provenance. Their implementation status
and delivery order must be checked in the current entry points linked above.

### Product and architecture boundaries

- FALSE FLAG remains the game experience. Globe, live-data and VR surfaces
  extend that experience rather than define a separate dashboard product.
- The VR concept is an operations room with stylised advisers and a readable
  situation surface. Cesium remains in the FastAPI web surface and is displayed
  or streamed into the room; it is not embedded in the XR renderer.
- The demonstration path is live-first. Mock and simulated paths are test
  fixtures, while a recording is a hardware contingency.
- The published DTDL interfaces are extended with sidecars rather than edited
  in place.
- Models may emit named movement intent, but only checked gazetteer data and
  deterministic movement logic may write coordinates.
- The real/simulated boundary is conveyed spatially through the exercise zone
  and fog rather than through an explanatory screen label.
- Multi-screen event delivery requires independent subscriber copies because
  audience filtering may mutate a payload.

### Adviser advice, trust and private memory

- Each seated adviser receives an independent model call. Calls share the
  decision context, but each receives only that adviser's role, concerns,
  triggers and state; no adviser sees another's answer before responding.
- A decision-override penalty applies only to advisers who objected and must
  not be charged twice. Broader strategic-quality effects remain distinct from
  that objection path.
- `CharacterAttitude` and `NarrativeState.characters` remain separate from
  foreign-actor models and are the intended home for adviser stance and
  bounded private memory.
- Private adviser memory must survive save/load/resume and must not leak into
  another adviser's prompt, player-facing output or public telemetry.
- The agreed first verification boundary was one game type under both
  Mystery-disabled and Mystery-enabled conditions.
- [`ADVISOR_SENTIMENT_SYSTEM.md`](ADVISOR_SENTIMENT_SYSTEM.md) is historical
  design input for interpersonal triggers, not an approved implementation
  specification.

### Prompt and control-surface quality

- Prompt changes require evidence from the effective runtime prompt, context,
  route, output and parser result. Older prompts are comparison evidence, not
  a presumed correct baseline.
- Control surfaces should describe data and provenance clearly, provide
  usable zoom controls, and state the true scope of reset operations.
- Visual comprehension and accessibility were agreed as bounded acceptance
  criteria for description, zoom and reset behaviour, not as a separate
  product direction.
- Adviser independence, control-surface quality and the Situation Globe are
  separate concerns. None is a hidden prerequisite for another.

## Deliberately not carried forward

This historical record contains no current commit or issue status, dependency
table, branch-claim workflow, Kanbanger instructions, defect list or next-step
directive. Those details changed after 30 August and belong in the canonical
current documents. It also contains no credential or token text from the
shared session.
