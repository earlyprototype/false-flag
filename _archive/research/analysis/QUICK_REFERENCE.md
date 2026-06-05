# QUICK REFERENCE - Architecture Summary

**For:** Fast lookup when user returns  
**See:** COMPLETE_ARCHITECTURE_MAP.md for full details

---

## WHAT'S RUNNING TODAY

✅ **4-Phase Turn Loop:** Briefing → Discussion → Decision → Adjudication  
✅ **LLM Advisors:** Free-form Q&A (no hardcoded proposals)  
✅ **Diplomatic System:** 7 countries, access levels, LLM personalities  
✅ **Difficulty Scaling:** 0.5×/0.7×/1.0× multipliers on scenario effects  
✅ **Rich CLI:** Colored output, tables, panels, spinners  
✅ **Save/Load:** JSON persistence with auto-save  
✅ **Stochastic Injects:** LLM-generated events after scripted turns  

---

## WHAT'S INTEGRATED

✅ **Narrative State** (`models/narrative_state.py`) - Fully integrated (Phase 2)  
✅ **Gameplay Modes** - Classic/Immersive/Emergent fully functional (Phase 2)  
✅ **Character Attitudes** - Trust tracking, relationship display (Phase 2)  
✅ **Save/Load** - Play mode and narrative state persist (Phase 2)  
✅ **Two-Mode Selection** - Original Story Mode / Mystery Mode (Phase 2C)  
✅ **Narrative Config** - Stored in WorldState.narrative (Team 2)  
✅ **LLM Adjudication** (`engine/narrative_adjudication.py`) - Quality assessment (Phase 3)  
✅ **Dynamic Effects** - Effect scaling based on decision quality (Phase 3)  
✅ **Character Reactions** - Advisor responses to player decisions (Phase 3)  

## WHAT'S READY FOR TEAM 2 COORDINATION

⏭️ **context_builder.py Implementation** - Team 2's orchestration layer  
⏭️ **Narrative-Influenced AI** - Wire secret truth into advisor/diplomatic responses  

**Note:** Team 2 confirmed Orchestrator/Formatter pattern - `context_builder` will call 
`NarrativeState.to_llm_context()` and `NarrativeConfig.to_llm_context()` when implemented.  

---

## WHAT'S MISSING

❌ **De-escalation Keywords** - No way to reduce escalation_risk (game unwinnable)  
❌ **Multi-Agent Actors** - Individual state actors with hidden motivations  
❌ **Hidden Agendas** - Secret motivations affecting outcomes  

---

## CURRENT ADJUDICATION (ADVANCED)

**Location:** `cli/main.py` calls `engine/narrative_adjudication.py:adjudicate_with_narrative()`

**How it works:**
```python
# LLM-driven quality assessment
1. Assess action quality (1-10 scale)
2. Generate reasoning explanation
3. Calculate dynamic effects (scaled by quality)
4. Generate character reactions
5. Update narrative_state.hidden_metrics
6. Display: Assessment → Effects → Reactions

# Fallback to keywords if LLM fails:
run_turn_adjudication_fallback() (primitive system at engine/sim_loop.py:463)
```

**Features:**
- ✅ Quality assessment with reasoning
- ✅ Dynamic effect scaling
- ✅ Context-aware decisions
- ✅ Character personality-driven reactions
- ✅ Graceful degradation on failure

---

## KEY DATA STRUCTURES

### WorldState (Current, Running)
```python
turn: int
phase: Phase  # briefing|discussion|decision|adjudication
difficulty: str  # standard|challenging|brutal
metrics: Metrics  # risk, stability, cohesion, casualties
flags: Dict[str, bool]
diplomatic_relationships: Dict[str, int]
```

### Metrics
```python
escalation_risk: int  # 0-100, ≥85 = war
domestic_stability: int  # 0-100, <30 = collapse
alliance_cohesion: int  # 0-100, <25 = fragmentation
casualties_mil: int
casualties_civ: int
```

### NarrativeState (Built, Not Wired)
```python
hidden_metrics: Metrics  # LLM guidance
characters: Dict[str, CharacterAttitude]  # Trust scores
active_crises: List[str]
play_mode: PlayMode  # classic|immersive|emergent

# Methods
get_situation_vibes() → List[VibeLevel]  # 🔴🔴🔴⚪⚪
to_llm_context() → str  # For LLM prompts
display_for_mode() → List[str]  # Mode-specific display
```

---

## LLM USAGE (Current)

**Provider:** Gemini 2.5 Flash (or mock for testing)  
**Router:** `llm/router.py` - provider-agnostic interface  

**Calls Per Turn:**
- Discussion Q&A: 2-5 calls
- Decision interpretation: 1 call
- Advisor pushback: 1 call
- Critical omissions: 1 call
- Diplomatic encounters: 5-11 calls (if used)
- **Total: ~10-20 calls/turn**

---

## DIPLOMATIC SYSTEM

**7 Countries:** USA, France, Germany, Poland, Russia, Ukraine, Ireland

**Access Levels (by alliance_cohesion):**
- USA: Leader ≥60, Diplomat ≥30
- France: Leader ≥50, Diplomat ≥25
- Germany: Leader ≥55, Diplomat ≥30
- Poland: Leader ≥45, Diplomat ≥20
- Russia: Always diplomat (hostile)

**Mechanics:**
- LLM-driven conversation (max 11 exchanges)
- Personality profiles in `data/diplomatic_profiles.yaml`
- Outcome assessment affects alliance_cohesion
- Updates diplomatic_relationships dict

---

## DIFFICULTY SYSTEM

**Multipliers (on scenario effects only):**
- Standard: 0.5× (winnable with de-escalation mechanics)
- Challenging: 0.7× (tight margins)
- Brutal: 1.0× (currently unwinnable)

