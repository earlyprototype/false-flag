# FALSE FLAG Project Handover — 30 August 2026

This is the durable resume point after reconciling the public Claude session
from 29 August. It records context, decisions and work ownership. It does not
replace [`PLAN.md`](../../PLAN.md), which remains the delivery plan.

## Resume here

1. Read [`PLAN.md`](../../PLAN.md) for delivery order and acceptance gates.
2. Read [`BUILD_STATE.md`](../BUILD_STATE.md) for current engineering facts,
   implementation constraints and known defects.
3. Read the local Kanbanger board through its MCP tools. Never edit
   `_kanban.md` directly.
4. Claim one issue before creating its named branch. Finish through a pull
   request and move the Kanbanger task to `REVIEW`; only the owner moves it to
   `DONE`.

## Current repository state

- `main` was aligned with `origin/main` at commit `42bf968` before this
  reconciliation branch was created.
- PRs #65–#69 are merged. PR #68 carried the stacked #66 dashboard change to
  `main`. The DTDL model, `/dtdl`, the DTDL data-flow view and the dashboard
  twin panel are on `main`.
- No Situation Globe implementation exists. Its first code still requires the
  owner's explicit **go**.
- Issue #79 is the reconciliation work. Its branch is
  `docs/79-session-reconciliation`.
- The other branch names below are reservations, not pre-created branches.
  Create one only when an agent claims the corresponding Kanbanger task.

## Source and recovery status

The exact source is the public shared session:

<https://claude.ai/code/session_015NPEdfpJtAXR7sqKXHxQAQ>

All 213 transcript entries visible in that session were read during this
reconciliation. The page is provenance, not project memory; the decisions and
unfinished work are captured below and in GitHub issues #79–#86. Credential
text visible in the source was deliberately omitted.

The optional workspace-local Claude JSONL named
`b667bdbc-13f1-4187-bc39-e4b372908fd4.jsonl` is **not** this transcript. It
records earlier DTDL and control-surface work from 27–28 August. These
workspace-local summaries are also absent from a fresh clone:

- `Research/System/session-transcript-2026-08-27-handover.md`
- `Research/System/session-transcript-2026-08-28-review.md`

The tracked Situation Globe snapshot is
[`2026-08-29-SITUATION-GLOBE.md`](2026-08-29-SITUATION-GLOBE.md) and is
available in every clone.

Direct HTTP and headless-browser retrieval of the public session hit
Cloudflare. The connected Chrome session could read it. Use this handover
unless exact wording must be checked again.

## Decisions added by the final Claude discussion

### Advisor-specific decision advice

- `Role;1`, `Participant;1`, `kind=ai_agent` and `advisor_trust` already exist
  in the published DTDL model. This work does not justify editing those
  interfaces in place.
- `generate_advisor_pushback` currently makes one model call for a combined
  response covering five advisor roles. Each seated advisor must instead be
  called independently, reusing the existing `generate_group` fan-out path.
- Each call receives shared decision context plus only that advisor's role,
  concerns, triggers and current state. One advisor must not see another's
  response before answering.
- The existing decision-override penalty already charges only the advisors
  who objected. Preserve that path and do not charge them twice. A separate
  strategic-quality drift changes trust uniformly; issue #82 must make that
  broader state advisor-specific.
- `CharacterAttitude` and `NarrativeState.characters` remain the home for
  advisor stance and bounded private memory. Useful hidden-agenda, redline and
  trust patterns from foreign actors may be reused, but the two models must
  not be merged.
- The historical
  [`ADVISOR_SENTIMENT_SYSTEM.md`](ADVISOR_SENTIMENT_SYSTEM.md) supplies a
  candidate taxonomy for advisor-specific interpersonal triggers such as
  praise, dismissal, ignored warnings, hostility and firing attempts. It is a
  design input, not an approved implementation specification.
- Private advisor memory must survive save/load/resume and must not leak to
  another advisor, a player-facing call or public telemetry.
- Initial delivery covers one game type, verified with Mystery disabled and
  enabled.

### Prompt quality

- The owner reports that prompt quality has regressed.
- Old prompts are comparison evidence, not a presumed correct baseline.
- Audit the effective runtime prompt, context, route, output and parser result
  before changing production prompt text. Remediation issues follow confirmed
  findings.

### Control surfaces

- The data-flow view has incomplete description and source-traceability
  coverage and no zoom controls.
- Demo reset is unreliable and its current controls do not state their true
  scope.
- Visual comprehension and accessibility need a bounded audit after the
  description, zoom and reset changes land.
- The Situation Globe is separate from advisor independence and these
  control-surface changes. None of them is a hidden prerequisite for the
  Globe's owner gate.

## Work and branch map

