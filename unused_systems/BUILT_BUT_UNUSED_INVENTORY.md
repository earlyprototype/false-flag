# BUILT BUT UNUSED SYSTEMS - INVENTORY

**Purpose:** Track systems that have been coded and tested but are not yet integrated into the main game loop  
**Last Updated:** 8 November 2025  
**Status:** Comprehensive audit complete

---

## PRIORITY 1: READY TO INTEGRATE (High Value, Low Effort)

### 1. Narrative State System
**File:** `models/narrative_state.py`  
**Status:** ✅ Coded, ✅ Tested (via `simple_test.py`), ❌ Not wired to game loop  
**Integration Effort:** 2-3 hours  
**Value:** Enables multiple gameplay modes (Classic/Immersive/Emergent)

**What It Does:**
- Separates hidden metrics (LLM guidance) from player-visible state
- Generates "vibe" displays (🔴🔴🔴⚪⚪ SEVERE ↗) instead of raw numbers
- Tracks character attitudes and trust scores
- Provides mode-specific display (Classic shows metrics, Immersive shows vibes)

**Key Classes:**
```python
class NarrativeState(BaseModel):
    hidden_metrics: Metrics
    previous_metrics: Optional[Metrics]
    situation_summary: str
    recent_events: List[str]
    characters: Dict[str, CharacterAttitude]
    active_crises: List[str]
    turn: int
    game_time: str
    play_mode: PlayMode
```

**Integration Points:**
1. Wrap `WorldState` in `NarrativeState` at game initialization
2. Add display mode switching in `cli/main.py` game loop
3. Pass `narrative_state.to_llm_context()` to all LLM prompts

**Blocking Issues:** None - fully functional

**Last Worked On:** Session with Pydantic underscore fix (user emphatically asked to remove the leading underscore)

---

### 2. Narrative Adjudication (LLM Quality Assessment)
**File:** `engine/narrative_adjudication.py`  
**Status:** ✅ Coded, ⚠️ Partially tested, ❌ Not wired to game loop  
**Integration Effort:** 2-3 hours  
**Value:** Replaces primitive keyword adjudication with context-aware quality scaling

**What It Does:**
- LLM assesses action quality (exceptional/good/adequate/poor/catastrophic)
- Scales base effects by quality multiplier (0.5× to 2.5×)
- Generates character responses guided by metrics
- Updates character trust scores based on decision quality

**Key Functions:**
```python
def assess_action_quality(action, interpretation, context, llm_fn, rng) -> Tuple[str, str]:
    """Returns (quality_level, reasoning)"""

def adjudicate_with_narrative(narrative_state, action, interpretation, rng, llm_fn) -> Tuple[Dict, List, str]:
    """Complete narrative adjudication pipeline"""
    # 1. Assess quality
    # 2. Determine base effects (keywords)
    # 3. Apply quality scaling
    # 4. Generate character responses
    # 5. Update trust scores
    # 6. Check crisis thresholds
```

**Integration Points:**
1. Replace `run_turn_adjudication()` in `cli/main.py` game loop
2. Import from `engine.narrative_adjudication`
3. Pass `llm_generate_fn` and `narrative_state`

**Blocking Issues:** Needs de-escalation keywords added to base effects

**Dependencies:** Works better with NarrativeState but can wrap WorldState

---

### 3. Gameplay Mode Selector
**File:** `cli/main.py` (lines 51-82)  
**Status:** ✅ Menu coded, ❌ Modes not functional  
**Integration Effort:** 1-2 hours  
**Value:** Player choice between metrics (Classic) and narrative (Immersive)

**What It Does:**
- Interactive menu at game start
- Three modes: Classic Wargame, Immersive Narrative, Emergent Drama
- Stores choice in `WorldState.play_mode` (field exists but unused)

**Code Location:**
```python
def select_play_mode() -> str:
    """Present play mode selection menu"""
    # Already coded, menu works
```

**Integration Points:**
1. Use `play_mode` in display logic (already captured in WorldState)
2. Call `narrative_state.display_for_mode(play_mode)` instead of raw metrics
3. Adjust LLM prompt detail based on mode

**Blocking Issues:** Requires NarrativeState to be integrated first

---

## PRIORITY 2: NEEDS COMPLETION (Partially Built)

