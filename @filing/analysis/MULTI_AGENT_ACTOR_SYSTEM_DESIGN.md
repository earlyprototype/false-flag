# Multi-Agent Actor System - Design Document

**Date:** Saturday, 9 November 2025  
**Status:** Design Phase - Ready to Implement  
**Estimated Time:** 4-8 hours (minimal), 10-15 hours (full)  
**Priority:** HIGH - Core gameplay enhancement

---

## EXECUTIVE SUMMARY

Transform abstract "alliance cohesion" metrics into realistic simulation of individual state actors with hidden motivations, secret agendas, and context-specific responses.

**Current Problem:**
```
Player: "I call NATO for support"
Game: "Alliance cohesion +5" (treats NATO as single entity)
Reality: WRONG - NATO is 31 different countries with different interests
```

**Target Solution:**
```
Player: "I call NATO for support"
Game: Simulates individual responses:
  - USA: Cautious (+2, conditional on proof)
  - France: Undermining (-5, secret Russia backchannel)
  - Germany: Hesitant (+1, energy concerns)
  - Poland: Strong support (+15, high threat perception)
Net Result: Alliance FRACTURED, not unified
```

**Key Insight:** Effects derived from **actual actor behavior**, not abstract metrics.

---

## PART 1: ARCHITECTURE OVERVIEW

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: STATE ACTOR DEFINITIONS                           │
│ (models/state_actors.py - NEW FILE)                        │
├─────────────────────────────────────────────────────────────┤
│ StateActor class with:                                      │
│ • Public state: official_position, relationship_uk         │
│ • Hidden state: true_motivations, hidden_agendas           │
│ • Strategic data: threat_perception, dependencies          │
│ • Constraints: redlines, domestic_pressure                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: RESPONSE SIMULATION                               │
│ (engine/actor_simulation.py - NEW FILE)                    │
├─────────────────────────────────────────────────────────────┤
│ LLM simulates each actor individually:                     │
│ • Input: Actor's hidden state + player action + context   │
│ • Process: LLM roleplays actor's response                  │
│ • Output: PUBLIC_RESPONSE, TRUST_CHANGE, WILL_SUPPORT     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: EFFECT AGGREGATION                                │
│ (engine/actor_simulation.py)                               │
├─────────────────────────────────────────────────────────────┤
│ Combine individual responses into net effects:             │
│ • Strong allies: +X to cohesion                             │
│ • Undermining actors: -X to cohesion                        │
│ • Conditional support: Flags for next turn                 │
│ • Update actor relationships individually                   │
└─────────────────────────────────────────────────────────────┘
```

---

## PART 2: DATA MODEL

### StateActor Class

**File:** `models/state_actors.py` (NEW)

```python
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class StateActor(BaseModel):
    """Individual nation-state with public and hidden state."""
    
    # === IDENTIFICATION ===
    country_code: str = Field(..., description="ISO 3166 code (USA, FRA, DEU, etc.)")
    full_name: str = Field(..., description="Official country name")
    
    # === PUBLIC STATE (player can see through diplomacy) ===
    official_position: str = Field(..., description="Public diplomatic stance")
    relationship_uk: int = Field(default=50, ge=0, le=100, description="UK relationship score")
    public_commitments: List[str] = Field(default_factory=list, description="Stated commitments")
    
    # === HIDDEN STATE (player cannot see, guides LLM) ===
    true_motivations: List[str] = Field(
        default_factory=list,
        description="Actual strategic goals (energy_security, contain_russia, avoid_war)"
    )
    hidden_agendas: List[str] = Field(
        default_factory=list,
        description="Secret plans (russia_backchannel, undermine_uk_influence)"
    )
    threat_perception: int = Field(
        default=50, ge=0, le=100,
        description="How threatened they actually feel (may differ from public)"
    )
    domestic_pressure: int = Field(
        default=50, ge=0, le=100,
        description="Internal political constraints (elections, public opinion)"
    )
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Strategic vulnerabilities (RUS: natural_gas_supply)"
    )
    redlines: List[str] = Field(
        default_factory=list,
        description="Actions they will not support (offensive_action, nuclear_first_use)"
    )
    
    # === STRATEGIC CAPABILITIES ===
    military_capability: int = Field(default=50, ge=0, le=100)
    economic_leverage: int = Field(default=50, ge=0, le=100)
    diplomatic_influence: int = Field(default=50, ge=0, le=100)
    intelligence_sharing: str = Field(default="limited", description="full/selective/limited/none")
    
    # === BEHAVIORAL TRACKING ===
    recent_actions: List[str] = Field(default_factory=list, description="Last 3 actions taken")
    trust_trajectory: str = Field(default="stable", description="improving/stable/declining")
    last_contacted_turn: Optional[int] = Field(default=None)


