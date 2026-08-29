# Feasibility Study — The Situation Globe

> **New here?** This is an engineering-fidelity document — dense on purpose, written for whoever builds and maintains this so nothing is lost between sessions. For the plain-language version, start with [`XR_GLOBE_FEASIBILITY_IN_BRIEF.md`](XR_GLOBE_FEASIBILITY_IN_BRIEF.md); the plan and open decisions are in the Owner's Brief (PR #69) and issues #70–#75.

**Integrating simulated gods-eye-view GEOINT layers into FALSE FLAG as a between-turn XR data layer — with an authoritative spatial layer and a VR ops room**

*Version 2, 2026-08-28. Basis: this repository at `main` (35c11c0) plus the open DTDL PRs #65/#66, and [bilawalsidhu/gods-eye-view](https://github.com/bilawalsidhu/gods-eye-view) (MIT) at commit `314a0e1`. Produced by two multi-agent analysis passes (39 agents total): pass 1 — six codebase readers, three competing presentation architectures, three-lens judging, seven adversarially-verified claims, completeness critique; pass 2, under the owner's revised **build-what's-needed** framing — three targeted engine readers, three competing authoritative-spatial-layer designs, two-lens judging, five further verified claims (two by executing probes against the real engine), completeness critique. Raw agent output: `audits/2026-08-28-xr-feasibility/`. Cut material: `XR_GLOBE_FEASIBILITY_DISCARDS.md`.*

*Owner rulings recorded 2026-08-28, which this version incorporates: (1) feasibility means what can be **built**, not what current code supports — the v1 "engine-untouched" virtue is explicitly revoked, replaced by protected-tree diff discipline and the new test files named in §4a; (2) the VR aim is **presence in the ops room** — the theatrical experience is the product; (3) the VR cast is **stylised comic characters against a hyper-real globe** — the register contrast is deliberate; (4) the between-turn window is **design-paced**, not LLM-latency-paced.*

---

## 1. Verdict

**Feasible at both layers, as a port of ideas rather than an embed of code — and the two layers are order-independent tracks, not a stack.**

- **Track A — Presentation** (v1 verdict, unchanged in substance): a zero-build CesiumJS "situation globe" (`api/globe.html`, served like `dashboard.html`), fed over a dedicated `/geo/stream` SSE endpoint with per-subscriber fan-out; vendor only gods-eye-view's three GLSL sensor shaders and its camera-recipe grammar; DTDL `Theatre;1` sidecar. One change from v1: **the scripted red-fleet track legs are cut** — Track B's first stage supersedes them with real state for about the same effort.
- **Track B — Authoritative spatial layer** (new, sanctioned by the reframing): typed unit positions become **engine state, written at each turn boundary**. The LLM never touches a coordinate: it emits **movement orders** (unit, mission, gazetteer destination, speed band) in one added non-blocking call; a pure, RNG-free kinematics module advances positions once per adjudication; deterministic **geometric tripwires** turn crossings into narrative events; the globe renders the engine's stored positions under source labels (`adjudicated` — written by this turn's kinematics step · `simulated` — projected forward between turns · `estimated` — the player's fog-filtered view). Failure behaviour is bounded by construction: only two code paths write a position — the gazetteer lookup at load and the kinematics arithmetic at turn-resolve — so any failure leaves positions un-updated, never invented, never discontinuous.
- **VR** — the projected-screen ops room: Cesium never enters the XR pipeline (the v1 "never build VR on CesiumJS" ruling is *extended*, not reversed). A three.js WebXR boardroom renders the globe as a texture on a wall screen, with the advisors as stylised sprites from the repo's existing pixel-art pipeline. Sound under two hard conditions (§6), verified against specs and shipping code.

---

## 2. Three findings, restated under the new framing

