# Gemini 2.5 Pro Hybrid System - Implementation Report

**Feature**: Strategic use of Gemini 2.5 Pro for high-value LLM tasks  
**Status**: 🔲 Proposed - Not Yet Implemented  
**Priority**: P2 - Medium (Quality enhancement)  
**Estimated Effort**: 2-3 hours  

---

## Executive Summary

**Current System**: All LLM calls use Gemini 2.5 Flash for cost efficiency

**Proposed System**: Hybrid approach using Pro for high-value creative/analytical tasks, Flash for routine operations

**Cost Impact**: 2-4x increase per playthrough ($0.10 → $0.40), still very affordable

**Quality Impact**: Significantly better story generation, diplomatic conversations, and strategic analysis where it matters most

---

## Current LLM Architecture

### Gemini 2.5 Flash - Current Default

**Strengths**:
- ⚡ Fast response times (~1-2 seconds)
- 💰 Very cheap ($0.000075 per 1K input tokens, $0.0003 per 1K output)
- 📊 Good for structured tasks
- ✅ Sufficient for most advisor responses

**Limitations**:
- 📖 Less creative/sophisticated than Pro
- 🤔 Shallower reasoning on complex scenarios
- 💬 More generic/formulaic responses
- 🎭 Less nuanced character portrayal

### Current Usage Pattern

```
Total LLM Calls per Full Playthrough: ~75-120

Breakdown:
- Advisor responses: ~40-60 calls
- Decision interpretation: ~10-15 calls
- Pushback generation: ~5-10 calls
- Critical omissions: ~3-5 calls
- Diplomatic conversations: ~10-20 calls
- Stochastic inject generation: ~5-15 calls
- Adjudication: ~10-15 calls

Total Cost (All Flash): ~$0.10-0.20 per playthrough
```

---

## Problem Analysis: Where Flash Falls Short

### 1. Stochastic Inject Generation (Turn 7+)

**Current Quality** (Flash):
```yaml
title: "Russian Submarine Activity Increases"
description: |
  Intelligence reports indicate increased Russian submarine activity 
  in the North Atlantic. Naval forces have detected three additional 
  Akula-class submarines moving toward UK waters. This represents 
  a significant escalation of the crisis.
```

**Expected Quality** (Pro):
```yaml
title: "INTELLIGENCE FLASH: Dragon Class Submarine Detected - Unprecedented Chinese Presence"
description: |
  GCHQ has confirmed the presence of a Type 093A "Dragon" class Chinese 
  attack submarine operating in the GIUK gap - the first confirmed Chinese 
  SSN deployment to the North Atlantic in peacetime. The vessel was detected 
  by USS Virginia conducting coordinated maneuvers with Russian forces.
  
  More troubling: intercept of encrypted burst transmissions between the 
  Chinese submarine and Russian Northern Fleet suggests operational 
  coordination. NSA assesses with medium-high confidence that this represents 
  a prearranged strategic partnership exercise.
  
  This unprecedented deployment raises critical questions about the true 
  nature of Sino-Russian cooperation in this crisis.
```

**Why Pro is Better**:
- Weaves together narrative threads (China Proxy War narrative)
- Creates mystery and intrigue
- More authentic intelligence briefing style
- Subtle hints without revealing truth
- Better world-building details

---

### 2. Major Power Diplomacy

**Current Quality** (Flash - US President, China Proxy narrative):
```
US President: Prime Minister, we're monitoring the situation closely. 
I need to be honest - there are some concerns in Washington about 
how this crisis is developing. We want to support you, but we need 
to understand all the factors at play. Are you seeing any unusual 
patterns in the intelligence?
```

**Expected Quality** (Pro):
```
US President: Prime Minister... [long pause] ...I'm going to be frank 
with you, and I need you to be frank with me. 

We're getting signals from our Pacific Command that don't add up. 
Beijing is being unusually quiet about this crisis - and when China 
goes quiet, my Joint Chiefs get nervous. We've also noted some... 
financial movements... that our Treasury people find interesting.

Now, I'm not saying anything definitively, but before I commit the 
Harry Truman carrier group to the North Atlantic, I need to know: 
Have your people at GCHQ seen anything unusual? Any third parties 
with interest in seeing NATO tied up in Europe? Because if this is 
what I think it might be, we're playing a very different game.
```

**Why Pro is Better**:
- More sophisticated dialogue
- Realistic hesitation and subtext
- Natural build-up to key question
- Character depth (pauses, choosing words carefully)
- Hints at concerns without being obvious