**Location:** `engine/sim_loop.py:apply_inject_effects()`

**Casualties NOT scaled** (always full impact)

---

## FILE QUICK MAP

### Must Know
```
cli/main.py                    - Main game loop
engine/sim_loop.py             - Turn phases (CURRENT adjudication here)
agents/conversation.py         - Advisor Q&A, interpretation, pushback
engine/diplomacy.py            - Diplomatic encounters
models/world.py                - WorldState, Metrics
```

### Ready to Integrate
```
models/narrative_state.py          - Hidden metrics system
engine/narrative_adjudication.py   - LLM quality assessment
```

### Data
```
data/scenarios/war_game_2025/initial_conditions.yaml  - Start state
data/scenarios/war_game_2025/scenarios.yaml           - Difficulty config
data/scenarios/war_game_2025/episodes/turn_*.yaml    - Turn injects
data/diplomatic_profiles.yaml                         - Country personalities
```

---

## INTEGRATION POINTS FOR ACTOR SIMULATION

### Where to Plug In

**Option A: Replace Current Adjudication**
```
File: engine/sim_loop.py
Function: run_turn_adjudication() (line 463)
Replace with: adjudicate_with_actor_simulation()
```

**Option B: Enhance Narrative Adjudication**
```
File: engine/narrative_adjudication.py
Function: adjudicate_with_narrative()
Add: actor simulation before applying effects
```

### What Needs Building

```
1. models/state_actors.py (NEW)
   - StateActor class with hidden motivations
   - StateActorSystem to manage all actors

2. engine/actor_simulation.py (NEW)
   - simulate_actor_response(actor, action, context)
   - calculate_effects_from_responses(responses)

3. Integration with existing systems
   - Use diplomatic_profiles.yaml as base
   - Add hidden state (agendas, dependencies, redlines)
   - LLM simulates each actor individually
```

---

## RECENT FIXES & INTEGRATIONS

✅ **Phase 1: Inject Display Scene Parser** (9 Nov 2025)
- Fixed scene-setting detection (`scene_setting_end` no longer -1)
- Rich Panel now returns description text for parsing
- Dramatic pacing restored (scene → SPACE → briefing)

✅ **Phase 2: Narrative State Integration** (9 Nov 2025)
- Three gameplay modes now functional (Classic/Immersive/Emergent)
- Vibes display (🔴🔴🔴⚪⚪ SEVERE ↗) in Immersive mode
- Character attitude tracking with trust bars
- Save/load fully functional with backwards compatibility
- Two-mode selection: Original Story Mode / Mystery Mode

✅ **Phase 3: Narrative Adjudication** (8 Nov 2025)
- LLM-driven action quality assessment (1-10 scale)
- Dynamic effect scaling based on decision quality
- Character-specific advisor reactions
- Three-part display: Assessment → Effects → Reactions
- Graceful fallback to keyword system on LLM failure

---

## CRITICAL GAPS

### 1. De-escalation Mechanics ⚠️ PARTIALLY ADDRESSED
**Status:** LLM adjudication now recognizes de-escalation attempts and scales effects appropriately. Keyword fallback still lacks de-escalation.

**Remaining Work:**
```python
# Add to engine/sim_loop.py:run_turn_adjudication_fallback()
if "de-escalate" in action or "restraint" in action:
    escalation_risk -= 8

if "investigate" in action or "evidence" in action:
    escalation_risk -= 5
```

### 2. Multi-Agent Actors (4-8 hours to build)
- Individual state actors with hidden motivations
- Per-actor LLM simulation
- Effects derived from actor responses

### 3. Context Builder (Team 2 - In Progress)
- Wire `world.narrative.to_llm_context()` into advisor responses
- Wire `narrative_state.to_llm_context()` into LLM prompts
- Filter transcript for diplomatic security

---

## ACTOR SIMULATION EXAMPLE

### Current System (Abstract)
```
Action: "Call NATO summit"
Effect: alliance_cohesion +5 (treats NATO as single entity)
```

### Target System (Multi-Actor)
```
Action: "Call NATO summit"

Simulate:
USA → "We need proof first" (trust +2, conditional_support)
France → "Diplomatic channels first" (trust -5, undermining)
Germany → "Energy concerns" (trust +1, hesitant)
Poland → "We stand with UK!" (trust +15, strong_support)

Net Effect:
- Alliance FRACTURED (not unified)
- Only Poland strongly supportive
- France actively undermining
- Evidence: France has hidden agenda
```

---

## NEXT ACTIONS

### For Your Team (Actor System)
1. Design StateActor data structure with hidden fields
2. Define hidden state for 5 core actors (USA/FRA/DEU/POL/RUS)
3. Build simulate_actor_response() LLM pipeline
4. Test actor responses match personalities + hidden agendas

### For Integration (When Team Returns)
1. Wire narrative adjudication to replace keywords
2. Add de-escalation mechanics
3. Connect actor simulation to adjudication
4. Test full pipeline end-to-end

---

## QUESTIONS TO RESOLVE

### Design Decisions Needed

**1. Actor State Storage:**
- Extend diplomatic_profiles.yaml?
- New state_actors.yaml?
- Procedural generation?

**2. Actor Selection:**
- Which actors respond to each action?
- How many per action? (2-3 recommended)
- Priority/relevance scoring?

**3. Effect Aggregation:**
- How to combine actor responses?
- Weighted by influence?
- Simple average/majority?

**4. Player Visibility:**
- Show actor positions?
- Discover hidden agendas through intel?
- Always hidden, inferred from behavior?

---

**SEE COMPLETE_ARCHITECTURE_MAP.MD FOR FULL DETAILS**
