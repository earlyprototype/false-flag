# FALSE FLAG: THE WARGAME

## Overview

**False Flag: The Wargame** is an AI-powered narrative crisis simulation where you play as the Prime Minister of the United Kingdom facing a Russian false flag operation. Based on the podcast series "The Wargame," the game combines strategic decision-making, conversational AI advisors, and dynamic scenario generation to create an immersive political-military crisis experience.

---

## Game Premise

**October 2025.** Russia has falsely accused the UK of attacking their Severomorsk naval base, killing over 100 Russian naval personnel. In retaliation, Russia has deployed its entire Northern Fleet—15 submarines, destroyers, and frigates—toward British waters. Meanwhile, cyber attacks intensify, infrastructure fails, and two F-35 pilots are found murdered in Norfolk.

You are the Prime Minister. NATO's commitment wavers. The public grows fearful. Your military capabilities are limited. Every decision you make will determine whether the UK successfully navigates this crisis, stumbles into war, or appears weak before an adversary testing your resolve.

**The stakes are existential. The decisions are yours alone.**

---

## Core Gameplay

### Turn-Based Structure

Each turn represents a critical decision point in the escalating crisis. The game flows through distinct phases:

#### 1. **Briefing Phase**
- Receive intelligence updates and situation reports
- Learn about new developments (scripted or AI-generated)
- Mandatory diplomatic encounters may occur
- Review current metrics and world state

#### 2. **Discussion Phase**
- Ask your advisors questions conversationally
- Explore options, request analysis, challenge assumptions
- Call foreign leaders/diplomats for optional diplomatic negotiations
- Use commands like `/menu`, `/call [country]`, `/decide`

#### 3. **Decision Phase**
- Commit to a specific course of action
- LLM interprets your decision and its implications
- Advisors provide pushback and warnings
- Confirm or reconsider your choice

#### 4. **Adjudication Phase**
- Your decision is executed
- Metrics update based on outcomes
- World state changes (flags, postures, spatial elements)
- See consequences ripple through the scenario
- Turn advances

---

## Key Features

### 🤖 **AI-Powered Advisors**

Your COBRA team consists of five key advisors, each with distinct expertise and perspectives:

- **National Security Advisor**: Strategic coordination, intelligence assessment, policy integration
- **Chief of the Defence Staff**: Military capabilities, operational feasibility, force readiness
- **Home Secretary**: Domestic security, counter-terrorism, public safety
- **Foreign Secretary**: Diplomatic relations, alliance management, international law
- **Attorney General**: Legal framework, justification under international law, ethical constraints

**Advisors are conversational.** They don't just answer questions—they push back, challenge risky decisions, and provide contextual analysis based on the evolving crisis.

### 🌍 **Dynamic Diplomatic System**

Engage with world leaders and diplomats through LLM-driven conversations:

#### Available Countries:
- **United States**: NATO ally, but commitment uncertain
- **France**: European power, nuclear capability
- **Germany**: Economic heavyweight, energy dependence on Russia
- **Poland**: Frontline NATO state, highly concerned
- **Russia**: The adversary (use with extreme caution)
- **Ukraine**: Conflict zone, intelligence source
- **Ireland**: Neutral observer, in-joke (because why not?)

#### Access Levels:
Your access to leaders vs. diplomats depends on **Alliance Cohesion**:
- **High Cohesion (70+)**: Direct access to heads of state
- **Medium Cohesion (40-69)**: Access to senior diplomats
- **Low Cohesion (<40)**: Limited or no access

#### Diplomatic Outcomes:
- Conversations are limited to 11 exchanges (LLM biased to end earlier)
- Your approach affects relationship scores
- Alliance Cohesion can increase or decrease
- Poor diplomacy can backfire spectacularly

### 📊 **Core Metrics**

Four key metrics guide your decision-making:

1. **Escalation Risk (0-100)**
   - How close the crisis is to military conflict
   - Aggressive actions increase risk
   - De-escalation measures reduce it
   - **Critical threshold: 85+ = High risk of war**

2. **Domestic Stability (0-100)**
   - Public confidence in government
   - Civil order and social cohesion
   - Media perception and panic levels
   - **Critical threshold: <30 = Potential government collapse**

3. **Alliance Cohesion (0-100)**
   - NATO unity and support
   - Willingness of allies to back UK actions
   - Determines diplomatic access levels
   - **Critical threshold: <25 = Alliance fragmentation**

4. **Influence (0-100)**
   - UK's ability to shape international response
   - Credibility with allies and adversaries
   - Effectiveness of diplomatic and military posturing
   - **Critical threshold: <20 = Loss of leadership role**

