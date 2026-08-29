# Handover — Situation Globe, morning of 29 Aug 2026

For whoever picks this up: the owner, or a fresh session. Two minutes of reading. Nothing needs reconstructing from chat logs.

## Read in this order

1. **[`PLAN.md`](../../PLAN.md)** (repo root) — the plan. Five stages, each with its build checklist, its done test, and its status. It is the only place the plan lives; update it there and nowhere else.
2. This file — what happened, what's waiting, what to do first.
3. [`docs/OWNERS_BRIEF.md`](../OWNERS_BRIEF.md) — plain-language explanation of what the thing is, if you're new to it.

## Where things stand

- **`main`**: carries the DTDL twin surface (PRs #65, #66, #68 merged) — `/dtdl`, the dataflow DTDL mode, the dashboard twin panel. **No Situation Globe code exists.** Nothing has been built.
- **PR #67** (`claude/vr-game-xr-simulation-feasibility-gomu1j`) — the feasibility record: study, plain-language brief, component map (5 diagrams), discards register, raw analysis output. Green, mergeable, out of draft.
- **PR #69** (`claude/xr-globe-planning`) — the plan and planning docs: `PLAN.md`, README pointer, owner's brief, decision briefs, build state, this handover. Green, mergeable, out of draft.

## Waiting on the owner

1. **The "go"** — authorization to write this project's first code (Stage 1, First Light). This is the only thing blocking build work.
2. **Merge PR #69** — puts `PLAN.md` and the README pointer on `main`, where anyone in the repo finds the plan immediately. One click.
3. **Four open decisions**, each with a working default so silence blocks nothing: [#72](https://github.com/earlyprototype/false-flag/issues/72) data-file location · [#73](https://github.com/earlyprototype/false-flag/issues/73) demo campaign cut · [#74](https://github.com/earlyprototype/false-flag/issues/74) default visual register · [#75](https://github.com/earlyprototype/false-flag/issues/75) Quest headset available (the VR diagram is drawn assuming yes).
4. **Fire the [Manus research queue](https://github.com/earlyprototype/false-flag/issues/70)** when convenient — its gazetteer verification task feeds Stage 2. Credits don't expire.

## If the answer is "go", the first work is

Stage 1 in `PLAN.md`. Concretely: create `api/globe.html`, serve it at `GET /globe` by FileResponse copying the pattern `api/server.py` already uses for `/dashboard`; load CesiumJS in the page; hardcode ~10 place-name→coordinate entries; call `GET /game/{id}/resources` and plot each unit at its named base; subscribe to one session event stream (**one consumer only** — see traps); add one vendored sensor shader and the EXERCISE chrome. Done when every unit sits at its real location on the projector and a game event visibly changes the display.

## Rulings that stand — do not re-open

- **Language**: documents state what a thing does, how, and why it matters. No metaphor. The words "truth" and "lie" were deliberately removed from every project document; don't reintroduce them.
- **The plan has one home**: `PLAN.md`. Other documents point at it. Never restate it.
- **Live-first**: the demo runs the real system. Simulated modes are CI test fixtures only — never a runtime the build retreats to. Non-determinism of play is the project's thesis, not a cost. The recorded demo film exists only for hardware failure.
- **Movement design settled** ([#71](https://github.com/earlyprototype/false-flag/issues/71), closed): the AI issues validated movement orders in fixed text; it never writes coordinates; any failure holds position. Only scheduling decides when it's built.
- **Sim/real boundary** ([#77](https://github.com/earlyprototype/false-flag/issues/77)): communicated spatially — a zone — and by fog register. Never text labels on the player's screen.
- **Position writes**: only two code paths ever write a coordinate — the gazetteer lookup at load, and the movement arithmetic at turn-resolve.

## Traps

- Any edit to `models/world.py` **must** be followed by `python3 dev-scripts/build_play_bundle.py` and the regenerated `docs/game.zip` committed, or exactly 4 tests fail on the packaging stamp.
- The session event stream is single-consumer today: two clients on one session steal each other's events. One consumer per session until the fan-out fix lands (Stage 3).
- Never edit the 13 published DTDL interfaces. New capability goes in new sidecar files, then re-run Microsoft's DTDLParser.
- CodeRabbit's "Merge Risk: Moderate" banner on #67 is **stale** — it assessed commit `3081816`; both issues it names were fixed in `4e7ff10`. Its review checkbox clears it.
- The claude.ai artifact page from the first analysis pass predates the plan rework. Refresh or retire it; the repository is the memory.

## What happened yesterday, in one paragraph

Two multi-agent analysis passes established feasibility (twelve claims, several proven by executing code against the real engine). The owner then reframed the work three times, each time enlarging it: feasibility means what can be *built*, not what current code supports; the VR aim is presence in an ops room rather than immersive terrain; and the map should carve a game zone inside genuinely live real-world data feeds, with the game reading live-derived facts as context. The movement decision was settled and closed. Two new capabilities were captured as issues: a real-email inject artifact (#76) and live-hybrid mode (#77). The documentation was rewritten twice — first into mechanical language, then into a single-source structure with `PLAN.md` at the root — after the owner correctly identified that the plan had no home and no visible status.
