# Tech element briefs

One short, factual brief per technology element, written for future agents and
sessions picking this project up cold, so established facts stop being
re-derived in conversation. Each brief states what the element is, its role
here, verified integration facts, constraints and risks, and the current
decision state.

Facts verified against the repo as of 1 Sep 2026 — version-pinned details
(CesiumJS versions, Quest Browser versions, ruling dates) may age; each brief
cites its sources so they can be re-checked.

- [WEBXR.md](WEBXR.md) — browser-delivered VR: option B of open route decision #127, its strengths, and its three known weaknesses.
- [CESIUM.md](CESIUM.md) — the globe engine: exactly how the shipped `/globe` page uses CesiumJS today, and the in-room-screen question on each VR route.
- [CONVAI.md](CONVAI.md) — the avatar embodiment layer, never the brain: puppet mode vs conversational mode, SDK facts, and the cloud dependency.
- [QUEST3.md](QUEST3.md) — Meta Quest 3 hardware facts, sourcing state (#75), and what to plug in on day one.
- [SERVER_STREAMING.md](SERVER_STREAMING.md) — the laptop FastAPI server as the spine: how surfaces attach, the destructive single-consumer stream limit, and Stage 3's planned fan-out.