class ActorResponse(BaseModel):
    """Response from a single state actor to player action."""
    
    actor_id: str
    public_response: str = Field(..., description="What they say publicly")
    private_assessment: str = Field(..., description="What they actually think")
    trust_change: int = Field(default=0, ge=-20, le=20)
    will_support: str = Field(..., description="yes/no/conditional")
    conditions: List[str] = Field(default_factory=list, description="If conditional, what they need")
    intel_shared: Optional[str] = Field(default=None, description="Intelligence they share")


class StateActorSystem(BaseModel):
    """Manages all state actors in the simulation."""
    
    actors: Dict[str, StateActor] = Field(default_factory=dict)
    turn: int = Field(default=1)
    
    def get_actor(self, country_code: str) -> Optional[StateActor]:
        """Get actor by country code."""
        return self.actors.get(country_code)
    
    def get_relevant_actors(self, action_type: str, max_actors: int = 3) -> List[str]:
        """Identify which actors should respond to this action type."""
        # Implemented in actor_simulation.py
        pass
    
    def update_actor_relationship(self, country_code: str, delta: int):
        """Update bilateral relationship score."""
        if country_code in self.actors:
            current = self.actors[country_code].relationship_uk
            self.actors[country_code].relationship_uk = max(0, min(100, current + delta))
```

---

## PART 3: INITIAL ACTOR DEFINITIONS

### Core 5 Actors (Minimal Implementation)

**USA - Cautious Ally**
```yaml
country_code: USA
full_name: United States of America
official_position: "Strong ally but requires evidence and Congressional consultation"
relationship_uk: 60

true_motivations:
  - avoid_entanglement_without_proof
  - maintain_nato_credibility
  - focus_on_china_pivot
  - domestic_politics_first

hidden_agendas:
  - election_year_caution
  - wants_europe_to_lead

threat_perception: 50  # Don't feel directly threatened
domestic_pressure: 70   # Congress skeptical, public war-weary

dependencies:
  CHN: strategic_competitor  # China is main focus

redlines:
  - no_offensive_without_unambiguous_proof
  - congress_approval_required
  - no_nuclear_first_use

military_capability: 100
economic_leverage: 95
diplomatic_influence: 100
intelligence_sharing: selective  # Shares most, but holds back China-related intel
```

**France - Hidden Agenda**
```yaml
country_code: FRA
full_name: French Republic
official_position: "European solidarity with UK, but diplomatic solutions preferred"
relationship_uk: 45

true_motivations:
  - european_strategic_autonomy
  - reduce_anglosaxon_dominance
  - position_as_mediator
  - protect_french_interests

hidden_agendas:
  - secret_russia_backchannel  # ⚠️ KEY: France has back-channel to Moscow
  - wants_uk_weakened_to_strengthen_french_leadership
  - delay_nato_action_to_create_space_for_diplomacy

threat_perception: 30  # Low - geographically distant, nuclear deterrent
domestic_pressure: 60   # Public anti-war, Macron positioning for election

dependencies:
  DEU: eu_partnership
  RUS: diplomatic_relationship  # Values dialogue channel

redlines:
  - will_not_support_offensive_action
  - must_pursue_diplomatic_track_first
  - no_subordination_to_us_uk_axis

military_capability: 80
economic_leverage: 70
diplomatic_influence: 85
intelligence_sharing: limited  # Shares selectively, hides Russia channel
```

**Germany - Economically Constrained**
```yaml
country_code: DEU
full_name: Federal Republic of Germany
official_position: "Solidarity with allies, but must follow proper procedures"
relationship_uk: 50

true_motivations:
  - energy_security_paramount
  - avoid_economic_catastrophe
  - maintain_nato_consensus
  - constitutional_constraints

