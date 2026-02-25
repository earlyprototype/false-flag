# Incoming Diplomatic Calls System - Implementation Report

**Feature**: Allow foreign nations to initiate contact with the UK Prime Minister  
**Status**: 🔲 Not Implemented - Critical Gap Identified  
**Priority**: P1 - High (Core gameplay mechanic)  
**Estimated Effort**: 6-8 hours  

---

## Executive Summary

**Problem Discovered**: The current diplomatic system only allows the UK PM to initiate calls. Foreign nations cannot contact the PM, even in urgent situations or to deliver threats.

**Real-World Context**: In an actual crisis:
- Russia would use diplomatic channels to deliver ultimatums
- The US would call to coordinate strategy
- Allies would reach out for clarification on UK position
- Adversaries would make demands or propaganda statements

**Proposed Solution**: Add incoming call system that triggers based on game state, player actions, and narrative context.

**Value Proposition**: Increases realism, creates dramatic moments, removes player control temporarily (creates tension), enables reactive diplomacy.

---

## Current System Limitations

### What Exists Now

**Diplomatic System** (`engine/diplomacy.py`):
- Player initiates via `/call <country>` command
- Access levels restrict who player can call
- Multi-turn conversations work well
- Outcome assessment after call ends

**What's Missing**:
- ❌ Foreign nations cannot initiate contact
- ❌ No "incoming call" interrupts during discussion phase
- ❌ No urgent diplomatic messages between turns
- ❌ No way for Russia to deliver threats proactively
- ❌ No mechanism for allies to warn/advise unprompted

---

## Real-World Scenarios That Should Trigger Incoming Calls

### 1. Russian Escalation & Threats

**Trigger**: Player takes aggressive military action

```
[During Discussion Phase]

*URGENT DIPLOMATIC CALL INCOMING*

Russian Ambassador: "Prime Minister, I have been instructed by President 
Putin to deliver the following message personally. Your government's 
decision to deploy attack submarines within range of our naval forces 
is viewed as an act of aggression. 

President Putin demands immediate withdrawal of all UK military assets 
from the operational area. You have six hours to comply. Failure to do 
so will be met with appropriate defensive measures.

This call is concluded."

[CALL ENDED BY RUSSIA]
```

**Game Impact**:
- Creates time pressure
- Forces player to respond (militarily or diplomatically)
- Adds flag: `russia_ultimatum_given`
- Starts countdown timer (optional feature)

---

### 2. US Urgent Coordination

**Trigger**: Major escalation event, player invoked NATO Article 5, or critical decision needed

```
[Interrupt During Briefing]

📞 INCOMING CALL: White House Situation Room

US President: "Prime Minister, sorry to interrupt your briefing but 
we have a situation. Our Ohio-class submarine in the North Atlantic 
has detected a Russian SSBN attempting to achieve firing position.

I need your authorization to share our exact tracking data with your 
forces. But I also need to know - if this goes hot, are you prepared 
to authorize military action? I need a clear answer right now because 
my Joint Chiefs are asking if we're really doing this.

What's your position?"

[REQUIRES IMMEDIATE RESPONSE]
```

**Game Impact**:
- Player must make snap decision
- No time for advisor consultation (forces independent thinking)
- Establishes US commitment level based on response
- Affects Alliance Cohesion

---

### 3. Allied Warnings

**Trigger**: Player making risky decisions, alliance cohesion dropping

```
[After Player Ignores NATO Coordination]

📞 INCOMING CALL: Élysée Palace, Paris

French President: "Prime Minister, I'm calling because I'm deeply 
concerned about reports that the UK is considering unilateral military 
action without consulting NATO partners.

We have a shared security architecture for a reason. If you act alone, 
you put the entire alliance at risk. I'm asking you, as a friend and 
ally, to slow down and consult before any further escalation.

Can I have your assurance that you will coordinate with NATO before 
any military strikes?"

[Player response affects France relationship and Alliance Cohesion]
```

---

### 4. Third-Party Intelligence Sharing

**Trigger**: Narrative-dependent, China Proxy War narrative