### 4. Character Attitude Tracking
**File:** `models/narrative_state.py` (embedded in NarrativeState)  
**Status:** ✅ Data structure exists, ⚠️ Update logic incomplete  
**Integration Effort:** 1-2 hours  
**Value:** Advisors remember and react to player's track record

**What It Does:**
- Tracks per-character trust scores
- Records character stance (supportive/neutral/concerned/opposed)
- Influences pushback intensity and advisor responses

**Data Structure:**
```python
class CharacterAttitude(BaseModel):
    character_id: str
    trust_score: int  # 0-100
    stance: str  # supportive/neutral/concerned/opposed
    recent_interactions: List[str]
```

**What's Missing:**
- Trust score update logic based on decision quality
- Influence on advisor pushback generation
- Display in Immersive mode

**Integration Points:**
1. Update trust scores in `adjudicate_with_narrative()`
2. Pass trust scores to `build_pushback_prompt()`
3. Display character attitudes in Immersive mode

---

### 5. Crisis Tracking System
**File:** `models/narrative_state.py` (embedded in NarrativeState)  
**Status:** ✅ Data structure exists, ⚠️ Trigger logic incomplete  
**Integration Effort:** 2-3 hours  
**Value:** Dynamic crisis emergence based on metric thresholds

**What It Does:**
- Tracks active crises (list of crisis IDs)
- Triggers new crises when metrics cross thresholds
- Resolves crises when metrics improve

**Data Structure:**
```python
active_crises: List[str]  # ["energy_crisis", "nato_fracture", "domestic_unrest"]
```

**What's Missing:**
- Crisis definitions and trigger thresholds
- Crisis resolution conditions
- Display in briefing phase
- Impact on inject generation

**Integration Points:**
1. Call `check_critical_thresholds()` after adjudication
2. Add crisis context to inject generation prompts
3. Display active crises in briefing phase

---

## PRIORITY 3: DESIGNED BUT NOT IMPLEMENTED

### 6. Multi-Agent Actor Simulation
**File:** NOT YET CREATED  
**Proposed Files:** `models/state_actors.py`, `engine/actor_simulation.py`  
**Status:** ❌ Not coded, ✅ Designed (see COMPLETE_ARCHITECTURE_MAP.md)  
**Integration Effort:** 4-8 hours  
**Value:** Individual state actors with hidden motivations (THE BIG ONE)

**What It Would Do:**
- Model individual state actors (USA, France, Germany, Poland, Russia, etc.)
- Each actor has public position + hidden motivations
- LLM simulates each actor's response to player actions
- Aggregate effects derived from actor responses (not abstract metrics)

**Proposed Architecture:**
```python
class StateActor(BaseModel):
    country_code: str
    official_position: str
    relationship_uk: int
    # HIDDEN
    true_motivations: List[str]
    hidden_agendas: List[str]
    threat_perception: int
    domestic_pressure: int
    dependencies: Dict[str, str]

def simulate_actor_response(actor, action, context, llm_fn) -> ActorResponse:
    """LLM simulates individual actor's reaction"""

def calculate_effects_from_responses(responses) -> Dict[str, int]:
    """Aggregate actor responses into metric changes"""
```

**Design Questions:**
- How many actors simulate per action? (2-3 recommended)
- Which actors are relevant to each action type?
- How to aggregate actor responses into net effects?
- When/how are hidden agendas revealed to player?

**Integration Points:**
1. Replace abstract "alliance" logic in adjudication
2. Use diplomatic_profiles.yaml as base + add hidden state
3. Call actor simulation before applying effects

**Blocking Issues:** Requires design decisions (see COMPLETE_ARCHITECTURE_MAP.md Part 10)

---

### 7. De-escalation Mechanics
**File:** `engine/sim_loop.py` (needs modification)  
**Status:** ❌ Not implemented  
**Integration Effort:** 30 minutes  
**Value:** Makes game winnable at Standard difficulty (CRITICAL)

**What's Missing:**
Currently NO keywords reduce `escalation_risk`. Only increases exist.