hidden_agendas: []  # No hidden agendas - genuinely constrained

threat_perception: 40  # Moderate - not immediate target
domestic_pressure: 80   # Public strongly anti-war, energy fears

dependencies:
  RUS: natural_gas_supply  # ⚠️ CRITICAL DEPENDENCY
  EU: economic_integration

redlines:
  - cannot_support_actions_threatening_gas_supply
  - bundestag_approval_required
  - no_offensive_military_action

military_capability: 60
economic_leverage: 85
diplomatic_influence: 75
intelligence_sharing: full  # Shares openly within NATO
```

**Poland - Strong Ally**
```yaml
country_code: POL
full_name: Republic of Poland
official_position: "Unwavering support for UK, Russia is existential threat"
relationship_uk: 85

true_motivations:
  - contain_russian_aggression
  - strengthen_nato
  - protect_eastern_europe
  - prevent_appeasement

hidden_agendas: []  # No hidden agendas - genuine ally, transparent

threat_perception: 95  # ⚠️ CRITICAL: Feel directly threatened
domestic_pressure: 20   # Public supports strong stance, government unified

dependencies: {}  # No significant dependencies

redlines: []  # Will support almost anything against Russia

military_capability: 50
economic_leverage: 30
diplomatic_influence: 40
intelligence_sharing: full  # Shares everything, wants UK intelligence in return
```

**Russia - Adversary**
```yaml
country_code: RUS
full_name: Russian Federation
official_position: "UK attacked Severomorsk, we are defending ourselves"
relationship_uk: 10

true_motivations:
  - test_nato_resolve
  - fracture_alliance
  - neutralize_uk_as_obstacle
  - demonstrate_us_wont_defend_europe

hidden_agendas:
  - operation_tuman  # Pre-planned attack, UK is target
  - exploit_nato_divisions
  - undermine_us_commitment

threat_perception: 40  # Don't fear UK militarily
domestic_pressure: 30   # Regime controls narrative, public supportive

dependencies: {}

redlines:
  - will_escalate_if_nato_deploys_offensively
  - nuclear_option_if_regime_threatened

military_capability: 90
economic_leverage: 60  # Energy exports
diplomatic_influence: 40
intelligence_sharing: none
```

---

## PART 4: ACTOR SIMULATION ENGINE

### Core Function: `simulate_actor_response()`

**File:** `engine/actor_simulation.py` (NEW)

```python
from typing import List, Tuple
from random import Random

from models.state_actors import StateActor, ActorResponse
from models.world import WorldState

def simulate_actor_response(
    actor: StateActor,
    player_action: str,
    world_context: str,
    llm_generate_fn,
    rng: Random
) -> ActorResponse:
    """
    Use LLM to simulate how this specific actor responds.
    
    The LLM is given the actor's HIDDEN STATE (motivations, agendas, dependencies)
    and asked to roleplay their response realistically.
    """
    
    # Build prompt with actor's secret knowledge
    prompt = f"""
You are simulating {actor.full_name}'s response to a UK government action.

=== ACTOR IDENTITY ===
Country: {actor.full_name} ({actor.country_code})
Official Position: {actor.official_position}
Relationship with UK: {actor.relationship_uk}/100

=== HIDDEN STATE (guides your response, UK does not know this) ===
True Motivations: {', '.join(actor.true_motivations)}
Hidden Agendas: {', '.join(actor.hidden_agendas) if actor.hidden_agendas else 'None'}
Threat Perception: {actor.threat_perception}/100
Domestic Pressure: {actor.domestic_pressure}/100
Dependencies: {actor.dependencies}
Redlines: {', '.join(actor.redlines) if actor.redlines else 'None'}

Strategic Capabilities:
- Military: {actor.military_capability}/100
- Economic: {actor.economic_leverage}/100
- Diplomatic: {actor.diplomatic_influence}/100
- Intelligence Sharing: {actor.intelligence_sharing}

=== WORLD CONTEXT ===
{world_context}

=== UK ACTION ===
{player_action}

=== TASK ===
Respond as {actor.full_name} would REALISTICALLY respond given:
1. Your true motivations (not just public position)
2. Your hidden agendas
3. Your actual threat perception
4. Your domestic/economic constraints
5. Your dependencies and vulnerabilities

Respond in this EXACT format:

PUBLIC_RESPONSE: [What you say publicly/diplomatically to UK]

PRIVATE_ASSESSMENT: [What you actually think internally]

TRUST_CHANGE: [number from -20 to +20, how this action affects your view of UK]

WILL_SUPPORT: [yes/no/conditional]

CONDITIONS: [If conditional, what specific conditions must UK meet? Leave empty if yes/no]

INTEL_SHARED: [Any intelligence you choose to share, or "none"]

Be realistic. If you have hidden agendas, let them guide your response.
If you have dependencies (e.g., Russian gas), they constrain your actions.
If you have redlines, enforce them.
"""
    
    try:
        response_text = llm_generate_fn(prompt, rng)
        return _parse_actor_response(actor.country_code, response_text)
    
    except Exception as e:
        # Fallback to heuristic response
        return _heuristic_actor_response(actor, player_action)


