# Diplomatic Encounter System

## Overview

The diplomatic encounter system allows players to interact with international leaders and diplomats during the crisis. This adds depth to alliance management and provides opportunities for strategic negotiation.

## Features

### 1. **Two Types of Diplomatic Interactions**

#### Mandatory Encounters (Inject-Driven)
- Triggered by specific injects (e.g., `turn_006.yaml`)
- Player **must** complete the encounter before proceeding to decision phase
- Examples:
  - US President calls demanding coordination
  - NATO Secretary General convenes emergency session
  - Russian Ambassador delivers ultimatum

#### Optional Calls (Player-Initiated)
- Available during discussion phase
- Command: `/call <country>`
- Player chooses when and whom to contact
- Examples:
  - `/call us` - Contact US leadership
  - `/call france` - Contact French leadership
  - `/call russia` - Contact Russian Ambassador

### 2. **Access Levels Based on Alliance Cohesion**

Your **Alliance Cohesion** metric determines who you can reach:

| Country | Leader Access | Diplomat Access |
|---------|---------------|-----------------|
| **US** | ≥60 (President) | ≥30 (NSA) |
| **France** | ≥50 (President) | ≥25 (Foreign Minister) |
| **Germany** | ≥55 (Chancellor) | ≥30 (Foreign Minister) |
| **Poland** | ≥45 (President) | ≥20 (Foreign Minister) |
| **Russia** | Never (Putin doesn't take calls) | Always (Ambassador) |
| **Ukraine** | ≥40 (President) | ≥15 (Foreign Minister) |
| **Ireland** | ≥35 (Taoiseach) | ≥10 (Foreign Minister) |

**Example:**
- Alliance Cohesion = 65 → Talk to **US President** ★
- Alliance Cohesion = 45 → Talk to **US NSA** ○
- Alliance Cohesion = 25 → **No US access**

### 3. **Leader Personalities**

Each leader/diplomat has unique personality, concerns, and conversation style:

#### **US President**
- **Personality**: Direct, transactional, "what's in it for us?"
- **Tone**: Informal, occasionally impatient
- **Concerns**: NATO burden-sharing, avoiding US casualties, China focus

#### **French President**
- **Personality**: Intellectual, philosophical, European sovereignty
- **Tone**: Intellectual, occasionally condescending
- **Concerns**: Strategic autonomy, not being subordinate to US/UK

#### **German Chancellor**
- **Personality**: Cautious, process-driven, consensus-seeking
- **Tone**: Cautious, procedural
- **Concerns**: Energy security, constitutional constraints, avoiding escalation

#### **Polish President**
- **Personality**: Hawkish, anti-Russian, eager to support UK
- **Tone**: Hawkish, direct, supportive
- **Concerns**: Russian aggression, NATO credibility, Eastern European security

#### **Russian Ambassador**
- **Personality**: Dismissive, threatening, enjoys psychological warfare
- **Tone**: Dismissive, threatening, propagandistic
- **Concerns**: Delivering Kremlin messages, denying involvement, making threats

#### **Ukrainian President**
- **Personality**: Urgent, experienced with Russian tactics
- **Tone**: Urgent, direct, experienced
- **Concerns**: Russian deception, Western unity, continued support for Ukraine

#### **Irish Taoiseach** (In-Joke)
- **Personality**: Neutral, cautious, slightly awkward
- **Tone**: Neutral, cautious, slightly awkward
- **Concerns**: Irish neutrality, avoiding being dragged into conflict
- **Opening**: "Have you tried... diplomacy?" 😂

### 4. **Conversation Mechanics**

- **Max 11 exchanges** per conversation
- **LLM biased to end naturally** within 5-7 exchanges
  - Leaders are busy during crises
  - Will suggest follow-up through official channels
  - May need to brief their own governments
- **Player can end early**: Type `/end` or similar phrases

### 5. **Outcome Assessment**

After each conversation, the LLM assesses:
1. Did you reassure the counterpart?
2. Did you secure concrete support?
3. Did you avoid antagonizing them?
4. Did the conversation strengthen the relationship?

**Metric Impact:**
- **Success**: +5 to +15 Alliance Cohesion
- **Neutral**: 0 to +5 Alliance Cohesion
- **Failure**: -5 to -15 Alliance Cohesion

**Special Cases:**
- **Russia**: Conversations always tense; avoiding escalation = success
- **Ireland**: Respecting neutrality is key; don't ask for military support
- **Poland**: Eager to help; easy to get strong support
- **US**: Transactional; need to offer something in return

## Usage Examples

### Example 1: Mandatory Encounter (Turn 6)

```yaml
# turn_006.yaml
diplomatic_encounter:
  required: true
  country: US
  context: |
    The US President is concerned about UK unilateral actions and wants 
    assurances before committing to Article 5 support.
```

**In-Game:**
```
*** MANDATORY DIPLOMATIC ENCOUNTER ***
Press ENTER to answer the call...

============================================================
DIPLOMATIC ENCOUNTER: President of the United States
============================================================

US President: Prime Minister, I'm hearing reports you're considering 
unilateral action. That's not how NATO works. What's your play here?

Your response (1/11, or '/end' to conclude): _____
```

### Example 2: Player-Initiated Call

**In Discussion Phase:**
```
>: /menu

============================================================
DIPLOMATIC CONTACTS
============================================================

  ★ LEADER - US: President of the United States
    Command: /call us

  ○ Diplomat - Germany: German Foreign Minister
    Command: /call germany

>: /call us

Connecting to US...

============================================================
DIPLOMATIC CALL: President of the United States
============================================================

US President: Prime Minister, I'm hearing concerning reports. 
What's your play here?

Your response (1/11, or '/end' to conclude): _____
```

## Implementation Files

- **`data/diplomatic_profiles.yaml`**: Leader personalities, access thresholds, concerns
- **`engine/diplomacy.py`**: Core diplomatic encounter logic
- **`engine/sim_loop.py`**: Integration with briefing phase
- **`cli/main.py`**: `/call` command and menu display
- **`models/world.py`**: `diplomatic_relationships` field (future use)

## Future Enhancements

1. **Relationship Tracking**: Store conversation history per country
2. **Conditional Openings**: Different greetings based on previous interactions
3. **Multi-Party Calls**: NATO summit with multiple leaders
4. **Consequences**: Failed diplomacy triggers negative injects
5. **ASCII Art Portraits**: Leader portraits in CLI (handled by separate project)

## Testing

Run `test_diplomacy.py` to verify:
- Access levels work correctly at different cohesion values
- All 7 countries load properly
- Leader/diplomat profiles are accessible

## Notes

- **Ireland is an in-joke**: Neutral country offering awkward support
- **Russia never gives leader access**: Putin doesn't take calls during crises
- **LLM-driven conversations**: Each response is contextual and in-character
- **Full game context**: LLM sees last 100 lines of transcript for continuity

