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
- **`?ionToken=...` upgrade path.** A token passed in the URL is set as
  `Cesium.Ion.defaultAccessToken`, and Cesium Ion photoreal imagery replaces
  the OSM tiles.
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
- **Data on the globe.** Units from `GET /game/{id}/resources` plot at their
  gazetteer bases as points with labels; any location the gazetteer cannot
  place goes to a visible UNRESOLVED tray, never an invented coordinate.
  Live updates arrive over the session's SSE stream (SERVER_STREAMING.md).

## The globe on the VR routes

- **Unity route (option A of #127): Cesium for Unity.** Cesium publishes an
  official Unity plugin, so on that route a globe on an in-room screen is
  supported product, not a hack.
- **WebXR route (option B of #127): open integration question.** CesiumJS
  itself has no WebXR mode (none as of 1.144; proof-of-concept PR #11372 in
  the CesiumJS repo is unmerged — `docs/XR_GLOBE_FEASIBILITY.md`). On this
  route the globe must render to an offscreen canvas textured onto the
  room's monitor mesh, which needs a proof of concept. See WEBXR.md.

## Decision state

The globe page as shipped is settled and live (Stage 1 of PLAN.md, DONE —
done test passed 31 Aug 2026). Which VR route carries the globe onto an
in-room screen is open (issue #127).
