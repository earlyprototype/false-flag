# Situation Globe and Ops Room — Build Plan

**This is the canonical implementation plan.** It describes what is built, what
comes next, and the observable test that completes each slice. Supporting
documents explain the evidence; they do not define a competing sequence.

## Product centre

FALSE FLAG remains the AI wargame described in the
[README's session walkthrough](README.md#what-happens-in-a-session): a
multi-turn crisis in which the player questions five cabinet advisers, handles
diplomatic pressure, makes a free-form decision, receives pushback, and lives
with the adjudicated consequences.

The Situation Globe, live context and VR operations room deepen that same
campaign. They are not a replacement game, a generic agent demonstration, or
a dashboard product.

The end-to-end acceptance path is one authentic turn:

1. A crisis briefing arrives, including bounded live context where relevant.
2. The player questions the five cabinet advisers and receives distinct advice.
3. A diplomatic encounter or other campaign pressure may interrupt.
4. The player makes a free-form decision and answers any pushback.
5. The engine interprets and adjudicates the decision.
6. Campaign consequences update the same session, globe and VR room.
7. The next turn continues from the resulting state.

[Owner ruling, 1 September 2026](https://github.com/earlyprototype/false-flag/issues/136#issuecomment-5499898594):
implementation estimates do not decide scope or cut features. Work is sequenced
by dependencies and observable done tests.

## Current status

| Item | What it delivers | Status | Evidence |
|---|---|---|---|
| **Globe Display** | Read-only Cesium globe showing scenario resources | `DONE` — projector test passed 31 Aug 2026 | [Issue #94](https://github.com/earlyprototype/false-flag/issues/94) · [PR #95](https://github.com/earlyprototype/false-flag/pull/95) · [PR #104](https://github.com/earlyprototype/false-flag/pull/104) |
| **1 · Multi-client Session Streaming** | One played campaign observed reliably by several surfaces | `NOT STARTED` | — |
| **2 · Spatial Decision Loop** | Campaign forces move from authored state and validated player orders | `NOT STARTED` — movement design settled | [Issue #71](https://github.com/earlyprototype/false-flag/issues/71) |
| **3 · Live Context Integration** | Real external context appears around, and may inform, the fictional exercise | `NOT STARTED` — boundary and live-first posture settled | [Issue #77](https://github.com/earlyprototype/false-flag/issues/77) |
| **4 · Quest Ops-Room Display** | The existing game is present inside a WebXR operations room | `NOT STARTED` — build order settled; device availability open | [WebXR brief](docs/tech/WEBXR.md) · [Issue #75](https://github.com/earlyprototype/false-flag/issues/75) |
| **5 · Demonstration Reliability and Submission** | The authentic game turn can be launched, shown, recovered and submitted | `NOT STARTED`; reliability work runs throughout | — |

Slice 1 is the shared dependency. Once its session contract is stable, spatial,
live-data and VR work may proceed independently; the numbers show integration
order, not elapsed-time estimates.

## Completed foundation — Globe Display

*Technical descriptor: serve a read-only Cesium globe that plots scenario
resources and responds to events from one API session.*

Completed in [PR #95](https://github.com/earlyprototype/false-flag/pull/95),
with follow-ups in PRs
[#104](https://github.com/earlyprototype/false-flag/pull/104),
[#106](https://github.com/earlyprototype/false-flag/pull/106) and
[#108](https://github.com/earlyprototype/false-flag/pull/108).

Current limits are explicit:

- It plots UK forces at authored base locations; it does not yet show moving
  red-force tracks.
- An event refreshes the display but does not yet move a unit.
- The session stream is destructive and safe for only one subscriber.
- No external live feed or XR room exists yet.

## 1 · Multi-client Session Streaming

*Technical descriptor: give every subscriber an independent event delivery
path and expose session-scoped snapshots to the player, dashboard, globe and
VR room.*

### Build

- [ ] Select one API-backed player: either restore and complete the checked-in
      Next client or port one maintained client onto the API. Do not build both.
      The chosen client must run each later turn through
      `POST /game/{session_id}/briefing`; the current Next source omits that
      call and cannot yet play a complete campaign.
- [ ] Replace the single destructive session queue with per-subscriber queues;
      copy each payload before audience filtering.
- [ ] Scope theatre snapshots and view permissions to a game session.
- [ ] Publish a versioned theatre snapshot with an ETag; use SSE as change
      notification rather than as the only state store.
- [ ] Prove the selected player uses the same API session observed by the
      dashboard and globe. Do not claim that the terminal CLI or static
      Pyodide build is attached until it actually is.
- [ ] Keep REFEREE data server-filtered and require authentication before any
      control surface leaves localhost.
- [ ] Add a regression check in which two subscribers receive every event.
- [ ] Add the `Theatre;1` and `TheatreAsset;1` DTDL sidecars without modifying
      the 13 published interfaces; re-run Microsoft's DTDL parser.

### Done test

A real API-played campaign, dashboard and globe share one session ID; two
simultaneous subscribers each receive every permitted event; reconnecting from
the snapshot restores the current display.

## 2 · Spatial Decision Loop

*Technical descriptor: persist unit tracks, advance authored routes with pure
kinematics, and translate decision text into validated orders that visibly
change the campaign.*

### Build

- [ ] Add `UnitTrack`, `MovementOrder` and `SpatialState`, including standing
      orders, bounded order history and fired-tripwire latches.
- [ ] Hydrate scenario units from sourced gazetteer entries at new game and
      load.
- [ ] Advance positions once per turn along authored route polylines with
      deterministic, zero-RNG kinematics.
- [ ] Publish the resulting snapshot to the theatre endpoint and interpolate
      only for display between authoritative turn boundaries.
- [ ] Derive the player intelligence picture from authoritative tracks. The
      facilitator may see stored positions; the player sees only bounded,
      stale or noisy estimates where the scenario permits them.
- [ ] Add the bounded movement-order call settled in
      [issue #71](https://github.com/earlyprototype/false-flag/issues/71): the
      model emits unit, mission, named destination and speed band; it never
      emits coordinates.
- [ ] Validate every order against the unit registry, gazetteer and mission
      legality rules. Bad or incomplete output creates no new order, visibly
      reports the miss, and leaves the last standing order active.
- [ ] Evaluate authored spatial tripwires at the start of the next briefing so
      movement can become campaign news.
- [ ] Persist and verify tracks, orders and tripwire state across save, load and
      resume; rebuild the browser play bundle after any `WorldState` change.

### Done test

During an authentic turn, a free-form player decision produces a validated
order, the intended unit moves, the globe shows that consequence, and the next
briefing can react to a crossed boundary. A deliberately malformed model reply
moves nothing new and reports the failure. Save/load/resume preserves the same
positions and standing orders. The player view never exposes hidden
authoritative positions. In a seeded hidden-track case, the facilitator sees
the stored position while the player receives a bounded stale or noisy estimate
that is visibly distinct from that position.

## 3 · Live Context Integration

*Technical descriptor: ingest bounded real-world feeds into separate Cesium
layers and adviser context without allowing external data to mutate game
state.*

### Build

- [ ] Resolve campaign-clock coherence before live observations enter adviser
      prompts: move the campaign date to "now," treat current conditions as an
      explicitly present-day exercise baseline, or keep them spectator-only.
      Record the owner choice; do not let September 2026 weather masquerade as
      an October 2025 observation.
- [ ] Weather first: sample current conditions at checked scenario gazetteer
      points through Open-Meteo, cache them, display observation time and
      source health, and—if the clock ruling permits—place the bounded summary
      in `WorldReference.environmentalFactors` with its temporal framing.
- [ ] Add one bounded civilian-flight layer outside the exercise-zone polygon.
      Select the provider only after its current data terms permit the intended
      demo use.
- [ ] Keep real and fictional entities in independent Cesium data sources.
- [ ] Apply the owner-set boundary from
      [issue #77](https://github.com/earlyprototype/false-flag/issues/77): real
      context outside the exercise zone; simulated campaign layers own the
      consequential picture inside it; fog carries the transition on the
      player surface.
- [ ] External data may inform adviser context but never write gauges,
      positions, orders or outcomes.
- [ ] Record provider, observation time, ingestion time and availability for
      the after-action journal.
- [ ] Use recorded external responses only in automated tests. There is no
      silent runtime fallback: an unavailable or stale source is shown as
      unavailable or stale.
- [ ] Preserve every required provider and map attribution.

### Done test

Current weather changes a visible environmental layer and obeys the recorded
campaign-clock rule; when adviser use is permitted, the response states the
correct temporal framing and game state remains unchanged. Live civilian
tracks remain outside the exercise zone. Disconnecting either provider
produces an explicit source-health failure rather than fabricated live data.

## 4 · Quest Ops-Room Display

*Technical descriptor: put the existing campaign surfaces into a portable
three.js/WebXR room, measure the real headset, then select a local quad layer or
a streamed screen source.*

### Build

- [ ] Build the portable room and world-locked screen first. The room uses the
      existing game session, transcript and globe; it does not create another
      simulation.
- [ ] Use the existing stylised art direction for adviser presence and keep
      dialogue driven by real transcript events.
- [ ] Measure the portable build on the available Quest: frame rate, frame
      time, thermal behaviour, text legibility, input latency and recovery
      after headset sleep.
- [ ] If local globe rendering meets the recorded device budget, promote the
      screen to an `XRQuadLayer` for legibility.
- [ ] If it does not, keep the same room and use a server-rendered H.264/WebRTC
      video source on a media quad layer; return input through an authenticated
      data channel.
- [ ] Provide captions, a flicker-free visual mode and a motion-comfort mode.

### Done test

On the Quest, the player can enter the room, read the situation screen, hear or
read the real cabinet exchange, and watch the same campaign consequence shown
on the projector. The recorded measurements—not preference—identify the local
quad-layer or streamed-source path.

## 5 · Demonstration Reliability and Submission

*Technical descriptor: secure, rehearse, measure, recover and present one full
FALSE FLAG turn using the real game path.*

This work starts alongside Slice 1 and continues as the build changes.

### Build

- [ ] Write the authentic-turn sequence from briefing through the next-turn
      consequence; the dashboard is supporting evidence, not the product.
- [ ] Keep the launch and recovery procedure reproducible on the demonstration
      machine; measure restart rather than guessing it.
- [ ] Bind control surfaces safely and authenticate anything reachable beyond
      localhost.
- [ ] Rehearse the real network path and a source-unavailable state.
- [ ] Record a real run as hardware-failure contingency, clearly marked as an
      exercise recording.
- [ ] Demonstrate the agent roles through the existing game: distinct advice,
      disagreement, memory, pushback, human authority and adjudicated
      consequences.
- [ ] Obtain and record mentor approval for FALSE FLAG as an alternative
      Challenge entry unless an organiser maps it to an official statement;
      evidence the real user, credible buyer or commissioner, current cost of
      the problem and why an agentic approach is justified.
- [ ] Capture named playtester or mentor feedback and retain sources for every
      customer, competitor and commercial claim used in the presentation.
- [ ] Support the challenge presentation with evidence of the game already
      built and a clearly identified 28 Aug–13 Sep contribution; do not present
      pre-existing work as new.
- [ ] Prepare the editable presentation and demo link required by the official
      participant playbook.

### Done test

The complete turn runs from the written sequence without operator invention;
the recovery procedure works; the recording exists; and the editable deck plus
demo link are ready for submission.

## Challenge facts — external constraints, not scope estimates

- Build period: 28 August–13 September 2026.
- Final submission: 13 September 2026 at 14:00 Irish time.
- Regional demonstration at Irish Manufacturing Research: 14 September 2026;
  seven-minute presentation followed by three minutes of questions.
- Theme: **AI & Agents: Strategy, Processes and Roles**.
- Team eligibility: 4–9 members including one team leader. Confirm the
  registered team still complies; the formation deadline has passed.
- Judging covers the problem and customer, the working solution, commercial
  focus, and effective and responsible use of AI.

Theme fit is not entry approval. The playbook requires an official Challenge
statement or a mentor-approved alternative; the catalogue requires a wildcard
to identify a real user, buyer or commissioning body, current problem cost and
why agentic AI is justified. Those are open compliance gates, not claims to
invent for the deck.

The official sources are the
[2026 Participant Playbook](https://docs.google.com/document/d/1bYT1itRT6h0YU4i8uGbEUK78dJYa6z561qSe6tjSkNs/edit?usp=sharing),
[2026 Challenge Catalogue](https://docs.google.com/document/d/1D2rQhMPmqIFsCMyi_QPxVJCQQQYZ_phuHkdfz69UoX8/edit?usp=sharing),
and [AICC event page](https://www.aicc.co/events/2026/september-2026/techireland-national-ai-challenge-2026).

## Technical references

- [Owner ruling: live-hybrid boundary and live-first operation](https://github.com/earlyprototype/false-flag/issues/77)
- [Owner ruling: validated movement orders](https://github.com/earlyprototype/false-flag/issues/71)
- [God's Eye View at the analysed commit](https://github.com/bilawalsidhu/gods-eye-view/tree/314a0e1)
- [God's Eye View data-source and attribution register at the analysed commit](https://github.com/bilawalsidhu/gods-eye-view/blob/314a0e1/DATA_SOURCES.md)
- [Open-Meteo licence](https://open-meteo.com/en/license)
- [OpenSky terms of use](https://opensky-network.org/about/terms-of-use)
- [WebXR Layers specification](https://immersive-web.github.io/layers/)
- [Microsoft DTDL parser](https://github.com/digitaltwinconsortium/DTDLParser)

## Other owner-scheduled capabilities

These remain recorded without an agent-assigned date or cut ruling:

- Real-channel email inject — [issue #76](https://github.com/earlyprototype/false-flag/issues/76).
- Voice production — [issue #78](https://github.com/earlyprototype/false-flag/issues/78).
- Further visual-design controls — [issue #92](https://github.com/earlyprototype/false-flag/issues/92).

## Supporting documents

- [Current engineering state](docs/BUILD_STATE.md)
- [Plain-language owner brief](docs/OWNERS_BRIEF.md)
- [Technical feasibility evidence](docs/XR_GLOBE_FEASIBILITY.md)
- [Current component map](docs/XR_GLOBE_COMPONENT_MAP.md)
- [Technology briefs](docs/tech/README.md)
- [Historical handovers](docs/handover/README.md)
