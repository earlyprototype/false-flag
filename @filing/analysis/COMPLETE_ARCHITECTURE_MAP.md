# COMPLETE ARCHITECTURE MAP & SYSTEM ANALYSIS

**Generated:** Saturday, 9 November 2025  
**Purpose:** Comprehensive codebase analysis for actor simulation integration  
**Status:** THOROUGH DEEP-DIVE COMPLETE

---

## EXECUTIVE SUMMARY

### What's Actually Running (PRODUCTION)
✅ **Turn-based game loop** with 4 phases (briefing → discussion → decision → adjudication)  
✅ **Primitive keyword-based adjudication** (`run_turn_adjudication` in `sim_loop.py`)  
✅ **LLM-powered advisor conversation** (free-form Q&A, no hardcoded proposals)  
✅ **LLM-powered diplomatic system** (7 countries, access levels, personality-driven)  
✅ **Difficulty scaling** (Standard/Challenging/Brutal - just implemented)  
✅ **Rich CLI with formatted display** (metrics tables, spinners, colored output)  
✅ **Save/load system** with JSON persistence  
✅ **Stochastic inject generation** (LLM-generated events after scripted turns)

### What's Built But Not Wired (READY TO INTEGRATE)
⏭️ **Narrative State System** (`models/narrative_state.py`) - Hidden metrics + vibes  
⏭️ **Narrative Adjudication** (`engine/narrative_adjudication.py`) - LLM quality assessment  
⏭️ **Gameplay Mode Selector** (`cli/main.py`) - Classic/Immersive/Emergent modes  
⏭️ **Character attitude tracking** - Trust scores, relationships, stances

### What's Missing (NEEDS BUILDING)
❌ **Multi-agent actor simulation** - Individual state actors with hidden motivations  
❌ **De-escalation mechanics** - Keywords to reduce escalation risk  
❌ **Actor-specific response generation** - Per-country LLM simulation  
❌ **Hidden agenda system** - Secret motivations that affect outcomes

---

## PART 1: CORE GAME LOOP ARCHITECTURE

### 1.1 Entry Point: `cli/main.py`

**Command Structure:**
```python
.\.venv\Scripts\python.exe -m cli.main play
    --variant [standard|fast_start]
    --difficulty [standard|challenging|brutal]
    --play-mode [classic|immersive|emergent]  # NEW, not yet functional
    --stochastic-injects  # Enabled by default
    --seed 42
```

**Initialization Flow:**
```
1. Display intro sequence (streaming text with [PAUSE] markers)
2. Load initial_conditions.yaml
3. Create WorldState with initial metrics
4. Enter main game loop
```

### 1.2 Turn Structure (4 Phases)

#### **Phase 1: BRIEFING** (`run_turn_briefing`)
```
Location: engine/sim_loop.py:221

Flow:
1. Load inject YAML (turn_NNN.yaml or turn_NNN_fast.yaml)
   - OR generate stochastically if missing (llm/inject_generator.py)
2. Display inject with Rich panels (channel-based coloring)
3. Apply inject effects to metrics (with difficulty multiplier)
4. Handle mandatory diplomatic encounters (if specified in inject)
5. Update flags and world state

Output: inject dict, transcript lines
```

#### **Phase 2: DISCUSSION** (`run_turn_discussion`)
```
Location: engine/sim_loop.py:304

Flow:
1. Player enters discussion mode (free-form Q&A)
2. Commands available:
   - Ask questions → LLM advisor responses (agents/conversation.py)
   - /call [country] → Diplomatic encounter (engine/diplomacy.py)
   - /menu → Show available commands
   - /decide → Move to decision phase
   - /save [name] → Save game state
   - /quit → Exit game

Advisor Routing:
- Keyword matching determines which advisor responds
- NSA coordinates responses
- Multiple advisors can respond to complex questions

Diplomatic System:
- Access level based on alliance_cohesion metric
- Leader vs diplomat determined by thresholds
- LLM-driven conversation (max 11 exchanges)
- Outcome assessment affects alliance_cohesion

Output: Q&A transcript, diplomatic outcomes
```

#### **Phase 3: DECISION** (`run_turn_decision`)
```
Location: engine/sim_loop.py:304

Flow:
1. Player commits to action (free-form text)
2. LLM interprets action (agents/conversation.py:interpret_player_action)
3. LLM generates advisor pushback (agents/conversation.py:generate_advisor_pushback)
4. LLM checks critical omissions (agents/conversation.py:check_critical_omissions)
5. Player confirms or revises

LLM Prompts Used:
- Decision interpretation: Clarify what player intends
- Advisor pushback: Domain-specific concerns
- Critical omissions: High-priority strategic gaps

Output: interpretation, pushback list, critical concerns
```

