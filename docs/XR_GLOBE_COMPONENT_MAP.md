# Situation Globe — Component Map

> **New here?** This is an engineering-fidelity document — dense on purpose, written for whoever builds and maintains this so nothing is lost between sessions. For the plain-language version, start with [`XR_GLOBE_FEASIBILITY_IN_BRIEF.md`](XR_GLOBE_FEASIBILITY_IN_BRIEF.md); the plan and open decisions are in the Owner's Brief (PR #69) and issues #70–#75.

**Visual companion to [`XR_GLOBE_FEASIBILITY.md`](XR_GLOBE_FEASIBILITY.md).** Every box below is classified: **CORE** (solid, in the competition sprint), **STRETCH** (attempt only behind its decision gate), or **DEFERRED** (post-competition, design verified and waiting). Links under each diagram go to the study section or file that specifies the component. Milestones and decision points are in the last diagram.

---

## 1 · System overview — what talks to what

```mermaid
flowchart LR
  subgraph ENGINE["ENGINE (Track B — stored positions)"]
    SPATIAL["models/spatial.py\nUnitTrack · MovementOrder"]:::core
    KIN["engine/kinematics.py\npure, zero-RNG advance"]:::core
    GAZ["gazetteer.yaml\n~30 authored coords"]:::core
    DOCT["red doctrine legs\nauthored routes"]:::core
    MOVE["MOVEMENT LLM call\norders, never coords"]:::stretch
    TRIP["engine/tripwires.py\nboundary predicates"]:::defer
    FOG["engine/intel_picture.py\nfog / estimates"]:::defer
  end

  subgraph API["API TIER (Track A — serving)"]
    FAN["per-subscriber fan-out\n+ /geo/stream SSE"]:::core
    THEATRE["GET /theatre\nversioned snapshot"]:::core
    DAEMON["api/geo_sim.py\nsnapshot-fed interpolator"]:::defer
    DTDL["Theatre;1 DTDL sidecar\n+ /dtdl serving"]:::core
  end

  subgraph CLIENT["CLIENTS"]
    GLOBE["api/globe.html\nzero-build CesiumJS"]:::core
    SHADERS["vendored CRT/NVG/FLIR\nshaders (MIT)"]:::core
    BADGES["DTMI HUD badges\n(IMR resonance)"]:::core
    VR["VR ops room\nS1/S2/S3"]:::defer
  end

  subgraph OPS["DEMO OPS"]
    RUNBOOK["runbook + proxy stance\n+ attract loop"]:::core
    VIDEO["recorded video fallback\n(non-negotiable)"]:::core
  end

  GAZ -->|hydrates| SPATIAL
  DOCT -->|standing orders| SPATIAL
  MOVE -.->|validated orders| SPATIAL
  SPATIAL -->|once per adjudication| KIN
  KIN -->|SpatialSnapshot| THEATRE
  KIN -.->|snapshot mailbox, latest-wins| DAEMON
  KIN -.->|positions| TRIP
  TRIP -.->|system inject| ENGINE
  SPATIAL -.->|stored positions| FOG
  FOG -.->|estimates| THEATRE
  THEATRE -->|poll + ETag| GLOBE
  FAN -->|SSE nudge + events| GLOBE
  DAEMON -.->|interpolated frames| FAN
  DTDL -->|model + instances| BADGES
  SHADERS --> GLOBE
  GLOBE -->|projector| RUNBOOK
  GLOBE -.->|canvas texture| VR

  classDef core stroke-width:3px
  classDef stretch stroke-dasharray:6 3,stroke-width:2px
  classDef defer stroke-dasharray:2 4,stroke-width:1px
```

**Legend**: thick border = CORE (sprint) · long dashes = STRETCH (gated) · short dashes = DEFERRED (post-competition). Dotted arrows are paths that exist only once their source component ships.

