# PLAYTEST FEEDBACK REPORT
**Session Date**: Saturday, November 8, 2025  
**Tester**: Primary Developer  
**Build**: Dynamic Narrative System - Phase 3 Complete  
**Scenario Tested**: Fast Start Mode, Turn 1-4+  

---

## Executive Summary

First playtest of the Dynamic Narrative System revealed the core mechanics are functioning, but significant UX/presentation issues need addressing before wider testing. The narrative selection system worked correctly, but gameplay flow, text formatting, and advisor interaction patterns require immediate attention.

**Status**: 🟡 **Needs Polish** - Core systems operational, presentation layer needs work

---

## 🚨 CRITICAL ISSUES (Block Gameplay)

### Issue #7: Decision Cancellation Flow
**Priority**: P0 - Critical  
**Status**: 🔴 Blocks natural gameplay flow  

**Problem**:  
When player cancels a decision after receiving advisor pushback, the game loop returns to the START of the turn (showing briefing again) instead of returning to the discussion phase.

**Expected Behavior**:  
Cancel → Return to discussion phase → Player can ask more questions → Make new decision

**Actual Behavior**:  
Cancel → Return to turn start → Briefing shown again → Entire turn restarts

**Technical Cause**:  
`continue` statement at line 1314 of `cli/main.py` restarts outer turn loop from line 587, which includes briefing phase.

**Fix Required**:  
Restructure turn loop to separate briefing (run once) from discussion/decision (repeatable loop).

---

### Issue #14: Advisor Identity Collapse
**Priority**: P0 - Critical  
**Status**: 🔴 Breaks roleplay immersion  

**Problem**:  
Player cannot consistently address specific advisors. Multiple advisors merge into a single voice, breaking the cabinet meeting simulation.

**Example**:  
Player asks "What does the Foreign Secretary think?" → Response comes from "Intelligence Coordinator"

**Technical Cause**:  
Likely issue in advisor routing logic in `agents/conversation.py:handle_player_question()`. The LLM may not be correctly identifying which advisor should respond, or the routing keywords are insufficient.

**Fix Required**:  
1. Review advisor routing keywords in `handle_player_question()`
2. Add explicit addressing syntax: `/ask foreign_sec <question>`
3. Improve LLM prompt to maintain character identity consistency

---

## ⚠️ HIGH PRIORITY (UX Problems)

### Issue #1: Markdown Formatting Leakage in Advisor Responses
**Priority**: P1 - High  
**Status**: 🟡 Breaks visual polish  

**Problem**:  
Advisor responses contain raw markdown formatting (`**bold**`, `*italic*`) instead of using terminal color codes.

**Example**:  
```
Intelligence Coordinator: We need to **immediately** gather evidence...
```

**Expected**:  
```
Intelligence Coordinator: We need to [bold]immediately[/bold] gather evidence...
```

**Fix Required**:  
1. Add markdown-to-rich formatting conversion function
2. Apply to all LLM-generated advisor text before display
3. Alternative: Instruct LLM in prompts to avoid markdown

---

### Issue #2: General Markdown Leakage Throughout
**Priority**: P1 - High  
**Status**: 🟡 Widespread formatting issue  

**Problem**:  
Markdown formatting appears in multiple contexts beyond advisor responses (injects, diplomatic conversations, etc.)

**Fix Required**:  
Implement global text sanitization/conversion pipeline for all LLM outputs.

---

### Issue #5: Duplicate Player Input on Diplomatic Calls
**Priority**: P1 - High  
**Status**: 🟡 Breaks conversation flow  

**Problem**:  
When making a diplomatic call, the player's input is echoed back to the screen unnecessarily before the diplomat's response.

**Screenshot Evidence**: Provided by tester showing:
```
Prime Minister: have you tried sobriety? Sorry, long day...
Taoiseach: [response begins]
```

**Fix Required**:  
Remove echo of player input in `engine/diplomacy.py` diplomatic call display logic (similar to how it was fixed for decision phase).

---

