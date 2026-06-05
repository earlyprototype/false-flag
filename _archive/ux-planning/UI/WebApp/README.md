# FALSE FLAG - Web UI Development Tracking

**Purpose:** Structured development plan, progress tracking, and technical reference for Web UI + CLI Dashboard convergence  
**Created:** 23 November 2025  
**Status:** Phase 0 - Stabilisation (Active)  

---

## Quick Start

### New to This Project?
1. Read [00_MASTER_DEV_PLAN.md](00_MASTER_DEV_PLAN.md) - **START HERE**
2. Check current phase in [02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md](02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md)
3. Review technical specs in [03_TECHNICAL_SPECS/](03_TECHNICAL_SPECS/)

### Working on a Task?
1. Check [02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md](02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md) for active work
2. Review phase details in [01_PHASE_PLANS/](01_PHASE_PLANS/)
3. Reference API or components in [03_TECHNICAL_SPECS/](03_TECHNICAL_SPECS/)
4. Update sprint doc when task complete

### Blocked on Something?
1. Add to [02_IMPLEMENTATION_TRACKING/BLOCKERS.md](02_IMPLEMENTATION_TRACKING/BLOCKERS.md)
2. Alert project lead
3. Check if there's a workaround in phase plan

---

## Folder Structure

```
UX/UI/WebApp/
├── 00_MASTER_DEV_PLAN.md          # Central command - START HERE
│
├── 01_PHASE_PLANS/                 # Detailed phase breakdowns
│   ├── Phase_0_Stabilisation.md    # (CURRENT) API contracts, defensive frontend
│   ├── Phase_1_Decision_Parity.md  # Decision Review dialog, interpret/commit
│   ├── Phase_2_Deep_State_Intel.md # Vibes, trust, flags, intel endpoints
│   ├── Phase_3_Diplomacy_Meta.md   # Diplomacy, save/load, settings
│   └── Phase_4_Visual_Convergence.md # SCUMM refactor, CLI Dashboard, polish
│
├── 02_IMPLEMENTATION_TRACKING/     # Active development
│   ├── CURRENT_SPRINT.md          # This week's tasks and progress
│   ├── BLOCKERS.md                # Current impediments
│   └── COMPLETED_TASKS.md         # Done log with retrospectives
│
├── 03_TECHNICAL_SPECS/             # Reference material
│   ├── API_Contracts.md           # All backend endpoint specs
│   ├── Component_Library.md       # All frontend component specs
│   └── File_Structure.md          # Directory templates and conventions
│
├── 04_PROGRESS_REPORTS/            # Weekly status snapshots
│   └── 2025-11-23_Project_Kickoff.md
│
├── 05_ARCHIVED_RESEARCH/           # Historical decisions
│   └── shadcn-research.md         # Component selection research
│
├── FULL_STACK_DEPLOYMENT_PACKAGE.md  # Strategic roadmap (reference)
├── WEB_UI_DEPLOYMENT_PACKAGE.md      # Frontend implementation guide (reference)
└── README.md                       # This file
```

---

## Numbered Folder System

### Why Numbers?
- **Clear hierarchy** - 00 is most important, 01-05 are reference/tracking
- **Alphabetical sorting** - Folders appear in logical order
- **ADHD-friendly** - Reduces cognitive load when navigating
- **Explicit priority** - No ambiguity about what to read first

### Folder Purposes

**00 - Master Plan**
- Single file, single source of truth
- Overall progress tracker
- Quick navigation to all other docs

**01 - Phase Plans**
- One file per phase (5 total)
- Detailed task breakdowns
- Exit criteria and dependencies
- ADHD-friendly chunked tasks

**02 - Implementation Tracking**
- Live documents (updated daily/weekly)
- Current sprint work
- Active blockers
- Completed task log

**03 - Technical Specs**
- Reference material (stable, updated per phase)
- API contracts for backend
- Component library for frontend
- File structure and conventions

**04 - Progress Reports**
- Weekly status snapshots
- Historical record of progress
- Retrospectives and learnings

**05 - Archived Research**
- Historical decisions preserved
- No longer active, but referenced

---

## How to Use This System

### Starting Your Day
1. Check [CURRENT_SPRINT.md](02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md)
2. Find your active task
3. Review phase plan for context
4. Reference technical specs as needed

### Completing a Task
1. Mark task complete in CURRENT_SPRINT.md
2. Move to COMPLETED_TASKS.md with notes
3. Update MASTER_DEV_PLAN.md status (change ⏸ to ✅)
4. Commit changes with clear message

### Encountering a Blocker
1. Document in [BLOCKERS.md](02_IMPLEMENTATION_TRACKING/BLOCKERS.md)
2. Assess severity (Critical/High/Medium/Low)
3. Identify mitigation options
4. Alert team if High/Critical

### Finishing a Phase
1. Verify all exit criteria met
2. Update COMPLETED_TASKS.md with retrospective
3. Create weekly progress report in 04_PROGRESS_REPORTS/
4. Update MASTER_DEV_PLAN.md (advance current phase)
5. Review next phase plan as team