---

### 3. Critical Omissions Analysis

**Current Quality** (Flash):
```
The Prime Minister's decision to engage President Trump addresses the 
diplomatic dimension but critically omits several key areas:

1. No military posture adjustment ordered
2. No domestic public communication planned  
3. No legal framework preparation initiated

These omissions could lead to significant problems if the situation 
escalates rapidly.
```

**Expected Quality** (Pro):
```
Strategic Gap Assessment: The Prime Minister's focus on securing US 
commitment via direct presidential engagement is sound but represents 
a single-track approach to a multi-dimensional crisis. Three critical 
omissions create unacceptable risk:

1. FORCE POSTURE PARALYSIS
   Current military stance: PASSIVE OBSERVATION
   Risk: Russian probing attacks on under-defended assets
   Window for remedy: ~2 hours before next Russian naval maneuver
   Cascading effect: If UK shows no military response, signals weakness
   
2. DOMESTIC INFORMATION VACUUM  
   Current public stance: SILENT (last update 6 hours ago)
   Risk: Panic buying already reported; social media speculation rampant
   Window for remedy: Next news cycle (90 minutes)
   Cascading effect: Loss of public confidence, potential civil disorder
   
3. LEGAL AUTHORITY DEFICIT
   Current ROE status: PEACETIME RULES
   Risk: If Russia attacks, response delayed by legal consultation
   Window for remedy: NSC meeting (can be called now)
   Cascading effect: Tactical paralysis in crisis moment

STRATEGIC ASSESSMENT: The Prime Minister is treating this as a 
diplomatic problem requiring diplomatic solutions. The military, 
domestic, and legal dimensions require parallel action NOW, not 
sequential handling after the Trump call.
```

**Why Pro is Better**:
- Deeper strategic analysis
- Cascading effect reasoning
- Time-sensitive window identification
- More military/professional language
- Explains the "why" behind each omission

---

## Proposed Hybrid Architecture

### Decision Matrix: When to Use Pro

| Use Case | Model | Rationale |
|----------|-------|-----------|
| **Stochastic Inject Generation** | Pro | Core replayability feature, needs creativity |
| **Major Power Diplomacy** (USA, Russia, China) | Pro | High-stakes conversations, character depth matters |
| **Critical Omissions** (High stakes: Escalation >80) | Pro | Strategic analysis quality critical |
| **Adjudication** (Late game: Turn >10 OR High stakes) | Pro | Fair assessment matters for player satisfaction |
| **Newspaper Briefings** (Planned feature) | Pro | Authentic journalism style, world-building |
| **Minor Power Diplomacy** (Ireland, France, Germany) | Flash | Sufficient quality for routine conversations |
| **Advisor Responses** (Routine questions) | Flash | Domain expertise is factual, not creative |
| **Decision Interpretation** | Flash | Straightforward task, Flash handles well |
| **Pushback Generation** | Flash | Template-driven, Flash sufficient |
| **Character Responses** (Post-adjudication) | Flash | Short flavor text, Flash adequate |

### Expected Call Distribution

```
Full Playthrough (15 turns):

PRO CALLS (~30):
- Stochastic injects (Turn 7-15): ~10 calls
- Major power diplomacy: ~5-10 calls  
- Critical omissions (high stakes): ~3-5 calls
- Adjudication (late game): ~5-10 calls
- Newspaper briefings: ~0-5 calls (future feature)

FLASH CALLS (~70):
- Advisor responses: ~40-50 calls
- Decision interpretation: ~10-12 calls
- Routine diplomacy: ~5-10 calls
- Pushback generation: ~3-5 calls
- Adjudication (early game): ~5-8 calls

COST ANALYSIS:
Pro calls:   30 × $0.02 = $0.60
Flash calls: 70 × $0.005 = $0.35
---------------------------------
Total per playthrough: ~$0.95

vs Current (All Flash): ~$0.20

Increase: ~4-5x, but still <$1 per full game
```

---

## Implementation Plan

### Phase 1: Infrastructure (1 hour)

**Add Pro capability to router:**

