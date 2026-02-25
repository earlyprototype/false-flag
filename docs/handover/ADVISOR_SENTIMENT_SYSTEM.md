# Advisor Sentiment & Trust System - Implementation Report

**Feature**: Real-time trust updates based on interpersonal interactions  
**Status**: 🔲 Proposed - Not Yet Implemented  
**Priority**: P2 - Medium (After UX fixes)  
**Estimated Effort**: 4-6 hours  

---

## Executive Summary

**Problem Discovered**: During playtesting, the tester attempted to "fire all staff" and noticed advisor trust scores did not change. This revealed that the current trust system only responds to **strategic decision quality**, not **interpersonal treatment**.

**Proposed Solution**: Add real-time sentiment analysis to detect how the player treats individual advisors, updating trust scores based on conversational tone and actions.

**Value Proposition**: Increases roleplay immersion, rewards good leadership, creates meaningful consequences for toxic management behavior.

---

## Current System Analysis

### How Trust Currently Works

**Location**: `engine/narrative_adjudication.py:_update_character_attitudes()`

```python
trust_deltas = {
    "exceptional": +5,
    "good": +2,
    "adequate": 0,
    "poor": -3,
    "catastrophic": -8
}
```

**Triggers**: Only during adjudication phase, based on LLM assessment of decision quality

**Frequency**: Once per turn, affects all UK advisors equally

**What It Tracks**:
- Strategic competence
- Decision-making quality
- Risk assessment ability

**What It Doesn't Track**:
- How you speak to specific advisors
- Whether you follow their advice
- Interpersonal respect/disrespect
- Asking for expertise vs ignoring them
- Threats, praise, or emotional tone

---

## The Gap: Interpersonal Dynamics

### What Should Affect Trust (But Doesn't):

| Player Action | Expected Impact | Current Impact |
|---------------|-----------------|----------------|
| "You're fired!" | -10 trust, possible resignation | Nothing |
| "Thank you, excellent advice" | +2 trust | Nothing |
| Ignore repeated warnings | -3 trust | Nothing |
| Follow advisor's recommendation | +3 trust | Nothing |
| Ask wrong advisor for their domain | No penalty | Nothing |
| Insult advisor personally | -5 trust, morale hit | Nothing |

### Playtest Example
**Player Action**: "I'm firing all my staff"  
**Expected Outcome**: 
- Dramatic pushback
- Major trust loss
- Possible resignations
- Morale collapse among remaining advisors

**Actual Outcome**: Nothing happened

---

## Proposed Solution: Sentiment Tracking System

### Architecture Overview

```
Player sends message to advisor
         ↓
Advisor generates response
         ↓
[NEW] Analyze player message sentiment
         ↓
[NEW] Update advisor-specific trust score
         ↓
[NEW] Check for extreme actions (firing, threats)
         ↓
[NEW] Trigger special responses if needed
         ↓
Continue game
```

### Three Implementation Options

---

## Option 1: Lite Version (Recommended)

**Scope**: Detect only extreme cases  
**Effort**: 2-3 hours  
**LLM Calls**: 0 additional (keyword-based)  

### What It Does:
- Detects explicit firing attempts
- Detects severe insults (keyword matching)
- Triggers advisor pushback/resignation
- Major trust penalty (-10)

### Implementation:

```python
def check_extreme_interaction(player_message: str, advisor_role: str) -> dict:
    """Detect extreme player actions toward advisor.
    
    Returns:
        {
            'severity': 'none' | 'hostile' | 'firing',
            'trust_delta': int,
            'trigger_response': bool
        }
    """
    msg_lower = player_message.lower()
    
    # Firing detection
    fire_keywords = ["fire", "fired", "resign", "resignation", "dismiss", "sack", "remove from post"]
    if any(word in msg_lower for word in fire_keywords):
        return {
            'severity': 'firing',
            'trust_delta': -10,
            'trigger_response': True,
            'response_type': 'resignation_pushback'
        }
    
    # Severe insult detection
    insult_keywords = ["incompetent", "idiot", "useless", "stupid", "moron"]
    if any(word in msg_lower for word in insult_keywords):
        return {
            'severity': 'hostile',
            'trust_delta': -5,
            'trigger_response': True,
            'response_type': 'offense_taken'
        }
    
    return {'severity': 'none', 'trust_delta': 0, 'trigger_response': False}
```

### Special Responses:

```python
RESIGNATION_PUSHBACK = {
    "national_security_advisor": "Prime Minister, I serve at Her Majesty's pleasure, not yours. If you wish to request my resignation, you'll need to go through proper channels. And with respect, this is not the time for internal politics. Now, about this Russian threat...",
    
    "chief_defence_staff": "Prime Minister, I am a serving officer appointed by the Sovereign. You cannot simply 'fire' me. If you've lost confidence in my counsel, we can discuss this after we've resolved the immediate military crisis.",
    
    "foreign_secretary": "Prime Minister, I'm an elected MP and Cabinet member. You'd need the party's support to remove me, and frankly, now is not the time. Can we focus on the Russians?",
    
    # ... etc for each advisor
}
```

### Pros:
✅ Simple, reliable keyword matching  
✅ No additional LLM costs  
✅ Covers the most egregious cases  
✅ Fast to implement  

### Cons:
❌ Misses subtle disrespect  
❌ No positive reinforcement (praise)  
❌ Can be gamed with creative insults  

---

## Option 2: Standard Version (Balanced)

**Scope**: LLM-based sentiment analysis  
**Effort**: 4-6 hours  
**LLM Calls**: 1 per advisor interaction (Flash - cheap)  

### What It Does:
- Analyzes tone of every player message
- Detects respect, neutrality, hostility, threats
- Updates trust incrementally (+1/0/-1/-3)
- Special responses for extreme cases

### Implementation:

```python
def analyze_player_sentiment(
    player_message: str,
    advisor_role: str,
    llm_generate_fn,
    rng: Random
) -> dict:
    """Use LLM to analyze player's conversational tone.
    
    Returns:
        {
            'category': 'respectful' | 'neutral' | 'dismissive' | 'hostile',
            'trust_delta': int,
            'confidence': float
        }
    """
    
    prompt = f"""Analyze the tone of this message from the UK Prime Minister to their {advisor_role}:

"{player_message}"

Classify the tone as:
A) Respectful/Grateful - Thanking, praising, acknowledging expertise, showing appreciation
B) Neutral/Professional - Normal working relationship, factual questions, standard interaction
C) Dismissive/Hostile - Ignoring advice, being rude, confrontational, impatient
D) Insulting/Threatening - Personal attacks, threats to fire, extreme disrespect

Important Context:
- This is a crisis situation, so some urgency/stress is normal
- Focus on respect level, not just tone
- "Fire" or "resign" comments should be category D

Respond with only the letter (A, B, C, or D) and your confidence (High/Medium/Low).
Format: "X - [Confidence]"

Example: "B - High" """

    response = llm_generate_fn(prompt, rng, temperature=0.3, max_tokens=20)
    
    # Parse response
    category_map = {
        "A": {'category': 'respectful', 'trust_delta': +1},
        "B": {'category': 'neutral', 'trust_delta': 0},
        "C": {'category': 'dismissive', 'trust_delta': -1},
        "D": {'category': 'hostile', 'trust_delta': -3}
    }
    
    letter = response.strip()[0].upper()
    result = category_map.get(letter, {'category': 'neutral', 'trust_delta': 0})
    
    # Extract confidence
    result['confidence'] = 'high' if 'high' in response.lower() else 'medium'
    
    return result
```

### Integration Point:

```python
# In agents/conversation.py:handle_player_question()
# After generating advisor response:

for char_id in responding_advisors:
    # ... existing response generation ...
    
    # NEW: Analyze sentiment
    sentiment = analyze_player_sentiment(question, char_info['role'], llm_generate_fn, rng)
    
    # Update trust if using narrative state
    if hasattr(world, 'narrative_state') and world.narrative_state:
        if sentiment['category'] == 'hostile':
            # Trigger special response
            special_response = generate_pushback_for_hostility(char_id, sentiment)
            responses.append((role, special_response))
        
        # Update trust
        world.narrative_state.update_character_attitude(
            char_id,
            trust_delta=sentiment['trust_delta']
        )
```

### Pros:
✅ Catches subtle disrespect  
✅ Provides positive reinforcement  
✅ More nuanced than keywords  
✅ Still relatively cheap (Flash model)  

### Cons:
❌ Adds latency (1 extra LLM call per interaction)  
❌ Not 100% reliable (LLM judgment)  
❌ Might trigger false positives  
❌ Costs add up over time  

---

## Option 3: Premium Version (Full System)

**Scope**: Multi-factor trust tracking  
**Effort**: 8-12 hours  
**LLM Calls**: 1-2 per interaction (consider using Pro)  