#### **Phase 4: ADJUDICATION** (`run_turn_adjudication`)
```
Location: engine/sim_loop.py:463

CURRENT IMPLEMENTATION (PRIMITIVE):
- Keyword matching on action text
- Fixed effect magnitudes
- No context awareness
- No quality assessment

Keywords:
- "deploy"/"surge" → escalation_risk +5
- "diplomatic"/"nato"/"alliance" → alliance_cohesion +5
- "public"/"statement"/"reassure" → domestic_stability +3
- "nuclear"/"strike" → escalation_risk +20, alliance_cohesion -30

MISSING:
- De-escalation keywords (escalation_risk -X)
- Quality-based scaling
- Context-aware effects
- Actor-specific responses

Output: Updated world state, transcript
```

### 1.3 Main Game Loop (`cli/main.py:492-1015`)

```python
while True:
    # 1. BRIEFING
    inject, briefing_lines = run_turn_briefing(...)
    display_briefing()
    
    # 2. DISCUSSION (loop until /decide)
    while not player_decided:
        command = get_player_input()
        if command.startswith("/call"):
            run_diplomatic_encounter()
        elif command == "/decide":
            player_decided = True
        else:
            responses = handle_player_question()
            display_responses()
    
    # 3. DECISION
    action = get_player_decision()
    interpretation, pushback, concerns = run_turn_decision(...)
    display_interpretation_and_pushback()
    
    confirmed = get_confirmation()
    if not confirmed:
        continue  # Back to discussion
    
    # 4. ADJUDICATION
    adjudication_transcript = run_turn_adjudication(...)
    
    # 5. DISPLAY RESULTS
    display_metrics_table()  # Rich formatted
    
    # 6. CHECK END CONDITIONS
    if check_game_over():
        display_end_screen()
        break
    
    # 7. ADVANCE TURN
    world.turn += 1
    auto_save()
```

---

## PART 2: DATA STRUCTURES & MODELS

### 2.1 WorldState (`models/world.py`)

```python
class WorldState(BaseModel):
    # Turn tracking
    turn: int = 1
    phase: Phase  # "briefing" | "discussion" | "decision" | "adjudication"
    scene: int = 1  # Legacy, deprecated
    
    # NEW: Difficulty setting
    difficulty: str = "standard"  # "standard" | "challenging" | "brutal"
    
    # Core metrics
    metrics: Metrics  # See below
    
    # Boolean flags (narrative state)
    flags: Dict[str, bool] = {}
    # Example: {"us_commitment": True, "f35_pilots_murdered": True}
    
    # Force postures
    posture: Dict[str, str] = {}
    # Example: {"carrier_readiness": "high", "qra_status": "active"}
    
    # Spatial state (unit locations)
    spatial_state: Dict[str, List[str]] = {}
    # Example: {"Portsmouth": ["HMS_Prince_of_Wales"], "UK_waters": ["Type45_Destroyer_1"]}
    
    # Discussion transcript (current turn only)
    discussion_transcript: List[str] = []
    
    # Diplomatic relationships
    diplomatic_relationships: Dict[str, int] = {}
    # Example: {"USA": 60, "France": 45, "Russia": 5}
```

### 2.2 Metrics (`models/world.py`)

```python
class Metrics(BaseModel):
    escalation_risk: int       # 0-100, threshold 85 = war
    domestic_stability: int    # 0-100, threshold <30 = collapse
    alliance_cohesion: int     # 0-100, threshold <25 = fragmentation
    casualties_mil: int        # Absolute count
    casualties_civ: int        # Absolute count
```

**Critical Thresholds:**
- Escalation Risk ≥ 85: "High risk of war"
- Domestic Stability < 30: "Government collapse risk"
- Alliance Cohesion < 25: "Alliance fragmentation"

**Diplomatic Access Thresholds:**
- USA Leader: ≥60, Diplomat: ≥30
- France Leader: ≥50, Diplomat: ≥25
- Germany Leader: ≥55, Diplomat: ≥30
- Poland Leader: ≥45, Diplomat: ≥20
- Russia: Never leader, always diplomat (ambassador)
- Ukraine Leader: ≥40, Diplomat: ≥15
- Ireland Leader: ≥35, Diplomat: ≥10

