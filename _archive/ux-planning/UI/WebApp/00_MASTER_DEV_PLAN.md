# FALSE FLAG - Master Development Plan
**Web UI + CLI Dashboard Convergence**  
**Created:** 23 November 2025  
**Status:** Phase 0 - Stabilisation  

---

## Quick Navigation

- **Active Work:** [02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md](02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md)
- **Blockers:** [02_IMPLEMENTATION_TRACKING/BLOCKERS.md](02_IMPLEMENTATION_TRACKING/BLOCKERS.md)
- **Technical Specs:** [03_TECHNICAL_SPECS/](03_TECHNICAL_SPECS/)
- **Progress Reports:** [04_PROGRESS_REPORTS/](04_PROGRESS_REPORTS/)

---

## Project Vision

Create two primary front-ends (CLI Dashboard + Web App) sharing a unified headless engine, with:
- **Feature parity** between interfaces
- **SCUMM-style aesthetic** for web (Indiana Jones: Fate of Atlantis)
- **Professional Calm theme** for CLI
- **ADHD-friendly design** throughout
- **Safe, reversible** development workflow

---

## Overall Progress Tracker

### Phase 0: Stabilisation (COMPLETE)
**Goal:** No crashes, predictable API contracts, CLI remains untouched

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| Define API contracts | ✅ COMPLETE | Backend | See FULL_STACK_DEPLOYMENT_PACKAGE.md |
| Backend hardening | ✅ COMPLETE | Backend | GameManager.get_resources() standardisation |
| Frontend guards | ✅ COMPLETE | Frontend | Defensive data handling in page.tsx |
| Smoke tests | ✅ COMPLETE | QA | api/test_client.py updated and passing |

**Exit Criteria:**
- [x] All Phase 0 API contracts documented and stable
- [x] Frontend handles missing/malformed data gracefully
- [x] Smoke tests pass (resources, diplomacy, call endpoints)
- [x] CLI main.py still works identically

---

### Phase 1: Decision Loop Parity (COMPLETE)
**Goal:** Web App matches CLI's decision discipline

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| API: /decision/interpret | ✅ COMPLETE | Backend | Returns interpretation + concerns |
| API: /decision/commit | ✅ COMPLETE | Backend | Executes decision |
| Decision Review dialog | ✅ COMPLETE | Frontend | Implemented in panels/DecisionReviewDialog.tsx |
| CLI alignment verification | ✅ COMPLETE | QA | Smoke tests pass |

**Dependencies:** Phase 0 complete

---

### Phase 2: Deep State & Intel (COMPLETE)
**Goal:** Surface diagnostic data (vibes, trust, flags, intel)

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| API: Situation vibes | ✅ COMPLETE | Backend | /game/{id}/state/vibes |
| API: Advisor trust scores | ✅ COMPLETE | Backend | /game/{id}/state/advisors |
| API: World flags | ✅ COMPLETE | Backend | /game/{id}/state/flags |
| API: Intel endpoints | ✅ COMPLETE | Backend | /game/{id}/intel & /intel/{code} |
| Status panel (web) | ✅ COMPLETE | Frontend | Tabs: Vibes, Advisors, Flags |
| Intelligence panel (web) | ✅ COMPLETE | Frontend | Dossier viewer |

**Dependencies:** Phase 1 complete

---

### Phase 3: Diplomacy & Meta-Game (COMPLETE)
**Goal:** Interactive diplomacy and meta-game loop

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| Refactor Diplomacy Engine | ✅ COMPLETE | Backend | Create DiplomaticEncounter class |
| API: Start Encounter | ✅ COMPLETE | Backend | POST /game/action/call |
| API: Diplomacy Reply | ✅ COMPLETE | Backend | POST /game/action/diplomacy/reply |
| Diplomacy Panel (web) | ✅ COMPLETE | Frontend | Chat interface |
| Save/load API | ✅ COMPLETE | Backend | Shared saves/ directory |
| Scenario selection (web) | ✅ COMPLETE | Frontend | Start screen |
| Settings Panel (web) | ✅ COMPLETE | Frontend | LLM Config & Themes |

**Dependencies:** Phase 2 complete

---

### Phase 4: Visual Convergence & Polish (IN PROGRESS)
**Goal:** SCUMM aesthetic + CLI Dashboard fully realised

| Task | Status | Owner | Notes |
|------|--------|-------|-------|
| CLI: dashboard.py | ⏸ PENDING | CLI Dev | Rich.Layout implementation |
| CLI: main_dashboard.py | ⏸ PENDING | CLI Dev | Dashboard entry point |
| Web: SceneViewport.tsx | ✅ COMPLETE | Frontend | Refactored from page.tsx |
| Web: CommandBar.tsx | ✅ COMPLETE | Frontend | SCUMM-style commands |
| Web: StatusBar.tsx | ✅ COMPLETE | Frontend | Metrics display |
| SCUMM panel styling | ✅ COMPLETE | Frontend | CRT overlay & component styles |
| Theme semantic alignment | 🏗 IN_PROGRESS | Both | CLI/Web theme parity |

