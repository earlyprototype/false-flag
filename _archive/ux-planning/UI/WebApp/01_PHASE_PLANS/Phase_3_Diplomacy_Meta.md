# Phase 3: Diplomacy & Meta-Game
**Status:** PENDING (blocked by Phase 2)  
**Goal:** Full parity for diplomatic encounters, save/load, settings  
**Estimated Duration:** 3-4 weeks  

---

## Overview

This phase brings meta-game features to Web UI:
- **Diplomatic encounters** (`/call`) - structured conversations with foreign leaders
- **Save/load system** - persist game state to disk
- **Scenario selection** - choose starting conditions
- **Game settings** - difficulty, play mode, LLM config
- **Theme switching** - SCUMM themes (DEFCON/Retro/Slate/Standard)

---

## Exit Criteria

- [ ] Diplomatic encounter system functional in Web UI
- [ ] Save/load works for both CLI and Web (shared format)
- [ ] Web start screen allows scenario/difficulty/mode selection
- [ ] LLM configuration panel works
- [ ] Theme selector applies SCUMM themes dynamically
- [ ] All meta-game features match CLI functionality

---

## Task Breakdown

### 1. Diplomacy Engine Backend

#### 1.1 Enhance Diplomatic Encounter API
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (enhance `POST /game/action/call`)
- `engine/diplomacy.py` (method: `run_diplomatic_encounter`)

**Current API (basic):**
```
POST /game/action/call
Body: { "session_id": str, "country_name": str }
Response: { "status": "processed" }  # SSE stream only
```

**Enhanced API:**
```
POST /game/action/call
Body: { 
  "session_id": str, 
  "country_name": str,
  "approach": "formal" | "direct" | "urgent"  // optional
}
Response: { "status": "processed" }

SSE Events:
- "encounter_intro" - { "counterpart": str, "title": str, "mood": str }
- "dialogue" - { "speaker": str, "text": str, "sentiment": str }
- "options" - { "choices": [str] }
- "outcome" - { "cohesion_delta": int, "notes": str }
- "state_update" - { "metrics": {...}, "phase": str }
```

**Tasks:**
- [ ] Structure `run_diplomatic_encounter` to emit discrete events
- [ ] Emit `encounter_intro` with counterpart details
- [ ] Emit `dialogue` for each exchange
- [ ] Emit `options` for player choice points
- [ ] Emit `outcome` with consequences
- [ ] Update alliance_cohesion metric
- [ ] Add unit test for structured output

---

#### 1.2 Get Available Contacts Endpoint (Already in Phase 0)
**Owner:** Backend  
**Status:** ✅ COMPLETE (from Phase 0)  
**Files:**
- `api/server.py` (`GET /game/{id}/diplomacy/contacts`)

No additional work needed - Phase 0 already covers this.

---

### 2. Save/Load System Backend

#### 2.1 Create Save Game Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/game_manager.py` (method: `save_game`)

**Required API Endpoint:**
```
POST /game/save
Body: {
  "session_id": str,
  "save_name": str
}
Response: {
  "success": true,
  "save_path": "saves/my_game_2025-11-23.json",
  "timestamp": "2025-11-23T16:30:00Z"
}
```

**Save Format (JSON):**
```json
{
  "metadata": {
    "save_name": "Critical Decision Point",
    "saved_at": "2025-11-23T16:30:00Z",
    "game_version": "1.0.0"
  },
  "game_state": {
    "scenario_id": "war_game_2025",
    "turn": 5,
    "phase": "discussion",
    "metrics": { ... },
    "world": { ... },
    "narrative_state": { ... }
  }
}
```

**Tasks:**
- [ ] Create `saves/` directory if not exists
- [ ] Serialize `GameManager` state to JSON
- [ ] Save to `saves/{save_name}_{timestamp}.json`
- [ ] Make format compatible with CLI save format
- [ ] Add unit test

---

#### 2.2 Create Load Game Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/game_manager.py` (method: `load_game`)

**Required API Endpoint:**
```
POST /game/load
Body: {
  "save_path": "saves/my_game_2025-11-23.json"
}
Response: {
  "session_id": str,
  "turn": int,
  "phase": str,
  "metrics": { ... }
}
```