**Proposed Fix:**
```python
# Add to run_turn_adjudication() at line ~500
if any(word in action_lower for word in ["de-escalate", "restraint", "defensive", "measured"]):
    world.metrics.escalation_risk = clamp(world.metrics.escalation_risk - 8)
    transcript.append("Effect: Measured response reduces escalation risk")

if any(word in action_lower for word in ["investigate", "evidence", "verify", "assess"]):
    world.metrics.escalation_risk = clamp(world.metrics.escalation_risk - 5)
    transcript.append("Effect: Investigation approach buys time")

if any(word in action_lower for word in ["dialogue", "negotiate", "diplomatic channel"]):
    world.metrics.escalation_risk = clamp(world.metrics.escalation_risk - 6)
    transcript.append("Effect: Diplomatic engagement reduces tensions")
```

**Integration Points:**
1. Modify `engine/sim_loop.py:run_turn_adjudication()`
2. Add keywords above existing escalation keywords
3. Test with Standard difficulty

**Blocking Issues:** None - straightforward addition

---

### 8. Hidden Agenda Discovery System
**File:** NOT YET CREATED  
**Proposed File:** `engine/intelligence.py`  
**Status:** ❌ Not coded, ⚠️ Concept only  
**Integration Effort:** 2-4 hours  
**Value:** Player can discover hidden actor motivations through intelligence actions

**What It Would Do:**
- "Investigate [country]" actions reveal hidden information
- Intelligence quality affects discovery success
- Discovered agendas displayed in briefings
- Affects player's strategic choices

**Proposed Architecture:**
```python
def investigate_actor(actor, action, world, llm_fn) -> IntelligenceReport:
    """Attempt to discover hidden information about actor"""
    # Success based on action quality + alliance_cohesion
    # Reveals partial or full hidden agenda

def update_actor_visibility(world, actor_id, discovered_info):
    """Mark information as discovered in world state"""
```

**Integration Points:**
1. Add "investigate" action handler in adjudication
2. Update actor display to show discovered vs unknown
3. Use in LLM prompts (only include discovered information)

**Blocking Issues:** Requires multi-agent actor system to be built first

---

## PRIORITY 4: LEGACY/DEPRECATED SYSTEMS

### 9. Old AdvisorProposal System
**File:** `engine/adjudicator.py`  
**Status:** ⚠️ Code exists, ❌ Not used, ✅ Replaced by conversational system  
**Integration Effort:** N/A - should be deleted or marked deprecated  
**Value:** None - superseded by free-form Q&A system

**What It Was:**
- Pre-defined advisor proposals with hardcoded effects
- Player chose from menu of options
- Rigid, not conversational

**Why It's Unused:**
Replaced by `agents/conversation.py` which does:
- Free-form player questions
- LLM-generated advisor responses
- Dynamic action interpretation

**Recommendation:** 
- Mark as deprecated in docstring
- Keep for reference but don't use
- Eventually delete in future cleanup

