# CesiumJS

CesiumJS is the open-source JavaScript globe engine: a WebGL 3D Earth with
imagery layers, terrain, entities and camera control, rendered in an ordinary
browser page. It is the engine behind this project's situation globe.

## How the shipped globe page uses it today

`api/globe.html`, served at `GET /globe` as one self-contained page with no
build step, is the live integration. Verified facts, from the file itself:

- **Pinned version 1.132.0**, loaded from cdnjs. `window.CESIUM_BASE_URL` is
  set before the library loads — it is where Cesium fetches its workers and
  assets from.
- **Keyless by default.** OpenStreetMap imagery over the default ellipsoid
  (`EllipsoidTerrainProvider`), so the page renders with zero accounts and
  zero tokens. The OSM attribution stays on screen in the Cesium credit line.
- **`?ionToken=...` imagery path.** A token passed in the URL is set as
  `Cesium.Ion.defaultAccessToken`; the explicit OSM layer is then omitted and
  `Viewer` uses
  [Cesium's documented default world imagery](https://cesium.com/learn/cesiumjs/ref-doc/Viewer.html#ConstructorOptions).
  This code does not request Google Photorealistic 3D Tiles. A URL-borne token
  lands in browser history, server access logs and referrer headers, so use a
  scoped or throwaway Ion token here, never a shared account credential.
- **FLIR filter.** One vendored MIT sensor shader
  (`api/static/thermal.shader.js`, from bilawalsidhu/gods-eye-view, licence
  retained in its header) runs as a Cesium `PostProcessStage`. Off by
  default — the FLIR pass is a look, not the reading surface. The server
  serves the shader as one named file so nothing else in `api/static/`
  becomes public.
- **CRT filter.** An inline green-phosphor `PostProcessStage` preview, also
  off by default. Decision #74 (default visual register) is ruled, 31 Aug
  2026: all resting-default options stay live behind switches; both filters
  are toggle buttons on the page.
- **Zoom controls (#107, review findings applied in PR #108).** The + / −
  buttons zoom along the view ray, clamped to ~2 km–20,000 km with amounts
  floored at zero so + can never move the camera the opposite way; the
  log-scale slider sets camera height via `setView` with orientation
  preserved, and tracks native wheel/pinch zoom through `camera.changed`.
- **Data on the globe.** The player-safe `GET /game/{id}/theatre` snapshot
  supplies turn, phase and units. Units plot at their gazetteer bases as points
  with labels; any location the gazetteer cannot place goes to a visible
  UNRESOLVED tray, never an invented coordinate. SSE events trigger a
  conditional snapshot fetch using its strong ETag
  ([SERVER_STREAMING.md](SERVER_STREAMING.md)).

## The globe in the VR room

The selected room route is WebXR. CesiumJS remains an ordinary flat renderer;
the room uses its output as the source for a world-locked screen.

Build the portable canvas-texture screen first and measure it on the Quest. If
local rendering meets the recorded budget, promote the panel to an
`XRQuadLayer`. If it does not, keep the room and replace only the panel source
with server-rendered H.264/WebRTC video. See [WEBXR.md](WEBXR.md) and the
[WebXR Layers specification](https://immersive-web.github.io/layers/).

## Decision state

The globe page as shipped is settled and live (completed foundation in
[`PLAN.md`](../../PLAN.md); projector test passed 31 Aug 2026). The room route
and measurement fork are settled. Quest availability remains open in
[issue #75](https://github.com/earlyprototype/false-flag/issues/75).
