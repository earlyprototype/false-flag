# WebXR

WebXR is the W3C browser API for immersive experiences: a web page served over
HTTPS can enter a full VR (or AR) session on a headset directly from the
headset's browser. Nothing is installed on the device; the room is a URL.

## Role in this project

WebXR is **option B of the open VR route decision (issue #127)**: the
browser-delivered walk-in room. The owner's recorded vision (proposed
1 Sep 2026): you walk into a room with a screen; the advisors sit in the
seats; the screen loads the data layer virtually — delivered through the
headset's browser, nothing installed, continuous with the existing web stack
(the CesiumJS globe page, the Convai Web SDK, the same laptop server).
Option A is a Unity-native installed app. Both options render the same room
experience; #127 decides only the engine and delivery path.

## Strengths

- **Standalone delivery.** The headset's browser opens a URL on the laptop
  server. No build step, no store, no install on the device.
- **Continuity with the web stack.** This is a Python/web repo. The globe
  page, the streaming endpoints and the dashboards already exist as web
  surfaces; a WebXR room extends them rather than adding a second toolchain,
  and iteration stays a page refresh.

## The three known weaknesses

1. **Browser session lifecycle.** A browser VR session does not survive
   headset sleep or a page reload the way an installed app does. Re-entry
   after sleep/reload must be rehearsed before live use.
2. **Performance ceiling.** A browser-delivered room runs below what a
   native app can do on the same headset.
3. **The globe-on-a-screen integration.** CesiumJS is not VR-native: the
   library has no WebXR mode (none as of CesiumJS 1.144; the proof-of-concept
   PR #11372 in the CesiumJS repo is unmerged — `docs/XR_GLOBE_FEASIBILITY.md`,
   claim 1). The globe must render to an offscreen canvas that is textured
   onto the in-room monitor mesh. This integration needs a proof of concept.

## Verified supporting facts (`docs/XR_GLOBE_FEASIBILITY.md`)

- **Render-loop ownership.** `window.requestAnimationFrame` is not guaranteed
  to fire during an immersive session on standalone headsets. Cesium must run
  with `useDefaultRenderLoop: false` and have `viewer.render()` driven from
  `xrSession.requestAnimationFrame`, or the globe silently freezes in-headset.
- **Crisp text on the in-room screen.** Meta Quest Browser (≥16.1) supports
  XRQuadLayer: the compositor resamples the panel once, giving materially
  crisper text on a label-heavy screen. Desktop Chrome ships only
  XRProjectionLayer, so quad-layer benefits are Quest-only.
- **Unproven on-device performance.** CesiumJS running flat in the Quest
  browser at usable framerates is unproven; the feasibility study gates the
  local in-headset variants on an on-device check. The first smoke test in
  [QUEST3.md](QUEST3.md) answers exactly this.

## Decision state

Open — issue #127 (VR room delivery route: Unity-native or WebXR walk-in).
No default applies; the owner rules when ready. The hardware that would prove
either route is tracked in #75 (see [QUEST3.md](QUEST3.md)).
