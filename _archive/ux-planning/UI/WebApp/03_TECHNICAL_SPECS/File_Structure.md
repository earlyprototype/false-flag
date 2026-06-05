# File Structure Reference
**Purpose:** Directory templates and file organization for the FALSE FLAG project  
**Status:** Living document - updated as structure evolves  

---

## Table of Contents

1. [Overall Project Structure](#overall-project-structure)
2. [Backend Structure](#backend-structure)
3. [Frontend Structure](#frontend-structure)
4. [CLI Structure](#cli-structure)
5. [Documentation Structure](#documentation-structure)

---

## Overall Project Structure

```
wargame/
├── api/                          # Backend API (FastAPI)
├── cli/                          # CLI interfaces
├── data/                         # Game data (scenarios, configs)
├── engine/                       # Core game logic (headless)
├── frontend/                     # Web UI (Next.js)
├── models/                       # Data models
├── tests/                        # Test suites
├── UX/                           # UX documentation
│   └── UI/
│       ├── WebApp/              # Web UI development tracking
│       └── cli/                 # CLI development docs
├── saves/                        # Saved games (CLI + Web)
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── README.md                     # Project overview
```

---

## Backend Structure

### API Layer (`api/`)

```
api/
├── server.py                     # FastAPI app + routes
├── test_client.py                # Smoke tests
├── routes/                       # Route modules (future)
│   ├── game.py                  # Game session routes
│   ├── state.py                 # State/diagnostics routes
│   └── settings.py              # Settings routes
└── middleware/                   # Middleware (future)
    ├── auth.py                  # Authentication
    └── logging.py               # Request logging
```

**Key Files:**
- **server.py** - Main FastAPI application
  - Endpoints for game session management
  - SSE streaming for narrative events
  - CORS configuration for frontend

- **test_client.py** - Automated smoke tests
  - Phase 0: Resources, diplomacy, discussion tests
  - Phase 1+: Decision parity tests
  - Run with: `python api/test_client.py`

---

### Engine Layer (`engine/`)

```
engine/
├── game_manager.py               # Single source of truth
├── initial_conditions.py         # Scenario loader
├── sim_loop.py                   # Turn simulation
├── diplomacy.py                  # Diplomatic encounters
├── intelligence.py               # Intel assessments
├── narrative_state.py            # Narrative/character state
└── world.py                      # World state (metrics, flags)
```

**Key Files:**
- **game_manager.py** - Core game controller
  - Methods: `run_turn_briefing()`, `run_turn_discussion()`, `run_turn_decision()`
  - State management: metrics, advisors, world state
  - All UIs interact through this layer

- **narrative_state.py** - Narrative/character tracking
  - Advisor trust scores
  - Relationship states
  - Situation vibes
  - Character attitudes (immersive mode)

- **world.py** - World simulation state
  - Metrics (escalation_risk, stability, cohesion, casualties)
  - Flags (crisis markers)
  - Turn counter

---

### Models Layer (`models/`)

```
models/
├── game_state.py                 # Core game state models
├── metrics.py                    # Metric definitions
├── advisors.py                   # Advisor definitions
└── scenarios.py                  # Scenario data models
```

---

### Data Layer (`data/`)

```
data/
├── initial_conditions.yaml       # Main scenario data
├── scenarios/                    # Additional scenarios (future)
│   ├── war_game_2025.yaml
│   └── baltic_crisis.yaml
└── prompts/                      # LLM prompt templates
    ├── briefing.txt
    ├── discussion.txt
    └── decision.txt
```

**Key Files:**
- **initial_conditions.yaml** - Starting state
  - UK forces and stockpiles
  - Diplomatic contacts
  - Advisor roster
  - Initial world state

---

## Frontend Structure

### Next.js Web UI (`frontend/`)

```
frontend/
├── app/
│   ├── layout.tsx                # Root layout, font imports
│   ├── page.tsx                  # Main game page
│   ├── start/
│   │   └── page.tsx             # Start screen (Phase 3)
│   ├── globals.css               # Tailwind + SCUMM styles
│   └── api/                      # Next.js API routes (if needed)
│
├── components/
│   ├── game/                     # Core layout components
│   │   ├── SceneViewport.tsx    # Narrative display
│   │   ├── CommandBar.tsx       # Command buttons
│   │   ├── StatusBar.tsx        # Metrics bar
│   │   ├── PhaseHeader.tsx      # Turn/phase header
│   │   └── ConversationLog.tsx  # Message history
│   │
│   ├── panels/                   # Modal dialogs
│   │   ├── StatusPanel.tsx      # /status equivalent
│   │   ├── AdvisorPanel.tsx     # /advise equivalent
│   │   ├── ResourcesPanel.tsx   # /resources equivalent
│   │   ├── DiplomacyPanel.tsx   # /call equivalent
│   │   ├── MenuPanel.tsx        # /menu equivalent
│   │   ├── ThemePanel.tsx       # /theme equivalent
│   │   ├── IntelligencePanel.tsx # /intel equivalent
│   │   └── DecisionReviewDialog.tsx  # Phase 1
│   │
│   ├── narrative/                # Narrative components
│   │   ├── TypewriterText.tsx   # Char-by-char reveal
│   │   ├── IntelChannel.tsx     # Briefing indicator
│   │   ├── MetricChanges.tsx    # Delta display
│   │   └── NarrativeOutcome.tsx # Adjudication display
│   │
│   ├── input/                    # Input components
│   │   ├── QuestionInput.tsx    # Discussion input
│   │   ├── DecisionInput.tsx    # Decision input
│   │   └── DiplomaticInput.tsx  # Diplomacy input
│   │
│   ├── metrics/                  # Metric displays
│   │   ├── MetricsTable.tsx     # Full metrics table
│   │   ├── MetricIndicator.tsx  # Single metric
│   │   ├── ProgressBar.tsx      # ASCII-style bar
│   │   └── StatusBadge.tsx      # Status labels
│   │
│   ├── ui/                       # Shadcn base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── separator.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   ├── tabs.tsx
│   │   └── accordion.tsx
│   │
│   └── ErrorBoundary.tsx         # Error boundary (Phase 0)
│
├── lib/
│   ├── game-state.ts             # Game state management
│   ├── llm-client.ts             # LLM API integration
│   ├── typewriter.ts             # Typewriter effect logic
│   ├── theme-manager.ts          # Theme switching
│   ├── keyboard-shortcuts.ts     # Shortcut system (Phase 4)
│   └── utils.ts                  # Helper functions
│
├── types/
│   ├── game.ts                   # Game state types
│   ├── metrics.ts                # Metrics types
│   └── narrative.ts              # Narrative types
│
├── config/
│   ├── advisors.ts               # Advisor definitions
│   ├── diplomatic-contacts.ts    # Country/diplomat data
│   └── commands.ts               # Command definitions
│
├── public/
│   ├── fonts/                    # Custom fonts (if needed)
│   └── sounds/                   # UI sounds (optional)
│
├── tailwind.config.ts            # Tailwind theme config
├── components.json               # Shadcn configuration
├── tsconfig.json                 # TypeScript config
├── next.config.js                # Next.js config
├── package.json                  # Dependencies
└── .env.local                    # Local environment vars
```

**Key Files:**

- **app/page.tsx** - Main game interface
  - Phase 0-3: Monolithic (700+ lines)
  - Phase 4: Refactored to < 200 lines (composition only)

- **app/globals.css** - Global styles
  - Tailwind directives
  - SCUMM component classes (`.scumm-panel`, `.scumm-button`)
  - Typography classes
  - Custom animations

- **tailwind.config.ts** - Tailwind configuration
  - SCUMM color palettes (4 themes)
  - Custom shadows, border-radius
  - Font families (Crimson, Libre Baskerville, IBM Plex Mono)

- **lib/game-state.ts** - State management
  - Session management
  - Message log
  - Active panel tracking
  - API call wrappers

---

## CLI Structure

### Terminal Interfaces (`cli/`)

```
cli/
├── main.py                       # Classic CLI (golden, don't modify)
├── main_dashboard.py             # Dashboard CLI entry point (Phase 4)
├── dashboard.py                  # Dashboard implementation (Phase 4)
├── rich_ui.py                    # Rich UI helpers
├── theme.py                      # Color palettes
├── formatters.py                 # Text formatting
├── narrator.py                   # Narrator voice
└── panels/                       # Dashboard panels (Phase 4)
    ├── transcript_panel.py
    ├── metrics_panel.py
    └── command_panel.py
```

**Key Files:**

- **main.py** - Classic scrolling CLI (GOLDEN - protected)
  - Entry: `python -m cli.main play`
  - Uses Rich for formatting
  - Supports all game commands
  - Reference implementation for Web UI

- **main_dashboard.py** - Dashboard CLI (Phase 4)
  - Entry: `python -m cli.main dashboard`
  - Uses Rich.Layout for persistent UI
  - Live-updating panels
  - Same game logic as classic CLI

- **theme.py** - CLI color themes
  - Professional Calm (default)
  - High Contrast
  - Warm
  - Semantic color mappings

---

## Documentation Structure

### UX/UI/WebApp/ (Development Tracking)

```
UX/UI/WebApp/
├── 00_MASTER_DEV_PLAN.md         # Central command doc
│
├── 01_PHASE_PLANS/                # Phase-by-phase breakdown
│   ├── Phase_0_Stabilisation.md
│   ├── Phase_1_Decision_Parity.md
│   ├── Phase_2_Deep_State_Intel.md
│   ├── Phase_3_Diplomacy_Meta.md
│   └── Phase_4_Visual_Convergence.md
│
├── 02_IMPLEMENTATION_TRACKING/    # Active development
│   ├── CURRENT_SPRINT.md         # This week's work
│   ├── BLOCKERS.md               # Current impediments
│   └── COMPLETED_TASKS.md        # Done log
│
├── 03_TECHNICAL_SPECS/            # Reference material
│   ├── API_Contracts.md          # API endpoint specs
│   ├── Component_Library.md      # Frontend component specs
│   └── File_Structure.md         # This document
│
├── 04_PROGRESS_REPORTS/           # Weekly status
│   └── YYYY-MM-DD_Status.md      # Dated reports
│
├── 05_ARCHIVED_RESEARCH/          # Historical decisions
│   └── shadcn-research.md        # Component research
│
├── FULL_STACK_DEPLOYMENT_PACKAGE.md  # Strategic roadmap
└── WEB_UI_DEPLOYMENT_PACKAGE.md      # Frontend implementation guide
```

---

### UX/UI/cli/ (CLI Development)

```
UX/UI/cli/
├── CLI_DEVELOPMENT_PACKAGE.md    # CLI design guide
├── DASHBOARD_DEPLOYMENT_PACKAGE.md  # Dashboard plan
├── DASHBOARD_FIX_PLAN.md         # Dashboard fixes (if needed)
└── README.txt                    # CLI docs index
```

---

## Naming Conventions

### Python Files
- **Modules:** `snake_case.py` (e.g., `game_manager.py`)
- **Classes:** `PascalCase` (e.g., `GameManager`)
- **Functions:** `snake_case` (e.g., `run_turn_briefing`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_TURNS`)

### TypeScript/React Files
- **Components:** `PascalCase.tsx` (e.g., `SceneViewport.tsx`)
- **Utilities:** `kebab-case.ts` (e.g., `game-state.ts`)
- **Types:** `PascalCase` (e.g., `GameState`, `Metrics`)
- **Interfaces:** `PascalCase` with `I` prefix optional (e.g., `StatusPanelProps`)

### Documentation Files
- **Core docs:** `UPPER_SNAKE_CASE.md` (e.g., `README.md`, `MASTER_DEV_PLAN.md`)
- **Phase plans:** `Phase_N_Name.md` (e.g., `Phase_0_Stabilisation.md`)
- **Progress reports:** `YYYY-MM-DD_Status.md`

---

## File Size Guidelines

### Keep Files Manageable
- **Components:** < 300 lines (split if larger)
- **Pages:** < 200 lines in Phase 4 (composition only)
- **API routes:** < 500 lines (split into route modules if larger)
- **Engine modules:** < 600 lines

### When to Split
If a file exceeds guideline:
1. Extract subcomponents
2. Create utility modules
3. Use composition patterns
4. Consider feature modules

---

## Import Conventions

### Frontend (TypeScript)
```typescript
// External libraries first
import React, { useState } from 'react';
import { Dialog } from '@/components/ui/dialog';

// Internal utilities
import { cn } from '@/lib/utils';

// Types
import type { GameState, Metrics } from '@/types/game';

// Local components
import { MetricIndicator } from './MetricIndicator';
```

### Backend (Python)
```python
# Standard library first
import os
from typing import Dict, List

# External libraries
from fastapi import FastAPI, HTTPException

# Internal modules
from engine.game_manager import GameManager
from models.game_state import GameState

# Local imports
from .utils import parse_metrics
```

---

## Development Workflow

### Adding New Features

1. **Planning** - Document in phase plan
2. **Spec** - Update API contracts or component library
3. **Implement** - Write code in appropriate directory
4. **Test** - Add tests in `tests/`
5. **Document** - Update relevant docs
6. **Track** - Log in CURRENT_SPRINT.md
7. **Complete** - Move to COMPLETED_TASKS.md

### File Creation Checklist

Before creating new file:
- [ ] Is there an existing file that should be extended?
- [ ] Does this belong in a subdirectory?
- [ ] Is the naming convention correct?
- [ ] Is the location logical for imports?
- [ ] Will this file be < 300 lines?

---

**Last Updated:** 23 Nov 2025  
**Next Update:** When file structure changes significantly


