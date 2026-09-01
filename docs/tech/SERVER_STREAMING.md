# The laptop server and its event stream

One FastAPI server (`api/server.py`) running on the laptop is the spine every
surface attaches to. It owns the game sessions, serves every page, and pushes
live events over SSE. Anything that shows the game — dashboard, dataflow,
globe, a future VR room — attaches to this server.

## How a surface attaches

1. **Session id in the URL.** Pages take `?game=<session id>`. There is no
   list-games endpoint (`/health` reports only an active-session count), so
   a page opened without an id asks for one to be pasted, or points at
   `/dashboard`, where a session is started.
2. **Snapshot fetch.** The page fetches state — the globe reads
   `GET /game/{id}/resources` and plots every unit.
3. **Live stream.** The page opens an `EventSource` on
   `GET /stream/{session_id}` (SSE, via sse-starlette) and refreshes its
   snapshot when events arrive.

## What flows on the stream

Each running session (`GameSession`) owns one `asyncio.Queue`. Engine code
pushes through `push_event` / `push_event_threadsafe`, which stamp layer,
turn, T+ and sequence onto every item. Event types the globe subscribes to:
`transcript`, `system`, `state_update`, `diplomacy`, `intel`, `ending`,
`inject_fired`, `adjudication`, `parse_health`, `llm_call`. Events carry a
server-side layer tag: the REFEREE layer (raw adjudication effects, LLM call
records, parse health) is filtered out of player streams server-side and
reaches only sessions created with the facilitator flag (`_stream_filter`).

## The limit: a destructive single-consumer stream

`/stream/{id}` reads from that one queue, so a read removes the event. The
header comment of `api/globe.html` states the concern verbatim:

> ONE CONSUMER ONLY. /stream/{id} is a destructive single-consumer queue
> until Stage 3's per-subscriber fan-out lands: a second reader (a dashboard
> tab on the same session) steals events from this page.

Practical consequence: attach at most one live surface per session. A second
tab does not error — each consumer silently receives only a subset of the
events, which presents as a flaky page.

**The planned fix is Stage 3 of PLAN.md** ("Theatre API and Multi-Client Streaming", status
NOT STARTED): per-subscriber fan-out on the session event bus, with
per-subscriber payload copies. Its done test is exactly this limit removed —
two browsers on the same session each receive every event.

## Surfaces that consume the stream today

Three shipped pages each open an `EventSource` on `/stream/{id}`:

- `/globe` (`api/globe.html`) — the situation globe.
- `/dashboard` (`api/dashboard.html`) — observability panels and controls.
- `/dataflow` (`api/dataflow.html`) — the digital-twin model view.

All three are served by this same server as self-contained HTML with no
build step. Until the fan-out exists they contend for the same queue, so run
one of them per session.
