# Phase 1: Decision Loop Parity
**Status:** PENDING (blocked by Phase 0)  
**Goal:** Web App matches CLI's decision discipline  
**Estimated Duration:** 2-3 weeks  

---

## Overview

The CLI has a sophisticated two-step decision process:
1. **Interpret → Pushback** - AI analyses your decision, advisors raise critical concerns
2. **Confirm/Modify/Override → Adjudicate** - You choose how to proceed

Currently the Web UI skips step 1 entirely, going straight to adjudication. This phase brings full parity with CLI decision workflow.

---

## Exit Criteria

- [ ] API endpoint `/game/decision/interpret` implemented and tested
- [ ] API endpoint `/game/decision/commit` implemented and tested
- [ ] Web UI Decision Review dialog functional
- [ ] All decision options work: Apply/Modify/Ignore/Discuss
- [ ] CLI decision behaviour unchanged (reference implementation)
- [ ] Web decision behaviour matches CLI semantically

---

## Task Breakdown

### 1. Backend API Changes

#### 1.1 Create `/decision/interpret` Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)
- `engine/game_manager.py` (extract interpretation logic)

**Current CLI Flow (in `run_turn_decision`):**
```python
# Step 1: Interpret
interpretation = interpret_decision(action_text)
# Step 2: Critical concerns
critical_concerns = gather_critical_concerns(interpretation)
# Step 3: User choice (A/S/M/I/D)
# Step 4: Adjudicate (only if user proceeds)
```

**Required API Endpoint:**
```
POST /game/decision/interpret
Body: { "session_id": str, "action_text": str }
Response: {
  "interpretation": {
    "summary": str,
    "forces_involved": [str],
    "timeline": str,
    "estimated_risk": str
  },
  "critical_concerns": [
    {
      "role": str,  # "NSA", "CDS", etc.
      "concern": str,
      "recommendation": str
    }
  ]
}
```

**Tasks:**
- [ ] Extract interpretation logic from `cli/main.py` into `engine/` layer
- [ ] Create `GameManager.interpret_decision(action_text)` method
- [ ] Call LLM for interpretation (use existing prompt)
- [ ] Parse interpretation into structured format (`parse_interpretation_simple`)
- [ ] Gather critical concerns from advisors
- [ ] Return JSON structure above
- [ ] Add unit test

---

#### 1.2 Create `/decision/commit` Endpoint
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (new endpoint)

**Current CLI Flow:**
After user confirms/overrides, CLI calls adjudication logic.

**Required API Endpoint:**
```
POST /game/decision/commit
Body: {
  "session_id": str,
  "action_text": str,  # Original or modified
  "user_choice": "confirm" | "override" | "apply_recommendations"
}
Response: { "status": "processed" }  # SSE streams adjudication
```

**SSE Stream Events:**
- `reasoning` - thinking steps
- `inject` - narrative injects
- `state_update` - metrics changes, phase transition

**Tasks:**
- [ ] Implement endpoint using existing adjudication logic
- [ ] Log user choice (confirm/override) for narrative context
- [ ] Stream adjudication via SSE (same as current `/game/decision`)
- [ ] Update turn phase after adjudication
- [ ] Add unit test

---

#### 1.3 Legacy Endpoint Deprecation
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `api/server.py` (existing `POST /game/decision`)

**Tasks:**
- [ ] Keep current `/game/decision` for backward compatibility
- [ ] Add deprecation warning in logs
- [ ] Update API documentation: recommend `/decision/interpret` + `/decision/commit`

---

### 2. Frontend Changes

#### 2.1 Create Decision Review Dialog Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/panels/DecisionReviewDialog.tsx` (create)
- `frontend/app/page.tsx` (integrate)

**UI Layout:**
```
┌─────────────────────────────────────────────┐
│ DECISION REVIEW                             │
├─────────────────────────────────────────────┤
│ Your Decision:                              │
│ "Deploy carrier strike group to Baltic..."│
│                                             │
│ Operational Summary:                        │
│ - Forces: HMS Queen Elizabeth CSG           │
│ - Timeline: 24-48 hours deployment          │
│ - Estimated Risk: Moderate escalation      │
│                                             │
│ ⚠ CRITICAL CONCERNS (2)                    │
│                                             │
│ [CDS] Concern: Insufficient air cover...   │
│       Recommendation: Deploy additional... │
│                                             │
│ [NSA] Concern: Risk of Russian sub contact│
│       Recommendation: Increase ASW assets  │
│                                             │
│ ┌─────────────────────────────────────────┐│
│ │ [A] Apply All Recommendations          ││
│ │ [M] Modify Decision Manually           ││
│ │ [I] Ignore Concerns and Proceed        ││
│ │ [D] Return to Discussion                ││
│ └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

**Component Props:**
```typescript
interface DecisionReviewDialogProps {
  isOpen: boolean;
  onClose: () => void;
  decisionText: string;
  interpretation: Interpretation;
  criticalConcerns: CriticalConcern[];
  onApplyRecommendations: () => void;
  onModify: () => void;
  onIgnoreAndProceed: () => void;
  onReturnToDiscussion: () => void;
}
```

**Tasks:**
- [ ] Create component with Shadcn Dialog
- [ ] Style with SCUMM panel classes
- [ ] Display interpretation summary
- [ ] List critical concerns with role badges
- [ ] Implement 4 action buttons with keyboard shortcuts
- [ ] Handle "Apply Recommendations" by modifying decision text
- [ ] Handle "Modify" by returning to decision input
- [ ] Handle "Ignore" by proceeding to commit
- [ ] Handle "Return" by switching phase back to discussion

---

#### 2.2 Update Decision Input Flow
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/page.tsx` (decision submission logic)
- `frontend/components/input/DecisionInput.tsx` (if exists)

