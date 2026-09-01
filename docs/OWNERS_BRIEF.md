# Owner's Brief — Situation Globe and VR Operations Room

This is the plain-language explanation. The canonical sequence and done tests
live in [`PLAN.md`](../PLAN.md); current engineering truth lives in
[`BUILD_STATE.md`](BUILD_STATE.md).

## What stays central

FALSE FLAG is already the game: the Prime Minister receives a crisis briefing,
questions five cabinet advisers, handles diplomatic pressure, makes a
free-form decision, receives pushback, and lives with the adjudicated
consequences over multiple turns.

The new work does not replace that experience. It makes the same campaign
spatial, connected to bounded live context, and present inside a VR operations
room.

Source: [README — What Happens in a Session](../README.md#what-happens-in-a-session).

## What the build adds

### A shared live campaign

The player, dashboard, globe and VR room observe one game session. Each screen
gets its own copy of permitted events, so opening a second display cannot steal
updates from the first.

The API session now gives every attached subscriber its own copy of each live
event. Only the first subscriber receives the pre-connect backlog, and late or
reconnecting displays still need the versioned theatre snapshot. The terminal
and static browser also remain separate engine instances. The build must prove
the shared player path before claiming “one engine, many surfaces.”

### Campaign geography

Every relevant unit receives a stored track. Authored places come from a
checked gazetteer; deterministic movement arithmetic advances units along
authored routes once per turn. The player sees intelligence estimates where
appropriate; the facilitator may see stored positions.

The player's decision can produce a bounded movement order, but the model never
writes coordinates. It may name a known unit, mission, destination and speed
band. The engine validates that text and ordinary kinematics writes the next
position. A bad reply creates no new order and cannot invent a location.

Source: [owner decision #71](https://github.com/earlyprototype/false-flag/issues/71).

### Live external context

The globe also receives genuinely live, fiction-neutral context. Weather is the
first feed; a bounded civilian-flight layer follows after its provider terms are
cleared.

Real feeds and fictional campaign entities remain separate. Outside the
exercise zone the real picture is visible; inside it the game's consequential
layers own the picture and fog carries the transition. Live facts may inform an
adviser's environmental context, but they never directly change a metric,
position, order or outcome.

One framing choice remains open before weather enters dialogue: the shipped
campaign is dated October 2025 while a live feed is observed now. The owner must
either rebase the campaign date, define current conditions as a present-day
exercise baseline, or keep them spectator-only. The UI and prompt must never
present one date as the other.

Source: [owner decision #77](https://github.com/earlyprototype/false-flag/issues/77).

### The VR operations room

The VR build puts the existing campaign into a three.js/WebXR room. The
situation globe is a world-locked screen; adviser presence and dialogue are
driven by the real campaign transcript.

The order is fixed:

1. Build the portable room and screen.
2. Measure that build on the real Quest.
3. If local rendering meets the measured budget, use an `XRQuadLayer`.
4. Otherwise keep the room and feed the screen from a server-rendered
   H.264/WebRTC stream.

The measurement selects where the screen pixels are produced. It does not
change the game, room or session contract.

[Owner ruling](https://github.com/earlyprototype/false-flag/issues/127#issuecomment-5498505180);
technical source: [WebXR Layers specification](https://immersive-web.github.io/layers/).

## Assessment of the route

| Slice | Value added | Assessment |
|---|---|---|
| Multi-client Session Streaming | Makes the played campaign, globe, dashboard and VR room agree instead of silently stealing events from one another. | Correct first dependency. First select and complete one API-backed player; streaming alone cannot prove this slice. Do not build two players. |
| Spatial Decision Loop | Turns the globe into gameplay: decisions move forces and geography can create later consequences. | Highest direct game value. The bounded-order and deterministic-coordinate route protects the simulation from model invention. |
| Live Context Integration | Makes the fictional crisis feel situated in the present world and gives advisers grounded environmental context. | Valuable only with a hard boundary. Weather first is the useful low-risk proof; civilian flights wait for provider permission. |
| Quest Ops-Room Display | Makes the existing cabinet game spatially present without creating a second game. | Correct route. Build the portable screen, measure the real headset, then choose the rendering path from evidence. |
| Demonstration Reliability and Submission | Proves the complete game survives presentation conditions and makes the Challenge contribution legible. | Essential throughout the build, not a final polish phase. The authentic turn remains the test. |

Overall, this route adds value because every slice strengthens the existing
decision loop. If a proposed task cannot improve that loop, make it more
legible, or make it more reliable, it does not belong in this build.

## What a complete demonstration is

It is one authentic FALSE FLAG turn:

1. Briefing with relevant live context.
2. Cabinet questioning, disagreement and pushback.
3. Diplomatic pressure where the campaign calls for it.
4. A free-form player decision.
5. Interpretation and adjudication by the existing engine.
6. Consequences visible in campaign state, on the globe and in the VR room.
7. The following turn begins from those consequences.

The dashboard may explain calls, sources and state changes, but it supports the
game; it is not the product.

## What exists now

- The full game loop, adviser system, diplomacy, adjudication and save/load are
  built.
- The Cesium globe is built and passed its projector test on 31 August 2026.
- Per-subscriber live streaming is built. A shared API player, reconnectable
  snapshot, moving tracks, live feeds and the VR room are not built yet.

Detailed status: [`BUILD_STATE.md`](BUILD_STATE.md).

## Reference map

- [Canonical plan](../PLAN.md)
- [Current engineering state](BUILD_STATE.md)
- [Current component map](XR_GLOBE_COMPONENT_MAP.md)
- [Full feasibility evidence](XR_GLOBE_FEASIBILITY.md)
- [Plain feasibility findings](XR_GLOBE_FEASIBILITY_IN_BRIEF.md)
- [Technology briefs](tech/README.md)