**Tasks:**
- [ ] Load JSON from `saves/` directory
- [ ] Deserialize into `GameManager` instance
- [ ] Create new session ID
- [ ] Return current game state
- [ ] Add unit test

---

#### 2.3 List Saves Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)

**Required API Endpoint:**
```
GET /game/saves
Response: {
  "saves": [
    {
      "path": "saves/my_game_2025-11-23.json",
      "name": "Critical Decision Point",
      "timestamp": "2025-11-23T16:30:00Z",
      "turn": 5,
      "scenario": "war_game_2025"
    }
  ]
}
```

**Tasks:**
- [ ] Scan `saves/` directory
- [ ] Read metadata from each save file
- [ ] Return sorted by timestamp (newest first)
- [ ] Add unit test

---

### 3. Scenario & Settings Backend

#### 3.1 Create Scenario List Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `data/` directory (scan for scenario files)

**Required API Endpoint:**
```
GET /scenarios
Response: {
  "scenarios": [
    {
      "id": "war_game_2025",
      "name": "War Game 2025",
      "description": "Rapid escalation in Eastern Europe...",
      "difficulty_options": ["easy", "standard", "hard"],
      "mode_options": ["classic", "immersive", "emergent"]
    }
  ]
}
```

**Tasks:**
- [ ] Scan `data/` for scenario YAML files
- [ ] Parse metadata from each scenario
- [ ] Return available scenarios
- [ ] Add unit test

---

#### 3.2 Create LLM Config Endpoints
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoints)
- `engine/llm_config.py` (if exists, or create)

**Get Config Endpoint:**
```
GET /settings/llm
Response: {
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Set Config Endpoint:**
```
POST /settings/llm
Body: {
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7
}
Response: { "success": true }
```

**Tasks:**
- [ ] Store LLM config in session or global settings
- [ ] Validate config before applying
- [ ] Add unit test

---

### 4. Frontend - Diplomacy Panel

#### 4.1 Create Enhanced Diplomacy Panel
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/panels/DiplomacyPanel.tsx` (enhance or replace)

**Layout:**
```
┌─────────────────────────────────────────────┐
│ DIPLOMATIC ENCOUNTER                        │
├─────────────────────────────────────────────┤
│ [SELECT CONTACT]  [CALL IN PROGRESS]       │
│                                             │
│ === SELECT CONTACT ===                      │
│                                             │
│ United States                               │
│ > President (direct line)                  │
│   Disposition: Supportive                   │
│                                             │
│ France                                      │
│ > Foreign Minister                         │
│   Disposition: Cautious                     │
│                                             │
│ [SELECT APPROACH]                           │
│ ○ Formal    ○ Direct    ○ Urgent           │
│                                             │
│ [INITIATE CALL]                             │
└─────────────────────────────────────────────┘

After call initiated:
┌─────────────────────────────────────────────┐
│ CALL IN PROGRESS - US President            │
├─────────────────────────────────────────────┤
│ [President Carter]:                         │
│ "Prime Minister, we're concerned about..."  │
│                                             │
│ [You]:                                      │
│ "Mr. President, we need your support on..." │
│                                             │
│ [President Carter]:                         │
│ "I understand. What specifically do you..." │
│                                             │
│ === YOUR RESPONSE ===                       │
│ > Request immediate military support        │
│ > Seek diplomatic coordination              │
│ > Express concern about lack of action      │
│                                             │
│ [OUTCOME]                                   │
│ Alliance Cohesion: +5                       │
│ Notes: President committed to joint patrol │
└─────────────────────────────────────────────┘
```

**Component Structure:**
```typescript
interface DiplomacyPanelProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}
```

**Tasks:**
- [ ] Fetch contacts from `/game/{id}/diplomacy/contacts`
- [ ] Display contact list with access levels and dispositions
- [ ] Add approach selector (formal/direct/urgent)
- [ ] On "Initiate Call", POST to `/game/action/call`
- [ ] Listen to SSE for encounter events
- [ ] Display dialogue as it streams
- [ ] Show options when emitted, allow player selection
- [ ] Display outcome and cohesion delta
- [ ] Style with SCUMM panel classes

