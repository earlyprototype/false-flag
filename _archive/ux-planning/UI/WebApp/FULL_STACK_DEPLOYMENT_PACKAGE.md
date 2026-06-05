# FALSE FLAG – Full Stack Deployment Package (CLI + Web App)

**Project:** FALSE FLAG: THE WARGAME  
**Scope:** CLI Dashboard + Web App (SCUMM-style) on top of shared Headless Engine  
**Status:** Working but inconsistent – this package defines how to stabilise and converge.

---

## 1. Executive Summary

The game now has three layers:

- **Engine layer (Headless):** `engine/`, `models/`, `data/`, `GameManager` – the single source of truth for game rules and state.
- **CLI layer:** `cli/main.py` (classic scrolling terminal, already upgraded with Rich and themes).
- **Web layer:** `api/server.py` (FastAPI + SSE) + `frontend/` (Next.js 14 + Tailwind + shadcn).

The goal of this package is to:

- Ensure **feature parity** between CLI and Web App.
- Align the **CLI Dashboard** deployment plan and the **Web UI (SCUMM) Deployment Package** into one roadmap.
- Keep changes **safe and reversible**, with the engine and classic CLI treated as “golden”.

---

## 2. Architecture Overview

- **Headless Engine**
  - `engine/game_manager.py` – wraps world state, briefing, discussion, decision, adjudication.
  - `engine/initial_conditions.py`, `engine/sim_loop.py`, `engine/diplomacy.py`, `engine/intelligence.py`.
  - Contract: all UIs talk to the game **only** via `GameManager` or a thin API on top.

- **CLI UIs**
  - `cli/main.py` – classic interactive game (already upgraded with Rich, narrator, themes).
  - Future `cli/main_dashboard.py` + `cli/dashboard.py` – persistent Rich layout dashboard (from `DASHBOARD_DEPLOYMENT_PACKAGE.md`).

- **Web UI**
  - `api/server.py` – FastAPI; exposes `GameManager` via HTTP + SSE.
  - `frontend/app/page.tsx` – Situation Room dashboard (shadcn/Tailwind).
  - Target aesthetic and component breakdown are defined in  
    `UX/UI/cli/WebApp/WEB_UI_DEPLOYMENT_PACKAGE.md`.

**Rule of thumb:**  
Business logic lives in the engine; CLI and Web should do **rendering + input only**.

---

## 3. Feature Parity Matrix (CLI ↔ Web)

**Core loop**

- **Briefing**
  - CLI: `run_turn_briefing` with streamed intro, narrator, injects.
  - Web: `POST /game/new` + SSE inject events.
  - **Gap:** ensure all briefing text (including narrator bridge) is exposed and rendered – not just a short summary.

- **Discussion**
  - CLI: free-form questions, `/advise` (all advisors), `/call`, `/intel`.
  - Web: free-form questions wired to `/game/discussion`; `ADVISE`/`RESOURCES`/`DIPLOMACY` partially implemented.
  - **Gap:** `/advise`, `/call`, `/intel` need full, reliable equivalents.

- **Decision**
  - CLI: two-step **Interpret → Pushback → Confirm/Modify/Override → Adjudicate**.
  - Web: single `/game/decision` call on “EXECUTE”.
  - **Gap (critical):** missing Decision Review phase and critical-concerns handling.

- **Adjudication**
  - CLI: detailed narrative assessment, effects table, advisor + international reactions.
  - Web: SSE stream of reasoning and injects (already present but not yet visualised as clearly).

**Meta / Utilities**

- `/status` – metrics, vibes, flags        → **Web:** metrics panel (partial), vibes/flags missing.
- `/menu` – advisors, contacts, metrics guide, commands  
  → **Web:** command bar + panels (only partially implemented).
- `/resources` – forces + stockpiles      → **Web:** Resources dialog (needs stable data shape).
- `/call` – diplomatic encounter          → **Web:** Diplomacy dialog (currently a stub).
- `/intel` – actor assessment             → **Web:** not yet implemented.
- `/llm` – model settings                 → **Web:** not yet implemented.
- `/theme` – theme switching              → **Web:** theming via Tailwind/shadcn, but no in‑game switch yet.
- Save/Load, Scenario/Mode/Difficulty     → **Web:** not yet exposed.

This package’s roadmap brings the Web App up to the same standard while keeping CLI work in sync.

---

## 4. Combined Roadmap (Phases)

### Phase 0 – Stabilise What Exists (NOW)

