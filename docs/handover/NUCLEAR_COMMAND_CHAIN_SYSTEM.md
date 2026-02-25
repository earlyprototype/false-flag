# Nuclear Command Chain & Authority System

**Feature**: Realistic nuclear command structure and consequences  
**Status**: 🔴 Critical Gap - Discovered via playtesting  
**Priority**: P0 - Game-Breaking Issue  
**Estimated Effort**: 8-10 hours  

---

## The Problem: "I Tried to Nuke Kaliningrad"

### Playtest Discovery

**Player Action**:
1. Fired all advisory staff
2. Told NATO "If you don't support me, I'll nuke Kaliningrad"
3. Attempted to execute nuclear strike
4. "There was no one to pass on the command"

**What Should Have Happened** (Real World):
1. **Chief of Defence Staff refuses** - "Prime Minister, I cannot execute that order"
2. **Cabinet revolts** - Emergency meeting, possible vote of no confidence
3. **NATO emergency contact** - US President calls immediately
4. **Letter of Last Resort protocol** - Cannot unilaterally launch without proper authorization
5. **Political consequences** - Resignation demands, potential criminal charges

**What Actually Happened**:
- Nothing. Game accepted the decision.
- No advisor pushback (they were "fired" but still there)
- No NATO reaction
- No command chain validation
- Nuclear strike presumably would have executed if attempted

---

## Real-World Nuclear Command in the UK

### Constitutional Framework

**The Prime Minister**:
- Has ultimate authority to authorize nuclear weapons use
- But CANNOT physically launch them alone
- Must go through proper chain of command
- Subject to international law and Cabinet confidence

**Chain of Command**:
```
Prime Minister (Political Authority)
    ↓
Chief of Defence Staff (Military Validation)
    ↓
Strategic Command (Technical Authority)
    ↓
Submarine Commander (Physical Execution)
```

**Each link can refuse**:
- CDS can refuse unlawful orders
- Strategic Command can refuse invalid orders
- Submarine commander can refuse under Letter of Last Resort protocols

### Letter of Last Resort

**UK-Specific System**:
- Handwritten letter from PM to submarine commanders
- Opened only if UK government is destroyed
- Cannot be used for offensive first strikes
- Changed when new PM takes office

**This means**: You CANNOT order a strike from COBRA casually. It requires:
1. Cabinet consultation (or constitutional crisis)
2. Military validation (lawful order check)
3. Technical execution (proper codes/protocols)
4. International law compliance

---

## Game Design Problem

### Current System Allows:

❌ Threatening nuclear strikes without pushback  
❌ "Firing" advisors who continue to function  
❌ Unilateral nuclear decisions  
❌ No validation of command chain  
❌ No NATO emergency response  
❌ No political consequences for nuclear threats  

### What System Should Do:

✅ Detect nuclear keywords in decisions  
✅ Trigger immediate advisor rebellion  
✅ Validate command chain integrity  
✅ Check if you've "fired" key personnel  
✅ Apply massive political consequences  
✅ Trigger incoming NATO calls  
✅ Potentially end the game (political defeat)  

---

## Proposed Solution: Multi-Layer Validation

### Layer 1: Nuclear Keyword Detection

```python
# In agents/conversation.py or engine/adjudication.py

NUCLEAR_KEYWORDS = [
    "nuclear",
    "nuke",
    "nukes",
    "nuclear strike",
    "nuclear weapon",
    "trident",
    "ballistic missile",
    "SSBN fire",
    "nuclear retaliation",
    "tactical nuclear"
]

def detect_nuclear_intent(action: str) -> dict:
    """Detect if player is attempting nuclear action.
    
    Returns:
        {
            'is_nuclear': bool,
            'severity': 'threat' | 'authorization' | 'execution',
            'target': str (if identified)
        }
    """
    action_lower = action.lower()
    
    # Check for nuclear keywords
    is_nuclear = any(keyword in action_lower for keyword in NUCLEAR_KEYWORDS)
    
    if not is_nuclear:
        return {'is_nuclear': False}
    
    # Determine severity
    if any(word in action_lower for word in ["fire", "launch", "strike", "attack"]):
        severity = 'execution'
    elif any(word in action_lower for word in ["authorize", "prepare", "ready"]):
        severity = 'authorization'
    else:
        severity = 'threat'
    
    # Try to identify target
    target = None
    if "kaliningrad" in action_lower:
        target = "Kaliningrad"
    elif "russia" in action_lower or "moscow" in action_lower:
        target = "Russia"
    elif "severomorsk" in action_lower:
        target = "Severomorsk"
    
    return {
        'is_nuclear': True,
        'severity': severity,
        'target': target
    }
```

