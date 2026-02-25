# Multi-Agent Actor System - LLM Constraints & Configuration

**Date**: 12 November 2025  
**Status**: Design Specification  
**Purpose**: Define all constraints for LLM usage in multi-agent simulation

---

## PART 1: MODEL CONFIGURATION

### Current LLM Setup

**Provider**: Google Gemini (free tier)  
**Model**: `gemini-2.5-flash-lite` ⚡ (configurable in `config.py`)  
**API Key**: `GOOGLE_API_KEY` environment variable / `config.py`

**Available Alternatives:**
- `gemini-2.5-flash-lite` ⚡ (current) - Fastest, efficient, 1M token context
- `gemini-2.5-flash` - Fast, efficient, 1M token context
- `gemini-2.5-pro` - Higher quality, slower, more expensive
- `mock` - Deterministic testing (no API calls)

### Generation Parameters

**Current Settings** (`config.py`):
```python
GEMINI_TEMPERATURE = 0.7      # Balance of consistency and creativity
GEMINI_MAX_TOKENS = 4096      # Per response (increased from 2048)
```

**For Multi-Agent Actor Simulation:**
```python
# Recommended settings
ACTOR_TEMPERATURE = 0.6        # Slightly lower for consistent actor behavior
ACTOR_MAX_TOKENS = 400         # Constrained output per actor
ACTOR_TOP_P = 0.9             # Nucleus sampling
ACTOR_TOP_K = 40              # Top-K sampling
```

**Rationale:**
- **Lower temperature (0.6 vs 0.7)**: Actors should behave consistently with their hidden state
- **Constrained tokens (400)**: Prevent verbose responses, keep responses focused
- **Top-P/Top-K**: Standard values for balanced generation

### Safety Settings

**Current** (`gemini_driver.py`):
```python
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
```

**For Actor Simulation:**
- **KEEP BLOCK_NONE**: Wargame requires mature political content
- **Justification**: Simulating geopolitical actors discussing war, threats, sanctions

---

## PART 2: CONTEXT CONSTRAINTS (INPUT)

### Token Budget per Actor Response

**Prompt Structure:**
```
┌─────────────────────────────────────────┐
│ ACTOR IDENTITY              (~150 tokens)│
│ • Country, official position            │
│ • Relationship with UK                  │
├─────────────────────────────────────────┤
│ HIDDEN STATE                (~300 tokens)│
│ • True motivations                      │
│ • Hidden agendas                        │
│ • Threat perception                     │
│ • Dependencies                          │
│ • Redlines                              │
├─────────────────────────────────────────┤
│ WORLD CONTEXT               (~250 tokens)│
│ • Current metrics                       │
│ • Recent events                         │
│ • Crisis phase                          │
├─────────────────────────────────────────┤
│ UK ACTION                   (~100 tokens)│
│ • Player's action text                  │
├─────────────────────────────────────────┤
│ TASK INSTRUCTIONS           (~150 tokens)│
│ • Output format specification           │
│ • Constraints                           │
└─────────────────────────────────────────┘
TOTAL INPUT: ~950 tokens per actor
```

### Context Limits

**Per Actor Prompt**: ~950 tokens input
**Per Turn (3 actors)**: ~2,850 tokens input
**Per Game (10 turns)**: ~28,500 tokens input

**Gemini 2.5 Flash Context Window**: 1,000,000 tokens  
**Safety Margin**: Massive headroom (only ~3% usage per game)

### Context Building Strategy

**Use Existing System:**
```python
from llm.context_builder import get_diplomatic_context

# Already implemented - builds structured context
context = get_diplomatic_context(
    world=world,
    action=action,
    interpretation=interpretation
)
```

**Key Components:**
1. **Crisis summary**: 1-2 sentences
2. **Escalation level**: High/Medium/Low
3. **Alliance status**: Cohesion score
4. **Recent developments**: Last 2-3 turns
5. **UK credibility**: Trust trajectory

**Constraint:** Keep context under 300 tokens to allow for actor detail

---

## PART 3: OUTPUT CONSTRAINTS (RESPONSE)

### Structured Output Format

**Required Fields:**
```
PUBLIC_RESPONSE: [1-2 sentences, diplomatic language]
PRIVATE_ASSESSMENT: [1-2 sentences, internal thinking]
TRUST_CHANGE: [integer -20 to +20]
WILL_SUPPORT: [yes/no/conditional]
CONDITIONS: [if conditional, semicolon-separated list]
INTEL_SHARED: [optional intelligence or "none"]
```