### 2.3 NarrativeState (`models/narrative_state.py`) - NOT YET USED

```python
class NarrativeState(BaseModel):
    # Hidden metrics (LLM guidance, not shown to player)
    hidden_metrics: Metrics
    previous_metrics: Optional[Metrics]  # For trend calculation
    
    # Player-visible state
    situation_summary: str
    recent_events: List[str]
    characters: Dict[str, CharacterAttitude]
    active_crises: List[str]
    
    # Metadata
    turn: int
    game_time: str
    play_mode: PlayMode  # "classic" | "immersive" | "emergent"
    
    # Methods
    def get_situation_vibes() -> List[VibeLevel]  # 🔴🔴🔴⚪⚪ display
    def to_llm_context() -> str  # Context string with hidden metrics
    def display_for_mode() -> List[str]  # Mode-specific display
```

### 2.4 Inject Structure (YAML)

```yaml
# Example: turn_001_fast.yaml
id: turn_001_fast_cobra_briefing
title: "COBRA Emergency: Northern Fleet Deployment"
description: |
  Multi-paragraph narrative description.
  
  Can include scene-setting, advisor dialogues, breaking news.
  
  [PAUSE] markers for dramatic pauses.

channel: briefing  # "briefing" | "intel" | "breaking" (affects display color)

effects:
  - metric: escalation_risk
    delta: 10..15  # Range, midpoint used deterministically
  - metric: domestic_stability
    delta: -8..-13
  - metric: alliance_cohesion
    delta: -2..-5

# Optional: Mandatory diplomatic encounter
diplomatic_encounter:
  required: true
  country: "US"
  context: "President demands coordination before any NATO action"
```

---

## PART 3: LLM INTEGRATION ARCHITECTURE

### 3.1 LLM Router (`llm/router.py`)

**Provider System:**
```
Priority 1: WARGAME_LLM env var
Priority 2: config.py LLM_PROVIDER
Priority 3: Default to "mock"

Supported:
- mock: MockDeterministicDriver (for testing)
- offline: OfflineDriver (pre-recorded responses)
- gemini: GeminiDriver (Google Gemini 2.5 Flash)
- openai: Future
- anthropic: Future
```

**Interface:**
```python
def generate_text(prompt: str, rng: Random, show_spinner: bool = True) -> str:
    """Universal LLM generation function"""
    driver = _get_text_driver()
    if show_spinner and driver != "mock":
        with Spinner("Thinking"):
            return driver.generate_text(prompt, rng)
    return driver.generate_text(prompt, rng)
```

### 3.2 LLM Usage Points (CURRENT)

| System | Location | Purpose | Frequency |
|--------|----------|---------|-----------|
| **Advisor Q&A** | `agents/conversation.py` | Answer player questions | Per question |
| **Action Interpretation** | `agents/conversation.py` | Clarify player intent | Per decision |
| **Advisor Pushback** | `agents/conversation.py` | Domain-specific concerns | Per decision |
| **Critical Omissions** | `agents/conversation.py` | Strategic gap detection | Per decision |
| **Diplomatic Conversation** | `engine/diplomacy.py` | Leader/diplomat responses | Per exchange |
| **Diplomatic Outcome** | `engine/diplomacy.py` | Assess conversation result | Per conversation |
| **Stochastic Injects** | `llm/inject_generator.py` | Generate events | After scripted turns |

**Total LLM Calls Per Turn (Typical):**
- Discussion phase: 2-5 questions = 2-5 calls
- Decision phase: 3 calls (interpretation + pushback + omissions)
- Diplomatic calls: 5-11 exchanges = 5-11 calls (if used)
- **Average: ~10-20 calls per turn** (current system)

### 3.3 Prompt Engineering (`llm/prompts.py`)

**Key Prompt Builders:**
```python
def build_advisor_context(world, initial_conditions, advisor_id, question, transcript):
    """Build context for advisor Q&A"""
    # Includes: world state, advisor personality, question, recent history

def build_decision_interpretation_prompt(world, action, transcript):
    """Interpret what player action means"""
    # Includes: world state, action text, context

def build_pushback_prompt(world, action, interpretation, advisor_id):
    """Generate advisor-specific concerns"""
    # Includes: advisor domain, action implications, risk assessment

def build_critical_omissions_prompt(world, action, interpretation):
    """Identify strategic gaps in decision"""
    # Includes: world state, action, what's NOT being addressed
```

