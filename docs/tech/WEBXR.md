# WebXR Operations Room

WebXR is the browser API used for the portable FALSE FLAG operations room. A
headset opens the room from the laptop server; the room observes the same game
session as the globe and dashboard.

## Selected build route

The current build order supersedes the earlier open-ended Unity-versus-WebXR
comparison in issue #127:

1. Build a portable three.js/WebXR room with a world-locked situation screen.
2. Measure it on the real Quest.
3. If local globe rendering meets the recorded device budget, use an
   `XRQuadLayer` for the screen.
4. Otherwise keep the same room and use a server-rendered H.264/WebRTC video
   source on a media quad layer.

This decision selects WebXR for the room. The device measurement selects only
the screen source. The 1 September 2026
[owner ruling](https://github.com/earlyprototype/false-flag/issues/127#issuecomment-5498505180)
is also recorded in [`DECISION_BRIEFS.md`](../DECISION_BRIEFS.md). Issue #127
is closed and remains useful as history, but it no longer defines the current
route.

## Why the room extends the game

- The campaign still runs in the existing engine.
- Adviser presence and dialogue come from the real campaign transcript.
- The situation screen displays the same session-scoped snapshot as the
  projector globe.
- VR does not create a second simulation or delegate adviser reasoning to an
  avatar service.

## Portable screen

CesiumJS has no supported immersive-WebXR globe mode. Its upstream
[WebXR implementation remains an open proof-of-concept PR](https://github.com/CesiumGS/cesium/pull/11372), so
the first build uses its ordinary canvas as the source for a screen inside the
three.js room.

Two implementation constraints from the feasibility study remain load-bearing:

- The immersive session owns animation timing. Cesium rendering must be driven
  from the XR session's animation frame while immersive mode is active.
- The canvas-to-texture update must occur in the same rendering task, or use an
  explicitly preserved buffer, so the copied frame is defined.

These are implementation constraints to prove in the portable build—not a
reason to choose the final screen source in advance.

## Quad-layer branch

An `XRQuadLayer` is a flat world-space composition layer. The compositor can
keep text and maps at a different resolution from the main eye buffer and
avoid unnecessary resampling. This is why it is the preferred branch if local
rendering passes the Quest measurement.

Primary source:
[WebXR Layers API Level 1](https://immersive-web.github.io/layers/), sections
“Introduction,” “XRQuadLayer,” and “Application flow.” Browser support remains
limited and must be tested on the target Quest rather than inferred from the
specification.

## Streamed-source branch

If local globe rendering misses the measured device budget, the laptop renders
the screen and sends H.264 video over WebRTC to a media quad layer. Only screen
content is streamed; head tracking and the room remain local. Any returned
input is an authenticated control surface.

## Device acceptance measurements

Record:

- frame rate and frame time;
- thermal behaviour over the intended session;
- text and map-label legibility;
- screen-input latency;
- reconnect behaviour after headset sleep or page reload;
- comfort and accessibility with motion and flicker controls.

The recorded result—not preference—selects the quad-layer or streamed-source
branch.

## References

- [Canonical XR Ops Room stream](../../PLAN.md#xr-ops-room)
- [Full feasibility evidence, “VR: the ops room”](../XR_GLOBE_FEASIBILITY.md#6-vr-the-ops-room)
- [Quest device brief](QUEST3.md)
- [WebXR Layers specification](https://immersive-web.github.io/layers/)
- [WebXR layer samples](https://immersive-web.github.io/webxr-samples/layers-samples/)
- [Meta Quest Browser overview](https://developers.meta.com/horizon/documentation/web/)
- [Meta Quest Browser feature-detection guidance](https://developers.meta.com/horizon/documentation/web/browser-specs/)
