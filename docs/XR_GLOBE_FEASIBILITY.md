# Feasibility Study — The Situation Globe

**Integrating simulated gods-eye-view GEOINT layers into FALSE FLAG as a between-turn XR data layer**

*Study date: 2026-08-28 · Basis: this repository at `main` (35c11c0) plus the open DTDL PRs #65/#66, and [bilawalsidhu/gods-eye-view](https://github.com/bilawalsidhu/gods-eye-view) (MIT) at commit `314a0e1`. Produced by a multi-agent analysis: six codebase readers, three competing architecture designs, a three-lens judging panel, seven adversarially-verified feasibility claims, and a completeness critique.*

---

## 1. Verdict

**Feasible, high-value, and well-matched to this codebase — but as a port of ideas, not an embed of code.** The recommended shape is a **zero-build CesiumJS "situation globe"** (`api/globe.html`, served exactly like `dashboard.html`), fed by a **per-session ambient GEOINT simulator** daemon over a **new dedicated SSE endpoint**, vendoring only gods-eye-view's three GLSL sensor shaders and its scene-recipe camera grammar, with a **DTDL `Theatre;1` sidecar interface** making the globe a renderer over the twin model that PRs #65/#66 land.

Three findings frame everything:

1. **The "between-inject/turn" framing is architecturally exact.** The engine is provably quiescent between `resolve_decision` and the next `POST /briefing` — nothing runs. That dead time is free real estate an ambient simulator can own completely without racing the engine, using the already-sanctioned daemon-thread pattern from `api/demo.py`.
2. **The scenario is already geospatial in prose.** Geography is real-world (Portsmouth, Faslane, RAF Lossiemouth, Severomorsk, the GIUK gap — ~30 named places), so a hand-authored gazetteer (an afternoon of work) puts the existing ORBAT on a real globe. But there are **zero machine-readable coordinates anywhere**, `WorldState.spatial_state` is a confirmed-dead field, and positions never advance during play — so every moving entity on the globe is presentation-layer fiction and must be labeled as such.
3. **VR must not be built on CesiumJS.** Cesium's WebXR request has been open since 2016 with an unmerged proof-of-concept PR; its "VR mode" is legacy WebVR-era stereo. The honest headset path is **three.js + NASA-AMMOS 3DTilesRendererJS** (working WebXR example, loads Google 3D Tiles) or **Cesium for Unity** (official Quest/OpenXR support). Ship the projector "war-room wall" first; keep the event contract renderer-agnostic so a headset client is a bolt-on later.

---

## 2. What each repository brings

| | FALSE FLAG | gods-eye-view |
|---|---|---|
| **Core** | LLM-driven turn-based crisis narrative: injects, advisor discussion, free-text decisions, LLM adjudication | Continuous real-time photorealistic 3D globe (CesiumJS + Google 3D Tiles) with 13 live GEOINT layers |
| **Data model** | Metrics, flags, actor trust, hidden narrative truth; DTDL twin model (13 interfaces, Microsoft-parser-validated) on PRs #65/#66 | Per-layer entity feeds (flights, vessels, satellites, fires, CCTV, radio…) with dead-reckoning interpolation |
| **Serving** | FastAPI + layer-tagged SSE bus (SITREP/INTEL/DIPLOMATIC/DOMESTIC/CABINET/REFEREE), zero-build `FileResponse` HTML pages | Vite dev server with same-origin `/api/*` middlemen for every feed |
| **Aesthetic** | CRT/terminal, classification strips, phosphor green | "Forbidden cockpit": CRT/NVG/FLIR GLSL sensor shaders, cinematic scene director |
| **What transfers** | The event bus, the facilitator inject seam, the demo driver, the DTDL model | The *ideas* and 3 shader modules + scene-recipe JSON grammar (~1–1.5k lines), **not** the ~25–30k lines of live-feed plumbing |

The deep symmetry: gods-eye-view's native rendering model is **sparse keyframes (15–30 s) + client-side dead reckoning** — which is exactly what a turn-based engine can emit. FALSE FLAG doesn't need to become real-time; the globe client manufactures continuity from keyframes, the same way gods-eye-view already does for 15-second ADS-B polls.

---

## 3. Verified feasibility claims