**Context Building Strategy:**
```python
def build_conversation_history_context(transcript, max_lines=500):
    """Extract recent transcript for LLM context"""
    # Takes last N lines to fit within token limits
    # Prioritizes recent events and player actions
```

---

## PART 4: EXISTING SYSTEMS DEEP-DIVE

### 4.1 Advisor System (Conversational, No Hardcoded Proposals)

**Architecture:**
```
agents/conversation.py:
- handle_player_question(): Routes question to appropriate advisor
- Keyword matching determines which advisor(s) respond
- Multiple advisors can respond to complex questions
- LLM generates in-character responses

Key Change from Original Design:
❌ OLD: AdvisorProposal system with pre-defined actions
✅ NEW: Free-form conversational Q&A
```

**Advisor Profiles (from initial_conditions.yaml):**
```yaml
characters:
  chief_defence_staff:
    role: "Military Commander"
    influence: 85
    knowledge_domains: ["military_operations", "force_readiness", "threat_assessment"]
    pushback_triggers:
      - "Militarily implausible actions"
      - "Operations beyond UK capability"
      - "Actions that waste limited munitions"
    key_concerns: ["Russian naval exercise", "pilot security", "limited air defence"]
  
  national_security_advisor:
    role: "Intelligence Coordinator"
    influence: 90
    knowledge_domains: ["intelligence_assessment", "cyber_security", "strategic_planning"]
    # ... etc for all 6 advisors
```

### 4.2 Diplomatic System (Fully Functional)

**Architecture:**
```
engine/diplomacy.py:
- load_diplomatic_profiles(): Load from data/diplomatic_profiles.yaml
- check_diplomatic_access(): Determine access level based on alliance_cohesion
- run_diplomatic_encounter(): Execute LLM-driven conversation
- assess_diplomatic_outcome(): LLM evaluates conversation success

Flow:
1. Player types /call [country]
2. System checks access level (leader vs diplomat vs none)
3. Load personality profile from YAML
4. Build conversation prompt with personality + concerns
5. LLM generates counterpart responses
6. Exchange loop (max 11, biased to end at 5-7)
7. LLM assesses outcome → alliance_cohesion delta
8. Update diplomatic_relationships dict
```

**Diplomatic Profiles (data/diplomatic_profiles.yaml):**
```yaml
countries:
  US:
    leader:
      title: "President of the United States"
      access_threshold: 60
      personality: "Direct, transactional, focused on American interests..."
      tone: "informal, direct, occasionally impatient"
      key_concerns:
        - "US commitment to NATO Article 5"
        - "European defence spending"
        - "Avoiding American casualties"
      opening_lines:
        - "Prime Minister, I'm hearing concerning reports. What's your play here?"
        - "We need to talk about what's happening in your backyard."
```

**7 Countries Available:**
1. US (President/NSA)
2. France (President/Foreign Minister)
3. Germany (Chancellor/Foreign Minister)
4. Poland (President/Foreign Minister)
5. Russia (Ambassador only - hostile)
6. Ukraine (President/Foreign Minister)
7. Ireland (Taoiseach/Foreign Minister - in-joke)

### 4.3 Difficulty System (Just Implemented)

**Architecture:**
```
Difficulty levels affect SCENARIO EFFECTS only (not player actions):

data/scenarios/war_game_2025/scenarios.yaml:
difficulties:
  standard:
    multiplier: 0.5
  challenging:
    multiplier: 0.7
  brutal:
    multiplier: 1.0

engine/sim_loop.py:apply_inject_effects():
if metric_name not in ["casualties_civ", "casualties_mil"]:
    delta_value = int(delta_value * difficulty_multiplier)
```

**Effect on Balance:**
- Brutal (1.0×): Currently unwinnable (documented in FAST_MODE_BALANCE_REPORT.md)
- Challenging (0.7×): Still very difficult
- Standard (0.5×): Tight but theoretically winnable (needs de-escalation mechanics)

### 4.4 Save/Load System (`engine/persistence.py`)

**Format:** JSON
**Location:** `saves/` directory
**Auto-save:** After each turn

**Saved State:**
```json
{
  "scenario": "war_game_2025",
  "world": {
    "turn": 3,
    "phase": "briefing",
    "difficulty": "standard",
    "metrics": {...},
    "flags": {...},
    "posture": {...},
    "spatial_state": {...},
    "diplomatic_relationships": {...}
  },
  "transcript": ["...", "..."]
}
```