### What It Does:
- Sentiment analysis (as in Option 2)
- Tracks if you follow advisor's recommendations
- Tracks if you ask appropriate advisors for their expertise
- Tracks repeated ignoring of warnings
- Compound effects (multiple bad interactions = resignation)
- Morale system (firing one advisor affects all)

### Additional Features:

```python
class AdvisorInteractionHistory:
    """Track detailed interaction patterns with each advisor."""
    
    def __init__(self, advisor_id: str):
        self.advisor_id = advisor_id
        self.recommendations_given = []
        self.recommendations_followed = 0
        self.recommendations_ignored = 0
        self.warnings_given = []
        self.warnings_ignored = 0
        self.sentiment_history = []
        self.expertise_appropriate_asks = 0
        self.expertise_inappropriate_asks = 0
    
    def calculate_trust_modifier(self) -> int:
        """Calculate trust based on full interaction history."""
        
        # Base: Sentiment average
        base = sum(self.sentiment_history[-10:]) / len(self.sentiment_history[-10:])
        
        # Bonus: Following advice
        if self.recommendations_given:
            follow_rate = self.recommendations_followed / self.recommendations_given
            base += follow_rate * 5
        
        # Penalty: Ignoring warnings
        if self.warnings_ignored >= 3:
            base -= 5
        
        # Bonus: Asking for their expertise
        if self.expertise_appropriate_asks > self.expertise_inappropriate_asks:
            base += 2
        
        return int(base)
```

### Resignation System:

```python
def check_resignation_conditions(advisor_id: str, narrative_state: NarrativeState) -> bool:
    """Determine if advisor should resign."""
    
    character = narrative_state.characters.get(advisor_id)
    if not character:
        return False
    
    # Resignation triggers:
    # 1. Trust below 20
    if character.trust < 20:
        return True
    
    # 2. Three consecutive hostile interactions
    recent_sentiments = get_recent_sentiments(advisor_id, count=3)
    if all(s < -1 for s in recent_sentiments):
        return True
    
    # 3. Explicit firing attempt
    if narrative_state.flags.get(f"{advisor_id}_fired"):
        return True
    
    return False
```

### Pros:
✅ Extremely immersive  
✅ Rewards good leadership  
✅ Complex emergent behaviors  
✅ High replay value  

### Cons:
❌ Significant development time  
❌ Complex to balance  
❌ Might frustrate casual players  
❌ Higher LLM costs  

---

## Recommended Implementation: **Option 2 (Standard)**

### Rationale:
1. **Addresses the bug**: Player's "firing" action now has consequences
2. **Balanced effort**: 4-6 hours is reasonable for the value added
3. **Scalable**: Can upgrade to Option 3 later if desired
4. **Cost-effective**: Flash model is cheap, adds ~$0.05 per full playthrough
5. **Immersive**: Adds meaningful interpersonal dynamics without overcomplicating

### Phased Rollout:

**Phase 1** (2 hours): Lite version (keyword detection)
- Implement firing detection
- Add resignation pushback responses
- Basic trust penalties

**Phase 2** (3 hours): Add LLM sentiment
- Implement `analyze_player_sentiment()`
- Integrate into conversation flow
- Add trust updates

**Phase 3** (2 hours): Polish & Balance
- Tune trust delta values
- Add special responses for each category
- Playtest and adjust thresholds

---

## Integration Points

### Files to Modify:

1. **`agents/conversation.py`**
   - Add `analyze_player_sentiment()` function
   - Integrate sentiment check into `handle_player_question()`
   - Add special response generation for hostile interactions

2. **`models/narrative_state.py`**
   - Add `interaction_history` tracking (optional, for Option 3)
   - Ensure `update_character_attitude()` handles sentiment deltas

3. **`data/scenarios/.../initial_conditions.yaml`**
   - Add resignation pushback responses for each advisor

4. **`llm/prompts.py`**
   - Add sentiment analysis prompt template

### Testing Requirements:

```python
# Unit tests needed:
def test_sentiment_analysis_firing():
    assert analyze_sentiment("You're fired!") == {'category': 'hostile', 'trust_delta': -3}

def test_sentiment_analysis_praise():
    assert analyze_sentiment("Excellent advice, thank you") == {'category': 'respectful', 'trust_delta': +1}

def test_sentiment_analysis_neutral():
    assert analyze_sentiment("What are our options?") == {'category': 'neutral', 'trust_delta': 0}

def test_resignation_attempt_triggers_pushback():
    # Player says "fire National Security Advisor"
    # Should get special pushback response
    # Should apply -10 trust penalty
```

