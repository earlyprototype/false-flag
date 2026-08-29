# Situation Globe — Build Plan

**This file is the plan. It is the only place the plan lives.** Everywhere else either points here or draws a picture of it. If you are picking this work up — new to it, returning to it, or handing it on — read this file and nothing else is required.

Each stage names **what gets built** and the **done test**: an observable fact you can watch happen. A stage is not finished because it feels finished; it is finished when its done test passes.

**Keep this file current**: when a stage completes, set its status to `DONE`, put the commit or PR in Evidence, and tick its build items. When something changes, change it here first.

---

## Status

| Stage | What it delivers | Status | Evidence |
|---|---|---|---|
| **1 · First Light** | The map page exists and shows the game's forces | `NOT STARTED` — awaiting the owner's "go" | — |
| **2 · The Fleet Moves** | Units have real positions that advance each turn | `NOT STARTED` | — |
| **3 · Standards on the Glass** | The map reads the digital-twin model; many screens can watch | `NOT STARTED` | — |
| **4 · Show-Safe** | The demo runs to a written sequence without improvisation | `NOT STARTED` | — |
| **5 · The Cabinet Orders the Map** | Decision text moves the forces | `NOT STARTED` — design settled ([#71](https://github.com/earlyprototype/false-flag/issues/71) closed: orders on); schedule-gated | — |
| **Afterwards** | Line-crossing events, fog, live-hybrid, email artifact, VR ops room | `NOT STARTED` | — |

**Dates**: challenge started 28 Aug 2026 · onsite 12 Sep at Irish Manufacturing Research · final 14 Sep.
**Cut order under time pressure**: Afterwards → Stage 5 → Stage 3. Stages 1, 2 and 4 are the floor.
**Nothing is built yet.** No stage has started; the first line of code needs the owner's authorization (see Stage 1).

---

## Stage 1 · First Light — *about a day*

**Build**
- [ ] `api/globe.html`, served at `GET /globe` by FileResponse — the pattern `dashboard.html` already uses
- [ ] CesiumJS satellite Earth in that page
- [ ] ~10 starter gazetteer entries (place name → coordinates), hardcoded for now
- [ ] Read `GET /game/{id}/resources` and plot every unit at its named base
- [ ] Subscribe to one live game event stream (one consumer only — the multi-screen fix comes in Stage 3)
- [ ] One vendored sensor shader; diegetic EXERCISE chrome

**Done test** — on the projector, every unit in the order of battle sits at its real location, and an event in the running game visibly changes the display.

**Needs first**: the owner's **"go"** — authorization to write this project's first code.

---

## Stage 2 · The Fleet Moves — *about a week*

**Build**
- [ ] `models/spatial.py` — `UnitTrack`, `MovementOrder`, `SpatialState` (including `order_log` and the fired-tripwire latch set)
- [ ] `gazetteer.yaml` — ~30 entries, each coordinate checked against a source (file location: [#72](https://github.com/earlyprototype/false-flag/issues/72))
- [ ] `engine/kinematics.py` — pure `advance(dt)` along authored route polylines, per-domain speed tables, no randomness
- [ ] Position hydration at game start and at load
- [ ] Red fleet's authored route legs
- [ ] `resolve_decision` advances positions once per turn and publishes a snapshot
- [ ] Save format 2.4 → 2.5, then the play-bundle rebuild that must follow any `models/world.py` edit
- [ ] Tests: kinematics units · save→load→resume equality · gazetteer covers every unit location

**Done test** — in a live campaign the red group advances every turn along its route; save at turn 3, reload, and positions are identical; the test suite is back at its 712-passed baseline.

**No AI is involved in this stage.** Costs nothing to run.

---

## Stage 3 · Standards on the Glass — *about a week*

**Build**
- [ ] `interop/models/theatre.json` — `Theatre;1` (one per session) and `TheatreAsset;1` (one per unit; position as telemetry with a source label), as **new sidecar files**; the 13 merged interfaces are never edited
- [ ] Microsoft DTDLParser re-run, its output committed
- [ ] `GET /theatre` — versioned snapshot endpoint with ETag
- [ ] Per-subscriber fan-out on the session event bus, with per-subscriber payload copies
- [ ] Globe reads `/theatre` plus stream notifications; DTMI badges bound to `/dtdl`

**Done test** — two browsers on the same session each receive every event (today one steals from the other); the parser reports PARSE OK with the new interface count; live model identifiers show over a moving map.

*This is the stage built for the IMR room — digital twins are their field.*

---

## Stage 4 · Show-Safe — *three to four days · not optional*

Hardens the **real** path. It is not a rehearsal of a simulated stand-in — that is a rule of this project.

**Build**
- [ ] Written start-to-finish demo sequence
- [ ] Restart drill, measured under 60 seconds
- [ ] Localhost binding plus authenticated proxy for anything reachable off the machine
- [ ] Two timed projector rehearsals of the actual demo
- [ ] Unattended booth-loop configuration decided **at rehearsal**, as a labelled choice, never a silent default
- [ ] If the email artifact ([#76](https://github.com/earlyprototype/false-flag/issues/76)) is in by then: a deliverability rehearsal
- [ ] One film recorded from a real run — hardware-catastrophe contingency only

**Done test** — one rehearsal executed start to finish against the written sequence with zero operator improvisation, and the film file exists.

---

## Stage 5 · The Cabinet Orders the Map — *about a week · schedule-gated*

Built only if Stage 4 is complete with at least three clear days before the onsite. **The design question is closed** — [#71](https://github.com/earlyprototype/false-flag/issues/71): orders on. Only the calendar decides whether it lands before 12 Sep.

**Build**
- [ ] `MOVEMENT` call family, seeded from a derived `crc32` (never a draw from the master RNG)
- [ ] Prompt and parser: labelled lines, ≤8 orders, terminal sentinel, whole block discarded if the reply is truncated
- [ ] Validation against the unit registry, the gazetteer, and the per-unit mission legality graph
- [ ] Hold-on-failure with a player-visible transcript line; mock driver answers `NO_ORDERS`
- [ ] Inject `movements:` list parsing
- [ ] Spatial context block on the deciding calls; player-facing calls receive the estimates view only
- [ ] One deliberate golden-test re-baseline commit

**Done test** — a committed decision naming a movement produces the matching `order_log` entry and the unit moves next turn; a deliberately garbled reply produces zero orders plus the visible note.

---

## Afterwards — post-competition, each buildable on its own

- [ ] Tripwire engine — declarative line-crossing predicates evaluated at the top of `get_turn_briefing`
- [ ] Fog of war and patrol tasking — `engine/intel_picture.py`, staleness-radius estimates, derived-seed noise
- [ ] Between-turn animation — snapshot-fed interpolation daemon and `/geo/stream`
- [ ] Live-hybrid mode ([#77](https://github.com/earlyprototype/false-flag/issues/77)) — real live feeds with a carved-out game zone
- [ ] Real-email inject artifact ([#76](https://github.com/earlyprototype/false-flag/issues/76)), if not taken at Stage 4
- [ ] VR ops room — portable screen build, then the on-device measurement, then quad-layer or streamed source

---

## Gates

| Gate | Question | Effect |
|---|---|---|
| **Go** | Owner authorizes the first code | Starts Stage 1 |
| **Schedule check** (after Stage 2) | On schedule? | Yes → Stage 3 · Behind → skip to Stage 4. Standards chrome is droppable; a rehearsed demo is not |
| **Stretch gate** (after Stage 4) | Stage 4 done and ≥3 clear days left? | Yes → Stage 5 · No → Stage 5 moves to Afterwards |

Gates are schedule instruments only. No design questions remain inside them.

## Open questions and parallel work

Decisions still open, each with a working default so silence never blocks a stage: [#72](https://github.com/earlyprototype/false-flag/issues/72) which folder the map's data files live in · [#73](https://github.com/earlyprototype/false-flag/issues/73) which campaign cut the judges watch · [#74](https://github.com/earlyprototype/false-flag/issues/74) the globe's default visual register · [#75](https://github.com/earlyprototype/false-flag/issues/75) whether a Meta Quest headset is available.

Running alongside, off-branch: the [Manus research queue](https://github.com/earlyprototype/false-flag/issues/70) — its gazetteer verification task feeds Stage 2.

## Where the detail lives

- **Why each choice** — the feasibility study and its twelve verified findings: `docs/XR_GLOBE_FEASIBILITY.md`, plain-language version `docs/XR_GLOBE_FEASIBILITY_IN_BRIEF.md`
- **The picture** — `docs/XR_GLOBE_COMPONENT_MAP.md` (what talks to what, how a position gets written, the turn cycle, the VR build order, these stages as a diagram)
- **What the game gains, in plain language** — `docs/OWNERS_BRIEF.md`
- **Session-to-session engineering state** — `docs/BUILD_STATE.md`
- **What was considered and cut** — `docs/XR_GLOBE_FEASIBILITY_DISCARDS.md`
