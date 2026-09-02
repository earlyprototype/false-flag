# Current Build State

Current as of 1 September 2026. Start here after
[`PLAN.md`](../PLAN.md). Historical handovers are indexed separately in
[`docs/handover/README.md`](handover/README.md).

## Product centre

FALSE FLAG is the AI wargame. The existing campaign loop—briefing, five-adviser
discussion, diplomacy, free-form decision, pushback, adjudication and
consequences—is the product. The Situation Globe, live external context and VR
operations room extend that same game.

Evidence: [README — What Happens in a Session](../README.md#what-happens-in-a-session)
and [GAME_DESCRIPTION — Core Gameplay](../GAME_DESCRIPTION.md#core-gameplay).

## Repository state

- The reviewed implementation baseline is
  [`631b082`](https://github.com/earlyprototype/false-flag/commit/631b082). It
  includes the delivery-system close-out in PR #133 and adviser pushback fan-out
  in [PR #123](https://github.com/earlyprototype/false-flag/pull/123).
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
- Independent per-subscriber SSE queues for one session's observers.
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
- The theatre snapshot is one common player-safe projection. Session IDs are
  not authentication, and per-viewer permissions are not built.
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

## Current external facts

- Challenge submission is due 13 September 2026 at 14:00 Irish time.
- The IMR regional demonstration is 14 September; the official pitch format is
  seven minutes plus three minutes of questions.
- Teams must contain 4–9 members including one team leader; current registration
  compliance has not been recorded in this repository.
- Unless an organiser maps FALSE FLAG to an official statement, it needs
  mentor approval as an alternative Challenge entry. That approval and the
  catalogue's wildcard evidence are not yet recorded.
- The existing game predates the challenge period. Submission material must
  distinguish it from work completed during 28 August–13 September.

Sources:
[official Participant Playbook](https://docs.google.com/document/d/1bYT1itRT6h0YU4i8uGbEUK78dJYa6z561qSe6tjSkNs/edit?usp=sharing),
[official Challenge Catalogue](https://docs.google.com/document/d/1D2rQhMPmqIFsCMyi_QPxVJCQQQYZ_phuHkdfz69UoX8/edit?usp=sharing), and
[AICC event page](https://www.aicc.co/events/2026/september-2026/techireland-national-ai-challenge-2026).

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
6. Read the Kanbanger board through the MCP resource. If it reports the outer
   `fogOfWar` folder rather than `false-flag/_kanban.md`, restart with the
   project-scoped MCP binding; do not create or hand-edit another board. Once
   correctly bound, reconcile the old #127 architecture-decision task with the
   selected WebXR route and closed GitHub issue.