### 4.5 Stochastic Inject Generation (`llm/inject_generator.py`)

**Activation:**
- Standard variant: Turn 7+
- Fast variant: Turn 4+

**Generation Process:**
```python
def generate_inject(world, turn, initial_conditions, rng, root_path, transcript):
    1. Build context: world state, recent events, crisis trajectory
    2. LLM generates event description + title + effects
    3. Parse LLM response into inject dict structure
    4. Validate effects are in proper format
    5. Return inject dict (used like YAML inject)
```

**Prompting Strategy:**
```
"You are generating the next crisis event for Turn {turn}.
Current state: Risk={risk}, Stability={stability}, Cohesion={cohesion}
Recent events: {events}

Generate a realistic escalation that:
- Builds on previous events
- Challenges player's recent decisions
- Increases tension and complexity
- Provides new strategic dilemmas

Return format:
TITLE: [Brief title]
DESCRIPTION: [Multi-paragraph narrative]
EFFECTS:
escalation_risk: [delta]
domestic_stability: [delta]
alliance_cohesion: [delta]"
```

### 4.6 Rich CLI System (`cli/rich_ui.py`, `cli/theme.py`)

**Features:**
- Colored output (danger/warning/success/muted)
- Formatted tables (metrics display)
- Panels (inject display with channel colors)
- Spinners (during LLM generation)
- Box drawing (consistent borders)

**Theme Configuration:**
```python
COLORS = {
    "danger": "bright_red",
    "warning": "yellow",
    "success": "bright_green",
    "accent": "cyan",
    "muted": "bright_black",
    "prompt": "bright_white"
}
```

---

## PART 5: WHAT'S BUILT BUT NOT WIRED

### 5.1 Narrative State System (`models/narrative_state.py`)

**Status:** ✅ Coded, ✅ Tested, ❌ Not integrated into game loop

**Purpose:**
- Separate hidden metrics (LLM guidance) from player display
- Support multiple play modes (Classic/Immersive/Emergent)
- Track character attitudes and relationships
- Generate "vibe" displays (🔴🔴🔴⚪⚪) instead of raw numbers

**Integration Points:**
```
1. Replace WorldState with NarrativeState in game loop
   OR: Add NarrativeState wrapper around WorldState
   
2. Switch display based on play_mode:
   - Classic: Show raw metrics (current behavior)
   - Immersive: Show vibes + character attitudes
   - Emergent: Show narrative summary only

3. Pass NarrativeState.to_llm_context() to all LLM prompts
   (includes hidden metrics for guidance)
```

### 5.2 Narrative Adjudication (`engine/narrative_adjudication.py`)

**Status:** ✅ Coded, ✅ Tested, ❌ Not integrated into game loop

**Purpose:**
- LLM assesses action quality (exceptional/good/adequate/poor/catastrophic)
- Scale base effects by quality multiplier (0.5× to 2.5×)
- Generate character responses guided by metrics
- Update character trust scores

**Complete Pipeline:**
```python
def adjudicate_with_narrative(narrative_state, action, interpretation, rng, llm_fn):
    1. assess_action_quality() 
       → LLM judges: "exceptional" with reasoning
       
    2. determine_base_effects()
       → Heuristic keywords: {alliance_cohesion: +5, escalation_risk: -5}
       
    3. apply_quality_scaling()
       → Exceptional (2.5×): {alliance_cohesion: +12, escalation_risk: -12}
       
    4. Apply to hidden_metrics
       
    5. generate_character_responses()
       → LLM simulates advisor responses guided by new metrics
       
    6. update_character_attitudes()
       → Exceptional action: all advisors' trust +5
       
    7. check_and_trigger_crises()
       → Metrics crossed threshold? Add crisis to active_crises list
       
    return final_effects, character_responses, reasoning
```

**Integration Point:**
```
Replace engine/sim_loop.py:run_turn_adjudication()
with engine/narrative_adjudication.py:adjudicate_with_narrative()
```

### 5.3 Gameplay Mode Selector (`cli/main.py`)

**Status:** ✅ Menu coded, ❌ Modes not functional yet

