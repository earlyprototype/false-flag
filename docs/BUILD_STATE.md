# Build State — Situation Globe (stock-take, 2026-08-28 evening)

**Purpose**: single resume point. Any continuation — renewed agent session, different model, or the owner alone — starts here.

## Where things stand

- **`main` now carries the full DTDL twin model**: PR #65 merged directly; PR #66 (dashboard twin panel) merged via carrier PR #68, because #66's stacked base didn't auto-retarget (its branch wasn't deleted at #65's merge — remember this for future stacked PRs). `/dtdl`, `/dtdl/{dtmi}`, the ◇ DTDL dataflow mode, and the dashboard `Session;1` telemetry panel are all live on `main`.
- **This branch** (`claude/vr-game-xr-simulation-feasibility-gomu1j`, PR #67, draft) is synced on top of merged main and holds: the feasibility study v2 (`XR_GLOBE_FEASIBILITY.md`), the component map (`XR_GLOBE_COMPONENT_MAP.md` — 5 Mermaid diagrams, CORE/STRETCH/DEFERRED), the discards register, the Manus ops doc (`MANUS_TASKS.md`), and both raw analysis outputs under `audits/2026-08-28-xr-feasibility/`.
- **Decisions recorded**: build-what's-needed framing · ops-room VR thesis · lo-fi cast/hyper-real globe · design-paced between-turn holds · dates: onsite 12 Sep at IMR, final 14 Sep · #65/#66 merged (D0's merge half done) · Manus credits (60.9k) durable, off-branch role only.
- **D0's build half is NOT yet taken**: the owner chose "merge, then take stock before building." No implementation code exists yet — docs only.

## The plan (short form — full detail in the study §7 and the component map §5)

M0 First Light (spike: `api/globe.html` on a live demo session — now against merged main, so the DTMI badges can come earlier than planned) → D0b commit → M1 The Fleet Moves (zero-LLM position system: `models/spatial.py`, `engine/kinematics.py`, `gazetteer.yaml`, doctrine legs, save round-trip + **`dev-scripts/build_play_bundle.py` after any `models/world.py` edit**) → D1 schedule check → M2 Standards on the Glass (`Theatre;1` sidecar + live badges + DTDLParser re-run) → M3 Show-Safe (runbook, proxy stance, attract loop, cold-restart drill, **recorded video fallback**) → D2 gate → M4 stretch (MOVEMENT call) → M5 post-comp (tripwires, fog, daemon, VR ops room).

## Immediate next actions (in order)

1. **M0 spike** (~a day): serve `api/globe.html` at `GET /globe` (FileResponse, `dashboard.html` pattern, session-attach header cloned from it), CesiumJS from CDN, ~10 hardcoded gazetteer entries, plot the ORBAT from `GET /game/{id}/resources`, one vendored sensor shader, EXERCISE watermark. Attach to `POST /demo/start` with `WARGAME_LLM=mock`. **One `/stream` consumer per session** (known destructive-queue defect).
2. Fire Manus P1 tasks (briefs are paste-ready in `MANUS_TASKS.md`): gazetteer QA → feeds M1; IMR brief; rubric hunt.
3. M1 per study §4a engine-diff list; claims 8–10's conditions in the study are **normative** for the implementation (fail-to-hold, closed vocabulary, sentinel, mock `NO_ORDERS`, derived seeds, `world.posture` not `world.flags`).

## Needs / open items

- Owner: ratify the TASKORD+IRONCLAD hybrid (or hear both — full specs in `audits/.../workflow2_full_output.json`); geo-pack location (`data/` vs `api/geo_data/`); demo variant; Quest availability; save downgrade-loss acceptance.
- Agent-subscription renewal decision (~30 Aug): weighed against the stakes; this file + the study + discards register are the continuation insurance either way.
- DTDLParser re-validation once `Theatre;1` is authored (dotnet 8 + DTDLParser 1.1.3 — the pass-2 probe recipe).

## How to resume without the current session

Read, in order: this file → `XR_GLOBE_COMPONENT_MAP.md` (visual) → `XR_GLOBE_FEASIBILITY.md` (authority; §4a is the implementation spec, §3 the verified constraints) → `XR_GLOBE_FEASIBILITY_DISCARDS.md` (what was considered and cut, so it isn't relitigated). The raw agent outputs under `audits/` answer any "why" the docs compress.

## Session close, 2026-08-28 (late) — rulings landed after the sections above

- **The seam (owner-confirmed)**: live-hybrid per-layer split; the game reads live-derived facts as context, never state — issue #77 is authoritative, including the **boundary-as-zone** design (no text labels on player surfaces; fog carries the reality boundary; diegetic EXERCISE chrome only where optics require) and the **live-first / no-fallback build posture** (non-determinism of play is the thesis; simulated modes are CI fixtures only; session journaling is AAR journalism, not replay-protection). Recorded demo film: **kept**, as hardware-catastrophe contingency only.
- **Real-email inject artifact**: issue #76, MVP-worthy.
- **N1 reframed mechanically** in issue #71 with the recommendation on record (orders on — completes the interpretation call the engine already runs and discards).
- **Language ruling enforced repo-wide**: mechanical language only (what/how/why); truth/lie metaphors removed from all docs on both branches.
- **Docs status at close**: study + map + in-brief + discards (PR #67) and owner's brief + this file + decision briefs (PR #69) all current. **Known stale**: the claude.ai artifact page (pre-dates the sprint-milestone rework, tonight's rulings, and the language sweep) — refresh it or retire it; the repo is the memory.
- **Not yet done, deliberately**: no implementation code — D0b ("go") never given; Manus P1 tasks not yet fired (briefs in #70); decisions #71–#75 open with safe defaults; renewal decision open.
