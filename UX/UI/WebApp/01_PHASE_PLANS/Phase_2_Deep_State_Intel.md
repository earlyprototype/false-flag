# Phase 2: Deep State & Intel
**Status:** PENDING (blocked by Phase 1)  
**Goal:** Surface diagnostic data (vibes, trust, flags, intel)  
**Estimated Duration:** 2-3 weeks  

---

## Overview

The CLI exposes deep state diagnostics through `/status` and `/intel` commands:
- **Situation vibes** - narrative atmosphere descriptors
- **Advisor trust scores** - relationship metrics with each advisor
- **World flags** - active crisis markers
- **Intelligence assessments** - detailed actor dossiers

This phase brings that diagnostic depth to the Web UI.

---

## Exit Criteria

- [ ] API endpoints for vibes, trust, flags, and intel implemented
- [ ] Web Status panel shows trust bars and active flags
- [ ] Web Intelligence panel can view actor dossiers
- [ ] Data updates in real-time as game state changes
- [ ] CLI `/status` and `/intel` behaviour unchanged

---

## Task Breakdown

### 1. Backend API - Situation Vibes

#### 1.1 Create Vibes Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/narrative_state.py` (method: `get_situation_vibes()`)

**CLI Current Access:**
```python
vibes = self.narrative_state.get_situation_vibes()
# Returns: ["tense", "uncertainty", "resolve"]
```

**Required API Endpoint:**
```
GET /game/{id}/state/vibes
Response: {
  "vibes": ["tense", "uncertainty", "resolve"],
  "dominant": "tense",
  "intensity": 7  // 0-10 scale
}
```

**Tasks:**
- [ ] Expose `narrative_state.get_situation_vibes()` via API
- [ ] Add dominant vibe calculation (most frequent/weighted)
- [ ] Add intensity score (based on escalation_risk)
- [ ] Add unit test

---

### 2. Backend API - Advisor Trust

#### 2.1 Create Advisor Trust Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/narrative_state.py` (data: `characters`)

**CLI Current Access:**
```python
for role, char in self.narrative_state.characters.items():
    trust = char.get("trust", 50)
    relationship = char.get("relationship", "professional")
```

**Required API Endpoint:**
```
GET /game/{id}/state/advisors
Response: {
  "advisors": [
    {
      "role": "NSA",
      "name": "Sir Humphrey Appleby",
      "trust": 65,
      "relationship": "cautious",
      "status": "active",
      "notes": "Skeptical of military action"
    }
  ]
}
```

**Tasks:**
- [ ] Extract advisor data from `narrative_state.characters`
- [ ] Map trust scores (0-100 scale)
- [ ] Map relationship types (professional/supportive/cautious/adversarial)
- [ ] Include advisor status (active/absent/replaced)
- [ ] Add unit test

---

### 3. Backend API - World Flags

#### 3.1 Create Flags Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/world.py` (data: `world.flags`)

**CLI Current Access:**
```python
for flag, value in self.world.flags.items():
    if value:  # Only show active flags
        print(f"[ACTIVE] {flag}")
```

**Required API Endpoint:**
```
GET /game/{id}/state/flags
Response: {
  "active_flags": [
    {
      "key": "russian_mobilisation",
      "label": "Russian Mobilisation Detected",
      "severity": "critical",
      "turn_activated": 3
    }
  ],
  "inactive_flags": [
    {
      "key": "nato_article_5",
      "label": "NATO Article 5 Invoked"
    }
  ]
}
```

**Tasks:**
- [ ] Expose `world.flags` dictionary via API
- [ ] Separate active (true) from inactive (false) flags
- [ ] Add human-readable labels for each flag
- [ ] Add severity classification (critical/elevated/monitoring)
- [ ] Track when flag was activated (turn number)
- [ ] Add unit test

---

### 4. Backend API - Intelligence

#### 4.1 Create Intel List Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/intelligence.py`

**Required API Endpoint:**
```
GET /game/{id}/intel
Response: {
  "available_actors": [
    {
      "code": "RUS",
      "name": "Russia",
      "category": "adversary",
      "last_updated": "Turn 5"
    },
    {
      "code": "US",
      "name": "United States",
      "category": "ally",
      "last_updated": "Turn 4"
    }
  ]
}
```

**Tasks:**
- [ ] List all actors with available intelligence
- [ ] Categorise actors (ally/neutral/adversary)
- [ ] Track last assessment turn
- [ ] Add unit test

---

#### 4.2 Create Intel Detail Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/intelligence.py` (method: `generate_actor_detailed_assessment`)

