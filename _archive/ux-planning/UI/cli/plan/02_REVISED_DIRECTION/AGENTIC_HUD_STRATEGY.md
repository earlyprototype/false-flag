# Revised Direction: The Agentic HUD Strategy

## 1. Executive Summary
We are pivoting away from the "Persistent Dashboard" (Split-pane) model to an **"Agentic HUD" (Heads-Up Display)** model. 

**Why?** 
1.  **UX Alignment:** The game is conversational (Agentic). A scrolling narrative log preserves the context of advisor discussions better than a static dashboard.
2.  **Technical Stability:** The previous attempt to mix a `Rich.Live` rendering loop with a blocking `input()` prompt caused significant input handling bugs.
3.  **Research Alignment:** As per `agenticCLI.md`, "Agentic CLIs" differ from "Operational Dashboards." We should optimize for the former (narrative flow) rather than the latter (state monitoring).

---

## 2. The "Agentic HUD" Concept

### A. The Primary View: "The Stream"
The default view is a high-fidelity, linear scrolling log. This mimics a high-stakes secure messaging channel (like a Situation Room log).

**Features:**
*   **Contextual Headers (Adaptive SitRep):** Every new turn or phase change prints a "SitRep" block. Crucially, this adapts to the `PlayMode`:
    *   **Classic Mode:** Shows raw metric numbers (Risk: 80/100).
    *   **Immersive Mode:** Shows "Vibes" (Risk: HIGH, Stability: SHAKY) and Advisor Attitudes.
    *   **Emergent Mode:** Shows only the Narrative Summary (no metrics).
*   **Rich Dialogue:** Advisor text is color-coded and formatted (Markdown) in the stream.
*   **Inline Events:** "Risk increased to 80%" appears as a distinct alert event in the stream (Classic Mode only).

### B. The Secondary View: "The War Room" (On-Demand)
The dashboard functionality is preserved but moved to a dedicated **Modal View**.

**Interaction:**
1.  User types `/status`, `/map`, or `/warroom`.
2.  Screen clears.
3.  **Full-Screen Dashboard** renders (using `Rich.Layout`).
    *   **Classic:** Full metrics, graphs, resource tables.
    *   **Immersive/Emergent:** Filtered view showing only known intel, map state, and qualitative assessments (no raw numbers).
    *   Bottom: "Press [ENTER] to return to secure channel..."
4.  User presses a key -> Screen restores to the Stream.

**Technical Benefit:**
This decouples the *Rendering Loop* from the *Input Loop*. The Dashboard is a static snapshot (or a dedicated loop that doesn't need to handle complex text input), eliminating the "blocked commands" bug.

---

## 3. Implementation Strategy (MVU Pattern)

We will apply the **Model-View-Update (MVU)** pattern recommended in `CLItoolsresearch.md`, adapted for our Python codebase.

### The Model (`models/world.py` & `models/narrative_state.py`)
*   Existing `WorldState` object.
*   `NarrativeState` dictates visibility (hidden metrics vs visible vibes).

### The View (`cli/views/`)
We will create pure functions that take `WorldState` and return `Rich` renderables.

*   `view_sitrep(world, play_mode) -> Panel`: The inline header (polymorphic based on mode).
*   `view_warroom(world, play_mode) -> Layout`: The full-screen dashboard (filtered by mode).
*   `view_dialogue(message) -> Text`: Formatted chat bubbles.

### The Update (`engine/`)
*   Game engine modifies `WorldState`.
*   CLI simply re-renders the relevant View.

---

## 4. PowerShell & Accessibility Notes
*   **PowerShell Compat:** This stream-based approach works *better* in standard PowerShell windows than the complex split-pane dashboard, which often suffered from rendering artifacts on Windows Legacy Console.
*   **Accessibility:** A scrolling log is screen-reader friendly. A rigid dashboard is not.

## 5. Next Steps
1.  **Deprecate** `cli/main_dashboard.py`.
2.  **Enhance** `cli/rich_ui.py` to include the "War Room" full-screen layout (supporting all 3 modes).
3.  **Update** `cli/main.py` to support the `/warroom` modal toggle and ensure `view_sitrep` respects `play_mode`.
