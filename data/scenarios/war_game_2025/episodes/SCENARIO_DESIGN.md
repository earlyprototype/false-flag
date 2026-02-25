# Scenario Design: Hybrid Scripted + Dynamic

## Philosophy

**Turns 1-5: Canonical Setup** → Everyone starts from the same crisis  
**Turn 6+: Dynamic Branching** → YOUR decisions create YOUR unique game

## Why This Works

### The Branch Point (Turn 5)
Turn 5 ends with a **missile launch detection** - a deliberate near-miss in the North Sea. This is the perfect decision catalyst because your response determines the trajectory:

- **Aggressive retaliation** → War escalation path
- **Defensive posture** → Deterrence path  
- **Diplomatic solution** → De-escalation path
- **Backing down** → Capitulation path

### After Turn 5: Emergent Narrative

Gemini generates injects based on:
- ✅ Your previous decisions
- ✅ Current world state (metrics, flags)
- ✅ Realistic scenario patterns (from podcast)
- ✅ Russian strategy (neutralize UK, fracture NATO)
- ✅ UK constraints (limited stocks, uncertain allies)

## What We Mined from Episodes 2-5

### Key Insights

**Russian Strategy:**
- Calibrated strikes (not all-out war)
- Test NATO resolve incrementally
- Exploit UK weaknesses
- Psychological warfare
- Ultimatums with tight deadlines

**UK Reality:**
- Missile stocks: days, not weeks
- Only 2 air patrols for entire UK
- Type-45s: 6 total, typically 2 operational
- Attack subs: 5 total, only 2 deployable
- No Iron Dome (would cost £25bn+)

**Alliance Dynamics:**
- US commitment uncertain (Trump-era)
- NATO divided (France cautious, Poland supportive, Germany diplomatic)
- Coalition of willing possible (Norway, Netherlands, Denmark)

### Scenario Library Contents

We extracted **60+ realistic scenario elements**:

**Naval:** Submarine surfacing, task force positioning, engagement options  
**Infrastructure:** Power stations, gas pipelines, undersea cables  
**Military Targets:** Air bases, naval bases, GCHQ, MOD  
**Civilian:** London strikes, transport chaos  
**Covert Ops:** Pilot assassinations, diplomat exodus  
**Diplomatic:** Russian ultimatums, US ceasefire brokering, NATO consultations  
**UK Responses:** Submarine kills, deep strikes, northern deployment, nuclear signaling

## How Gemini Uses This

### NOT a Script
The scenario library is **inspiration, not a script**. Gemini adapts based on:

**If you authorized strikes:**
- Russia retaliates (gas pipeline? More missiles? Ultimatum?)
- Escalation ladder climbs
- Allies react (some support, some urge restraint)

**If you sought NATO:**
- Article 4 consultation (divided response)
- Coalition of willing forms
- US pressure for ceasefire

**If you focused on defence:**
- Russia tests resolve differently
- Submarine provocations
- Infrastructure sabotage

**If you threatened nuclear:**
- Russian counter-threat
- OR backing down (deterrent works)
- Ally panic

### Maintains Realism

Gemini is constrained by:
- UK military limitations (can't suddenly have 100 missiles)
- Russian objectives (neutralize UK, not invade)
- Alliance politics (US uncertain, Europe divided)
- Time pressure (stocks depleting, public pressure)

## Example Divergent Paths

### Path A: Aggressive Player
**Turn 5 Decision:** "Authorize submarine strikes on Russian task force"

**Turn 6 (Gemini-generated):**
- Russian destroyer sunk, but UK submarine damaged
- Russia issues ultimatum: cease fire or face gas pipeline attack
- Norway offers F-35 support
- US urges restraint

**Turn 7:**
- Depends on Turn 6 decision...

### Path B: Defensive Player
**Turn 5 Decision:** "Hold position, request NATO Article 4"

**Turn 6 (Gemini-generated):**
- NATO consultation (divided: Poland supports, Germany urges diplomacy)
- Russian submarine surfaces near Faslane (nuclear base)
- Public panic, calls for action
- US offers to broker ceasefire

**Turn 7:**
- Depends on Turn 6 decision...

### Path C: Diplomatic Player
**Turn 5 Decision:** "Accept US-brokered ceasefire, withdraw to defensive positions"

**Turn 6 (Gemini-generated):**
- Russia demands UK withdraw from Estonia
- Public outrage ("we backed down!")
- Poland condemns UK weakness
- Domestic stability plummets

**Turn 7:**
- Depends on Turn 6 decision...

## Replayability

Every playthrough after Turn 5 is unique:
- Different decisions → different consequences
- Same decision, different timing → different outcomes
- Emergent narratives based on YOUR strategy

## Comparison to Podcast

**Podcast:** Linear story, predetermined outcome  
**Your Game:** Branching narrative, player agency

**Podcast Value:** Provides realistic scenario patterns  
**Your Game Value:** Applies those patterns dynamically

## Technical Implementation

```
Turn N:
1. Check for episode file (turn_NNN.yaml)
2. If exists → load scripted inject
3. If not exists → generate_inject(world, turn_N, initial_conditions, scenario_library)
4. Gemini adapts scenario_library patterns to current world state
5. Player makes decision
6. World state updates
7. Turn N+1 → repeat
```

## Future Enhancements

When you transcribe Episodes 2-6 fully:
- Add more scenario patterns to library
- Refine escalation sequences
- Add specific dialogue/characterization
- Validate Gemini outputs against podcast realism

But the **core design remains**: Scripted setup (Turns 1-5) → Dynamic branching (Turn 6+)

---

**This design gives you:**
- ✅ Consistent starting scenario (for comparison/discussion)
- ✅ Replayability (different strategies, different outcomes)
- ✅ True agency (your decisions matter)
- ✅ Emergent storytelling (unique narratives)
- ✅ Podcast authenticity (realistic patterns)

**Your game is MORE powerful than the podcast because it's YOUR story.** 🎯

