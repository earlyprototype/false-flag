# Automatic Stochastic Generation

## What Changed

Dynamic scenario generation is now **enabled by default** and **automatically activates** when you reach the end of scripted content.

## How It Works

### Seamless Transition

When you reach the transition point:
- **Standard Campaign:** After Turn 6
- **Fast Start:** After Turn 3

You'll see:
```
===============================================================================
ENTERING DYNAMIC SCENARIO GENERATION
===============================================================================

The scripted scenario has concluded. From this point forward,
events will be dynamically generated based on your decisions.

Press SPACE to continue...
```

The game then continues seamlessly with LLM-generated content based on your previous decisions and the current world state.

## Default Behaviour

### Before This Change
```powershell
# Required manual flag
.\.venv\Scripts\python.exe -m cli.main play --stochastic-injects
```

### After This Change
```powershell
# Works automatically - no flag needed!
.\.venv\Scripts\python.exe -m cli.main play
```

## Disabling Dynamic Generation

If you want to play **only** the scripted content:

```powershell
.\.venv\Scripts\python.exe -m cli.main play --no-stochastic-injects
```

The game will end gracefully after the last scripted turn.

## Benefits

1. **No Technical Knowledge Required:** Players don't need to understand flags
2. **Seamless Experience:** Automatic transition with clear messaging
3. **No "No Inject" Errors:** Game continues naturally
4. **Still Controllable:** Can disable with `--no-stochastic-injects` if desired

## What Gets Generated

After the transition, the LLM generates:
- New crisis events based on your decisions
- Advisor responses reflecting the evolving situation
- Metric effects appropriate to the scenario
- Diplomatic encounters and complications
- Escalation patterns consistent with your actions

All generation uses:
- Full game transcript history
- Current world state and metrics
- Initial scenario conditions
- Scenario library for thematic consistency

## Testing

To test the transition:

### Fast Start (3 turns to transition)
```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start
# Play through Turns 1-3
# Turn 4 will show transition message and generate content
```

### Standard (6 turns to transition)
```powershell
.\.venv\Scripts\python.exe -m cli.main play --variant standard
# Play through Turns 1-6
# Turn 7 will show transition message and generate content
```

## Technical Details

### Implementation

**File:** `cli/main.py`

**Logic:**
1. Check if `world.turn >= stochastic_from_turn`
2. If true and stochastic not yet enabled, show transition message
3. Auto-enable `stochastic_injects = True`
4. Continue game loop with LLM generation

**Default Flag:**
```python
stochastic_injects: bool = typer.Option(True, "--stochastic-injects/--no-stochastic-injects", ...)
```

### Scenario Configuration

Each scenario variant defines when to transition:

```yaml
# scenarios.yaml
fast_start:
  stochastic_from: 4  # Transition at Turn 4
  
standard:
  stochastic_from: 7  # Transition at Turn 7
```

---

**Result:** Players can now enjoy the full game experience without needing to understand technical flags or worry about "no inject" errors!



