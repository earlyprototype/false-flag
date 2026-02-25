# FALSE FLAG: THE WARGAME - Developer Handover Package

**Package Date**: November 8, 2025  
**Build Status**: Dynamic Narrative System - Phase 3 Complete  
**Ready for**: Alpha Testing with UX fixes required  

---

## 📦 Package Contents

This handover package contains all documentation needed to understand, maintain, and extend the False Flag wargame project.

### 🎯 Start Here

1. **[HANDOVER_SUMMARY.md](./HANDOVER_SUMMARY.md)** - Executive overview of the project
2. **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** - Technical architecture guide
3. **[PLAYTEST_FEEDBACK.md](./PLAYTEST_FEEDBACK.md)** - Latest testing results and issues
4. **[IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)** - What's done, what's pending

### 📚 Core Documentation

#### User-Facing
- **[GAME_DESCRIPTION.md](./GAME_DESCRIPTION.md)** - What is False Flag?
- **[PLAYER_COMMANDS.md](./PLAYER_COMMANDS.md)** - In-game command reference

#### System Documentation
- **[DYNAMIC_NARRATIVE_SYSTEM.md](./DYNAMIC_NARRATIVE_SYSTEM.md)** - Core replayability feature
- **[SCENARIO_VARIANTS.md](./SCENARIO_VARIANTS.md)** - Standard vs Fast Start modes
- **[DIPLOMATIC_SYSTEM.md](./DIPLOMATIC_SYSTEM.md)** - How foreign leader interactions work
- **[CRITICAL_OMISSIONS_SYSTEM.md](./CRITICAL_OMISSIONS_SYSTEM.md)** - Advisor pushback mechanics

#### Development Guides
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Installation and configuration
- **[DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md)** - How to add features
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - QA procedures

#### Enhancement Proposals
- **[NUCLEAR_COMMAND_CHAIN_SYSTEM.md](./NUCLEAR_COMMAND_CHAIN_SYSTEM.md)** - 🔴 **P0 CRITICAL** - Prevent nuclear exploits
- **[INCOMING_DIPLOMATIC_CALLS.md](./INCOMING_DIPLOMATIC_CALLS.md)** - P1 - Allow foreign nations to contact the PM
- **[GEMINI_PRO_HYBRID_SYSTEM.md](./GEMINI_PRO_HYBRID_SYSTEM.md)** - P2 - Strategic use of Pro model for quality
- **[ADVISOR_SENTIMENT_SYSTEM.md](./ADVISOR_SENTIMENT_SYSTEM.md)** - P2 - Interpersonal trust tracking

---

## 🚀 Quick Start for New Developers

### Prerequisites
- Python 3.10+
- Google Gemini API key
- Windows 10/11 (native), or Linux/Mac (compatibility mode)

### Setup (5 minutes)
```bash
# Clone repository
cd wargame

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API
# Create .env file with: GEMINI_API_KEY=your_key_here

# Run game
python -m cli.main play
```

### First Changes to Make
1. **Read**: [PLAYTEST_FEEDBACK.md](./PLAYTEST_FEEDBACK.md) - Critical issues list
2. **Fix**: Issue #7 (Decision cancellation flow) - See line references in feedback doc
3. **Test**: Run Fast Start mode to Turn 2, cancel a decision, verify flow
4. **Deploy**: Update changelog, commit, tag release

---

## 📊 Project Status Overview

### ✅ Completed Features (Production Ready)
- Turn-based COBRA meeting simulation
- LLM-driven advisor personalities (Gemini 2.5 Flash)
- Dynamic event generation (scripted + procedural)
- Diplomatic system with dynamic access levels
- Scenario variants (Standard + Fast Start)
- **Dynamic Narrative System (NEW)** - Multiple hidden story paths
- Rich CLI with color coding and tables
- Save/load game state
- Metrics tracking and adjudication
- Critical omissions checker

### 🟡 Completed Features (Need Polish)
- Text formatting (markdown leakage)
- Advisor identity consistency
- Score display timing
- Critical advisory UI

### 🔲 Planned Features (Not Started)
- Bilateral relationship tracking
- International newspaper briefings  
- Private advisor conversations
- Additional narrative paths (Irish Connection, US Contractors, etc.)
- Difficulty scaling improvements
- Victory/defeat conditions

---

## 🐛 Known Issues (As of Nov 8, 2025)

### Critical (P0)
- **Issue #7**: Decision cancellation returns to turn start instead of discussion phase
- **Issue #14**: Advisor identity collapse - can't consistently address specific advisors

### High Priority (P1)  
- **Issue #1**: Markdown formatting leaking through (`**bold**` visible)
- **Issue #5**: Player input duplicated in diplomatic calls
- **Issue #9**: Meta-text in stochastic inject headers
- **Issue #13**: Score display timing confuses causality

See [PLAYTEST_FEEDBACK.md](./PLAYTEST_FEEDBACK.md) for full list with technical details.

---

## 🏗️ Architecture at a Glance

