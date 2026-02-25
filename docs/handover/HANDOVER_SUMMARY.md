# FALSE FLAG: THE WARGAME - Executive Handover Summary

**Date**: November 8, 2025  
**Status**: Alpha - Core Systems Complete, UX Polish Required  
**Next Milestone**: Beta Release after Phase 1 Fixes  

---

## What Is This Project?

False Flag is a **single-player wargame simulation** where you play as the UK Prime Minister managing a crisis with Russia. It combines:

- **Turn-based strategy** with narrative consequences
- **LLM-powered advisors** that remember your decisions and provide contextual advice
- **Dynamic storytelling** where hidden "narrative truths" shape how foreign leaders behave
- **Diplomatic simulation** with real-time conversations with world leaders
- **Branching scenarios** that respond to your choices

**Target Audience**: Strategy gamers, political simulation fans, military history enthusiasts

**Unique Selling Point**: Every playthrough feels different because the LLM creates unique responses, and the hidden narrative system means you're solving a mystery while managing a crisis.

---

## Project Timeline

### Development History
- **Initial Build** (Pre-Oct 2025): Basic turn-based CLI game with keyword-based adjudication
- **Phase 1** (Oct 2025): LLM integration for advisors and dynamic conversations
- **Phase 2** (Oct-Nov 2025): Narrative state tracking, character attitudes, hidden metrics
- **Phase 3** (Nov 2025): **Dynamic Narrative System** - Multiple story paths with different NPC behaviors
- **Current** (Nov 8, 2025): First playtest complete, bug fixing phase

### What Was Just Completed
✅ **Dynamic Narrative System** - The game's signature feature
- Players select (or are randomly assigned) a "narrative truth" at game start
- Foreign diplomats behave according to secret motivations
- Example: In "Russia Aggression" narrative, USA is supportive. In "China Proxy War" narrative, USA is evasive and suspicious.
- System is fully integrated across all LLM agents

---

## Current State

### ✅ What Works (Production Quality)
1. **Core Gameplay Loop**: Briefing → Discussion → Decision → Adjudication
2. **Advisor System**: 5 distinct UK cabinet advisors with personalities and expertise
3. **Diplomatic System**: Call foreign leaders, have multi-turn conversations
4. **Scenario Variants**: "Standard Campaign" (slower) vs "Fast Start" (compressed)
5. **Dynamic Events**: Scripted turns (1-6) transition to LLM-generated content
6. **Metrics System**: 5 tracked metrics affect gameplay (Escalation, Stability, Cohesion, Casualties)
7. **Save/Load**: Can save mid-game and resume
8. **Rich UI**: Color-coded text, tables, formatted panels

### 🟡 What Works (Needs Polish)
1. **Text Formatting**: Markdown leaking through (`**bold**` visible to player)
2. **Advisor Identity**: Sometimes merges into single voice
3. **UI Timing**: Scores display at wrong moment in turn flow
4. **Critical Warnings**: Too cluttered, hard to read

### 🔴 What's Broken (Critical)
1. **Decision Cancellation**: Returns to turn start instead of discussion phase
2. **Advisor Addressing**: Can't consistently talk to specific advisors

### 🔲 What's Missing (Planned)
1. **Bilateral Relationships**: Individual scores with each country
2. **Newspaper Briefings**: International developments at turn start
3. **More Narratives**: Only 2 narrative paths currently (Russia Aggression, China Proxy War)
4. **Victory Conditions**: Game continues indefinitely, no win/lose states

---

## Technical Overview

### Architecture
- **Language**: Python 3.10+
- **LLM**: Google Gemini 2.5 Flash (via API)
- **UI**: Rich library for terminal formatting
- **Data**: YAML files for scenarios, Pydantic models for state
- **Platform**: Windows (native), Linux/Mac (compatible with minor tweaks)

