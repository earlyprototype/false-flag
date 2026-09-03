# The live control surface — a plain-English guide

Two web pages, one small server. Both look inside a running (or simulated)
game. Install the supported dependency set, then start it:

```bash
pip install -r requirements.txt -r api/requirements.txt
python -m uvicorn api.server:app --port 8000
```

- **`/dataflow`** — the engine's map. For understanding how the game is
  built, watching it run step by step, and tweaking AI behaviour.
- **`/dashboard`** — the facilitator's control room. For running a live
  session for other people and steering it while it happens.

Both are free to explore: click **All → mock** (dataflow) before starting
a demo, or use **Start demo campaign** on the dashboard — this routes every
AI call to a free, canned response generator instead of the real API, so
nothing costs money or credit.

---

## `/dataflow` — the engine's map

Every point where the game asks an AI model for something is a box on a
diagram. Lines show how information moves between boxes. It's a live,
clickable flowchart of the whole engine.

**Use it when you want to:**
- See how False Flag is actually built, without reading code
- Watch one turn of the game happen, box by box, explained in plain English
- Change which AI model answers a particular kind of question — live, no
  restart
- Rewrite the instructions (the "prompt") a particular AI call gets
- Check how False Flag's internal concepts line up with an outside
  industry standard for exercise-simulation software (the "twin model")

**The controls, left to right along the top:**

| Control | What it does |
|---|---|
| **Immersive / Classic / Emergent** | Picks a game type. Boxes and lines the chosen type never uses go grey. |
| **Mystery** checkbox | Adds the hidden-narrative boxes to the diagram when ticked. |
| **Session box + Attach** | Paste in an existing game's session ID to watch it live instead of starting a new one. It uses the browser's session-scoped operator stream capability when one exists; otherwise it is a public view. |
| **Start live demo / Stop** | Runs a real automated game through the diagram so you can watch it live. |
| **All → mock** | Switches every AI call to the free fake responder first — click this before "Start live demo" to explore for free. |
| **Clear overrides** | Removes every model/routing override, back to defaults. It does **not** touch edited prompts — reset those one at a time with "Reset to default" in the box's own panel. |
| **Reset layout** | Puts every box back in its original position (see below). |
| **▶ Walkthrough** | A guided tour: one turn of the game, one step at a time, in plain English. Use arrow keys to move through it. |
| **◇ DTDL** | Overlays the "twin model" — badges each matching box with the industry-standard concept it corresponds to. |

**Click any box** to open a side panel. Boxes with a blue border are AI
calls — their panel lets you see the model currently handling that call,
switch it to a different one, or edit the exact instructions it's given.
The change applies to that call's very next use.

**Drag any box** (or the elbow of any connecting line) to rearrange the
diagram to your own taste — your layout is remembered on this browser.

---

## `/dashboard` — the facilitator's control room

This is what you'd have open while hosting a live game for someone else.
One continuously-updating page: what's happening right now, the numbers
driving the story underneath, and the controls to intervene.

**Use it when you want to:**
- Watch a session happen in real time while someone else plays
- See the hidden numbers (war risk, public support, alliance trust,
  casualties) that the player never sees directly
- Manually push a news event or crisis into a running game
- Change an AI model or its instructions mid-session, the same as on
  the engine map
- Check the same "twin model" telemetry, but live and in one place

**The panels, top to bottom:**

| Panel | What it shows / does |
|---|---|
| **Event ledger** | A live, colour-coded feed of everything happening — situation reports, intelligence, diplomatic exchanges, domestic news, cabinet-only chatter, and (facilitator-only) referee notes. |
| **Metric traces** | Charts of the hidden numbers over time. |
| **LLM calls** | One line per AI request made: which family of call, which model answered, how fast, whether it had to fall back to a backup. |
| **Reroute matrix** | Every AI call type in one table — pin a specific model or provider to it, live. |
| **Inject console** | Write your own headline and story content and fire it into the session as a news event — pick the channel it arrives on and, optionally, which hidden number it nudges. |
| **Prompt hot-edit** | Pick any AI call family and rewrite the instructions it's given, without touching code. |
| **Twin model** | The same industry-standard mapping as the engine map's ◇ DTDL mode, but as a live table: current values, and the full list of matched concepts. |

Start a session with **New facilitated game**, or watch a running one by
pasting its session ID into **Attach**. Creating one issues a separate
facilitator capability kept in this browser tab. Attaching by session ID alone
is a public view unless that tab already holds the capability. Public views
receive the campaign's player-safe projection: Classic gameplay numbers remain,
while Immersive and Emergent use qualitative situation vibes. Hidden Mystery
state, exact adviser trust, raw actor scores and referee events stay on the
capability-bearing facilitator view. The server prevents these audience-specific
responses from being cached across viewers. **Start demo campaign** runs a free mock
game through the whole page so you can see every panel move.

---

## Which one do I actually open?

- **Exploring or tweaking the engine, or demoing the architecture** →
  `/dataflow`
- **Running a real session for real players and want to watch or steer
  it** → `/dashboard`

Nothing you do on either page is destructive — reroutes and prompt edits
can always be cleared back to default, and nothing here touches game saves.