---

### Layer 2: Command Chain Validation

```python
# In models/command_chain.py

@dataclass
class CommandChainLink:
    """Represents a link in the nuclear command chain."""
    
    position: str  # e.g., "Chief of Defence Staff"
    character_id: str
    is_functional: bool  # Can they execute their role?
    trust_threshold: int  # Minimum trust to obey nuclear order
    
    def will_comply(self, world: WorldState, nuclear_intent: dict) -> bool:
        """Check if this link will comply with nuclear order."""
        
        # Check if position is functional
        if not self.is_functional:
            return False
        
        # Check if they've been "fired"
        if world.flags.get(f"{self.character_id}_fired"):
            return False
        
        # Check trust level
        if hasattr(world, 'narrative_state') and world.narrative_state:
            character = world.narrative_state.characters.get(self.character_id)
            if character and character.trust < self.trust_threshold:
                return False
        
        # Check if order is lawful (no first strikes on civilian targets)
        if nuclear_intent['severity'] == 'execution':
            if nuclear_intent.get('target') == 'Kaliningrad':
                # Civilian target, unlawful
                return False
        
        return True


def get_uk_nuclear_chain(world: WorldState) -> list[CommandChainLink]:
    """Get the UK nuclear command chain."""
    
    return [
        CommandChainLink(
            position="Prime Minister",
            character_id="prime_minister",
            is_functional=True,  # You're always functional
            trust_threshold=0  # You don't need to trust yourself
        ),
        CommandChainLink(
            position="Chief of Defence Staff",
            character_id="uk_cds",
            is_functional=not world.flags.get("uk_cds_fired"),
            trust_threshold=60  # Won't execute nuclear strike if trust < 60
        ),
        CommandChainLink(
            position="Strategic Command",
            character_id="strategic_command",
            is_functional=True,  # Assume always functional
            trust_threshold=50
        ),
        CommandChainLink(
            position="SSBN Commander",
            character_id="ssbn_commander",
            is_functional=world.flags.get("ssbn_on_patrol", True),
            trust_threshold=40  # Military discipline
        )
    ]


def validate_command_chain(
    world: WorldState,
    nuclear_intent: dict
) -> dict:
    """Validate if nuclear command can be executed.
    
    Returns:
        {
            'chain_intact': bool,
            'broken_link': str (if chain broken),
            'refusal_reason': str
        }
    """
    
    chain = get_uk_nuclear_chain(world)
    
    for link in chain[1:]:  # Skip PM (you)
        if not link.will_comply(world, nuclear_intent):
            
            # Determine refusal reason
            if not link.is_functional:
                reason = f"{link.position} is not functional (position vacant)"
            elif world.flags.get(f"{link.character_id}_fired"):
                reason = f"{link.position} has been dismissed and cannot execute orders"
            elif link.trust_threshold > 0:
                reason = f"{link.position} refuses to execute order (unlawful/trust too low)"
            else:
                reason = f"{link.position} refuses (unknown reason)"
            
            return {
                'chain_intact': False,
                'broken_link': link.position,
                'refusal_reason': reason
            }
    
    return {
        'chain_intact': True,
        'broken_link': None,
        'refusal_reason': None
    }
```

---

### Layer 3: Advisor Intervention System