```python
# In llm/router.py

def generate_text(
    prompt: str,
    rng: Random,
    temperature: float = 0.7,
    max_tokens: int = 500,
    show_spinner: bool = True,
    use_pro: bool = False  # NEW PARAMETER
) -> str:
    """Generate text using LLM with model selection.
    
    Args:
        prompt: The input prompt
        rng: Random number generator
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
        show_spinner: Show loading spinner
        use_pro: If True, use Gemini 2.5 Pro; if False, use Flash
    
    Returns:
        Generated text string
    """
    
    # Select model based on use_pro flag
    if use_pro:
        model = "gemini-2.5-pro-latest"
        # Pro can handle longer context better
        if max_tokens == 500:  # Default
            max_tokens = 1000  # Give Pro more room
    else:
        model = "gemini-2.5-flash-latest"
    
    # Route to appropriate driver
    if MOCK_MODE:
        return mock_driver.generate_text(prompt, rng, temperature, max_tokens)
    else:
        return gemini_driver.generate_text(
            prompt, 
            rng, 
            model=model,  # Pass model selection
            temperature=temperature, 
            max_tokens=max_tokens,
            show_spinner=show_spinner
        )
```

**Update Gemini driver to accept model parameter:**

```python
# In llm/gemini_driver.py

def generate_text(
    prompt: str,
    rng: Random,
    model: str = "gemini-2.5-flash-latest",  # NEW PARAMETER
    temperature: float = 0.7,
    max_tokens: int = 500,
    show_spinner: bool = True
) -> str:
    """Generate text using Google Gemini API.
    
    Args:
        model: Which Gemini model to use (flash or pro)
        ... (other params as before)
    """
    
    genai.configure(api_key=API_KEY)
    model_instance = genai.GenerativeModel(model)  # Use specified model
    
    # ... rest of implementation
```

---

### Phase 2: Strategic Pro Usage (1-2 hours)

**Stochastic Inject Generation** (Always Pro):

```python
# In engine/events.py or llm/inject_generator.py

def generate_dynamic_inject(
    world: WorldState,
    turn_number: int,
    initial_conditions: Dict,
    scenario_library: Dict,
    transcript: List[str],
    llm_generate_fn
) -> Dict:
    """Generate dynamic inject using LLM."""
    
    prompt = build_inject_generation_prompt(...)
    
    # ALWAYS use Pro for stochastic generation
    inject_yaml = llm_generate_fn(
        prompt,
        rng,
        temperature=0.8,  # Higher creativity
        max_tokens=1000,  # Longer for detailed injects
        use_pro=True  # ← CRITICAL: Use Pro
    )
    
    return parse_inject_yaml(inject_yaml)
```

**Critical Omissions** (Conditional Pro):

```python
# In agents/conversation.py

def check_critical_omissions(
    world: WorldState,
    action: str,
    interpretation: str,
    initial_conditions: Dict,
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> List[Tuple[str, str, str]]:
    """Check for critical strategic gaps in player's decision."""
    
    # Determine if situation is high-stakes
    high_stakes = (
        world.metrics.escalation_risk > 80 or
        world.metrics.domestic_stability < 30 or
        world.metrics.alliance_cohesion < 25 or
        world.turn > 8  # Late game is always high-stakes
    )
    
    prompt = build_critical_omissions_prompt(...)
    
    # Use Pro for high-stakes analysis
    response = llm_generate_fn(
        prompt,
        rng,
        temperature=0.5,
        max_tokens=800,
        use_pro=high_stakes  # ← Conditional
    )
    
    return parse_critical_concerns(response)
```

**Major Power Diplomacy** (Always Pro):

```python
# In engine/diplomacy.py

MAJOR_POWERS = ["USA", "RUS", "CHN"]

def conduct_diplomatic_call(
    world: WorldState,
    country: str,
    initial_conditions: Dict,
    llm_generate_fn,
    rng: Random,
    transcript: List[str]
):
    """Conduct diplomatic conversation with foreign leader."""
    
    # Use Pro for major powers
    use_pro = country in MAJOR_POWERS
    
    conversation_history = []
    
    for exchange in range(11):  # Max 11 exchanges
        player_message = get_player_input()
        
        prompt = build_diplomatic_conversation_prompt(...)
        
        diplomat_response = llm_generate_fn(
            prompt,
            rng,
            temperature=0.7,
            max_tokens=600,
            use_pro=use_pro  # ← Pro for USA/Russia/China
        )
        
        # ... rest of conversation
```

**Adjudication** (Conditional Pro):