### Issue #9: Stochastic Inject Meta-Header
**Priority**: P1 - High  
**Status**: 🟡 Breaks immersion  

**Problem**:  
When dynamic inject generation activates (Turn 4+), injects display with meta-header: `[Stochastically generated inject]`

**Current**:  
```
[Stochastically generated inject]

BREAKING: Russian submarine spotted...
```

**Expected**:  
```
A new day dawns on a highly uncertain future for the UK...

BREAKING: Russian submarine spotted...
```

**Fix Required**:  
Replace debug header with narrative flavor text in `engine/events.py` or inject display logic.

---

### Issue #13: Score Display Timing
**Priority**: P1 - High  
**Status**: 🟡 Confuses causality  

**Problem**:  
Metric changes display AFTER the next turn's inject text, making it appear that the Russian response (not the player's decision) caused the metric changes.

**Current Flow**:  
```
[Player makes decision]
[Adjudication reasoning]
[Turn advances]
[Russian inject: "Russia deploys more submarines"]
[Metrics table shows changes]
```

**Expected Flow**:  
```
[Player makes decision]
[Adjudication reasoning]
[Metrics table shows immediate impact of decision]
[Turn advances]
[Russian inject: "Russia deploys more submarines"]
```

**Fix Required**:  
Move metrics display to immediately after adjudication reasoning, before turn increment and next inject.

---

## 🎨 MEDIUM PRIORITY (Polish)

### Issue #3: Critical Advisory Graphic Design
**Priority**: P2 - Medium  
**Status**: 🟢 Cosmetic  

**Problem**:  
The Critical Advisory warning display has too many warning symbols and poor text wrapping, making it cluttered and hard to read.

**Current**:  
```
⚠️ ⚠️ ⚠️ ⚠️ CRITICAL ADVISORY ⚠️ ⚠️ ⚠️ ⚠️
Diplomatic Lead: While the Prime Minister's instruction to engage President Trump is absolutely critical for securing US commitment, this decision critically omits several...
[Text continues without wrapping]
```

**Expected**:  
```
╭─────────────────────────────────────────────────╮
│  ⚠️  CRITICAL ADVISORIES                         │
╰─────────────────────────────────────────────────╯

Diplomatic Lead:
  While the Prime Minister's instruction to engage
  President Trump is absolutely critical...
  
  → RECOMMENDATION: Initiate concurrent diplomatic...
```

**Fix Required**:  
1. Reduce warning symbols (1-2 max)
2. Add proper text wrapping with Rich library
3. Use panel/box formatting for clarity

---

### Issue #4: General Text Formatting & Readability
**Priority**: P2 - Medium  
**Status**: 🟢 Cosmetic  

**Problem**:  
General formatting issues throughout game text reduce readability. See screenshot provided by tester showing inconsistent spacing, line breaks, and visual hierarchy.

**Fix Required**:  
Comprehensive formatting audit and standardization using Rich library components.

---

### Issue #15: Private Conversation Context Leakage
**Priority**: P2 - Medium  
**Status**: 🟡 Breaks realism  

**Problem**:  
When player attempts to have a "private" conversation with one advisor (e.g., Intelligence Coordinator), other advisors respond as if they overheard.

**Example**:  
Player: "Intelligence Coordinator, can we discuss setting up a false flag operation?"  
Response: "Diplomatic Lead: Prime Minister, I must object to this course of action!"

**Expected**:  
Only the Intelligence Coordinator responds unless the player explicitly broadens the conversation.

**Fix Required**:  
1. Implement conversation scoping in `agents/conversation.py`
2. Track who is "in" the current conversation
3. Only provide transcript to advisors who are addressed or involved
4. Add `/private <advisor>` command for sensitive discussions

---

## 🤔 DESIGN QUESTIONS / FEATURE REQUESTS

### Issue #6: Bilateral Relationship Metric
**Type**: Feature Request  
**Priority**: P3 - Nice to Have  

**Question**:  
Should we add individual relationship scores with each country, separate from overall Alliance Cohesion?

