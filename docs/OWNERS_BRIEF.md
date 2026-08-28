# The Owner's Brief — the Situation Globe, in plain language

*This is the translation layer. The other documents are deliberately dense — they exist so no engineer (human or AI) ever loses the thread between sessions. **This one is for you and anyone new to the project.** Plain here means mechanically concrete, not vague: every section says what actually exists, what changes it, and links to the deep version. (Deep links point at the feasibility branch until PR #67 merges, after which they're neighbours in this folder.)*

**Drill-down map**: [findings in plain language](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY_IN_BRIEF.md) · [full technical study](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md) · [visual component map](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md) · [decisions & tasks: issues #70–#75](https://github.com/earlyprototype/false-flag/issues) · [`BUILD_STATE.md`](BUILD_STATE.md) · [`DECISION_BRIEFS.md`](DECISION_BRIEFS.md)

---

## What we're building, in one paragraph

Right now, between turns, the game goes quiet — the cabinet argues, and nothing moves. We're adding **a live map of the war**: a satellite Earth on a big screen where the Russian Northern Fleet visibly sails toward Scotland while the players deliberate. The player's screen draws the *intelligence estimate* of enemy positions (fuzzy circles that sharpen when they task patrol aircraft); the facilitator's screen draws the *actual stored positions*. When the fleet crosses a line that matters — into the GIUK gap, within missile range of London — the game notices at the start of the next turn and makes it that turn's news.

## The two parts, mechanically

**1 · The screen** — a single web page, served the same way our existing dashboard is, that draws the game's state on a satellite Earth. It adds visual filters borrowed from the gods-eye-view project (clean satellite → CRT → night-vision → thermal, switched by the escalation score the game already computes), scripted camera moves when events land, and a permanent EXERCISE watermark. It only ever *displays* data; it cannot change the game. *(Deep: [study, Track A](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md#4-track-a--presentation-architecture) · [map, diagram 1](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md#1--system-overview--what-talks-to-what).)*

**2 · The position system** — a small new piece of game state. Concretely:

- A **lookup table** of ~30 real places (Faslane, the GIUK gap, Severomorsk…) with hand-checked coordinates. This is the only place coordinates ever come from.
- **One new record per unit** in the saved game: latitude, longitude, heading, speed, and its current order (e.g. "transit to GIUK_gap at cruise speed").
- Positions update at **exactly one moment each turn** — when the turn resolves — by ordinary movement arithmetic: speed × time along a pre-drawn route. No randomness, no AI, in that step.
- The AI's only involvement (and it's optional — [decision #71](https://github.com/earlyprototype/false-flag/issues/71)): after a decision it may emit text orders in a fixed format, e.g. `ORDER: HMS_Prince_of_Wales | transit | GIUK_gap | cruise`. The game checks every order against the fixed unit list and the lookup table; **an unrecognised or garbled order is ignored** — that unit keeps doing what it was already doing, and a visible note says so. The AI never writes numbers; if its call fails completely, no orders are issued and everything continues on its previous course.
- **Consequence of this design**: a failure can leave the map *out of date*, but nothing can ever put a *made-up position* on it. That's the whole safety argument, and it's structural, not a promise.

*(Deep: [study, Track B — the full spec](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY.md#4a-track-b--the-authoritative-spatial-layer) · [map, diagram 2 — the order pipeline](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md#2--track-b-mechanism--how-a-position-gets-written-and-why-no-failure-path-can-write-an-invented-one) · the save-file and turn-timing behaviour were verified by running the real engine code — [findings 9 & 10](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY_IN_BRIEF.md).)*

## The plan, as five moments

1. **First Light** — the map page exists: units from the game's force list plotted on the Earth, attached to a running demo game, on the projector. *(Needs nothing but "go".)*
2. **The Fleet Moves** — the position system above, minus any AI: authored routes only. The red fleet advances turn by turn; save/load keeps working. Zero running cost.
3. **Standards on the Glass** — small live badges show the map is reading the game's Microsoft-validated digital-twin model — the moment built for the IMR room. *(Deep: [finding 6](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_FEASIBILITY_IN_BRIEF.md).)*
4. **Show-Safe** — rehearsed run-sheet, self-playing attract mode, restart drill, and a recorded film of the demo as the fail-safe.
5. **(Stretch, gated by [#71](https://github.com/earlyprototype/false-flag/issues/71))** **The Cabinet Orders the Map** — the AI order channel above goes live: you type "surge the carrier group north" and the ships obey.

*(Milestones with their decision gates, visually: [map, diagram 5](https://github.com/earlyprototype/false-flag/blob/claude/vr-game-xr-simulation-feasibility-gomu1j/docs/XR_GLOBE_COMPONENT_MAP.md#5--milestones-and-decision-points-replaces-day-counting).)*

## The four open questions

Each is a GitHub issue — answer by commenting and closing; each has a safe default if you stay silent.

1. **[#71 — Should the AI's orders move your forces?](https://github.com/earlyprototype/false-flag/issues/71)** (the order channel above: on, off, or read both designs first)
2. **[#72 — Which folder do the map's data files live in?](https://github.com/earlyprototype/false-flag/issues/72)** (beside the story episodes, or a separate technical folder)
3. **[#73 — Which campaign cut do the judges watch?](https://github.com/earlyprototype/false-flag/issues/73)** (full slow-burn vs quick-start; we can time both and pick)
4. **[#74 — First impression: bare satellite Earth or the CRT filter?](https://github.com/earlyprototype/false-flag/issues/74)** (both ship; this sets the default)

Plus one fact when you know it: **[#75 — is a Quest headset available?](https://github.com/earlyprototype/false-flag/issues/75)** And the research task queue for Manus lives in **[#70](https://github.com/earlyprototype/false-flag/issues/70)**.

## Glossary

- **Gazetteer** — the ~30-place coordinate lookup table above; the only source of coordinates in the system.
- **Digital twin / DTDL** — a Microsoft standard for describing a system as structured data. The game already models itself this way (merged today); the map becomes a display of that model. IMR's home field.
- **Tripwire** — a line or circle on the map the game checks once per turn; a crossing becomes that turn's event.
- **Fog of war** — players see estimates (last confirmed position + a circle that grows with staleness); the facilitator sees the stored positions.
- **Position labels** — every dot on the map carries how it was produced: *updated this turn by the movement step*, *projected forward between turns*, or *estimate shown to the player*. Nothing displays without one.