---

## Impact Assessment

### Gameplay Impact:
- **Minor** for normal players (most interactions neutral)
- **Major** for roleplay-focused players
- **Prevents** toxic management behavior
- **Rewards** respectful leadership

### Performance Impact:
- +1 LLM call per advisor interaction (Flash model)
- ~50ms latency per interaction
- Minimal memory overhead

### Cost Impact:
- Flash: ~$0.000075 per analysis
- ~20-30 advisor interactions per game
- **Total: ~$0.002 per full playthrough** (negligible)

---

## Success Criteria

### Minimum Viable Implementation:
✅ Firing attempts trigger pushback  
✅ Major trust penalty applied  
✅ System doesn't break normal gameplay  

### Full Success:
✅ All sentiment categories detected accurately (>80% precision)  
✅ Trust deltas feel balanced  
✅ Players notice and appreciate the feature  
✅ Special responses feel natural and in-character  
✅ No false positives on neutral interactions  

---

## Risks & Mitigation

### Risk: False Positives
**Example**: "This situation is a disaster" flagged as insulting the advisor  
**Mitigation**: Tune prompt to focus on interpersonal tone, not situation assessment

### Risk: Gaming the System
**Example**: Player uses creative insults that bypass detection  
**Mitigation**: Accept this as okay - player is being creative, not toxic

### Risk: Annoying Power Users
**Example**: Speedrunners annoyed by sentiment checks  
**Mitigation**: Make it optional via config flag

### Risk: LLM Costs Scaling
**Example**: 100 interactions = $0.75 in costs  
**Mitigation**: Very unlikely in practice; if needed, add rate limiting

---

## Alternative: Don't Implement

### Arguments Against Implementation:

1. **Working as Designed**: The current system tracks strategic competence, not interpersonal skills. This is intentional - you're the PM, they can't quit.

2. **Realism**: In reality, Cabinet members can't be easily fired mid-crisis. The current system is actually more realistic.

3. **Scope Creep**: This adds complexity to an already complex system. Focus on core gameplay first.

4. **Edge Case**: The "fire everyone" scenario is a joke test case, not real gameplay.

5. **Cost/Benefit**: 4-6 hours of dev time for a feature most players won't notice.

**Counter-Arguments**:
- Adds immersion and replay value
- Relatively cheap to implement (Option 1 is 2 hours)
- Makes conversations more meaningful
- Fun test case revealed a legitimate design gap

---

## Recommendation

**Implement Option 1 (Lite) immediately** (2 hours)
- Fixes the playtest bug
- Adds minimal complexity
- No additional LLM costs
- Good enough for Beta

**Upgrade to Option 2 (Standard) post-launch** (4 hours)
- If players request it
- If analytics show it adds value
- After core UX issues resolved

**Consider Option 3 (Premium) for DLC/sequel**
- If game is successful
- If community wants deeper simulation
- As part of "hardcore management" mode

---

## Appendix: Example Interactions

### Scenario 1: Firing Attempt
```
Player: "National Security Advisor, you're fired. You've been useless."

[Sentiment Analysis: Category D - Hostile, -3 trust]
[Special Response Triggered]

National Security Advisor: "Prime Minister, I serve at Her Majesty's pleasure, 
not yours. If you've lost confidence in my counsel, we can discuss this through 
proper channels after we've resolved the immediate crisis. And with respect, 
your characterization is both incorrect and unhelpful. Now, regarding the Russian 
threat..."

[Trust: 75 → 65]
[Flag: nsa_firing_attempted = True]
```

### Scenario 2: Respectful Interaction
```
Player: "Thank you, NSA. That's exactly the intelligence I needed. Your analysis 
has been invaluable."

[Sentiment Analysis: Category A - Respectful, +1 trust]

National Security Advisor: "Thank you, Prime Minister. That's what we're here for."

[Trust: 75 → 76]
```

### Scenario 3: Neutral Professional
```
Player: "What are our options for responding to this submarine incursion?"

[Sentiment Analysis: Category B - Neutral, 0 trust]

Chief of Defence Staff: "Prime Minister, we have three courses of action..."

[Trust: 80 → 80]
```

---

**Report Compiled**: November 8, 2025  
**Status**: Awaiting approval for implementation  
**Next Step**: Prioritize against UX bug fixes  
**Estimated ROI**: Medium-High (good feature for replay value)