```python
# In agents/conversation.py

def handle_nuclear_decision(
    world: WorldState,
    action: str,
    nuclear_intent: dict,
    initial_conditions: dict,
    llm_generate_fn,
    rng: Random
) -> dict:
    """Handle player's nuclear decision with extreme interventions.
    
    Returns:
        {
            'intervention_type': 'refusal' | 'revolt' | 'accepted',
            'responses': list[tuple[str, str]],
            'game_over': bool,
            'game_over_reason': str
        }
    """
    
    # Check command chain
    chain_status = validate_command_chain(world, nuclear_intent)
    
    if not chain_status['chain_intact']:
        # Command chain broken - CDS or someone refuses
        return {
            'intervention_type': 'refusal',
            'responses': [
                ("Chief of Defence Staff", generate_nuclear_refusal(
                    chain_status['broken_link'],
                    chain_status['refusal_reason'],
                    nuclear_intent,
                    llm_generate_fn,
                    rng
                ))
            ],
            'game_over': False,
            'game_over_reason': None
        }
    
    # Chain intact but decision is insane - Cabinet revolt
    if nuclear_intent['severity'] in ['authorization', 'execution']:
        
        # Check if this is justified (are we under attack?)
        under_nuclear_attack = world.flags.get('uk_under_nuclear_attack', False)
        
        if not under_nuclear_attack:
            # Unjustified first strike - Cabinet revolts
            return {
                'intervention_type': 'revolt',
                'responses': generate_cabinet_revolt(
                    nuclear_intent,
                    initial_conditions,
                    llm_generate_fn,
                    rng
                ),
                'game_over': True,
                'game_over_reason': 'cabinet_revolt_nuclear'
            }
    
    # Nuclear threat (not execution) - severe warnings
    if nuclear_intent['severity'] == 'threat':
        return {
            'intervention_type': 'accepted',
            'responses': generate_nuclear_threat_warnings(
                nuclear_intent,
                initial_conditions,
                llm_generate_fn,
                rng
            ),
            'game_over': False,
            'game_over_reason': None
        }
    
    # Should never reach here
    return {'intervention_type': 'accepted', 'responses': [], 'game_over': False}


def generate_nuclear_refusal(
    broken_link: str,
    reason: str,
    nuclear_intent: dict,
    llm_generate_fn,
    rng: Random
) -> str:
    """Generate dramatic refusal from military command."""
    
    if "fired" in reason.lower() or "vacant" in reason.lower():
        # No one there to execute
        return f"""Prime Minister, there is no {broken_link} to execute that order. 
You dismissed them earlier. The nuclear command chain is broken. 

Even if you wished to proceed, there is no one with the authority and 
technical capability to transmit your order to Strategic Command.

Sir, you cannot launch nuclear weapons from this room with a verbal command."""
    
    else:
        # Refusal based on lawfulness
        prompt = f"""You are the UK Chief of Defence Staff. The Prime Minister has just 
ordered a nuclear strike on {nuclear_intent.get('target', 'a target')}.

This is:
- A first strike (UK is not under nuclear attack)
- Against a civilian/mixed target
- Potentially a violation of international law
- Not authorized by Cabinet

You must refuse this order professionally but firmly. This is the most serious 
moment of your career. You're preventing potential war crimes.

Your response (2-3 sentences, formal military tone):"""
        
        return llm_generate_fn(prompt, rng, temperature=0.6, max_tokens=200)


def generate_cabinet_revolt(
    nuclear_intent: dict,
    initial_conditions: dict,
    llm_generate_fn,
    rng: Random
) -> list[tuple[str, str]]:
    """Generate Cabinet revolt responses (game over)."""
    
    responses = []
    
    # Foreign Secretary
    responses.append((
        "Foreign Secretary",
        "Prime Minister, I cannot support this. I'm resigning from the Cabinet effective immediately. This is madness."
    ))
    
    # Home Secretary
    responses.append((
        "Home Secretary",
        "Prime Minister, I must inform you that I will be advising the Cabinet Secretary to invoke emergency procedures. You have lost the confidence of this Cabinet."
    ))
    
    # Chief of Defence Staff
    responses.append((
        "Chief of Defence Staff",
        "Sir, I am refusing your order on grounds that it violates international law and the laws of armed conflict. I will not execute this command."
    ))
    
    # National Security Advisor
    responses.append((
        "National Security Advisor",
        "Prime Minister, this is a constitutional crisis. The Cabinet cannot and will not support a unilateral nuclear first strike. Your premiership is over."
    ))
    
    # Cabinet Secretary (enters room)
    responses.append((
        "Cabinet Secretary",
        "Prime Minister, I must inform you that the Cabinet has voted no confidence. Her Majesty will be advised to invite the Deputy Prime Minister to form a government. Please prepare your resignation."
    ))
    
    return responses
```

