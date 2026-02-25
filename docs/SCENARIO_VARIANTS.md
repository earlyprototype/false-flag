# Scenario Variants System

## Overview

The wargame now supports multiple scenario variants with different pacing and complexity levels. Players can choose their preferred experience at game start through an interactive menu.

## Available Scenarios

### 1. Standard Campaign
**Difficulty:** Moderate  
**Estimated Time:** 90-120 minutes  
**Scripted Turns:** 6  
**Stochastic From:** Turn 7

**Description:** Experience the full crisis as it unfolds over 6 scripted turns

**Features:**
- Gradual escalation from diplomatic crisis to missile launch
- 6 hours of in-game time before stochastic gameplay
- Full NATO consultation and diplomatic complexity
- Detailed world-building and character development

**Recommended For:** First-time players, narrative focus

**Timeline:**
- **Turn 1** (17:00): Initial COBRA briefing - F-35 pilots murdered, Russian fleet deployed
- **Turn 2** (19:00): Submarine surfaces near Orkney, public panic begins
- **Turn 3** (21:00): Drax Power Station explosion, infrastructure attack
- **Turn 4** (00:00): NATO consultation, alliance fracturing
- **Turn 5** (03:00): Ballistic missile launch (8-12 minute warning)
- **Turn 6** (05:00): Actual strikes - war begins
- **Turn 7+**: Stochastic LLM-generated gameplay

---

### 2. Fast Start ⚡
**Difficulty:** Intense  
**Estimated Time:** 45-60 minutes  
**Scripted Turns:** 3  
**Stochastic From:** Turn 4

**Description:** Compressed timeline - reach critical decisions faster

**Features:**
- Rapid escalation with breaking developments mid-turn
- 3 hours of in-game time before stochastic gameplay
- All key narrative beats preserved but compressed
- Faster path to player-driven emergent gameplay

**Recommended For:** Experienced players, replay value, time-limited sessions

**Timeline:**
- **Turn 1** (17:00-19:00): COBRA briefing + Breaking submarine provocation
- **Turn 2** (21:00-00:00): Infrastructure attack + NATO consultation
- **Turn 3** (03:00): Ballistic missile launch
- **Turn 4+**: Stochastic LLM-generated gameplay

---

## How It Works

### Scenario Selection Menu

When you start a new game, you'll see:

```
# FALSE FLAG: THE WARGAME
===============================================================================

SELECT SCENARIO

1. Standard Campaign
   Difficulty: Moderate
   Estimated Time: 90-120 minutes
   Experience the full crisis as it unfolds over 6 scripted turns
   
   • Gradual escalation from diplomatic crisis to missile launch
   • 6 hours of in-game time before stochastic gameplay
   • Full NATO consultation and diplomatic complexity
   
   Recommended for: First-time players, narrative focus

2. Fast Start
   Difficulty: Intense
   Estimated Time: 45-60 minutes
   Compressed timeline - reach critical decisions faster
   
   • Rapid escalation with breaking developments mid-turn
   • 3 hours of in-game time before stochastic gameplay
   • All key narrative beats preserved but compressed
   
   Recommended for: Experienced players, replay value, time-limited sessions

Select scenario (enter number):
```

### Technical Implementation

**File Structure:**
```
data/scenarios/war_game_2025/
├── scenarios.yaml              # Scenario variant registry
├── initial_conditions.yaml     # Shared initial conditions
└── episodes/
    ├── turn_001.yaml          # Standard Turn 1
    ├── turn_002.yaml          # Standard Turn 2
    ├── turn_003.yaml          # Standard Turn 3
    ├── turn_004.yaml          # Standard Turn 4
    ├── turn_005.yaml          # Standard Turn 5
    ├── turn_006.yaml          # Standard Turn 6
    ├── turn_001_fast.yaml     # Fast Start Turn 1
    ├── turn_002_fast.yaml     # Fast Start Turn 2
    └── turn_003_fast.yaml     # Fast Start Turn 3
```

**Configuration (`scenarios.yaml`):**
```yaml
scenarios:
  standard:
    name: "Standard Campaign"
    description: "Experience the full crisis..."
    scripted_turns: 6
    turn_prefix: "turn_"
    turn_suffix: ""              # Uses turn_001.yaml
    stochastic_from: 7
    
  fast_start:
    name: "Fast Start"
    description: "Compressed timeline..."
    scripted_turns: 3
    turn_prefix: "turn_"
    turn_suffix: "_fast"         # Uses turn_001_fast.yaml
    stochastic_from: 4
```

