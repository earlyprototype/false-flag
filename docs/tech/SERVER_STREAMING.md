# FastAPI Sessions and Event Streaming

`api/server.py` owns its own headless game sessions and serves the dashboard,
dataflow view and situation globe. Those API surfaces can share a session ID.

The terminal CLI and static Pyodide browser do **not** attach to those sessions:
each currently creates its own engine instance. Do not describe the current
system as one live session across every playing surface until that connection
is proved.

## How an API surface attaches

1. A client creates an API game session. A caller that asks to facilitate
   receives a separate, opaque capability. Restored sessions currently have
   player authority through the session ID, but no facilitator authority.
2. The globe accepts `?game=<session id>`; the dashboard and dataflow view
   accept a pasted session ID.
3. The shipped globe fetches its current snapshot from
   `GET /game/{id}/theatre`.
4. Player and globe pages open `GET /stream/{id}` for change events. The
   facilitator dashboard and dataflow operator use
   `GET /stream/{id}/facilitator`, which receives a path-scoped stream cookie.

Session-bearing REST responses and decoded stream events pass through the same
server visibility projector. A valid facilitator capability receives the full
payload. Public Classic viewers retain intended gameplay metrics and numeric
effects; public Immersive and Emergent viewers receive qualitative situation
vibes instead. Exact adviser trust, raw actor scores and structured Mystery
state are never public. `GET /game/{id}/state` is the authoritative raw state
and requires the facilitator capability. Player-facing model prompts follow the
same boundary: qualitative bands and relationship words replace exact metrics
and trust, while Mystery truth reaches faction-roleplay prompts only. Hidden
Red objectives and private scenario strategy do not enter public inject prompts.

Public non-Classic projection removes legacy numeric effect-box lines from its
copy of transcript fields. Stored transcripts and facilitator responses remain
unchanged. Audience-dependent `/game/` responses use `private, no-store` and
`Vary: X-Facilitator-Capability`; the common player-safe theatre snapshot keeps
its separate ETag policy.

There is no list-sessions endpoint; `/health` reports only a count.

The v1 theatre body contains `schema_version`, `session_id`, `turn`, `phase`,
and the existing player-visible forces and stockpiles. Its strong ETag is built
from canonical visible JSON. Exact `If-None-Match` revalidation returns 304;
responses carry `Cache-Control: private, no-cache`. It is a common player-safe
projection, not a facilitator view. Session IDs are not authentication.

## What the stream carries

Engine and API actions call `push_event` or `push_event_threadsafe`. Events are
stamped with layer, turn, elapsed time and sequence. Current event families
include transcript, system, state update, diplomacy, intelligence, ending,
inject, adjudication, parse health and LLM-call records.

REFEREE-layer data is filtered server-side per connection. Untagged events also
fail closed for public viewers. Other public events are projected for the
session's play mode before delivery; REFEREE events and unprojected payloads
reach only a connection presenting the session's facilitator capability. The
session ID alone never grants that authority. Qualitative vibes are stamped at
event emission, so a delayed subscriber does not receive present-time vibes on
an older event.

## Current delivery model

Each active subscriber owns an independent `asyncio.Queue`. `GameSession`
copies every event before delivery, so filtering one subscriber's copy cannot
alter another's. Events emitted with no active subscriber wait for the first
subscriber, preserving the cold open and briefing produced before EventSource
can attach. `stream_ready` is emitted only after subscriber registration and
triggers the globe's reconnect snapshot. Subscriber queues are removed on
disconnect.

The dashboard keeps its control capability in tab-scoped `sessionStorage` and
sends it in the `X-Facilitator-Capability` header on session controls. Session
creation also sets the same value in an HttpOnly, SameSite cookie scoped only
to `/stream/{id}/facilitator`; this lets a separately opened dataflow operator
view use native `EventSource` without exposing the bearer in an access-log URL.
Without that cookie the operator path receives the public stream. The globe
uses the public path, so the browser never sends the cookie to it.

`event_seq` orders delivery; `turn` and `t_plus_s` record emission. A worker
event may therefore carry an earlier T+ than a lower-sequence event published
directly on the loop. Subscriber queues and the no-subscriber backlog remain
unbounded. The theatre snapshot, not this queue history, restores the globe
after attach or reconnect.

The shipped consumers are:

- `/dashboard` — capability-bearing facilitator observability and controls.
- `/dataflow` — DTDL/dataflow operator view, public without a capability.
- `/globe` — public situation globe.

The dashboard, dataflow view and globe may now observe the same API session
concurrently with permissions decided for each connection.

## Remaining Slice 1 work

Slice 1, **Multi-client Session Streaming**, is defined in
[`PLAN.md`](../../PLAN.md#1--multi-client-session-streaming). The fan-out and
two-subscriber regression, the shared REST/SSE visibility projector and the v1
player-safe theatre snapshot are complete. The shared API player proof and
deployment authentication remain. The local capability separates viewers
within one API session; it is not an account or login system.

SSE remains a change-notification path. The snapshot—not queue history—is what
restores a reconnecting display.

## Evidence

- [`api/server.py`](../../api/server.py), sections `GameSession`,
  `_project_for_viewer`, `_stream_filter` and `stream_game_events`.
- [`api/globe.html`](../../api/globe.html), session snapshot and `EventSource`
  setup.
- [`tests/test_api_server.py`](../../tests/test_api_server.py), theatre endpoint
  and Situation Globe contract checks.
- [`tests/test_dashboard_api.py`](../../tests/test_dashboard_api.py),
  request-scoped stream filtering and facilitator-control checks.
- [Canonical Slice 1](../../PLAN.md#1--multi-client-session-streaming).