**Three Modes:**
```
1. Classic Wargame
   - Visible metrics (Risk: 75/100)
   - Traditional strategy game feel
   - Current experience

2. Immersive Narrative (DEFAULT)
   - Vibes (🔴🔴🔴🔴⚪ SEVERE ↗)
   - Character attitudes
   - Narrative focus

3. Emergent Drama (EXPERIMENTAL)
   - Pure narrative
   - Minimal structure
   - Maximum LLM freedom
```

**Integration:**
```
1. Pass play_mode to NarrativeState initialization
2. Use narrative_state.display_for_mode(play_mode)
3. Route LLM prompts through narrative context
```

---

## PART 6: GAP ANALYSIS - WHAT'S MISSING

### 6.1 De-escalation Mechanics (CRITICAL)

**Problem:**
- Current adjudication has NO WAY to reduce escalation_risk
- Only keywords increase it (+5 for "deploy", +20 for "nuclear")
- Makes Standard difficulty unwinnable

**Solution Required:**
```python
# Add to engine/sim_loop.py:run_turn_adjudication()

if any(word in action_lower for word in ["de-escalate", "restraint", "defensive"]):
    world.metrics.escalation_risk = clamp(world.metrics.escalation_risk - 8)
    transcript.append("Effect: Measured response reduces escalation risk")

if any(word in action_lower for word in ["investigate", "evidence", "verify"]):
    world.metrics.escalation_risk = clamp(world.metrics.escalation_risk - 5)
    transcript.append("Effect: Investigation approach buys time")
```

**Impact:** Makes Standard difficulty winnable with good play

### 6.2 Multi-Agent Actor Simulation (YOUR FOCUS)

**What's Missing:**
Individual state actors with:
```python
class StateActor:
    country_code: str
    official_position: str  # Public
    relationship_uk: int    # Public
    
    # HIDDEN (guides LLM, player doesn't see)
    true_motivations: List[str]
    hidden_agendas: List[str]
    threat_perception: int
    domestic_pressure: int
    dependencies: Dict[str, str]
    redlines: List[str]
```

**Current Limitation:**
```python
# Current: Abstract aggregate
"NATO" → alliance_cohesion +5 (treats NATO as single entity)

# Needed: Individual actors
USA → cautious support (+2 trust, conditional)
France → undermining (-5 trust, hidden agenda)
Germany → hesitant (+1 trust, energy concerns)
Poland → strong support (+15 trust, enthusiastic)
→ Net result: alliance fractured, not unified
```

**Architecture Needed:**
```
1. models/state_actors.py
   - StateActor class
   - StateActorSystem (manages all actors)
   
2. engine/actor_simulation.py
   - simulate_actor_response()
   - calculate_effects_from_responses()
   
3. Integration with narrative_adjudication.py
   - Replace abstract metrics with actor-specific outcomes
```

### 6.3 Hidden Agenda System

**What's Missing:**
- Actors have secret motivations player doesn't know
- France secret Russia backchannel
- Germany energy dependence constraints
- USA domestic politics affecting decisions

**Example:**
```yaml
# In state actor definition (hidden from player)
France:
  public_position: "European solidarity with UK"
  hidden_agendas:
    - secret_russia_backchannel
    - wants_uk_anglosaxon_influence_reduced
    - positioning_as_mediator_not_ally
  
  # Affects LLM responses
  when_player_calls_for_nato_action:
    public: "We must pursue diplomatic channels first"
    private_thinking: "This weakens UK, strengthens French position as mediator"
    actual_effect: trust -5, actively_undermining: true
```

### 6.4 Intelligence System

**Current:**
- Pre-scripted intelligence in initial_conditions.yaml
- No player discovery mechanics
- No uncertainty or fog of war

**Potential Enhancement:**
- Hidden actor agendas discoverable through intelligence gathering
- "Investigate" actions reveal more information
- Intelligence quality affects decision-making

---

## PART 7: INTEGRATION ROADMAP

### Phase 2A: Wire Up Narrative Adjudication (2-3 hours)

**Goal:** Replace primitive keyword adjudication with LLM quality assessment

**Steps:**
```
1. Modify cli/main.py game loop:
   - Import adjudicate_with_narrative
   - Replace run_turn_adjudication() call
   - Pass llm_generate_fn

2. Update display to show quality reasoning
   - Show "Action Quality: EXCEPTIONAL"
   - Show reasoning text
   - Keep metrics display

3. Test with existing scenarios
   - Verify effects scale appropriately
   - Ensure graceful LLM fallback

4. Add de-escalation keywords to heuristics
   - Provides baseline even without LLM
```

