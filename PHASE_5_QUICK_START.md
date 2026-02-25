# Phase 5: Multi-Agent Actors + Intelligence - Quick Start

## ✅ What Was Built (6-8 hours)

**Multi-Agent State Actor System:**
- 5 individual countries (USA, France, Germany, Poland, Russia)
- Each with hidden motivations, secret agendas, and constraints
- LLM-driven responses to player actions
- Individual relationship tracking

**Intelligence Briefing System:**
- Economic indicators (maps to domestic stability)
- Diplomatic SIGINT (maps to alliance cohesion + actor states)
- Military posture (maps to escalation risk)
- Displays in Immersive/Emergent modes only

**New Player Commands:**
- `/intel` - List available countries
- `/intel usa` - Detailed US assessment
- `/intel fra` - Detailed France assessment (reveals patterns)

---

## How To Test

### 1. Start New Game in Immersive Mode

```powershell
python wargame.py play --play-mode immersive
```

**What to watch for:**
- ✅ "Multi-agent actor system initialized" message at start
- ✅ Intelligence briefing appears after Turn 1 inject (before discussion)
- ✅ "INTERNATIONAL REACTIONS" section after making decisions

### 2. Make NATO-Related Decision

```
Decision> I invoke NATO Article 4 emergency consultations and request
allied intelligence sharing
```

**Expected output:**
```
═══════════════════════════════════════════════════════════
INTERNATIONAL REACTIONS
═══════════════════════════════════════════════════════════

United States of America: (+5)
  "The United States supports Article 4 consultations. We will
   coordinate closely with UK on intelligence sharing."

French Republic: (-2)
  "France supports diplomatic dialogue. We must not rush into
   military commitments without exhausting all options."

Federal Republic of Germany: (+2)
  "Germany agrees consultations are appropriate. We will participate
   in NATO discussions."

Republic of Poland: (+15)
  "Poland fully supports UK's invocation of Article 4. We stand
   ready to contribute forces and intelligence."
```

### 3. Check Intelligence Briefing (Turn 2+)

**After inject briefing, before discussion:**
```
═══════════════════════════════════════════════════════════
         INTELLIGENCE SUMMARY - Turn 2, 19:00
         Classification: TOP SECRET - EYES ONLY
═══════════════════════════════════════════════════════════

ECONOMIC INDICATORS (GCHQ Financial Intelligence):
• FTSE 100: -8.2% (significant sell-off...)
• Sterling: £1 = $1.18 (-3.4%)

DIPLOMATIC SIGNAL INTELLIGENCE (MI6 Cable Traffic):
• Washington-London hotline: Active coordination
• Paris-Berlin encrypted comms: 340% above baseline (UNUSUAL)
• Polish PM attempted UK PM call x3 (eager to coordinate)

MILITARY POSTURE ASSESSMENT (Northwood Joint Ops):
• Russian Northern Fleet: Maintaining aggressive posture
...
```

### 4. Use /intel Command During Discussion

```
Discussion> /intel

Available countries for intelligence assessment:

  /intel usa - United States of America
  /intel fra - French Republic
  /intel deu - Federal Republic of Germany
  /intel pol - Republic of Poland
  /intel rus - Russian Federation

Discussion> /intel fra

═══════════════════════════════════════════════════════════
         DETAILED ASSESSMENT - French Republic
         Turn 2
═══════════════════════════════════════════════════════════

Relationship Trend: DECLINING ↘
Current Assessment: 43/100

Recent Indicators:
• Mixed signals in diplomatic communications
• Intelligence sharing: limited
• Some hesitation in public statements

Recent Actions:
• Response to UK action (T1)

Analyst Assessment: Unreliable. May undermine UK position diplomatically.
═══════════════════════════════════════════════════════════
```

---

## What To Look For

### ✅ Success Indicators

1. **Actor Differentiation:**
   - Poland always enthusiastic (+10 to +15)
   - USA conditional (+2 to +5)
   - France lukewarm (-5 to 0)
   - Germany hesitant (+1 to +3)

2. **Hidden Agenda Hints:**
   - Intelligence shows "Paris-Berlin encrypted comms spike"
   - France public: "We support UK" but actions say otherwise
   - Over 3-4 turns, pattern emerges

