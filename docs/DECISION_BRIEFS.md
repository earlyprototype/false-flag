# Decision Briefs — what each open call needs, when it's due, and the default

*Companion to `BUILD_STATE.md`. Principle: no decision is due before the milestone that needs it; every decision has a safe default; M0 (First Light — the first working version of the map page: the game's forces plotted on the satellite Earth, attached to a running demo game, on the projector; saying "go" authorizes building it, the first code of this project — nothing is built yet) + B1 (the build stage every movement design shares: the position system with no AI) require none of them.*

| # | Decision | Due at | Context source | Default if silent |
|---|---|---|---|---|
| N1 | Movement architecture (issue [#71](https://github.com/earlyprototype/false-flag/issues/71): should the AI's movement orders move your forces?) | Before B2 (the build stage where the movement designs diverge: who issues movement orders) | This page, §below | The hybrid |
| N2 | Geo-pack home (issue [#72](https://github.com/earlyprototype/false-flag/issues/72): which folder the map's data files live in) | First geo commit | None (taste; `git mv`-reversible) | `data/scenarios/…`, diff-first |
| N3 | Demo campaign variant (issue [#73](https://github.com/earlyprototype/false-flag/issues/73): which campaign cut the judges watch) | M0 rehearsal | Stopwatch two mock runs (M0 produces them) | Time both, pick at M0 |
| N4 | Default globe register (issue [#74](https://github.com/earlyprototype/false-flag/issues/74): bare satellite Earth vs the CRT filter as the globe's default look) | M3 (Show-Safe, the demo-hardening milestone) dress rehearsal | Your eyes on the projector (both framings ship regardless) | Clean photoreal + escalation ladder, CRT toggle present |
| — | Quest availability — is a Meta Quest VR headset available? (a yes/no to record in issue [#75](https://github.com/earlyprototype/false-flag/issues/75)) | Before the VR spike | A fact, not a reading | S3 (streamed screen) path assumed |
| — | Save downgrade loss | B1 | Executed probe, study claim 9 | Accept + document + version bump 2.4→2.5 |

---

## The N1 one-pager: should the cabinet's words move ships?

All three designs share ~80% of the build — `models/spatial.py`, `engine/kinematics.py`, the gazetteer (the hand-checked coordinate lookup table of ~30 real places, the only source of coordinates in the system), red doctrine legs, save discipline. **Stage B1 is identical under every option.** They diverge only on who issues *blue* movement orders after B1:

**The hybrid (default)** — during adjudication, one added, non-blocking, cheap LLM call reads the decision round and emits up to 8 structured orders (`ORDER: unit | mission | destination | speed`) — never coordinates. Orders are validated against the ORBAT (the scenario's order of battle — the unit list), the ~30-place gazetteer, and a per-unit mission legality graph (red cannot jump rendezvous→strike, mirroring the episodes' escalation ordering). Any parse failure, truncation, or outage degrades to "all units hold" with a visible line — a failure leaves positions un-updated, never invented. Plus: readiness as live state (HMS PoW's — HMS Prince of Wales's — 3-turn rule renders), route polylines (ships follow sea lanes), and detected-visibility tripwires (an unseen crossing reaches the player later as ambiguous intel). **You get**: "move the carrier group to the GIUK gap" in the decision text actually moves it; advisors can then argue from real geometry. **You pay**: one more LLM call family, one deliberate re-golden commit, and the guard-rail discipline (all specified, all verified feasible — study claim 8).

**IRONCLAD pure (zero-LLM)** — no movement call at all; units follow authored doctrine and posture templates only. **You get**: perfect determinism, zero parse surface, the red fleet's dread-clock advance intact. **You pay**: the player's spatial intent is silently dropped every turn — geography is watchable, never playable. Honest fallback position; also exactly what the hybrid degrades to when its LLM call fails, so choosing it later loses nothing already built.

**TASKORD pure** — the hybrid minus the legality graph, readiness, and route polylines. Saves a few days; loses the pieces that keep red honest and make the map feel inhabited. Only worth it under extreme schedule pressure — and D1's (the schedule-check decision gate's) cut goes to M2 (Standards on the Glass — the digital-twin standards badges) / M3 (Show-Safe) first anyway.

**The decision in one sentence**: if the demo's climax should be a judge watching the player *say* "surge the carrier north" and the map *obey* — take the hybrid; if the two weeks argue for watching a perfect clockwork threat instead, IRONCLAD is the dignified fallback, and the hybrid literally contains it.

Full specs, judge scores, and every graft: `audits/2026-08-28-xr-feasibility/workflow2_full_output.json` (`designs`, `judges`).
