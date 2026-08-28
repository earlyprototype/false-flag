# The Owner's Brief — the Situation Globe, in plain language

*This is the translation layer. The other documents are deliberately dense — they exist so no engineer (human or AI) ever loses the thread between sessions. **This one is for you and anyone new to the project.** Plain here means mechanically concrete, not vague: every section says what actually exists, what changes it, and links to the deep version. (Deep links point at the feasibility branch until PR #67 merges, after which they're neighbours in this folder.)*

**Drill-down map**: [findings in plain language](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY_IN_BRIEF.md) · [full technical study](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md) · [visual component map](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md) · [decisions & tasks: issues #70–#75](https://github.com/earlyprototype/false-flag/issues) (the Manus research task queue plus the five open calls — each spelled out below) · [`BUILD_STATE.md`](BUILD_STATE.md) · [`DECISION_BRIEFS.md`](DECISION_BRIEFS.md)

---

## What we're building, in one paragraph

Right now, between turns, the game goes quiet — the cabinet argues, and nothing moves. We're adding **a live map of the war**: a satellite Earth on a big screen where the Russian Northern Fleet visibly sails toward Scotland while the players deliberate. The player's screen draws the *intelligence estimate* of enemy positions (fuzzy circles that sharpen when they task patrol aircraft); the facilitator's screen draws the *actual stored positions*. When the fleet crosses a line that matters — into the GIUK gap, within missile range of London — the game notices at the start of the next turn and makes it that turn's news.

## The two parts, mechanically

**1 · The screen** — a single web page, served the same way our existing dashboard is, that draws the game's state on a satellite Earth. It adds visual filters borrowed from the gods-eye-view project (clean satellite → CRT → night-vision → thermal, switched by the escalation score the game already computes), scripted camera moves when events land, and a permanent EXERCISE watermark. It only ever *displays* data; it cannot change the game. *(Deep: [study, Track A](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md#4-track-a--presentation-architecture) · [map, diagram 1](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md#1--system-overview--what-talks-to-what).)*

**2 · The position system** — a small new piece of game state. Concretely:

- A **lookup table** of ~30 real places (Faslane, the GIUK gap, Severomorsk…) with hand-checked coordinates. This is the only place coordinates ever come from.
- **One new record per unit** in the saved game: latitude, longitude, heading, speed, and its current order (e.g. "transit to GIUK_gap at cruise speed").
- Positions update at **exactly one moment each turn** — when the turn resolves — by ordinary movement arithmetic: speed × time along a pre-drawn route. No randomness, no AI, in that step.
- The AI's only involvement (and it's optional — decision [#71](https://github.com/earlyprototype/false-flag/issues/71): should the AI's movement orders move your forces?): after a decision it may emit text orders in a fixed format, e.g. `ORDER: HMS_Prince_of_Wales | transit | GIUK_gap | cruise`. The game checks every order against the fixed unit list and the lookup table; **an unrecognised or garbled order is ignored** — that unit keeps doing what it was already doing, and a visible note says so. The AI never writes numbers; if its call fails completely, no orders are issued and everything continues on its previous course.
- **Consequence of this design**: a failure can leave the map *out of date*, but nothing can ever put a *made-up position* on it. That's the whole safety argument, and it's structural, not a promise.

*(Deep: [study, Track B — the full spec](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md#4a-track-b--the-authoritative-spatial-layer) · [map, diagram 2 — the order pipeline](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md#2--track-b-mechanism--how-a-position-gets-written-and-why-no-failure-path-can-write-an-invented-one) · the save-file and turn-timing behaviour were verified by running the real engine code — [findings 9 & 10](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY_IN_BRIEF.md).)*

## The plan — what gets built, and what tells you it's done

Five stages. Each one is usable on its own, so stopping after any of them still leaves you something to show. Every stage names the thing that gets built and the thing you can *watch happen* that proves it works. Full engineering detail: [study §7](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md#7-the-plan--milestones-as-build-contents-and-exit-tests); the same five as a diagram: [component map §5](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md#5--milestones--build-contents-and-exit-tests).

**1 · First Light** *(about a day)*
Built: a single new web page the game server hands out at `/globe`, drawing the satellite Earth; a starter list of about ten places with their coordinates; the page reads the game's existing force list and puts every unit on the map at its base; it listens to a running game's live event feed; one sensor filter; the EXERCISE marking.
Done when: on the projector, every unit in the order of battle sits at its real location, and something happening in the game visibly changes the display.
*Needs: your "go" — authorization to write this project's first code. Nothing is built yet.*

**2 · The Fleet Moves** *(about a week)*
Built: the position record per unit; the ~30-place coordinate table, checked against sources; the movement arithmetic that walks each unit along its route; the red fleet's authored routes; the once-per-turn update when a turn resolves; save-file version bump and the packaging rebuild that must follow it; tests.
Done when: in a real campaign the red fleet advances every turn along its route; you save at turn three, reload, and the positions come back identical; the existing test suite still passes in full.
*No AI involved in this stage at all. Costs nothing to run.*

**3 · Standards on the Glass** *(about a week)*
Built: two new digital-twin description files (one per session, one per unit) added alongside the thirteen already merged — never editing those; Microsoft's validator re-run and its output committed; a state endpoint the map reads; the fix that lets more than one screen watch a game at once; live model badges on the map.
Done when: two browsers watching the same game each get every update (today one steals from the other); Microsoft's validator reports a clean parse; the badges show live model identifiers over a moving map.
*This is the stage built for the IMR room — digital twins are their field.*

**4 · Show-Safe** *(three or four days — not optional)*
Built: a written start-to-finish sequence for running the demo; a restart drill timed under a minute; the network lockdown for anything reachable beyond your laptop; two full timed rehearsals on a projector; the unattended booth configuration decided during rehearsal as a deliberate choice; one film recorded from a real run, kept only for hardware disaster.
Done when: you run one rehearsal start to finish following the written sequence without improvising, and the film exists.
*This hardens the real thing. It is not a rehearsal of a fake version — that is a rule of this project.*

**5 · The Cabinet Orders the Map** *(about a week — built only if stage 4 is finished with three clear days spare)*
Built: the AI order channel described above — the extra call, the fixed order format, the checks against the unit list and coordinate table, the ignore-and-tell-the-player behaviour on anything malformed, and the one-off test-baseline refresh that follows.
Done when: you commit a decision that names a movement and the unit moves next turn with the order recorded; and a deliberately mangled AI reply produces no movement at all plus a visible note saying so.
*The design question here is settled — [issue #71](https://github.com/earlyprototype/false-flag/issues/71) is closed: orders on. Only the schedule decides whether it lands before the onsite.*

**Afterwards** *(each buildable on its own)*: the line-crossing events, fog of war and patrol tasking, the between-turn animation, [live-hybrid mode](https://github.com/earlyprototype/false-flag/issues/77), the [real-email artifact](https://github.com/earlyprototype/false-flag/issues/76) if it hasn't landed sooner, and the VR ops room.

If time runs short, the cutting order is: the afterwards tier first, then stage 5, then stage 3.

## The four open questions

Each is a GitHub issue — answer by commenting and closing; each has a safe default if you stay silent.

1. **[#71 — Should the AI's orders move your forces?](https://github.com/earlyprototype/false-flag/issues/71)** (the order channel above: on, off, or read both designs first)
2. **[#72 — Which folder do the map's data files live in?](https://github.com/earlyprototype/false-flag/issues/72)** (beside the story episodes, or a separate technical folder)
3. **[#73 — Which campaign cut do the judges watch?](https://github.com/earlyprototype/false-flag/issues/73)** (full slow-burn vs quick-start; we can time both and pick)
4. **[#74 — First impression: bare satellite Earth or the CRT filter?](https://github.com/earlyprototype/false-flag/issues/74)** (both ship; this sets the default)

Plus one fact when you know it: **[#75 — is a Meta Quest VR headset available?](https://github.com/earlyprototype/false-flag/issues/75)** (a plain yes/no to record on the issue). And the research task queue for Manus lives in **[#70](https://github.com/earlyprototype/false-flag/issues/70)** (paste-ready briefs for the Manus research agent).

## Glossary

- **Gazetteer** — the ~30-place coordinate lookup table above; the only source of coordinates in the system.
- **Digital twin / DTDL** — a Microsoft standard for describing a system as structured data. The game already models itself this way (merged today); the map becomes a display of that model. IMR's home field.
- **Tripwire** — a line or circle on the map the game checks once per turn; a crossing becomes that turn's event.
- **Fog of war** — players see estimates (last confirmed position + a circle that grows with staleness); the facilitator sees the stored positions.
- **Position labels** — every dot on the map carries how it was produced: *updated this turn by the movement step*, *projected forward between turns*, or *estimate shown to the player*. Nothing displays without one.
