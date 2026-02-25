# Free-Form Wargame Engine Refactor - Complete

**Date:** 27 October 2025  
**Status:** MVP Complete

## Summary

Successfully refactored the wargame from a proposal-based system to a free-form conversational model with two-phase turn structure. The game now supports:

1. **Conversational Advisors**: Players can ask questions and get in-character LLM-generated responses
2. **Free-Form Actions**: Players describe their actions in natural language
3. **Advisor Pushback**: LLM generates warnings when actions violate constraints
4. **Episode-Based Injects**: Turn-by-turn inject files with optional stochastic generation
5. **Save/Load**: Persistent game state across sessions
6. **Interactive CLI**: Full discussion → decision → adjudication flow

## Architecture Changes

### Core Components Created

1. **`engine/events.py`**: Episode-based inject loading (`load_inject_for_turn`)
2. **`engine/initial_conditions.py`**: Parses scenario setup YAML
3. **`engine/persistence.py`**: Save/load game state
4. **`engine/sim_loop.py`**: Refactored for two-phase turns
5. **`llm/prompts.py`**: LLM prompt templates for advisors, interpretation, pushback
6. **`agents/conversation.py`**: Conversational advisor system
7. **`llm/inject_generator.py`**: Stochastic inject generation
8. **`cli/main.py`**: Interactive CLI with discussion and decision phases

### Models Updated

- **`models/world.py`**: Added `turn`, `phase`, `spatial_state`, `discussion_transcript` fields

### Files Removed

- `agents/advisors.py` (old hardcoded proposals)
- `agents/leader.py` (old proposal selection)
- `assets/init/wargame_initial_conditions.yaml` (duplicate)
- Legacy placeholder files

### LLM Integration

- **Mock Driver**: Deterministic template-based responses for testing (current)
- **Gemini 2.5 Flash**: Planned for production (stretch goal)
- **Router**: Provider-agnostic with `generate_text()` interface

## Game Flow

### Turn Structure

```
1. BRIEFING PHASE
   - Load inject from episodes/turn_NNN.yaml
   - If missing + stochastic mode: LLM generates inject
   - Display inject and apply effects

2. DISCUSSION PHASE (loop)
   - Player asks questions
   - LLM generates in-character advisor responses
   - No world state changes
   - Player types 'decide' when ready

3. DECISION PHASE
   - Player enters action
   - LLM interprets action
   - LLM generates advisor pushback (if any)
   - Player confirms or cancels

4. ADJUDICATION PHASE
   - Apply action effects to world state
   - Update metrics and flags
   - Auto-save game
   - Advance to next turn
```

### CLI Commands

```bash
# Interactive mode
python -m cli.main play --scenario war_game_2025 --seed 42

# Load saved game
python -m cli.main play --load saves/war_game_2025_turn_003.json

# Stochastic inject generation
python -m cli.main play --stochastic-injects

# Batch mode (testing)
python -m cli.main batch --scenario war_game_2025 --seed 42

# Display intro
python -m cli.main intro
```

## Initial Conditions

Created comprehensive `data/scenarios/war_game_2025/initial_conditions.yaml` with:

- **Metadata**: Title, description, start date
- **Metrics**: Initial values for escalation, stability, cohesion, etc.
- **Characters**: UK advisors and Russian team with knowledge domains and pushback triggers
- **Forces**: UK naval and air assets with locations and readiness
- **Stockpiles**: Ammunition counts by category
- **Constraints**: Capability, political, legal, time limitations
- **Intelligence**: What UK knows vs what Russia knows
- **Objectives**: Primary and secondary goals for both sides

## Episode Files

Created `data/scenarios/war_game_2025/episodes/turn_001.yaml` based on podcast:

- COBRA briefing with F-35 pilot murders, Severomorsk false flag, Russian naval deployment
- Effects: +6 escalation risk, -4 domestic stability

Future episodes (2-4) to be added as podcast content is analyzed.

## Testing

### Current Status

- ✅ Episode loading works
- ✅ Initial conditions loading works
- ✅ Two-phase turn structure works
- ✅ Mock LLM responses work
- ✅ Save/load works
- ✅ Interactive CLI works
- ⚠️ Golden transcript needs update (format changed)
- ⚠️ Seed smoke test needs update (no longer uses proposals)

### Next Steps

1. Update gate tests for new system
2. Create episodes for turns 2-50 (podcast episode 1)
3. Add Gemini 2.5 Flash driver
4. Playtest and refine advisor responses
5. Add progressive disclosure (stretch goal)
6. Implement spatial model for unit tracking (stretch goal)

## Key Design Decisions

1. **Mock-first approach**: Get game flow working with deterministic mock, add real LLM later
2. **Episode files over database**: Simple YAML files for easy editing and version control
3. **Heuristic adjudication**: Simple keyword-based effects for MVP, can be enhanced later
4. **UK-centric**: Player is PM, advisors are UK government, Russia is controlled by injects
5. **Named locations**: Simple spatial model (not hex grid) matching podcast structure

## Known Issues

- Gate tests need updating for new system
- Adjudication is currently heuristic (keyword-based), not sophisticated
- No real LLM integration yet (mock only)
- Only turn 1 inject created so far

## Files Modified

- `engine/events.py` - Added episode loading
- `engine/sim_loop.py` - Complete refactor for two-phase turns
- `engine/adjudicator.py` - Kept for compatibility, not used in new system
- `llm/router.py` - Added `generate_text()` for conversational system
- `llm/mock_driver.py` - Added text generation support
- `llm/offline_driver.py` - Updated for new interface
- `llm/client.py` - Updated protocol for text generation
- `models/world.py` - Added turn/phase tracking
- `cli/main.py` - Complete rewrite for interactive mode
- `data/scenarios/war_game_2025/initial_conditions.yaml` - Enhanced with characters, forces, constraints

## Success Metrics

✅ Player can ask advisors questions  
✅ Player can enter free-form actions  
✅ Advisors provide in-character responses  
✅ Advisors push back on implausible actions  
✅ Game state persists across sessions  
✅ Injects load from episode files  
✅ Stochastic inject generation works (mock)  
✅ Two-phase turn structure implemented  
✅ Interactive CLI fully functional  

## Conclusion

The MVP is complete and functional. The game can now be played interactively with conversational advisors, free-form player input, and proper turn structure. Next phase is to add real LLM integration (Gemini 2.5 Flash) and create more episode content.