**Example:**
```
PUBLIC_RESPONSE: We appreciate the UK's commitment to transparency. The United States will brief Congress and respond within 48 hours.

PRIVATE_ASSESSMENT: Action is reasonable but UK hasn't provided concrete proof. Domestic politics constrains immediate commitment.

TRUST_CHANGE: +3

WILL_SUPPORT: conditional

CONDITIONS: Congressional approval required; Intelligence package must include satellite imagery; No offensive action before diplomatic options exhausted

INTEL_SHARED: NSA intercepts show Russian naval communications spike 240% in last 6 hours
```

### Token Limits per Field

| Field | Max Tokens | Constraint |
|-------|-----------|------------|
| PUBLIC_RESPONSE | 80 | 1-2 sentences, diplomatic |
| PRIVATE_ASSESSMENT | 80 | 1-2 sentences, internal |
| TRUST_CHANGE | 5 | Integer only, -20 to +20 |
| WILL_SUPPORT | 15 | Enum: yes/no/conditional |
| CONDITIONS | 120 | Semicolon list if conditional |
| INTEL_SHARED | 100 | Optional, can be "none" |
| **TOTAL** | **~400** | **Per actor response** |

### Response Validation

**Parsing Rules:**
```python
def _parse_actor_response(actor_id: str, response_text: str) -> ActorResponse:
    """
    Parse LLM response with strict validation:
    
    1. Extract each field using string matching
    2. Validate TRUST_CHANGE is integer -20 to +20
    3. Validate WILL_SUPPORT is yes/no/conditional
    4. If parsing fails, use fallback heuristic
    """
```

**Fallback on Parse Failure:**
- If LLM returns malformed output
- If required fields missing
- If validation fails
- **Action:** Use `_heuristic_actor_response()` for that actor

### Error Handling

**Three-Tier Fallback:**
```
Try 1: LLM simulation
  ↓ (if API error)
Try 2: Retry once with same prompt
  ↓ (if still fails)
Fallback: Heuristic based on actor's relationship_uk
```

**Heuristic Logic:**
```python
def _heuristic_actor_response(actor: StateActor, action: str) -> ActorResponse:
    """
    Deterministic fallback based on actor state:
    
    - relationship_uk > 70: Support (yes)
    - relationship_uk 40-70: Conditional
    - relationship_uk < 40: Oppose (no)
    
    Trust change: ±2 random variation
    """
```

---

## PART 4: PERFORMANCE CONSTRAINTS

### Latency Budget

**Sequential Simulation** (3 actors):
- Actor 1: 2-4 seconds
- Actor 2: 2-4 seconds  
- Actor 3: 2-4 seconds
- **Total**: 6-12 seconds per turn

**With Spinner:**
```
[Simulating international response...]
  🇺🇸 USA... (2.3s)
  🇫🇷 France... (3.1s)
  🇵🇱 Poland... (2.8s)
[Response complete]
```

**Player Perception:** Acceptable (feels like "AI thinking")

### Parallel Processing (IMPLEMENTED)

**Implementation**: Parallel API calls using `ThreadPoolExecutor`

```python
# Parallel processing using concurrent.futures
responses = batch_generate_text([
    actor_1_prompt,
    actor_2_prompt,
    actor_3_prompt,
    actor_4_prompt,
    actor_5_prompt
], rng)
# Total time: ~3-4 seconds (all actors in parallel)
```

**Benefits:**
- 60-70% latency reduction vs sequential
- Same token cost
- All relevant actors processed simultaneously
- Uses ThreadPoolExecutor for reliable parallel execution

### Cost Constraints

**Gemini 2.5 Flash Pricing** (as of Nov 2025):
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

**Cost per Actor:**
- Input: 950 tokens × $0.075 / 1M = $0.00007
- Output: 400 tokens × $0.30 / 1M = $0.00012
- **Total**: $0.00019 per actor

**Cost per Turn** (all relevant actors, typically 3-5):
- $0.00057 - $0.00095 per turn (depending on number of relevant actors)

**Cost per Game** (10 turns):
- Fast mode (3 turns): $0.0017
- Standard (10 turns): $0.0057
- **Total game cost**: < $0.01

**Free Tier Limit**: 1,500 requests/day  
**Safety**: ~400 games/day before hitting limit

---

## PART 5: QUALITY CONSTRAINTS

### Consistency Requirements

**Actor Personality Consistency:**
- Actor must respond **in character** with their hidden state
- France with Russia backchannel → consistently cautious/undermining
- Poland with high threat perception → consistently supportive
- Germany with gas dependency → consistently hesitant on energy-related actions

**Validation:**
```python
def validate_actor_consistency(actor: StateActor, response: ActorResponse):
    """
    Check response aligns with actor's hidden state:
    
    - If actor has hidden agenda "undermine_uk", trust_change should be ≤ 0
    - If actor has redline matched, will_support should be "no"
    - If actor has high threat_perception (>70), should be supportive
    """
```

### Output Quality Metrics