---

### 5. Frontend - Start Screen

#### 5.1 Create Game Start Screen
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/start/page.tsx` (create new route)
- `frontend/app/page.tsx` (redirect if no active session)

**Layout:**
```
┌─────────────────────────────────────────────┐
│        FALSE FLAG: THE WARGAME              │
│                                             │
│  [NEW GAME]         [LOAD GAME]            │
│                                             │
│  === NEW GAME ===                           │
│                                             │
│  Scenario:                                  │
│  ○ War Game 2025                           │
│    Rapid escalation in Eastern Europe...   │
│                                             │
│  Difficulty:                                │
│  ○ Easy    ○ Standard    ○ Hard            │
│                                             │
│  Play Mode:                                 │
│  ○ Classic - Helpful advisors              │
│  ○ Immersive - Personality-driven advisors │
│  ○ Emergent - Surprise outcomes            │
│                                             │
│  [START GAME]                               │
│                                             │
│  === LOAD GAME ===                          │
│                                             │
│  > Critical Decision Point                  │
│    Turn 5 - 2025-11-23 16:30               │
│                                             │
│  > Baltic Crisis Peak                       │
│    Turn 8 - 2025-11-22 14:15               │
│                                             │
│  [LOAD SELECTED]                            │
└─────────────────────────────────────────────┘
```

**Tasks:**
- [ ] Fetch scenarios from `/scenarios`
- [ ] Display scenario details
- [ ] Add difficulty and mode selectors
- [ ] On "Start Game", POST to `/game/new` with selections
- [ ] Fetch save list from `/game/saves`
- [ ] Display saves with metadata
- [ ] On "Load Selected", POST to `/game/load`
- [ ] Redirect to main game page after start/load

---

### 6. Frontend - Settings Panels

#### 6.1 Create LLM Settings Panel
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/panels/LLMSettingsPanel.tsx` (create)

**Layout:**
```
┌─────────────────────────────────────────────┐
│ LLM CONFIGURATION                           │
├─────────────────────────────────────────────┤
│ Provider:                                   │
│ ○ OpenAI    ○ Anthropic    ○ Local         │
│                                             │
│ Model:                                      │
│ [gpt-4                          ▼]         │
│                                             │
│ Temperature: 0.7                            │
│ [━━━━━━━●━━━━━━━] (0.0 - 2.0)             │
│                                             │
│ Max Tokens: 2000                            │
│ [━━━━━━━●━━━━━━━] (500 - 4000)            │
│                                             │
│ [SAVE] [CANCEL]                             │
└─────────────────────────────────────────────┘
```

**Tasks:**
- [ ] Fetch current config from `/settings/llm`
- [ ] Display provider/model/temperature/max_tokens
- [ ] Add sliders for temperature and max_tokens
- [ ] On "Save", POST to `/settings/llm`
- [ ] Show confirmation message

---

