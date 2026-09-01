# Decision Briefs — what each open call needs, when it's due, and the default

*Companion to `BUILD_STATE.md`. Principle: no decision is due before the milestone that needs it; every decision has a safe default. The owner gave GO on 30 Aug; M0 (First Light) shipped in PR #95 and is `DONE` — the projector done-test passed 31 Aug. B1 (the build stage every movement design shares: the position system with no AI) requires none of the remaining open decisions.*

| # | Decision | Due at | Context source | Default if silent |
|---|---|---|---|---|
| N1 | Movement architecture ([#71](https://github.com/earlyprototype/false-flag/issues/71)) | **SETTLED 28 Aug — orders on** | This page, §below | Hybrid selected |
| N2 | Geo-pack home (issue [#72](https://github.com/earlyprototype/false-flag/issues/72): which folder the map's data files live in) | **RULED 1 Sep — SPLIT** | Ruling on the closed issue | Scenario truth with the scenario, engine-derived with the tech, accounting across the seam |
| N3 | Demo campaign variant (issue [#73](https://github.com/earlyprototype/false-flag/issues/73): which campaign cut the users watch) | **Now timeable** — M0 is done; interacts with [#89](https://github.com/earlyprototype/false-flag/issues/89), which may drop `fast_start` | Stopwatch two mock runs against `main` | Time both, then pick |
| N4 | Default globe register (issue [#74](https://github.com/earlyprototype/false-flag/issues/74): bare satellite Earth vs the CRT filter as the globe's default look) | **RULED 31 Aug — all options stay** | Ruling on the closed issue | Bare Earth working default; FLIR + CRT switches live (PR #106); revisit late dev |
| — | Quest availability — is a Meta Quest VR headset available? (a yes/no to record in issue [#75](https://github.com/earlyprototype/false-flag/issues/75)) | Before the VR spike | A fact, not a reading | S3 (streamed screen) path assumed |
| — | Save downgrade loss | B1 | Executed probe, study claim 9 | Accept + document + version bump 2.4→2.5 |

---

## N1 decision record: the cabinet's words move ships

All three designs share ~80% of the build — `models/spatial.py`, `engine/kinematics.py`, the gazetteer (the hand-checked lookup table of ~30 authored locations), red doctrine legs, save discipline. **Stage B1 is identical under every option.** They diverge only on who issues *blue* movement orders after B1:

**The hybrid (default)** — during adjudication, one added, non-blocking, cheap LLM call reads the decision round and emits up to 8 structured orders (`ORDER: unit | mission | destination | speed`) — never coordinates. Orders are validated against the ORBAT (the scenario's order of battle — the unit list), the ~30-place gazetteer, and a per-unit mission legality graph (red cannot jump rendezvous→strike, mirroring the episodes' escalation ordering). Clean parses apply with provenance `adjudicated`; partial parses apply valid lines and visibly skip bad lines; empty, truncated, or failed calls issue zero new orders, every unit continues its last validated standing order, and kinematics advances. Plus: readiness as live state (HMS PoW's — HMS Prince of Wales's — 3-turn rule renders), route polylines (ships follow sea lanes), and detected-visibility tripwires (an unseen crossing reaches the player later as ambiguous intel). **You get**: "move the carrier group to the GIUK gap" in the decision text actually moves it; advisors can then argue from real geometry. **You pay**: one more LLM call family, one deliberate re-golden commit, and the guard-rail discipline (all specified, all verified feasible — study claim 8).

**IRONCLAD pure (zero-LLM)** — no movement call at all; units follow authored doctrine and posture templates only. **You get**: perfect determinism, zero parse surface, the red fleet's dread-clock advance intact. **You pay**: the player's spatial intent is silently dropped every turn — geography is watchable, never playable. Honest fallback position; also exactly what the hybrid degrades to when its LLM call fails, so choosing it later loses nothing already built.

**TASKORD pure** — the hybrid minus the legality graph, readiness, and route polylines. Saves a few days; loses the pieces that keep red honest and make the map feel inhabited. Only worth it under extreme schedule pressure — and D1's (the schedule-check decision gate's) cut goes to M2 (Standards on the Glass — the digital-twin standards badges) / M3 (Show-Safe) first anyway.

**Ruling**: use the hybrid validated-order channel. Scheduling decides whether
it lands before 12 Sep; the architecture is not open.

Full specs, judge scores, and every graft: `audits/2026-08-28-xr-feasibility/workflow2_full_output.json` (`designs`, `judges`).
