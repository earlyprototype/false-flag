# Phase 3.0: Multi-Modal Interface Implementation Plan

**Version:** 1.0
**Date:** 2025-11-23
**Status:** Proposed

---

## 1. Objectives

This phase will implement the "Multi-Modal Interface" design, a context-aware UI that switches between four distinct visual modes.

**Primary Goals:**
1.  Refactor the main game loop in `cli/main.py` to support a UI state machine.
2.  Implement rendering functions for the four visual modes: "Report," "Console," "Council," and "Diplomacy."
3.  Integrate these modes into the appropriate phases of the game loop.
4.  Deprecate and remove the old dashboard implementation (`cli/dashboard.py`, `cli/main_dashboard.py`).
5.  Deliver a polished, thematic, and highly usable CLI experience.

---

## 2. Core Architectural Change: UI State Machine

The central change will be the introduction of a UI state machine within the `play()` function of `cli/main.py`. The main loop will no longer just print text; it will manage a `ui_mode` variable and call a dedicated rendering function based on the current mode.

**Example State Machine Logic:**

```python
# In cli/main.py

ui_mode = "REPORT"  # Initial state

while True:
    # Game logic updates world_state and determines the next ui_mode
    
    # Render the view based on the current mode
    if ui_mode == "REPORT":
        render_report_view(console, content)
        # Transition to next mode, e.g., COUNCIL
        ui_mode = "COUNCIL" 
    elif ui_mode == "COUNCIL":
        # The council view contains its own input loop
        next_game_action = render_council_view(console, world_state)
        # Process action and determine next mode
        ui_mode = process_action(next_game_action)
    elif ui_mode == "CONSOLE":
        # The console view is for critical decisions
        decision = render_console_view(console, world_state)
        # ...
    # ... etc.
```

---

## 3. Implementation Tasks

### Task 1: UI State Machine Scaffolding

*   **File:** `cli/main.py`
*   **Action:** Refactor the main `play()` function. Introduce an `ui_mode` variable and the basic `if/elif/else` structure to switch between rendering functions. Define the initial state transitions (e.g., from `SETUP` to `REPORT`).

### Task 2: Implement "The Report" View (Narrative)

*   **File:** `cli/rich_ui.py` (new function)
*   **Action:** Create `render_report_view(console, title: str, content: str)`.
*   **Details:** This function will take a title (e.g., "NEWS FROM POLAND") and text content. It will render it inside a `rich.Panel` styled to look like a newspaper or formal document. This will be used for briefings and non-interactive scene-setting.

### Task 3: Implement "The Console" View (Decision Hub)

*   **File:** `cli/rich_ui.py` (new function)
*   **Action:** Create `render_console_view(console, world_state)`.
*   **Details:** This will render the "diegetic terminal" modal. It will contain a `rich.Layout` with sections for vital stats, warnings, and extracted "key headlines." This view will be triggered by `/status` and before critical decisions. It will need helper functions to parse recent events to generate the headlines.

### Task 4: Implement "The Council" View (Advisor Dialogue)

*   **File:** `cli/rich_ui.py` (new function)
*   **Action:** Create `render_council_view(console, world_state, history)`.
*   **Details:** This is the most complex view.
    1.  It will loop through the dialogue `history`.
    2.  For each entry, it will create a `rich.Panel` (the speech bubble).
    3.  It will use `rich.Align` to position the bubbles left or right.
    4.  It will manage its own input loop at the bottom.
    5.  Streaming text into the bubbles will require careful implementation, likely by dynamically updating the content of the last panel.

### Task 5: Implement "The Diplomacy" View

*   **File:** `cli/rich_ui.py` (new function)
*   **Action:** Create `render_diplomacy_menu(console, world_state)`.
*   **Details:** This function will display a "contacts list" of available diplomats. When one is selected, the game state will transition, and the main loop will then use the `render_council_view` for the ensuing conversation, simply passing in the diplomat's name instead of an advisor's.

### Task 6: Integration and Deprecation

*   **Files:** `cli/main.py`, `cli/dashboard.py`, `cli/main_dashboard.py`
*   **Action:**
    1.  Go through the game loop in `cli/main.py` and replace all old `print` and `typer.echo` calls with transitions to the appropriate UI mode and calls to the new rendering functions.
    2.  Once fully integrated, delete `cli/dashboard.py` and `cli/main_dashboard.py`.
    3.  Update documentation to reflect the new, singular UI approach.

---

## 4. High-Level Timeline (Estimate)

*   **Week 1:** Tasks 1 & 2. Set up the state machine and implement the simplest view ("The Report"). This provides a solid foundation.
*   **Week 2:** Task 3 & 5. Implement the data-heavy "Console" view and the "Diplomacy" menu.
*   **Week 3:** Task 4. Tackle the complex "Council" view with its speech bubbles and dynamic text.
*   **Week 4:** Task 6. Full integration, testing, and cleanup.

**Total Estimated Time:** 3-4 Weeks.