**CLI Current Access:**
```python
assessment = generate_actor_detailed_assessment(
    actor_name="Russia",
    world=self.world,
    player_metrics=self.metrics
)
```

**Required API Endpoint:**
```
GET /game/{id}/intel/{actor_code}
Response: {
  "actor": "Russia",
  "code": "RUS",
  "assessment": {
    "military_posture": "Aggressive buildup along borders...",
    "political_intent": "Seeking to fracture NATO cohesion...",
    "economic_factors": "Sanctions causing domestic strain...",
    "likely_next_moves": [
      "Escalate hybrid warfare",
      "Test NATO resolve with probes"
    ],
    "vulnerabilities": [
      "Economic isolation",
      "Domestic unrest potential"
    ]
  },
  "confidence": "medium",
  "last_updated": 5
}
```

**Tasks:**
- [ ] Expose `generate_actor_detailed_assessment` via API
- [ ] Parse assessment into structured sections
- [ ] Add confidence level (high/medium/low)
- [ ] Track last update turn
- [ ] Add unit test
- [ ] Add caching (don't regenerate every request)

---

### 5. Frontend - Status Panel Enhancement

#### 5.1 Extend Status Panel Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/panels/StatusPanel.tsx`
- `frontend/app/page.tsx`

**Current Status Panel:**
Shows basic metrics only.

**Enhanced Status Panel Layout:**
```
┌─────────────────────────────────────────┐
│ STATUS OVERVIEW                         │
├─────────────────────────────────────────┤
│ [METRICS TAB] [ADVISORS TAB] [FLAGS TAB]│
│                                         │
│ === ADVISORS ===                        │
│                                         │
│ NSA - Sir Humphrey Appleby              │
│ Trust: ████████░░ 65/100                │
│ Relationship: Cautious                  │
│                                         │
│ CDS - General Sarah Mitchell            │
│ Trust: ███████████ 85/100               │
│ Relationship: Supportive                │
│                                         │
│ === ACTIVE FLAGS ===                    │
│                                         │
│ ⚠ [CRITICAL] Russian Mobilisation      │
│    Activated: Turn 3                    │
│                                         │
│ ⚡ [ELEVATED] Naval Incident             │
│    Activated: Turn 4                    │
└─────────────────────────────────────────┘
```

**Tasks:**
- [ ] Add tabbed interface (Metrics/Advisors/Flags)
- [ ] Fetch advisor trust data from `/game/{id}/state/advisors`
- [ ] Display trust bars (use ProgressBar component)
- [ ] Color-code relationships (supportive=green, cautious=yellow, adversarial=red)
- [ ] Fetch active flags from `/game/{id}/state/flags`
- [ ] Display flags with severity badges
- [ ] Show turn activated for each flag
- [ ] Add "Situation: [dominant vibe]" header from `/state/vibes`

---

### 6. Frontend - Intelligence Panel

#### 6.1 Create Intelligence Panel Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/panels/IntelligencePanel.tsx` (create)
- `frontend/app/page.tsx` (integrate)

**Layout:**
```
┌───────────────────────────────────────────────┐
│ INTELLIGENCE ASSESSMENTS                      │
├─────────────┬─────────────────────────────────┤
│ ACTORS      │ RUSSIA - DETAILED ASSESSMENT    │
│             │                                 │
│ > Russia    │ Category: Adversary             │
│   USA       │ Confidence: Medium              │
│   China     │ Updated: Turn 5                 │
│   France    │                                 │
│             │ === MILITARY POSTURE ===        │
│             │ Aggressive buildup along NATO   │
│             │ borders. 3 divisions moved...   │
│             │                                 │
│             │ === POLITICAL INTENT ===        │
│             │ Seeking to fracture NATO...     │
│             │                                 │
│             │ === LIKELY NEXT MOVES ===       │
│             │ • Escalate hybrid warfare       │
│             │ • Test NATO resolve             │
│             │                                 │
│             │ === VULNERABILITIES ===         │
│             │ • Economic isolation            │
│             │ • Domestic unrest potential     │
└─────────────┴─────────────────────────────────┘
```

**Component Structure:**
```typescript
interface IntelligencePanelProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}
```

**Tasks:**
- [ ] Create split-pane layout (actor list + detail view)
- [ ] Fetch actor list from `/game/{id}/intel`
- [ ] Display actors categorised by ally/neutral/adversary
- [ ] On actor selection, fetch detail from `/game/{id}/intel/{code}`
- [ ] Display assessment in readable sections
- [ ] Show confidence level and last update
- [ ] Add loading state while fetching detail
- [ ] Style with SCUMM panel classes

---

### 7. Frontend - Integration

#### 7.1 Add Intelligence Command Button
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/page.tsx` (CommandBar section)

**Tasks:**
- [ ] Add "INTEL" button to CommandBar
- [ ] Wire to open IntelligencePanel
- [ ] Add keyboard shortcut (Ctrl+I or /intel)

---

#### 7.2 Update Status Button
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/page.tsx` (CommandBar section)

**Tasks:**
- [ ] Ensure STATUS button opens enhanced StatusPanel
- [ ] Fetch vibes/advisors/flags data on panel open
- [ ] Refresh data when panel reopened (in case state changed)

---

### 8. Testing

#### 8.1 Backend API Tests
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `tests/test_deep_state_api.py` (create)

**Test Cases:**
1. **Vibes Endpoint Test**
   - [ ] GET `/game/{id}/state/vibes` returns 200
   - [ ] Response has `vibes` array, `dominant` string, `intensity` number

2. **Advisors Endpoint Test**
   - [ ] GET `/game/{id}/state/advisors` returns 200
   - [ ] Each advisor has `role`, `trust`, `relationship`

3. **Flags Endpoint Test**
   - [ ] GET `/game/{id}/state/flags` returns 200
   - [ ] Response has `active_flags` and `inactive_flags` arrays

4. **Intel List Endpoint Test**
   - [ ] GET `/game/{id}/intel` returns 200
   - [ ] Response has `available_actors` array

5. **Intel Detail Endpoint Test**
   - [ ] GET `/game/{id}/intel/RUS` returns 200
   - [ ] Response has structured `assessment` object

---

#### 8.2 Frontend Integration Test
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Test Protocol:**
1. Open STATUS panel
2. **Verify:** Tabs present (Metrics/Advisors/Flags)
3. Click "Advisors" tab
4. **Verify:** Shows advisor names, trust bars, relationships
5. Click "Flags" tab
6. **Verify:** Shows active flags with severity badges
7. Close STATUS panel
8. Click INTEL button (or press Ctrl+I)
9. **Verify:** Intelligence panel opens
10. **Verify:** Actor list visible
11. Click "Russia"
12. **Verify:** Detailed assessment loads and displays
13. **Verify:** Assessment has all sections (military/political/likely moves/vulnerabilities)

---

### 9. Documentation

#### 9.1 Update API Contracts
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `03_TECHNICAL_SPECS/API_Contracts.md`

**Tasks:**
- [ ] Document `/game/{id}/state/vibes`
- [ ] Document `/game/{id}/state/advisors`
- [ ] Document `/game/{id}/state/flags`
- [ ] Document `/game/{id}/intel`
- [ ] Document `/game/{id}/intel/{actor_code}`

---

#### 9.2 Update Component Library
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `03_TECHNICAL_SPECS/Component_Library.md`

**Tasks:**
- [ ] Document enhanced StatusPanel component
- [ ] Document IntelligencePanel component
- [ ] Add props interfaces and usage examples

---

## Dependencies

**Blocks:**
- Phase 3 (Diplomacy & Meta-Game)

**Blocked By:**
- Phase 1 complete (decision parity established)

**External Dependencies:**
- `narrative_state.py` - vibes and character data
- `intelligence.py` - actor assessments
- `world.py` - flags system

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Intel assessments slow to generate | Medium | Add caching, pre-generate for major actors |
| Trust scores not updating properly | Medium | Verify narrative_state mutation logic |
| Flags not persisting across turns | High | Add flag history tracking in world state |
| UI cluttered with too much data | Medium | Use tabs, collapsible sections, progressive disclosure |

---

## Success Metrics

- **Full diagnostic visibility** matching CLI `/status` depth
- **Intelligence panel** provides actionable strategic insights
- **Trust/relationship tracking** visible and understandable
- **Developer confidence** in state introspection for debugging

---

## Notes

**Why This Matters:**
Deep state visibility transforms the game from "what happened?" to "why did it happen?". Understanding advisor trust and world flags helps players make strategic decisions grounded in narrative context.

**ADHD-Friendly Approach:**
- Backend work (4 endpoints) can be tackled sequentially
- Frontend work (2 panels) can be done in parallel with backend
- Each endpoint has clear input/output contract
- Visual progress: API → UI → Integration → Polish

---

**Previous Phase:** [Phase_1_Decision_Parity.md](Phase_1_Decision_Parity.md)  
**Next Phase:** [Phase_3_Diplomacy_Meta.md](Phase_3_Diplomacy_Meta.md)