**Dependencies:** Phase 3 complete

---

## Development Principles

### Golden Code Protection
**NEVER modify without strong justification:**
- `engine/` directory (game logic)
- `models/` directory (data structures)
- `data/` directory (scenarios, initial conditions)
- `cli/main.py` (classic CLI - always playable)

### Safety Rails
- All major changes behind **feature flags** (env vars)
- Backend changes isolated from CLI
- Rollback strategy: stop web/API, run CLI directly
- Test before merge: `python -m cli.main play`

### ADHD-Friendly Workflow
- **One phase at a time** - complete before moving forward
- **Clear exit criteria** for each phase
- **Visual progress tracking** - this document
- **Checkpoint validation** - smoke tests, manual verification
- **Documented blockers** - explicit dependency tracking

---

## Status Legend

- ⏸ PENDING - Not started
- 🏗 IN_PROGRESS - Active work
- ⏳ BLOCKED - Waiting on dependency
- ✅ COMPLETE - Done and verified
- ❌ CANCELLED - No longer required

---

## File Structure Reference

### Backend (Engine + API)
```
engine/
├── game_manager.py           # Single source of truth
├── initial_conditions.py
├── sim_loop.py
├── diplomacy.py
└── intelligence.py

api/
├── server.py                 # FastAPI + SSE
└── test_client.py            # Smoke tests
```

### Frontend (Web UI)
```
frontend/
├── app/
│   ├── page.tsx             # Current monolith (to be refactored)
│   └── globals.css          # SCUMM styles
├── components/
│   ├── game/                # Core layout components
│   ├── panels/              # Modal dialogs
│   ├── narrative/           # Typewriter, intel channels
│   ├── input/               # Phase-specific inputs
│   └── metrics/             # Data displays
└── lib/
    ├── game-state.ts
    ├── llm-client.ts
    └── theme-manager.ts
```

### CLI (Terminal Interface)
```
cli/
├── main.py                  # Classic CLI (golden)
├── main_dashboard.py        # Future: dashboard entry point
├── dashboard.py             # Future: Rich layout UI
├── rich_ui.py               # Current enhanced UI
├── theme.py                 # Color palettes
└── formatters.py            # Text formatting
```

---

## Key Decisions Log

### 2025-11-23: Shadcn Component Selection
**Decision:** Use official Shadcn components with Dark Matter-inspired theme  
**Rationale:** Research (see 05_ARCHIVED_RESEARCH/shadcn-research.md) showed:
- Command component perfect for CLI-style interaction
- Dark Matter theme matches Professional Calm aesthetic
- Official components safer than third-party registries

**Priority components:**
1. Command (CMDK) - command palette
2. Table - metrics/resources display
3. Dialog - modal panels
4. Card - panel containers
5. Badge - status indicators

### 2025-11-23: SCUMM Aesthetic Choice
**Decision:** Indiana Jones: Fate of Atlantis (1992) visual style  
**Rationale:**
- 256-color VGA (smooth gradients, not blocky pixels)
- Painterly panels with depth
- Serious, sophisticated tone appropriate for political thriller
- Proven adventure game UI layout

**Color adaptation:** Warm browns → cold war blues/greys/teals

---

## Current Sprint

See: [02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md](02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md)

---

## Reporting Schedule

**Weekly Status Reports:** Every Friday  
**Location:** `04_PROGRESS_REPORTS/YYYY-MM-DD_Status.md`

**Format:**
- Completed this week
- Blockers encountered
- Next week targets
- Phase progress percentage

---

## Contact & References

**Primary Documentation:**
- [FULL_STACK_DEPLOYMENT_PACKAGE.md](FULL_STACK_DEPLOYMENT_PACKAGE.md) - Strategic roadmap
- [WEB_UI_DEPLOYMENT_PACKAGE.md](WEB_UI_DEPLOYMENT_PACKAGE.md) - Frontend implementation guide

**Phase Details:**
- [01_PHASE_PLANS/](01_PHASE_PLANS/) - Detailed task breakdowns per phase

**Technical Specs:**
- [03_TECHNICAL_SPECS/API_Contracts.md](03_TECHNICAL_SPECS/API_Contracts.md) - Backend contracts
- [03_TECHNICAL_SPECS/Component_Library.md](03_TECHNICAL_SPECS/Component_Library.md) - Frontend components
- [03_TECHNICAL_SPECS/File_Structure.md](03_TECHNICAL_SPECS/File_Structure.md) - Directory templates

---

**Last Updated:** 23 November 2025 (Phase 0 Complete)  
**Next Review:** Phase 1 mid-point

