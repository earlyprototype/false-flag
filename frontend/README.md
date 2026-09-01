# Situation Room Frontend — Incomplete Source Snapshot

This directory contains a Next.js/React client for `api/server.py`. Its pages
already call the game, discussion, decision, diplomacy, saved-game listing and
load, and SSE endpoints; it is not a mock-only UI. It has no save-game call.

It is **not runnable from the current tree** because `package.json`, the lock
file, TypeScript configuration and component metadata are absent. Commands such
as `npm install` and `npm run dev` therefore fail here. Do not use this README
as a setup guide or claim this client as a demonstrated surface until its build
is deliberately restored and verified.

There is also a known campaign-flow gap: the current page acknowledges turn
one's briefing but never calls `POST /game/{session_id}/briefing` for later
turns, so later injects, effects and mandatory encounters would be skipped.

## What is present

- `app/page.tsx` — API-backed game screen and SSE client.
- `app/start/page.tsx` — scenario and save selection.
- `components/` — game panels and shared UI pieces.
- Next, Tailwind and PostCSS configuration fragments.

## What is authoritative today

- The terminal CLI and static Pyodide browser are the maintained playing
  surfaces.
- The FastAPI session endpoints are real and tested.
- `/dashboard`, `/dataflow` and `/globe` are self-contained FastAPI-served
  observer/control pages.
- The CLI and static browser do not currently share an API session with those
  observer pages.

Current integration work is defined by
[`PLAN.md` — Multi-client Session Streaming](../PLAN.md#1--multi-client-session-streaming)
and documented in
[`docs/tech/SERVER_STREAMING.md`](../docs/tech/SERVER_STREAMING.md).

## If this client is selected later

Recover or recreate only the missing build metadata, add the missing later-turn
briefing call, pin compatible versions, run a production build, and test one
complete game turn against the current API before changing this status. Do not
maintain a second frontend simply because
source files are present.
