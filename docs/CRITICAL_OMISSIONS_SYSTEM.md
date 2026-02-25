# Critical Omissions Check System

## Overview

The Critical Omissions Check is a strategic safety net that triggers after you make a decision. Your advisors scan for **catastrophic gaps** in your decision-making - critical actions you haven't taken that could lead to disaster.

This is different from the existing pushback system:
- **Pushback**: Evaluates what you're *doing* (is this action risky?)
- **Critical Check**: Evaluates what you're *NOT doing* (have you forgotten something crucial?)

## When It Triggers

After you enter a decision and see the interpretation, **before adjudication**, if any advisor detects a critical omission, you'll see:

```
⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠
CRITICAL ADVISORY
⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠

Foreign Secretary: Prime Minister, we're deploying significant military 
assets into contested waters, but we haven't engaged NATO or the United 
States. If this escalates, we'll be facing Russia alone. I strongly 
recommend we invoke Article 4 or at minimum secure US coordination 
BEFORE we deploy.

   → RECOMMENDATION: Invoke NATO Article 4 consultations before deployment

───────────────────────────────────────────────────────────────────────────────

What would you like to do?
  [1] Modify my decision
  [2] Return to discussion phase
  [3] Proceed anyway (acknowledge the risks)

Choose [1-3]:
```

## Threshold: HIGH

The system has a **high threshold** - it only flags gaps that could lead to:

### Catastrophic Outcomes
- Loss of NATO/alliance support (military isolation)
- Violations of international law (legal catastrophe)
- Catastrophic escalation with Russia (nuclear risk)
- Domestic political collapse (government falls)
- Military disaster (forces unprepared/unsupported)

### What IS Flagged (Examples)
✅ Military deployment WITHOUT engaging NATO/US coordination
✅ Offensive action WITHOUT legal authority under international law
✅ Major crisis WITHOUT public statement (domestic panic risk)
✅ Escalation WITHOUT ally consultation (Article 5 denial risk)
✅ Committing forces WITHOUT securing logistics/support

### What is NOT Flagged
❌ Suboptimal tactics (those are minor concerns)
❌ Missed opportunities (those aren't catastrophic)
❌ Policy disagreements (those are normal pushback)
❌ Minor procedural gaps (those are acceptable)

## Which Advisors Check

Five key advisors scan for omissions in their domains:

| Advisor | Checks For |
|---------|-----------|
| **Foreign Secretary** | Alliance coordination, diplomatic channels, Article 4/5 |
| **Chief of Defence Staff** | Military readiness, force protection, operational feasibility |
| **Home Secretary** | Domestic security, public safety, civil messaging |
| **Attorney General** | Legal authority, international law, rules of engagement |
| **National Security Advisor** | Strategic coordination, intelligence, overall risk |

## Player Response Options

When a critical advisory appears, you have **3 choices**:

### [1] Modify My Decision
- Returns you to the decision input prompt
- Keep the interpretation in mind
- Enter a **modified** decision addressing the concern

### [2] Return to Discussion Phase
- Go back to asking advisors questions
- Gather more information
- Ask specifically about the concern raised
- Then come back to `/decide` when ready

### [3] Proceed Anyway
- Acknowledge the risks
- The decision goes through as-is
- Advisors have warned you
- Consequences will follow in adjudication

## Example Flow

```
Decision>: deploy HMS Queen Elizabeth to GIUK gap

INTERPRETATION:
[LLM describes naval deployment, timeline, forces involved...]

⚠  CRITICAL ADVISORY ⚠

Foreign Secretary: Prime Minister, we're deploying our carrier strike group 
into contested waters near Russian naval forces, but we haven't coordinated 
with NATO or secured US support. If shooting starts, we'll be isolated and 
likely unable to invoke Article 5 effectively.

   → RECOMMENDATION: Engage NATO Secretary General and US President before deployment

Attorney General: Additionally, PM, we haven't established clear rules of 
engagement or legal authority under international law. If our forces engage 
Russian units, we need documented self-defence justification or UN mandate.

   → RECOMMENDATION: Secure Cabinet approval for rules of engagement

───────────────────────────────────────────────────────────────────────────────

What would you like to do?
  [1] Modify my decision
  [2] Return to discussion phase
  [3] Proceed anyway (acknowledge the risks)

Choose [1-3]: 1

Decision cancelled. Please enter a modified decision.

Decision>: deploy HMS Queen Elizabeth to GIUK gap AND invoke NATO Article 4 
consultations AND establish rules of engagement with Cabinet approval

INTERPRETATION:
[LLM interprets modified decision with NATO coordination and legal framework...]

[No critical concerns - advisors are satisfied]

Proceed with this decision? [Y/n]:
```

## Design Rationale

### Why This Feature Exists

1. **Catches Genuine Strategic Errors**: Easy to forget Article 4 in the heat of crisis
2. **Makes Advisors Feel Alive**: They're watching your back, not just reactive
3. **Adds Dramatic Tension**: That moment of "oh shit, they're right"
4. **Improves Player Learning**: Highlights what actually matters strategically
5. **Fits COBRA Vibe**: Cabinet pushing back at critical moments

### Why High Threshold

- **Rare = Impactful**: If it triggers every turn, it becomes noise
- **Respects Player Agency**: Only intervenes for truly catastrophic gaps
- **Maintains Pacing**: Doesn't slow down every decision
- **Emphasises Weight**: When it appears, you KNOW it's serious

### Why After Interpretation

- You see what you're doing first (full context)
- Advisors can evaluate decision in context
- Last-chance check before commitment
- Natural dramatic beat in the flow

## Technical Implementation

### Files Modified

- `llm/prompts.py`: Added `build_critical_omissions_prompt()`
- `agents/conversation.py`: Added `check_critical_omissions()`
- `engine/sim_loop.py`: Updated `run_turn_decision()` to return critical concerns
- `cli/main.py`: Added critical advisory UI and player choice handling

### Prompt Engineering

The LLM prompt:
- Shows advisor the player's decision
- Shows current world state and recent events
- Shows conversation history for context
- Specifies HIGH threshold explicitly
- Provides examples of critical vs minor omissions
- Defines advisor's specific domain of responsibility
- Requests structured response: CONCERN + RECOMMENDATION or NO_CONCERN

### Response Parsing

The system parses LLM responses for:
```
CONCERN: [description of the critical gap]
RECOMMENDATION: [specific action to take]
```

Or:
```
NO_CONCERN
```

Multiple advisors can raise concerns simultaneously (each gets their own section).

## Future Enhancements

Possible improvements:
- Track if player ignores warnings (increase consequences)
- Learn from player's past mistakes (reference them)
- Escalate severity if same omission appears repeatedly
- Add metric tracking for "warnings ignored" vs "warnings heeded"

## Testing Scenarios

To test the system, try decisions that:

1. **Deploy military without NATO** → Should trigger Foreign Secretary
2. **Attack without legal authority** → Should trigger Attorney General
3. **Major action without public statement** → Should trigger Home Secretary
4. **Commit forces without logistics** → Should trigger CDS
5. **Escalate without ally consultation** → Should trigger NSA or Foreign Sec

Conversely, well-rounded decisions should NOT trigger warnings:
- "Deploy carrier AND invoke Article 4 AND secure Cabinet approval"
- "Increase readiness WHILE engaging allies AND briefing public"

## Player Feedback

This feature enhances the simulation by:
- Making strategic omissions visible
- Teaching good crisis management
- Adding realistic advisor behaviour
- Creating memorable dramatic moments
- Rewarding comprehensive thinking

**The goal: Make the player feel like they're truly running a crisis response, not just playing a game.**