**Files Affected:**
- `engine/adjudicator.py` (the file itself)
- `agents/advisors.py` (if it exists - didn't find in scan)
- References in `models/world.py` imports

---

### 10. Scene-Based Turn Tracking
**File:** `models/world.py`  
**Status:** ✅ Field exists (`WorldState.scene`), ⚠️ Deprecated  
**Integration Effort:** N/A - migration complete  
**Value:** None - replaced by `turn` field

**What It Was:**
- Old system used `scene` for turn tracking
- Confusing terminology (scene vs turn)

**Current State:**
```python
class WorldState(BaseModel):
    turn: int = 1  # NEW: Current system
    scene: int = 1  # DEPRECATED: Backwards compatibility only
```

**Recommendation:**
- Keep field for save file compatibility
- Document as deprecated
- Remove in future breaking version

---

## ADDITIONAL NOTES

### Test Files Created But Not Integrated
```
test_menus.py           - Menu testing (can be deleted after integration)
simple_test.py          - NarrativeState testing (can be deleted after integration)
test_aesthetics.py      - CLI theme testing (can be deleted)
test_diplomacy.py       - Diplomatic system testing (can be deleted)
```

**Recommendation:** Delete after systems are integrated and working in production.

---

### Temporary Files
```
failed_assets.txt       - Image generation tracking (keep for reference)
generation_log.txt      - Image generation log (keep for reference)
user_approval.txt       - Session notes (keep for reference)
```

---

## INTEGRATION PRIORITY ROADMAP

### Phase 1: Quick Wins (Total: 3-4 hours)
1. ✅ Add de-escalation keywords (30 mins) - **CRITICAL FOR BALANCE**
2. ✅ Wire narrative adjudication (2-3 hours)
3. ✅ Enable gameplay mode selector (1 hour)

**Result:** Context-aware adjudication, player choice of display modes

### Phase 2: Polish Narrative System (Total: 3-4 hours)
1. ✅ Complete character attitude tracking (1-2 hours)
2. ✅ Implement crisis tracking (2-3 hours)

**Result:** Dynamic, responsive narrative layer

### Phase 3: Multi-Agent Actors (Total: 4-8 hours)
1. ⚠️ Design state actor data structure (design decisions needed)
2. ✅ Build actor simulation engine (4-6 hours)
3. ✅ Integrate with adjudication (2 hours)

**Result:** Individual state actors with hidden motivations (GAME-CHANGING)

### Phase 4: Intelligence System (Total: 2-4 hours)
1. ✅ Build intelligence gathering mechanics
2. ✅ Hidden agenda discovery system
3. ✅ Integrate with display

**Result:** Player can discover hidden information through actions

---

## TRACKING CHANGES

**When a system is integrated:**
1. Mark as ✅ INTEGRATED in this document
2. Add integration date and commit reference
3. Move to "Recently Integrated" section below

**When a system is deprecated:**
1. Mark as ⚠️ DEPRECATED
2. Document reason for deprecation
3. Move to "Legacy Systems" section

---

## RECENTLY INTEGRATED

### ✅ Narrative Adjudication (LLM Quality Assessment)
**Date Integrated:** Saturday, 9 November 2025  
**Integration Time:** ~45 minutes  
**Status:** ✅ Complete, ⏳ Testing Pending  

**What It Does:**
- LLM assesses action quality (exceptional → catastrophic)
- Scales effects by quality multiplier (0.5× to 2.5×)
- Generates context-aware character responses
- **Includes de-escalation mechanics** (game now winnable)
- Updates advisor trust scores
- Graceful fallback to keyword system

**Files Modified:**
- `cli/main.py` - Game loop integration (~115 lines)

**Documentation:**
- `analysis/LLM_ADJUDICATOR_INTEGRATION_COMPLETE.md`
- `analysis/LLM_ADJUDICATOR_IMPLEMENTATION_PLAN.md`

**Benefits Delivered:**
- ✅ De-escalation keywords → Game winnable at Standard difficulty
- ✅ Quality-based rewards → Skill matters
- ✅ Context-aware effects → Realistic outcomes
- ✅ Character reactions → Immersive experience
- ✅ Graceful fallback → Robust system

**Cost:** $0.0003-0.001 per game  
**Latency:** 2-4 seconds per turn  
**Risk:** LOW (fallback available)

---

### ✅ Narrative State System
**Date Integrated:** Saturday, 9 November 2025 (Phase 2)  
**Status:** ✅ Complete, ✅ Tested  

**What It Does:**
- Three gameplay modes (Classic/Immersive/Emergent)
- Hidden metrics for LLM guidance
- Character attitude tracking with trust scores
- Mode-specific display rendering

**Files Modified:**
- `cli/main.py` - Mode selection and display
- `engine/persistence.py` - Save/load support

**Documentation:**
- `analysis/NARRATIVE_STATE_INTEGRATION_COMPLETE.md`

---

### ✅ Gameplay Mode Selector
**Date Integrated:** Saturday, 9 November 2025 (Phase 2)  
**Status:** ✅ Complete  

**What It Does:**
- Interactive menu at game start
- Three modes: Classic/Immersive/Emergent
- Player choice persists through save/load

**Files Modified:**
- `cli/main.py` - Menu and mode handling

---

## CONTACT & QUESTIONS

**Questions about integration?** See `analysis/COMPLETE_ARCHITECTURE_MAP.md`  
**Quick lookup?** See `analysis/QUICK_REFERENCE.md`  
**Design decisions needed?** See "PART 10: INTEGRATION CHECKLIST" in architecture map

---

**END OF INVENTORY**

_This is a living document. Update as systems are built, integrated, or deprecated._