```python
# In engine/narrative_adjudication.py

def assess_action_quality(
    action: str,
    narrative_state: NarrativeState,
    interpretation: str,
    llm_generate_fn
) -> Dict[str, Any]:
    """Assess quality of player's decision."""
    
    # Use Pro for late game or high-stakes situations
    use_pro = (
        narrative_state.turn > 10 or
        narrative_state.hidden_metrics.escalation_risk > 85 or
        len(action) > 200  # Complex decisions deserve better analysis
    )
    
    prompt = build_quality_assessment_prompt(...)
    
    response = llm_generate_fn(
        prompt,
        rng,
        temperature=0.5,
        max_tokens=600,
        use_pro=use_pro  # ← Conditional
    )
    
    return parse_quality_assessment(response)
```

---

### Phase 3: Configuration System (30 minutes)

**Create config file:**

```yaml
# config/llm_config.yaml

llm:
  default_model: "flash"  # flash or pro
  
  models:
    flash:
      name: "gemini-2.5-flash-latest"
      default_temperature: 0.7
      default_max_tokens: 500
      cost_per_1k_input: 0.000075
      cost_per_1k_output: 0.0003
    
    pro:
      name: "gemini-2.5-pro-latest"
      default_temperature: 0.7
      default_max_tokens: 1000
      cost_per_1k_input: 0.00125
      cost_per_1k_output: 0.005
  
  # Force Pro usage for these contexts
  always_use_pro:
    - stochastic_inject_generation
    - major_power_diplomacy  # USA, Russia, China
    - newspaper_briefings
  
  # Conditionally use Pro based on game state
  conditional_pro:
    critical_omissions:
      enabled: true
      thresholds:
        escalation_risk: 80
        domestic_stability: 30
        turn: 8
    
    adjudication:
      enabled: true
      thresholds:
        turn: 10
        escalation_risk: 85
        decision_length: 200
    
    diplomacy:
      major_powers: ["USA", "RUS", "CHN"]
      minor_powers_use_flash: true
  
  # Cost tracking
  cost_tracking:
    enabled: true
    log_to_file: "logs/llm_costs.json"
    show_summary_on_quit: false  # Set true for development
```

**Load config:**

```python
# In llm/router.py

import yaml
from pathlib import Path

def load_llm_config() -> dict:
    """Load LLM configuration from file."""
    config_path = Path(__file__).parent.parent / "config" / "llm_config.yaml"
    
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    else:
        # Return default config
        return {
            'llm': {
                'default_model': 'flash',
                'always_use_pro': ['stochastic_inject_generation'],
                'conditional_pro': {}
            }
        }

LLM_CONFIG = load_llm_config()
```

---

## Cost Tracking System

**Optional feature for development/analytics:**

```python
# In llm/router.py

class LLMCostTracker:
    """Track LLM API costs during gameplay."""
    
    def __init__(self):
        self.calls = []
        self.total_cost = 0.0
    
    def log_call(
        self,
        model: str,
        prompt_tokens: int,
        output_tokens: int,
        context: str  # e.g., "stochastic_inject", "advisor_response"
    ):
        """Log an LLM call for cost tracking."""
        
        # Get costs from config
        if "pro" in model:
            input_cost = 0.00125 * (prompt_tokens / 1000)
            output_cost = 0.005 * (output_tokens / 1000)
        else:  # flash
            input_cost = 0.000075 * (prompt_tokens / 1000)
            output_cost = 0.0003 * (output_tokens / 1000)
        
        call_cost = input_cost + output_cost
        self.total_cost += call_cost
        
        self.calls.append({
            'model': model,
            'context': context,
            'prompt_tokens': prompt_tokens,
            'output_tokens': output_tokens,
            'cost': call_cost,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_summary(self) -> dict:
        """Get cost summary by context."""
        from collections import defaultdict
        
        by_context = defaultdict(lambda: {'calls': 0, 'cost': 0.0})
        
        for call in self.calls:
            ctx = call['context']
            by_context[ctx]['calls'] += 1
            by_context[ctx]['cost'] += call['cost']
        
        return {
            'total_calls': len(self.calls),
            'total_cost': self.total_cost,
            'by_context': dict(by_context),
            'pro_calls': sum(1 for c in self.calls if 'pro' in c['model']),
            'flash_calls': sum(1 for c in self.calls if 'flash' in c['model'])
        }

# Global tracker
COST_TRACKER = LLMCostTracker()
```

**Show summary on quit:**

