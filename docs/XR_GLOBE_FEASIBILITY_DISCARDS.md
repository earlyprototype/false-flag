# XR Globe Feasibility — Discards Register

> **New here?** This is an engineering-fidelity document — dense on purpose, written for whoever builds and maintains this so nothing is lost between sessions. For the plain-language version, start with [`XR_GLOBE_FEASIBILITY_IN_BRIEF.md`](XR_GLOBE_FEASIBILITY_IN_BRIEF.md); the plan is [`PLAN.md`](../PLAN.md), the explanation is [the Owner's Brief](OWNERS_BRIEF.md), and the current calls and defaults are in [`DECISION_BRIEFS.md`](DECISION_BRIEFS.md).

**Everything reported by analysis agents but cut or compressed out of `XR_GLOBE_FEASIBILITY.md`, preserved for future examination.**

*Companion to `docs/XR_GLOBE_FEASIBILITY.md`. Raw agent output (6 readers, 3 full designs, 3 judge verdicts, 7 verifications, 24 ideas, critique) is preserved verbatim at `audits/2026-08-28-xr-feasibility/workflow1_full_output.json`. The second analysis pass (authoritative ORBAT spatial layer + VR projected-screen workaround) is complete; its output is registered at `audits/2026-08-28-xr-feasibility/workflow2_full_output.json` (see section G).*

**Status codes**: `CUT` — dropped from the report entirely · `COMPRESSED` — survives as a phrase, detail lost · `RESURRECTED` — restored by an owner ruling in the 2026-08-28 session (build-what's-needed framing; ops-room-presence VR thesis; lo-fi cast/hi-fi world aesthetic; design-paced between-turn holds) · `REF` — reference fact never surfaced, kept here for whoever builds this.

---

## A. Cut or compressed ideas (from the 24-idea extension panel)

**A1 · Cockpit ride-alongs — `CUT`, now partially `RESURRECTED`.** Between turns the player "joins" a simulated P-8 out of RAF Lossiemouth sweeping the GIUK gap, or a QRA Typhoon pair from Coningsby — first-person cockpit camera with the CRT/NVG/FLIR vision cycle; when the next inject involves something at sea, the simulator routes the patrol for a flyby so the player glimpses the Kilo-class before the briefing names it. gods-eye-view ships most of it: `cockpitTracking.js` (92 lines coordinating `layer.trackById`/`cockpitView.enter/exit`) plus ~10 cockpit modules riding the flights layer's dead-reckoned entities. Cut for [L] effort and heavier vendoring. *Resurrection path (cheap, post-ops-room ruling): the patrol's sensor feed as one of the boardroom wall monitors first — diegetically exactly what real ops rooms have; cockpit-as-a-place is the later upgrade, and the same fixed-seat XR pattern as the boardroom itself. Also the panel's verdict: "the natural VR seed — a cockpit is the easiest XR frame: fixed seat, world moves."*

**A2 · Mid-exercise timeline scrubber — `COMPRESSED`** (survives as "event journal + catch-up" in Phase 2). Full concept: persist every stamped bus event to a per-session journal (append inside `_make_item`; sessions are in-memory with `Last-Event-ID` ignored today), add `GET /game/{id}/events?since_seq=N&layer=…` respecting the REFEREE filter, then a facilitator scrubber: drag back to any point mid-exercise, see per-layer exactly what players had been told by then, jump the camera to any past inject, resume live. Smallest server change with the widest unlock (late-join for every observer surface, "what did we know and when" AAR facilitation, the bridge from live sessions to DTDL replay).

**A3 · Facilitator pre-brief spatial storyboard — `CUT`.** Before the exercise, render the whole scripted campaign as a spatial storyboard from the episode `geo:` blocks — where turns 1–6 will land, the Northern Fleet's authored track, which bases are implicated — so facilitators brief observers and plan manual injects around the authored arc. A genuine exercise-design artifact; costs little once the geo pack exists.

**A4 · Watch-officer voice brief, full mechanism — `COMPRESSED`** (survives as one line). Detail lost: the script source is the engine's rolling `situation_summary` + the turn's inject, reformatted by a prompt for the existing narrator LLM family (hot-editable via `PUT /prompts/{family}`) into a spoken watch brief **with an ordered location list**; the globe converts that list into a scene-director project (recipes like `orbital-watch`, `omniscience-pullback` are the authoring format) synced to TTS. Two-rung voice ladder: browser `speechSynthesis` at $0, upgradeable later.

**A5 · Intel desk as the GEOINT analog — `COMPRESSED`.** `engine/intelligence.py` deterministically renders **hidden metrics** as in-fiction SIGINT/cable-traffic/media-monitoring prose on the INTEL layer — the natural in-fiction source for geolocated intercept pins whose confidence grading is *real game state*, not decoration. The reader called it "the natural in-fiction analog for gods-eye-view's simulated GEOINT layers."

**A6 · LLM ambient world ticker — deferred, now under active re-examination.** The full [L] variant: a `GEO_AMBIENT` LLM context (13th family in `llm/model_config.py`) reading `situation_summary` + `recent_injects` + the ORBAT each turn and scripting the next N minutes of ambient GEOINT. Deferred from MVP (parse fragility, spend); the in-flight second workflow evaluates it as one of three authoritative-spatial-layer designs.

---

## B. Non-winning design elements not grafted

Full architectures for both losing designs are in the raw JSON (`designs[1]`, `designs[2]`); items below are the pieces worth individual recovery.

### From "Full XR Operational Picture" (scored 3rd — timeline infeasibility, not wrongness)

**B1 · three.js WebXR war-room table diorama — `CUT`, now `RESURRECTED` in modified form.** Room-scale virtual briefing room; the North Atlantic theatre as a 1:2,000,000 diorama *on the table between the players*; entities as instanced meshes fed by the identical SSE stream; sensor shaders ported as three.js postprocessing passes; controller-driven inject composer. The ops-room ruling supersedes it with room + screens; the table survives as the upgrade path ("the room persists, the table upgrades").

**B2 · `ffbus.ts` shared typed SSE client — `CUT`.** One client library (EventSource + Last-Event-ID resume + typed geo event decoding) consumed by both the desktop globe and any headset app. Worth building the moment a second renderer exists.

**B3 · Authored TLE set + client-side SGP4 — `COMPRESSED`.** Satellites need **zero position telemetry**: ship epoch-matched synthetic TLEs as data, propagate client-side with satellite.js (gods-eye-view's own satellite approach). Pairs with B14.

**B4 · The `styleFacade.js` option — `CUT`.** ~300-line StyleManager facade (`applyVisualState`/`setRecordingMode`/`runImmediateNavigation`) so gods-eye-view's actual `director.js` runs without its 10,293-line `ui.js` monolith — the alternative to the report's chosen "reimplement director-lite (~300 lines)". Judges flagged the facade estimate as the likeliest overrun; recover only if the full director's capabilities (captureShot authoring, project import/export, migration) prove worth it.

**B5 · Diegetic sensor-static transition — `CUT`.** For irreconcilable state changes (a vessel sunk, a base struck) where slew-not-teleport can't apply: cut to sensor static, then reveal the new picture. The designed answer to hard narrative discontinuities.

**B6 · "SIMULATED — OPERATION TUMAN" per-layer labeling — `COMPRESSED`.** Reuse gods-eye-view's `traffic.js` status-chip convention verbatim on every simulated layer's row controls and legend — the honest-labeling pattern applied at layer granularity, not just the page watermark.

**B7 · Escalation-band civil-traffic drain — kept in spirit; mechanism detail here.** Procedural civil ADS-B/AIS "chaff" whose density is a *function of escalation_risk* — airspace visibly empties as the crisis deepens; a second ambient tell alongside the sensor ladder.

### From "Twin Theatre" (scored 2nd — standards depth)

**B8 · Runtime model discovery — `CUT` deliberately.** The globe fetches `GET /dtdl` at attach, then routes `twin_telemetry` by DTMI through a renderer registry (a plain dict `{dtmi → render rules}`, explicitly *not* a generic DTDL interpreter). Cut as indirection tax (+30–40%); recover if the judging story needs "the client discovered its contract from the standard at runtime" demonstrated live. Its own guard-rail: "a pure-DTMI-routed renderer for ~4 entity kinds is indirection with thin payoff — the payoff must be demonstrated, not asserted."

**B9 · `GeoLocation;1` gazetteer twins — `COMPRESSED`.** Model the gazetteer as first-class twins so `Inject`/`EventLedgerEntry` reference places **by DTDL relationship instead of free text** — semantically the strongest standards move in either losing design; ~15–25 instances cover the entire scenario.

**B10 · `OrbitalAsset;1 extends TheatreEntity;1` — `CUT`.** TLE line pairs as Properties; satellite twins carry no position telemetry at all (clients run SGP4). Note the judges' caveat: the claim that the local validator supports `extends` was verified only against the worktree — re-check post-merge.

**B11 · `adt_bridge.py` + the recorded Azure capstone — `COMPRESSED`.** `azure-digitaltwins-core` upload of `interop/models/*.json` + live mirroring of `twin_lifecycle`/`twin_telemetry` into a real ADT instance; one recorded "same models, zero edits, running in Azure" demo as the judging capstone, never a live-demo dependency. Known transform needed: exported Relationship values are plain string ids, not ADT relationship objects.

**B12 · Player tasking-as-advisory-text — `CUT`, now `RESURRECTED` as central.** Player clicks on the globe append advisory text to the decision free-text — deliberately non-adjudicative in the original. The build-what's-needed reframing promotes this to real spatial decision verbs; the in-flight workflow's "orders-not-positions" design is its formalization.

**B13 · Implementation conventions worth keeping** — `REF`: `world_sim` RNG salting (`random.Random(session_seed ^ GEO_SALT)`); `seed.py` instantiating twins from the ORBAT with the `$metadata.$model` Azure-DT binding convention `export_run.py` already uses; `twin_store.py` as JSON-snapshotable in-memory graph; degradation-path discipline (every phase independently droppable with a named exit criterion, and a named minimum cut: "Phase 1 minus GEO_EXTRACTION minus OrbitalAsset — 3 interfaces, scripted+ambient only — still keeps the standards story intact").

---

## C. Judge corrections and grafts not carried into the report

**C1 · `interop/CORRESPONDENCE.md` is a broken pointer — `CUT`, action item.** Referenced by `export_run.py`'s PROFILE_NOTE but absent from the PR #65/#66 worktree. Restore/merge before judging — a free credibility fix independent of all geo work.

**C2 · `PLAYER_LAYERS` is derived — `REF`.** It's a frozenset of all non-REFEREE layers (`models/layers.py:28-30`), so if a Layer enum value is ever added, the enum addition alone suffices; there is no separate PLAYER_LAYERS edit (two designs got this wrong).

**C3 · Fan-out implementation trap — `CUT`, important.** `_stream_filter` pops the server-side `_layer` key before yield; under per-subscriber fan-out the payload **must be copied per subscriber** — popping from a shared dict once strips the tag for every other queue. Whoever builds the fan-out needs this.

**C4 · `SampledPositionProperty` is not free dead reckoning — `CUT`, important.** Cesium's forward extrapolation is linear hold/extrapolate: CAP racetrack orbits and turning vessels at 10–30 s fix cadence render as polygons or overshoot corners. Either densify fixes on curved segments or keep a small (~150-line) client-side constant-turn model (gods-eye-view's own `arcOffsetEnu` approach).

**C5 · Numbers hygiene — `REF`.** The "60–100k LOC discarded" rhetoric is inflated 2–3× (own inventory ≈ 25–30k); every gods-eye-view line count was gathered via summarized fetches ±20%; the "CesiumJS 1.124" pin is unconfirmed (npm at 1.144) — pin to what the cloned commit `314a0e1`'s `package.json` actually says. All dtdl-branch line citations are provisional until #65/#66 land.

---

## D. Reader findings never surfaced (reference facts for whoever builds this)

**D1 · Complete SSE event vocabulary** — player-visible: `transcript` (type scene|inject|system|narrator|advisor|error), `system`, `state_update` {phase, turn, metrics}, `diplomacy` (call_started|call_turn), `intel` (assessment_pulled {actor, code, confidence}), `ending`; REFEREE-only: `adjudication` (raw effects/pushback/critical_concerns), `parse_health`, `llm_call` (family/tier/provider/model/latency_ms/fallback/prompt_chars/reply_chars — no prompt bodies), `inject_fired`. `DATA_LAYERS.md` is referenced in code comments but does not exist as a file — doc gap.

**D2 · `api/llm_relay.py` as a relay template** — its register_session/bind/pusher contextvar pattern is a working template for relaying *any* out-of-band telemetry source onto a session's bus as tagged events.

**D3 · Frontend build hazards for any in-app globe** — CRTOverlay is `fixed inset-0 z-50` over the whole viewport: DOM scanlines would stack on the Cesium canvas and double-apply with the GLSL CRT shader (carve the viewport out, or make the shader the sole treatment). Radix Dialog mount/unmount destroys the WebGL context — the globe needs persistent mounting with visibility toggling, a deviation from the panel convention. `reactStrictMode` double-mounts effects in dev — Cesium init needs a guard. `API_URL` is hardcoded `http://localhost:8000` in three files; CORS allowlist is localhost:3000/3001 only. `SceneViewport.tsx:172` has a children slot (transcript floats over `bg-black/40` translucency) — the natural in-app mount point. Root `.gitignore` ignores `*.png` globally; the repo's precedent is fetch-not-commit for large runtimes (16.5 MB Pyodide). Dead code: `NoiseTexture.tsx` unused, `components/game/StatusBar.tsx` is a legacy duplicate.

**D4 · Theme↔shader bridge** — `theme-retro`'s 120° phosphor green *is* an NVG palette and `theme-defcon`'s cyan a CRT palette; tint the vendored shaders' uniforms from the active theme's CSS tokens so DOM chrome and globe shift together via the existing SettingsPanel switcher.

**D5 · gods-eye-view mechanics worth knowing** — layer registration: `dataManager.register(layerObj)` then `finalizeRegistrations(LAYER_STATE_REGISTRY)`; enabled-state persisted under `gev:layer-state:v2` with origins user/voice/tool; toggles serialized with AbortController supersession and intent epochs. `flights.js`: render clock 30 s behind wall time (`RENDER_DELAY_SEC`), corrections decay over 900 ms (`DR_CORRECTION_MS`), one GPU-batched BillboardCollection (5000+ sprites), glTF model caps 150/350. Share-link v2 encodes camera+layers+selected subject — a natural carrier for between-turn XR coordination state keyed to turn ids. `window.__gevQaRegisterLayer` is a dev-build seam for registering synthetic layers at runtime. The Puppeteer QA harness (`scripts/qa-*.mjs`) drives layers with **fabricated intercepted `/api` responses** — a ready-made regression-testing pattern for our scenario feed server. Feed-shape coupling: flights expects OpenSky `/states/all` semantics (`on_ground`, `true_track`, baro metres) plus adsbdb enrichment, and rejects snapshots older than 120 s. Voice: `gevActions.js` (camera verbs, layer toggles, director calls) is deliberately LLM-agnostic plain JS; `contextStore.js`/`analystEngine.js` provide the scene snapshot an LLM narrator would consume; `initGevVoiceCommands` is a single severable call site. Node engines pinned 24.14.x/26.x. Performance is hand-tuned (render governor, LOD, label arbiter, budget governors) — naively adding layers can blow the frame budget, and those governors are *not* being vendored.

**D6 · Keyless photoreal route — `CUT`, valuable.** CesiumJS's `createGooglePhotorealistic3DTileset` loads **ion asset 2275207** when no Google key is set — photorealistic 3D tiles through the Cesium ion free tier, no Google billing account. (Community tier: free below $50K org revenue/funding, 15 GB streaming + 1,000 imagery sessions/month; a solo project of this size qualifies.) Google-key billing mechanics if used directly: only *root tileset* queries bill (one covers ~3 h of rendering; renderer tile requests are free); default cap 10,000/day ≈ $54/day worst case; every page load/hot-reload consumes one of the 1,000 free monthly.

**D7 · Simulated-feed guards** — a scenario feed must emit current-epoch timestamps (flights marks snapshots stale after 120 s) and schema-valid rows (string `icao24`, finite lon/lat) or layers show STALE/UNAVAILABLE chips; the AIS middleware 503s when `AISSTREAM_API_KEY` is unset — bypass it or point the layer at the simulator via `VITE_AIS_LIVE_API_URL` (no code change); earthquakes/bikeshare/radio fetch external hosts directly (1-line URL changes each, or leave off).

**D8 · Prior in-repo lineage for the globe** — `AGENTIC_HUD_STRATEGY.md:30-34` already planned a "War Room" full-screen modal (`/status`, `/map`, `/warroom`) listing "map state" — never implemented; the Rich dashboard is still ⏸ pending. "Immersive" in repo vocabulary means a *play mode* (metrics vs vibes vs narrative), not immersive tech. The only VR mention in the repo is one Long-Term roadmap line: "VR integration for immersive cabinet room" (`docs/handover/README.md:268`) — which the ops-room ruling now makes concrete. The intro DMS coordinate-strip convention (`69°04'N 033°25'E`) is pinned by `tests/test_cli_modes.py:138` and doubles as the diegetic HUD format for camera bookmarks. The fog aesthetic was always designed to wire density = escalation_risk/100.

**D9 · DTDL model details for the geo extension** — `WorldReference.organisations[]` carries 9 country actors with role lead|partner|support|adversary + disposition + accessLevel (natural capital-marker/choropleth layer); `environmentalFactors` Map (weather, public_mood, media_coverage) as globe-ambience drivers; inject effects use delta-strings (`"5..8"` midpoint) scaled by difficulty 0.5/0.7/1.0 with min magnitude 1; capture path is coupled to `dev-scripts/play_campaign.py` internals (refactors there silently break capture); don't overclaim conformance beyond "DTDL v3, official-parser-clean" (SEDL is unpublished; profile explicitly not claimed SEDL-conformant). Mystery Mode's hidden `NarrativeConfig` reaches **only** actor-simulation and diplomacy prompts — new geo producers must respect both the REFEREE fence and that segregation or a player globe becomes a wallhack.

**D10 · DTDL geospatial proof specifics** — geospatial schemas (`point`/`lineString`/…) are **core DTDL** v2/v3/v4, not an extension; only Latitude/Longitude semantic co-types need `dtmi:dtdl:extension:quantitativeTypes;1`; **no Altitude semantic type exists** (model altitude as `Distance`/metre or the GeoJSON 3rd coordinate); stay on `context;3` (ADT supports only v2/v3); ADT accepts Telemetry in models but does not *store* telemetry (durable state should be Properties; `SendTelemetry` only emits events); `maxMultiplicity` is accepted but unenforced. The local `validate_dtdl.py` is stricter than the spec (bare-string content `@type` only; `point` not in its whitelist) — which is why plain-double position Objects are the chosen encoding. The executed proof harness (dotnet + DTDLParser 1.1.3) lived in session scratch and is gone, but is reproducible in minutes.

**D11 · Bus throughput measurements** — the exact `_make_item` path serialized a batched 500-entity position payload (55.5 KB) at 957 events/s and per-entity events at 176k/s: transport is never the constraint; topology (single-consumer queue) and semantics (append-only ledger, no conflation, no eviction) are.

---

## E. Critique items dropped or downgraded

**E1 · Pyodide/GitHub-Pages exclusion — `CUT`, must be stated somewhere.** The browser build (the surface the owner actually plays; "merging to main is deploying") has no API server — the globe does not exist there in MVP. The demo story must run the FastAPI stack and say so explicitly, or accept a worker-bridge port as future work.

**E2 · Save/load × geo state — `CUT`.** RNG-state-carrying saves restore the engine mid-campaign, but simulator state, ring buffers, and the fictional clock are serialized nowhere: a loaded turn-5 session needs a turn-keyed ambient re-seed strategy. Unaddressed by all three designs; belongs in the spatial-layer design now under way.

**E3 · Distraction hypothesis — `CUT`.** Every engagement claim is untested — specifically whether an animated globe *distracts from the advisor-discussion phase, which is the actual game*. At least one scripted playtest with the rehearsed runbook belongs in the phasing.

**E4 · No-merge degradation story — `CUT`.** If PRs #65/#66 churn or don't land, the globe against `main` loses `/dtdl` and the DTMI badges; the degradation story (globe still works, standards chrome dark) was never written.

**E5 · Episode-YAML pass-through untested end-to-end — `CUT`.** "The engine ignores unknown episode keys" is read from `events.py` but was never tested through save/load and the difficulty-scaling path — a 10-minute test before committing the `geo:` authoring format.

**E6 · Superseded gates (owner rulings, 2026-08-28)** — for the record: the "measure LLM turn latency first" gate is dissolved (the between-turn window is design-paced — the engine waits indefinitely for `POST /briefing`; what remains is token-cost bookkeeping for a live demo); the `pace_s ≤ 30` attract-mode cap is one line of our own `api/demo.py`; "decorative, never adjudicative" is reframed as Phase-1 posture, not a ceiling, pending the authoritative-spatial-layer verdicts.

---

## G. Pass 2 discards (authoritative spatial layer + VR screen — 2026-08-28, second workflow)

Raw output: `audits/2026-08-28-xr-feasibility/workflow2_full_output.json`. Most of pass 2 landed in the v2 study; what follows is what did not.

**G1 · CARTOGRAPHER (async world-simulator design) — `ELIMINATED`, grafts survive.** A separate out-of-band LLM pass emitting validated spatial deltas after adjudication. Killed on two verified defects: its "in-version determinism fully preserved" claim is false (delta commit timing is wall-clock racy, so tripwire firing turns vary between identically-seeded runs), and it never addresses the save/async race (a delta committing after serialization is silently lost). Its full spec remains in the raw JSON. Grafts that survived into v2: the derived-seed idiom (`crc32`, no master-RNG draw), the `GET /theatre` ETag/version-polled endpoint with SSE as nudge, the prompt-grep Mystery-leak CI test, and the parse-health fallback dashboard counter.

**G2 · IRONCLAD (doctrine state machine) — merged, not whole.** Full design preserved in raw JSON. Elements *not* carried into the hybrid: the zero-LLM-forever stance (v2 keeps the MOVEMENT call; IRONCLAD's honest cost was that the player's spatial intent is silently dropped every turn — "inaction bias is a design choice with a gameplay cost, not a free safety property"); its joint unit×posture×destination mega-parse across ~18 units (the largest parsed output ever shipped — v2 caps orders at 8 lines instead). Carried in: transition graphs, detected-visibility tripwires, readiness-as-live-state, route polylines, quiet-turn tripwire-becomes-inject.

**G3 · Spatial ending predicates — `DEFERRED v2 opt-in` (unanimous).** "Resolution requires red withdrawn north of the GIUK line"; "the decapitation ending reachable only while red holds inside the Kalibr envelope." Zero-added-latency ordering argument is correct, but conditioning scoring on geometry is an owner-approved change only. One ideation agent pitched shipping it now; overruled by designs, judges, and critique alike.

**G4 · Capped advisory spawned entities — `DEFERRED v2`.** CARTOGRAPHER's one keeper gameplay idea: the world simulator may spawn max 8 TTL'd, `origin='simulated'`, never-metric-bearing color entities (a shadowing trawler, an unexplained contact) so the world can grow texture without opening the coordinate-hallucination door.

**G5 · FORCES INVOLVED advisory pre-highlight — `CUT` (small, free signal).** The interpretation call already *requests* a FORCES INVOLVED label and the reply is returned unparsed (`game_manager.py` returns `forces_involved: []` as a literal placeholder). Parsing it against the unit registry gives an advisory pre-highlight of tasked units in the order flow — free signal from an existing call.

**G6 · FORCE_POSTURE label on actor replies — `CUT` (flavour-only third channel).** Optional posture label on the RUS actor's reply, parsed default-none — never load-bearing since actor selection caps at 3 and RUS isn't guaranteed present.

**G7 · Reference facts from the pass-2 readers not in the study** — `REF`: the decision round is up to ~12 LLM calls across 3 concurrent rounds (`MAX_ROUND_WORKERS=3`); preview reuse (ER-074) draws child seeds even for no-LLM lambdas; three calls already mutate state from parsed numbers (quality effects+multiplier, actor TRUST_CHANGE/WILL_SUPPORT, diplomacy OUTCOME/delta) — the precedent the movement call extends; there is **no JSON repair and no parse-level retry anywhere** (retries are transport-only, mock-substituted on double failure — and the mock's canned replies are well-formed, hence the fabrication guard); a measured full campaign logged 16 parse misses, all content gaps, zero parser failures; `update_world_flags` **replaces the whole flags dict from metrics** (`engine/flags.py:38-40`) — nothing durable may live in `world.flags`; `world.posture` survives, serializes, and is never reassigned (probe-confirmed latch home); mid-turn tripwire firing has exactly one safe seam (post-facilitator-inject recheck, discussion phase, no ledger write); `json.dump(default=str)` silently stringifies non-native types in saves; dual pydantic pins (core 2.7.3, api ≥2.9) mean two environments to verify; the scenario clock is internally inconsistent (episode comments say +2h/+2h/+3h/+3h; `scenarios.yaml` says "6 hours over 6 turns") — the turn→clock table must pick.

**G8 · Verified-claim conditions too detailed for the study** — `REF`: the full evidence chains for claims 8–12 (every parse path enumerated; the pydantic probe in both directions including required-field and retype failure modes; the tripwire live probe transcript; the complete WebXR source list — Khronos spec, immersive-web #225, Meta layer benchmarks, three.js PR #25254, the 289 ms WebRTC measurement; the platform-by-platform public range figures with sources) are in `workflow2_full_output.json → verified`.

## H. How to examine further

- Pass 1 raw output: `audits/2026-08-28-xr-feasibility/workflow1_full_output.json` — keys `readers` (6), `designs` (3, full architectures), `judges` (3), `verified` (7 claims with evidence), `extensions` (24 ideas with mechanisms), `critique`.
- Pass 2 raw output: `workflow2_full_output.json` — same shape: `readers` (3), `designs` (3: TASKORD / IRONCLAD / CARTOGRAPHER in full), `judges` (2), `verified` (5, incl. executed probes), `extensions` (16), `critique`.
- Each idea entry carries a `mechanism` field with file:line anchors into both repos — written to be actionable without re-analysis.