## Command Line Usage

### Interactive Menu (Default)
```powershell
.\.venv\Scripts\python.exe -m cli.main play
# Shows scenario selection menu
```

### Skip Menu (Specify Variant)
```powershell
# Standard campaign
.\.venv\Scripts\python.exe -m cli.main play --variant standard

# Fast Start
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start
```

### Dynamic Generation (Default Behaviour)
```powershell
# Dynamic generation is ENABLED BY DEFAULT
# Standard: generates content after Turn 6
.\.venv\Scripts\python.exe -m cli.main play --variant standard

# Fast Start: generates content after Turn 3
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start

# To play ONLY scripted content (disable dynamic generation):
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start --no-stochastic-injects
```

## Compression Strategy

### How Fast Start Preserves Narrative

Fast Start compresses 6 turns into 3 without sacrificing world-building by:

1. **Breaking News Interrupts**: Turn 1 starts with the COBRA briefing, then a breaking update interrupts mid-turn with the submarine provocation
2. **Embedded Reactions**: Turn 2 includes the infrastructure attack, then NATO's response arrives as a phone call during the crisis
3. **Perfect Climax**: Turn 3 (missile launch) is preserved exactly as-is - it's the ideal transition to stochastic gameplay

### What's Preserved

✅ All key events (F-35 murders, submarine, Drax explosion, NATO fracturing, missile launch)  
✅ All advisor perspectives and personalities  
✅ Diplomatic complexity and alliance tensions  
✅ Escalation curve and psychological pressure  
✅ Decision complexity and strategic dilemmas

### What's Different

- **Pacing:** 2 crisis moments per turn instead of 1
- **Timeline:** 3 hours to missile launch vs 10 hours
- **Breathing room:** Less time between decisions
- **Urgency:** Breaking developments feel more immediate

## Adding New Variants

To create a new scenario variant:

1. **Add to `scenarios.yaml`:**
```yaml
scenarios:
  your_variant:
    name: "Your Variant Name"
    description: "Description"
    difficulty: "Easy/Moderate/Hard/Intense"
    scripted_turns: 3
    turn_prefix: "turn_"
    turn_suffix: "_yourvariant"
    stochastic_from: 4
    estimated_time: "30-45 minutes"
    features:
      - "Feature 1"
      - "Feature 2"
    recommended_for: "Who should play this"
```

2. **Create turn files:**
```
episodes/turn_001_yourvariant.yaml
episodes/turn_002_yourvariant.yaml
episodes/turn_003_yourvariant.yaml
```

3. **Test:**
```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant your_variant
```

The variant will automatically appear in the selection menu!

## Design Philosophy

### ADHD-Friendly Considerations

The scenario system is designed with ADHD-friendly principles:

- **Clear choice architecture:** 2 distinct options, not overwhelming
- **Transparent time commitments:** Estimated duration shown upfront
- **Flexible engagement:** Choose intensity based on current capacity
- **Progress tracking:** Know exactly when stochastic gameplay begins
- **No wrong choice:** Both variants are complete experiences

### Replay Value

Different variants encourage replay:
- **First playthrough:** Standard for full narrative immersion
- **Subsequent plays:** Fast Start to explore different strategies
- **Time-limited:** Fast Start for shorter sessions
- **Experimentation:** Fast Start to quickly reach emergent gameplay

## Future Variants (Ideas)

Potential future scenarios:

- **Sandbox Mode:** Start with stochastic generation from Turn 1
- **Tutorial Mode:** Extended first turn with advisor guidance
- **Nightmare Mode:** Compressed timeline + worse starting metrics
- **Historical Mode:** Based on actual Cold War crises
- **Multiplayer Mode:** Different players control different advisors

## Technical Notes

### Save Game Compatibility

- Save files store the variant used
- Loading a save continues with the same variant
- No cross-contamination between variants

### Stochastic Generation

- Each variant specifies when LLM generation begins
- Standard: Turn 7+ (after 6 scripted turns)
- Fast Start: Turn 4+ (after 3 scripted turns)
- LLM uses full transcript history regardless of variant

### Performance

- Scenario selection adds ~100ms to startup
- No performance impact during gameplay
- Turn file loading is identical for all variants

---

**Ready to play?**

```powershell
.\.venv\Scripts\python.exe -m cli.main play
```

Choose your scenario and begin the crisis. 🎮