```python
# In cli/main.py

def show_cost_summary():
    """Display LLM cost summary (development mode)."""
    from llm.router import COST_TRACKER
    
    summary = COST_TRACKER.get_summary()
    
    console.print("")
    console.print(f"[{COLORS['primary']}]═══ LLM COST SUMMARY ═══[/{COLORS['primary']}]")
    console.print(f"Total Calls: {summary['total_calls']}")
    console.print(f"  - Pro:   {summary['pro_calls']}")
    console.print(f"  - Flash: {summary['flash_calls']}")
    console.print(f"Total Cost: ${summary['total_cost']:.4f}")
    console.print("")
    console.print("By Context:")
    for context, data in sorted(summary['by_context'].items(), key=lambda x: x[1]['cost'], reverse=True):
        console.print(f"  {context}: {data['calls']} calls, ${data['cost']:.4f}")
```

---

## Testing & Validation

### Quality Comparison Tests

**Test 1: Inject Generation**
- Generate 10 stochastic injects with Flash
- Generate 10 stochastic injects with Pro
- Compare on:
  - Creativity score (human evaluation)
  - Narrative coherence
  - World-building detail
  - Subtle hint quality

**Test 2: Diplomatic Conversation**
- Have same conversation with US President using Flash vs Pro
- Compare on:
  - Character depth
  - Dialogue naturalness
  - Subtext and sophistication
  - Player satisfaction

**Test 3: Critical Omissions**
- Analyze same risky decision with Flash vs Pro
- Compare on:
  - Strategic depth
  - Cascading effect identification
  - Actionable recommendations
  - False positive rate

### Cost Validation

**Run 5 full playthroughs:**
- Track actual costs
- Validate estimates
- Identify optimization opportunities
- Ensure costs stay reasonable (<$1.50 per game)

---

## Rollout Strategy

### Beta Release (Recommended):
- ✅ Enable Pro for stochastic injects (always)
- ✅ Enable Pro for major power diplomacy (always)
- ⚠️ Keep Flash for everything else
- 📊 Track quality feedback from playtesters

### 1.0 Release:
- ✅ Add conditional Pro for critical omissions
- ✅ Add conditional Pro for late-game adjudication
- 📊 Validate cost per playthrough stays <$1.00

### Post-Launch:
- ✅ Add newspaper briefings with Pro
- ✅ Fine-tune conditional thresholds based on analytics
- 🎛️ Consider user preference toggle (Quality vs Cost mode)

---

## User Communication

**Do NOT** tell players about the model switching. This is an implementation detail.

**Do** communicate value:
- "Enhanced storytelling system"
- "Improved diplomatic AI"  
- "More sophisticated strategic analysis"

**Optional** (for transparency):
Add to settings menu:
```
AI Quality Mode:
○ Balanced (Recommended) - Strategic use of advanced AI for key moments
○ Performance - Faster responses, lower cost
○ Premium - Maximum quality for all interactions
```

---

## Alternatives Considered

### Alternative 1: All Pro
**Pros**: Maximum quality everywhere  
**Cons**: 10-15x cost increase ($2-3 per game), overkill for routine tasks  
**Decision**: Rejected - diminishing returns

### Alternative 2: All Flash
**Pros**: Very cheap, sufficient for most tasks  
**Cons**: Mediocre story generation, impacts core feature quality  
**Decision**: Current system - acceptable but can improve

### Alternative 3: User Choice
**Pros**: Player control, transparent  
**Cons**: Adds complexity, most won't understand difference  
**Decision**: Maybe post-launch as advanced option

---

## Success Metrics

### Quantitative:
- Average cost per playthrough: <$1.00
- Pro calls as % of total: 25-35%
- Player complaint rate about costs: <5%

### Qualitative:
- Playtest feedback on story quality: Improved
- Diplomatic conversation satisfaction: Improved
- "This feels generic" complaints: Reduced
- "The story surprised me" comments: Increased

---

## Recommendation

**Implement Phase 1 & 2 immediately** (2-3 hours)
- Add Pro capability to router
- Enable Pro for stochastic injects
- Enable Pro for major power diplomacy

**Add Phase 3 (config system) post-launch** (30 min)
- When we have analytics to tune thresholds
- When we want to experiment with different strategies

**Expected ROI**: High
- Modest cost increase (4-5x but still <$1/game)
- Significant quality improvement for core features
- Better reviews and player satisfaction
- Increased replayability value

---

**Report Compiled**: November 8, 2025  
**Status**: Ready for implementation  
**Dependencies**: None (clean implementation)  
**Risk Level**: Low (fallback to Flash always available)