3. **Intelligence Accuracy:**
   - Economic indicators reflect stability level
   - Diplomatic SIGINT reflects alliance cohesion
   - Military posture reflects escalation risk

4. **Aggregate Alliance Cohesion:**
   - Calculated from individual actors
   - USA weighted 2x, Germany 1.5x, France 1x, Poland 0.5x
   - Updates after each decision

### ❌ Potential Issues

1. **Actor System Not Loaded:**
   - Error: "Warning: Could not load actor system"
   - Fix: Check `data/state_actors.yaml` exists

2. **No Intelligence Briefing:**
   - Playing Classic mode (only shows in Immersive/Emergent)
   - Turn 1 (only shows Turn 2+)

3. **LLM Errors:**
   - Actor responses fallback to generic text
   - Check LLM model settings with `/llm`

---

## Testing Scenarios

### Scenario 1: Discover France's Hidden Agenda

**Turns 1-5:** Make various NATO decisions
**Expected:** 
- Turn 1: France says "European solidarity"
- Turn 2: Intel shows "Paris-Berlin comms spike"
- Turn 3: France relationship declining despite supportive words
- Turn 4: Intel shows "French Ambassador met Russian counterpart"
- Turn 5: Player deduces France is undermining UK

### Scenario 2: Cultivate Polish Alliance

**Actions:** 
- Request Polish forward deployment
- Share intelligence with Poland
- Publicly thank Polish support

**Expected:**
- Poland relationship: 85 → 90 → 95
- Intelligence shows: "Polish PM eager to coordinate"
- Poland offers military assets unprompted

### Scenario 3: Compare Classic vs Immersive

**Test A:** Play Turn 1 in Classic mode
- See: "alliance_cohesion: 40"
- See: Metrics table

**Test B:** Play Turn 1 in Immersive mode  
- See: Intelligence briefing with hints
- See: Individual actor responses
- See: No raw numbers

---

## Quick Commands Reference

### During Discussion Phase:
- `/status` - Show current situation
- `/intel` - List available countries for assessment
- `/intel <code>` - Detailed assessment (usa, fra, deu, pol, rus)
- `/menu` - Show all commands
- `/advise` - Get all advisor opinions
- `/decide` - Make decision (ends discussion)

### Intelligence Command:
```
/intel          # Show available actors
/intel usa      # US detailed assessment
/intel fra      # France detailed assessment
/intel deu      # Germany detailed assessment
/intel pol      # Poland detailed assessment
/intel rus      # Russia detailed assessment (adversary)
```

---

## Files Created

1. `models/state_actors.py` - Actor classes
2. `data/state_actors.yaml` - Actor definitions with hidden agendas
3. `engine/intelligence.py` - Intelligence briefing generation
4. `analysis/PHASE_5_MULTI_AGENT_COMPLETE.md` - Full documentation

## Files Modified

1. `models/world.py` - Added `actor_system` field
2. `engine/narrative_adjudication.py` - Added `generate_actor_responses()`
3. `cli/main.py` - Actor initialization, intel display, /intel command

---

## Cost Impact

**Per Turn with Multi-Agent:**
- 4 LLM calls for actor responses (USA, FRA, DEU, POL)
- Using Flash: ~$0.08 per turn
- Using Pro: ~$0.40 per turn

**Recommendation:** Use Flash for actor responses (adequate quality)

---

## Next Steps After Testing

1. ✅ Verify actor differentiation (USA ≠ Poland ≠ France)
2. ✅ Confirm intelligence hints are discoverable
3. ✅ Check aggregate alliance cohesion calculation
4. ✅ Test `/intel` command for all actors
5. ❌ **NOT YET:** Save/load persistence (actors reset on load)

---

## Need Help?

**Issue:** Actor system not loading
**Fix:** Check terminal for error message, verify `data/state_actors.yaml` exists

**Issue:** No intelligence briefing
**Fix:** Must be Immersive/Emergent mode, Turn 2+

**Issue:** Generic actor responses
**Fix:** LLM might be failing, check `/llm` settings

**Issue:** All actors respond the same
**Fix:** Check `data/state_actors.yaml` has different motivations

---

**Status:** READY FOR PLAYTESTING ✅
**Estimated Test Time:** 30-45 minutes for full validation