def _parse_actor_response(actor_id: str, response_text: str) -> ActorResponse:
    """Parse LLM response into structured ActorResponse."""
    lines = response_text.strip().split('\n')
    
    public_response = ""
    private_assessment = ""
    trust_change = 0
    will_support = "conditional"
    conditions = []
    intel_shared = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("PUBLIC_RESPONSE:"):
            public_response = line.split(":", 1)[1].strip()
        
        elif line.startswith("PRIVATE_ASSESSMENT:"):
            private_assessment = line.split(":", 1)[1].strip()
        
        elif line.startswith("TRUST_CHANGE:"):
            try:
                trust_change = int(line.split(":", 1)[1].strip())
                trust_change = max(-20, min(20, trust_change))
            except:
                trust_change = 0
        
        elif line.startswith("WILL_SUPPORT:"):
            support_str = line.split(":", 1)[1].strip().lower()
            if support_str in ["yes", "no", "conditional"]:
                will_support = support_str
        
        elif line.startswith("CONDITIONS:"):
            cond_text = line.split(":", 1)[1].strip()
            if cond_text and cond_text.lower() != "none":
                conditions = [c.strip() for c in cond_text.split(';')]
        
        elif line.startswith("INTEL_SHARED:"):
            intel_text = line.split(":", 1)[1].strip()
            if intel_text and intel_text.lower() != "none":
                intel_shared = intel_text
    
    return ActorResponse(
        actor_id=actor_id,
        public_response=public_response or f"{actor_id} acknowledges the action.",
        private_assessment=private_assessment or "Assessing situation.",
        trust_change=trust_change,
        will_support=will_support,
        conditions=conditions,
        intel_shared=intel_shared
    )


def identify_relevant_actors(action: str, actor_system, max_actors: int = 3) -> List[str]:
    """
    Determine which actors should respond to this action.
    
    Relevance based on:
    - Action keywords (NATO → all NATO members relevant)
    - Actor threat perception (high threat → more reactive)
    - Recent interaction (contacted recently → more likely to respond)
    """
    relevant = []
    action_lower = action.lower()
    
    # Always relevant: Core allies
    always_relevant = ["USA", "FRA", "DEU", "POL"]
    
    # NATO actions → all NATO members
    if any(word in action_lower for word in ["nato", "article 5", "alliance"]):
        relevant.extend(always_relevant)
    
    # Diplomatic actions → mentioned countries + close allies
    elif any(word in action_lower for word in ["diplomatic", "call", "contact"]):
        # Add explicitly mentioned countries
        for code in actor_system.actors.keys():
            if code.lower() in action_lower or actor_system.actors[code].full_name.lower() in action_lower:
                relevant.append(code)
        
        # Add close allies if none mentioned
        if not relevant:
            relevant = ["USA", "POL"]  # Default to closest allies
    
    # Military actions → threatened actors respond
    elif any(word in action_lower for word in ["deploy", "military", "forces"]):
        for code, actor in actor_system.actors.items():
            if actor.threat_perception > 70:
                relevant.append(code)
    
    # Default: Top 2-3 most relevant actors
    if not relevant:
        relevant = ["USA", "FRA", "POL"]  # Default key actors
    
    # Limit to max_actors, prioritize by relationship_uk
    if len(relevant) > max_actors:
        relevant = sorted(relevant, key=lambda c: actor_system.actors[c].relationship_uk, reverse=True)[:max_actors]
    
    return relevant