#### 6.2 Create Theme Selector Panel
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/panels/ThemePanel.tsx` (create)
- `frontend/lib/theme-manager.ts` (create)

**Themes (from WEB_UI_DEPLOYMENT_PACKAGE):**
1. **DEFCON** (default) - Cold war blues/greys/orange
2. **Standard** - Cyan/blue accent colors
3. **Retro** - Phosphor green monochrome
4. **Slate** - High contrast black/white

**Layout:**
```
┌─────────────────────────────────────────────┐
│ THEME SELECTION                             │
├─────────────────────────────────────────────┤
│ ● DEFCON         [Preview]                 │
│   Cold War Tactical                         │
│                                             │
│ ○ Standard       [Preview]                 │
│   Modern Interface                          │
│                                             │
│ ○ Retro          [Preview]                 │
│   Phosphor Terminal                         │
│                                             │
│ ○ Slate          [Preview]                 │
│   High Contrast                             │
│                                             │
│ [APPLY]                                     │
└─────────────────────────────────────────────┘
```

**Tasks:**
- [ ] Create theme-manager.ts to handle CSS variable switching
- [ ] Define all 4 theme CSS variable sets
- [ ] Display theme options with preview swatches
- [ ] On selection, apply theme to `<html>` element via class
- [ ] Persist theme choice to localStorage
- [ ] Add theme buttons with icons showing current theme

---

### 7. Testing

#### 7.1 Backend Tests
**Owner:** Backend  
**Status:** ⏸ PENDING  

**Test Cases:**
1. **Diplomatic Encounter Test**
   - [ ] POST `/game/action/call` emits structured SSE events
   - [ ] Outcome includes cohesion_delta
   
2. **Save Game Test**
   - [ ] POST `/game/save` creates file in `saves/`
   - [ ] File contains valid JSON with all state

3. **Load Game Test**
   - [ ] POST `/game/load` restores exact state
   - [ ] Metrics and turn match saved values

4. **List Saves Test**
   - [ ] GET `/game/saves` returns all saves
   - [ ] Sorted by timestamp

5. **Scenarios Test**
   - [ ] GET `/scenarios` returns available scenarios

6. **LLM Config Test**
   - [ ] GET/POST `/settings/llm` works
   - [ ] Invalid config rejected

---

#### 7.2 Frontend Integration Tests
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Test Protocol:**
1. **Start Screen Test**
   - Open start screen
   - Verify scenarios load
   - Select difficulty/mode
   - Start game
   - Verify game session created

2. **Save/Load Test**
   - Play to turn 3
   - Save game with name "Test Save"
   - Verify save appears in list
   - Load save
   - Verify turn/metrics restored

3. **Diplomacy Test**
   - Open DIPLOMACY panel
   - Select contact
   - Choose approach
   - Initiate call
   - Verify dialogue streams
   - Select response option
   - Verify outcome shown

4. **Settings Test**
   - Open LLM Settings
   - Change temperature
   - Save
   - Verify config updated

5. **Theme Test**
   - Open Theme panel
   - Switch to Retro theme
   - Verify colors change
   - Reload page
   - Verify theme persists

---

### 8. Documentation

#### 8.1 Update API Contracts
**Owner:** Backend  
**Status:** ⏸ PENDING  

**Tasks:**
- [ ] Document enhanced `/game/action/call`
- [ ] Document `/game/save`, `/game/load`, `/game/saves`
- [ ] Document `/scenarios`
- [ ] Document `/settings/llm`

---

#### 8.2 Update Component Library
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Tasks:**
- [ ] Document DiplomacyPanel component
- [ ] Document StartScreen component
- [ ] Document LLMSettingsPanel component
- [ ] Document ThemePanel component
- [ ] Document theme-manager utility

---

## Dependencies

**Blocks:**
- Phase 4 (Visual Convergence & Polish)

**Blocked By:**
- Phase 2 complete (deep state & intel functional)

**External Dependencies:**
- `diplomacy.py` - encounter logic
- `data/` - scenario files
- `saves/` - directory for save files

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Save format incompatible between CLI and Web | High | Define shared JSON schema, test cross-compatibility |
| Diplomatic encounters too slow (LLM calls) | Medium | Stream incrementally, show progress indicators |
| Theme switching breaks styling | Medium | Test all components in all themes before release |
| Start screen overwhelming (too many options) | Low | Use progressive disclosure, good defaults |

---

## Success Metrics

- **Save/load system** works seamlessly across CLI and Web
- **Diplomatic encounters** feel rich and consequential
- **Start screen** makes game accessible to new players
- **Settings** give players control without overwhelming
- **Themes** work consistently across all components

---

## Notes

**Why This Matters:**
Meta-game features transform the prototype into a complete game. Save/load enables long campaigns, scenario selection adds replayability, and themes let players customise their experience.

**ADHD-Friendly Approach:**
- Break into 3 streams: Diplomacy, Save/Load, Settings
- Each stream independent (can be done in any order)
- Clear visual milestones (Start Screen functional, Theme switching works)
- Test each stream before integration

---

**Previous Phase:** [Phase_2_Deep_State_Intel.md](Phase_2_Deep_State_Intel.md)  
**Next Phase:** [Phase_4_Visual_Convergence.md](Phase_4_Visual_Convergence.md)


