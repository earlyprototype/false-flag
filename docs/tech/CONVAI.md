# Convai — Optional Avatar Service

Convai is not part of the current build dependency chain. No Convai integration
exists in this repository, and the portable WebXR operations room must work
without it.

## Project boundary

- FALSE FLAG's existing engine remains the only source of adviser reasoning,
  dialogue and campaign state.
- The VR room uses real transcript events from that engine.
- Initial adviser presence uses the existing stylised art direction and does
  not depend on a hosted avatar SDK.
- A future avatar service may perform already-generated lines, voices or
  lip-sync, but it must not become a second game brain.

This prevents avatar integration, account state, pricing or venue internet from
blocking the operations-room screen and full game turn.

## When this document becomes active again

Re-evaluate Convai only when the portable room, shared session and transcript
animation are working and the owner explicitly schedules richer embodiment.
At that point, re-check current official SDK capabilities, pricing, data terms
and browser support; do not rely on the August 2026 comparison preserved in
historical strategy material.

## Current references

- [Canonical Quest slice](../../PLAN.md#4--quest-ops-room-display)
- [WebXR room brief](WEBXR.md)
- [Voice-production issue #78](https://github.com/earlyprototype/false-flag/issues/78)