**Goal:** No crashes, predictable API contracts, CLI remains untouched.

- **Backend hardening**
  - Define and document JSON shapes for:
    - `POST /game/new`
    - `GET /game/{id}/resources`
    - `GET /game/{id}/diplomacy/contacts`
    - `POST /game/action/call`
    - `POST /game/discussion`
    - `POST /game/decision` (current one‑shot version).
  - Make `GameManager.get_resources()` and `get_diplomatic_contacts()` return **simple, flat, well-typed** structures derived from `initial_conditions.yaml`.

- **Frontend hardening**
  - In `page.tsx`, guard all uses of `resources`/`contacts` (no assumptions about nested objects).
  - If data is missing or malformed, show a minimal textual fallback (e.g. “No resources data available” or raw JSON dump) instead of throwing.
  - Ensure `RESOURCES` and `DIPLOMACY` dialogs cannot break the transcript view.

- **Smoke tests**
  - Extend `api/test_client.py` to:
    - Create a session.
    - Call `/game/{id}/resources` and assert `200` + `uk_forces` + `stockpiles`.
    - Call `/game/action/call` with a known country and assert `200`.
  - These become the **“Phase 0 green”** checks.

**Output:** Existing Web UI is stable and safe to iterate on; CLI still works exactly as before.

---

### Phase 0 API Contracts

Documented JSON contracts for the stabilised endpoints (structure shown with required keys; optional keys marked with `?`):

- **POST `/game/new`**
  - Request: `{ "scenario_id": "war_game_2025", "variant": "standard", "difficulty": "standard", "play_mode": "immersive", "player_name": "Prime Minister" }`
  - Response: `{ "session_id": string, "turn": int, "phase": string, "metrics": { "<metric>": int }, "advisors": [{ "role": string, "status": string }] }`

- **GET `/game/{id}/resources`**
  - Response: `{ "forces": [{ "id": string, "branch": string, "unit_type"?: string, "location"?: string, "status"?: string, "role"?: string, "readiness_turns"?: int, "notes"?: string }], "stockpiles": [{ "category": string, "name": string, "count": int, "note"?: string }] }`

- **GET `/game/{id}/diplomacy/contacts`**
  - Response: `[{ "country_code": string, "title"?: string, "access_level": "leader"|"foreign_minister"|"ambassador"|"restricted", "disposition"?: string, "notes"?: string }]`

- **POST `/game/action/call`**
  - Request: `{ "session_id": string, "country_name": string }`
  - Response: `{ "status": "processed" }` (SSE stream delivers the transcript segments)

- **POST `/game/discussion`**
  - Request: `{ "session_id": string, "question": string }`
  - Response: `{ "status": "processed" }` (advisor replies are streamed via SSE)

- **POST `/game/decision`**
  - Request: `{ "session_id": string, "action_text": string }`
  - Response: `{ "status": "processed" }` (interpretation, reasoning, reactions streamed; state_update event carries metrics/phase)

These contracts are the reference for the CLI dashboard, Web UI, and Phase 0 smoke tests. Any missing field should be treated as `null`/empty by clients rather than failing.

---
### Phase 1 – Decision Loop Parity (Engine + Web)

**Goal:** Web App matches the CLI’s decision discipline.

- **API changes**
  - Introduce:
    - `POST /game/decision/interpret`  
      → runs `run_turn_decision` **up to** interpretation + pushback, returns:
      - `interpretation`
      - `critical_concerns` (role, concern, recommendation)
      - `forces_involved`, `timeline` (parsed summary like `parse_interpretation_simple`).
    - `POST /game/decision/commit`  
      → runs adjudication and turn advance (essentially current `/game/decision` logic).
  - Keep current `/game/decision` temporarily as a compatibility shim and mark it “legacy”.

- **Web UI changes**
  - Add a **Decision Review dialog**:
    - Opens when user hits EXECUTE in Decision phase.
    - Shows:
      - “Your Decision” (exact text).
      - Operational summary, forces, timeline.
      - Critical concerns with options:
        - **Apply recommendations** (A/S).
        - **Modify manually** (M – returns them to edit).
        - **Ignore and proceed** (I).
        - **Return to discussion** (D).
    - Only calls `/decision/commit` when the user chooses to proceed.

- **CLI alignment**
  - Keep the CLI logic as the behavioural reference; do not change semantics, only surface the same steps via API and Web.

---

### Phase 2 – Deep State & Intel