**Additional Tracking:**
- Military casualties
- Civilian casualties
- Flags (e.g., `public_awareness`, `us_commitment`)
- Force postures (e.g., readiness states, deployments)
- Spatial state (unit locations, asset status)

### 🎲 **Hybrid Inject System**

The game delivers scenario events through a flexible system:

#### Scripted Injects:
- Hand-crafted YAML files (`turn_NNN.yaml`)
- Based on traditional scenario and historical crises
- Ensure key narrative beats and realistic escalation

#### Stochastic Injects (Optional):
- AI-generated events using LLM
- Draws from scenario library
- Adapts to player decisions and world state
- Creates emergent, unpredictable scenarios

**You control the mode**: Pure scripted, pure stochastic, or hybrid.

### 🎭 **Cinematic Presentation**

The game features a polished, dramatic presentation:

- **Character-by-character scrolling text** for narrative moments
- **Scene-based intro sequences** with SPACE-driven pacing
- **Clear screen transitions** between scenes and turns
- **Structured formatting** for briefings, discussions, and adjudications
- **Real-time diplomatic conversations** with streaming LLM responses
- **Metric deltas displayed** after adjudication (e.g., `Alliance Cohesion: 45/100 (+5)`)

Press SPACE during scrolling to skip to the end of the current scene. Press SPACE at prompts to advance.

---

## Gameplay Commands

### During Discussion Phase:

- **Ask questions naturally**: `"NSA, what's your assessment of Russian intentions?"`
- **`/decide`**: Commit to a decision and move to Decision Phase
- **`/menu`**: View available commands, advisors, diplomatic contacts, and metrics guide
- **`/call [country]`**: Initiate diplomatic conversation
  - Examples: `/call us`, `/call france`, `/call russia`
- **`/save [filename]`**: Save current game state
- **`/quit`**: Exit the game

### Diplomatic Commands:

- **Type naturally**: Speak to foreign leaders/diplomats as yourself (the PM)
- **`/end`**: Conclude diplomatic conversation early
- **Max 11 exchanges per conversation** (LLM may end sooner)

---

## Technical Architecture

### LLM Integration

The game uses **Google Gemini 2.5 Flash** (configurable) for:

- **Player action interpretation**: Understanding complex, natural language decisions
- **Advisor response generation**: In-character, contextual, non-meta responses
- **Stochastic inject generation**: Creating realistic scenario events
- **Diplomatic counterpart simulation**: Roleplaying foreign leaders/diplomats
- **Outcome assessment**: Analyzing conversation results and metric impacts

**Context Window**: Leverages Gemini's 1M token context to include full game history, ensuring advisors remember previous discussions and decisions.

**Safety Settings**: Configured to handle mature content appropriate for a military-political crisis simulation.

### World State Model

Built on **Pydantic** for type-safe state management:

```python
class WorldState:
    turn: int
    phase: str
    metrics: Metrics
    flags: Dict[str, Any]
    posture: Dict[str, Any]
    spatial_state: Dict[str, Any]
    discussion_transcript: List[str]
    diplomatic_relationships: Dict[str, int]
```

### Persistence

- **Save/Load**: Full game state serialization
- **Transcript logging**: Complete record of all interactions
- **Resume capability**: Pick up exactly where you left off

### Scenario Structure

```
data/scenarios/war_game_2025/
├── initial_conditions.yaml    # Starting metrics, forces, intelligence
├── scenario_library.yaml      # Elements for stochastic generation
└── episodes/
    ├── turn_001.yaml          # Scripted injects
    ├── turn_002.yaml
    └── ...
```

---

## Realism & Inspiration

**False Flag: The Wargame** is grounded in real-world crisis dynamics:

### Historical Parallels:
- 1983 Able Archer NATO exercise (Soviet near-nuclear response)
- 2014 Ukraine crisis and hybrid warfare
- 2018 Salisbury poisonings and diplomatic expulsions
- Modern Russian false flag operations

### Military Realism:
- **UK force constraints**: Limited air defense (2 Type-45 destroyers), small submarine fleet, CAP limitations
- **Stockpile limits**: Realistic missile counts (30 Tomahawks, 96 Sea Viper missiles, etc.)
- **Readiness states**: HMS Prince of Wales requires 3 turns to reach full readiness
- **Intelligence fog**: Incomplete information, confidence levels, attribution challenges

### Political Dynamics:
- **NATO Article 5 ambiguity**: Will allies honor commitments?
- **Escalation ladders**: Gray zone tactics, hybrid warfare, nuclear signaling
- **Domestic pressure**: Media, Parliament, public panic
- **Legal constraints**: International law, Rules of Engagement, proportionality