**Example**:  
```
Alliance Cohesion: 75/100 (NATO overall)
USA Relationship: 80/100
Ireland Relationship: 45/100
France Relationship: 65/100
```

**Rationale**:  
- More granular diplomatic gameplay
- Ireland interaction felt flat - no way to influence them
- Creates interesting dynamics where you might have strong NATO cohesion but weak bilateral ties
- Rare strong/weak relationships could unlock unique events

**Complexity Assessment**: Medium  
**Value Assessment**: High (adds meaningful player agency)

**Recommendation**: ✅ Implement as part of diplomatic system enhancement

---

### Issue #8: Amend Decision Option
**Type**: Feature Request  
**Priority**: P3 - Nice to Have  

**Question**:  
Should we add an explicit "Amend Decision" option in the decision phase menu?

**Current Flow**:  
1. Enter decision
2. Receive pushback
3. Options: Proceed / Cancel (returns to discussion)

**Proposed Flow**:  
1. Enter decision
2. Receive pushback
3. Options: Proceed / Amend / Cancel

**Amend Behavior**:  
Prompts for modified decision immediately without returning to discussion.

**Assessment**:  
Minor UX improvement, easy to implement.

**Recommendation**: ✅ Implement (quick win)

---

### Issue #10: International Developments Briefing
**Type**: Feature Request  
**Priority**: P2 - Medium  

**Question**:  
Should we add a "newspaper front page" style briefing at the start of each turn showing international developments?

**Concept**:  
```
═══════════════════════════════════════════════════════
        THE TIMES  |  Monday, October 6, 2025
═══════════════════════════════════════════════════════

CHINA CALLS FOR RESTRAINT IN NORTH ATLANTIC CRISIS
Beijing urges diplomatic solution as tensions mount...

GERMAN CHANCELLOR UNDER PRESSURE OVER GAS SUPPLIES
Coalition fractures as Green Party demands action...

US CONGRESSIONAL HAWKS PUSH FOR ARTICLE 5 ACTIVATION
Senate Armed Services Committee holds emergency session...
═══════════════════════════════════════════════════════
```

**Purpose**:  
- Provides context for narrative truth (subtle hints)
- Shows international reactions to player's decisions
- Increases immersion and realism

**Narrative System Integration**:  
Headlines would vary based on which narrative is active:
- **Russia Aggression**: Headlines focus on Russian military buildup
- **China Proxy War**: Subtle hints about Chinese financial/diplomatic activity

**Recommendation**: ✅ High value for narrative system, implement after UX fixes

---

### Issue #11: `/advise` Command Arguments
**Type**: Feature Request  
**Priority**: P3 - Nice to Have  

**Question**:  
Can we append arguments to `/advise` command for response formatting?

**Examples**:  
- `/advise concise` - Brief responses (1-2 sentences each)
- `/advise bullets` - Bullet point recommendations only
- `/advise military` - Only military advisors respond
- `/advise diplomatic` - Only diplomatic advisors respond

**Assessment**:  
Easy to implement via prompt engineering. Add parsing for arguments in command handler.

**Recommendation**: ✅ Implement `/advise concise` immediately (addresses verbosity issue)

---

### Issue #12: Advisor Attitude Scoring Transparency
**Type**: Information Request  
**Priority**: P4 - Documentation  

**Question**:  
How are advisor attitudes/trust scores calculated?

**Current System** (from `engine/narrative_adjudication.py`):  
```python
trust_deltas = {
    "exceptional": +5,
    "good": +2,
    "adequate": 0,
    "poor": -3,
    "catastrophic": -8
}
```

Trust scores stored in `narrative_state.characters[char_id].trust` (0-100 scale).

**Affects**:  
- Advisor tone in responses
- Likelihood of pushback
- Character relationship descriptions in narrative

**Action Required**:  
Add `/status advisors` command to show current trust levels and relationship summaries.

---

## 🎮 POSITIVE FINDINGS

### ✅ What Worked Well

1. **Narrative Selection System**  
   - Menu displayed correctly
   - Selection persisted through game
   - No crashes related to narrative storage

