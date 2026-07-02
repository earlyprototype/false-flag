# FALSE FLAG: THE WARGAME

An interactive political-military crisis simulation inspired by "The Wargame" podcast.

You are the Prime Minister of the United Kingdom. Russia has deployed an unprecedented naval force to the North Atlantic following a terrorist attack they falsely blame on Britain. Your decisions in the coming hours will determine whether the UK faces down this threat, stumbles into war, or appears weak before an adversary testing NATO's resolve.

![Dialogue Demo](dialogue_demo.gif)

## Features

- **Free-form Decision Making**: Describe any action you want to take - the game interprets and adjudicates it
- **AI-Powered Advisors**: Ask questions and get intelligent responses from your Cabinet (CDS, NSA, Foreign Secretary, Home Secretary, Attorney General)
- **Dynamic Scenario Generation**: Events unfold based on your decisions and the evolving crisis
- **Realistic Constraints**: Limited military capabilities, alliance politics, legal frameworks, and public opinion
- **Two-Phase Turns**: Discussion phase (ask questions, gather advice) and Decision phase (commit to action)
- **Save/Load System**: Continue your campaign across multiple sessions

## Quick Start

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install packages
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 2. Play with Mock Advisors (No Setup Required)

```powershell
.\.venv\Scripts\python.exe -m cli.main play
```

This uses template-based responses for testing.

### 3. Enable Real AI Advisors (Recommended)

For intelligent, context-aware responses:

1. Install Gemini SDK:
   ```powershell
   .\.venv\Scripts\pip.exe install google-generativeai
   ```

2. Get free API key from [Google AI Studio](https://aistudio.google.com/apikey)

3. Create `config.py` from template:
   ```powershell
   copy config.example.py config.py
   ```

4. Edit `config.py` and add your API key:
   ```python
   GOOGLE_API_KEY = "AIza..."
   LLM_PROVIDER = "gemini"
   ```

5. Play:
   ```powershell
   .\.venv\Scripts\python.exe -m cli.main play
   ```

See [docs/GEMINI_SETUP.md](docs/GEMINI_SETUP.md) for detailed setup instructions.

## How to Play

### Commands

During gameplay, you can use:

- **Ask Questions**: `CDS, what are our military options?`
- **Get Advice**: `NSA, what's Russia's likely next move?`
- **Check Status**: `/status` - View metrics and situation
- **View Menu**: `/menu` - See available advisors and commands
- **Make Decision**: `/decide` - Commit to your action
- **Save Game**: `/save` - Save progress
- **Quit**: `/quit` - Exit game

### Example Gameplay

```
> CDS, what are our air defence capabilities?

Military Commander: Prime Minister, we can maintain only two simultaneous 
combat air patrols across the entire UK. Our Type-45 destroyers provide 
ballistic missile defence, but we have limited coverage...

> Foreign Secretary, will NATO support us?

Diplomatic Lead: Prime Minister, the US commitment is uncertain. We must 
activate Article 4 consultations immediately and engage directly with 
Washington to secure their backing...

> /decide

Prime Minister, what is your decision?
> Deploy Type-45 destroyers to defensive positions and request emergency 
  NATO consultations under Article 4

[Decision interpreted and adjudicated...]
```

## Game Mechanics

### Metrics

Your decisions affect four key metrics:

- **Mission Progress** (0-100): How close you are to resolving the crisis
- **Escalation Risk** (0-100): Danger of conflict escalation
- **Domestic Stability** (0-100): Public confidence and infrastructure security
- **Alliance Cohesion** (0-100): NATO unity and US commitment

### Advisor Pushback

Your advisors will warn you if actions are:
- Militarily implausible (deploying unavailable assets)
- Legally problematic (violating international law)
- Diplomatically risky (fracturing NATO)
- Domestically dangerous (causing panic)

### Constraints

You must balance:
- Limited military capabilities (only 2 air patrols for entire UK)
- Uncertain US/NATO commitment
- Legal frameworks (international law, rules of engagement)
- Public messaging and domestic security
- Russian provocations and false flag operations

## Project Structure

```
wargame/
├── cli/                    # Command-line interface
│   └── main.py            # Main entry point
├── engine/                 # Core game engine
│   ├── sim_loop.py        # Turn-based game loop
│   ├── initial_conditions.py  # Scenario setup
│   └── persistence.py     # Save/load system
├── llm/                    # LLM integration
│   ├── router.py          # Provider selection
│   ├── gemini_driver.py   # Google Gemini integration
│   ├── mock_driver.py     # Testing/offline mode
│   └── prompts.py         # Prompt templates
├── agents/                 # Advisor system
│   └── conversation.py    # Question handling & responses
├── models/                 # Data models
│   └── world.py           # Game state
├── data/scenarios/         # Scenario data
│   └── war_game_2025/
│       ├── initial_conditions.yaml  # Starting state
│       └── episodes/      # Turn-based injects
└── docs/                   # Documentation
    └── GEMINI_SETUP.md    # AI setup guide
```

## Development

### Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/
```

### Run Linter

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

### Batch Mode (for testing)

```powershell
.\.venv\Scripts\python.exe -m scripts.batch_runner war_game_2025 42
```

## Further Documentation

- **[GAME_DESCRIPTION.md](GAME_DESCRIPTION.md)**: Full premise, characters, and the world behind the crisis
- **[Diplomatic System](docs/handover/DIPLOMATIC_SYSTEM.md)**: How alliance negotiation and diplomatic encounters work
- **[Nuclear Command Chain](docs/handover/NUCLEAR_COMMAND_CHAIN_SYSTEM.md)**: Nuclear authority, consequences, and escalation control
- **[Dynamic Narrative System](docs/handover/DYNAMIC_NARRATIVE_SYSTEM.md)**: The hidden-narrative engine driving emergent storytelling

## Credits

Inspired by "The Wargame" podcast by Audible and Somethin' Else.

## Licence

MIT — see [LICENSE](LICENSE).

---

**Ready to face the crisis? The nation is waiting for your decision.** 🇬🇧

