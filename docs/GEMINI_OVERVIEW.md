# GEMINI.md

## IMPORTANT: Initialisation

1. Do not run scripts or code unless explicitly asked. User will generally use you for code base research and feedback.
2. Listen to instructions and follow them as they are stated. Do not try to anticipate user's next steps. Wait for them to state their next step.
3. The (Gimini CLI) user is not a formally trained software or game developer and are on a learning journey.  Understand that they may need complex or less familiar terms explained to them. Complex tasks should also be broken down and outlined clearly, without verbosity and over use of technical terms. Where you see it, provide feedback that might support said user's learning
4. Similarily, when reviewing code, make sure to check for common errors typical of novice or vibe code developers. 
5. The (Gemini CLI) user has a strong background in systems thinking and product architecture and sees their role as that of a development architect leveraging AI coding to build out the product. 

## Project Overview

This project is a political-military crisis simulation game called "FALSE FLAG: THE WARGAME". The player takes on the role of the UK Prime Minister and must make decisions to resolve a crisis with Russia. The game is inspired by "The Wargame" podcast.

The game is a Python project that uses the Gemini API for its AI advisors. It has a command-line interface (CLI) that uses the `rich` library for a visually appealing and interactive experience. The game has a clear structure, with a `cli` for the command-line interface, an `engine` for the game logic, `llm` for the language model integration, and so on.

## Project Architecture

The application is a turn-based narrative simulation engine with a modular architecture.

-   **`wargame_cli.py`**: The main entry point of the application. It uses the `typer` library to create the command-line interface and launches the core game logic.

-   **`cli/`**: This directory contains the code for the command-line interface.
    -   **`main.py`**: This file orchestrates the application, containing the main game loop that drives the simulation forward.
    -   **`rich_ui.py`**: Handles the presentation layer, using the `rich` library to create a visually appealing and interactive CLI.

-   **`engine/`**: The core of the game, this directory contains the main simulation logic.
    -   **`sim_loop.py`**: Contains the `Simulation` class, which manages the game state and turn progression.
    -   **`adjudicator.py`**: Acts as the bridge between the game engine and the large language model (LLM). It uses the `ContextBuilder` to create a prompt from the current game state and sends it to the `GeminiClient`.
    -   **`actor_simulation.py`**: Simulates the behavior of non-player characters (NPCs) or state actors.
    -   **`scenario_loader.py`**: Loads game scenarios and actor profiles from YAML files in the `data/` directory.

-   **`llm/`**: This directory handles the integration with the Gemini large language model.
    -   **`client.py`**: Provides a client for interacting with the Gemini API.
    -   **`context_builder.py`**: Constructs the detailed prompts sent to the LLM, based on the current game state.

-   **`data/`**: This directory contains the game's data, stored in YAML format.
    -   **`scenarios/`**: Holds the different game scenarios.
    -   **`state_actors.yaml`**: Defines the profiles of the various state actors in the game.

-   **`agents/`**: This directory appears to be an experimental feature and is not currently integrated into the main application flow.

## Building and Running

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install packages
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 2. Enable Real AI Advisors (Recommended)

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
   GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
   LLM_PROVIDER = "gemini"
   ```

### 3. Play the game

```powershell
.\.venv\Scripts\python.exe -m cli.main play
```

## Development Conventions

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