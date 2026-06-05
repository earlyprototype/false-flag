# Phase 0: Stabilisation
**Status:** CURRENT PHASE  
**Goal:** No crashes, predictable API contracts, CLI remains untouched  
**Estimated Duration:** 1-2 weeks  

---

## Overview

Stabilise the existing Web UI without changing CLI or core engine. Make the frontend resilient to missing/malformed data and establish clear API contracts that both CLI and Web can depend on.

**Philosophy:** Fix the foundation before building higher floors.

---

## Exit Criteria

- [ ] All Phase 0 API contracts documented with example JSON
- [ ] `GameManager.get_resources()` returns flat, well-typed structure
- [ ] `GameManager.get_diplomatic_contacts()` returns flat, well-typed structure
- [ ] Frontend handles missing data without crashes
- [ ] Smoke tests pass for all Phase 0 endpoints
- [ ] CLI `python -m cli.main play` works identically to pre-Phase 0

---

## Task Breakdown

### 1. Backend Hardening

#### 1.1 Define API Contract Schemas
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `03_TECHNICAL_SPECS/API_Contracts.md` (already documented in FULL_STACK)

**Deliverables:**
- JSON schema for `POST /game/new`
- JSON schema for `GET /game/{id}/resources`
- JSON schema for `GET /game/{id}/diplomacy/contacts`
- JSON schema for `POST /game/action/call`
- JSON schema for `POST /game/discussion`
- JSON schema for `POST /game/decision`

**Acceptance:**
- All required keys documented
- Optional keys marked with `?`
- Example JSON provided for each endpoint

---

#### 1.2 Standardise Resources Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `engine/game_manager.py` (method: `get_resources()`)
- `api/server.py` (endpoint: `GET /game/{id}/resources`)

**Current Problem:**
- Unclear data shape from `initial_conditions.yaml`
- Frontend crashes on unexpected nesting

**Required Output:**
```json
{
  "forces": [
    {
      "id": "carrier_qe",
      "branch": "Royal Navy",
      "unit_type": "Aircraft Carrier",
      "location": "Mediterranean",
      "status": "Ready",
      "readiness_turns": 0,
      "notes": "Flagship of task force"
    }
  ],
  "stockpiles": [
    {
      "category": "Munitions",
      "name": "Storm Shadow",
      "count": 24,
      "note": "Air-launched cruise missile"
    }
  ]
}
```

**Tasks:**
- [ ] Parse `initial_conditions.yaml` forces section
- [ ] Flatten nested structures
- [ ] Return consistent shape (even if some forces lack fields)
- [ ] Add unit test for `get_resources()`

---

#### 1.3 Standardise Diplomacy Contacts Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `engine/game_manager.py` (method: `get_diplomatic_contacts()`)
- `api/server.py` (endpoint: `GET /game/{id}/diplomacy/contacts`)

**Required Output:**
```json
[
  {
    "country_code": "US",
    "title": "President (direct line)",
    "access_level": "leader",
    "disposition": "Supportive",
    "notes": "Special relationship"
  },
  {
    "country_code": "FR",
    "title": "Foreign Minister",
    "access_level": "foreign_minister",
    "disposition": "Cautious",
    "notes": null
  }
]
```

**Tasks:**
- [ ] Parse diplomatic roster from `initial_conditions.yaml`
- [ ] Map access levels consistently
- [ ] Handle missing disposition/notes gracefully
- [ ] Add unit test for `get_diplomatic_contacts()`

---

### 2. Frontend Hardening

#### 2.1 Defensive Data Handling in page.tsx
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/page.tsx`

**Current Problem:**
- Assumes resources/contacts have specific structure
- Crashes if API returns unexpected shape

**Required Changes:**
- [ ] Add type guards for `resources` data
- [ ] Add type guards for `contacts` data
- [ ] Show fallback UI if data missing: "No resources data available"
- [ ] Show raw JSON dump if data malformed (for debugging)
- [ ] Ensure RESOURCES dialog cannot crash transcript view
- [ ] Ensure DIPLOMACY dialog cannot crash transcript view

**Example Guard:**
```typescript
// Before accessing resources.forces
if (!resources?.forces || !Array.isArray(resources.forces)) {
  return <div>No forces data available</div>;
}
```

---

#### 2.2 Error Boundary Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/ErrorBoundary.tsx` (create)
- `frontend/app/page.tsx` (wrap main UI)