2. **Core Gameplay Loop**  
   - Turn progression functional
   - Phase transitions clear
   - No game-breaking bugs in main path

3. **Diplomatic System**  
   - Ireland call worked (despite formatting issues)
   - Diplomat personality came through
   - Conversation flow natural

4. **Advisor Interaction**  
   - Despite identity collapse issues, individual advisor expertise was evident
   - Intelligence Coordinator provided good context
   - Critical concerns system triggered appropriately

5. **Stochastic Generation**  
   - Dynamic injects generated successfully at Turn 4+
   - Content quality was appropriate
   - Transition message displayed correctly

---

## 📊 TESTING METRICS

**Turns Completed**: 4+ (Fast Start Mode)  
**Commands Used**: `/call`, `/advise`, `/menu`, `/resources`  
**Critical Paths Tested**: Briefing → Discussion → Decision (with cancellation) → Adjudication  
**Diplomatic Interactions**: 1 (Ireland - Taoiseach)  
**Decision Cancellations**: Multiple (triggered Issue #7)  

---

## 🔧 RECOMMENDED FIX ORDER

### Phase 1: Critical Fixes (Required for next playtest)
1. **Issue #7**: Decision cancellation flow (2-3 hours)
2. **Issue #14**: Advisor identity/addressing system (3-4 hours)
3. **Issue #13**: Score display timing (30 minutes)

### Phase 2: High Priority UX (Should do before wider testing)
4. **Issue #1/#2**: Markdown formatting cleanup (1-2 hours)
5. **Issue #5**: Remove duplicate input echo (15 minutes)
6. **Issue #9**: Stochastic inject header (15 minutes)

### Phase 3: Polish & Features (Nice to have)
7. **Issue #3**: Critical Advisory formatting (1 hour)
8. **Issue #8**: Amend decision option (30 minutes)
9. **Issue #11**: `/advise` arguments (1 hour)
10. **Issue #4**: General formatting audit (2-3 hours)

### Phase 4: New Features (Future sprint)
11. **Issue #6**: Bilateral relationship metric system (4-6 hours)
12. **Issue #10**: International developments briefing (6-8 hours)
13. **Issue #12**: Advisor status command (1 hour)
14. **Issue #15**: Private conversation system (3-4 hours)

---

## 🎯 SUCCESS CRITERIA FOR NEXT PLAYTEST

**Must Have** (Phase 1 + 2 complete):
- ✅ Decision cancellation returns to discussion phase
- ✅ Can address specific advisors reliably
- ✅ No markdown formatting visible to player
- ✅ Scores display immediately after decision
- ✅ No duplicate text echoing

**Nice to Have** (Phase 3):
- ✅ Clean Critical Advisory presentation
- ✅ `/advise concise` command functional
- ✅ Professional text formatting throughout

**Future Enhancements** (Phase 4):
- 🔲 Bilateral relationship tracking
- 🔲 Newspaper-style briefings
- 🔲 Private conversation system

---

## 📝 NOTES

### On Narrative System Testing
The tester did not explicitly report on whether different narrative selections (Russia Aggression vs China Proxy War) produced different diplomatic behaviors, as this was the primary goal of Phase 3 implementation. **Follow-up testing specifically targeting narrative differentiation is required.**

### On LLM Tone
Player's informal/humorous tone during diplomatic call ("have you tried sobriety?") was handled appropriately by the Irish Taoiseach character. LLM maintained character dignity while responding to unusual input. **Personality system working as intended.**

### On Game Difficulty
No feedback on whether Fast Start mode's compressed timeline felt appropriately challenging. **Pacing assessment needed in future tests.**

---

## 🔄 NEXT ACTIONS

1. **Prioritize fixes** with developer
2. **Create implementation tickets** for Phase 1 critical issues
3. **Schedule follow-up playtest** after Phase 1+2 complete
4. **Design bilateral relationship system** (Issue #6)
5. **Prototype newspaper briefing** (Issue #10)

---

**Report Compiled By**: AI Assistant  
**Target Audience**: Development Team  
**Next Review**: After Phase 1 fixes implemented