Each claim was adversarially verified (attempt-to-refute, with primary sources; the DTDL claim was proven by actually running Microsoft's parser).

| # | Claim | Verdict | Essence |
|---|---|---|---|
| 1 | CesiumJS can do in-headset VR/WebXR today | **REFUTED** | No WebXR as of v1.144. `Scene.useWebVR` is dead WebVR-era stereo. PoC PR #11372 unmerged since 2023. Use three.js + 3DTilesRendererJS (working WebXR example) or Cesium for Unity (Quest/OpenXR) for any real headset work. |
| 2 | Google Photorealistic 3D Tiles fit a demo budget; keyless fallback exists | **CONDITIONAL** | 1,000 free root-tileset queries/month (one covers ~3 h of rendering) is ample — but needs a billing-enabled account with quota caps. gods-eye-view **hard-throws without a Google key** (`src/main.js:83-86`); a dummy key or 3-line patch drops it to the keyless stack: OSM raster imagery + Re:Earth terrain (not Cesium World Terrain, not Bing — those need an ion token). |
| 3 | gods-eye-view layers can run on locally simulated feeds, no external keys | **CONDITIONAL (essentially yes)** | The layer contract is source-agnostic; `mode:'sim'` is a first-class feed state (the traffic layer's keyless default *is* a built-in simulation); nearly every layer consumes same-origin `/api/*` middleware — a local scenario server emitting the documented shapes drives layers with **zero client changes** (~200–600 LOC + fixtures, 1–3 days). Feeds must pass freshness/schema guards (current timestamps, valid ids, finite lat/lon). |
| 4 | CesiumJS embeds cleanly in the Next.js frontend | **CONDITIONAL** | The committed frontend is a **non-buildable scaffold** — `package.json`, lockfile, `tsconfig`, and `lib/utils.ts` were never committed. The documented Next+Cesium pattern works (client component, `ssr:false`, copy static assets, `CESIUM_BASE_URL`, Node ≥ 22, Turbopack ignores webpack plugins) but requires bootstrapping the frontend first. **The zero-build `FileResponse` pattern is the only serving path that has ever worked in this repo** — use it for the MVP. |
| 5 | The SSE bus can carry globe-cadence telemetry without rework | **CONDITIONAL** | Raw throughput is fine (~957 batched 500-entity events/s measured), but each session's single `asyncio.Queue` is a *work queue, not a broadcast bus*: concurrent consumers steal alternate events (a live defect already affecting player-UI + dashboard on one session). Adding any second screen needs per-subscriber fan-out (realistically 100+ lines with cleanup and tests, not the "~30 lines" a naive read suggests). Correct design: **sparse keyframes + client interpolation on a dedicated `/geo/stream` endpoint** — never 1–10 Hz server push. |
| 6 | A DTDL geospatial extension is standard-clean | **CONFIRMED (executed proof)** | A candidate `TheatreAsset` with geospatial `point`/`lineString` telemetry + `Latitude`/`Longitude` semantic co-types parsed clean alongside the existing 13 interfaces in Microsoft's official DTDLParser: **PARSE OK, 14 interfaces, 309 entities**. Geospatial schemas are *core* DTDL v2/v3/v4. Stay on `dtmi:dtdl:context;3` (ADT supports only v2/v3); model altitude as `Distance`/metre (no Altitude semantic type exists). |
| 7 | Scenarios contain enough geospatial ground truth | **CONDITIONAL** | Geography is unambiguously real-world; a ~30-entry gazetteer covers every named location. But no coordinates exist in state, the ORBAT is served from static initial conditions forever, and the Russian flotilla has only region + heading. Fixed sites: cheap and honest. Moving units: authored tracks or uncertainty areas, never fake precision. LLM geocoding only as *extraction + gazetteer lookup*, never freehand lat/lon. |

---

## 4. Recommended architecture

**"Situation Globe" — zero-build, engine-untouched, twin-shaped.** (Winner of a 3-design judged comparison — MVP-first beat both a full-XR plan and a DTDL-purist plan on feasibility and demo reliability — then hardened with the best grafts from the losers.)

### Components

- **`api/globe.html`** (~1.5–2k lines, new): self-contained CesiumJS page at `GET /globe`, session-attach header cloned from `dashboard.html`, six-layer toggle sidebar reusing the dashboard legend colors, `SampledPositionProperty` entity rendering, a mini scene-director (~120 lines) consuming camera-recipe JSON, a **permanent EXERCISE/SIMULATED watermark**, and facilitator click-to-compose wired to the existing `POST /game/{sid}/inject`.
- **`api/geo_sim.py`** (~500–700 lines, new): per-session ambient-simulator daemon cloned from the `api/demo.py:_drive` pattern — but it **never takes `session.lock` and never mutates engine state**. Own seeded RNG (engine determinism untouched). Reads game events from a tap; emits `geo_batch` / `geo_focus` / `geo_event` / `sim_clock` frames into **its own per-subscriber queue fan-out**. Scripted per-turn track legs (red fleet along North Atlantic → GIUK → UK waters) **slewed across however long the real turn takes**, plus procedural ambient corridors modulated by `escalation_risk`. Applies facilitator-vs-player truth filtering at emit time.
- **`api/server.py`** (~90–150 lines modified): a mirror tap where events are stamped (`_make_item` + both push paths), a bounded `recent_events` ring, subscriber register/unregister, `GET /globe`, `GET /geo/stream/{sid}` (SSE, snapshot-on-connect), `GET /geo/config/{scenario}`, static mount for pinned Cesium assets.
- **Geo pack** (`geo_layer.yaml`, ~200 lines, authored): the gazetteer (name → lat/lon for every ORBAT/scenario location), per-turn scripted tracks, per-inject camera hints **keyed by inject id, not turn number** (the `fast_start` variant renumbers files).
- **Vendored from gods-eye-view (MIT, headers + pinned commit in a `VENDORED.md`)**: `styles/thermal.js`, `styles/retro.js`, `styles/surveillance.js` — self-contained Cesium `PostProcessStage` GLSL modules (FLIR/CRT/NVG) — plus the `SCENE_RECIPES` JSON *shape* (reimplemented; the upstream director hard-requires its 10k-line UI monolith). **Explicitly not vendored**: the live-feed manager, per-feed adapters, Vite middleware, voice stack, and the CC BY-NC-SA submarine-cable dataset.
- **DTDL sidecar — pulled into the MVP** (cheap, verified): a `Theatre;1` / `TheatreAsset;1` interface file added to `interop/models/` (auto-served by the `/dtdl` glob; `Session;1` stays frozen — the 9-stream test asserts the *run document*, not the interface count, so nothing breaks). Wire events shaped as `twin_lifecycle` / `twin_telemetry` so the Phase-2+ Azure story is a relabeling, not a rewire. HUD shows live `dtmi:falseflag:*` badges — the flashy demo visibly renders the Microsoft-validated twin.

### Data flow

```
engine (quiescent between turns; untouched)
  └─ adjudication / inject events ──► SSE bus (stamped in _make_item)
                                        ├─► /stream (player UI, dashboard — unchanged)
                                        └─► mirror tap ──► geo_sim daemon
                                                             ├─ scripted + ambient track keyframes
                                                             ├─ sim_clock (fictional time, slew ratio)
                                                             ├─ truth filter (REFEREE vs player estimate)
                                                             └─► /geo/stream fan-out ──► globe client(s)
                                                                        Cesium interpolation fills the gaps
facilitator globe click ──► POST /game/{sid}/inject (existing 403-gated seam) ──► engine
```

### Reconciliation rules (turn-based truth vs continuous picture)

- Positions are **decorative, never adjudicative** — they never enter engine state, saves, or the DTDL run export (honoring the "wire, never fabricate" ruling; `spatial_state` stays dormant).
- On a turn boundary that contradicts interpolation: **slew, don't teleport** — decay the correction over 30–90 s, presented diegetically as an intelligence-picture refresh.
- Escalation bands drive the sensor shader ladder: **0–25 clean, 25–50 CRT, 50–75 NVG, 75–100 FLIR** (crossfaded) — plus the fictional clock (the campaign runs Sun 5 Oct 17:00 → 03:00, so late turns play in real darkness). The player *sees* escalation before reading a number.
- Classified assets (SSBN on patrol) render as **probability areas labeled POSITION WITHHELD**, never fake dots. Player view gets **uncertainty ellipses** that bloom with time-since-fix; the facilitator view renders ground truth — the REFEREE layer split made visible as fog-of-war geometry.
- When a threshold ending fires, the simulator needs an ending state machine (fleet stops advancing on `resolution`; goes dark on `war`) — currently unspecified anywhere, must be in the MVP.

---

## 5. Requirements

**Zero mandatory external dependencies.** No npm/Node build, no Google key, no Cesium ion token, no LLM spend for the demo loop.

- CesiumJS pinned to the version in gods-eye-view's actual `package.json` at the vendored commit; fetched by a ~20-line script into `api/static/cesium/` (fetch-not-commit, like the Pyodide precedent), CDN fallback. **Note: local Cesium assets do not make imagery offline** — bundle Cesium's low-res NaturalEarthII textures as the true no-network fallback; OSM streaming (with attribution + identifying User-Agent, per OSMF tile policy) is the online default.
- Optional upgrades: `CESIUM_ION_TOKEN` (Bing imagery + World Terrain), Google Maps key (photorealistic 3D tiles — metered: 1,000 free root queries/month, then $6/1,000; set quota caps).
- Python: no new packages (FastAPI + sse-starlette already present); PyYAML for the geo pack.
- New SSE vocabulary on a **new endpoint** — deliberately *no* `Layer` enum change (in-payload layer tags instead), keeping the diff outside the protected tree.
- Branch off the merged #65/#66 tree (the design assumes `/dtdl` exists); all changes are additive routes + one tap, so rebases stay contained.
- Tests: geo-pack loads, gazetteer covers every ORBAT name, simulator determinism under a fixed seed, **facilitator truth never leaks into player queues**, snapshot-on-connect ordering. Never touch `interop/test_interop.py`.
- Demo runbook: `WARGAME_LLM=mock`, `POST /demo/start`, globe on the projector, dashboard on the operator laptop. One `/stream` consumer per session until fan-out also covers the game bus. 60-second cold-restart drill. **Pre-record a video capture as the demo-day dead-man fallback.**

### Prerequisites (do these before building)

1. **Measure a real-LLM campaign.** The entire thesis fills "multi-minute" between-turn dead air, but turn wall-time and call count were never measured — and `api/demo.py` caps `pace_s` at 30 s, so **attract mode structurally cannot showcase the ambient layer**; it shows cinematics. Present them honestly as different things.
2. **Pin the competition parameters.** Deadline, rubric, live-demo-vs-video, IP rules appear nowhere in the repo, and the design choice (demo-reliability-first vs standards-depth-first) genuinely flips on the rubric — the judging panel split 2–1.
3. **Security hardening before anything leaves localhost.** The API has zero auth, and unauthenticated process-wide `POST /routing` and `PUT /prompts` — on venue wifi anyone could rewrite the LLM prompts mid-demo. Bind localhost + authenticated reverse proxy, or a read-only mirror for spectator surfaces.
4. **Gazetteer QA** — cross-check every coordinate; one wrong base position in front of judges is a credibility bug.
5. **Session/thread lifecycle** — sessions are never evicted; per-session daemons and queues leak over a booth day. Add idle timeout + teardown.

---

## 6. The honest VR/XR path

| Phase | Surface | Tech | Status |
|---|---|---|---|
| Now (MVP) | **War-room wall** — full-screen clean view on a projector | CesiumJS page | The "XR story" at a fraction of the risk; reads as an operations centre from the back of a judging room |
| Stretch 1 | In-browser headset (Quest Browser) | **three.js + NASA-AMMOS 3DTilesRendererJS** (`renderer.xr` + VRButton; working VR example upstream; loads Google 3D Tiles/ion) | Proven components; needs aggressive screen-space-error tuning on standalone Quest |
| Stretch 2 | Native headset app | **Cesium for Unity** (official Quest 2/Pro OpenXR support) | Highest fidelity; heavier toolchain |
| Anti-path | ~~CesiumJS VR mode~~ | `Scene.useWebVR` | Legacy WebVR stereo; browsers removed WebVR ~2020. Do not build on it, do not wait for PR #11372 |

The strongest XR image for judges isn't a VR globe — it's the **COBRA war-room table diorama**: the theatre rendered between the players at table height, uncertainty ellipses and all. Because the `/geo/stream` contract is renderer-agnostic (twin-telemetry frames + gazetteer), a headset client is a third renderer, not a rewrite.

---

## 7. Phased roadmap

| Phase | Scope | Effort (solo + LLM assistance) |
|---|---|---|
| **0 — Spike** | `globe.html` against an existing `/demo/start` session via the *existing* `/stream`, hardcoded 10-entry gazetteer, one shader. Proves the projector wow-shot end-to-end before any server change. | 1 day |
| **1 — MVP** | Fan-out tap + `/geo/stream`, `geo_sim.py` (scripted red-fleet track + ambient corridors + `sim_clock`), geo pack for turns 1–6, sensor ladder, inject camera cues, watermark, `Theatre;1` sidecar + DTMI HUD badges, tests, runbook | 2–3 weeks *(judges' consensus: budget 2–3× the optimistic 3–5-day claim once grafts and cleanup are counted)* |
| **2 — Facilitator depth** | Dual-truth god view + uncertainty ellipses, click-to-inject with structured `geo:{locationId,lat,lon}` on `ManualInjectRequest`, `/geo/spawn` + `/geo/track` EXCON puppeting, `scene_cue` broadcast (one button flies every screen's camera), event journal + `?since_seq` catch-up, after-action replay page from the DTDL export | 1–1.5 weeks |
| **3 — Stretch** | Async LLM `GEO_EXTRACTION` for stochastic turns (extraction + gazetteer lookup; failure degrades to ambient-only, never blocks a turn), WebXR war-room table, voice interrogation, ADT upload demo | post-competition |

Every phase is independently droppable with a named exit criterion; Phase 0+1 alone is a jury-ready demo.

---

## 8. Engagement & playability extensions

Curated from 24 generated ideas (S/M/L = effort):

1. **[M] Living watch floor** — the red fleet visibly advances through the GIUK gap while the cabinet argues. Turns the sim's worst UX moment (multi-minute silent adjudication) into its most atmospheric one.
2. **[S] DEFCON sensor ladder + fictional night** — escalation picks the shader; the campaign clock runs into literal darkness where NVG is the only honest view. Highest feel-per-effort in the set; zero backend changes.
3. **[M] Cinematic inject reveals** — `flash_alert` → FLIR snap-zoom on the Orkney contact; `intelligence` → NVG orbit of Severomorsk; `diplomatic` → capital-to-capital arcs. ~10 lines of authored YAML per scripted inject.
4. **[M] Fog-of-war globe** — player sees intelligence *estimates* (aging ghost contacts, blooming ellipses); facilitator sees truth. Two screens, same session, different realities — the game's epistemic core made spatial, and the strongest two-screen judge moment.
5. **[M] Click-the-globe EXCON console** — facilitator clicks the North Sea, a pre-filled inject composer opens, firing it plays the reveal cinematic on the player's globe. Exercises the existing 403-gated `deliver_inject` seam verbatim.
6. **[M] Home-front layer** — media injects spawn broadcast rings over cities; city activity visibly dims as `domestic_stability` falls (reusing gods-eye-view's deterministic traffic-sim pattern). Gives the neglected domestic axis equal dramatic weight.
7. **[M] Watch-officer voice brief** — each turn opens with a 30-second narrated camera tour built from the existing `situation_summary` (browser `speechSynthesis` = $0 baseline). Solves briefing fatigue; doubles as the shareable trailer.
8. **[S] Assessment overlay** — decisions plotted on the timeline/globe colored by `qualityVerdict`, joined to the DTDL `LearningObjective` interfaces (Bloom levels) already in the model. Cheapest idea with the strongest serious-game credential.
9. **[M] Multi-screen ops room** — one screen per data layer (SITREP wall, INTEL desk, DIPLOMATIC board, CABINET transcript, REFEREE console); each is a dumb SSE consumer filtering the layer tag every event already carries. Re-frames the solo game as a staffed seminar wargame.
10. **[S] Zero-spend attract mode** — self-playing deterministic mock campaign choreographing the globe unattended (with the honest caveat from §5: it demos cinematics, not the between-turn ambience).

## 9. Synergies only possible because both repos exist

- **Interrogate the globe under fog-of-war** — gods-eye-view's voice action grammar (`gevActions.js` is deliberately LLM-agnostic; the OpenAI stack severs cleanly) answered by FALSE FLAG's own advisor LLM, which *structurally cannot leak hidden truth*. "Show me naval activity near the strait" → in-fiction answer + camera response, generated by the cabinet AI under real epistemic constraints. Neither repo can do this alone; strongest single judge-facing moment.
- **After-action replay from the DTDL export** — the `Session;1` run document already carries turn-stamped metrics, injects, decisions, phase changes, and advisor trust; a replay page scrubs the whole campaign on the globe **offline, zero tokens**. Converts the DTDL work from compliance artifact into the debrief product.
- **The twin graph as the single contract** — one Microsoft-parser-validated model drives the live globe, the dashboard twin panel, and (unchanged) an Azure Digital Twins upload. "Same twins, three surfaces" is an interoperability claim few competition entries can make.
- **Peacetime baseline + simulated crisis deltas** — fiction-neutral live layers (real satellites, real seismicity) as ambient texture, conflict layers simulated and EXERCISE-labeled per layer, using gods-eye-view's own honest-labeling switch (`traffic.js` precedent). As escalation climbs, simulated NOTAMs thin real civil-traffic corridors. (Caveat: never propagate real current-epoch TLEs under the fictional 2025 clock — synthesize epoch-matched TLEs.)
- **CCTV/radio as diegetic evidence** — media injects spawn clickable "camera" pins with generated stills; SIGINT intercepts become geolocated pins with real confidence grading. The player *hunts the globe* for the story between turns — a player verb, not passive watching.

---

## 10. Risks and honest caveats

- **Scope creep is the top risk.** Judges chose the small design, then grafted ten features onto it. Tier the grafts as explicit cut lines; the Phase-0 spike is the commitment gate.
- **The demo shows cinematics; live play shows the ambient layer.** `pace_s ≤ 30` caps mock-mode gaps. Don't imply otherwise to judges.
- **A pre-existing bus defect** (single-consumer queue) is exposed by any second screen — fixing it is base-project repair, which is the stronger justification for the change.
- **Narrative-contradiction risk**: ground truth is LLM prose; the globe can lag a twist the geo pack didn't script. Mitigations: author from inject prose, uncertainty rendering, slew-not-teleport; accept the residual.
- **Optics**: simulated military tracks over real UK/Russian bases in a surveillance aesthetic, presented in neutral Ireland. Mitigations to state in the submission: permanent EXERCISE watermark, zero-live-feed construction for conflict layers, classified assets non-plotted, a short responsible-use note.
- **Accessibility (currently zero coverage)**: CRT flicker/photosensitivity option, WCAG contrast on phosphor palettes, motion-comfort settings for camera fly-tos, captions for any voice brief. A national competition plausibly scores this.
- **Aesthetic register**: a raw photoreal globe fights the CRT identity — ship it defaulted *into* CRT sensor mode with classification-strip chrome (deliberate stance, needs owner sign-off).

### Licensing/attribution manifest

| Item | License | Obligation |
|---|---|---|
| gods-eye-view vendored shaders + recipe grammar | MIT | Retain headers; record pinned commit in `VENDORED.md` |
| CesiumJS | Apache-2.0 | Notice file |
| OSM raster tiles | OSMF tile policy | Attribution, identifying User-Agent, no heavy use, no SLA |
| Re:Earth keyless terrain | CC BY 4.0 | Attribution |
| Cesium ion (optional) | Community tier | Free below $50K org revenue/funding — check prize implications |
| Google 3D Tiles (optional) | Metered ToS | Visible attribution always; Google-geocoder-only pairing |
| TeleGeography cables dataset | CC BY-NC-SA | **Do not copy** |

---

## 11. Owner decision checklist

1. Competition parameters: deadline, rubric, live-demo vs video, IP/prize rules → picks the winning trade-off.
2. Merge sequencing for #65/#66 (this design branches from the merged tree).
3. Geo pack location: `data/scenarios/.../geo_layer.yaml` (protected tree, diff-first) vs `api/geo_data/` (zero-controversy).
4. Aesthetic stance: photoreal locked behind CRT sensor mode by default?
5. Demo scenario variant (standard vs `fast_start`) — geo pack keys by inject id either way.
6. Real-LLM timing measurement: who runs it and on which provider budget.
7. VR hardware reality: is a Quest available? (Decides whether Stretch 1 is ever more than a doc.)
8. Spectator/QR surfaces: only behind the read-only mirror from the hardening plan.