**Result:** Context-aware, quality-based adjudication

### Phase 2B: Integrate Narrative State Display (1-2 hours)

**Goal:** Make Immersive mode functional

**Steps:**
```
1. Wrap WorldState in NarrativeState
   - narrative_state.hidden_metrics = world.metrics
   - Initialize characters from initial_conditions

2. Add display mode switching:
   if play_mode == "classic":
       display_metrics_table(world.metrics)
   elif play_mode == "immersive":
       display_vibes(narrative_state.get_situation_vibes())
       display_character_attitudes(narrative_state.characters)

3. Update LLM prompts:
   - Use narrative_state.to_llm_context()
   - Includes hidden metrics for guidance
```

**Result:** Players can choose Classic (numbers) or Immersive (vibes)

### Phase 3: Multi-Agent Actor Simulation (4-8 hours)

**Goal:** Individual state actors with hidden motivations

**Steps:**
```
1. Create models/state_actors.py (NEW FILE)
   - StateActor class
   - StateActorSystem class
   - Initialize from diplomatic_profiles.yaml + hidden state

2. Create engine/actor_simulation.py (NEW FILE)
   - simulate_actor_response(actor, action, context, llm_fn)
   - calculate_effects_from_responses(responses, world)
   - identify_relevant_actors(action)

3. Integrate with narrative_adjudication.py:
   - After quality assessment
   - Before applying effects
   - Simulate 2-3 relevant actors
   - Derive effects from their actual responses

4. Update diplomatic system:
   - Use actor's hidden state in prompts
   - Track actor responses affect their hidden state
   - Hidden agendas influence future interactions
```

**Result:** Realistic multi-actor geopolitics with hidden motivations

### Phase 4: Intelligence & Discovery (Future)

**Goal:** Player can discover hidden information

**Steps:**
```
1. Add intelligence gathering actions
   - "Investigate French position"
   - "Request CIA assessment of European unity"

2. Reveal hidden information based on actions
   - High-quality intelligence actions reveal hidden agendas
   - Poor actions miss key information

3. Update UI to show discovered vs unknown
   - "France: Position unclear (investigate to learn more)"
   - "France: SECRET AGENDA DISCOVERED - Russia backchannel"
```

---

## PART 8: CURRENT vs DESIGNED SYSTEMS COMPARISON

### What's Actually Running vs What We Designed

| System | Production Status | Design Status | Integration Effort |
|--------|------------------|---------------|-------------------|
| **Turn Loop** | ✅ Running | ✅ Complete | N/A |
| **Advisor Q&A** | ✅ Running | ✅ Complete | N/A |
| **Diplomatic System** | ✅ Running | ✅ Complete | N/A |
| **Difficulty Scaling** | ✅ Running | ✅ Complete | N/A |
| **Save/Load** | ✅ Running | ✅ Complete | N/A |
| **Stochastic Injects** | ✅ Running | ✅ Complete | N/A |
| **Rich CLI** | ✅ Running | ✅ Complete | N/A |
| **Narrative State** | ❌ Not running | ✅ Complete | 2-3 hours |
| **Narrative Adjudication** | ❌ Not running | ✅ Complete | 2-3 hours |
| **Gameplay Modes** | ⚠️ Menu only | ✅ Complete | 1-2 hours |
| **De-escalation** | ❌ Missing | ⚠️ Designed | 30 mins |
| **Actor Simulation** | ❌ Missing | ⚠️ Partially designed | 4-8 hours |
| **Hidden Agendas** | ❌ Missing | ⚠️ Concept only | 2-4 hours |

---

## PART 9: KEY FILES REFERENCE

### Core Engine
```
engine/sim_loop.py          - Main turn loop, all 4 phases
engine/adjudicator.py       - OLD advisor proposal system (not used)
engine/diplomacy.py         - Diplomatic encounter system
engine/initial_conditions.py - Load YAML initial state
engine/events.py            - Load turn injects
engine/flags.py             - Flag updates and risk checks
engine/persistence.py       - Save/load JSON
```

### Agents & LLM
```
agents/conversation.py      - Advisor Q&A, interpretation, pushback
llm/router.py              - LLM provider abstraction
llm/prompts.py             - Prompt building utilities
llm/inject_generator.py    - Stochastic event generation
llm/gemini_driver.py       - Google Gemini integration
llm/mock_driver.py         - Testing/offline mode
```

