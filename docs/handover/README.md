# Historical Handover Index

Files in this directory are dated handover or feature snapshots. They preserve
what an earlier session believed; they do **not** define current project status,
setup instructions or build order.

## Current entry points

1. [`PLAN.md`](../../PLAN.md) — canonical build sequence and done tests.
2. [`docs/BUILD_STATE.md`](../BUILD_STATE.md) — current implementation truth and
   known gaps.
3. [`docs/OWNERS_BRIEF.md`](../OWNERS_BRIEF.md) — plain-language product
   extension.
4. The Kanbanger board through `kanban://current-board` — task execution state;
   never hand-edit `_kanban.md`.

## Dated handovers

- [`2026-09-01-DELIVERY-SYSTEM-PM.md`](2026-09-01-DELIVERY-SYSTEM-PM.md) —
  delivery-system snapshot through PR #110. Its product ordering and dates are
  superseded by the current plan.
- [`2026-08-30-PROJECT-HANDOVER.md`](2026-08-30-PROJECT-HANDOVER.md) —
  sanitised historical record of the 29 August Claude session. It
  preserves provenance and settled decisions but no current status or next
  step.
- [`2026-08-29-SITUATION-GLOBE.md`](2026-08-29-SITUATION-GLOBE.md) — planning
  snapshot before Globe Display shipped and before the current live/VR sequence.

## November 2025 package

The remaining undated feature reports and package files were created around
8 November 2025. Some implementation explanations may still be useful, but
their statuses, priorities, setup steps, provider assumptions and next actions
are historical. In particular:

- `HANDOVER_SUMMARY.md`, `IMPLEMENTATION_STATUS.md`, `PLAYTEST_FEEDBACK.md` and
  `PHASE_3_COMPLETE.md` are status snapshots, not current reports.
- `SETUP_GUIDE.md` is Gemini-specific and is superseded by the root
  [README quickstart](../../README.md#quickstart) and
  [`docs/LLM_PROVIDERS.md`](../LLM_PROVIDERS.md).
- Files named `*_SYSTEM.md` may describe implemented systems or old proposals;
  verify every claim against current code before using it.

Broken links in the old package index to `SYSTEM_ARCHITECTURE.md`,
`GAME_DESCRIPTION.md`, `PLAYER_COMMANDS.md`, `DEVELOPMENT_WORKFLOW.md` and
`TESTING_GUIDE.md` were removed when this index replaced it; those files do not
exist in this directory.

## Rule for future handovers

Use an ISO-dated filename, state the branch/commit, link to the canonical plan
instead of restating it, and mark the handover superseded when a later one
replaces it.