1. **The between-turn window is architecturally exact — and design-paced.** The engine is provably quiescent between `resolve_decision` and the next `POST /briefing`; the next turn starts only when the client asks (`api/server.py:872-916`). The window is therefore whatever the design wants: a **watch-floor phase** with its own verbs and an explicit "Convene COBRA" action, not filler during LLM latency. The ambient daemon owns that window; under Track B it projects the engine's stored positions forward along the same kinematics the engine itself uses.
2. **Geography is real, and becomes real state.** ~30 named real-world places (Portsmouth, Faslane, RAF Lossiemouth, Severomorsk, the GIUK gap) make the gazetteer an afternoon's work. Today there are zero machine-readable coordinates and positions never advance — v1 called moving entities "presentation-layer fiction". Under the sanctioned build that ruling becomes a **source-label system**: positions are engine state written at turn boundaries (`adjudicated`), deterministic projection between them (`simulated`), and fog-filtered estimates to the player (`estimated`).
3. **VR is real — as presence, not as immersive terrain.** CesiumJS in-headset remains refuted. But the game's fiction is a PM in a briefing room looking at screens, so the correct VR shape is the **ops room**: world-locked screens (comfortable, cheap, crisp via WebXR quad layers on Quest), a stylised comic cast (no rigging, no uncanny valley, and nothing that could be mistaken for real footage), and the hyper-real globe on the wall. The register contrast — chunky comic advisors debating brinkmanship in front of a bleeding-edge surveillance picture — is a deliberate aesthetic stance.

---

## 3. Verified claims (twelve, adversarially tested)

Pass-1 claims 1–7; pass-2 claims 8–12. "Executed" = proven by running code, not reading it.