```
wargame/
├── cli/main.py              # Game loop, UI orchestration
├── engine/
│   ├── sim_loop.py         # Turn phase orchestration
│   ├── diplomacy.py        # Foreign leader conversations
│   ├── narrative_adjudication.py  # LLM-based scoring
│   └── scenario_loader.py  # Content loading
├── models/
│   ├── world.py            # Game state
│   ├── narrative.py        # Story configuration
│   └── narrative_state.py  # Hidden metrics/characters
├── llm/
│   ├── router.py           # LLM call orchestration
│   ├── context_builder.py  # Role-based context assembly
│   └── prompts.py          # Prompt templates
├── agents/
│   └── conversation.py     # Advisor interaction logic
└── data/scenarios/
    └── war_game_2025/
        ├── initial_conditions.yaml
        ├── narratives.yaml      # Story paths (NEW)
        └── episodes/            # Turn-by-turn content
```

**Key Design Patterns**:
- **Separation of Concerns**: Models, Engine, LLM, UI layers independent
- **Role-Based Context**: Different LLM agents get filtered information
- **Event-Driven**: Injects trigger effects → Effects update metrics → Metrics trigger crises
- **Narrative Layer**: Secret truths guide AI behavior without explicit revelation

---

## 🎮 Gameplay Flow

```
New Game
  ↓
Select Scenario Variant (Standard / Fast Start)
  ↓
Select Play Mode (Classic / Immersive / Emergent)
  ↓
Select Difficulty (Standard / Challenging / Brutal)
  ↓
Select Narrative (Russia Aggression / China Proxy / Random) [HIDDEN]
  ↓
View Intro Scenes (cinematic text with pauses)
  ↓
┌─────────────── MAIN GAME LOOP ───────────────┐
│                                               │
│  TURN N                                       │
│    ↓                                          │
│  BRIEFING PHASE                               │
│    • Load inject (scripted or generated)     │
│    • Apply inject effects to metrics         │
│    • Display to player                       │
│    ↓                                          │
│  DISCUSSION PHASE                             │
│    • Player asks advisors questions          │
│    • Can use commands (/menu, /call, etc)    │
│    • Loop until player types /decision       │
│    ↓                                          │
│  DECISION PHASE                               │
│    • Player states action/decision           │
│    • LLM interprets intent                   │
│    • Advisors provide pushback (if needed)   │
│    • Critical concerns raised (if severe)    │
│    • Player confirms, amends, or cancels     │
│    ↓                                          │
│  ADJUDICATION PHASE                           │
│    • LLM assesses decision quality           │
│    • Apply metric changes                    │
│    • Generate character responses            │
│    • Update advisor trust scores             │
│    • Check for crisis triggers               │
│    ↓                                          │
│  [Metrics displayed]                         │
│    ↓                                          │
│  Turn N+1 → Loop back to BRIEFING            │
│                                               │
└───────────────────────────────────────────────┘
```

---

## 🔑 Key Technologies

- **Python 3.10+**: Core language
- **Rich**: Terminal UI library (colors, tables, panels)
- **Typer**: CLI framework
- **Pydantic**: Data validation and models
- **PyYAML**: Scenario content loading
- **Google Gemini 2.5 Flash**: LLM for all text generation
- **msvcrt**: Windows keyboard input (for spacebar prompts)

---

## 📞 Support & Resources

### Documentation Links
- Full architecture: [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)
- Narrative system details: [DYNAMIC_NARRATIVE_SYSTEM.md](./DYNAMIC_NARRATIVE_SYSTEM.md)
- Latest bugs: [PLAYTEST_FEEDBACK.md](./PLAYTEST_FEEDBACK.md)

### Getting Help
- Check `/analysis/` folder for detailed technical discussions
- Review Git history for context on specific implementations
- LLM integration patterns in `/llm/prompts.py`

### Contributing
1. Review [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md)
2. Pick an issue from [PLAYTEST_FEEDBACK.md](./PLAYTEST_FEEDBACK.md)
3. Create feature branch
4. Write tests (see [TESTING_GUIDE.md](./TESTING_GUIDE.md))
5. Submit PR with clear description

---

## 📈 Roadmap Priorities

### Immediate (Before Next Playtest)
1. Fix critical UX issues (decision flow, advisor identity)
2. Clean up text formatting (markdown removal)
3. Polish UI presentation

### Short Term (Next Sprint)
4. Implement bilateral relationship system
5. Add newspaper-style international briefings
6. Expand narrative options (3-4 more paths)

### Medium Term (Next Quarter)
7. Multiplayer support (multiple cabinet members)
8. Mobile/web interface
9. Save replay/AAR generation
10. Steam/itch.io release

### Long Term (Future)
11. Scenario editor
12. Community scenario sharing
13. AI opponent for PvE mode
14. VR integration for immersive cabinet room

---

**Package Maintained By**: Development Team  
**Last Updated**: November 8, 2025  
**Next Review**: After Phase 1 fixes complete