### Code Organization
```
wargame/
├── cli/          # User interface and game loop
├── engine/       # Core game mechanics
├── llm/          # AI integration (prompts, context building)
├── models/       # Data structures (world state, narratives)
├── agents/       # Advisor behavior and conversation logic
├── data/         # Scenario content (YAML files)
└── docs/         # Documentation (you are here)
```

### Key Dependencies
- `rich` - Terminal UI
- `typer` - CLI framework
- `pydantic` - Data validation
- `pyyaml` - Content loading
- `google-generativeai` - Gemini API client

### LLM Usage Patterns
- **Context Management**: Different AI agents get filtered information (e.g., foreign diplomats don't see your internal deliberations)
- **Prompt Engineering**: Specific instructions for tone, length, and behavior
- **Narrative Injection**: Hidden truths embedded in system prompts to guide behavior
- **Error Handling**: Fallback to keyword-based system if LLM fails

---

## What Makes This Special

### 1. Narrative Replayability
Most games are predictable on second playthrough. False Flag has **hidden narrative modes** that change NPC behavior without telling the player:

**Example**:
- **Narrative A** (Russia Aggression): US President is supportive, offers military aid
- **Narrative B** (China Proxy War): US President is evasive, asks probing questions about China

The player must deduce what's really happening from diplomatic interactions.

### 2. Living Advisors
The cabinet advisors **remember everything you've said and done**:
- Reference past decisions: "As I warned in Turn 2..."
- Build trust or lose it based on decision quality
- Provide increasingly stern pushback if you make reckless choices
- Each has distinct personality and areas of expertise

### 3. Emergent Drama
Because the LLM generates content, **every playthrough is unique**:
- Different diplomatic conversations
- Unique crisis developments after scripted turns end
- Unpredictable consequences that feel organic

### 4. Realistic Constraints
Unlike most games where you have infinite resources:
- Only **2 Type-45 destroyers** with 96 total anti-ballistic missiles
- Can only defend **2 locations simultaneously** with fighter CAP
- **30 Tomahawk missiles** total - use them wisely
- Actions have diplomatic costs (aggressive moves hurt Alliance Cohesion)

---

## Business/Release Context

### Target Platforms (Priority Order)
1. **PC (Windows)** - Primary platform, fully supported
2. **PC (Linux)** - Minor compatibility, mostly works
3. **PC (Mac)** - Minor compatibility, mostly works
4. **Steam** - Planned distribution channel
5. **itch.io** - Indie game platform for beta testing

### Monetization (TBD)
- **Premium**: $9.99-14.99 one-time purchase
- **Early Access**: $7.99 during development
- **DLC Potential**: Additional scenarios, historical conflicts

### Competition
- **DEFCON** - Nuclear war strategy (real-time, more arcade-y)
- **Democracy 4** - Political simulation (broader scope, less military)
- **Command: Modern Operations** - Military sim (hardcore, expensive)

**Positioning**: More narrative and accessible than Command, more focused than Democracy, more strategic than DEFCON.

---

## Immediate Priorities

### Before Next Playtest (Est. 6 hours)
1. Fix decision cancellation flow (2-3 hours)
2. Fix advisor identity/addressing (3-4 hours)
3. Move score display timing (30 minutes)

### Before Beta Release (Est. 15 hours)
4. Clean up all markdown formatting (1-2 hours)
5. Remove duplicate text echoing (15 minutes)
6. Replace meta-text headers (15 minutes)
7. Polish Critical Advisory UI (1 hour)
8. General formatting audit (2-3 hours)
9. Add `/advise concise` command (1 hour)
10. Comprehensive QA pass (4-6 hours)

### Nice to Have for 1.0 (Est. 20-30 hours)
11. Bilateral relationship system (4-6 hours)
12. Newspaper-style briefings (6-8 hours)
13. 3-4 additional narrative paths (8-12 hours)
14. Victory/defeat conditions (2-4 hours)

---

## Known Risks & Mitigation

### Technical Risks
1. **LLM API Costs**: Gemini Flash is cheap but costs add up
   - *Mitigation*: Implement caching, use shorter prompts where possible
   
2. **LLM Availability**: Google API downtime = game unplayable
   - *Mitigation*: Fallback to keyword-based adjudication exists
   
3. **Windows-Only**: `msvcrt` module limits cross-platform
   - *Mitigation*: Already planned `curses` alternative for Unix

### Design Risks
1. **Too Complex**: Players might find COBRA simulation overwhelming
   - *Mitigation*: Tutorial mode, better onboarding
   
2. **Too Text-Heavy**: Long advisor responses might bore players
   - *Mitigation*: `/advise concise` command, better UI formatting
   
3. **Repetitive**: Limited scenario content after Turn 6
   - *Mitigation*: Stochastic generation + more narrative paths

---

## Success Metrics

### Alpha Success (Current Phase)
- ✅ Core gameplay loop functional
- ✅ LLM integration working
- ✅ Dynamic narratives implemented
- 🟡 First playtest completed with feedback
- 🔲 Critical bugs fixed

### Beta Success (Next Phase)
- 🔲 5+ external playtesters
- 🔲 Complete gameplay session without crashes
- 🔲 Positive feedback on narrative variety
- 🔲 <5 P0/P1 bugs reported
- 🔲 Average session length >30 minutes

### 1.0 Success (Release)
- 🔲 Steam page live
- 🔲 50+ wishlists before launch
- 🔲 4+ narrative paths available
- 🔲 Tutorial/onboarding complete
- 🔲 Professional trailer/marketing assets

---

## Team/Stakeholder Context

### Current Team
- **Developer**: Solo developer (with AI assistant)
- **Testers**: Internal only (1 person)
- **Users**: 0 external users yet

### Required Skills for Maintenance
- **Python**: Intermediate level (async, OOP, decorators)
- **LLM/AI**: Understanding of prompt engineering
- **Game Design**: Balancing, pacing, player psychology
- **YAML**: Content authoring for scenarios
- **Terminal UI**: Rich library knowledge

### If You're Taking Over
1. **Week 1**: Read all docs in `/docs/handover/`, run the game, break things
2. **Week 2**: Fix one bug from playtest feedback, add one small feature
3. **Week 3**: Create a new narrative path (see `data/scenarios/war_game_2025/narratives.yaml`)
4. **Week 4**: Conduct your own playtest, document findings

---

## Resources & Links

### Key Files to Understand
1. `cli/main.py` - Game loop (where everything starts)
2. `engine/sim_loop.py` - Turn phase orchestration
3. `llm/context_builder.py` - How LLM context is assembled
4. `models/narrative.py` - Narrative system data structures
5. `data/scenarios/war_game_2025/narratives.yaml` - Story paths

### Documentation
- **This folder** (`docs/handover/`) - All handover docs
- `/analysis/` - Detailed technical discussions and decision logs
- `/docs/` - Individual feature documentation (pre-handover organization)

### External Resources
- [Gemini API Docs](https://ai.google.dev/docs)
- [Rich Library Docs](https://rich.readthedocs.io/)
- [Pydantic Docs](https://docs.pydantic.dev/)

---

## Questions for Incoming Developer

Before you start, answer these to ensure you're set up for success:

1. ✅ Do you have Python 3.10+ installed?
2. ✅ Do you have a Gemini API key?
3. ✅ Have you read the PLAYTEST_FEEDBACK.md document?
4. ✅ Can you run the game successfully?
5. ✅ Do you understand the turn-based gameplay loop?
6. ✅ Have you reviewed the critical bugs list?

If all ✅, you're ready to start! Begin with fixing Issue #7 (decision cancellation flow).

---

**Handover Compiled By**: AI Development Assistant  
**For**: Future Developer  
**Contact**: See project README for maintainer info  
**Last Updated**: November 8, 2025

