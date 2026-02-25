# Narrative Selection Menu - Design Correction

**Date:** Saturday, 9 November 2025  
**Priority:** 🔴 HIGH - Affects player experience  
**For:** Team 2 (Narrative System)  
**Issue:** Current menu reveals which narrative is active (spoils mystery)

---

## THE PROBLEM

**Current Implementation:**
```
SELECT NARRATIVE

1. Russia Aggression
   The crisis is exactly as it appears: Russia is undertaking a major 
   aggressive military operation...
   
2. China Proxy War
   This crisis is a sophisticated proxy operation by China...
   
3. Random
```

**Why This Is Wrong:**
- ❌ Player sees exactly which narrative is active
- ❌ Spoils the mystery and deduction challenge
- ❌ Defeats the purpose of hidden motivations
- ❌ "Random" doesn't make sense when player sees the options

---

## THE SOLUTION

### Corrected Menu Design

```
# FALSE FLAG: THE WARGAME
===============================================================================

SELECT GAME TYPE

Choose how you want to experience the crisis:

1. Original Story Mode
   Play the standard story mode as designed. Experience the crisis through
   the eyes of the Prime Minister as events unfold.
   
2. Mystery Mode
   A hidden narrative guides AI agent behaviour. Foreign leaders and 
   diplomats may have secret motivations that aren't immediately apparent.
   You must deduce the truth from their actions and responses.
   
   ⚠ The narrative is randomly selected and hidden from you!

Select game type (enter number):
```

---

## IMPLEMENTATION CHANGES

### File: `cli/main.py`

**Function to Change:** `select_narrative(scenario_id: str)`

**New Signature:**
```python
def select_game_type(scenario_id: str) -> Optional[NarrativeConfig]:
    """Display game type selection menu (Original vs Mystery).
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        NarrativeConfig if Mystery mode selected (randomly chosen),
        None if Original Story Mode selected
    """
```

**New Logic:**
```python
# Display menu with 2 options
console.print("1. Original Story Mode")
console.print("   Play the standard story mode as designed...")
console.print("")
console.print("2. Mystery Mode")
console.print("   A hidden narrative guides AI agent behaviour...")
console.print("   ⚠ The narrative is randomly selected and hidden from you!")
console.print("")

choice = typer.prompt("Select game type (enter number)", type=int, default=1)

if choice == 1:
    # Original Story Mode - no secret narrative
    return None
elif choice == 2:
    # Mystery Mode - randomly select narrative
    narratives = load_narrative_configs(scenario_id)
    if narratives:
        import random
        selected = random.choice(narratives)
        console.print("")
        console.print(f"[{COLORS['success']} bold]✓ Mystery Mode activated[/{COLORS['success']} bold]")
        console.print("")
        # DO NOT tell player which narrative was selected
        return selected
    else:
        # Fallback if no narratives available
        return None
```

**Update WorldState Initialization:**
```python
# If selected_game_type is None → Original Story Mode (no narrative)
# If selected_game_type is NarrativeConfig → Mystery Mode (has narrative)

world = WorldState(
    turn=1,
    scene=1,
    difficulty=difficulty,
    narrative=selected_game_type,  # None or NarrativeConfig
    metrics=Metrics(...),
    flags={},
    posture={},
)
```

---

## GAMEPLAY EXPERIENCE

### Original Story Mode (narrative = None)
```
Player Experience:
• AI agents behave straightforwardly
• Russia is aggressive (as stated in briefings)
• France supports NATO (as expected)
• China calls for restraint (neutral position)
• No hidden agendas
• Scripted narrative as designed
```

### Mystery Mode (narrative = random selection)
```
Player Experience:
• Player NEVER told which narrative is active
• AI agents may have hidden motivations
• Player observes inconsistencies:
  - "France seems hesitant about Article 5..."
  - "USA is oddly suspicious of something..."
  - "China is being unusually 'helpful'..."
• Player must deduce: "Wait, is this a proxy operation?"
• Replayability: Different narrative each playthrough
• Genuine mystery and investigation gameplay
```

---

## EXAMPLES

