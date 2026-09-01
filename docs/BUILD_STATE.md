# Build State — Situation Globe (stock-take, 2026-08-31)

**Start here** if you are new to this or returning after a break. The canonical plan is [`PLAN.md`](../PLAN.md); the 29 Aug handover is historical context only: [`docs/handover/2026-08-29-SITUATION-GLOBE.md`](handover/2026-08-29-SITUATION-GLOBE.md).

**Purpose**: single resume point for engineering state. Any continuation — renewed agent session, different model, or the owner alone — starts here.

## Where things stand

- **`main` includes PRs #95–#99 and #101–#108.** It carries the full DTDL twin surface, the Stage 1 Situation Globe implementation (plus the URL fix #104, CRT filter #106, and manual zoom #108), the advisor-prompt and pushback fixes (#96/#97), the dashboard usability changes (#98), the P1a research salvage (#99), the in-repo kanban board (#101), and the three-stage CI pipeline with the verdict-gated review (#103).
- **Stage 1 · First Light is `DONE`** — the owner ran the projector done-test on 31 Aug and it passed ([#94](https://github.com/earlyprototype/false-flag/issues/94), closed). The owner gave GO on 30 Aug; implementation shipped in [PR #95](https://github.com/earlyprototype/false-flag/pull/95).
- **Movement architecture is settled.** [#71](https://github.com/earlyprototype/false-flag/issues/71) selected the hybrid validated-order channel; only scheduling remains.
- **In flight**: advisor-pushback fan-out ([#87](https://github.com/earlyprototype/false-flag/issues/87)) and the prompt-quality audit ([#83](https://github.com/earlyprototype/false-flag/issues/83)), dispatched 1 Sep on parallel lanes.

## The plan

Canonical, with per-stage status and done tests: **[PLAN.md](../PLAN.md)** at the repository root. Do not restate the plan here — update PLAN.md and link to it.

## Immediate next actions (in order)

1. Run Stage 1's projector done-test from `main`: every ORBAT unit appears at its named location and a live `state_update` visibly changes the globe.
2. Finish PR #99 review and CI; merge only after human approval.
3. Then start Stage 2 from [`PLAN.md`](../PLAN.md). The §4a degradation ladder is normative: bad lines are visibly skipped; failed calls issue zero new orders while standing orders continue and kinematics advances.

## Needs / open items

- Open working-default decisions: geo-pack location ([#72](https://github.com/earlyprototype/false-flag/issues/72)); demo variant ([#73](https://github.com/earlyprototype/false-flag/issues/73)); default visual register ([#74](https://github.com/earlyprototype/false-flag/issues/74)); Quest availability ([#75](https://github.com/earlyprototype/false-flag/issues/75)); save downgrade-loss acceptance.
- P1a gazetteer QA is present in PR #99; the remaining Manus queue stays in [#70](https://github.com/earlyprototype/false-flag/issues/70).
- DTDLParser re-validation once `Theatre;1` is authored (dotnet 8 + DTDLParser 1.1.3 — the pass-2 probe recipe).

## How to resume without the current session

Read, in order: this file → `XR_GLOBE_COMPONENT_MAP.md` (visual) → `XR_GLOBE_FEASIBILITY.md` (authority; §4a is the implementation spec, §3 the verified constraints) → `XR_GLOBE_FEASIBILITY_DISCARDS.md` (what was considered and cut, so it isn't relitigated). The raw agent outputs under `audits/` answer any "why" the docs compress.

## Historical record: session close, 2026-08-28 (late)

- **The seam (owner-confirmed)**: live-hybrid per-layer split; the game reads live-derived facts as context, never state — issue [#77](https://github.com/earlyprototype/false-flag/issues/77) (live-hybrid mode: real live data feeds with a carved-out game zone) is authoritative, including the **boundary-as-zone** design (no text labels on player surfaces; fog carries the reality boundary; diegetic EXERCISE chrome only where optics require) and the **live-first / no-fallback build posture** (non-determinism of play is the thesis; simulated modes are CI fixtures only; session journaling is AAR journalism, not replay-protection). Recorded demo film: **kept**, as hardware-catastrophe contingency only.
- **Real-email inject artifact** (a game inject delivered as an actual email): issue [#76](https://github.com/earlyprototype/false-flag/issues/76), MVP-worthy.
- **N1 (the movement-architecture decision) reframed mechanically** in issue [#71](https://github.com/earlyprototype/false-flag/issues/71) (should the AI's movement orders move your forces?) with the recommendation on record (orders on — completes the interpretation call the engine already runs and discards).
- **Language ruling enforced repo-wide**: mechanical language only (what/how/why); truth/lie metaphors removed from all docs on both branches.
- **Docs status at close**: study + map + in-brief + discards (PR #67) and owner's brief + this file + decision briefs (PR #69) all current. **Known stale**: the claude.ai artifact page (pre-dates the sprint-milestone rework, tonight's rulings, and the language sweep) — refresh it or retire it; the repo is the memory.
- **Superseded after this pause**: the owner gave GO on 30 Aug, #71 settled the hybrid, and Stage 1 shipped in PR #95. Decisions [#72](https://github.com/earlyprototype/false-flag/issues/72)–[#75](https://github.com/earlyprototype/false-flag/issues/75) retain working defaults.

## Planned DTDL additions (documented now, built at milestone M2)

The digital-twin model on `main` (13 interfaces) is not modified; new capability lands as versioned sidecar interface files auto-served by `/dtdl`. Planned: `Theatre;1` (one per session, relating the session to its map entities) and `TheatreAsset;1` (one per unit; position record as telemetry with a source label: adjudicated / simulated / estimated) — both already proven to parse clean in Microsoft's official DTDLParser (study claim 6; re-run the validator when the files land). Existing slots reused rather than extended: `WorldReference.environmentalFactors` carries live-derived environment facts (issue [#77](https://github.com/earlyprototype/false-flag/issues/77)), and the `Inject` channel/targets already describe the real-email delivery (issue [#76](https://github.com/earlyprototype/false-flag/issues/76)). Published interface versions are never edited in place.

## Historical record: end of session, 2026-08-28 (night)

**Where the plan lives now**: `PLAN.md` at the repository root is canonical — five stages, build checklists, done tests, status table, gates, cut order. README links it from the top. The owner's brief, this file, the study (§7) and the component map (§5) all point at it; none of them restate it. **Update PLAN.md first, always.**

**Repository state**
- This 28 Aug snapshot is superseded by the current state above ("Where things stand").

**Decisions and rulings recorded tonight**
- #71 **closed**: the hybrid validated-order channel is selected. Failed calls issue zero new orders; standing orders and kinematics continue. Only scheduling decides when it is built (stage 5).
- #77: live-hybrid seam confirmed as the design — per-layer real/simulated split, game reads live-derived facts as context and never as state; **boundary is spatial (a zone), never text labels**; fog carries it.
- **Live-first build posture**: the demo runs the real system; simulated modes are CI fixtures only, never a runtime the build retreats to. Non-determinism of play is the project thesis, not a cost. Recorded demo film kept, for hardware failure only.
- #76: real-email inject artifact, MVP-worthy.
- Language rule: mechanical statements of what/how/why. No metaphor ("truth", "lie") anywhere in project docs.

**Current correction:** [#72](https://github.com/earlyprototype/false-flag/issues/72) (geo files: SPLIT — scenario truth with the scenario, engine-derived with the tech, accounting across the seam) and [#74](https://github.com/earlyprototype/false-flag/issues/74) (visual register: all options stay live behind switches) are **ruled and closed**; [#73](https://github.com/earlyprototype/false-flag/issues/73) and [#75](https://github.com/earlyprototype/false-flag/issues/75) remain open. P1a from queue #70 landed via PR #99. Stage 1 is **DONE** — projector done-test passed 31 Aug.

**Known stale**: the claude.ai artifact page predates the plan rework; refresh or retire it. The repository is the memory.
