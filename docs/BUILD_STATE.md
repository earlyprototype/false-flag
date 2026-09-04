# Current Build State

Current as of 4 September 2026. Start here after
[`PLAN.md`](../PLAN.md). Historical handovers are indexed separately in
[`docs/handover/README.md`](handover/README.md).

## Product centre

FALSE FLAG is the AI wargame. The existing campaign loop—briefing, five-adviser
discussion, diplomacy, free-form decision, pushback, adjudication and
consequences—is the product. The Situation Globe, live external context and VR
operations room extend that same game.

One person plays the Prime Minister. Classic, Immersive and Emergent are
presentation choices for that campaign. Mystery is an optional hidden-story
layer. The dashboard, dataflow view and globe are supporting surfaces, not
separate players.

Evidence: [README — What Happens in a Session](../README.md#what-happens-in-a-session)
and [GAME_DESCRIPTION — Core Gameplay](../GAME_DESCRIPTION.md#core-gameplay).

## Repository state

- The canonical execution sequence is [`PLAN.md`](../PLAN.md). Do not infer a
  competing sequence from a handover, feasibility snapshot or issue title.

## What is built

- A headless `GameManager` and complete multi-turn campaign loop.
- Five cabinet-adviser roles, conversational questioning, decision
  interpretation, pushback and critical-omission checks.
- Scripted and generated injects, diplomacy, adjudication, campaign memory,
  endings and save/load.
- Terminal and static-browser playing surfaces.
- A FastAPI session path with decision, diplomacy, save/load and SSE endpoints.
- Independent per-subscriber SSE queues for one session's connected surfaces.
- A per-session facilitator capability checked on each stream and
  session-scoped control request. The session ID grants player authority, is
  not authentication, and does not grant facilitator authority.
- A versioned, player-safe theatre snapshot with strong ETag revalidation; the
  globe restores from it and treats SSE as change notification.
- An observability dashboard, dataflow/DTDL view and control surface.
- Thirteen published DTDL interfaces.
- The shipped Cesium Situation Globe, completed in
  [PR #95](https://github.com/earlyprototype/false-flag/pull/95) and verified on
  the projector on 31 August.

## What is not built

- The globe plots static UK resource locations; it has no authoritative moving
  red-force tracks.
- The theatre snapshot is one common public snapshot. The local bearer
  capability protects facilitator controls and REFEREE data, but deployment
  authentication and user accounts are not built.
- The terminal CLI and static Pyodide browser each own their own engine session;
  they are not observers of a FastAPI session.
- The checked-in `frontend/` source has API calls, but its package metadata is
  absent, so the documented Next.js start commands do not work from this tree.
  It also omits the later-turn `POST /game/{session_id}/briefing` call required
  for injects, effects and mandatory encounters after turn one.
- No authoritative track model, kinematics module or validated movement-order
  path exists.
- No external live-data adapter exists.
- No WebXR room or on-device Quest measurement exists.

These gaps are ordered and tested in [`PLAN.md`](../PLAN.md).

## Load-bearing implementation facts

- Engine state remains the only authority. Displays hold read-only snapshots.
- An LLM may emit a named movement order but never a coordinate. Gazetteer
  hydration and deterministic kinematics are the only coordinate writers.
- Failed movement interpretation creates no new order; the last validated
  standing order remains active.
- Live external facts may inform adviser context but never mutate metrics,
  positions, orders or outcomes. The authoritative boundary is
  [issue #77](https://github.com/earlyprototype/false-flag/issues/77).
- Prompt use is still gated by the unresolved campaign-clock rule: current
  observations must not be presented as facts from the October 2025 scenario.
- The player experiences the live/fictional boundary spatially through the
  exercise zone and fog, not through literal explanatory labels. Spectator and
  recording surfaces retain diegetic `EXERCISE` marking.
- REFEREE data is filtered server-side. Routing, prompt-edit and future movement
  controls must not leave localhost without authentication.
- Every `models/world.py` change requires rebuilding `docs/game.zip`.
- Stable derived randomness uses `crc32`, never Python's process-salted
  `hash()`.
- Live-feed fixtures are for automated tests only. Runtime source failure is
  visible; the application does not silently substitute fake live data.

## Current focus

The first Shared Campaign proof passed on 4 September 2026. With the mock
provider, the existing dashboard started one campaign and the dataflow view
joined the same session. Both received live updates and restored the same
session after reload. Live-event history is not replayed after reload.

The next decision is which existing API-backed player to complete. The
checked-in Next source is not currently runnable and must not silently become
the product merely because it exists.

## Resume order

1. Read [`PLAN.md`](../PLAN.md).
2. Read this file.
3. Read [`OWNERS_BRIEF.md`](OWNERS_BRIEF.md) for the plain-language product
   extension.
4. Use [`XR_GLOBE_COMPONENT_MAP.md`](XR_GLOBE_COMPONENT_MAP.md) for the current
   data flow.
5. Consult [`XR_GLOBE_FEASIBILITY.md`](XR_GLOBE_FEASIBILITY.md) only for the
   technical evidence behind a decision; its dated analysis is not the current
   schedule.
6. Read the Kanbanger board through the MCP resource. Its canonical workspace
   is the outer `fogOfWar` folder, with `_kanban.md` and `.kanban.json` beside
   the `false-flag` repository. If it reports another folder or a missing board,
   stop and report the binding problem; do not create or hand-edit another
   board.