---

## Winning & Losing

**There is no single "win" condition.** Success is measured across multiple dimensions:

### Successful Outcomes:
- De-escalate crisis without appearing weak
- Maintain NATO cohesion and alliance support
- Protect UK territory and citizens
- Preserve government legitimacy
- Navigate gray zone without triggering Article 5

### Failure States:
- **Total War**: Escalation Risk reaches 100
- **Government Collapse**: Domestic Stability falls below critical threshold
- **Alliance Fragmentation**: NATO unity breaks down
- **Loss of Sovereignty**: UK forced into unacceptable compromises
- **Catastrophic Casualties**: Military or civilian losses spiral

### The Challenge:
Every decision involves trade-offs:
- Act aggressively → Escalation Risk ↑, Influence ↑
- Seek diplomacy → Escalation Risk ↓, Perceived weakness
- Rally NATO → Alliance Cohesion ↑, Domestic Stability ↓ (if allies don't deliver)
- Public transparency → Domestic panic vs. democratic legitimacy

**The game is designed to be difficult.** You will face impossible choices, incomplete information, and unintended consequences.

---

## Installation & Setup

### Requirements:
- Python 3.10+
- Google Gemini API key (or compatible LLM)
- Windows (for current msvcrt-based input handling)

### Quick Start:

```bash
# Clone repository
git clone [repository-url]
cd wargame

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
# Edit config.py with your Gemini API key

# Run the game
python -m cli.main play
```

### Configuration:

Edit `config.py`:
```python
GOOGLE_API_KEY = "your-api-key-here"
GEMINI_MODEL = "gemini-2.5-flash"  # or gemini-2.5-pro for higher quality
GEMINI_MAX_TOKENS = 4096  # Max tokens per LLM response
```

---

## Game Philosophy

**False Flag: The Wargame** is not a power fantasy. You are not Captain America. You are a civilian politician facing:

- **Limited military capabilities** (UK is not a superpower)
- **Uncertain allies** (NATO is a political alliance, not a guarantee)
- **Asymmetric adversary** (Russia uses hybrid warfare, false flags, escalation dominance)
- **Domestic constraints** (Parliament, media, public opinion matter)
- **Fog of war** (Intelligence is incomplete, attribution is hard)

The game respects player intelligence while challenging assumptions. Advisors will push back on unrealistic plans. The LLM is prompted to be skeptical, not sycophantic.

**Inspiration**: *DEFCON*, *Balance of Power*, *Hidden Agenda*, *Twilight Struggle*, and the "serious games" tradition of military and political simulations.

---

## Credits & Acknowledgments

### Podcast Source:
Based on **"The Wargame"** podcast series, which simulates realistic crisis scenarios with expert participants.

### Development:
- **Game Design & Implementation**: AI-assisted development using Claude Sonnet 4.5
- **Scenario Content**: Mined from podcast transcripts and historical crises
- **LLM Integration**: Google Gemini 2.5 Flash
- **Framework**: Python, Typer, Pydantic, YAML

### Special Thanks:
- The "Wargame" podcast creators for inspiring this project
- The AI research community for making sophisticated LLMs accessible
- Military historians and crisis simulation experts whose work informs the realism

---

## Future Enhancements

Potential expansions (not yet implemented):

- **Multiplayer Mode**: Player as PM, AI or human as Russian President
- **Campaign Mode**: Multiple linked scenarios (Ukraine, Taiwan, Arctic, etc.)
- **Advanced Graphics**: Terminal UI → Rich/Blessed → GUI
- **Modding Support**: Community-created scenarios and episodes
- **Historical Scenarios**: Cuban Missile Crisis, Suez Crisis, Falklands War
- **AI Director**: Dynamic difficulty adjustment based on player performance

---

## Disclaimer

**This is a work of fiction.** Any resemblance to actual persons, governments, or events is coincidental. The game is designed for educational and entertainment purposes, exploring crisis decision-making dynamics.

**Not Suitable For:**
- Actual crisis planning or policy guidance
- Children (mature themes: war, casualties, political violence)
- Players seeking simple, clear-cut "good guy vs. bad guy" narratives

**Content Warnings:**
- Military violence and casualties
- Political tension and existential threats
- Realistic portrayal of crisis stress
- Potentially disturbing scenarios (nuclear brinkmanship, civilian casualties)

---

## License

[To be determined based on your preferences]

---

## Contact & Contribution

[Your contact information / contribution guidelines if you want to open source]

---

**The crisis has begun. Your advisors are waiting. What will you decide?**