### Models
```
models/world.py            - WorldState, Metrics (CURRENT)
models/narrative_state.py  - NarrativeState, vibes (NEW, not wired)
```

### CLI
```
cli/main.py               - Main entry point, game loop
cli/rich_ui.py            - Rich formatting utilities
cli/theme.py              - Colors, symbols, styling
cli/formatters.py         - Text formatting helpers
```

### Data
```
data/scenarios/war_game_2025/
  initial_conditions.yaml     - Starting state, advisors, forces
  scenarios.yaml              - Variant configs, difficulty settings
  episodes/
    turn_001.yaml            - Standard turns (6 scripted)
    turn_001_fast.yaml       - Fast turns (3 scripted)
    
data/diplomatic_profiles.yaml - All country personalities
```

### New Systems (Ready but Not Integrated)
```
engine/narrative_adjudication.py  - LLM quality assessment system
models/narrative_state.py         - Hidden metrics + vibes
```

---

## PART 10: INTEGRATION CHECKLIST FOR ACTOR SIMULATION

### Prerequisites
✅ Understand current adjudication flow (`run_turn_adjudication`)  
✅ Understand LLM prompt structure (`llm/prompts.py`)  
✅ Understand diplomatic system architecture (`engine/diplomacy.py`)  
✅ Review initial_conditions.yaml character definitions  
✅ Review diplomatic_profiles.yaml structure  

### Design Decisions Needed

**1. Actor State Storage**
- [ ] Extend diplomatic_profiles.yaml with hidden state?
- [ ] Create separate state_actors.yaml?
- [ ] Generate hidden state procedurally?

**2. Actor Selection**
- [ ] Which actors respond to each action type?
- [ ] How many actors simulate per action? (2-3 recommended)
- [ ] Priority/relevance scoring system?

**3. Effect Aggregation**
- [ ] How to derive net effects from actor responses?
- [ ] Weighted by actor influence?
- [ ] Simple majority/average?
- [ ] Player visibility into actor positions?

**4. Hidden Agenda Mechanics**
- [ ] When/how are hidden agendas revealed?
- [ ] Intelligence actions to discover them?
- [ ] Permanent or evolving based on player actions?

### Implementation Sequence

**Step 1:** Create state actor models (models/state_actors.py)  
**Step 2:** Define initial hidden state for 5 core actors (USA, France, Germany, Poland, Russia)  
**Step 3:** Build actor response simulation (engine/actor_simulation.py)  
**Step 4:** Integrate with narrative_adjudication pipeline  
**Step 5:** Test with Standard difficulty scenarios  
**Step 6:** Expand to full 7-actor system  
**Step 7:** Add intelligence/discovery mechanics  

---

## CONCLUSION

### System Maturity Assessment

**Production-Ready (Running Today):**
- Turn-based game loop with 4 distinct phases
- LLM-powered conversational advisors (Q&A, pushback, omissions)
- Sophisticated diplomatic system (7 countries, access levels, personalities)
- Difficulty scaling (Standard/Challenging/Brutal)
- Rich CLI with formatted display
- Save/load persistence
- Stochastic event generation

**Integration-Ready (Built, Not Wired):**
- Narrative state system with hidden metrics
- LLM quality-based adjudication
- Multiple gameplay modes (Classic/Immersive/Emergent)
- Character attitude tracking

**Needs Building (Your Team's Focus):**
- Multi-agent actor simulation with individual motivations
- Hidden agenda system
- Actor-specific response generation
- Intelligence gathering/discovery mechanics

### Recommended Next Steps

**For Your Team (Actor Simulation):**
1. Design StateActor data structure
2. Define hidden state for 5 core actors
3. Build actor response simulation engine
4. Create effect aggregation from actor responses

**For Integration:**
1. Wire up narrative adjudication (replaces primitive keywords)
2. Add de-escalation mechanics (makes game winnable)
3. Connect actor simulation to adjudication pipeline
4. Test across all difficulty levels

### Architecture is Solid

The codebase is well-structured for actor simulation integration:
- Clear separation of concerns
- LLM abstraction layer ready
- Diplomatic system provides template for actor behavior
- Narrative state system designed for hidden information
- All integration points identified

**You can proceed with confidence building the multi-agent system in parallel.**

---

**END OF COMPREHENSIVE ARCHITECTURE MAP**

*Generated via systematic codebase analysis*  
*All systems documented, all integration points identified*  
*Ready for actor simulation implementation*


