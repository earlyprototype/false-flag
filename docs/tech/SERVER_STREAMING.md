# FastAPI Sessions and Event Streaming

`api/server.py` owns its own headless game sessions and serves the dashboard,
dataflow view and situation globe. Those API surfaces can share a session ID.

The terminal CLI and static Pyodide browser do **not** attach to those sessions:
each currently creates its own engine instance. Do not describe the current
system as one live session across every playing surface until that connection
is proved.

## How an API surface attaches

1. A client creates or restores an API game session.
2. Observer pages receive `?game=<session id>`.
3. Each page fetches its current snapshot. The shipped globe currently reads
   `GET /game/{id}/resources`.
4. Each page opens `GET /stream/{id}` for change events.

There is no list-sessions endpoint; `/health` reports only a count.

## What the stream carries

Engine and API actions call `push_event` or `push_event_threadsafe`. Events are
stamped with layer, turn, elapsed time and sequence. Current event families
include transcript, system, state update, diplomacy, intelligence, ending,
inject, adjudication, parse health and LLM-call records.

REFEREE-layer data is filtered server-side. It must never be sent to an
ordinary player and must remain protected when multi-subscriber delivery is
implemented.

## Current defect: destructive delivery

Each `GameSession` owns one `asyncio.Queue`. Reading an item removes it. If the
dashboard and globe subscribe together, neither receives a complete copy; the
failure looks like intermittent missing updates rather than a clear error.

The shipped consumers are:

- `/dashboard` — observability and controls.
- `/dataflow` — DTDL/dataflow view.
- `/globe` — situation globe.

Until Slice 1 is complete, use only one live subscriber per API session.

## Required fix

Slice 1, **Multi-client Session Streaming**, is defined in
[`PLAN.md`](../../PLAN.md#1--multi-client-session-streaming). It requires:

- one independent queue per subscriber;
- a copied payload before audience filtering;
- a session-scoped, reconnectable theatre snapshot with an ETag;
- teardown of subscriber queues on disconnect;
- a regression check proving two simultaneous clients each receive every
  permitted event.

SSE remains a change-notification path. The snapshot—not queue history—is what
restores a reconnecting display.

## Evidence

- [`api/server.py`](../../api/server.py), sections `GameSession`,
  `push_event`, `_stream_filter` and `stream_events`.
- [`api/globe.html`](../../api/globe.html), session snapshot and `EventSource`
  setup.
- [`tests/test_api_server.py`](../../tests/test_api_server.py), Situation Globe
  endpoint and resource-contract checks.
- [Canonical Slice 1](../../PLAN.md#1--multi-client-session-streaming).