---

## Phase Overview

### Phase 0: Stabilisation (CURRENT)
**Duration:** 1-2 weeks  
**Goal:** No crashes, predictable API contracts  
**Key Tasks:**
- Define API contract schemas
- Standardise resources/diplomacy endpoints
- Add defensive data handling to frontend
- Create smoke test suite

**Exit Criteria:**
- All Phase 0 endpoints documented
- Frontend handles missing data gracefully
- Smoke tests pass
- CLI unchanged

---

### Phase 1: Decision Parity
**Duration:** 2-3 weeks  
**Goal:** Web App matches CLI's decision discipline  
**Key Tasks:**
- Split decision into interpret/commit endpoints
- Create Decision Review dialog
- Implement critical concerns handling

**Exit Criteria:**
- Web decision flow includes interpretation step
- CLI and Web semantically identical

---

### Phase 2: Deep State & Intel
**Duration:** 2-3 weeks  
**Goal:** Surface diagnostic data (vibes, trust, flags, intel)  
**Key Tasks:**
- Vibes/trust/flags API endpoints
- Intelligence assessment endpoints
- Enhanced Status panel
- New Intelligence panel

**Exit Criteria:**
- Full diagnostic visibility matching CLI
- Intel panel provides strategic insights

---

### Phase 3: Diplomacy & Meta-Game
**Duration:** 3-4 weeks  
**Goal:** Full parity for diplomacy, save/load, settings  
**Key Tasks:**
- Enhanced diplomatic encounters
- Save/load system
- Start screen (scenario selection)
- LLM config panel
- Theme selector

**Exit Criteria:**
- Save/load works across CLI and Web
- All meta-game features match CLI

---

### Phase 4: Visual Convergence & Polish
**Duration:** 3-4 weeks  
**Goal:** SCUMM aesthetic fully realised, CLI Dashboard complete  
**Key Tasks:**
- Refactor page.tsx into modular components
- Apply SCUMM styling consistently
- Implement CLI Dashboard
- Keyboard shortcuts
- Accessibility audit
- Performance optimisation

**Exit Criteria:**
- Web UI codebase maintainable (< 200 line page.tsx)
- CLI Dashboard functional
- Accessibility score 90+
- Performance score 90+

---

## Key Principles

### Golden Code Protection
**NEVER modify without strong justification:**
- `engine/` - Core game logic
- `models/` - Data structures
- `data/` - Scenarios
- `cli/main.py` - Classic CLI

### ADHD-Friendly Workflow
- **One phase at a time** - Complete before moving forward
- **Clear exit criteria** - No ambiguity about "done"
- **Visual progress** - Master plan shows status
- **Chunked tasks** - No task > 1 day of work
- **Explicit dependencies** - Know what blocks what

### Safety Rails
- All major changes behind feature flags
- Incremental refactoring (test after each step)
- Rollback strategy: stop web/API, run CLI directly
- Test CLI before every commit

---

## Contributing

### Before Starting Work
1. Read relevant phase plan
2. Check for blockers
3. Understand acceptance criteria
4. Review technical specs

### While Working
1. Update CURRENT_SPRINT.md (mark in_progress)
2. Document decisions in code comments
3. Write tests alongside code
4. Ask questions early (don't get stuck)

### Before Committing
1. Test your changes
2. Test CLI still works (`python -m cli.main play`)
3. Update relevant docs
4. Mark task complete in tracking docs

---

## Documentation Standards

### UK English
All documentation in UK English (colour not color, organisation not organization)

### Code Comments
- **What** is obvious from code
- **Why** should be in comments
- **How** can be in comments if complex

### Markdown Formatting
- Use headers for structure (# ## ###)
- Use code blocks with language tags
- Use checkboxes for task lists
- Use tables for comparisons
- Use blockquotes for important notes

---

## Contact & Help

**Questions about:**
- **Architecture/Design** - Check FULL_STACK_DEPLOYMENT_PACKAGE.md or MASTER_DEV_PLAN.md
- **API Contracts** - Check 03_TECHNICAL_SPECS/API_Contracts.md
- **Components** - Check 03_TECHNICAL_SPECS/Component_Library.md
- **File Organization** - Check 03_TECHNICAL_SPECS/File_Structure.md
- **Current Work** - Check 02_IMPLEMENTATION_TRACKING/CURRENT_SPRINT.md

**Stuck?** Document in BLOCKERS.md and alert team.

---

## Project Vision

Create two primary front-ends (CLI Dashboard + Web App) sharing a unified headless engine, with:
- **Feature parity** between interfaces
- **SCUMM-style aesthetic** for web (Indiana Jones: Fate of Atlantis 1992)
- **Professional Calm theme** for CLI
- **ADHD-friendly design** throughout
- **Safe, reversible** development workflow

**End Result:** A serious political crisis simulation game playable in browser or terminal, with deep strategic gameplay and a polished retro-modern interface.

---

**Last Updated:** 23 November 2025  
**Next Review:** Phase 0 completion (29 Nov 2025)  
**Maintainer:** Project Lead