| # | Claim | Verdict | Essence |
|---|---|---|---|
| 1 | CesiumJS can do in-headset VR today | **REFUTED — superseded in practice** | No WebXR as of v1.144; PoC PR #11372 unmerged and unprioritized. Never build or wait on the *direct* route — but read with claim 11: the ops-room projected screen (§6) delivers the VR element with CesiumJS never touching the headset pipeline, so the practical verdict on VR is **achievable**, not blocked. |
| 2 | Google 3D Tiles fit a demo budget; keyless fallback exists | **CONDITIONAL** | 1,000 free root queries/month is ample (billing account + caps needed). gods-eye-view hard-throws without a key; 3-line patch → keyless OSM + Re:Earth stack. Keyless photoreal also exists via Cesium ion asset 2275207. |
| 3 | gods-eye-view layers run on locally simulated feeds | **CONDITIONAL (yes)** | Layer contract is source-agnostic; `mode:'sim'` is first-class; same-origin `/api/*` seam → zero client changes, ~1–3 days. Feeds must pass freshness/schema guards. |
| 4 | CesiumJS embeds in the Next.js frontend | **CONDITIONAL** | The committed frontend never builds (no `package.json` in git). Zero-build `FileResponse` HTML is the only proven serving path here — use it. |
| 5 | The SSE bus carries globe telemetry without rework | **CONDITIONAL** | Throughput fine (~957 batched 500-entity events/s measured); but the per-session queue is a destructive work-queue — any second consumer needs per-subscriber fan-out (a live defect worth fixing regardless). Sparse keyframes + client interpolation, never high-Hz push. |
| 6 | A DTDL geospatial extension is standard-clean | **CONFIRMED (executed)** | `TheatreAsset` with geospatial telemetry parsed clean in Microsoft's DTDLParser (14 interfaces, 309 entities). Stay on `context;3`; no Altitude semantic type. *The new provenance fields (§4a) require a re-validation run — pending.* |
| 7 | Scenarios hold enough geospatial reference data | **CONDITIONAL** | Real-world names throughout; gazetteer cheap. No coordinates in state — which Track B now fixes rather than works around. |
| 8 | The repo's LLM plumbing can carry a movement-orders schema | **CONDITIONAL** | The house labelled-line dialect (`llm/parsing.py`) plus 5 defensive layers already parse state-mutating numbers (quality effects, actor trust) — orders extend a battle-tested pattern, **not JSON** (no repair infrastructure exists). Normative guards: separate non-blocking call; fail-to-hold; closed-vocabulary validation (ORBAT ids + gazetteer); terminal sentinel with whole-block discard on truncation (today truncation is counted, never rejected); mock driver must answer `NO_ORDERS` so an API outage can never fabricate movement. |
| 9 | A typed spatial field keeps old saves loadable and the suite green | **CONDITIONAL (executed)** | Probed on the repo's pinned pydantic 2.7.3 with the real `save_game`/`load_game`: an `Optional[...] = None` field loads every old save byte-identically (a *required* field kills them all). Suite green **only after** `python3 dev-scripts/build_play_bundle.py` regenerates `docs/game.zip` (4 stamp tests fail otherwise — baseline 712 passed restored after rebuild). Downgrade direction is loadable but **silently lossy** — an accepted-loss owner decision; bump save version 2.4→2.5. Add a new field; never retype the dead `spatial_state`. The probe covers field compatibility only — the full persisted-vs-reconstructed restore contract is defined in §4a. |
| 10 | A boundary tripwire can generate a legitimate game event | **CONDITIONAL (executed)** | Probed live against the real engine: surfacing, LLM visibility (3 channels), honest ledger recording (same-turn overwrite / solo entry on quiet turns), and coexistence with scripted injects all demonstrated. One legal firing instant: top of `get_turn_briefing` (replay-guarded, zero RNG draws). The load-bearing timing claim — tripwire lines land inside the LAST TURN slice the same turn's inject generator sees — was **confirmed by direct inspection** (`get_last_turn_slice`, `llm/context_builder.py:161-204`); pin with a regression test. Latch in `world.posture` or a new field, never `world.flags` (wiped on every effects application — probe-confirmed). |
| 11 | The projected-screen VR workaround is sound | **CONDITIONAL** | Architecture confirmed and well-precedented; the *naive* version fails. Two hard conditions in §6. Quad-layer benefits are Quest-only; the streamed variant measures ~235–290 ms end-to-end (fine for turn cadence); CesiumJS flat on Quest Browser is **unproven** — half-day on-device spike required before committing to the local variant. |
| 12 | Range rings / intercept times are computable from scenario data | **CONDITIONAL** | Structure yes, numbers no: zero speeds, ranges, or coordinates exist. But every blue platform is real with published figures (Aster 30 ~120 km — [Think Defence](https://www.thinkdefence.co.uk/the-type-45-daring-class-destroyer/), [Defense Advancement](https://www.defenseadvancement.com/company/mbda/aster-30/); Spearfish ~50–56 km — [Navy Lookout](https://www.navylookout.com/spearfish-the-royal-navys-heavyweight-torpedo/), [Wikipedia](https://en.wikipedia.org/wiki/Spearfish_torpedo); full sourced dossier is Manus task P2a, issue #70) — authoring is cheap. ASW sonar and Sea Viper BMD rings are classified territory: **fictional-doctrine labels mandatory**. A turn→clock table must be authored (game time never advances; episode intervals are irregular comments). And `engine/intelligence.py:197-199` already **fabricates random distances** ("holding {150–250}nm") — replace with the real layer, don't coexist. |

---

## 4. Track A — Presentation architecture

As v1, with corrections. Components: `api/globe.html` (zero-build CesiumJS, layer toggles, mini scene-director, vendored CRT/NVG/FLIR shaders, EXERCISE watermark, DTMI HUD badges) · `api/geo_sim.py` (**~500 greenfield lines** — v1's "upgrade the daemon" framing was wrong, no such file exists; the pass-1 judges' 2–3× effort multiplier applies) · server tap + `/geo/stream` fan-out + snapshot-on-connect · gazetteer + geo pack (camera hints keyed by inject id) · `Theatre;1` DTDL sidecar with `twin_lifecycle`/`twin_telemetry`-shaped wire events.

Changes under Track B: the daemon's keyframe source flips from scripted fiction to an immutable deep-copied `SpatialSnapshot` published by `resolve_decision` into a latest-wins mailbox on the session; between snapshots it interpolates by calling **the same `engine/kinematics.advance()`** at fractional dt — the ambient picture is a forward projection of the engine's stored positions, labelled `simulated`. Slew-not-teleport reconciliation (30–90 s decay, read as an intelligence-picture refresh) is retained verbatim. A version-polled `GET /theatre` state endpoint (ETag) serves as the globe's authoritative state endpoint, with SSE as change notification — sidestepping the destructive queue rather than relying on mailbox discipline alone. Escalation→sensor ladder, fog-of-war ellipses, click-to-inject EXCON console, and the demo runbook carry over unchanged.

## 4a. Track B — The authoritative spatial layer

The reconciled hybrid of the two leading pass-2 designs (the judges split 1–1 between them; their grafts converge on exactly this): **TASKORD**'s order emission + pure kinematics, plus **IRONCLAD**'s transition-graph legality, detected-visibility tripwires, readiness-as-live-state, and authored route polylines, plus the derived-seed movement call both judges endorsed.

**Spatial model** (`models/spatial.py`, new, JSON-native scalars only): `UnitTrack{unit_id, side, domain, lat, lon, heading_deg, speed_kts, location_name, status, order, last_confirmed_turn, …}`; `MovementOrder{unit_id, mission, destination|bearing_deg, speed_band, issued_turn, source}`; `Mission ∈ {hold, transit, patrol, screen, shadow, intercept, strike, rtb, surge}`; provenance `∈ {adjudicated, simulated, estimated}`; a bounded `order_log` (~50) for AAR replay. Added to `WorldState` as `spatial: Optional[SpatialState] = None` (the executable probe's load-bearing default); the dead `spatial_state` field is deleted in the same change; save version 2.4→2.5; **every `models/world.py` edit is followed by the play-bundle rebuild**.

**Restore contract (what survives a save/load).** *Persisted inside `SpatialState`*: unit tracks and standing orders, the bounded `order_log`, and the `fired_tripwires` latch set — all serialize with `WorldState`. *Reconstructed, never persisted*: the daemon's interpolation baseline and the snapshot mailbox (the daemon re-primes from the first `SpatialSnapshot` published after load), fog offsets (derived from the process-stable seed recipe, so a reload renders identical estimates), and all sub-turn interpolated positions. Acceptance test required: save → load → resume must reproduce identical positions, `order_log`, tripwire state, and the next watch-floor output (`test_spatial_saveload.py`).

**Movement.** The LLM decides *intent*, never coordinates: one dedicated `MOVEMENT` call appended to decision round 3 (a free worker slot exists — the honest claim is "no added worker contention", not "zero wall-clock"), seeded from a derived generator (`crc32(f"{seed}:movement:{turn}")`) rather than a master-RNG draw — erasing the cross-version determinism fence entirely. Output is the house labelled-line dialect: `NO_ORDERS` or up to 8 `ORDER: <unit_id> | mission=<enum> | dest=<gazetteer_id> | speed=<band>` lines with a terminal sentinel. Validation is set-membership plus a per-unit **mission transition graph** (red cannot jump rendezvous→strike) enforcing escalation ordering on movement itself. `engine/kinematics.py` (pure, zero RNG) advances tracks once per `resolve_decision` along **authored route polylines** (sea lanes, not great circles through Ireland), decrementing readiness (`turns_to_full_readiness` becomes live state — "surge degraded now vs. wait 3 turns" renders on the globe). Red pressure is a deterministic doctrine track the player can read and race. Second channel: injects gain an optional `movements:` list beside `effects:`; the facilitator inherits physics-respecting spatial power through `deliver_inject` for free (a true teleport requires an explicit REFEREE-logged primitive).

**Degradation ladder (normative).** Clean parse → applied, provenance `adjudicated`. Partial → valid lines applied, bad lines skipped with a **player-visible transcript line** plus `record_miss` (telemetry alone leaves half-executed intent invisible). Empty / mock-substituted / truncated → **zero new orders, all units hold on standing orders**, kinematics still advances, provenance `simulated`, with a dashboard counter so a campaign can't run "spatially deaf" unnoticed. Rationale: an un-updated position self-corrects at the next turn's kinematics step; an invented one corrupts every display and decision downstream of it.

**Tripwires.** Declarative predicates in scenario YAML (`zone_entry`, `zone_exit`, `range_ring`, `closing_within`, `eta_below`), evaluated as pure functions at exactly one instant: the top of `get_turn_briefing`, where positions are final, the replay guard is available, and — confirmed by inspection — the lines land inside the context slice the same turn's inject generator narrates from. Effects flow through the deliver-style primitives *with* the hidden-metrics sync (skipping it is the documented silent-revert bug). Ledger honesty via `PlayedEvent.kind ∈ {played, system}`. **Detected-visibility semantics**: the player-facing inject fires only when the current fog estimate supports detection; the REFEREE record always fires; undetected crossings surface later as delayed ambiguous intel — fog becomes event-level gameplay. On scripted-exhausted turns a firing tripwire *becomes* the turn's inject: geometry fills narrative dead air. Scenario starter set: GIUK crossing (flash_alert), 200 nm from Faslane (intelligence), Kalibr envelope of London (military), blue carrier into the gap (REFEREE-only, feeds red doctrine).

**Fog and ISR.** `engine/intel_picture.py`: blue units render from stored positions directly; red renders to the player as last confirmed fix + error radius growing with staleness, collapsing inside blue sensor footprints. Noise comes from a derived generator (`Random(zlib.crc32(f"{seed}:{unit_id}:{turn}:fog".encode()))` — process-stable, unlike Python's salted `hash()`) — never the sacred child-seed sequence — so reloads render identical estimates. ISR tasking becomes a move with a rendered receipt: P-8s up or a towed-array frigate forward visibly shrinks ellipses next turn; `shadow` holds a contact solid while trail is maintained. The facilitator view superimposes the player-estimate layer on the stored positions — **the deception gap is the visible false-flag game**. Mystery-mode side channel closed by CI, not discipline: a prompt-grep test asserts no `NarrativeConfig` secret strings reach the movement prompt; red movement derives only from player-visible events.

**Single-store rule.** Engine `world.spatial` is the only authority; the daemon and every client hold read-only snapshots; any position cache in narrative state or facilitator effect without the metrics sync recreates the silent-revert class. Quality-assessment REASONING is player-visible verbatim — player-facing calls receive the blue+estimates rendering only; one renderer split, one leak. Pinned by dedicated regression tests (see engine-diff list in the raw output).

**What stays decorative, permanently:** civil air/shipping corridors, satellite passes, shader cosmetics, sub-turn interpolated micro-positions (derived, never written back), the classified SSBN and other abstract-location units (never rendered as points), and the player's uncertainty ellipses (a view, not state). Spatial *ending* predicates are *v2 opt-in only* — conditioning scoring on geometry is an owner decision, deliberately deferred.

**Incremental LLM cost:** one extra FLASH call per turn; the spatial block adds ~450–1,300 tokens to the deciding calls (~2.5–6.5k/turn across them). The demo loop stays $0: in mock mode without live orders the map runs **doctrine-only** — red still closes on schedule offline, which is a defensible demo story stated honestly.

---

## 5. Gates

The decision points, each with an owner and an exit criterion. (Two v1 gates are struck: ~~LLM response time~~ — the window is design-paced; ~~the 30 s attract-mode pacing cap~~ — one line of our own `api/demo.py`.)

1. **Competition parameters** — **CLEARED 2026-08-28 (owner input)**: the challenge started 28 Aug, onsite day **12 Sep** (15 days), final **14 Sep**. The onsite venue is **Irish Manufacturing Research** — an RTO whose pillars (Digitisation/Industry 4.0, Robotics & Automation) and flagship REWIRE project run on digital twins, so the DTDL track is the venue's home turf and the `Theatre;1` sidecar + DTMI badges are promoted to sprint priority. Consequence: the full program does not fit; the §7 cut lines activate — see the 15-day sprint plan there. Rubric still unpublished as far as known; a Manus research task should hunt it.
2. **PRs #65/#66 merge sequencing** *(dependency)*: both tracks build on the merged tree; the DTDL provenance fields need a parser re-validation run post-merge. *Clears on merge + one rebase + PARSE OK.*
3. **Solo capacity vs. tiered scope** *(resource)*: combined honest estimate **~2–3 months part-time** (Track A 2–3 weeks at the judged 2–3× multiplier; Track B ~4–6 part-time weeks staged so every stage ships playable; re-golden churn; doctrine/gazetteer authoring — which *is* game design, 2–4 days; gazetteer QA; the Quest spike). "Two tracks" means order-independent for one person, not parallel. *Managed by the cut lines in §7, never removed.*
4. **Security before anything leaves localhost** *(engineering — worse under Track B)*: zero auth plus unauthenticated `POST /routing` and `PUT /prompts` now guard *the stored positions, facilitator move commands, and a network-reachable movement prompt* — venue wifi could literally move the fleet. Bind localhost + authenticated reverse proxy; read-only spectator mirror; the WebRTC variant's DataChannel is an input surface. *Hard gate for the position system.*
5. **Session/thread lifecycle** *(engineering — worse under Track B)*: sessions are never evicted, and the new per-session mailbox, daemon, fan-out queues and tripwire registries deepen the leak. *Clears with idle timeout + teardown.*
6. **Owner decisions resolved this revision** *(recorded)*: build-what's-needed ✓; ops-room VR thesis ✓; lo-fi cast / hi-fi world ✓; design-paced holds ✓. **Still open**: geo-pack location (`data/` vs `api/geo_data/`); demo scenario variant; downgrade silent-loss acceptance (claim 9); spatial endings (v2 opt-in); real-LLM cost measurement (demoted from gate to bookkeeping); **is a Quest physically available?** — gates the on-device spike and the whole Quest-local variant.

---

## 6. VR: the ops room

**Thesis (owner ruling): presence in the room is the product.** The PM's experience of the crisis is mediated through screens and people — a VR globe you could freely inspect would *break* the epistemology the fog-of-war design depends on. So the deliverable is a three.js WebXR boardroom: world-locked screens on the walls (the situation globe, the advisor transcript, a metrics board, a patrol's sensor feed — all feeds that already exist on the bus), the advisors as **stylised comic sprites** built from the repo's existing pixel-art pipeline (`Graphics/Animations`: DB16 palette, sprite scenes, diplomat variants — billboarded, 2–3 talking frames keyed off transcript SSE events), room lighting tied to `escalation_risk`, the fictional clock's darkness outside a window. The register contrast with the hyper-real globe is the point — and it's armour: stylised characters give emotional distance for mature subject matter, and nothing with a comic cast will be mistaken for real footage.

**The projected screen — sound under two hard conditions** (verified against the WebGL spec, WebXR issues, Meta's own numbers, and shipping three.js code):

1. **Render-loop ownership**: `window.requestAnimationFrame` is not guaranteed to fire during an immersive session on standalone headsets — Cesium must run `useDefaultRenderLoop:false` with `viewer.render()` driven from `xrSession.requestAnimationFrame`, or the globe silently freezes in-headset.
2. **Copy timing**: the canvas→texture copy must happen in the same JS task as Cesium's render (or `preserveDrawingBuffer:true`), else the WebGL spec makes the read undefined behavior (blank texture). Cross-context sharing is impossible; cap updates at ~24–30 Hz, 720–1080p.

| Shape | How | Status |
|---|---|---|
| **S1 · Portable** | three.js plane + `CanvasTexture`; same-task copy; controller-ray → UV → synthetic pointer events (the shipping `InteractiveGroup`/`HTMLMesh` pattern; keep the hidden canvas with a real layout rect; drive zoom via Cesium's Camera API, not fake wheel events) | Works on desktop-tethered headsets today |
| **S2 · Quest quality** | Same, panel promoted to an **XRQuadLayer** (Meta Quest Browser ≥16.1: compositor resamples once → materially crisper text, ~2.4 ms + >25 % GPU savings per Meta's sample; three.js PR #25254 / Babylon WebXRLayers). Chrome ships only XRProjectionLayer — Quest-only benefit | Best local variant **if** the spike passes |
| **S3 · Quest safe** | Server renders the globe; WebRTC H.264 1080p into `<video>` → `XRMediaBinding` quad layer; inputs via DataChannel. Measured ~235–290 ms end-to-end — fine for a turn-based situation screen, rubber-bandy for drag | The robust standalone path |
| Gate | CesiumJS *flat* on Quest Browser at usable framerates is **unproven** (sole public evidence: a 2021 failure report) | Half-day on-device spike before committing to S1/S2 locally |

Accepted limits: the globe is a monoscopic picture — no stereoscopic terrain, no reaching into the map (consistent with the screen-as-fiction thesis); comfort is fine (world-locked panel; screen-content latency is not head-motion latency). Accessibility now includes the headset: CRT/FLIR flicker inside an HMD is a photosensitivity risk beyond the monitor case — static shader variants and a motion-comfort setting are requirements, not polish. The native path for later remains Cesium for Unity (official Quest/OpenXR).

---

## 7. The plan

**The plan is not in this document.** It lives at the repository root in **[`PLAN.md`](../PLAN.md)** — five stages, each with its build checklist, its done test (an observable fact), and its current status. That file is the single source; this study is the evidence behind it (why each choice, what was verified, what was rejected).

Dates: challenge started 28 Aug 2026 · onsite 12 Sep at IMR · final 14 Sep. Cut order under pressure: post-competition tier → stage 5 → stage 3. The gates are schedule instruments only — no design questions remain inside them ([#71](https://github.com/earlyprototype/false-flag/issues/71), the movement-architecture decision, is closed: orders on).

## 8. Engagement & playability

Geometry-native mechanics (pass 2), on top of the v1 set (watch floor, sensor ladder + fictional night, inject cinematics, fog globe, click-to-inject, home-front layer, voice brief, assessment overlay, ops-room screens, attract mode):

1. **Spatial verbs the interpreter honors** — "move the carrier group to the GIUK gap and put a picket off Faslane" produces actual engine movement, not flavor prose.
2. **Pre-commit geometry preview** — the interpret→confirm gate renders the projected turn: arrival snaps, and whether weapon envelopes will intersect ("can 96 Sea Viper even engage from here?"). Re-read live positions at commit — a facilitator inject between preview and commit invalidates the projection.
3. **Advisors quote arithmetic, not vibes** — "at 16 knots they are 18 hours from our territorial waters"; the omissions scan flags computed coverage gaps ("no P-8 coverage of the gap").
4. **Tripwire beats replace the scripted clock** — the GIUK crossing fires when the fleet actually gets there; campaign pacing derives from closure geometry.
5. **Trail-or-lose** — `shadow` keeps an SSN in trail and holds the contact solid (fog radius → 0 while maintained); `intercept` computes a real intercept point.
6. **ISR tasking as fog you spend** — the YAML's "can only defend 2 locations" limitation becomes a visible, aching trade-off on the map.
7. **Deterministic red pressure** — the doctrine track is a legible dread clock the ops-room wall literally draws.
8. **AAR with provenance** — the order log replays the campaign's actual geometry, badged adjudicated vs. projected.

## 9. Synergies (unchanged from v1, now on firmer ground)

Interrogate-the-globe under fog (gods-eye-view's LLM-agnostic action grammar + the advisor LLM that structurally cannot leak hidden state (it never receives it)) · after-action replay from the DTDL export, now with a real track history · one twin graph driving globe, dashboard, and ADT · peacetime live baseline + EXERCISE-labeled crisis deltas (epoch-matched TLEs only) · CCTV/radio as diegetic evidence the player hunts between turns.

---

## 10. Risks & labeling policy

- **The contradiction risk reverses direction.** v1: the narrative text was the only record of events, so the globe could only lag it. Now unit positions are engine state, and *the narrative must stay consistent with them* — the movement call and the spatial context block exist precisely to keep the narrator grounded; residual drift is bounded by fail-to-hold.
- **Determinism discipline** — fog noise or any spatial randomness touching `self.rng` corrupts resumed saves; the derived-generator rule is review-enforced. Prompt-text changes reshuffle mock goldens: land as one deliberate re-golden commit.
- **Two-store trap recurrence** — standing discipline plus regression tests, not a one-time fix.
- **Scope creep remains risk #1** — pass 2 produced 3 designs, 17 grafts, 16 ideas on top of pass 1's ten; the cut lines in §7 are the containment. Spatial endings stay v2 opt-in.
- **Labeling policy (merged)**: permanent EXERCISE watermark on every surface; per-layer SIMULATED chips; classified assets as POSITION WITHHELD areas; **fictional-doctrine labels on ASW/sonar and BMD-footprint rings** (real figures are classified — the one place experts could embarrass the entry); public-figure citations for blue platform ranges; replace `intelligence.py`'s fabricated random distances; comic cast in VR as structural anti-misinformation. One responsible-use paragraph in the submission.
- **Accessibility**: flicker-free shader variants (monitor *and* HMD), WCAG contrast on phosphor palettes, motion-comfort settings, captions for voice briefs.
- Licensing manifest unchanged from v1 (MIT shaders w/ pinned commit; Apache-2.0 Cesium; OSM policy; Re:Earth CC BY 4.0; ion Community terms; **never** the CC BY-NC-SA cables data).

## 11. Owner decision checklist

1. ~~Competition parameters~~ — **landed 2026-08-28** (onsite 12 Sep at IMR, final 14 Sep); the §7 sprint plan is the operative schedule. Remaining sub-item: the judging rubric, if published.
2. Merge #65/#66; then the DTDL provenance re-validation run.
3. Tiebreak ratification: accept the TASKORD+IRONCLAD hybrid as specified, or hear the two designs separately (both preserved in full in the audit output).
4. Downgrade silent-loss acceptance for saves (claim 9) — accept and document, or add version-aware load warnings.
5. Geo-pack location; demo scenario variant.
6. Quest availability — gates the on-device spike and the S1/S2-vs-S3 choice.
7. Spatial ending predicates — v2 opt-in, owner-approved scoring change only.
8. Budget note: real-LLM cost measurement before any live-LLM public demo (bookkeeping, not a gate).