**Tasks:**
- [ ] Create React Error Boundary component
- [ ] Catch rendering errors in dialogs/panels
- [ ] Display user-friendly error message
- [ ] Log error details to console
- [ ] Prevent entire app crash from single component failure

---

### 3. Testing

#### 3.1 Extend Smoke Test Suite
**Owner:** QA  
**Status:** ⏸ PENDING  
**Files:**
- `api/test_client.py`

**Required Tests:**
1. **Session Creation Test**
   - [ ] `POST /game/new` returns 200
   - [ ] Response contains `session_id`, `turn`, `phase`, `metrics`

2. **Resources Test**
   - [ ] `GET /game/{id}/resources` returns 200
   - [ ] Response has `forces` array
   - [ ] Response has `stockpiles` array
   - [ ] Each force has `id` and `branch`
   - [ ] Each stockpile has `category`, `name`, `count`

3. **Diplomacy Contacts Test**
   - [ ] `GET /game/{id}/diplomacy/contacts` returns 200
   - [ ] Response is array
   - [ ] Each contact has `country_code` and `access_level`

4. **Diplomatic Call Test**
   - [ ] `POST /game/action/call` with `{"country_name": "United States"}` returns 200
   - [ ] Response has `status: "processed"`

5. **Discussion Test**
   - [ ] `POST /game/discussion` with sample question returns 200
   - [ ] Response has `status: "processed"`

**Phase 0 Green Check:**
All 5 test categories pass without modification to CLI code.

---

### 4. Validation

#### 4.1 CLI Regression Test
**Owner:** QA  
**Status:** ⏸ PENDING  

**Test Protocol:**
1. Run `python -m cli.main play`
2. Complete full turn: Briefing → Discussion → Decision → Adjudication
3. Verify all commands work: `/status`, `/advise`, `/resources`, `/call`, `/menu`
4. Compare metrics changes with pre-Phase 0 behaviour
5. Document any differences (should be NONE)

**Acceptance:** CLI behaviour identical to before Phase 0 started.

---

#### 4.2 Web UI Smoke Test (Manual)
**Owner:** QA  
**Status:** ⏸ PENDING  

**Test Protocol:**
1. Start API server: `uvicorn api.server:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open `http://localhost:3000`
4. Create new game session
5. Click RESOURCES button - should show forces/stockpiles OR graceful fallback
6. Click DIPLOMACY button - should show contacts OR graceful fallback
7. Ask a discussion question - should receive advisor response
8. Submit a decision - should process without crash

**Acceptance:** No console errors, no UI crashes, data displays correctly or shows fallback.

---

## Dependencies

**Blocks:**
- Phase 1 (cannot proceed until API contracts stable)

**Blocked By:**
- None (Phase 0 is the starting point)

**External Dependencies:**
- `initial_conditions.yaml` structure (must be parseable)
- FastAPI server operational
- Next.js frontend builds successfully

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `initial_conditions.yaml` has inconsistent structure | High | Add schema validation, normalise during parsing |
| Frontend changes break existing functionality | Medium | Comprehensive manual testing before commit |
| API changes require CLI updates | High | Isolate API layer, don't modify engine contracts |
| Smoke tests fail due to env setup | Low | Document test environment requirements |

---

## Success Metrics

- **Zero crashes** in Web UI when navigating all dialogs
- **100% pass rate** on smoke test suite
- **CLI unchanged** (verified by regression test)
- **Developer confidence** in API contracts for Phase 1 work

---

## Notes

**ADHD-Friendly Checklist:**
Breaking Phase 0 into 4 major sections with clear, independent tasks:
1. Backend hardening (can work in parallel with frontend)
2. Frontend hardening (can work in parallel with backend)
3. Testing (requires 1 & 2 complete)
4. Validation (final gate before Phase 1)

Each section has granular tasks with clear acceptance criteria.

---

**Next Phase:** [Phase_1_Decision_Parity.md](Phase_1_Decision_Parity.md)