```
[Unexpected Call During Discussion]

📞 INCOMING CALL: Chinese Ministry of Foreign Affairs

Chinese Foreign Minister: "Prime Minister, I am calling to share 
information that may be relevant to your current crisis. Our maritime 
surveillance has observed unusual patterns in Russian naval logistics.

We believe you should be aware that certain... financial arrangements... 
have been made that suggest this operation is more complex than it 
appears. We are not taking sides, but as a responsible power, we 
thought you should know.

I cannot say more on an open line. Perhaps your intelligence services 
should examine Shanghai port records from the past ninety days."

[CALL ENDED BY CHINA]
[Adds flag: china_hint_given]
```

**Narrative Impact**: Provides cryptic clue about hidden narrative truth

---

### 5. Irish Neutrality Concerns

**Trigger**: Player actions affect Ireland (overflights, basing requests, etc.)

```
📞 INCOMING CALL: Dublin

Taoiseach: "Prime Minister, I'm calling about your recent request to 
use Irish airspace for military operations. You know our position on 
neutrality.

I'm under enormous pressure from my coalition partners. The Greens are 
threatening to collapse the government if I allow this. And frankly, 
the Irish people don't want to be dragged into a UK-Russia conflict.

I need you to respect our neutrality. Find another routing for your 
aircraft."

[IRISH AIRSPACE ACCESS DENIED]
```

---

## Proposed Implementation

### Architecture Overview

```
INCOMING CALL TRIGGER SYSTEM

Game State Monitor
    ↓
Check Trigger Conditions Each Turn/Phase
    ↓
If Conditions Met → Queue Incoming Call
    ↓
Interrupt Current Phase with Notification
    ↓
Present Caller & Opening Message
    ↓
[AUTO mode] Deliver message and end
[INTERACTIVE mode] Allow player response
    ↓
Apply Consequences Based on Player Response
    ↓
Resume Normal Game Flow
```

---

## Implementation Design

### 1. Trigger Definition System

```python
# In models/diplomatic_triggers.py

from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
from models.world import WorldState

@dataclass
class IncomingCallTrigger:
    """Defines conditions for an incoming diplomatic call."""
    
    trigger_id: str
    calling_country: str
    caller_title: str
    priority: int  # Higher = more urgent, interrupts sooner
    
    # Condition check function
    condition_check: Callable[[WorldState, list], bool]
    
    # Call type
    call_type: str  # 'ultimatum', 'coordination', 'warning', 'intelligence'
    is_interactive: bool  # If False, just delivers message and ends
    
    # Cooldown (prevent spam)
    cooldown_turns: int = 3
    
    # Can only trigger once per game
    one_time_only: bool = False
    
    # Narrative requirements
    required_narrative: Optional[str] = None  # e.g., "CHINA_PROXY_WAR"
    
    def check_trigger(self, world: WorldState, transcript: list) -> bool:
        """Check if conditions are met for this call."""
        
        # Check cooldown
        last_triggered = world.flags.get(f"call_trigger_{self.trigger_id}_last_turn", 0)
        if world.turn - last_triggered < self.cooldown_turns:
            return False
        
        # Check one-time
        if self.one_time_only and world.flags.get(f"call_trigger_{self.trigger_id}_fired"):
            return False
        
        # Check narrative requirements
        if self.required_narrative:
            if not world.narrative or world.narrative.narrative_id != self.required_narrative:
                return False
        
        # Check custom condition
        return self.condition_check(world, transcript)


# Example trigger definitions

def check_aggressive_action(world: WorldState, transcript: list) -> bool:
    """Check if player took aggressive military action."""
    recent_transcript = transcript[-20:] if len(transcript) > 20 else transcript
    
    aggressive_keywords = [
        "deploy attack submarines",
        "launch strike",
        "offensive action",
        "attack russian",
        "tomahawk missiles"
    ]
    
    for line in recent_transcript:
        if any(kw in line.lower() for kw in aggressive_keywords):
            return True
    
    return False


def check_high_escalation(world: WorldState, transcript: list) -> bool:
    """Check if escalation risk is critically high."""
    return world.metrics.escalation_risk > 85


def check_alliance_fracture(world: WorldState, transcript: list) -> bool:
    """Check if alliance cohesion is dangerously low."""
    return world.metrics.alliance_cohesion < 30


INCOMING_CALL_TRIGGERS = [
    IncomingCallTrigger(
        trigger_id="russian_ultimatum_aggressive",
        calling_country="RUS",
        caller_title="Russian Ambassador to the UK",
        priority=10,  # Highest - will interrupt
        condition_check=check_aggressive_action,
        call_type="ultimatum",
        is_interactive=False,  # Russia delivers message and hangs up
        one_time_only=True
    ),
    
    IncomingCallTrigger(
        trigger_id="us_coordination_urgent",
        calling_country="USA",
        caller_title="US President",
        priority=9,
        condition_check=check_high_escalation,
        call_type="coordination",
        is_interactive=True,  # Player must respond
        cooldown_turns=5
    ),
    
    IncomingCallTrigger(
        trigger_id="france_warning_unilateral",
        calling_country="FRA",
        caller_title="French President",
        priority=7,
        condition_check=check_alliance_fracture,
        call_type="warning",
        is_interactive=True,
        cooldown_turns=4
    ),
    
    # Narrative-specific trigger
    IncomingCallTrigger(
        trigger_id="china_cryptic_hint",
        calling_country="CHN",
        caller_title="Chinese Foreign Minister",
        priority=6,
        condition_check=lambda w, t: w.turn == 5,  # Specific turn
        call_type="intelligence",
        is_interactive=False,
        one_time_only=True,
        required_narrative="CHINA_PROXY_WAR"
    )
]
```

