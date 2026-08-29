# Handover — Situation Globe, 29 Aug 2026

This is the Situation Globe snapshot after PRs #67 and #69 merged. For the
current project-wide resume point, including the final 29 August Claude
discussion, use the
[`30 August project handover`](2026-08-30-PROJECT-HANDOVER.md).

## Read in this order

1. **[`PLAN.md`](../../PLAN.md)** (repo root) — the plan. Five stages, each with its build checklist, its done test, and its status. It is the only place the plan lives; update it there and nowhere else.
2. [`30 August project handover`](2026-08-30-PROJECT-HANDOVER.md) — the later Claude decisions, issue and branch map, and exact resume point.
3. This file — the Situation Globe snapshot.
4. [`docs/OWNERS_BRIEF.md`](../OWNERS_BRIEF.md) — plain-language explanation of what the thing is, if you're new to it.

## Where things stand

- **`main`** carries the DTDL twin surface and the complete Situation Globe
  feasibility and planning record from merged PRs #67 and #69.
- There are no open PRs. **No Situation Globe code exists.** Nothing has been
  built.

## Waiting on the owner

1. **The "go"** — authorization to write the first Situation Globe code (Stage 1, First Light). This is the only thing blocking build work.
2. **Four open decisions**, each with a working default so silence blocks nothing: [#72](https://github.com/earlyprototype/false-flag/issues/72) data-file location · [#73](https://github.com/earlyprototype/false-flag/issues/73) demo campaign cut · [#74](https://github.com/earlyprototype/false-flag/issues/74) default visual register · [#75](https://github.com/earlyprototype/false-flag/issues/75) Quest headset available (the VR diagram is drawn assuming yes).
3. **Review the existing P1a research** on `origin/manus/issue-70` before
   firing more work from [#70](https://github.com/earlyprototype/false-flag/issues/70).
   Its gazetteer dossier and arithmetic script have not yet been reconciled
   into `main`; accepted data feeds Stage 2.

## If the answer is "go", the first work is

Follow Stage 1 in [`PLAN.md`](../../PLAN.md). It owns the implementation
checklist and acceptance test; this snapshot does not maintain a copy.

## Rulings that stand — do not re-open

- **Language**: documents state what a thing does, how, and why it matters. Do not restore the prior metaphorical framing.
- **The plan has one home**: `PLAN.md` owns implementation order, checklists,
  gates and status. Supporting documents may summarize outcomes, but must link
  back rather than becoming an alternative plan.
- **Live-first**: the demo runs the real system. Simulated modes are CI test fixtures only — never a runtime the build retreats to. Non-determinism of play is the project's thesis, not a cost. The recorded demo film exists only for hardware failure.
- **Movement design settled** ([#71](https://github.com/earlyprototype/false-flag/issues/71), closed): the AI issues validated movement orders in fixed text; it never writes coordinates; any failure holds position. Only scheduling decides when it's built.
- **Sim/real boundary** ([#77](https://github.com/earlyprototype/false-flag/issues/77)): communicated spatially — a zone — and by fog register. Never text labels on the player's screen.
- **Position writes**: only two code paths ever write a coordinate — the gazetteer lookup at load, and the movement arithmetic at turn-resolve.

## Implementation constraints and known defects

- Any edit to `models/world.py` **must** be followed by `python3 dev-scripts/build_play_bundle.py` and the regenerated `docs/game.zip` committed, or exactly 4 tests fail on the packaging stamp.
- The session event stream is single-consumer today: two clients on one session steal each other's events. One consumer per session until the fan-out fix lands (Stage 3).
- Never edit the 13 published DTDL interfaces. New capability goes in new sidecar files, then re-run Microsoft's DTDLParser.
- PR #67 is merged, although GitHub retains its historical
  `CHANGES_REQUESTED` review decision. All seven review findings are
  addressed in the merged documents.
- The claude.ai artifact page from the first analysis pass predates the plan rework. Refresh or retire it; the repository is the memory.

## Later work captured that evening

The remainder of the public Claude session was recovered and turned into
issues #79–#86. It adds advisor-specific pushback, advisor trust and private
memory, an evidence-first prompt audit, and control-surface traceability,
reset and accessibility work. Those are separate workstreams, not Situation
Globe prerequisites. Their decisions, dependencies and branch names are in
the [30 August project handover](2026-08-30-PROJECT-HANDOVER.md).

## What happened yesterday, in one paragraph

Two multi-agent analysis passes established feasibility (twelve claims, several proven by executing code against the real engine). The owner then reframed the work three times, each time enlarging it: feasibility means what can be *built*, not what current code supports; the VR aim is presence in an ops room rather than immersive terrain; and the map should carve a game zone inside genuinely live real-world data feeds, with the game reading live-derived facts as context. The movement decision was settled and closed. Two new capabilities were captured as issues: a real-email inject artifact (#76) and live-hybrid mode (#77). The documentation was rewritten twice — first into mechanical language, then into a single-source structure with `PLAN.md` at the root — after the owner correctly identified that the plan had no home and no visible status.
