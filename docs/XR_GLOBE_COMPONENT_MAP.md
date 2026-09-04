# Situation Globe and VR Operations Room — Component Map

This is the visual companion to [`PLAN.md`](../PLAN.md). The plan owns sequence
and status; this file shows the target data relationships. Labels in the first
diagram distinguish what exists from what the build adds.

## 1 · One game, several surfaces

```mermaid
flowchart LR
  PLAYER["PLAYED FALSE FLAG SESSION\nbriefing · advisers · diplomacy\ndecision · adjudication"]

  subgraph ENGINE["HEADLESS GAME ENGINE"]
    GM["CURRENT · GameManager\ncampaign authority"]
    SPATIAL["PLANNED · SpatialState\ntracks · standing orders"]
    KIN["PLANNED · Kinematics\nauthored deterministic movement"]
    TRIP["PLANNED · Tripwires\nmovement becomes campaign news"]
  end

  subgraph LIVE["LIVE EXTERNAL CONTEXT"]
    WX["PLANNED · Weather\nOpen-Meteo"]
    CIV["PLANNED · Civilian tracks\nprovider after terms gate"]
    INGEST["PLANNED · Bounded ingestion\ncache · validate · timestamp"]
  end

  subgraph API["SESSION API"]
    SNAP["CURRENT V1 · Session theatre snapshot\nETag · reconnectable · player-safe"]
    FAN["CURRENT · Subscriber fan-out\nper-surface filtering"]
  end

  subgraph SURFACES["SUPPORTING SURFACES AROUND THE SAME CAMPAIGN"]
    DASH["CURRENT · Dashboard\nsupporting evidence and control"]
    GLOBE["CURRENT FOUNDATION · Cesium globe\nstatic campaign resources"]
    VR["PLANNED · WebXR operations room\nglobe screen + adviser presence"]
  end

  PLAYER --> GM
  GM --> SNAP
  GM --> SPATIAL --> KIN --> SNAP
  KIN --> TRIP --> GM
  GM --> FAN
  WX --> INGEST
  CIV --> INGEST
  INGEST -->|"after clock ruling · bounded facts only"| GM
  INGEST -->|"read-only live layers"| GLOBE
  SNAP --> GLOBE
  SNAP --> VR
  FAN --> DASH
  FAN --> GLOBE
  FAN --> VR
```

The engine owns campaign state. External feeds and displays do not write it.
Live facts may enter bounded adviser context under
[issue #77](https://github.com/earlyprototype/false-flag/issues/77), but never
write metrics, positions, orders or outcomes.

## 2 · One authentic turn

```mermaid
flowchart LR
  B["BRIEFING\nscripted/generated inject\n+ temporally framed live context"]
  C["CABINET DISCUSSION\nfive adviser roles"]
  P["DIPLOMATIC PRESSURE\nwhen the campaign requires it"]
  D["FREE-FORM DECISION\ninterpret · pushback · confirm"]
  A["ADJUDICATION\nconsequences + validated order"]
  M["SHARED CAMPAIGN VIEW\nstate · globe · VR room"]
  N["NEXT TURN\ncontinues from consequences"]

  B --> C --> P --> D --> A --> M --> N --> B
```

This loop—not the dashboard by itself—is the product acceptance path.

## 3 · How a campaign position is written

```mermaid
flowchart TD
  DECISION["Player decision text"]
  LLM["Movement interpretation\nunit · mission · named destination · speed band"]
  INJECT["Authored/facilitator movement"]
  VALIDATE{"Known unit?\nKnown place?\nLegal mission?"}
  HOLD["No new order\nvisible failure\nstanding order remains"]
  ORDER["Validated standing order"]
  KIN2["kinematics.advance()\nauthored route · zero RNG"]
  STATE["Authoritative SpatialState"]
  VIEW["Snapshot → globe and VR"]

  DECISION --> LLM --> VALIDATE
  INJECT --> VALIDATE
  VALIDATE -->|no| HOLD --> KIN2
  VALIDATE -->|yes| ORDER --> KIN2
  KIN2 --> STATE --> VIEW
```

Only gazetteer hydration and deterministic kinematics write coordinates. The
model never does. Source: settled movement design in
[issue #71](https://github.com/earlyprototype/false-flag/issues/71).

## 4 · Live/fictional boundary

```mermaid
flowchart LR
  REAL["OUTSIDE EXERCISE ZONE\nreal live context"]
  EDGE["ZONE EDGE\nspatial transition carried by fog"]
  GAME["INSIDE EXERCISE ZONE\nfictional campaign layers own\nconsequential information"]

  REAL --> EDGE --> GAME
```

The player surface does not explain this boundary with crude per-layer labels.
Spectator and recording surfaces use diegetic `EXERCISE` marking. Provider,
freshness and availability remain inspectable in the after-action record.

## 5 · VR screen build order

```mermaid
flowchart TD
  ROOM["Portable three.js/WebXR room\nworld-locked situation screen"]
  TEST["Measure on the real Quest\nframe time · thermal · legibility\ninput latency · sleep recovery"]
  PASS{"Local rendering meets\nrecorded device budget?"}
  LOCAL["Local screen source\nXRQuadLayer"]
  STREAM["Server-rendered source\nH.264/WebRTC media quad layer"]

  ROOM --> TEST --> PASS
  PASS -->|yes| LOCAL
  PASS -->|no| STREAM
```

The measurement chooses where the screen pixels are produced; the room, game
session and input contract stay the same. Technical basis:
[WebXR Layers specification](https://immersive-web.github.io/layers/).

## 6 · Build streams and dependency

```mermaid
flowchart LR
  CORE["CORE GAME INTEGRITY\none player · modes · Mystery"]
  DONE["COMPLETED FOUNDATION\nGlobe Display"]
  SHARED["SHARED CAMPAIGN & SURFACES\nnext: dashboard + dataflow"]
  SPATIAL["SPATIAL DECISION LOOP\ntracks + movement + tripwires"]
  LIVE2["LIVE CONTEXT\nweather + bounded civilian tracks"]
  XR["XR OPS ROOM\nportable → measured → local/streamed"]
  REL["DELIVERY RELIABILITY\ncross-cutting support"]

  CORE --> SHARED
  DONE --> SHARED
  SHARED --> SPATIAL
  SHARED --> LIVE2
  SHARED --> XR
  REL -.-> SHARED
  REL -.-> SPATIAL
  REL -.-> LIVE2
  REL -.-> XR
```

Core Game Integrity constrains every change. Shared Campaign & Surfaces is the
common dependency; its immediate proof is one dashboard and one dataflow view
attached to the same campaign. Spatial, Live Context and XR can then advance
independently. Delivery reliability runs throughout rather than becoming a
sixth product stream.

## References

- [Canonical plan](../PLAN.md)
- [Current build state](BUILD_STATE.md)
- [Full feasibility evidence](XR_GLOBE_FEASIBILITY.md)
- [Owner live-hybrid ruling](https://github.com/earlyprototype/false-flag/issues/77)
- [God's Eye View source at analysed commit](https://github.com/bilawalsidhu/gods-eye-view/tree/314a0e1)
- [God's Eye View data-source register at the analysed commit](https://github.com/bilawalsidhu/gods-eye-view/blob/314a0e1/DATA_SOURCES.md)
