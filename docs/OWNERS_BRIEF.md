# The Owner's Brief — the Situation Globe, in plain language

*This is the translation layer. The other documents in this folder are deliberately dense — they exist so no engineer (human or AI) ever loses the thread between sessions. **This one is for you.** It requires reading nothing else, and anything elsewhere that's opaque can be translated into here on request.*

---

## What we're building, in one paragraph

Right now, between turns, your game goes quiet — the cabinet argues, and nothing moves. We're adding **a live map of your war**: a beautiful satellite Earth on a big screen where the Russian Northern Fleet actually sails toward Scotland while the players deliberate. The player sees what UK intelligence *believes* (fuzzy circles that sharpen when they task patrol aircraft); the facilitator sees the truth. When the fleet crosses a line that matters — into the GIUK gap, within missile range of London — the game itself notices and makes it that turn's news. It's the war room wall your fiction always implied.

## The two halves

- **The screen** — a web page showing the Earth, borrowed ideas from the gods-eye-view project: sensor filters (clean satellite → CRT → night-vision → thermal as the crisis worsens), cinematic camera moves when injects land, a permanent EXERCISE watermark so nothing is ever mistaken for real.
- **The truth behind it** — the game engine actually *knowing* where every ship and squadron is. Positions only ever come from simple physics (speed × heading along real sea lanes) — the AI is never allowed to invent a coordinate. If anything goes wrong, ships simply hold their course: **the map can go stale, but it can never lie.**

## The plan, as five moments

1. **First Light** — the map exists: your forces plotted on the Earth, attached to a running game, on the projector. *(Needs nothing from you but "go".)*
2. **The Fleet Moves** — the red fleet visibly advances turn by turn, from real game state, costing nothing to run.
3. **Standards on the Glass** — small live badges show the map is powered by your Microsoft-validated digital-twin model. This is the moment built for the IMR room: digital twins are literally their field.
4. **Show-Safe** — nothing can break on stage: a rehearsed run-sheet, an attract mode that plays itself, and a recorded film of the whole demo in case the venue wifi, the laptop, or luck fails.
5. **(Stretch) The Cabinet Orders the Map** — you type "surge the carrier group north" as your decision, and the ships obey.

## The four questions, as you'd ask a friend

1. **Should your words move ships?** When you commit a decision, should the game read it and actually move your forces (with the never-invent-a-coordinate guardrail above)? Or is watching a perfectly scripted threat enough for now? *The exciting answer is yes; the cautious answer loses nothing already built and can be upgraded later.*
2. **Where do the map's notes live?** The coordinates, routes and camera moves are just files. Keep them beside your story episodes (they're part of the scenario, you review changes), or in a separate technical folder (faster, less tidy)?
3. **Which cut do the judges watch?** Your full slow-burn opening, or the quick-start version that reaches the naval drama sooner? *We can simply time both once First Light exists and pick with a stopwatch.*
4. **First impression: bare Earth, or through the green filter?** The crisis paints the world CRT-green and thermal as things worsen either way — this only decides what judges see in the first ten seconds. *Your own instinct — the comic cast against the hyper-real Earth — argues for bare.*

None of these is urgent. Each has a sensible default, and the first two moments need no decisions at all.

## What I need from you

- **"Go"** — starts First Light.
- The four answers above, whenever they're ripe (defaults cover silence).
- One fact when you know it: **is a Quest headset available to you?** (Decides which VR route we prove later.)

## Tiny glossary for words you'll meet

- **Gazetteer** — our list of ~30 real places (Faslane, the GIUK gap, Severomorsk…) with their coordinates. The only "geocoding" that ever happens.
- **Digital twin / DTDL** — a Microsoft standard for describing a system as data. Your game already models itself this way (that's what merged today); the map becomes a *view* of it. This is the language IMR speaks.
- **Tripwire** — a line on the map the game watches: crossing it creates that turn's event.
- **Fog of war** — players see estimates, not truth; the gap between the two *is* your game, made visible.
- **Provenance** — honesty labels on every dot: *adjudicated* (the engine says so), *simulated* (projected forward), *estimated* (what intel believes).