---

### 2. Call Queue Manager

```python
# In engine/diplomatic_calls.py

class IncomingCallQueue:
    """Manages queue of pending incoming diplomatic calls."""
    
    def __init__(self):
        self.queued_calls = []
    
    def check_triggers(self, world: WorldState, transcript: list):
        """Check all triggers and queue any that fire."""
        
        for trigger in INCOMING_CALL_TRIGGERS:
            if trigger.check_trigger(world, transcript):
                self.queue_call(trigger, world)
    
    def queue_call(self, trigger: IncomingCallTrigger, world: WorldState):
        """Add a call to the queue."""
        
        # Mark as triggered
        world.flags[f"call_trigger_{trigger.trigger_id}_last_turn"] = world.turn
        if trigger.one_time_only:
            world.flags[f"call_trigger_{trigger.trigger_id}_fired"] = True
        
        # Add to queue
        self.queued_calls.append({
            'trigger': trigger,
            'turn_queued': world.turn,
            'priority': trigger.priority
        })
        
        # Sort by priority (highest first)
        self.queued_calls.sort(key=lambda x: x['priority'], reverse=True)
    
    def has_pending_calls(self) -> bool:
        """Check if any calls are pending."""
        return len(self.queued_calls) > 0
    
    def get_next_call(self) -> Optional[Dict]:
        """Get the highest priority pending call."""
        if self.queued_calls:
            return self.queued_calls.pop(0)
        return None
    
    def clear_old_calls(self, current_turn: int, max_age: int = 2):
        """Remove calls older than max_age turns (they expired)."""
        self.queued_calls = [
            call for call in self.queued_calls
            if current_turn - call['turn_queued'] < max_age
        ]


# Global queue instance
INCOMING_CALL_QUEUE = IncomingCallQueue()
```

---

### 3. Call Content Generator

