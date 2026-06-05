# Web App Feature Parity Plan

**Goal**: Ensure the Web Application delivers the complete, nuanced gameplay experience of the CLI version, moving beyond a simple "chat interface" to a full wargame simulation.

## 1. Core Gameplay Loop (CRITICAL)
The current Web App simplifies the decision process into a single "Execute" click. The CLI's robust "Interpretation & Pushback" system is missing.

- [ ] **Decision Interpretation Phase**:
    - **API**: Split `POST /game/decision` into `/game/decision/interpret` (returns analysis) and `/game/decision/commit` (executes).
    - **UI**: Create a "Decision Review" modal/state.
        - Display: "Operational Order" (Interpretation of user's intent).
        - Display: "Forces Involved" & "Timeline".
        - **Feature**: "Critical Concerns" handling. If advisors object, show the concerns and offer the CLI's choices: **Adjust** (Modify order), **Override** (Ignore), or **Accept** (Apply recommendations).
- [ ] **Diplomacy Engine**:
    - **API**: Expose `run_diplomatic_encounter` logic. Currently, `/call` just asks a question. It needs to:
        - Track relationship state.
        - Calculate and apply `Alliance Cohesion` impacts.
        - Return structured dialogue (Intro -> Player Response -> Outcome).
- [ ] **Stochastic Injects**:
    - Ensure the "Dynamic Scenario Generation" (Turn 7+) triggers correctly in the API context.

## 2. Information & Intelligence
The CLI offers deep dives into world state that are currently hidden in the Web App.

- [ ] **Detailed Status Dashboard**:
    - **Vibes**: Display the "Situation Assessment" (Narrative vibes) text.
    - **Trust Metrics**: Visual bars for Advisor Trust (currently just "Online/Offline").
    - **Active Flags**: List of active boolean flags (e.g., `martial_law_declared`, `article_5_triggered`).
- [ ] **Intelligence Reports (`/intel`)**:
    - **UI**: Add an "Intelligence" tab/modal.
    - **API**: Expose `generate_actor_detailed_assessment` to view in-depth dossiers on Russia, France, US, etc.

## 3. Session Management & Persistence
The CLI saves state to JSON. The Web App is purely in-memory.

- [ ] **Save/Load System**:
    - **API**: Implement persistence to disk (`saves/` folder).
    - **UI**: "Load Game" screen on startup. "Save Game" button in settings.
- [ ] **Scenario Selection**:
    - **UI**: proper menu to select Scenario, Difficulty, and Play Mode (Classic/Immersive/Emergent) before starting.

## 4. Settings & Customization
- [ ] **LLM Configuration (`/llm`)**:
    - UI to toggle Flash/Pro models for cost/speed management.
- [ ] **Themes (`/theme`)**:
    - Port the CSS themes (Retro, Defcon, Slate) to Tailwind classes/variables to allow visual switching.

## Implementation Strategy

**Phase 1: The Decision Loop (Highest Priority)**
*   Refactor API to support the two-step decision process.
*   Build the "Decision Review" UI (Interpretation -> Pushback -> Commit).

**Phase 2: Deep State**
*   Expose Vibes, Trust, and Flags in the API.
*   Enhance the "Metrics" panel to show these details.

**Phase 3: Diplomacy & Intel**
*   Port the full Diplomacy state machine.
*   Add the Intel Dossier views.

**Phase 4: Meta-Game**
*   Save/Load and Scenario Setup screens.