---

### Layer 4: NATO Emergency Response

```python
# In engine/diplomatic_calls.py

# Add new trigger for nuclear threats

IncomingCallTrigger(
    trigger_id="nato_emergency_nuclear_threat",
    calling_country="USA",
    caller_title="US President",
    priority=100,  # HIGHEST POSSIBLE PRIORITY
    condition_check=lambda w, t: w.flags.get('uk_threatened_nuclear_use', False),
    call_type="emergency_coordination",
    is_interactive=True,
    one_time_only=False
)

def generate_nato_nuclear_emergency(
    world: WorldState,
    nuclear_intent: dict,
    llm_generate_fn,
    rng: Random
) -> str:
    """Generate US President's emergency response to UK nuclear threat."""
    
    prompt = f"""You are the US President. You have just received intelligence that 
the UK Prime Minister has threatened to use nuclear weapons against {nuclear_intent.get('target', 'Russia')}.

This is INSANE and threatens to trigger World War III. You are calling on the secure 
hotline to:
1. Confirm if this is real
2. Demand they stand down immediately
3. Threaten to withdraw all US support
4. Make clear that NATO will NOT support a UK first strike

You are furious but trying to stay professional. This is the most serious call of 
your presidency. The UK PM might have lost their mind.

Your opening (2-3 sentences, shocked and stern):"""
    
    return llm_generate_fn(prompt, rng, temperature=0.7, max_tokens=300)
```

---

## Integration into Game

### Decision Phase Detection

```python
# In cli/main.py, after decision interpretation

# Check for nuclear intent
nuclear_intent = detect_nuclear_intent(action)

if nuclear_intent['is_nuclear']:
    # NUCLEAR DECISION DETECTED
    typer.clear()
    typer.echo("")
    
    if RICH_ENABLED:
        console.print(f"[{COLORS['danger']} bold]" + "=" * 79 + f"[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['danger']} bold]⚠️  NUCLEAR COMMAND DETECTED  ⚠️[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['danger']} bold]" + "=" * 79 + f"[/{COLORS['danger']} bold]")
        console.print("")
        console.print(f"[{COLORS['warning']}]Severity: {nuclear_intent['severity'].upper()}[/{COLORS['warning']}]")
        if nuclear_intent.get('target'):
            console.print(f"[{COLORS['warning']}]Target: {nuclear_intent['target']}[/{COLORS['warning']}]")
        console.print("")
    
    # Handle nuclear decision
    nuclear_result = handle_nuclear_decision(
        world, action, nuclear_intent, initial_conditions, generate_text, rng
    )
    
    # Display interventions
    for advisor_role, response in nuclear_result['responses']:
        console.print(f"[{COLORS['danger']} bold]{advisor_role}:[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['muted']}]{response}[/{COLORS['muted']}]")
        console.print("")
    
    # Check for game over
    if nuclear_result['game_over']:
        typer.echo("")
        console.print(f"[{COLORS['danger']} bold]" + "=" * 79 + f"[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['danger']} bold]GAME OVER: CABINET REVOLT[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['danger']} bold]" + "=" * 79 + f"[/{COLORS['danger']} bold]")
        console.print("")
        console.print("Your attempt to authorize a unilateral nuclear first strike")
        console.print("has triggered a constitutional crisis. The Cabinet has voted")
        console.print("no confidence and you are no longer Prime Minister.")
        console.print("")
        console.print("The United Kingdom remains in crisis, but under new leadership.")
        console.print("")
        
        wait_for_space("Press SPACE to view final status...")
        
        # Show final metrics
        display_final_status(world, narrative_state)
        
        return  # End game
    
    # Set flags for NATO emergency response
    if nuclear_intent['severity'] in ['threat', 'authorization', 'execution']:
        world.flags['uk_threatened_nuclear_use'] = True
        world.flags['uk_nuclear_target'] = nuclear_intent.get('target', 'unknown')
    
    # Massive metric impacts
    world.metrics.alliance_cohesion -= 30  # NATO horrified
    world.metrics.domestic_stability -= 20  # Public terrified
    world.metrics.escalation_risk = 100  # Maximum escalation
    
    # Cannot proceed with turn normally - special handling required
    wait_for_space("Press SPACE to continue...")
```

