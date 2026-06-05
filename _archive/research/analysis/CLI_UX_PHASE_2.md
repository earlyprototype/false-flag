# CLI UX/UI ENHANCEMENT PLAN - PHASE 2

**Project:** FALSE FLAG: THE WARGAME
**Focus:** Advanced Input, Theming, and Content Formatting
**Status:** Draft

---

## 1. OBJECTIVE
Following the successful implementation of Phase 1 (Native Panels, Spinners, Rich Help), Phase 2 focuses on **interaction quality** and **visual variety**. The goal is to make the CLI feel less like a script runner and more like a reactive terminal.

---

## 2. PROPOSED ENHANCEMENTS

### 2.1 Advanced Input Handling (`prompt_toolkit`)
**Current State:** Uses `typer.prompt()`, which is blocking and offers no assistance.
**Proposal:** Integrate `prompt_toolkit` to replace standard input.
*   **Auto-completion:**
    *   Type `/call` -> Suggests [France, Germany, USA...]
    *   Type `/intel` -> Suggests [Russia, China, Iran...]
*   **Command History:** Up/Down arrows to recall previous commands.
*   **Syntax Highlighting:** Colorize commands (`/decide`) vs arguments.
*   **Non-blocking Input:** Allows text to stream while user is typing (future-proofing).

### 2.2 Expanded Use of Tree Views
**Current State:** `rich.Tree` is used only for Stockpiles.
**Proposal:** Apply hierarchical views to:
*   **Chain of Command:** Visualizing the Advisor structure (PM -> Ministers -> Depts).
*   **Diplomatic Graph:** Grouping countries by Alliance Block (NATO, CSTO, Neutral).

### 2.3 Selectable Retro Themes
**Current State:** Single default theme (Slate/Blue).
**Proposal:** Add a `/theme` command to switch styles instantly.
*   **DEFCON 1:** Red/Amber monochrome (Crisis mode).
*   **RETRO PHOSPHOR:** Green text, scanlines (1980s Wargames).
*   **HIGH CONTRAST:** Black/White (Accessibility).

### 2.4 Markdown Rendering for LLM Content
**Current State:** LLM text is streamed as plain text or basic strings.
**Proposal:** Ensure the `rich.Markdown` renderer is fully utilized for LLM responses.
*   Advisors can use **bold**, *italics*, and lists.
*   Injects can use headers and dividers.
*   *Note:* This requires updating the System Prompt to encourage Markdown formatting.

---

## 3. IMPLEMENTATION TASKS

1.  [ ] **Install `prompt_toolkit`:** Add to dependencies.
2.  [ ] **Create `InputHandler` Class:** Encapsulate the complex input logic.
3.  [ ] **Implement Auto-complete Registry:** Dynamic list of entities for completion.
4.  [ ] **Refactor `run_turn_discussion`:** Replace `typer.prompt` with `InputHandler.ask()`.
5.  [ ] **Theme Manager:** Extract colors to a swappable config.

---

## 4. COMPATIBILITY NOTE
These changes apply *only* to the CLI (`cli/`). The Web App (`frontend/`) and Headless Engine (`api/`) remain unaffected, preserving the "Headless" architecture.