| Issue | Deliverable | Branch to create when claimed | Depends on |
|---|---|---|---|
| [#79](https://github.com/earlyprototype/false-flag/issues/79) | Reconcile the 29 August session and handovers | `docs/79-session-reconciliation` | — |
| [#80](https://github.com/earlyprototype/false-flag/issues/80) | Rewrite the delivery plan in professional, mechanical language | `docs/80-delivery-plan` | #79 |
| [#81](https://github.com/earlyprototype/false-flag/issues/81) | Generate advisor pushback independently | `feat/81-independent-advisor-pushback` | — |
| [#82](https://github.com/earlyprototype/false-flag/issues/82) | Persist advisor-specific trust and private memory | `feat/82-advisor-trust-memory` | #81 |
| [#83](https://github.com/earlyprototype/false-flag/issues/83) | Audit runtime prompt quality and regression evidence | `audit/83-prompt-quality-regression` | — |
| [#84](https://github.com/earlyprototype/false-flag/issues/84) | Add data-flow descriptions, traceability and zoom | `feat/84-dataflow-traceability-controls` | — |
| [#85](https://github.com/earlyprototype/false-flag/issues/85) | Provide a reliable demo reset | `fix/85-control-surface-demo-reset` | — |
| [#86](https://github.com/earlyprototype/false-flag/issues/86) | Audit control-surface visual information and accessibility | `audit/86-control-surface-accessibility` | #84 and #85 |

Kanbanger tracks #79–#86 locally with the same issue, branch and dependency
contracts. Read it for live column state. The board was not synced to GitHub
while these issues were created because GitHub already holds the external work
contracts.

## Existing work not superseded

- [#15](https://github.com/earlyprototype/false-flag/issues/15), private
  advisor conversations, remains separate from decision pushback and private
  decision memory.
- [#17](https://github.com/earlyprototype/false-flag/issues/17), visible
  failure on an unparseable actor response, remains the highest correctness
  item.
- [#18](https://github.com/earlyprototype/false-flag/issues/18), safe CLI
  interruption, and [#64](https://github.com/earlyprototype/false-flag/issues/64),
  concurrent adjudication and cache coverage, remain separate.
- [#70](https://github.com/earlyprototype/false-flag/issues/70) is partially
  executed. Branch `origin/manus/issue-70` contains P1a commits `bc887ec` and
  `7b66a95` with the gazetteer dossier and derived-point arithmetic script.
  Review and reconcile those outputs before firing the remaining queue.
- [#71](https://github.com/earlyprototype/false-flag/issues/71) is closed:
  validated text orders may move forces; model output never writes
  coordinates; failure holds the prior position or course.
- #72–#75 remain the four non-blocking owner inputs for data location, demo
  cut, visual register and Quest availability. Their defaults and the separate
  save-downgrade decision live in
  [`DECISION_BRIEFS.md`](../DECISION_BRIEFS.md).
- #76 email artifacts, #77 live-hybrid operation and #78 voice production
  remain later or optional capabilities.

## Settled Situation Globe rulings

- Build the game experience required; do not restrict feasibility to current
  implementation.
- VR means presence in an operations room with stylised advisors around a
  high-fidelity globe. Cesium remains in the FastAPI web surface and is
  displayed or streamed into the room; it is not embedded in the XR renderer.
- The demo is live-first. Mock and simulated paths are test fixtures, not a
  runtime fallback. A recorded film is only a hardware contingency.
- Only gazetteer hydration and deterministic movement arithmetic may write
  coordinates.
- The real/simulated boundary is conveyed spatially through zone and fog, not
  by an on-screen text label.
- The 13 published DTDL interfaces are immutable. New theatre capability uses
  parser-validated sidecars.
- The current session event stream is a destructive single-consumer queue.
  Multi-screen delivery requires copied per-subscriber fan-out because
  `_stream_filter` mutates payloads.

## Known documentation defects and gaps

- [`CONTROL_SURFACE_GUIDE.md`](../CONTROL_SURFACE_GUIDE.md) says **Clear
  overrides** removes model and prompt changes. The implementation clears
  routing overrides only; prompt edits require individual node reset. Issue
  #85 owns the correction together with honest control labels.
- `DATA_LAYERS.md` is referenced by code but absent. A Kanbanger task already
  tracks it; do not silently invent a replacement inside unrelated work.
- [`ADVISOR_SENTIMENT_SYSTEM.md`](ADVISOR_SENTIMENT_SYSTEM.md) is a November
  2025 proposal despite its “implementation report” title. Its architecture,
  cost and latency estimates, constitutional claims and approval status are
  not current authority. Issue #82 may reuse its interpersonal trigger list
  only after checking it against current code and game intent.
- The first Claude artifact page predates the final plan rework. The repository
  and GitHub issues are authoritative.

## Exact next step

If issue #79 is still open, finish its branch, open the pull request if it is
absent, and merge it after review. Once #79 is closed, claim #80 in Kanbanger, create
`docs/80-delivery-plan` from current `main`, and apply the approved
professional-language rewrite without changing technical scope.

Issues #81, #83, #84 and #85 have no dependency on #79 and can be claimed by
separate agents. Start #82 only after #81; start #86 only after #84 and #85.
Do not start Situation Globe implementation until the owner explicitly says
**go**.