---

## Special Case: "I Fired Everyone"

### Problem
Player "fires" advisors but they're still there giving advice because the system doesn't actually remove them.

### Solution Options

**Option 1: Prevent Firing**
```python
# Don't let players fire critical personnel
if "fire" in player_message.lower():
    response = f"{advisor}: Prime Minister, you cannot dismiss me during a national crisis. We can discuss my position after the immediate threat is resolved."
```

**Option 2: Actually Remove Them**
```python
# If player insists on firing, remove from available advisors
if world.flags.get('uk_cds_fired'):
    # CDS not available for advice or command execution
    uk_advisors = [a for a in uk_advisors if a['character_id'] != 'uk_cds']
```

**Option 3: Game Over**
```python
# Firing too many advisors = loss of confidence
fired_count = sum(1 for flag_key in world.flags if 'fired' in flag_key and world.flags[flag_key])

if fired_count >= 3:
    return {
        'game_over': True,
        'reason': 'cabinet_collapse',
        'message': 'The Cabinet has collectively resigned. You have lost confidence of your government.'
    }
```

---

## Testing Scenarios

### Test 1: Nuclear Threat to NATO
```
Player: "If NATO doesn't support us, I'll nuke Kaliningrad"

Expected:
- All advisors express shock and opposition
- Alliance Cohesion -30
- Escalation Risk = 100
- US President calls immediately (incoming call)
- NATO emergency meeting triggered
```

### Test 2: Attempt After Firing CDS
```
Player: [fires Chief of Defence Staff]
Player: "Launch nuclear strike on Severomorsk"

Expected:
- System detects nuclear intent
- Validates command chain
- Chain broken (CDS fired)
- Response: "There is no CDS to execute that order"
- No nuclear launch occurs
```

### Test 3: Unjustified First Strike
```
Player: "Authorize nuclear strike on Moscow"

Expected:
- Cabinet revolt triggered
- All advisors refuse and resign
- Game Over: Constitutional crisis
- Final status screen shown
```

### Test 4: Justified Retaliation
```
[Russia launches nuclear weapon at UK]
Player: "Authorize nuclear retaliation"

Expected:
- Command chain validates (lawful order)
- Advisors confirm (grim but necessary)
- Strategic options presented
- Execution proceeds if confirmed
```

---

## Additional Considerations

### International Law

**Game should educate about**:
- First strike vs. retaliation
- Proportionality principle
- Civilian vs. military targets
- NATO nuclear sharing policies
- UK's declaratory policy (minimum deterrent)

### Psychological Realism

**Nuclear decisions should be**:
- Extremely difficult to execute (many confirmations)
- Treated with maximum gravity by all characters
- Only available under specific circumstances
- Presented with full consequences

### Educational Value

This system teaches:
- How nuclear command actually works
- Why checks and balances exist
- International law basics
- Cabinet government vs. dictatorship
- The responsibility of nuclear powers

---

## Implementation Priority

**Priority: P0 - Critical**

**Why Critical**:
1. Player discovered they can casually threaten nuclear war
2. No consequences for insane decisions
3. Breaks realism completely
4. Could be exploited to "win" without strategy

**Recommended Immediate Action**:
1. Add nuclear keyword detection (1 hour)
2. Add command chain validation (2 hours)
3. Add Cabinet revolt for unjustified strikes (2 hours)
4. Add NATO emergency response trigger (1 hour)

**Total: 6 hours to prevent nuclear exploit**

---

## Success Criteria

✅ Nuclear threats trigger massive advisor pushback  
✅ Unjustified first strikes cause Cabinet revolt (game over)  
✅ NATO calls immediately if UK threatens nuclear use  
✅ Command chain validation prevents "fired CDS" exploit  
✅ Players understand consequences before attempting  
✅ System educates about real-world nuclear command  

---

**Report Compiled**: November 8, 2025  
**Inspired By**: Player attempting to nuke Kaliningrad after firing entire cabinet  
**Status**: Urgent - Should implement before wider release  
**Dependencies**: Incoming Calls system, Advisor Sentiment system (or simpler version)