def calculate_effects_from_responses(
    responses: List[ActorResponse],
    actor_system
) -> Dict[str, int]:
    """
    Derive actual metric effects from actor responses.
    
    Instead of abstract "alliance_cohesion +5", calculate based on:
    - How many actors support (yes)
    - How many undermine (no, or low trust_change)
    - How many are conditional
    """
    effects = {
        "alliance_cohesion": 0,
        "escalation_risk": 0,
        "domestic_stability": 0
    }
    
    strong_support = 0
    undermining = 0
    conditional = 0
    
    for response in responses:
        actor = actor_system.actors.get(response.actor_id)
        if not actor:
            continue
        
        # Weight by actor's diplomatic influence
        weight = actor.diplomatic_influence / 50.0  # Normalize to 0-2 range
        
        if response.will_support == "yes":
            strong_support += weight
            effects["alliance_cohesion"] += int(5 * weight)
        
        elif response.will_support == "no":
            undermining += weight
            effects["alliance_cohesion"] -= int(8 * weight)
            effects["escalation_risk"] += int(3 * weight)  # Opposition signals weakness
        
        elif response.will_support == "conditional":
            conditional += weight
            effects["alliance_cohesion"] += int(2 * weight)  # Slight positive, but hesitant
        
        # Trust changes affect domestic stability (shows leadership quality)
        if response.trust_change > 5:
            effects["domestic_stability"] += 2
        elif response.trust_change < -5:
            effects["domestic_stability"] -= 3
    
    # Bonus/penalty based on overall consensus
    if strong_support >= 2 and undermining == 0:
        # Strong unified support
        effects["alliance_cohesion"] += 5
        effects["escalation_risk"] -= 5
    
    elif undermining >= 1 and strong_support < 2:
        # Divided alliance
        effects["alliance_cohesion"] -= 5
        effects["escalation_risk"] += 5
    
    return effects
```

---

## PART 5: INTEGRATION WITH ADJUDICATION

### Enhanced Adjudication Pipeline

**File:** `engine/narrative_adjudication.py` (MODIFY)

Add actor simulation before applying effects:

```python
def adjudicate_with_actor_simulation(
    narrative_state: NarrativeState,
    actor_system: StateActorSystem,
    action: str,
    interpretation: str,
    rng: Random,
    llm_generate_fn
) -> Tuple[Dict[str, int], List[ActorResponse], str]:
    """
    Enhanced adjudication with multi-agent actor simulation.
    
    Pipeline:
    1. Identify relevant actors
    2. Simulate each actor's response
    3. Calculate effects from responses
    4. Apply to metrics
    5. Update actor relationships
    6. Generate narrative summary
    """
    
    # 1. Identify which actors should respond
    relevant_actor_ids = identify_relevant_actors(action, actor_system, max_actors=3)
    
    # 2. Simulate each actor's response
    actor_responses = []
    world_context = narrative_state.to_llm_context()
    
    for actor_id in relevant_actor_ids:
        actor = actor_system.get_actor(actor_id)
        if not actor:
            continue
        
        response = simulate_actor_response(
            actor, action, world_context, llm_generate_fn, rng
        )
        actor_responses.append(response)
        
        # Update actor's relationship with UK
        actor_system.update_actor_relationship(actor_id, response.trust_change)
    
    # 3. Calculate effects from responses
    actor_effects = calculate_effects_from_responses(actor_responses, actor_system)
    
    # 4. Also run quality assessment for player skill
    quality_assessment = assess_action_quality(action, narrative_state, interpretation, llm_generate_fn)
    base_effects = determine_base_effects(action, narrative_state)
    quality_effects = apply_quality_scaling(base_effects, quality_assessment, narrative_state)
    
    # 5. Merge actor effects with quality effects (average)
    final_effects = {}
    all_metrics = set(actor_effects.keys()) | set(quality_effects.keys())
    
    for metric in all_metrics:
        actor_val = actor_effects.get(metric, 0)
        quality_val = quality_effects.get(metric, 0)
        # Weight: 60% actor responses, 40% quality assessment
        final_effects[metric] = int(actor_val * 0.6 + quality_val * 0.4)
    
    # 6. Apply to narrative state
    for metric, delta in final_effects.items():
        if hasattr(narrative_state.hidden_metrics, metric):
            current = getattr(narrative_state.hidden_metrics, metric)
            updated = clamp(current + delta)
            setattr(narrative_state.hidden_metrics, metric, updated)
    
    # 7. Generate narrative summary
    reasoning = _generate_actor_summary(actor_responses, quality_assessment)
    
    return final_effects, actor_responses, reasoning


