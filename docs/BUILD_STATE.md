# Build State — Situation Globe

Current as of 30 August 2026. This file records engineering state,
implementation constraints and known defects. The implementation plan and
stage status live only in [`PLAN.md`](../PLAN.md).

## Current state

- PR #67 (feasibility record) and PR #69 (plan and planning documents) are
  merged into `main`.
- `main` also carries the 13-interface DTDL twin model, `/dtdl`, the
  ◇ DTDL dataflow mode and the dashboard `Session;1` telemetry panel.
- No Situation Globe implementation exists. Stage 1 awaits the owner's
  explicit **go**.
- The final 29 August Claude discussion added separate advisor, prompt-audit
  and control-surface work. Its decisions and issue/branch map are in the
  [`30 August project handover`](handover/2026-08-30-PROJECT-HANDOVER.md).
- Movement architecture is settled by closed issue
  [#71](https://github.com/earlyprototype/false-flag/issues/71): validated
  textual orders may move forces; failures hold position.
- Open, non-blocking inputs are
  [#72](https://github.com/earlyprototype/false-flag/issues/72) data location,
  [#73](https://github.com/earlyprototype/false-flag/issues/73) demo cut,
  [#74](https://github.com/earlyprototype/false-flag/issues/74) visual register
  and [#75](https://github.com/earlyprototype/false-flag/issues/75) Quest
  availability. Their working defaults and the save-downgrade decision are in
  [`DECISION_BRIEFS.md`](DECISION_BRIEFS.md).
- The research queue is issue
  [#70](https://github.com/earlyprototype/false-flag/issues/70). Its P1a
  gazetteer dossier and arithmetic script exist on `origin/manus/issue-70`
  but have not been reconciled into `main`; review them before firing the
  remaining competition and technical research tasks.

## Constraints already verified

- The existing session stream is a destructive single-consumer queue. Stage 1
  uses one consumer per session. Stage 3 must add per-subscriber fan-out and
  copy each payload because `_stream_filter` mutates it.
- Only gazetteer hydration and deterministic movement arithmetic may write
  coordinates. AI output is text, then validation; failure writes nothing.
- Spatial save state includes tracks, orders, the order log and tripwire
  latches. Runtime mailboxes, interpolation and fog are reconstructed after
  load. Save/load/resume equality is a required check.
- Derived movement and fog seeds use stable `crc32`, never Python
  `hash()` or the campaign's master random stream.
- New Theatre capability uses sidecar DTDL interfaces. Never edit the 13
  published interfaces; re-run Microsoft's DTDLParser when sidecars land.
- Cesium runs in the FastAPI web surface. The GitHub Pages/Pyodide build has no
  API server. The VR room displays or streams that surface; Cesium does not
  enter the XR rendering pipeline.
- Quest performance is unproven until measured on a device.
- Any `models/world.py` edit requires
  `python dev-scripts/build_play_bundle.py` and a committed
  `docs/game.zip` rebuild.
- Before anything is reachable off localhost, routing, prompt-edit and future
  movement surfaces require authentication.
- Sessions are never evicted today. Subscriber queues and future daemons need
  lifecycle cleanup rather than deepening that leak.
- `intelligence.py` currently fabricates random distances; replace that
  before authoritative spatial state and the old intelligence path coexist.

## Durable evidence

- Technical authority: [`XR_GLOBE_FEASIBILITY.md`](XR_GLOBE_FEASIBILITY.md)
- Plain-language findings:
  [`XR_GLOBE_FEASIBILITY_IN_BRIEF.md`](XR_GLOBE_FEASIBILITY_IN_BRIEF.md)
- System diagrams: [`XR_GLOBE_COMPONENT_MAP.md`](XR_GLOBE_COMPONENT_MAP.md)
- Rejected and deferred alternatives:
  [`XR_GLOBE_FEASIBILITY_DISCARDS.md`](XR_GLOBE_FEASIBILITY_DISCARDS.md)
- Complete source workflows:
  [`audits/2026-08-28-xr-feasibility/`](../audits/2026-08-28-xr-feasibility/)
- Current resume point:
  [`handover/2026-08-30-PROJECT-HANDOVER.md`](handover/2026-08-30-PROJECT-HANDOVER.md)

The raw workflow files answer implementation “why” questions that the shorter
documents compress. Do not reconstruct those decisions from chat.
