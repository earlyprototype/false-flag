# Decision Register — Situation Globe and VR Room

This register records decisions that affect the canonical plan. It does not
assign dates or create a competing sequence. Current build order:
[`PLAN.md`](../PLAN.md).

## Settled

| Decision | Ruling | Evidence |
|---|---|---|
| Product centre | FALSE FLAG remains the AI wargame. Globe, live context and VR deepen the existing campaign rather than replacing it with a generic demonstration. | [Owner ruling, 1 Sep 2026](https://github.com/earlyprototype/false-flag/issues/136#issuecomment-5499898594); [PLAN — Product centre](../PLAN.md#product-centre) |
| Movement authority | A model may emit bounded named orders but never coordinates. Gazetteer hydration and deterministic kinematics are the coordinate writers. | [Issue #71](https://github.com/earlyprototype/false-flag/issues/71) |
| Geo-file ownership | Scenario-authored geography stays with scenario data; engine-derived geography stays with technical data; the seam remains explicit. | [Issue #72](https://github.com/earlyprototype/false-flag/issues/72) |
| Globe visual controls | The normal, CRT and FLIR views remain selectable rather than one being removed early. | [Issue #74](https://github.com/earlyprototype/false-flag/issues/74) |
| Live/simulated boundary | Real feeds and game state are separate layers. Live facts may inform context, never state. The exercise zone and fog carry the boundary; runtime is live-first with no silent fixture fallback. | [Issue #77](https://github.com/earlyprototype/false-flag/issues/77) |
| VR build route | Build the portable WebXR room/screen, measure it on the Quest, then use a local quad layer or streamed source according to the measurements. | [Owner ruling, 1 Sep 2026](https://github.com/earlyprototype/false-flag/issues/127#issuecomment-5498505180); [PLAN — XR Ops Room](../PLAN.md#xr-ops-room) |
| Planning estimates | Agent-generated duration estimates do not decide scope or cut features. Dependencies and observable done tests order the work. | [Owner ruling, 1 Sep 2026](https://github.com/earlyprototype/false-flag/issues/136#issuecomment-5499898594) |

## Open facts or selections

| Item | What resolves it | Current handling |
|---|---|---|
| Quest availability | Record the actual device available in [issue #75](https://github.com/earlyprototype/false-flag/issues/75). | Portable room work can begin; on-device measurement waits for the device. |
| Demonstrated campaign variant | Run and compare the existing variants, then record the owner's choice in [issue #73](https://github.com/earlyprototype/false-flag/issues/73). | Do not let a guessed duration choose it. |
| Civilian-flight provider | Confirm that current terms permit the intended live demonstration and document attribution. | Weather lands first. No flight provider becomes required before this gate passes. |
| Campaign clock versus live now | Owner choice required before live observations enter adviser prompts. | Rebase the campaign date, frame current conditions as a present-day exercise baseline, or keep the feed spectator-only; never present September 2026 weather as October 2025 fact. |
| Save downgrade behaviour | Choose whether loading a new spatial save in an older build may lose spatial fields silently. | Newer-build save/load/resume must preserve spatial state regardless. |

## References

- [Current build plan](../PLAN.md)
- [Current build state](BUILD_STATE.md)
- [Full feasibility evidence](XR_GLOBE_FEASIBILITY.md)