def _generate_actor_summary(responses: List[ActorResponse], quality: Dict) -> str:
    """Generate human-readable summary of actor responses."""
    summary_parts = []
    
    summary_parts.append(f"Action Quality: {quality['quality'].upper()}")
    summary_parts.append(f"Reasoning: {quality['reasoning']}")
    summary_parts.append("")
    summary_parts.append("International Response:")
    
    for response in responses:
        support_symbol = {
            "yes": "✓",
            "no": "✗",
            "conditional": "○"
        }.get(response.will_support, "?")
        
        summary_parts.append(f"  {support_symbol} {response.actor_id}: {response.public_response[:60]}...")
    
    return "\n".join(summary_parts)
```

---

## PART 6: IMPLEMENTATION PHASES

### Phase 1: Minimal Implementation (4-5 hours)

**Goal:** Proof of concept with 3 core actors

**Scope:**
1. Create `models/state_actors.py` with classes
2. Define USA, France, Poland actors (3 only)
3. Implement basic `simulate_actor_response()`
4. Integrate into adjudication (optional toggle)
5. Test with fast_start variant

**Deliverables:**
- ✓ State actor data models
- ✓ 3 actor definitions
- ✓ Basic LLM simulation
- ✓ Effects calculation
- ✓ Integration toggle (can enable/disable)

---

### Phase 2: Full Implementation (10-15 hours)

**Goal:** Complete system with all actors and polish

**Scope:**
1. Add Germany, Russia, Ukraine, Ireland
2. Implement relevance scoring (which actors respond)
3. Add actor memory (remember past interactions)
4. Intelligence discovery mechanics
5. Coalition-building strategies
6. Rich UI display of actor responses

**Deliverables:**
- ✓ 7+ actors defined
- ✓ Smart actor selection
- ✓ Memory system
- ✓ Discovery mechanics
- ✓ Polished UI

---

### Phase 3: Advanced Features (Future)

**Goal:** Deep simulation features

**Scope:**
1. Actor relationships evolve (France-Russia channel discovered)
2. Hidden agendas can be exposed
3. Economic leverage mechanics (Germany gas dependency)
4. Coalition formation (Eastern European bloc)
5. Actor-specific victory conditions

---

## PART 7: PLAYER EXPERIENCE CHANGES

### Old System:
```
Player: "I call emergency NATO summit"

Game: 
Alliance Cohesion: 35 → 40 (+5)
```

**Feels:** Abstract, unrealistic, no agency

---

### New System:
```
Player: "I call emergency NATO summit with intelligence briefing"

Game:
[Simulating international response...]

🇺🇸 USA (National Security Advisor):
"Prime Minister, we appreciate the intelligence package. The President 
will brief Congress tomorrow. We need 48 hours."
Trust: +3 | Support: CONDITIONAL | Conditions: Congressional approval

🇫🇷 France (Foreign Minister):
"We believe diplomatic channels should be exhausted first. Invoking NATO 
mechanisms now could escalate unnecessarily."
Trust: -5 | Support: NO | [Hidden: Protecting Russia backchannel]

🇵🇱 Poland (President):
"Poland stands unequivocally with the United Kingdom. We are ready to 
deploy forces immediately if Article 5 is invoked."
Trust: +12 | Support: YES | Intelligence Shared: Russian force movements

═══ OUTCOME ═══
Alliance Status: FRACTURED
Strong Support: Poland
Conditional Support: USA (needs Congressional approval)
Opposition: France (undermining position)

Effects:
  Alliance Cohesion: +2 (not the +5 you hoped for)
  Escalation Risk: +3 (France opposition signals division)
  Domestic Stability: +1 (mixed international response)