**Manual Review Checks** (testing phase):
1. **Realism**: Does response sound like real diplomat?
2. **Consistency**: Does actor behave according to hidden state?
3. **Variance**: Do different actions produce different responses?
4. **Format**: Does output parse correctly?

**Automated Tests:**
```python
def test_france_undermines_uk():
    """France with Russia backchannel should show low support"""
    actor = actors["FRA"]
    response = simulate_actor_response(actor, "Call emergency NATO summit", ...)
    
    assert response.will_support in ["no", "conditional"]
    assert response.trust_change <= 3  # Shouldn't trust UK much
    
def test_poland_supports_uk():
    """Poland with high threat perception should support anti-Russia actions"""
    actor = actors["POL"]
    response = simulate_actor_response(actor, "Deploy forces defensively", ...)
    
    assert response.will_support == "yes"
    assert response.trust_change >= 5
```

---

## PART 6: CONTEXT INJECTION STRATEGY

### What Each Actor MUST Know

**Essential Context:**
1. **Crisis overview**: 2 sentences (what's happening)
2. **Escalation level**: Current risk (numerical hidden, descriptive shown)
3. **UK's recent actions**: Last 1-2 turns
4. **Alliance state**: General cohesion level

**What Each Actor MUST NOT Know:**
1. **Other actors' hidden states**: France doesn't know Poland's true threat perception
2. **Player's future intentions**: Only current action
3. **Hidden metrics**: Actual numerical values (only descriptive)

### Dynamic Context Building

**Template:**
```python
def build_actor_context(actor: StateActor, narrative_state: NarrativeState) -> str:
    """
    Build tailored context for this specific actor.
    
    Includes:
    - General crisis state (everyone sees this)
    - Actor-specific perceptions (based on their intelligence_sharing level)
    - Actor's recent interactions with UK
    """
    
    context_parts = []
    
    # 1. Base crisis overview (everyone gets this)
    context_parts.append(f"CRISIS: {narrative_state.summary}")
    
    # 2. Escalation descriptor (not numbers)
    if narrative_state.hidden_metrics.escalation_risk > 80:
        context_parts.append("ESCALATION: Critical - military confrontation imminent")
    elif narrative_state.hidden_metrics.escalation_risk > 60:
        context_parts.append("ESCALATION: High - situation deteriorating rapidly")
    # ... etc
    
    # 3. Alliance state (general)
    context_parts.append(f"ALLIANCE STATUS: {_get_alliance_descriptor(narrative_state)}")
    
    # 4. Actor-specific intelligence (based on intelligence_sharing level)
    if actor.intelligence_sharing == "full":
        # Full FIVE EYES partner - gets detailed intel
        context_parts.append("UK INTELLIGENCE SHARED: [detailed package]")
    elif actor.intelligence_sharing == "selective":
        # Selective sharing - gets overview only
        context_parts.append("UK INTELLIGENCE SHARED: [summary only]")
    # ... etc
    
    return "\n".join(context_parts)
```

---

## PART 7: DETERMINISM & REPRODUCIBILITY

### RNG Seed Usage

**Current System:**
```python
def simulate_actor_response(
    actor: StateActor,
    player_action: str,
    world_context: str,
    llm_generate_fn,
    rng: Random  # ← Deterministic seed from game
) -> ActorResponse:
    """
    Uses rng seed for LLM temperature/sampling.
    Same seed + same inputs = same response.
    """
```

**Challenge with Gemini:**
- Gemini API doesn't support explicit seed parameter
- Cannot guarantee 100% deterministic output
- Temperature > 0 introduces variation

**Mitigation:**
- Use RNG to generate seed value for future use
- Store actor responses in save file
- Replay mode uses stored responses, not re-simulation

### Save/Load Actor State

**Persistence:**
```python
# In persistence.py
def save_game(save_path, world, narrative_state, actor_system):
    """
    Save includes:
    - WorldState (metrics, turn)
    - NarrativeState (hidden metrics, character attitudes)
    - ActorSystem (all actor states, recent responses)  # ← NEW
    """
    
def load_game(save_path):
    """
    Load restores complete actor state including:
    - relationship_uk scores
    - recent_actions history
    - trust_trajectory
    """
```

---

## PART 8: RATE LIMITING & THROTTLING

### API Rate Limits (Gemini Free Tier)

**Current Limits:**
- 1,500 requests per day
- 15 requests per minute
- No hard token limit (1M context window available)

**Multi-Agent Usage:**
- 3 actors per turn = 3 requests
- 10 turn game = 30 requests total
- **50 games per day before hitting limit**

### Throttling Strategy

**If Rate Limited:**
```python
import time

def simulate_actor_response_with_retry(actor, action, context, llm_fn, rng):
    """
    Retry logic with exponential backoff:
    
    1. Try API call
    2. If rate limited (429), wait 2 seconds
    3. Retry
    4. If still fails, wait 4 seconds
    5. Retry
    6. If still fails, use heuristic fallback
    """
    
    max_retries = 2
    base_wait = 2.0
    
    for attempt in range(max_retries + 1):
        try:
            return simulate_actor_response(actor, action, context, llm_fn, rng)
        except RateLimitError:
            if attempt < max_retries:
                wait_time = base_wait * (2 ** attempt)
                time.sleep(wait_time)
            else:
                # Final fallback
                return _heuristic_actor_response(actor, action)
```

---

## PART 9: TESTING CONSTRAINTS

### Test Scenarios for LLM Behavior

**Scenario 1: Consistency Test**
```python
def test_actor_consistency_across_similar_actions():
    """
    Same action type should produce similar responses.
    """
    actor = actors["USA"]
    
    response_1 = simulate("Call NATO allies")
    response_2 = simulate("Contact NATO for support")
    response_3 = simulate("Request NATO assistance")
    
    # All should have similar will_support and trust_change
    assert all(r.will_support == "conditional" for r in [response_1, response_2, response_3])
```

**Scenario 2: Hidden Agenda Test**
```python
def test_france_hidden_agenda_affects_response():
    """
    France's Russia backchannel should make them oppose offensive actions.
    """
    actor = actors["FRA"]
    
    # Offensive action
    response = simulate("Deploy strike forces to Estonian border")
    
    assert response.will_support in ["no", "conditional"]
    assert "diplomatic" in response.public_response.lower()
    # France should advocate diplomacy to protect backchannel
```

**Scenario 3: Dependency Test**
```python
def test_germany_gas_dependency_constrains_response():
    """
    Germany's gas dependency should make them hesitant on Russia sanctions.
    """
    actor = actors["DEU"]
    
    response = simulate("Propose immediate total Russian gas embargo")
    
    assert response.will_support in ["no", "conditional"]
    assert any(word in response.public_response.lower() 
               for word in ["energy", "supply", "economic"])
```

### Mock Mode for Testing

**Toggle for Development:**
```python
# config.py
LLM_PROVIDER = "mock"  # Use deterministic mock, no API calls

# During testing
USE_ACTOR_SIMULATION = True
LLM_PROVIDER = "mock"

# Actors will use heuristic responses, no API cost
```

---

## PART 10: IMPLEMENTATION CHECKLIST

### Configuration Changes

- [ ] Add `ACTOR_TEMPERATURE = 0.6` to `config.py`
- [ ] Add `ACTOR_MAX_TOKENS = 400` to `config.py`
- [ ] Update `gemini_driver.py` to support per-call temperature override
- [ ] Add `USE_ACTOR_SIMULATION = True` toggle to `config.py`

### LLM Integration

- [ ] Implement `simulate_actor_response()` in `engine/actor_simulation.py`
- [ ] Implement `_parse_actor_response()` with strict validation
- [ ] Implement `_heuristic_actor_response()` for fallback
- [ ] Add retry logic with exponential backoff
- [ ] Add error handling for rate limits

### Context Building

- [ ] Use existing `get_diplomatic_context()` from `llm/context_builder.py`
- [ ] Add actor-specific context tailoring
- [ ] Keep context under 300 tokens per actor

### Testing

- [ ] Unit tests for parsing logic
- [ ] Integration tests for consistency
- [ ] Hidden agenda validation tests
- [ ] Mock mode testing (no API calls)
- [ ] Cost tracking per game

---

## SUMMARY TABLE

| Constraint Type | Value | Justification |
|-----------------|-------|---------------|
| **Model** | gemini-2.5-flash-lite | Fastest, cost-effective, 1M context |
| **Temperature** | 0.7 | Balanced creativity and consistency |
| **Processing** | Parallel (ThreadPoolExecutor) | All relevant actors simultaneously |
| **Max Tokens** | 400 per actor | Focused responses |
| **Input Context** | ~950 tokens | Actor state + world context |
| **Actors per Turn** | All relevant | No reduction - all relevant actors respond |
| **Latency** | 3-5 seconds | Parallel processing with ThreadPoolExecutor |
| **Cost per Game** | < $0.01 | Within free tier |
| **Daily Limit** | 1,500 requests | ~400 games/day |
| **Fallback** | Heuristic | If LLM fails, use relationship_uk |
| **Determinism** | Best effort | RNG seed used, but not guaranteed |

---

## CONCLUSION

The Multi-Agent Actor System is **constrained to work within Gemini's free tier** whilst providing:

1. **Realistic**: Each actor responds individually based on hidden state
2. **Fast**: 6-12 seconds per turn (acceptable)
3. **Cheap**: < $0.01 per game
4. **Reliable**: Fallback to heuristics if LLM fails
5. **Testable**: Mock mode for development

**Ready to implement with these constraints.**