**Current Flow:**
```
User types decision → Click EXECUTE → POST /game/decision → Done
```

**New Flow:**
```
User types decision 
  → Click EXECUTE 
  → POST /game/decision/interpret
  → Show Decision Review Dialog
  → User chooses action:
     - Apply: Modify decision text, call /decision/commit
     - Modify: Close dialog, let user edit
     - Ignore: Call /decision/commit with original text
     - Discuss: Switch phase back to DISCUSSION
```

**Tasks:**
- [ ] Replace `/game/decision` call with `/decision/interpret`
- [ ] Open Decision Review Dialog on interpret response
- [ ] Store interpretation and concerns in state
- [ ] Implement "Apply Recommendations" logic:
  - Append advisor recommendations to decision text
  - Call `/decision/commit` with modified text
- [ ] Implement "Ignore and Proceed":
  - Call `/decision/commit` with original text, choice: "override"
- [ ] Implement "Return to Discussion":
  - Switch UI phase back to DISCUSSION
  - Clear decision input

---

### 3. Testing

#### 3.1 Backend Unit Tests
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `tests/test_decision_parity.py` (create)

**Test Cases:**
1. **Interpret Decision Test**
   - [ ] Call `GameManager.interpret_decision("Deploy forces to Estonia")`
   - [ ] Assert returns interpretation dict with summary, forces, timeline
   - [ ] Assert returns critical_concerns array

2. **API Interpret Endpoint Test**
   - [ ] POST `/game/decision/interpret` with sample decision
   - [ ] Assert 200 status
   - [ ] Assert response has `interpretation` and `critical_concerns`

3. **API Commit Endpoint Test**
   - [ ] POST `/game/decision/commit` with choice: "confirm"
   - [ ] Assert 200 status
   - [ ] Assert SSE stream emits state_update event
   - [ ] Assert game phase advances

---

#### 3.2 Frontend Integration Test
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Manual Test Protocol:**
1. Start game session, reach DECISION phase
2. Enter decision: "Send diplomatic protest to Russia"
3. Click EXECUTE
4. **Verify:** Decision Review Dialog opens
5. **Verify:** Shows interpretation summary
6. **Verify:** Shows critical concerns (if any)
7. **Test "Apply Recommendations":**
   - Click [A] button
   - Verify decision text updated
   - Verify commit call made
   - Verify adjudication starts
8. **Test "Modify":**
   - Click [M] button
   - Verify dialog closes
   - Verify can edit decision text
9. **Test "Ignore":**
   - Click [I] button
   - Verify commit call made with original text
   - Verify adjudication starts
10. **Test "Return to Discussion":**
    - Click [D] button
    - Verify phase switches back to DISCUSSION
    - Verify can ask questions again

---

#### 3.3 CLI Behavioural Reference Test
**Owner:** QA  
**Status:** ⏸ PENDING  

**Goal:** Ensure Web behaviour semantically matches CLI

**Test Protocol:**
1. Run CLI version: `python -m cli.main play`
2. Reach decision phase
3. Enter same decision as Web test
4. **Document CLI behaviour:**
   - What interpretation is shown?
   - What critical concerns appear?
   - What happens when you choose (A)?
   - What happens when you choose (M)?
   - What happens when you choose (I)?
5. Compare with Web UI behaviour step-by-step
6. Document any semantic differences

**Acceptance:** Web behaviour matches CLI intent, even if UI differs.

---

### 4. Documentation

#### 4.1 Update API Contracts
**Owner:** Backend  
**Status:** ⏸ PENDING  
**Files:**
- `03_TECHNICAL_SPECS/API_Contracts.md`

**Tasks:**
- [ ] Add `/game/decision/interpret` contract
- [ ] Add `/game/decision/commit` contract
- [ ] Mark `/game/decision` as legacy
- [ ] Provide example request/response JSON

---

#### 4.2 Update Component Library Docs
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `03_TECHNICAL_SPECS/Component_Library.md`

**Tasks:**
- [ ] Document `DecisionReviewDialog.tsx` component
- [ ] Add props interface
- [ ] Add usage example
- [ ] Add styling notes (SCUMM classes)

---

## Dependencies

**Blocks:**
- Phase 2 (Deep State & Intel)

**Blocked By:**
- Phase 0 complete (API contracts stable)

**External Dependencies:**
- Existing interpretation logic in CLI (reference)
- LLM API for decision interpretation

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Interpretation parsing fails for complex decisions | High | Extensive prompt engineering, fallback to simple parse |
| Critical concerns sometimes empty (no advisor pushback) | Medium | Handle empty array gracefully in UI, show "No concerns" |
| "Apply Recommendations" produces malformed decision text | Medium | Test with various recommendation formats, validate output |
| Backend changes break existing Web UI | High | Keep legacy endpoint, test both paths |

---

## Success Metrics

- **Web decision flow** includes interpretation and pushback step
- **Zero semantic differences** between CLI and Web decision handling
- **User can modify** decisions based on advisor feedback
- **Developer confidence** in decision API for future features

---

## Notes

**Why This Matters:**
The decision loop is the heart of the game. Skipping the interpretation/pushback step removes a critical layer of strategic thinking. This phase restores that depth to the Web UI.

**ADHD-Friendly Approach:**
- Split backend and frontend work (parallel streams)
- Each stream has 2-3 discrete tasks
- Clear testing checkpoints after each task
- Visual progress: Dialog mockup → API → Integration → Polish

---

**Previous Phase:** [Phase_0_Stabilisation.md](Phase_0_Stabilisation.md)  
**Next Phase:** [Phase_2_Deep_State_Intel.md](Phase_2_Deep_State_Intel.md)