**Goal:** Surface the same “deep state” diagnostics the CLI offers.

- **Engine/API**
  - Add endpoints to expose:
    - Situation “vibes” (`narrative_state.get_situation_vibes()`).
    - Advisor trust/relationship scores (from `narrative_state.characters`).
    - Active world flags (`world.flags`).
    - Intelligence assessments:
      - `GET /game/{id}/intel` – list of available actor dossiers.
      - `GET /game/{id}/intel/{actor}` – `generate_actor_detailed_assessment`.

- **Web UI**
  - Extend the metrics sidebar / add a “Status” panel mirroring `/status`:
    - Trust bars for each advisor.
    - Active risk flags list.
  - Add an **Intelligence** panel (per `WEB_UI_DEPLOYMENT_PACKAGE` `StatusPanel` / `IntelChannel`):
    - View and scroll detailed dossiers.

---

### Phase 3 – Diplomacy & Meta-Game

**Goal:** Full parity for `/call`, `/intel`, save/load, scenario selection, themes, LLM config.

- **Diplomacy engine**
  - Expose proper `run_diplomatic_encounter` via API:
    - Structured transcript: intro → options → outcome.
    - Cohesion delta and world metric updates.
  - Web: replace the simple `/action/call` proxy with a richer **DiplomacyPanel** as described in `WEB_UI_DEPLOYMENT_PACKAGE.md`.

- **Save/Load & Scenario setup**
  - API routes to save/load to a `saves/` directory in a way that both CLI and Web can share.
  - Web start screen with:
    - Scenario selection.
    - Difficulty, play mode, and (later) mystery‑mode toggles.
    - Load existing save.

- **Settings**
  - LLM configuration panel (equivalent of `/llm`).
  - Theme selector wired to SCUMM‑style theme tokens (DEFCON/Retro/Slate) and matching the CLI palettes.

---

### Phase 4 – CLI Dashboard & SCUMM Visual Convergence

**Goal:** Two primary front-ends—CLI Dashboard and Web App—sharing a coherent “situation room / SCUMM” aesthetic.

- **CLI Dashboard track** (from `DASHBOARD_DEPLOYMENT_PACKAGE.md`)
  - Implement `cli/dashboard.py` + `cli/main_dashboard.py` using `Rich.Layout` and `Rich.Live`.
  - Ensure dashboard draws from the same **engine state** and **theme semantics** as the Web App (metrics names, flags, advisor roles).

- **Web SCUMM track** (from `WEB_UI_DEPLOYMENT_PACKAGE.md`)
  - Gradually refactor `frontend/app/page.tsx` into:
    - `components/game/SceneViewport.tsx`
    - `components/game/CommandBar.tsx`
    - `components/game/StatusBar.tsx`
    - `components/panels/*` for `/status`, `/advise`, `/resources`, `/diplomacy`, `/menu`, `/theme`.
  - Apply SCUMM panel styles (`scumm-panel`, `scumm-button`, etc.) from the Tailwind config.

**Key principle:** visual convergence without forcing identical layouts – CLI stays terminal‑native, Web stays SCUMM‑inspired, but both present **the same information and choices**.

---

## 5. Development Workflow & Safety Rails

- **Golden code**
  - Treat `engine/`, `models/`, `data/`, and `cli/main.py` as “golden”; changes here require a strong reason and extra testing.

- **Branching logic**
  - For major phases (1–4), keep work behind:
    - Feature flags (env vars) on the backend.
    - UI toggles or hidden routes on the frontend (e.g. `/dev`).

- **Testing**
  - Extend `api/test_client.py` for backend smoke tests per phase.
  - Add a minimal frontend “smoke page” that pings the key endpoints and displays status (no heavy E2E yet).

- **Rollback**
  - Because the engine and classic CLI are isolated, rollback is:
    - Stop the Web/API processes.
    - Re-run `.\.venv\Scripts\python.exe -m cli.main play` for the stable game.

---

## 6. References

- `UX/UI/cli/DASHBOARD_DEPLOYMENT_PACKAGE.md` – CLI Dashboard design & workflow.
- `UX/UI/cli/WebApp/WEB_UI_DEPLOYMENT_PACKAGE.md` – Web SCUMM interface design.
- `analysis/WEB_APP_PARITY_PLAN.md` – Detailed parity notes for Web App.
- `cli/main.py`, `cli/rich_ui.py`, `cli/theme.py`, `cli/formatters.py` – current CLI implementation and aesthetics.


