# Current Sprint
**Week of:** 23-29 November 2025  
**Phase:** 1 - Decision Loop Parity  
**Sprint Goal:** Align Web App decision logic with CLI discipline (Interpret → Commit)

---

## Active Tasks

### Backend

#### 🏗 IN_PROGRESS: Implement Decision Endpoints
**Owner:** Backend  
**Target Date:** 24 Nov 2025  
**Files:** `api/server.py`, `engine/game_manager.py`

**Deliverable:**
- `POST /game/decision/interpret` returns interpretation + critical concerns
- `POST /game/decision/commit` executes final adjudication
- Legacy `/game/decision` preserved for compatibility

**Progress:**
- [ ] Split `GameManager.commit_decision` logic
- [ ] Create new API routes
- [ ] Verify response shapes

---

### Frontend

#### ⏸ PENDING: Decision Review Dialog
**Owner:** Frontend  
**Target Date:** 25 Nov 2025  
**Files:** `frontend/components/DecisionReviewDialog.tsx` (new), `frontend/app/page.tsx`

**Deliverable:**
- Modal dialog showing:
  - "Your Decision" text
  - Interpretation summary
  - Critical concerns list (with Apply/Modify buttons)
  - "EXECUTE ORDER" button (calls commit)

**Progress:**
- [ ] Create component structure
- [ ] Wire up API calls
- [ ] Handle "Modify" (return to input)
- [ ] Handle "Commit" (proceed to turn resolution)

---

### QA & Testing

#### ⏸ PENDING: Phase 1 Smoke Tests
**Owner:** QA  
**Target Date:** 26 Nov 2025  
**Files:** `api/test_client.py`

**Deliverable:**
- Tests for `/decision/interpret` (verify structure)
- Tests for `/decision/commit` (verify turn advance)

**Progress:**
- [ ] Add Interpret test case
- [ ] Add Commit test case

---

## Completed This Sprint
- **Phase 0 Stabilisation:** Successfully hardened API contracts and frontend data handling. All smoke tests passed.

---

## Blockers
_None currently_

---

## Next Sprint Preview
**Phase 2 Planning:** Deep State & Intel exposure (Vibes, Trust, Dossiers).