| Component | Class | Specified in | Anchors |
|---|---|---|---|
| `models/spatial.py`, `engine/kinematics.py`, gazetteer, doctrine legs | CORE | [Study §4a](XR_GLOBE_FEASIBILITY.md#4a-track-b--the-authoritative-spatial-layer) | claims 9, 12 |
| Fan-out + `/geo/stream`, `GET /theatre` | CORE | [Study §4](XR_GLOBE_FEASIBILITY.md#4-track-a--presentation-architecture) | claim 5 |
| `globe.html`, shaders, watermark | CORE | [Study §4](XR_GLOBE_FEASIBILITY.md#4-track-a--presentation-architecture) | claims 2–4 |
| `Theatre;1` sidecar + DTMI badges | CORE (promoted — IMR venue) | [Study §4](XR_GLOBE_FEASIBILITY.md#4-track-a--presentation-architecture), gate 1 | claim 6 |
| Runbook + video fallback | CORE | [Study §5 gates 4–5, §7](XR_GLOBE_FEASIBILITY.md#5-gates) | — |
| MOVEMENT call | STRETCH (gate D2) | [Study §4a](XR_GLOBE_FEASIBILITY.md#4a-track-b--the-authoritative-spatial-layer) | claim 8 |
| Tripwires, fog, snapshot-fed daemon, VR ops room | DEFERRED | [Study §4a, §6](XR_GLOBE_FEASIBILITY.md#6-vr-the-ops-room) | claims 10, 11 |

---

## 2 · Track B mechanism — how a position gets written, and why no failure path can write an invented one

```mermaid
flowchart TD
  LLM["MOVEMENT call (STRETCH)\nlabelled lines, ≤8 orders,\nterminal sentinel"]:::stretch
  INJ["inject movements: list\n(scripted / facilitator)"]:::core
  DOC["standing doctrine order\n(authored per unit)"]:::core

  VAL{"validate:\nunit ∈ ORBAT?\ndest ∈ gazetteer?\nmission legal in\ntransition graph?"}:::core
  HOLD["FAIL → HOLD\nkeep standing order\nrecord_miss + visible line\nprovenance: simulated"]:::core
  APPLY["apply order\nprovenance: adjudicated"]:::core
  KIN2["kinematics.advance()\nonce per resolve_decision\npure · zero RNG · route polylines"]:::core
  SNAP["SpatialSnapshot →\nmailbox + GET /theatre"]:::core
  TRIPS["tripwire eval\ntop of get_turn_briefing\n(confirmed timing)"]:::defer
  EST["fog filter →\nplayer estimates\n(staleness ellipses)"]:::defer
  TRUTH["facilitator view:\nstored positions +\nestimate overlay"]:::defer

  LLM -->|parse| VAL
  INJ --> VAL
  DOC -->|no new order| KIN2
  VAL -->|bad line| HOLD
  VAL -->|valid| APPLY
  HOLD --> KIN2
  APPLY --> KIN2
  KIN2 --> SNAP
  KIN2 -.-> TRIPS
  SNAP -.-> EST
  SNAP -.-> TRUTH

  classDef core stroke-width:3px
  classDef stretch stroke-dasharray:6 3
  classDef defer stroke-dasharray:2 4
```

The safety property is structural: initial coordinates come only from the authored gazetteer at hydration, and every subsequent *movement* coordinate is produced only by `kinematics.advance()` from validated enums — no LLM output ever becomes a coordinate by either path — every failure path converges on HOLD, so a failure leaves a position un-updated (self-correcting next turn), never invented ([study §4a](XR_GLOBE_FEASIBILITY.md#4a-track-b--the-authoritative-spatial-layer), claim 8 conditions).

---

## 3 · The turn, the watch floor, and the one legal tripwire instant

```mermaid
flowchart LR
  B["BRIEFING\ninject applied"] --> D["DISCUSSION\nadvisors, calls"]
  D --> DE["DECISION\ninterpret → commit"]
  DE --> A["ADJUDICATION\n~12 LLM calls\norders parsed here\nkinematics advances here"]
  A --> W["WATCH FLOOR\nengine quiescent\ndesign-paced hold\nglobe projects stored positions\nplayer convenes next turn"]
  W --> T{{"tripwire eval\n(top of next\nget_turn_briefing)"}}
  T -->|"crossing → system inject\n(detected-visibility)"| B2["next BRIEFING"]
  T -->|no crossing| B2

  style W stroke-width:3px
  style T stroke-dasharray:2 4
```

The watch floor is a designed phase, not latency filler — the engine waits indefinitely for the next `POST /briefing` ([study §2.1](XR_GLOBE_FEASIBILITY.md#2-three-findings-restated-under-the-new-framing)). Tripwires fire at exactly one instant, where positions are final and the same turn's inject generator sees the crossing (claim 10, confirmed).

---

## 4 · VR ops room — build order, drawn assuming a Quest headset is available

*(Assumption recorded 2026-08-28: drawn as if [issue #75](https://github.com/earlyprototype/false-flag/issues/75) — "is a Meta Quest VR headset available?" — answers **yes**. The issue stays open until the owner confirms; if it answers no, everything through S1 still ships for desktop-tethered headsets and demo capture — only the on-device Quest steps park.)*

```mermaid
flowchart TD
  WALL["projector war-room wall\nCesium page full-screen\n(the SHOWN artifact at the onsite)"]:::core
  ROOM["three.js WebXR boardroom\nworld-locked wall screens\nsprite cast from the existing\npixel-art pipeline"]:::defer
  S1["S1 · portable screen (build first)\nCesium: useDefaultRenderLoop:false,\nrender() driven from xrSession rAF;\nsame-task canvas→texture copy @≤30Hz;\ncontroller ray → UV → synthetic pointer\nWORKS TODAY desktop-tethered"]:::defer
  SPIKE{"half-day on-device spike:\nCesiumJS flat in Quest Browser\nat usable fps? (UNPROVEN —\nsole public evidence is a\n2021 failure report)"}:::gate
  S2["S2 · promote the panel\nto an XRQuadLayer\n(compositor resamples once →\ncrisp text; Quest Browser ≥16.1)"]:::defer
  S3["S3 · swap the screen source:\nserver renders Cesium →\nWebRTC H.264 → video quad layer\n(~250ms end-to-end; inputs via\nDataChannel → server-side events)"]:::defer

  WALL -->|same page, same data| ROOM
  ROOM --> S1
  S1 --> SPIKE
  SPIKE -->|usable fps| S2
  SPIKE -->|unusable fps| S3

  classDef core stroke-width:3px
  classDef defer stroke-dasharray:2 4
  classDef gate stroke-dasharray:6 3
```

Mechanics the tree encodes: the boardroom and S1 screen are one build (the room renders; the screen is a texture fed by Cesium's canvas under the two hard conditions of study claim 11); the spike is a measurement, not a design choice — its result selects *where the pixels are made* (on the headset → S2, on the server → S3) and nothing else changes, because the room, the cast, the input path, and the data contract are identical in both outcomes.

## 5 · Milestones and decision points (replaces day-counting)

```mermaid
flowchart TD
  M0["M0 · FIRST LIGHT\nglobe attached to a live demo session\nKEY: entities + 1 shader on the projector\nACCEPTABLE: static ORBAT plot, no stream"]:::core
  D0{"D0 · commit?\n#65/#66 merge decision\nmade here too"}:::gate
  M1["M1 · THE FLEET MOVES\ntyped state + kinematics + doctrine legs\nKEY: red fleet advances per turn from engine state,\nsaves round-trip, suite green, bundle rebuilt\nACCEPTABLE: hydrated static positions rendered"]:::core
  D1{"D1 · schedule check"}:::gate
  M2["M2 · STANDARDS ON THE GLASS\nTheatre;1 served, DTMI badges live,\nparser re-run clean\nACCEPTABLE: sidecar served, badges static"]:::core
  M3["M3 · SHOW-SAFE  (non-negotiable)\nrunbook · one-stream rule · proxy stance\nattract loop tuned · cold-restart drill\nRECORDED VIDEO FALLBACK IN HAND"]:::core
  D2{"D2 · ≥3 clear days\nbefore the onsite\nAND M3 done?"}:::gate
  M4["M4 · THE CABINET ORDERS THE MAP\nMOVEMENT call + re-golden commit"]:::stretch
  ONSITE(["ONSITE · 12 Sep · IMR"]):::core
  FINAL(["FINAL · 14 Sep"]):::core
  M5["M5 · post-competition\ntripwires engine · fog/ISR ·\nsnapshot-fed daemon · VR ops room"]:::defer

  M0 --> D0
  D0 -->|proceed| M1
  D0 -->|abort| ALT["fall back: dashboard +\ndataflow demo story"]:::defer
  M1 --> D1
  D1 -->|on schedule| M2
  D1 -->|behind| M3
  M2 --> M3
  M3 --> D2
  D2 -->|yes| M4 --> ONSITE
  D2 -->|no · pause M4| ONSITE
  ONSITE --> FINAL --> M5

  classDef core stroke-width:3px
  classDef stretch stroke-dasharray:6 3
  classDef defer stroke-dasharray:2 4
  classDef gate stroke-width:2px
```

Reading the gates: **D0** is the only abort point — after it, every later decision only *re-orders or pauses* work, never wastes it. **D1** protects M3: standards chrome is droppable, a safe demo is not. **D2** is the LLM-overestimation hedge you asked for — if the timeline estimates were pessimistic and M3 lands early, M4 is pre-authorized; if not, it pauses cleanly to M5 (the design is verified and waiting either way).

Parallel at all times, off-branch: the **Manus queue** — see [issue #70](https://github.com/earlyprototype/false-flag/issues/70) (credits are durable; ordering is build-dependency-driven).
