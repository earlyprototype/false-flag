# The Feasibility Study, In Brief

*Plain-language version of `XR_GLOBE_FEASIBILITY.md` — for anyone meeting this work for the first time. Nothing here requires reading the technical study; every finding below links back to it if you want the deep version. The plan lives in [`PLAN.md`](../PLAN.md), the explanation in [the Owner's Brief](OWNERS_BRIEF.md), and the current calls and defaults in [`DECISION_BRIEFS.md`](DECISION_BRIEFS.md).*

## What was studied

Can FALSE FLAG gain a **live map of its war** — a satellite Earth on a big screen where the Russian fleet visibly sails toward Scotland between turns — borrowing ideas from an open-source globe project (gods-eye-view), with a VR element, powered by the game's own Microsoft-standard digital-twin model? Two analysis passes, every important claim tested adversarially, several by running real code.

## The verdict

**Yes, at every layer** — as a *port of ideas*, not a copy-paste of code. The map can also draw from real game state: the engine keeps one position record per unit, updated once per turn by movement arithmetic along pre-drawn routes. The AI may only issue orders in plain words ("this unit sails to this named place") and never writes a number. Because only the coordinate lookup table and that arithmetic can write a position, a failure can leave the map out of date — it cannot put a made-up position on it.

## The twelve findings, plainly

1. **VR — blocked one way, open another.** The borrowed globe software cannot drive a VR headset directly (checked thoroughly; don't let anyone spend a week trying). It doesn't need to: we put the globe's picture on a **screen inside the VR room** — like the wall display in a real ops centre — which is a proven technique with two known technical rules to follow. So the practical answer on VR is *achievable*, not refused. *(Findings 1 and 11 in the study.)*
2. **The beautiful imagery is affordable.** The photorealistic Earth has a free tier that comfortably covers a competition demo, plus a completely free fallback look that needs no accounts at all. *(2)*
3. **We don't need anyone's live data.** The borrowed globe runs happily on our own simulated feeds — a few days' work, no external services, nothing real ever mixed in. *(3)*
4. **We serve the globe the simple way.** Our half-finished web frontend doesn't actually build; the globe ships as a single self-contained page, the same proven way our dashboard already works. *(4)*
5. **One real bug to fix first.** Today the game's live event feed can only serve *one* screen per session without them stealing each other's updates; a small fix lets many screens watch one game — worth doing regardless of the globe. *(5)*
6. **The digital-twin standard can carry a map.** Our twin model can hold coordinates and still pass Microsoft's official validator — proven by actually running it. This is the part the IMR audience will recognise as their own field. *(6)*
7. **The scenario is already a map.** Everything happens at real places (Faslane, the GIUK gap, Severomorsk…), so about thirty looked-up coordinates put the whole war on a real Earth. The game just doesn't *track* positions yet — that's exactly what the build adds. *(7)*
8. **The AI can be trusted with movement — because it never touches numbers.** It issues orders in the same plain labelled-text style the game already parses safely elsewhere; every order is checked against the known units and places, and any failure means ships simply hold course. *(8)*
9. **Old save files survive.** Adding positions to the game state keeps every existing save loadable — proven by running the real save/load code. (One build step must always follow that change; it's written down.) *(9)*
10. **The map can make news.** The game can honestly notice "the fleet crossed the line" at the start of a turn and make that the turn's event, visible to the player and the AI advisors alike — proven against the real engine. *(10)*
11. *(Merged into finding 1 above.)*
12. **The military numbers must be authored, and safely can be.** Ranges and speeds aren't in the scenario files, but every ship and missile in it is real with published public figures. Anything genuinely classified (sonar performance, missile-defence footprints) gets an explicit "fictional doctrine" label so no expert can catch us pretending. *(12)*

## Who reads what

- **Everyone, first**: this page, then the [Owner's Brief](OWNERS_BRIEF.md) and [`PLAN.md`](../PLAN.md).
- **Whoever builds or maintains**: the technical study, component map, and discards register in this folder — dense on purpose, so nothing is lost between sessions.
- **Whoever runs research tasks**: issue #70 (ready-to-paste briefs).