⚠️ INTEL: France's opposition seems unusually strong. Possible hidden agenda?
```

**Feels:** Realistic, consequential, strategic depth

---

## PART 8: COST & PERFORMANCE

### Token Usage

**Per Actor Response:**
- Prompt (actor state + context): ~800 tokens
- Response: ~200 tokens
- Total per actor: ~1000 tokens

**Per Turn (3 actors simulated):**
- Actor simulation: 3000 tokens
- Quality assessment: 600 tokens
- Character responses: 400 tokens
- **Total: 4000 tokens**

**Per Game:**
- Fast mode (3 turns): 12,000 tokens = $0.0015
- Standard (10 turns): 40,000 tokens = $0.005

**Comparison:**
- Current system (no actors): $0.0003/game
- With actors: $0.005/game
- **16× increase, but still < $0.01 per game**

---

## PART 9: TESTING STRATEGY

### Test 1: France Hidden Agenda Discovery

**Setup:**
1. Start new game
2. Make pro-NATO action (call Article 5)

**Expected:**
- USA: Conditional support
- France: Opposition (public: "diplomacy first", private: protecting Russia)
- Poland: Strong support

**Validation:**
- Alliance cohesion increases LESS than expected (France undermining)
- Player can infer France might be compromised

---

### Test 2: Germany Energy Dependency

**Setup:**
1. Propose action threatening Russian gas supply
2. Observe Germany response

**Expected:**
- Germany: NO or CONDITIONAL (energy concerns explicit)
- Public response mentions economic implications
- Trust decreases if UK ignores concerns

**Validation:**
- Effects reflect German hesitation
- Realistic geopolitical constraint

---

### Test 3: Poland Enthusiasm

**Setup:**
1. Any anti-Russia action
2. Observe Poland response

**Expected:**
- Poland: YES (enthusiastic, offers forces)
- Trust increases significantly
- Intel shared willingly

**Validation:**
- Strong ally provides tangible support
- Effects boosted by Polish backing

---

## PART 10: ROLLBACK & RISK MITIGATION

### Risks

| Risk | Mitigation |
|------|------------|
| LLM responses inconsistent | Use heuristic fallback, store actor state |
| Too expensive | Limit to 2-3 actors, cache responses |
| Too complex for players | Provide summary, hide technical details |
| Integration bugs | Make system optional toggle initially |

### Rollback Plan

**Toggle System:**
```python
# In cli/main.py or config.py
USE_ACTOR_SIMULATION = False  # Set to False to revert

if USE_ACTOR_SIMULATION:
    # Use actor simulation
    effects, responses = adjudicate_with_actor_simulation(...)
else:
    # Use standard adjudication
    effects, responses = adjudicate_with_narrative(...)
```

**Easy Rollback:** Just flip toggle, no code removal needed

---

## PART 11: SUCCESS CRITERIA

### Minimal (Phase 1) ✓

- [ ] StateActor class exists and validated
- [ ] 3 actors defined (USA, France, Poland)
- [ ] Actor responses differ meaningfully
- [ ] Effects derived from responses
- [ ] Can toggle on/off

### Full (Phase 2) ✓

- [ ] 7+ actors defined
- [ ] Relevance selection works
- [ ] Hidden agendas affect outcomes
- [ ] Player can discover inconsistencies
- [ ] Rich UI display

### Polish (Phase 3) ✓

- [ ] Actor memory persists
- [ ] Relationships evolve
- [ ] Intelligence mechanics
- [ ] Coalition strategies
- [ ] Balanced and fun

---

## CONCLUSION

**Ready to Implement:** Design complete, architecture clear, integration path defined.

**Recommendation:** 
1. Implement LLM adjudicator FIRST (1-2 hours)
2. Test and validate it works well
3. THEN add actor simulation on top (4-5 hours minimal)

**Why This Order:**
- LLM adjudicator provides immediate value (de-escalation, quality)
- Actor simulation builds on solid foundation
- Can test/validate each layer independently
- Easier rollback if issues arise

**Next:** Proceed with LLM adjudicator implementation.

---

**END OF DESIGN DOCUMENT**

*Ready for implementation when LLM adjudicator is stable.*