```python
# In engine/diplomatic_calls.py

def generate_incoming_call_content(
    trigger: IncomingCallTrigger,
    world: WorldState,
    transcript: list,
    llm_generate_fn,
    rng: Random
) -> Dict[str, Any]:
    """Generate the content of an incoming diplomatic call.
    
    Returns:
        {
            'opening_message': str,
            'requires_response': bool,
            'suggested_responses': list[str] (if interactive),
            'consequences': dict
        }
    """
    
    # Load diplomatic profile
    profile = get_diplomatic_profile(trigger.calling_country, world)
    
    # Get narrative context
    narrative_context = ""
    if world.narrative:
        narrative_context = world.narrative.to_llm_context(trigger.calling_country)
    
    # Build prompt based on call type
    if trigger.call_type == "ultimatum":
        prompt = f"""You are roleplaying as the {trigger.caller_title}.

{narrative_context}

Current Situation:
- Turn: {world.turn}
- Escalation Risk: {world.metrics.escalation_risk}/100
- The UK has just taken aggressive military action

Your Task:
Deliver a stern ultimatum to the UK Prime Minister. You are calling to:
1. Express outrage at UK aggression
2. Demand immediate cessation of military action
3. Issue a veiled threat of consequences
4. End the call abruptly (you will not take questions)

Keep it brief (2-3 sentences), formal, and threatening. This is a diplomatic protest, not a negotiation.

Your message:"""
    
    elif trigger.call_type == "coordination":
        prompt = f"""You are roleplaying as the {trigger.caller_title}.

{narrative_context}

Current Situation:
- Turn: {world.turn}
- Escalation Risk: {world.metrics.escalation_risk}/100
- Alliance Cohesion: {world.metrics.alliance_cohesion}/100

Your Task:
Call the UK PM urgently to coordinate strategy. You need:
1. To share urgent intelligence or situation update
2. To get UK's position on a critical decision
3. To ensure coordination before next moves

Be urgent but professional. Ask a direct question that requires an immediate answer.

Your opening message (2-3 sentences):"""
    
    # Generate content
    opening_message = llm_generate_fn(prompt, rng, temperature=0.7, max_tokens=300)
    
    return {
        'opening_message': opening_message,
        'requires_response': trigger.is_interactive,
        'call_type': trigger.call_type,
        'can_respond': trigger.is_interactive
    }
```

---

### 4. Integration into Game Loop

```python
# In cli/main.py - Main game loop modifications

# At START of each turn (after briefing):
def check_incoming_calls(world, transcript):
    """Check for incoming diplomatic calls."""
    
    # Check triggers
    INCOMING_CALL_QUEUE.check_triggers(world, transcript)
    
    # Clear expired calls
    INCOMING_CALL_QUEUE.clear_old_calls(world.turn)
    
    # Process highest priority call if any
    if INCOMING_CALL_QUEUE.has_pending_calls():
        next_call = INCOMING_CALL_QUEUE.get_next_call()
        handle_incoming_call(next_call, world, transcript)


def handle_incoming_call(
    call_data: Dict,
    world: WorldState,
    transcript: list
):
    """Handle an incoming diplomatic call with dramatic presentation."""
    
    trigger = call_data['trigger']
    
    # Dramatic interruption
    typer.clear()
    typer.echo("")
    
    if RICH_ENABLED:
        console.print("")
        console.print(f"[{COLORS['danger']} bold]" + "!" * 79 + f"[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['danger']} bold]📞 INCOMING DIPLOMATIC CALL[/{COLORS['danger']} bold]")
        console.print(f"[{COLORS['danger']} bold]" + "!" * 79 + f"[/{COLORS['danger']} bold]")
        console.print("")
        console.print(f"[{COLORS['warning']}]Caller: {trigger.caller_title} ({trigger.calling_country})[/{COLORS['warning']}]")
        console.print(f"[{COLORS['warning']}]Priority: {'URGENT' if trigger.priority > 8 else 'HIGH'}[/{COLORS['warning']}]")
        console.print("")
    else:
        typer.echo("=" * 79)
        typer.echo("📞 INCOMING DIPLOMATIC CALL")
        typer.echo("=" * 79)
        typer.echo(f"Caller: {trigger.caller_title} ({trigger.calling_country})")
        typer.echo("")
    
    wait_for_space("Press SPACE to answer call...")
    
    # Generate call content
    content = generate_incoming_call_content(
        trigger, world, transcript, generate_text, rng
    )
    
    # Display opening message
    typer.echo("")
    typer.echo(f"{trigger.caller_title}:")
    typer.echo("")
    
    # Stream the message for drama
    scroll_text(content['opening_message'], delay_ms=30)
    
    typer.echo("")
    
    # Handle based on call type
    if content['requires_response']:
        # Interactive - player must respond
        typer.echo("")
        typer.secho("You must respond to this call.", fg="yellow")
        typer.echo("")
        
        response = typer.prompt("Your response").strip()
        
        # Process response (mini diplomatic conversation)
        # ... (similar to existing diplomacy system)
        
    else:
        # Non-interactive - message only
        typer.echo("")
        typer.secho("[CALL ENDED BY FOREIGN PARTY]", fg="red")
        typer.echo("")
        
        # Apply automatic consequences
        apply_call_consequences(trigger, world, None)
    
    wait_for_space("Press SPACE to continue...")
    
    # Log to transcript
    transcript.append(f"INCOMING CALL from {trigger.calling_country}: {content['opening_message']}")


# Modify main game loop to check for calls at appropriate times:

while True:  # Main game loop
    # ... existing briefing phase ...
    
    # NEW: Check for incoming calls after briefing
    check_incoming_calls(world, transcript)
    
    # ... rest of game loop ...
```

