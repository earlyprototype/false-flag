# Situation Globe Feasibility — In Brief

This is the plain-language summary of the dated technical evidence in
[`XR_GLOBE_FEASIBILITY.md`](XR_GLOBE_FEASIBILITY.md). Current sequencing and
status live in [`PLAN.md`](../PLAN.md) and [`BUILD_STATE.md`](BUILD_STATE.md).

## What was studied

Whether FALSE FLAG can add a moving situation globe, authoritative campaign
positions, bounded live external context and a VR operations room without
allowing generated text or external feeds to corrupt game state.

The answer is yes, by extending the existing game rather than replacing it or
copying the whole God's Eye View application.

## Findings

1. **The globe already has a viable serving path.** A self-contained CesiumJS
   page served by FastAPI is simpler and more proven here than the incomplete
   Next.js build. That page shipped in
   [PR #95](https://github.com/earlyprototype/false-flag/pull/95).

2. **The current globe is only a display foundation.** It plots UK resources
   at authored bases. It does not yet hold authoritative moving tracks or show
   the red fleet advancing.

3. **Several displays cannot safely watch one session yet.** The API session
   owns one destructive queue, so subscribers silently divide the event stream.
   Per-subscriber fan-out and a reconnectable snapshot are required before the
   dashboard, globe and VR room can run together.

4. **Campaign positions can be safe engine state.** Authored coordinates come
   from a checked gazetteer; deterministic kinematics advances them along
   authored routes. The model may emit validated named orders but never a
   coordinate. This is the settled design in
   [issue #71](https://github.com/earlyprototype/false-flag/issues/71).

5. **Movement can become gameplay rather than decoration.** A player decision
   can move a unit, and a later boundary crossing can become the next briefing's
   news. Save/load must preserve the tracks, standing orders and fired
   tripwires.

6. **Live data is part of the build.** Weather is the first live input; one
   bounded civilian-flight layer follows. External facts may inform adviser
   context but never write campaign state. The game-zone and live-first rules
   are authoritative in
   [issue #77](https://github.com/earlyprototype/false-flag/issues/77).

7. **The right reuse from God's Eye View is small.** Reuse the conceptual
   fetch → validate → render pattern, source-health discipline and attribution
   practice. Do not port its large layer manager, Vite proxy surface, voice
   system or many feed-specific renderers. FALSE FLAG currently reuses only the
   pinned MIT thermal shader.

8. **The VR route is a screen inside the room.** Build the portable WebXR room
   first, measure it on the Quest, then use a local `XRQuadLayer` if the device
   result is good or a server-rendered H.264/WebRTC media layer if it is not.
   The WebXR standard explains why quad layers improve text and map legibility:
   [WebXR Layers specification](https://immersive-web.github.io/layers/).

9. **The full game remains the acceptance test.** Briefing, adviser debate,
   diplomacy, free-form decision, pushback, adjudication and continuing
   consequences must still work. The globe and room show that campaign; they do
   not reduce it to a technical pipeline.

## Data and licensing references

- [God's Eye View at the analysed commit](https://github.com/bilawalsidhu/gods-eye-view/tree/314a0e1)
- [God's Eye View data-source register at the analysed commit](https://github.com/bilawalsidhu/gods-eye-view/blob/314a0e1/DATA_SOURCES.md)
- [Open-Meteo licence](https://open-meteo.com/en/license)
- [OpenSky terms of use](https://opensky-network.org/about/terms-of-use)

Provider terms are independent of the MIT source-code licence. OpenSky in
particular requires written agreement for operational REST use; a flight feed
must not become demo-required until its intended use is permitted.

## Read next

- [Owner's plain-language brief](OWNERS_BRIEF.md)
- [Canonical build plan](../PLAN.md)
- [Current component map](XR_GLOBE_COMPONENT_MAP.md)
- [Full technical evidence](XR_GLOBE_FEASIBILITY.md)