### Example 1: Original Story Mode
```
Startup Flow:
1. Variant: Fast Start
2. Play Mode: Immersive
3. Difficulty: Standard
4. Game Type: Original Story Mode ← Selected
5. Begin gameplay

Result:
• world.narrative = None
• AI agents behave as written in briefings
• No hidden agendas
• Standard intended experience
```

### Example 2: Mystery Mode (Hidden China Narrative)
```
Startup Flow:
1. Variant: Fast Start
2. Play Mode: Immersive
3. Difficulty: Standard
4. Game Type: Mystery Mode ← Selected
5. System secretly selects: CHINA_PROXY_WAR
6. Begin gameplay (player doesn't know it's China)

Result:
• world.narrative = NarrativeConfig(CHINA_PROXY_WAR)
• Player sees: "✓ Mystery Mode activated"
• Player NOT told: Which narrative
• AI agents behave according to China narrative
• Player must deduce from behaviour
```

---

## SAVE/LOAD BEHAVIOUR

### Saving
```python
save_data = {
    "world": {
        "narrative": world.narrative.model_dump() if world.narrative else None
    }
}
```

### Loading
```python
# When loading Mystery Mode save:
# • Narrative is restored
# • Player still doesn't know which narrative
# • Maintains mystery even across sessions
```

---

## TESTING CHECKLIST

**Test 1: Original Story Mode**
```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start

# Select:
# 1. Play Mode: Immersive
# 2. Difficulty: Standard
# 3. Game Type: 1 (Original Story Mode)

# Expected:
✓ No narrative selected message
✓ world.narrative = None
✓ AI agents behave straightforwardly
```

**Test 2: Mystery Mode**
```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start

# Select:
# 1. Play Mode: Immersive
# 2. Difficulty: Standard
# 3. Game Type: 2 (Mystery Mode)

# Expected:
✓ "Mystery Mode activated" message
✓ NO indication of which narrative
✓ world.narrative = (one of the narratives, randomly chosen)
✓ AI agents behave according to hidden narrative
```

**Test 3: Save/Load Mystery Mode**
```powershell
# Start Mystery Mode, play 1 turn, /save
# Exit
# Reload

# Expected:
✓ Narrative preserved
✓ Still don't know which narrative
✓ AI agents continue behaving consistently
```

---

## WHY THIS DESIGN IS BETTER

**1. Preserves Mystery:**
- ✅ Player genuinely doesn't know the truth
- ✅ Must deduce from AI agent behaviour
- ✅ Replayability: "Was that China again, or something else?"

**2. Clear Player Choice:**
- ✅ "Original" = Standard intended experience
- ✅ "Mystery" = Replayability variant
- ✅ No confusion about what they're selecting

**3. Better UX:**
- ✅ Simple binary choice (not 3+ options)
- ✅ Clear expectations set upfront
- ✅ "Original" as default (safe choice)

**4. Maintains Surprise:**
- ✅ Mystery Mode players get genuine detective experience
- ✅ No spoilers in menu text
- ✅ Hidden agendas remain hidden

---

## INTEGRATION WITH PHASE 2 WORK

**No Changes Needed:**
- ✅ Play Mode selection (Classic/Immersive/Emergent) unchanged
- ✅ NarrativeState initialization unchanged
- ✅ Display system unchanged
- ✅ Save/load system already handles `narrative = None`

**The systems remain independent:**
- Game Type (yours) = WHETHER there's a secret truth
- Play Mode (ours) = HOW player sees the game

---

## SUMMARY OF CHANGES

**Rename Function:**
- `select_narrative()` → `select_game_type()`

**Change Return Type:**
- From: Always returns NarrativeConfig
- To: Returns `Optional[NarrativeConfig]` (None for Original, Config for Mystery)

**Change Menu:**
- From: List of narratives (Russia/China/Random)
- To: Binary choice (Original Story Mode / Mystery Mode)

**Hide Selection:**
- Never tell player which narrative was randomly selected
- Only confirm "Mystery Mode activated"

---

**PRIORITY:** Implement before public testing  
**IMPACT:** Affects core game experience and replayability  
**DEPENDENCIES:** None (our Phase 2 work already compatible)

---

**END OF SPECIFICATION**

*Preserving mystery for better player experience*