---

## Call Types & Behaviors

### Ultimatum
**Characteristics**:
- Non-interactive (no player response)
- Delivers message and hangs up
- Creates time pressure
- Typically from adversaries

**Implementation**:
```python
is_interactive = False
# Applies automatic consequences:
- Adds flags (e.g., 'russia_ultimatum_active')
- May start countdown timer
- Affects metrics (escalation +5, domestic stability -3)
```

---

### Coordination
**Characteristics**:
- Interactive (requires player response)
- Urgent tactical/strategic decision
- From allies (USA, NATO partners)
- Response affects relationship

**Implementation**:
```python
is_interactive = True
# Player must provide response
# Response analyzed for:
- Commitment level
- Coordination willingness
- Strategic alignment
# Affects Alliance Cohesion based on response
```

---

### Warning
**Characteristics**:
- Interactive (player can explain/reassure)
- Concerned tone from allies
- Opportunity to repair relationship
- Ignoring has consequences

**Implementation**:
```python
is_interactive = True
# Good response: +5 Alliance Cohesion
# Poor/dismissive response: -10 Alliance Cohesion
# No response (hang up): -15 Alliance Cohesion
```

---

### Intelligence
**Characteristics**:
- Non-interactive OR minimal interaction
- Provides clues or warnings
- Often from unexpected sources
- May be narrative-specific

**Implementation**:
```python
is_interactive = False  # Usually
# Adds intelligence flags
# May unlock new advisor knowledge
# Can hint at narrative truth
```

---

## Consequences System

```python
def apply_call_consequences(
    trigger: IncomingCallTrigger,
    world: WorldState,
    player_response: Optional[str]
):
    """Apply consequences based on call type and player response."""
    
    if trigger.call_type == "ultimatum":
        # Automatic effects
        world.metrics.escalation_risk += 5
        world.metrics.domestic_stability -= 3
        world.flags[f"{trigger.calling_country.lower()}_ultimatum_active"] = True
        
    elif trigger.call_type == "coordination":
        if player_response:
            # Analyze response quality
            if "yes" in player_response.lower() or "coordinate" in player_response.lower():
                world.metrics.alliance_cohesion += 5
            elif "no" in player_response.lower() or "unilateral" in player_response.lower():
                world.metrics.alliance_cohesion -= 10
        else:
            # No response = bad
            world.metrics.alliance_cohesion -= 15
    
    elif trigger.call_type == "warning":
        # Similar to coordination but more forgiving
        pass
    
    elif trigger.call_type == "intelligence":
        # Add knowledge flags
        world.flags[f"{trigger.trigger_id}_intel_received"] = True
```

---

## UI/UX Design

### Visual Hierarchy

```
┌─────────────────────────────────────────────────────┐
│ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! │
│ 📞 INCOMING DIPLOMATIC CALL                        │
│ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! │
│                                                     │
│ Caller: Russian Ambassador to the UK               │
│ Priority: URGENT                                   │
│ Type: ULTIMATUM                                    │
│                                                     │
│ Press SPACE to answer call...                      │
└─────────────────────────────────────────────────────┘
```

### Timing Options

**Option 1: Interrupt Immediately**
- Call interrupts current phase
- Player must answer now
- Creates urgency and tension
- **Recommended for high-priority calls**

**Option 2: Queue Until Phase End**
- Call notification appears
- Can be answered at end of current phase
- Less disruptive but less dramatic
- **Recommended for low-priority calls**

**Option 3: Turn Start Only**
- Calls only happen at turn start (after briefing)
- Most predictable, least disruptive
- Loses some tension
- **Recommended for first implementation**

---

## Testing Scenarios

### Test 1: Russian Ultimatum
1. Deploy UK submarines aggressively
2. Should trigger Russian ultimatum on next turn
3. Verify message delivered
4. Verify flags set correctly
5. Verify no response option (hangs up)

### Test 2: US Coordination
1. Escalation risk reaches 90
2. Should trigger US coordination call
3. Verify player can respond
4. Test "yes" response → Alliance Cohesion +5
5. Test "no" response → Alliance Cohesion -10

### Test 3: Narrative-Specific Call
1. Start game with China Proxy War narrative
2. Reach Turn 5
3. Verify China intelligence call triggers
4. Verify flag added for narrative clue

### Test 4: Cooldown System
1. Trigger same call type twice
2. Verify second call blocked by cooldown
3. Wait cooldown_turns
4. Verify call can trigger again

---

## Phased Implementation

### Phase 1: Basic System (4 hours)
- Create trigger definition system
- Create call queue manager
- Add one test trigger (Russian ultimatum)
- Integrate into game loop (turn start only)
- Simple message display (no LLM generation)

### Phase 2: LLM Integration (2 hours)
- Add LLM-based message generation
- Add narrative-aware context
- Improve message quality and variety

### Phase 3: Interactive Calls (2 hours)
- Add player response handling
- Add consequence system
- Add response quality analysis

### Phase 4: Advanced Features (2-4 hours)
- Add countdown timers for ultimatums
- Add mid-phase interrupts
- Add call history/log
- Add more trigger types

---

## Integration with Existing Systems

### Diplomatic System
- Reuse conversation logic for interactive calls
- Reuse profile/personality system
- Add new access level: "Can call YOU"

### Narrative System
- Triggers can be narrative-specific
- Call content reflects secret motives
- Provides avenue for subtle clues

### Metrics System
- Calls affect metrics based on type
- Player response quality affects outcomes
- Ignoring calls has penalties

---

## Alternative: Simpler "Messenger" System

If full incoming calls are too complex, consider:

```
[After Briefing]

📬 DIPLOMATIC MESSAGE RECEIVED

From: Russian Embassy, London
Priority: Urgent
Subject: Formal Protest

[View Message] or [Dismiss]

If viewed:
"The Russian Federation formally protests the UK's 
aggressive deployment of military assets..."

[No response required, but adds flag for later consequences]
```

**Pros**: Much simpler to implement (1-2 hours)  
**Cons**: Less dramatic, no real-time interaction  

---

## Success Criteria

### Minimum Viable:
✅ Russian ultimatum triggers on aggressive action  
✅ Message delivered with drama  
✅ Flags set correctly  
✅ Game doesn't break  

### Full Success:
✅ 5+ trigger types working  
✅ Interactive calls allow response  
✅ Narrative-specific calls trigger correctly  
✅ Players report increased tension/immersion  
✅ Consequences feel fair and meaningful  

---

## Recommendation

**Implement Phase 1 immediately** (4 hours)
- Addresses critical gap in gameplay
- Adds dramatic tension
- Makes world feel more reactive
- Relatively straightforward implementation

**Add Phases 2-3 for Beta** (4 hours)
- LLM quality improvement
- Interactive response system

**Consider Phase 4 post-launch** (2-4 hours)
- Advanced features if players love the system
- Countdown timers, interrupts, etc.

**Estimated Total: 6-8 hours for full system**  
**Immediate Value: High (core realism feature)**  
**Player Impact: Significant (changes power dynamic)**

---

**Report Compiled**: November 8, 2025  
**Status**: Ready for implementation  
**Priority**: P1 - Should implement before Beta  
**Dependencies**: None (builds on existing diplomatic system)

