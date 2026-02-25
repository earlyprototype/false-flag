# Dashboard deployment package discussion
_Exported on 11/23/2025 at 00:46:06 GMT from Cursor (2.1.17)_

---

**User**

@UI @UX/UI/DASHBOARD_DEPLOYMENT_PACKAGE.md 

---

**Cursor**

I've read through the Dashboard Deployment Package document. It's a comprehensive implementation guide for adding a persistent dashboard UI to your wargame CLI whilst keeping the original scrolling interface completely intact.

## What I see:

This is a **deployment-ready package** that provides:

1. **Complete code templates** for the dashboard implementation
2. **Step-by-step instructions** for creating `cli/dashboard.py` and `cli/main_dashboard.py`
3. **Testing procedures** and test file templates
4. **Rollback strategy** (can delete 2 files to completely revert)
5. **Zero-risk approach** - the original `cli/main.py` remains untouched

## What would you like to do?

I can help you with:

**A.** Start implementing the dashboard (following the Phase 1 instructions)
- Create `cli/dashboard.py`
- Create `cli/main_dashboard.py`
- Set up the initial structure

**B.** Review the implementation plan first
- Discuss any concerns or modifications needed
- Check if it aligns with your current codebase structure
- Verify dependencies are in place

**C.** Create the test suite first
- Set up `tests/test_dashboard.py`
- Verify your testing infrastructure is ready

**D.** Something else entirely

Which direction would you like to go? I'll work through this in manageable chunks given the ADHD-friendly approach you prefer.

---

**User**

[1 tool called]



Perfect! I've created a comprehensive deployment package ready for handover. Here's what's now available:



## 📦 Complete Deployment Package



### **Documentation Bundle (4 Files)**



1. **`MODERN_CLI_DESIGN_GUIDE.md`** (13KB)

   - Complete design system

   - 3 colour schemes (DEFCON/Calm/Mono)

   - ADHD-friendly principles

   - Code examples for all components

   - Testing guidelines



2. **`CLI_DASHBOARD_IMPLEMENTATION_PLAN.md`** (9KB)

   - 3-phase technical plan

   - Tech stack decisions

   - Risk mitigation

   - Design mockups

   - Success criteria



3. **`DASHBOARD_DEPLOYMENT_PACKAGE.md`** (17KB) ← **MAIN HANDOVER DOC**

   - Complete deployment instructions

   - Day-by-day workflow

   - Copy-paste code templates

   - Testing procedures

   - Rollback strategy

   - Troubleshooting guide



4. **`Proposal.md`** (Original UX report)

   - Current state analysis

   - Enhancement recommendations



### **Updated Code**



5. **`cli/theme.py`** (Updated)

   - New DEFCON colour scheme (default)

   - ASCII-only symbols (no emoji)

   - High-contrast ADHD-optimised palette



---



## 🎯 What the Developer Gets



### **Ready-to-Copy Code Templates:**



1. **Complete `cli/dashboard.py` class** (200 lines)

   - Header/Sidebar/Main/Footer rendering

   - Live metrics updates

   - Conversation logging

   - Full docstrings



2. **Modified discussion loop** for `cli/main_dashboard.py`

   - Drop-in replacement code

   - Exact line numbers where to modify



3. **Test suite** (`tests/test_dashboard.py`)

   - Unit tests for all dashboard methods

   - Integration tests for both CLI modes

   - User testing checklist



### **Zero-Risk Workflow:**



```

Day 1: Create dashboard.py → Test import

Day 2: Copy main.py → Modify discussion phase

Day 3: Run tests → Fix bugs

Day 4: User testing → Collect feedback

Day 5: Decision → Deploy or rollback

```



### **Instant Rollback:**

```powershell

# If anything breaks:

Remove-Item cli/main_dashboard.py

Remove-Item cli/dashboard.py



# Original still works:

python -m cli.main play

```



---



## 📋 Handover Checklist



**Developer receives:**

- ✅ 4 complete documentation files

- ✅ Updated theme with ADHD colours

- ✅ Copy-paste code templates

- ✅ Step-by-step instructions

- ✅ Test suite templates

- ✅ Troubleshooting guide

- ✅ Success criteria

- ✅ Rollback procedures



**Safety guarantees:**

- ✅ Original CLI never modified

- ✅ All game logic untouched

- ✅ Parallel development (both modes work)

- ✅ Complete rollback in <1 minute

- ✅ Save files compatible across modes



---



## 🚀 Next Steps



**For immediate implementation:**

1. Open `DASHBOARD_DEPLOYMENT_PACKAGE.md`

2. Follow Phase 1 (Day 1) instructions

3. Copy the `dashboard.py` code template

4. Test import works

5. Proceed to Phase 2 when ready



**The package is complete and ready for handover!**

---

**Cursor**

I can see you've shared what looks like a summary of the deployment package. I want to make sure I understand what you're asking me to do now.

**Are you:**

**A.** Asking me to **review** the DASHBOARD_DEPLOYMENT_PACKAGE.md to confirm it's complete and ready for handover?

**B.** Ready to **start implementing** the dashboard following the instructions in the package?

**C.** Wanting me to **verify** that all the pieces are in place (check if the referenced files exist, dependencies are correct, etc.)?

**D.** Looking for **feedback** on whether the deployment strategy is sound?

**E.** Something else?

I want to make sure I give you the right help here. The "[1 tool called]" at the top of your message suggests you might have been preparing to do something - what would you like me to do next?

---

**User**

b

---

**Cursor**

Brilliant! Let's start implementing the dashboard following Phase 1 of the deployment package.

Let me first check the current state of your `cli` folder to understand what we're working with:

Perfect! I can see:
- Your `cli` folder is set up
- `theme.py` already has the DEFCON colour scheme and the `progress_bar` function
- The discussion phase loop in `main.py` starts at line 974

Let me now create the dashboard implementation following **Phase 1 (Day 1)** of the deployment package.

## Step 1: Create Dashboard Class

```python
"""Dashboard layout manager using Rich.Live and Rich.Layout.

This module provides a persistent terminal UI with fixed zones:
- Header: Turn, Phase, Time (always visible)
- Sidebar: Live metrics (updates in-place)
- Main: Scrolling dialogue
- Footer: Available commands
"""

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box
from typing import List

class WargameDashboard:
    """Manages the persistent dashboard layout."""
    
    def __init__(self, world, console):
        """Initialize dashboard with world state and console.
        
        Args:
            world: WorldState object
            console: Rich Console instance
        """
        self.world = world
        self.console = console
        self.conversation_log = []
        
        # Create layout structure
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["body"].split_row(
            Layout(name="sidebar", size=32),
            Layout(name="main", ratio=1)
        )
    
    def render_header(self) -> Panel:
        """Render top bar: TURN | PHASE | TIME.
        
        Returns:
            Rich Panel with header content
        """
        from cli.theme import theme_manager
        COLORS = theme_manager.get_colors()
        
        # Format: TURN 004 | DISCUSSION PHASE | 17:00 HRS
        content = f"TURN {self.world.turn:03d} │ DISCUSSION PHASE │ 17:00 HRS"
        
        return Panel(
            f"[{COLORS['emphasis']} bold]{content}[/]",
            style=COLORS['primary'],
            box=box.ROUNDED,
            padding=(0, 2)
        )
    
    def render_sidebar(self) -> Panel:
        """Render left panel with live metrics.
        
        Returns:
            Rich Panel with metrics table
        """
        from cli.theme import theme_manager, SYMBOLS, progress_bar
        COLORS = theme_manager.get_colors()
        
        # Create metrics table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style=COLORS['secondary'])
        table.add_column("Value", justify="right")
        table.add_column("Bar", width=10)
        
        # Risk
        risk = self.world.metrics.escalation_risk
        risk_color = COLORS['metric_critical'] if risk >= 70 else COLORS['metric_bad'] if risk >= 50 else COLORS['metric_good']
        table.add_row(
            f"{SYMBOLS['risk']} Risk",
            f"[{risk_color}]{risk}[/]",
            progress_bar(risk, 100, 10)
        )
        
        # Stability
        stability = self.world.metrics.domestic_stability
        stab_color = COLORS['metric_critical'] if stability <= 30 else COLORS['metric_bad'] if stability <= 50 else COLORS['metric_good']
        table.add_row(
            f"{SYMBOLS['stability']} Stability",
            f"[{stab_color}]{stability}[/]",
            progress_bar(stability, 100, 10)
        )
        
        # Cohesion
        cohesion = self.world.metrics.alliance_cohesion
        coh_color = COLORS['metric_critical'] if cohesion <= 30 else COLORS['metric_bad'] if cohesion <= 50 else COLORS['metric_good']
        table.add_row(
            f"{SYMBOLS['cohesion']} Cohesion",
            f"[{coh_color}]{cohesion}[/]",
            progress_bar(cohesion, 100, 10)
        )
        
        # Casualties
        casualties = self.world.metrics.casualties_mil + self.world.metrics.casualties_civ
        table.add_row(
            f"{SYMBOLS['casualties']} Casualties",
            f"{casualties}",
            f"{self.world.metrics.casualties_mil}m {self.world.metrics.casualties_civ}c"
        )
        
        return Panel(
            table,
            title="[bold]SITUATION REPORT[/]",
            border_style=COLORS['primary'],
            box=box.ROUNDED,
            padding=(1, 1)
        )
    
    def render_main(self) -> Panel:
        """Render centre panel with scrolling conversation.
        
        Returns:
            Rich Panel with recent dialogue
        """
        from cli.theme import theme_manager
        COLORS = theme_manager.get_colors()
        
        # Show last 15 messages
        recent = self.conversation_log[-15:] if self.conversation_log else ["[dim]No messages yet[/]"]
        content = "\n".join(recent)
        
        return Panel(
            content,
            title="[bold]COBRA BRIEFING[/]",
            border_style=COLORS['secondary'],
            box=box.ROUNDED,
            padding=(1, 2)
        )
    
    def render_footer(self) -> Panel:
        """Render bottom bar with available commands.
        
        Returns:
            Rich Panel with command hints
        """
        from cli.theme import theme_manager
        COLORS = theme_manager.get_colors()
        
        commands = f"[{COLORS['primary']}]/status[/] [{COLORS['primary']}]/menu[/] [{COLORS['primary']}]/advise[/] [{COLORS['primary']}]/resources[/] [{COLORS['primary']}]/decide[/] [{COLORS['primary']}]/quit[/]"
        
        return Panel(
            commands,
            style=COLORS['muted'],
            box=box.ROUNDED,
            padding=(0, 2)
        )
    
    def update(self):
        """Refresh all dashboard panels."""
        self.layout["header"].update(self.render_header())
        self.layout["sidebar"].update(self.render_sidebar())
        self.layout["main"].update(self.render_main())
        self.layout["footer"].update(self.render_footer())
    
    def add_message(self, speaker: str, message: str):
        """Add a message to the conversation log.
        
        Args:
            speaker: Who is speaking (PM, NSA, CDS, etc.)
            message: The message content
        """
        from cli.theme import theme_manager
        COLORS = theme_manager.get_colors()
        
        if speaker == "PM":
            formatted = f"[{COLORS['emphasis']}]PM:[/] {message}"
        else:
            formatted = f"[{COLORS['secondary']}]{speaker}:[/] {message}"
        
        self.conversation_log.append(formatted)
        
        # Keep log size manageable (max 100 messages)
        if len(self.conversation_log) > 100:
            self.conversation_log = self.conversation_log[-100:]

```

Excellent! Dashboard class created. Now let's test the import works:

Perfect! Dashboard module imports successfully. 

## Step 2: Create Dashboard CLI

Now I'll copy `main.py` to `main_dashboard.py`:

Good! Now I need to read the full discussion phase loop to modify it. Let me get more context:

Let me continue reading to find where the discussion loop ends:

Let me find where the discussion loop ends:

Perfect! I can see the discussion loop runs from line 974 to line 1571. Now I need to modify this section to use the dashboard. According to the deployment package, I should keep ALL the command handlers but wrap them in the dashboard Live context.

Let me create the modified version:

```python
"""Interactive CLI for the wargame with two-phase turn structure.

Supports:
- Interactive mode: discussion → decision → adjudication
- Batch mode: run with pre-defined action
- Save/load game state
- Stochastic inject generation
"""

import typer
from pathlib import Path
from random import Random
from typing import Optional
import sys
import os

# CRITICAL: Import msvcrt FIRST on Windows (before Rich)
if sys.platform == "win32":
    import msvcrt

# Allow running this file directly
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# THEN import Rich (after msvcrt is loaded)
from cli.rich_ui import (
    console, phase_header, metrics_table,
    advisor_menu_panel, diplomatic_contacts_table,
    resources_tables, command_menu, metrics_guide_panel,
    format_markdown, RICH_ENABLED
)
from cli.theme import theme_manager, COLORS, SYMBOLS, BOX, WIDTH
from cli.formatters import format_advisor_response
from models.world import WorldState, Metrics
from models.narrative_state import NarrativeState, create_initial_narrative_state, PlayMode
from models.narrative import NarrativeConfig
from engine.scenario_loader import list_available_scenarios, get_scenario_config, get_turn_filename, load_narrative_configs
from engine.sim_loop import (
    run_turn_briefing,
    run_turn_discussion,
    run_turn_decision,
    run_turn_adjudication as run_turn_adjudication_fallback,  # Renamed for fallback
    run_single_scene
)
from engine.narrative_adjudication import adjudicate_with_narrative
from engine.intro import get_intro_lines
from engine.persistence import save_game, load_game
from engine.initial_conditions import load_initial_conditions
from engine.diplomacy import run_diplomatic_encounter, list_available_diplomatic_contacts
from llm.router import generate_text
from cli.model_settings_menu import model_settings_menu

# Task 2.5: Enable Rich help panel
app = typer.Typer(
    rich_markup_mode="rich", 
    help="FALSE FLAG: THE WARGAME - LLM-driven crisis simulation",
    no_args_is_help=True
)


def scroll_text(text: str, delay: float = 0.03, allow_skip: bool = True) -> bool:
    """Print text character by character with optional skip.
    
    Args:
        text: Text to scroll
        delay: Delay between characters (seconds)
        allow_skip: If True, pressing SPACE skips to end of scene
        
    Returns:
        True if user pressed SPACE to skip, False otherwise
    """
    import msvcrt
    import sys
    
    for i, char in enumerate(text):
        # Check if user pressed SPACE to skip rest of scene
        if allow_skip and msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                # Print rest of line and return skip signal
                sys.stdout.write(text[i:])
                sys.stdout.flush()
                print()
                return True  # Signal to skip rest of scene
            # Ignore other keys, continue scrolling
        
        sys.stdout.write(char)
        sys.stdout.flush()
        
        # Slightly longer pause after punctuation
        if char in '.!?':
            import time
            time.sleep(delay * 3)
        elif char in ',;:':
            import time
            time.sleep(delay * 2)
        else:
            import time
            time.sleep(delay)
    
    print()  # Newline at end
    return False  # No skip


def wait_for_space(prompt: str = "Press SPACE to continue...") -> None:
    """Wait for user to press spacebar to continue."""
    import msvcrt  # Windows-specific
    typer.echo("")
    typer.echo(prompt)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                typer.echo("")
                break


def parse_interpretation_simple(interpretation: str) -> dict:
    """Parse LLM interpretation into key sections for display.
    
    Args:
        interpretation: Full interpretation text
    
    Returns:
        Dict with parsed sections
    """
    sections = {
        "summary": "",
        "forces": [],
        "timeline": "",
        "concerns": ""
    }
    
    lines = interpretation.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("INTERPRETATION:"):
            sections["summary"] = line.replace("INTERPRETATION:", "").strip()
        elif line.startswith("FORCES INVOLVED:"):
            current_section = "forces"
        elif line.startswith("TIMELINE:"):
            current_section = "timeline"
        elif line.startswith("FEASIBILITY:"):
            if "impossible" in line.lower() or "requires clarification" in line.lower():
                sections["concerns"] = line.replace("FEASIBILITY:", "").strip()
            current_section = None
        elif current_section == "forces" and line and line.startswith("*"):
            # Extract force name from bullet point
            force = line.lstrip("* ").split(":")[0] if ":" in line else line.lstrip("* ")
            if force and len(sections["forces"]) < 5:  # Max 5 forces shown
                sections["forces"].append(force)
        elif current_section == "timeline" and line:
            sections["timeline"] = line
    
    return sections


def display_decision_summary(action: str, interpretation: str, show_details: bool = False):
    """Display decision interpretation in player-friendly format.
    
    Args:
        action: Player's original decision text
        interpretation: Full LLM interpretation
        show_details: If True, show full interpretation
    """
    COLORS = theme_manager.get_colors()
    
    # Show player's exact words in a box
    console.print("")
    from rich.panel import Panel
    console.print(Panel(f"[italic]{action}[/italic]", title="[bold]YOUR DECISION[/bold]", border_style="white"))
    console.print("")
    
    if show_details:
        # Show full interpretation
        console.print(Panel(format_markdown(interpretation), title="[bold]FULL INTERPRETATION (DETAILED)[/bold]", border_style="blue"))
        console.print("")
    else:
        # Show simplified summary
        parsed = parse_interpretation_simple(interpretation)
        
        # Build content for panel
        content = []
        
        # Show summary if we extracted one
        if parsed["summary"]:
            content.append(parsed["summary"])
            content.append("")
        
        # Show key forces
        if parsed["forces"]:
            content.append(f"[{COLORS['success']}]Forces Deployed:[/{COLORS['success']}]")
            for force in parsed["forces"]:
                content.append(f"  • {force}")
            content.append("")
        
        # Show timeline
        if parsed["timeline"]:
            content.append(f"[{COLORS['accent']}]Estimated Timeline:[/{COLORS['accent']}] {parsed['timeline']}")
            content.append("")
        
        # Show concerns
        if parsed["concerns"]:
            content.append(f"[{COLORS['warning']}]⚠ Operational Concerns: {parsed['concerns']}[/{COLORS['warning']}]")
            content.append("")
        
        content.append(f"[{COLORS['muted']}](Type 'details' to see full interpretation)[/{COLORS['muted']}]")
        
        console.print(Panel("\n".join(content), title="[bold]📋 OPERATIONAL ORDER[/bold]", border_style="cyan"))


def display_critical_concerns_with_selection(critical_concerns: list) -> tuple:
    """Display critical concerns and let player select which to address.
    
    Args:
        critical_concerns: List of (role, concern, recommendation) tuples
    
    Returns:
        Tuple of (action_code, selected_indices)
        action_code: 'A' (all), 'S' (select), 'M' (modify), 'I' (ignore), 'D' (discussion)
        selected_indices: List of 0-based indices of selected concerns
    """
    from rich.panel import Panel
    COLORS = theme_manager.get_colors()
    
    console.print("")
    console.print(Panel(f"Advisors have raised {len(critical_concerns)} critical concerns regarding your decision.", 
                        title=f"[{COLORS['warning']} bold]⚠️ CRITICAL ADVISORIES[/]", 
                        border_style=COLORS['warning']))
    console.print("")
    
    # Display each concern with number
    for idx, (role, concern, recommendation) in enumerate(critical_concerns, 1):
        console.print(f"[{COLORS['warning']} bold][{idx}] {role}[/{COLORS['warning']} bold]")
        console.print(f"  {concern}")
        console.print(f"  [{COLORS['primary']}]→ RECOMMENDATION: \"{recommendation}\"[/{COLORS['primary']}]")
        console.print("")
        console.print(f"[{COLORS['muted']}]" + "─" * 40 + f"[/{COLORS['muted']}]")
        console.print("")
    
    # Get selection
    console.print("Which concerns would you like to address?")
    console.print("")
    console.print(f"  [{COLORS['primary']}]A[/{COLORS['primary']}] - Apply ALL recommendations to my decision")
    console.print(f"  [{COLORS['primary']}]S[/{COLORS['primary']}] - Select specific recommendations")
    console.print(f"  [{COLORS['primary']}]M[/{COLORS['primary']}] - Modify decision manually instead")
    console.print(f"  [{COLORS['primary']}]I[/{COLORS['primary']}] - Ignore all and proceed anyway")
    console.print(f"  [{COLORS['primary']}]D[/{COLORS['primary']}] - Return to discussion phase")
    console.print("")
    
    choice = typer.prompt("Choose", type=str).strip().upper()
    
    if choice == "A":
        return ('A', list(range(len(critical_concerns))))
    elif choice == "S":
        console.print("")
        console.print("Enter concern numbers separated by spaces (e.g., '1 3')")
        selection = typer.prompt("Select").strip()
        try:
            indices = [int(x) - 1 for x in selection.split()]
            valid_indices = [i for i in indices if 0 <= i < len(critical_concerns)]
            return ('S', valid_indices)
        except ValueError:
            console.print(f"[{COLORS['danger']}]Invalid selection.[/{COLORS['danger']}]")
            return ('M', [])
    elif choice == "M":
        return ('M', [])
    elif choice == "I":
        return ('I', [])
    elif choice == "D":
        return ('D', [])
    else:
        console.print(f"[{COLORS['warning']}]Invalid choice. Please try again.[/{COLORS['warning']}]")
        return display_critical_concerns_with_selection(critical_concerns)


def append_recommendations_to_decision(original_decision: str, critical_concerns: list, selected_indices: list) -> str:
    """Append selected recommendations to original decision.
    
    Args:
        original_decision: Player's original decision text
        critical_concerns: Full list of concerns
        selected_indices: Indices of concerns to address
    
    Returns:
        Enhanced decision text
    """
    if not selected_indices:
        return original_decision
    
    additions = []
    for idx in selected_indices:
        role, concern, recommendation = critical_concerns[idx]
        additions.append(f"- {recommendation}")
    
    enhanced = original_decision
    enhanced += "\n\nAdditionally:"
    enhanced += "\n" + "\n".join(additions)
    
    return enhanced


def select_scenario_variant(scenario_id: str) -> str:
    """Display interactive scenario selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected variant key (e.g., 'standard', 'fast_start')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT SCENARIO[/{COLORS['primary']} bold]")
    console.print("")
    
    # Load available scenarios
    scenarios = list_available_scenarios(scenario_id)
    
    if len(scenarios) == 0:
        # No scenarios.yaml found - use default
        return "standard"
    
    # Display scenario options
    for idx, (key, config) in enumerate(scenarios, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        difficulty = config.get("difficulty", "")
        estimated_time = config.get("estimated_time", "")
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        if difficulty:
            console.print(f"   Difficulty: {difficulty}")
        if estimated_time:
            console.print(f"   Estimated Time: {estimated_time}")
        console.print(f"   {description}")
        
        # Show key features
        features = config.get("features", [])
        if features:
            console.print("")
            for feature in features[:3]:  # Show first 3 features
                console.print(f"   - {feature}")
        
        if recommended:
            console.print("")
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    console.print("")
    while True:
        try:
            choice = typer.prompt("Select scenario (enter number)", type=int)
            if 1 <= choice <= len(scenarios):
                selected_key = scenarios[choice - 1][0]
                selected_name = scenarios[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(scenarios)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_play_mode() -> str:
    """Display interactive gameplay mode selection menu.
    
    Returns:
        Selected mode key (e.g., 'classic', 'immersive', 'emergent')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAMEPLAY MODE[/{COLORS['primary']} bold]")
    console.print("")
    
    modes = [
        ("classic", {
            "name": "Classic Wargame",
            "description": "Traditional experience with visible metrics and mechanical effects",
            "features": [
                "See numerical impact of your decisions",
                "Clear thresholds and win conditions",
                "Strategic resource management focus"
            ],
            "recommended": "Traditional wargame players, first playthrough"
        }),
        ("immersive", {
            "name": "Immersive Narrative",
            "description": "Character-driven drama with hidden metrics guiding the story",
            "features": [
                "Visual 'vibes' instead of raw numbers",
                "Character attitudes and relationships",
                "Narrative consequences take center stage"
            ],
            "recommended": "Story-focused players, replay value"
        }),
        ("emergent", {
            "name": "Emergent Drama (Experimental)",
            "description": "Maximum LLM freedom with minimal structure",
            "features": [
                "Pure narrative immersion",
                "Every playthrough unique",
                "Unpredictable emergent outcomes"
            ],
            "recommended": "Experimental players, maximum replayability"
        })
    ]
    
    for idx, (key, config) in enumerate(modes, 1):
        console.print(f"[{COLORS['warning']} bold]{idx}. {config['name']}[/{COLORS['warning']} bold]")
        console.print(f"   {config['description']}")
        console.print("")
        for feature in config['features']:
            console.print(f"   - {feature}")
        console.print("")
        console.print(f"   Recommended for: {config['recommended']}")
        console.print("")
    
    while True:
        try:
            choice = typer.prompt("Select gameplay mode (enter number)", type=int, default=2)
            if 1 <= choice <= len(modes):
                selected_key = modes[choice - 1][0]
                selected_name = modes[choice - 1][1]['name']
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(modes)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_difficulty(scenario_id: str) -> str:
    """Display interactive difficulty selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected difficulty key (e.g., 'standard', 'challenging', 'brutal')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT DIFFICULTY[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Difficulty affects scenario effect magnitudes (crisis intensity).")
    console.print("Player action impacts remain the same across all difficulties.")
    console.print("")
    
    # Load difficulty definitions from scenarios.yaml
    root = Path(__file__).resolve().parents[1]
    scenario_path = root / "data" / "scenarios" / scenario_id / "scenarios.yaml"
    
    difficulties = []
    if scenario_path.exists():
        try:
            import yaml
            with open(scenario_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                difficulties_dict = data.get("difficulties", {})
                # Convert to list of tuples for consistent ordering
                difficulties = [
                    ("standard", difficulties_dict.get("standard", {})),
                    ("challenging", difficulties_dict.get("challenging", {})),
                    ("brutal", difficulties_dict.get("brutal", {}))
                ]
        except Exception:
            pass
    
    # Default if no difficulties found
    if not difficulties:
        difficulties = [
            ("standard", {"name": "Standard", "description": "Balanced challenge", "multiplier": 0.65}),
            ("challenging", {"name": "Challenging", "description": "Tight margins", "multiplier": 0.85}),
            ("brutal", {"name": "Brutal", "description": "Maximum intensity", "multiplier": 1.0})
        ]
    
    # Display difficulty options
    for idx, (key, config) in enumerate(difficulties, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        multiplier = config.get("multiplier", 1.0)
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        console.print(f"   Effect Multiplier: {multiplier}x")
        console.print(f"   {description}")
        
        if recommended:
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select difficulty (enter number)", type=int, default=1)
            if 1 <= choice <= len(difficulties):
                selected_key = difficulties[choice - 1][0]
                selected_name = difficulties[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(difficulties)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_narrative(scenario_id: str) -> Optional[NarrativeConfig]:
    """Display game type selection menu (Original Story Mode vs Mystery Mode).
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        None if Original Story Mode selected,
        NarrativeConfig (randomly chosen) if Mystery Mode selected
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAME TYPE[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Choose how you want to experience the crisis:")
    console.print("")
    
    # Display option 1: Original Story Mode
    console.print(f"[{COLORS['warning']} bold]1. Original Story Mode[/{COLORS['warning']} bold]")
    console.print("   Play the standard story mode as designed. Experience the crisis through")
    console.print("   the eyes of the Prime Minister as events unfold.")
    console.print("")
    
    # Display option 2: Mystery Mode
    console.print(f"[{COLORS['warning']} bold]2. Mystery Mode[/{COLORS['warning']} bold]")
    console.print("   A hidden narrative guides AI agent behaviour. Foreign leaders and")
    console.print("   diplomats may have secret motivations that aren't immediately apparent.")
    console.print("   You must deduce the truth from their actions and responses.")
    console.print("")
    console.print(f"   [{COLORS['danger']}]⚠ The narrative is randomly selected and hidden from you![/{COLORS['danger']}]")
    console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select game type (enter number)", type=int, default=1)
            if choice == 1:
                # Original Story Mode - no secret narrative
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Original Story Mode selected[/{COLORS['success']} bold]")
                console.print("")
                return None
            elif choice == 2:
                # Mystery Mode - randomly select narrative
                narratives = load_narrative_configs(scenario_id)
                
                if narratives:
                    import random
                    selected_narrative = random.choice(narratives)
                    console.print("")
                    console.print(f"[{COLORS['success']} bold]✓ Mystery Mode activated[/{COLORS['success']} bold]")
                    console.print("")
                    # DO NOT tell player which narrative was selected
                    return selected_narrative
                else:
                    # Fallback if no narratives available - treat as Original Mode
                    console.print("")
                    console.print(f"[{COLORS['warning']}]Mystery Mode unavailable - using Original Story Mode[/{COLORS['warning']}]")
                    console.print("")
                    return None
            else:
                console.print(f"[{COLORS['danger']}]Please enter 1 or 2[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


@app.command(rich_help_panel="GAMEPLAY")
def play(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed for determinism"),
    load_save: str = typer.Option(None, "--load", help="Load game from save file"),
    stochastic_injects: bool = typer.Option(True, "--stochastic-injects/--no-stochastic-injects", help="Generate injects dynamically (enabled by default)"),
    intro_only: bool = typer.Option(False, "--intro-only", help="Display intro and exit"),
    variant: str = typer.Option(None, "--variant", help="Scenario variant (e.g., 'standard', 'fast_start')"),
    difficulty: str = typer.Option(None, "--difficulty", help="Difficulty level (e.g., 'standard', 'challenging', 'brutal')"),
    play_mode: str = typer.Option(None, "--play-mode", help="Gameplay mode (e.g., 'classic', 'immersive', 'emergent')"),
    flash_only: bool = typer.Option(False, "--flash-only", help="Use Flash model for all LLM calls (5x faster, cheaper)"),
):
    """Play the wargame interactively."""
    
    # Get current colors for loop
    COLORS = theme_manager.get_colors()

    # Configure LLM model if flash_only flag is set
    if flash_only:
        from llm.model_config import get_model_config
        config = get_model_config()
        config.use_flash_for_all()
        typer.echo("")
        typer.echo("[Flash-only mode enabled - using gemini-2.5-flash for all calls]")
        typer.echo("")
    
    # If no variant specified and not loading a save, show selection menu
    if variant is None and load_save is None:
        variant = select_scenario_variant(scenario)
    elif variant is None:
        variant = "standard"  # Default for loaded games
    
    # If no play mode specified and not loading a save, show selection menu
    if play_mode is None and load_save is None:
        play_mode = select_play_mode()
    elif play_mode is None:
        play_mode = "immersive"  # Default for loaded games
    
    # If no difficulty specified and not loading a save, show selection menu
    if difficulty is None and load_save is None:
        difficulty = select_difficulty(scenario)
    elif difficulty is None:
        difficulty = "standard"  # Default for loaded games
    
    # Select game type (Original or Mystery mode) - only for new games
    selected_narrative = None
    if load_save is None:
        selected_narrative = select_narrative(scenario)  # Returns None for Original, NarrativeConfig for Mystery
    
    # Display intro with pauses
    if intro_only or load_save is None:
        intro_lines = get_intro_lines(200)
        
        # Split intro into sections (scenes)
        # Scene markers are lines with "## SCENE"
        current_section = []
        sections = []
        
        for line in intro_lines:
            if "===" in line and current_section:
                # Start of new scene - save previous and start new
                sections.append(current_section)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Only add final section if it has content beyond just a separator
        if current_section and len([l for l in current_section if l.strip() and "===" not in l]) > 0:
            sections.append(current_section)
        
        # Display each scene
        for i, scene in enumerate(sections):
            # Clear screen at start of EVERY scene (including title)
            typer.clear()
            
            skip_rest = False
            prev_line_blank = False
            for line in scene:
                if skip_rest:
                    # User pressed SPACE - print remaining lines instantly
                    # Check if line has Rich markup
                    if "[/" in line and "[" in line:
                        console.print(line)
                    else:
                        typer.echo(line)
                    continue
                    
                if "===" in line:
                    # Structural element - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip() == "":
                    # Blank line
                    if not prev_line_blank:
                        typer.echo("")
                    prev_line_blank = True
                elif line.strip().startswith("# "):
                    # Title - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip().startswith("## YOUR ROLE"):
                    # Section header - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                else:
                    # All other text (narrative)
                    # Check if line contains Rich markup
                    if "[/" in line and "[" in line:
                        # Has Rich markup - use console.print with brief pause
                        import time
                        console.print(line)
                        time.sleep(0.3)  # Brief pause for readability
                        prev_line_blank = False
                    else:
                        # Plain text - stream it
                        skipped = scroll_text(line, delay=0.02)
                        if skipped:
                            skip_rest = True  # Skip rest of scene
                        prev_line_blank = False
            
            # Pause after each scene
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
        
        typer.echo("")
    
    if intro_only:
        return
    
    rng = Random(seed)
    root = Path(__file__).resolve().parents[1]  # cli/main.py -> project root
    
    # For NEW games, load and display Turn 1 briefing as part of intro sequence
    # This makes the COBRA briefing flow seamlessly from the YOUR ROLE section
    first_briefing_as_intro = (load_save is None)
    
    # Load or create world state
    if load_save:
        save_path = Path(load_save)
        try:
            scenario, world, transcript, loaded_play_mode, loaded_narrative_state = load_game(save_path)
            # Use loaded play_mode if available, otherwise use command-line arg
            if loaded_play_mode:
                play_mode = loaded_play_mode
            typer.echo(f"Loaded game from {save_path}")
            typer.echo(f"Resuming at Turn {world.turn}")
            typer.echo("")
            
            # Use loaded narrative state if available, otherwise create new
            if loaded_narrative_state:
                narrative_state = loaded_narrative_state
            else:
                # Create narrative state from loaded world (legacy saves)
                narrative_state = create_initial_narrative_state(
                    metrics=world.metrics.copy(),
                    play_mode=play_mode,
                    game_time=f"Turn {world.turn}"
                )
                narrative_state.turn = world.turn
            
        except (FileNotFoundError, ValueError) as e:
            typer.echo(f"Error loading save: {e}", err=True)
            raise typer.Exit(1)
    else:
        # New game
        initial_conditions = load_initial_conditions(scenario, root)
        initial_metrics = initial_conditions.get("initial_metrics", {})
        
        world = WorldState(
            turn=1,
            scene=1,
            difficulty=difficulty,
            narrative=selected_narrative,  # Set the secret narrative truth
            metrics=Metrics(
                escalation_risk=initial_metrics.get("escalation_risk", 60),
                domestic_stability=initial_metrics.get("domestic_stability", 50),
                alliance_cohesion=initial_metrics.get("alliance_cohesion", 40),
                casualties_mil=initial_metrics.get("casualties_mil", 2),
                casualties_civ=initial_metrics.get("casualties_civ", 0),
            ),
            flags={},
            posture={},
        )
        
        # Initialize state actor system for multi-agent simulation
        try:
            from models.state_actors import load_actors_from_yaml
            actor_yaml_path = root / "data" / "state_actors.yaml"
            world.actor_system = load_actors_from_yaml(str(actor_yaml_path))
            console.print(f"[{COLORS['success']}]✓ Multi-agent actor system initialized[/{COLORS['success']}]")
        except Exception as e:
            console.print(f"[{COLORS['warning']}]Warning: Could not load actor system: {e}[/{COLORS['warning']}]")
            world.actor_system = None
        
        # Initialize narrative state system
        narrative_state = create_initial_narrative_state(
            metrics=world.metrics.copy(),
            play_mode=play_mode,
            game_time=initial_conditions.get("metadata", {}).get("start_time", "Sunday 5th October 2025, 17:00")
        )
        
        transcript = []
    
    # Load scenario configuration for variant-specific turn files
    scenario_config = get_scenario_config(scenario, variant, root)
    stochastic_from_turn = scenario_config.get("stochastic_from", 7)
    
    # Main game loop
    while True:
        # Refresh colors at start of loop in case theme changed
        COLORS = theme_manager.get_colors()
        
        # Capture metrics at START of turn (before inject effects)
        from copy import deepcopy
        turn_start_metrics = deepcopy(world.metrics)
        
        # Auto-enable stochastic generation when reaching the transition point
        if world.turn >= stochastic_from_turn:
            if not stochastic_injects:
                # First time reaching stochastic content - show transition message
                stochastic_injects = True
                console.print("")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print(f"[{COLORS['primary']} bold]ENTERING DYNAMIC SCENARIO GENERATION[/{COLORS['primary']} bold]")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print("")
                console.print("The scripted scenario has concluded. From this point forward,")
                console.print("events will be dynamically generated based on your decisions.")
                console.print("")
                wait_for_space("Press SPACE to continue...")
                console.print("")
        
        # Determine if we should use stochastic generation for this turn
        use_stochastic = stochastic_injects and world.turn >= stochastic_from_turn
        
        # Get turn filename based on scenario variant
        turn_filename = get_turn_filename(world.turn, scenario_config)
        
        # Briefing phase (with player input function for diplomatic encounters)
        # For Turn 1 of new games: suppress panel display and effect boxes (will be streamed in intro flow)
        is_turn1_intro = (first_briefing_as_intro and world.turn == 1)
        inject, briefing_lines = run_turn_briefing(
            world, 
            scenario, 
            use_stochastic, 
            rng, 
            root, 
            transcript,
            get_player_input=lambda prompt: typer.prompt(prompt).strip(),
            turn_filename=turn_filename,
            silent_effects=is_turn1_intro,  # Hide effect boxes for Turn 1 intro
            suppress_display=is_turn1_intro  # Suppress panel so we can stream the text
        )
        
        # Clear screen and display briefing at top
        # BUT: if this is Turn 1 of a new game, don't clear (flows from intro)
        if not (first_briefing_as_intro and world.turn == 1):
            typer.clear()
        else:
            # First briefing of new game - add separator but don't clear
            typer.echo("")
            typer.echo("=" * 79)
            typer.echo("")
        
        # Split briefing into scene-setting and actual briefing
        # Look for "The National Security Advisor" or similar transition line
        # BUT: for Turn 1 of new games, don't split - show everything in one flow
        scene_setting_end = -1
        if not (first_briefing_as_intro and world.turn == 1):
            for i, line in enumerate(briefing_lines):
                if "National Security Advisor" in line and ("clears" in line or "begins" in line):
                    scene_setting_end = i
                    break
        
        # Display scene-setting part with streaming
        skip_rest = False
        for i, line in enumerate(briefing_lines):
            # Stop at the transition line
            if scene_setting_end > 0 and i >= scene_setting_end:
                break
                
            if skip_rest:
                # User pressed SPACE - print rest instantly
                # Check if line has Rich markup
                if "[/" in line and "[" in line:
                    console.print(line)
                else:
                    typer.echo(line)
                continue
            
            # Scroll the turn number header
            if i == 1 and line.strip().startswith("TURN"):
                skipped = scroll_text(line, delay=0.05)
                if skipped:
                    skip_rest = True
            # Stream narrative text (not structural elements)
            elif line.strip() and not line.strip().startswith("==="):
                # Check if line contains Rich markup
                if "[/" in line and "[" in line:
                    # Has Rich markup - use console.print with brief pause
                    import time
                    console.print(line)
                    time.sleep(0.3)
                else:
                    # Plain text - stream it
                    skipped = scroll_text(line, delay=0.02)
                    if skipped:
                        skip_rest = True
            else:
                typer.echo(line)
        
        # Pause after scene-setting (only if we found a split point)
        if scene_setting_end > 0:
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
            
            # Display rest of briefing (the actual intelligence report)
            typer.echo("")
            for i in range(scene_setting_end, len(briefing_lines)):
                typer.echo(briefing_lines[i])
        
        transcript.extend(briefing_lines)
        
        # Show intelligence briefing (Immersive/Emergent modes only)
        if play_mode in ["immersive", "emergent"] and world.turn > 1:
            from engine.intelligence import generate_intelligence_briefing
            intel_lines = generate_intelligence_briefing(narrative_state, world, rng, detailed=False)
            typer.echo("")
            for line in intel_lines:
                console.print(line)
            typer.echo("")
        
        # Pause before discussion phase
        typer.echo("")
        wait_for_space("Press SPACE to begin discussion phase...")
        
        # After Turn 1 intro briefing is shown, reset the flag
        if first_briefing_as_intro and world.turn == 1:
            first_briefing_as_intro = False
        
        # Clear screen and show discussion phase at top
        typer.clear()
        typer.echo("")  # Buffer line BEFORE Rich output
        
        if RICH_ENABLED:
            console.print(phase_header("DISCUSSION", world.turn))
            typer.echo("")
            typer.echo("  Ask questions or type /decide when ready")
            console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
            typer.echo("")
            console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
            console.print("=" * 79)
            console.print("")
            console.print("Ask advisors questions, or type '/decide' when ready.")
            console.print("Type '/menu' for commands, '/advise' for all advisors, '/resources' for forces.")
        
        typer.echo("")
        
        # Discussion phase loop - DASHBOARD MODE
        from cli.dashboard import WargameDashboard
        from rich.live import Live
        
        dashboard = WargameDashboard(world, console)
        questions = []
        
        with Live(dashboard.layout, console=console, refresh_per_second=2) as live:
            while True:
                # Update dashboard
                dashboard.update()
                
                # Get input (pause live updates)
                live.stop()
                user_input = console.input(f"[{COLORS['primary']}]>[/] ").strip()
                live.start()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["/decide", "decide", "decision"]:
                break
            
            if user_input.lower() in ["/quit", "quit"]:
                typer.echo("Exiting game.")
                raise typer.Exit(0)
            
            if user_input.lower() in ["/save", "save"]:
                save_path = save_game(world, transcript, scenario, f"turn_{world.turn:03d}", root, play_mode, narrative_state)
                typer.echo(f"Game saved to {save_path}")
                continue
            
            if user_input.lower() in ["/theme", "theme"]:
                typer.echo("")
                console.print("Available themes:")
                console.print("  1. Standard (Cyan/Blue)")
                console.print("  2. DEFCON 1 (Red/Alert)")
                console.print("  3. Retro (Green Phosphor)")
                console.print("  4. Slate (Black/White Monochrome)")
                typer.echo("")
                
                theme_choice = typer.prompt("Select theme (1-4)").strip()
                theme_map = {"1": "standard", "2": "defcon1", "3": "retro", "4": "slate"}
                
                if theme_choice in theme_map:
                    theme_name = theme_map[theme_choice]
                    theme_manager.set_theme(theme_name)
                    COLORS = theme_manager.get_colors()
                    console.print(f"[{COLORS['success']}]Theme changed to {theme_name.title()}[/{COLORS['success']}]")
                    # Refresh current view
                    typer.clear()
                    if RICH_ENABLED:
                        console.print(phase_header("DISCUSSION", world.turn))
                        typer.echo("")
                        typer.echo("  Ask questions or type /decide when ready")
                        console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
                        typer.echo("")
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("[bold red]Invalid selection[/bold red]")
                continue

            if user_input.lower() in ["/status", "status"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Display based on play mode
                    if play_mode == "classic":
                        # Show metrics table (includes turn, phase, influence)
                        console.print(metrics_table(world))
                    elif play_mode == "immersive":
                        # Show vibes
                        typer.echo("═" * 60)
                        typer.echo("SITUATION ASSESSMENT")
                        typer.echo("═" * 60)
                        typer.echo("")
                        vibes = narrative_state.get_situation_vibes()
                        for vibe in vibes:
                            typer.echo(vibe.to_string())
                        typer.echo("")
                        
                        # Show character attitudes
                        typer.echo("═" * 60)
                        typer.echo("ADVISOR ATTITUDES")
                        typer.echo("═" * 60)
                        typer.echo("")
                        for char_id, char_attitude in narrative_state.characters.items():
                            trust_level = char_attitude.trust // 20
                            trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                            relationship_symbol = {
                                "allied": "✓",
                                "neutral": "○",
                                "hostile": "✗",
                                "unknown": "?"
                            }.get(char_attitude.relationship, "○")
                            typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
                    elif play_mode == "emergent":
                        # Show narrative summary
                        typer.echo("═" * 60)
                        typer.echo(narrative_state.situation_summary)
                        typer.echo("═" * 60)
                    
                    # Show active flags if any
                    if world.flags:
                        typer.echo("")
                        console.print(f"[{COLORS['warning']} bold]ACTIVE RISK FLAGS:[/{COLORS['warning']} bold]")
                        for flag, value in world.flags.items():
                            if value:
                                console.print(f"  [{COLORS['warning']}]{SYMBOLS['warning']} {flag.replace('_', ' ').title()}[/{COLORS['warning']}]")
                else:
                    # Fallback to plain text
                    typer.echo("=" * 60)
                    typer.echo("CURRENT SITUATION")
                    typer.echo("=" * 60)
                    typer.echo("")
                    typer.echo(f"Turn: {world.turn}")
                    typer.echo(f"Phase: {world.phase}")
                    typer.echo("")
                    typer.echo("Metrics:")
                    typer.echo(f"  Escalation Risk:      {world.metrics.escalation_risk}/100")
                    typer.echo(f"  Domestic Stability:   {world.metrics.domestic_stability}/100")
                    typer.echo(f"  Alliance Cohesion:    {world.metrics.alliance_cohesion}/100")
                    typer.echo(f"  Military Casualties:  {world.metrics.casualties_mil}")
                    typer.echo(f"  Civilian Casualties:  {world.metrics.casualties_civ}")
                    typer.echo("")
                    
                    # Calculate influence
                    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
                    influence = int((influence_raw - 50) / 5)
                    influence = max(-10, min(10, influence))
                    influence_sign = "+" if influence >= 0 else ""
                    typer.echo(f"Public Sentiment (Influence): {influence_sign}{influence}/10")
                    typer.echo("")
                    
                    if world.flags:
                        typer.echo("Active Risk Flags:")
                        for flag, value in world.flags.items():
                            if value:
                                typer.echo(f"  ! {flag.replace('_', ' ').title()}")
                        typer.echo("")
                
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/call "):
                # Handle diplomatic call
                country_input = user_input[6:].strip().upper()
                
                # Map common names to country codes
                country_map = {
                    "US": "US", "USA": "US", "AMERICA": "US", "UNITED STATES": "US",
                    "FRANCE": "France", "FRENCH": "France",
                    "GERMANY": "Germany", "GERMAN": "Germany",
                    "POLAND": "Poland", "POLISH": "Poland",
                    "RUSSIA": "Russia", "RUSSIAN": "Russia",
                    "UKRAINE": "Ukraine", "UKRAINIAN": "Ukraine",
                    "IRELAND": "Ireland", "IRISH": "Ireland"
                }
                
                country = country_map.get(country_input, country_input.capitalize())
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]Connecting to {country}...[/{COLORS['success']} bold]")
                
                # Run diplomatic encounter (with real-time printing)
                encounter_transcript, cohesion_delta = run_diplomatic_encounter(
                    world,
                    country,
                    required=False,
                    context=None,
                    llm_generate=generate_text,
                    rng=rng,
                    root_path=root,
                    full_transcript=transcript,
                    get_player_input=lambda prompt: typer.prompt(prompt).strip(),
                    print_fn=typer.echo  # Print in real-time
                )
                
                # Transcript already printed, just save it
                transcript.extend(encounter_transcript)
                
                # Apply alliance cohesion change
                from engine.utils import clamp, clamp_metrics
                from engine.flags import update_world_flags
                
                world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion + cohesion_delta)
                clamp_metrics(world.metrics)
                update_world_flags(world)
                
                continue
            
            if user_input.lower() in ["/advise", "advise"]:
                # Get advice from all advisors
                typer.echo("")
                
                if RICH_ENABLED:
                    # Top border
                    box = BOX["round"]
                    title = " COBRA ADVISORY PANEL "
                    title_len = len(title)
                    left_pad = (WIDTH - title_len - 2) // 2
                    right_pad = WIDTH - title_len - left_pad - 2
                    console.print(f"[{COLORS['accent']} bold]{box['tl']}{box['h'] * left_pad}{title}{box['h'] * right_pad}{box['tr']}[/{COLORS['accent']} bold]")
                    typer.echo("")
                else:
                    typer.echo("=" * 79)
                    typer.echo("COBRA ADVISORY PANEL")
                    typer.echo("=" * 79)
                    typer.echo("")
                
                typer.echo("Requesting input from all advisors on the current situation...")
                typer.echo("")
                
                # Ask each advisor for their assessment
                # Add conciseness instruction to keep responses brief
                advisors = [
                    ("National Security Advisor", "NSA, what's your assessment of the current situation and recommended course of action? [Please be concise - 3-4 sentences maximum]"),
                    ("Chief of the Defence Staff", "CDS, what are our military options and constraints? [Please be concise - 3-4 sentences maximum]"),
                    ("Foreign Secretary", "Foreign Secretary, what's the diplomatic landscape and alliance status? [Please be concise - 3-4 sentences maximum]"),
                    ("Home Secretary", "Home Secretary, what are the domestic security concerns? [Please be concise - 3-4 sentences maximum]"),
                    ("Attorney General", "Attorney General, what are the legal constraints and considerations? [Please be concise - 3-4 sentences maximum]")
                ]
                
                for advisor_name, question in advisors:
                    # Separator between advisors
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                    else:
                        typer.echo("─" * 79)
                    
                    console.print(f"  [{COLORS['secondary']} bold]{advisor_name.upper()}[/{COLORS['secondary']} bold]")
                    typer.echo("")
                    
                    # Get response from this advisor
                    discussion_lines = run_turn_discussion(world, scenario, [question], rng, root, transcript)
                    for line in discussion_lines:
                        # Skip the "Prime Minister:" echo and strip the conciseness instruction
                        if not line.startswith("Prime Minister:"):
                            # Remove the [Please be concise...] instruction from display
                            display_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            if display_line:  # Only display non-empty lines
                                # Format response with structure
                                if ":" in display_line:
                                    advisor_role, rest = display_line.split(":", 1)
                                    if RICH_ENABLED:
                                        formatted = format_advisor_response("", rest)
                                        console.print(formatted)
                                    else:
                                        console.print(f"[{COLORS['secondary']} bold]{advisor_role}:[/{COLORS['secondary']} bold]", end="")
                                        console.print(rest)
                                else:
                                    typer.echo(display_line)
                        else:
                            # For transcript, clean up the question
                            clean_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            transcript.append(clean_line)
                            continue
                    # Only add non-question lines to transcript (questions already added above)
                    transcript.extend([l for l in discussion_lines if not l.startswith("Prime Minister:")])
                    typer.echo("")
                
                if RICH_ENABLED:
                    # Bottom border
                    console.print(f"[{COLORS['accent']} bold]{box['bl']}{box['h'] * (WIDTH - 2)}{box['br']}[/{COLORS['accent']} bold]")
                else:
                    typer.echo("=" * 79)
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/resources", "resources"]:
                # Display UK forces and stockpiles
                initial_conditions = load_initial_conditions(scenario, root)
                
                typer.echo("")
                
                if RICH_ENABLED:
                    forces_table, stockpiles_table = resources_tables(initial_conditions)
                    console.print(forces_table)
                    typer.echo("")
                    console.print(stockpiles_table)
                    typer.echo("")
                    continue
                
                # Fallback to plain text
                typer.echo("=" * 79)
                typer.echo("UK MILITARY RESOURCES")
                typer.echo("=" * 79)
                typer.echo("")
                
                # Display stockpiles
                stockpiles = initial_conditions.get("stockpiles", {})
                if stockpiles:
                    typer.echo("AMMUNITION STOCKPILES:")
                    typer.echo("")
                    
                    # Air Defence
                    air_defence = stockpiles.get("air_defence_missiles", {})
                    if air_defence:
                        typer.echo("  Air Defence:")
                        for weapon, data in air_defence.items():
                            count = data.get("count", 0)
                            note = data.get("note", "")
                            typer.echo(f"    • {weapon.replace('_', ' ').title()}: {count}")
                            if note:
                                typer.echo(f"      {note}")
                        typer.echo("")
                    
                    # Naval Strike
                    typer.echo("  Naval Strike:")
                    tomahawk = stockpiles.get("tomahawk_cruise_missiles", {})
                    if tomahawk:
                        typer.echo(f"    • Tomahawk Cruise Missiles: {tomahawk.get('count', 0)}")
                        typer.echo(f"      {tomahawk.get('note', '')}")
                    harpoon = stockpiles.get("harpoon_anti_ship", {})
                    if harpoon:
                        typer.echo(f"    • Harpoon Anti-Ship: {harpoon.get('count', 0)}")
                        typer.echo(f"      {harpoon.get('note', '')}")
                    typer.echo("")
                    
                    # Air-Launched
                    typer.echo("  Air-Launched Precision:")
                    storm_shadow = stockpiles.get("storm_shadow_cruise_missiles", {})
                    if storm_shadow:
                        typer.echo(f"    • Storm Shadow: {storm_shadow.get('count', 0)}")
                        typer.echo(f"      {storm_shadow.get('note', '')}")
                    paveway = stockpiles.get("paveway_laser_guided_bombs", {})
                    if paveway:
                        typer.echo(f"    • Paveway LGBs: {paveway.get('count', 0)}")
                        typer.echo(f"      {paveway.get('note', '')}")
                    typer.echo("")
                    
                    # Anti-Submarine
                    typer.echo("  Anti-Submarine:")
                    spearfish = stockpiles.get("spearfish_torpedoes", {})
                    if spearfish:
                        typer.echo(f"    • Spearfish Torpedoes: {spearfish.get('count', 0)}")
                        typer.echo(f"      {spearfish.get('note', '')}")
                    stingray = stockpiles.get("stingray_lightweight_torpedoes", {})
                    if stingray:
                        typer.echo(f"    • Stingray Torpedoes: {stingray.get('count', 0)}")
                        typer.echo(f"      {stingray.get('note', '')}")
                    typer.echo("")
                
                # Display forces
                uk_forces = initial_conditions.get("uk_forces", {})
                if uk_forces:
                    naval = uk_forces.get("naval", [])
                    if naval:
                        typer.echo("NAVAL FORCES:")
                        typer.echo("")
                        for unit in naval:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            typer.echo(f"  • {unit_id} ({unit_type})")
                            typer.echo(f"    Location: {location}")
                            typer.echo(f"    Status: {status}")
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            typer.echo("")
                    
                    air = uk_forces.get("air", [])
                    if air:
                        typer.echo("AIR FORCES:")
                        typer.echo("")
                        for unit in air:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            
                            # Display unit header
                            typer.echo(f"  • {unit_id}")
                            
                            # Show type and role
                            if unit_type:
                                role = unit.get("role", "")
                                if role:
                                    typer.echo(f"    Type: {unit_type} ({role})")
                                else:
                                    typer.echo(f"    Type: {unit_type}")
                            
                            # Show location if present
                            if location:
                                typer.echo(f"    Location: {location}")
                            
                            # Show aircraft counts if present
                            aircraft_count = unit.get("aircraft_count")
                            operational_aircraft = unit.get("operational_aircraft")
                            if aircraft_count is not None:
                                if operational_aircraft is not None:
                                    typer.echo(f"    Aircraft: {operational_aircraft}/{aircraft_count} operational")
                                else:
                                    typer.echo(f"    Aircraft: {aircraft_count}")
                            
                            # Show status
                            typer.echo(f"    Status: {status}")
                            
                            # Show note if present
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            
                            typer.echo("")
                
                typer.echo("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/intel"):
                # Intelligence command - detailed actor assessment
                typer.echo("")
                
                # Parse command: /intel or /intel <country_code>
                parts = user_input.lower().split()
                if len(parts) == 1:
                    # Show available actors
                    if world.actor_system:
                        typer.echo("Available countries for intelligence assessment:")
                        typer.echo("")
                        for code, actor in world.actor_system.actors.items():
                            typer.echo(f"  /intel {code.lower()} - {actor.full_name}")
                        typer.echo("")
                    else:
                        typer.echo("Intelligence system not available.")
                else:
                    # Show detailed assessment for specific actor
                    country_code = parts[1].upper()
                    if world.actor_system:
                        from engine.intelligence import generate_actor_detailed_assessment
                        intel_lines = generate_actor_detailed_assessment(country_code, world, world.turn)
                        for line in intel_lines:
                            console.print(line)
                    else:
                        typer.echo("Intelligence system not available.")
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/llm", "llm", "/settings", "settings"]:
                # Open LLM model settings menu
                typer.echo("")
                typer.echo("Opening LLM Model Settings...")
                typer.echo("")
                model_settings_menu()
                # After returning from settings, clear and redisplay the discussion phase
                typer.clear()
                typer.echo("")
                if RICH_ENABLED:
                    console.print(phase_header("DISCUSSION", world.turn))
                    typer.echo("")
                    typer.echo("  Ask questions or type /decide when ready")
                    console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /intel  /llm[/{COLORS['muted']}]")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("=" * 79)
                    console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
                    console.print("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower() in ["/menu", "menu", "/help", "help"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Show advisor panel
                    console.print(advisor_menu_panel())
                    typer.echo("")
                    
                    # Show diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    console.print(diplomatic_contacts_table(available_contacts))
                    typer.echo("")
                    
                    # Show metrics guide
                    console.print(metrics_guide_panel())
                    typer.echo("")
                    
                    # Show commands
                    console.print(command_menu())
                    typer.echo("")
                    
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                else:
                    # Fallback to plain text
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]AVAILABLE ADVISORS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• National Security Advisor (NSA)")
                    typer.echo("  - Intelligence assessment, strategic planning, threat analysis")
                    typer.echo("  - Example: 'NSA, what's your assessment of Russian intentions?'")
                    typer.echo("")
                    typer.echo("• Chief of the Defence Staff (CDS)")
                    typer.echo("  - Military operations, force readiness, deployment options")
                    typer.echo("  - Example: 'CDS, what are our air defence capabilities?'")
                    typer.echo("")
                    typer.echo("• Foreign Secretary")
                    typer.echo("  - Diplomacy, alliance management, NATO coordination")
                    typer.echo("  - Example: 'Foreign Secretary, can we count on US support?'")
                    typer.echo("")
                    typer.echo("• Home Secretary")
                    typer.echo("  - Domestic security, civil protection, public messaging")
                    typer.echo("  - Example: 'Home Secretary, how do we reassure the public?'")
                    typer.echo("")
                    typer.echo("• Attorney General")
                    typer.echo("  - Legal framework, international law, rules of engagement")
                    typer.echo("  - Example: 'Attorney General, what are our legal constraints?'")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['success']} bold]DIPLOMATIC CONTACTS[/{COLORS['success']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    
                    # List available diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    if available_contacts:
                        for country, access_level, title in available_contacts:
                            if access_level == "leader":
                                console.print(f"[{COLORS['warning']} bold]  * LEADER[/{COLORS['warning']} bold] - {country}: {title}")
                            else:
                                console.print(f"  • Diplomat - {country}: {title}")
                            console.print(f"    Command: /call {country.lower()}")
                            typer.echo("")
                    else:
                        typer.echo("  No diplomatic contacts available (Alliance Cohesion too low)")
                        typer.echo("")
                    
                    console.print("=" * 60)
                    console.print(f"[{COLORS['warning']} bold]METRICS GUIDE[/{COLORS['warning']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• Escalation Risk (0-100)")
                    typer.echo("  Likelihood of conflict escalating to full-scale war")
                    typer.echo("  HIGH = Danger of Russian attack or nuclear exchange")
                    typer.echo("")
                    typer.echo("• Domestic Stability (0-100)")
                    typer.echo("  Public confidence, economic stability, infrastructure security")
                    typer.echo("  LOW = Civil unrest, panic, political pressure")
                    typer.echo("")
                    typer.echo("• Alliance Cohesion (0-100)")
                    typer.echo("  Strength of NATO solidarity and allied support")
                    typer.echo("  HIGH = Access to leaders, Article 5 support likely")
                    typer.echo("  LOW = Isolated, limited diplomatic access")
                    typer.echo("")
                    typer.echo("• Influence (-10 to +10)")
                    typer.echo("  Your political capital and public sentiment")
                    typer.echo("  Derived from: (Stability + Cohesion) / 2")
                    typer.echo("  Currently: Informational only (future: affects options)")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]COMMANDS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    console.print("")
                    console.print(f"[{COLORS['primary']}]  /menu or /help[/{COLORS['primary']}]     - Show this menu")
                    console.print(f"[{COLORS['primary']}]  /status[/{COLORS['primary']}]            - Show current metrics and situation")
                    console.print(f"[{COLORS['primary']}]  /advise[/{COLORS['primary']}]            - Get input from all advisors at once")
                    console.print(f"[{COLORS['primary']}]  /resources[/{COLORS['primary']}]         - Show UK forces and ammunition stockpiles")
                    console.print(f"[{COLORS['primary']}]  /call <country>[/{COLORS['primary']}]    - Contact a foreign leader or diplomat")
                    console.print(f"[{COLORS['primary']}]  /decide[/{COLORS['primary']}]            - Make your decision")
                    console.print(f"[{COLORS['primary']}]  /theme[/{COLORS['primary']}]             - Change UI theme")
                    console.print(f"[{COLORS['primary']}]  /save[/{COLORS['primary']}]              - Save game and continue")
                    console.print(f"[{COLORS['primary']}]  /quit[/{COLORS['primary']}]              - Exit game")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                
                typer.echo("")
                continue
            
            # Handle question
            questions.append(user_input)
            discussion_lines = run_turn_discussion(world, scenario, [user_input], rng, root, transcript)
            
            typer.echo("")  # Space before response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                typer.echo("")
            
            for line in discussion_lines:
                # Skip echoing the player's question (they just typed it)
                if not line.startswith("Prime Minister:"):
                    if ":" in line:
                        advisor_name, rest = line.split(":", 1)
                        
                        # Print advisor name
                        console.print(f"  [{COLORS['secondary']} bold]{advisor_name}[/{COLORS['secondary']} bold]")
                        typer.echo("")
                        
                        # Format response with structure
                        if RICH_ENABLED:
                            formatted = format_advisor_response("", rest)
                            console.print(formatted)
                        else:
                            typer.echo(rest)
                    else:
                        typer.echo(line)
            
            transcript.extend(discussion_lines)
            
            typer.echo("")  # Space after response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
            
            typer.echo("")
        
        # Decision phase loop - allows returning to discussion if decision is cancelled
        decision_confirmed = False
        while not decision_confirmed:
            # Decision phase - clear screen and start at top
            typer.clear()
            typer.echo("")  # Buffer line
            
            if RICH_ENABLED:
                console.print(phase_header("DECISION", world.turn))
                typer.echo("")
                typer.echo("  Enter your decision (or 'cancel' to return to discussion)")
            else:
                console.print("=" * 79)
                console.print(f"[{COLORS['emphasis']} bold]TURN {world.turn}: DECISION PHASE[/{COLORS['emphasis']} bold]")
                console.print("=" * 79)
                console.print("")
                console.print("Enter your decision (or 'cancel' to return to discussion):")
            
            typer.echo("")
            
            action = typer.prompt("Decision>").strip()
            
            if action.lower() == "cancel":
                # Return to discussion phase
                break
            
            if not action:
                typer.echo("No action entered. Returning to discussion.")
                typer.echo("")
                wait_for_space("Press SPACE to return to discussion...")
                break
            
            # Interpret and get pushback
            interpretation, pushback, critical_concerns, decision_lines = run_turn_decision(world, scenario, action, rng, root, transcript)
            transcript.extend(decision_lines)
            
            # Display decision with improved UX
            display_decision_summary(action, interpretation, show_details=False)
            
            # Option to see full details
            see_details = typer.prompt("", default="").strip().lower()
            if see_details == "details":
                display_decision_summary(action, interpretation, show_details=True)
                console.print("")
            
            # Handle critical omissions with selective addressing
            if critical_concerns:
                action_code, selected_indices = display_critical_concerns_with_selection(critical_concerns)
                
                if action_code == 'D':
                    # Return to discussion
                    typer.echo("")
                    typer.echo("Returning to discussion phase.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break
                
                elif action_code == 'M':
                    # Modify manually
                    typer.echo("")
                    typer.echo("Decision cancelled. Please enter a modified decision.")
                    typer.echo("")
                    continue
                
                elif action_code in ['A', 'S'] and selected_indices:
                    # Apply selected recommendations
                    console.print("")
                    console.print(f"[{COLORS['success']}]Applying {len(selected_indices)} recommendation(s)...[/{COLORS['success']}]")
                    console.print("")
                    
                    # Append recommendations
                    enhanced_decision = append_recommendations_to_decision(action, critical_concerns, selected_indices)
                    
                    # Show enhanced decision
                    from rich.panel import Panel
                    console.print(Panel(f"[italic]{enhanced_decision}[/italic]", title="[bold]ENHANCED DECISION[/bold]", border_style="white"))
                    console.print("")
                    
                    # Confirm
                    confirm = typer.confirm("Proceed with enhanced decision?", default=True)
                    
                    if not confirm:
                        console.print("")
                        console.print("Decision cancelled.")
                        console.print("")
                        continue
                    
                    # Update action for adjudication
                    action = enhanced_decision
                    
                    # Re-interpret
                    console.print("")
                    console.print("Re-interpreting enhanced decision...")
                    console.print("")
                    
                    interpretation, pushback, critical_concerns_2, decision_lines_2 = run_turn_decision(world, scenario, action, rng, root, transcript)
                    transcript.extend(decision_lines_2)
                    
                    # Display new interpretation
                    display_decision_summary(action, interpretation, show_details=False)
                    
                    # If STILL have concerns, warn
                    if critical_concerns_2:
                        console.print("")
                        console.print(f"[{COLORS['warning']}]⚠ Warning: Critical concerns remain.[/{COLORS['warning']}]")
                        console.print("")
                        # Let player proceed or go back
                        cont = typer.confirm("Proceed anyway?", default=False)
                        if not cont:
                            continue
                    
                    decision_confirmed = True
                
                else:  # 'I' - Ignore
                    typer.echo("")
                    typer.echo(f"[{COLORS['warning']}]Proceeding despite all concerns...[/{COLORS['warning']}]")
                    typer.echo("")
                    decision_confirmed = True
            
            # Confirm decision (regular pushback, if any)
            elif pushback:
                typer.echo("")
                confirm = typer.confirm("Proceed with this decision despite concerns?", default=True)
                if not confirm:
                    typer.echo("")
                    typer.echo("Decision cancelled. Returning to discussion.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break  # Break inner loop, return to discussion
                else:
                    decision_confirmed = True  # Proceed to adjudication
            else:
                decision_confirmed = True  # No pushback, proceed to adjudication
        
        # If decision was cancelled, go back to discussion phase
        if not decision_confirmed:
            continue
        
        # Adjudication phase - clear screen and start at top
        typer.clear()
        typer.echo("")  # Buffer line
        
        if RICH_ENABLED:
            console.print(phase_header("ADJUDICATION", world.turn))
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['success']} bold]TURN {world.turn}: ADJUDICATION[/{COLORS['success']} bold]")
            console.print("=" * 79)
        
        typer.echo("")  # Buffer line
        
        # Run LLM-driven adjudication with narrative quality assessment
        try:
            actor_responses = []
            
            if world.actor_system:
                # Use multi-agent simulation
                from engine.narrative_adjudication import adjudicate_with_actor_simulation
                
                final_effects, actor_responses, character_responses, reasoning = adjudicate_with_actor_simulation(
                    narrative_state,
                    world.actor_system,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            else:
                # Use standard narrative adjudication
                final_effects, character_responses, reasoning = adjudicate_with_narrative(
                    narrative_state,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            
            # Display quality reasoning
            typer.echo("")
            if RICH_ENABLED:
                console.print(Panel(format_markdown(reasoning), title=f"[{COLORS['accent']} bold]ACTION ASSESSMENT[/]", border_style=COLORS['accent']))
            else:
                typer.echo("=" * 60)
                typer.echo("ACTION ASSESSMENT")
                typer.echo("=" * 60)
                typer.echo("")
                typer.echo(reasoning)
            typer.echo("")
            
            # Display effects
            if RICH_ENABLED:
                console.print(f"[{COLORS['accent']} bold]EFFECTS[/]")
                console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
            else:
                typer.echo("=" * 60)
                typer.echo("EFFECTS")
                typer.echo("=" * 60)
            typer.echo("")
            
            for metric, delta in final_effects.items():
                if RICH_ENABLED:
                    color = COLORS['success'] if delta > 0 else COLORS['danger'] if delta < 0 else COLORS['muted']
                    console.print(f"  [{color}]{metric}: {delta:+d}[/{color}]")
                else:
                    typer.echo(f"  {metric}: {delta:+d}")
            typer.echo("")
            
            # Display character responses
            if character_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]ADVISOR REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("ADVISOR REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for char_name, response in character_responses:
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['secondary']} bold]{char_name}:[/{COLORS['secondary']} bold]")
                        console.print(f"  \"{response}\"")
                    else:
                        typer.echo(f"{char_name}:")
                        typer.echo(f"  \"{response}\"")
                    typer.echo("")
            
            # Display international reactions (multi-agent simulation)
            if actor_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]INTERNATIONAL REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("INTERNATIONAL REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for response in actor_responses:
                    trust_delta = response.trust_change
                    actor_id = response.actor_id
                    
                    # Get full name if available
                    actor_name = actor_id
                    if world.actor_system:
                        actor = world.actor_system.get_actor(actor_id)
                        if actor:
                            actor_name = actor.full_name
                    
                    if RICH_ENABLED:
                        color = COLORS['success'] if trust_delta > 0 else COLORS['danger'] if trust_delta < 0 else COLORS['muted']
                        console.print(f"[{COLORS['primary']} bold]{actor_name}:[/{COLORS['primary']} bold] [{color}]({trust_delta:+d})[/{color}]")
                        console.print(f"  \"{response.public_response}\"")
                    else:
                        typer.echo(f"{actor_name}: ({trust_delta:+d})")
                        typer.echo(f"  \"{response.public_response}\"")
                    typer.echo("")
            
            # Sync world metrics with narrative state (keep both in sync)
            world.metrics.escalation_risk = narrative_state.hidden_metrics.escalation_risk
            world.metrics.domestic_stability = narrative_state.hidden_metrics.domestic_stability
            world.metrics.alliance_cohesion = narrative_state.hidden_metrics.alliance_cohesion
            world.metrics.casualties_mil = narrative_state.hidden_metrics.casualties_mil
            world.metrics.casualties_civ = narrative_state.hidden_metrics.casualties_civ
            
            # Build transcript for save file
            adjudication_lines = [
                "Action Assessment:",
                reasoning,
                "",
                "Effects:"
            ]
            for metric, delta in final_effects.items():
                adjudication_lines.append(f"  {metric}: {delta:+d}")
            adjudication_lines.append("")
            
            if character_responses:
                adjudication_lines.append("Advisor Reactions:")
                for char_name, response in character_responses:
                    adjudication_lines.append(f"{char_name}: \"{response}\"")
                adjudication_lines.append("")
                
            if actor_responses:
                adjudication_lines.append("International Reactions:")
                for response in actor_responses:
                    adjudication_lines.append(f"{response.actor_id}: \"{response.public_response}\"")
                adjudication_lines.append("")
            
            transcript.extend(adjudication_lines)
        
        except Exception as e:
            # Fallback to primitive system on error
            if RICH_ENABLED:
                console.print(f"[{COLORS['warning']}][WARNING] LLM adjudication failed: {e}[/{COLORS['warning']}]")
                console.print(f"[{COLORS['warning']}][INFO] Falling back to keyword-based adjudication[/{COLORS['warning']}]")
            else:
                typer.echo(f"[WARNING] LLM adjudication failed: {e}")
                typer.echo("[INFO] Falling back to keyword-based adjudication")
            typer.echo("")
            
            adjudication_lines = run_turn_adjudication_fallback(world, action, interpretation, rng)
            for line in adjudication_lines:
                typer.echo(line)
            transcript.extend(adjudication_lines)
            
            # Sync narrative state from world (reverse sync in fallback mode)
            narrative_state.update_hidden_metrics({
                "escalation_risk": world.metrics.escalation_risk,
                "domestic_stability": world.metrics.domestic_stability,
                "alliance_cohesion": world.metrics.alliance_cohesion,
                "casualties_mil": world.metrics.casualties_mil,
                "casualties_civ": world.metrics.casualties_civ
            })
        
        # Narrative state turn already updated by adjudicate_with_narrative()
        narrative_state.turn = world.turn
        
        # Display based on play mode
        typer.echo("")
        if play_mode == "classic":
            # Classic mode: Show raw metrics with deltas
            if RICH_ENABLED:
                console.print(metrics_table(world, show_deltas=True, previous_metrics=turn_start_metrics))
                typer.echo("")  # Buffer after table
        elif play_mode == "immersive":
            # Immersive mode: Show vibes + character attitudes
            typer.echo("═" * 60)
            typer.echo("SITUATION ASSESSMENT")
            typer.echo("═" * 60)
            typer.echo("")
            
            vibes = narrative_state.get_situation_vibes()
            for vibe in vibes:
                typer.echo(vibe.to_string())
            
            typer.echo("")
            typer.echo("═" * 60)
            typer.echo("ADVISOR ATTITUDES")
            typer.echo("═" * 60)
            typer.echo("")
            
            for char_id, char_attitude in narrative_state.characters.items():
                # Create visual trust bar
                trust_level = char_attitude.trust // 20  # 0-5 scale
                trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                relationship_symbol = {
                    "allied": "✓",
                    "neutral": "○",
                    "hostile": "✗",
                    "unknown": "?"
                }.get(char_attitude.relationship, "○")
                
                typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
            
            typer.echo("")
        elif play_mode == "emergent":
            # Emergent mode: Narrative summary only
            typer.echo("═" * 60)
            typer.echo(narrative_state.situation_summary)
            typer.echo("═" * 60)
            typer.echo("")
        
        # Auto-save after each turn
        save_path = save_game(world, transcript, scenario, "autosave", root, play_mode, narrative_state)
        
        # Advance turn
        world.turn += 1
        world.scene = world.turn  # Keep scene in sync for legacy compatibility
        world.discussion_transcript = []
        
        typer.echo("")
        typer.echo("=" * 60)
        typer.echo(f"Turn {world.turn - 1} complete. Auto-saved to {save_path.name}")
        typer.echo("=" * 60)
        typer.echo("")
        
        # Continue to next turn with spacebar
        try:
            wait_for_space("Press SPACE to continue to next turn (or Ctrl+C to exit)...")
        except KeyboardInterrupt:
            typer.echo("\nGame paused. Use --load to resume.")
            break


@app.command(rich_help_panel="GAMEPLAY")
def batch(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed"),
    action: str = typer.Option("Deploy defensive forces", help="Action to take"),
):
    """Run a single turn in batch mode (for testing)."""
    
    transcript = run_single_scene(scenario, seed, "llm")
    for line in transcript:
        typer.echo(line)


@app.command(rich_help_panel="UTILITY")
def settings():
    """Configure LLM model settings (Flash vs Pro per system)."""
    console.print("\n[bold cyan]LLM Model Settings[/bold cyan]\n")
    console.print("Configure which systems use Flash (fast/cheap) vs Pro (sophisticated/expensive)\n")
    
    model_settings_menu()


@app.command(rich_help_panel="UTILITY")
def intro():
    """Display the intro text."""
    for line in get_intro_lines(200):
        typer.echo(line)


if __name__ == "__main__":
    app()

```

Now I need to add message logging to the dashboard. Let me add it for user questions and advisor responses:

```python
"""Interactive CLI for the wargame with two-phase turn structure.

Supports:
- Interactive mode: discussion → decision → adjudication
- Batch mode: run with pre-defined action
- Save/load game state
- Stochastic inject generation
"""

import typer
from pathlib import Path
from random import Random
from typing import Optional
import sys
import os

# CRITICAL: Import msvcrt FIRST on Windows (before Rich)
if sys.platform == "win32":
    import msvcrt

# Allow running this file directly
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# THEN import Rich (after msvcrt is loaded)
from cli.rich_ui import (
    console, phase_header, metrics_table,
    advisor_menu_panel, diplomatic_contacts_table,
    resources_tables, command_menu, metrics_guide_panel,
    format_markdown, RICH_ENABLED
)
from cli.theme import theme_manager, COLORS, SYMBOLS, BOX, WIDTH
from cli.formatters import format_advisor_response
from models.world import WorldState, Metrics
from models.narrative_state import NarrativeState, create_initial_narrative_state, PlayMode
from models.narrative import NarrativeConfig
from engine.scenario_loader import list_available_scenarios, get_scenario_config, get_turn_filename, load_narrative_configs
from engine.sim_loop import (
    run_turn_briefing,
    run_turn_discussion,
    run_turn_decision,
    run_turn_adjudication as run_turn_adjudication_fallback,  # Renamed for fallback
    run_single_scene
)
from engine.narrative_adjudication import adjudicate_with_narrative
from engine.intro import get_intro_lines
from engine.persistence import save_game, load_game
from engine.initial_conditions import load_initial_conditions
from engine.diplomacy import run_diplomatic_encounter, list_available_diplomatic_contacts
from llm.router import generate_text
from cli.model_settings_menu import model_settings_menu

# Task 2.5: Enable Rich help panel
app = typer.Typer(
    rich_markup_mode="rich", 
    help="FALSE FLAG: THE WARGAME - LLM-driven crisis simulation",
    no_args_is_help=True
)


def scroll_text(text: str, delay: float = 0.03, allow_skip: bool = True) -> bool:
    """Print text character by character with optional skip.
    
    Args:
        text: Text to scroll
        delay: Delay between characters (seconds)
        allow_skip: If True, pressing SPACE skips to end of scene
        
    Returns:
        True if user pressed SPACE to skip, False otherwise
    """
    import msvcrt
    import sys
    
    for i, char in enumerate(text):
        # Check if user pressed SPACE to skip rest of scene
        if allow_skip and msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                # Print rest of line and return skip signal
                sys.stdout.write(text[i:])
                sys.stdout.flush()
                print()
                return True  # Signal to skip rest of scene
            # Ignore other keys, continue scrolling
        
        sys.stdout.write(char)
        sys.stdout.flush()
        
        # Slightly longer pause after punctuation
        if char in '.!?':
            import time
            time.sleep(delay * 3)
        elif char in ',;:':
            import time
            time.sleep(delay * 2)
        else:
            import time
            time.sleep(delay)
    
    print()  # Newline at end
    return False  # No skip


def wait_for_space(prompt: str = "Press SPACE to continue...") -> None:
    """Wait for user to press spacebar to continue."""
    import msvcrt  # Windows-specific
    typer.echo("")
    typer.echo(prompt)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                typer.echo("")
                break


def parse_interpretation_simple(interpretation: str) -> dict:
    """Parse LLM interpretation into key sections for display.
    
    Args:
        interpretation: Full interpretation text
    
    Returns:
        Dict with parsed sections
    """
    sections = {
        "summary": "",
        "forces": [],
        "timeline": "",
        "concerns": ""
    }
    
    lines = interpretation.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("INTERPRETATION:"):
            sections["summary"] = line.replace("INTERPRETATION:", "").strip()
        elif line.startswith("FORCES INVOLVED:"):
            current_section = "forces"
        elif line.startswith("TIMELINE:"):
            current_section = "timeline"
        elif line.startswith("FEASIBILITY:"):
            if "impossible" in line.lower() or "requires clarification" in line.lower():
                sections["concerns"] = line.replace("FEASIBILITY:", "").strip()
            current_section = None
        elif current_section == "forces" and line and line.startswith("*"):
            # Extract force name from bullet point
            force = line.lstrip("* ").split(":")[0] if ":" in line else line.lstrip("* ")
            if force and len(sections["forces"]) < 5:  # Max 5 forces shown
                sections["forces"].append(force)
        elif current_section == "timeline" and line:
            sections["timeline"] = line
    
    return sections


def display_decision_summary(action: str, interpretation: str, show_details: bool = False):
    """Display decision interpretation in player-friendly format.
    
    Args:
        action: Player's original decision text
        interpretation: Full LLM interpretation
        show_details: If True, show full interpretation
    """
    COLORS = theme_manager.get_colors()
    
    # Show player's exact words in a box
    console.print("")
    from rich.panel import Panel
    console.print(Panel(f"[italic]{action}[/italic]", title="[bold]YOUR DECISION[/bold]", border_style="white"))
    console.print("")
    
    if show_details:
        # Show full interpretation
        console.print(Panel(format_markdown(interpretation), title="[bold]FULL INTERPRETATION (DETAILED)[/bold]", border_style="blue"))
        console.print("")
    else:
        # Show simplified summary
        parsed = parse_interpretation_simple(interpretation)
        
        # Build content for panel
        content = []
        
        # Show summary if we extracted one
        if parsed["summary"]:
            content.append(parsed["summary"])
            content.append("")
        
        # Show key forces
        if parsed["forces"]:
            content.append(f"[{COLORS['success']}]Forces Deployed:[/{COLORS['success']}]")
            for force in parsed["forces"]:
                content.append(f"  • {force}")
            content.append("")
        
        # Show timeline
        if parsed["timeline"]:
            content.append(f"[{COLORS['accent']}]Estimated Timeline:[/{COLORS['accent']}] {parsed['timeline']}")
            content.append("")
        
        # Show concerns
        if parsed["concerns"]:
            content.append(f"[{COLORS['warning']}]⚠ Operational Concerns: {parsed['concerns']}[/{COLORS['warning']}]")
            content.append("")
        
        content.append(f"[{COLORS['muted']}](Type 'details' to see full interpretation)[/{COLORS['muted']}]")
        
        console.print(Panel("\n".join(content), title="[bold]📋 OPERATIONAL ORDER[/bold]", border_style="cyan"))


def display_critical_concerns_with_selection(critical_concerns: list) -> tuple:
    """Display critical concerns and let player select which to address.
    
    Args:
        critical_concerns: List of (role, concern, recommendation) tuples
    
    Returns:
        Tuple of (action_code, selected_indices)
        action_code: 'A' (all), 'S' (select), 'M' (modify), 'I' (ignore), 'D' (discussion)
        selected_indices: List of 0-based indices of selected concerns
    """
    from rich.panel import Panel
    COLORS = theme_manager.get_colors()
    
    console.print("")
    console.print(Panel(f"Advisors have raised {len(critical_concerns)} critical concerns regarding your decision.", 
                        title=f"[{COLORS['warning']} bold]⚠️ CRITICAL ADVISORIES[/]", 
                        border_style=COLORS['warning']))
    console.print("")
    
    # Display each concern with number
    for idx, (role, concern, recommendation) in enumerate(critical_concerns, 1):
        console.print(f"[{COLORS['warning']} bold][{idx}] {role}[/{COLORS['warning']} bold]")
        console.print(f"  {concern}")
        console.print(f"  [{COLORS['primary']}]→ RECOMMENDATION: \"{recommendation}\"[/{COLORS['primary']}]")
        console.print("")
        console.print(f"[{COLORS['muted']}]" + "─" * 40 + f"[/{COLORS['muted']}]")
        console.print("")
    
    # Get selection
    console.print("Which concerns would you like to address?")
    console.print("")
    console.print(f"  [{COLORS['primary']}]A[/{COLORS['primary']}] - Apply ALL recommendations to my decision")
    console.print(f"  [{COLORS['primary']}]S[/{COLORS['primary']}] - Select specific recommendations")
    console.print(f"  [{COLORS['primary']}]M[/{COLORS['primary']}] - Modify decision manually instead")
    console.print(f"  [{COLORS['primary']}]I[/{COLORS['primary']}] - Ignore all and proceed anyway")
    console.print(f"  [{COLORS['primary']}]D[/{COLORS['primary']}] - Return to discussion phase")
    console.print("")
    
    choice = typer.prompt("Choose", type=str).strip().upper()
    
    if choice == "A":
        return ('A', list(range(len(critical_concerns))))
    elif choice == "S":
        console.print("")
        console.print("Enter concern numbers separated by spaces (e.g., '1 3')")
        selection = typer.prompt("Select").strip()
        try:
            indices = [int(x) - 1 for x in selection.split()]
            valid_indices = [i for i in indices if 0 <= i < len(critical_concerns)]
            return ('S', valid_indices)
        except ValueError:
            console.print(f"[{COLORS['danger']}]Invalid selection.[/{COLORS['danger']}]")
            return ('M', [])
    elif choice == "M":
        return ('M', [])
    elif choice == "I":
        return ('I', [])
    elif choice == "D":
        return ('D', [])
    else:
        console.print(f"[{COLORS['warning']}]Invalid choice. Please try again.[/{COLORS['warning']}]")
        return display_critical_concerns_with_selection(critical_concerns)


def append_recommendations_to_decision(original_decision: str, critical_concerns: list, selected_indices: list) -> str:
    """Append selected recommendations to original decision.
    
    Args:
        original_decision: Player's original decision text
        critical_concerns: Full list of concerns
        selected_indices: Indices of concerns to address
    
    Returns:
        Enhanced decision text
    """
    if not selected_indices:
        return original_decision
    
    additions = []
    for idx in selected_indices:
        role, concern, recommendation = critical_concerns[idx]
        additions.append(f"- {recommendation}")
    
    enhanced = original_decision
    enhanced += "\n\nAdditionally:"
    enhanced += "\n" + "\n".join(additions)
    
    return enhanced


def select_scenario_variant(scenario_id: str) -> str:
    """Display interactive scenario selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected variant key (e.g., 'standard', 'fast_start')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT SCENARIO[/{COLORS['primary']} bold]")
    console.print("")
    
    # Load available scenarios
    scenarios = list_available_scenarios(scenario_id)
    
    if len(scenarios) == 0:
        # No scenarios.yaml found - use default
        return "standard"
    
    # Display scenario options
    for idx, (key, config) in enumerate(scenarios, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        difficulty = config.get("difficulty", "")
        estimated_time = config.get("estimated_time", "")
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        if difficulty:
            console.print(f"   Difficulty: {difficulty}")
        if estimated_time:
            console.print(f"   Estimated Time: {estimated_time}")
        console.print(f"   {description}")
        
        # Show key features
        features = config.get("features", [])
        if features:
            console.print("")
            for feature in features[:3]:  # Show first 3 features
                console.print(f"   - {feature}")
        
        if recommended:
            console.print("")
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    console.print("")
    while True:
        try:
            choice = typer.prompt("Select scenario (enter number)", type=int)
            if 1 <= choice <= len(scenarios):
                selected_key = scenarios[choice - 1][0]
                selected_name = scenarios[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(scenarios)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_play_mode() -> str:
    """Display interactive gameplay mode selection menu.
    
    Returns:
        Selected mode key (e.g., 'classic', 'immersive', 'emergent')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAMEPLAY MODE[/{COLORS['primary']} bold]")
    console.print("")
    
    modes = [
        ("classic", {
            "name": "Classic Wargame",
            "description": "Traditional experience with visible metrics and mechanical effects",
            "features": [
                "See numerical impact of your decisions",
                "Clear thresholds and win conditions",
                "Strategic resource management focus"
            ],
            "recommended": "Traditional wargame players, first playthrough"
        }),
        ("immersive", {
            "name": "Immersive Narrative",
            "description": "Character-driven drama with hidden metrics guiding the story",
            "features": [
                "Visual 'vibes' instead of raw numbers",
                "Character attitudes and relationships",
                "Narrative consequences take center stage"
            ],
            "recommended": "Story-focused players, replay value"
        }),
        ("emergent", {
            "name": "Emergent Drama (Experimental)",
            "description": "Maximum LLM freedom with minimal structure",
            "features": [
                "Pure narrative immersion",
                "Every playthrough unique",
                "Unpredictable emergent outcomes"
            ],
            "recommended": "Experimental players, maximum replayability"
        })
    ]
    
    for idx, (key, config) in enumerate(modes, 1):
        console.print(f"[{COLORS['warning']} bold]{idx}. {config['name']}[/{COLORS['warning']} bold]")
        console.print(f"   {config['description']}")
        console.print("")
        for feature in config['features']:
            console.print(f"   - {feature}")
        console.print("")
        console.print(f"   Recommended for: {config['recommended']}")
        console.print("")
    
    while True:
        try:
            choice = typer.prompt("Select gameplay mode (enter number)", type=int, default=2)
            if 1 <= choice <= len(modes):
                selected_key = modes[choice - 1][0]
                selected_name = modes[choice - 1][1]['name']
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(modes)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_difficulty(scenario_id: str) -> str:
    """Display interactive difficulty selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected difficulty key (e.g., 'standard', 'challenging', 'brutal')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT DIFFICULTY[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Difficulty affects scenario effect magnitudes (crisis intensity).")
    console.print("Player action impacts remain the same across all difficulties.")
    console.print("")
    
    # Load difficulty definitions from scenarios.yaml
    root = Path(__file__).resolve().parents[1]
    scenario_path = root / "data" / "scenarios" / scenario_id / "scenarios.yaml"
    
    difficulties = []
    if scenario_path.exists():
        try:
            import yaml
            with open(scenario_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                difficulties_dict = data.get("difficulties", {})
                # Convert to list of tuples for consistent ordering
                difficulties = [
                    ("standard", difficulties_dict.get("standard", {})),
                    ("challenging", difficulties_dict.get("challenging", {})),
                    ("brutal", difficulties_dict.get("brutal", {}))
                ]
        except Exception:
            pass
    
    # Default if no difficulties found
    if not difficulties:
        difficulties = [
            ("standard", {"name": "Standard", "description": "Balanced challenge", "multiplier": 0.65}),
            ("challenging", {"name": "Challenging", "description": "Tight margins", "multiplier": 0.85}),
            ("brutal", {"name": "Brutal", "description": "Maximum intensity", "multiplier": 1.0})
        ]
    
    # Display difficulty options
    for idx, (key, config) in enumerate(difficulties, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        multiplier = config.get("multiplier", 1.0)
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        console.print(f"   Effect Multiplier: {multiplier}x")
        console.print(f"   {description}")
        
        if recommended:
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select difficulty (enter number)", type=int, default=1)
            if 1 <= choice <= len(difficulties):
                selected_key = difficulties[choice - 1][0]
                selected_name = difficulties[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(difficulties)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_narrative(scenario_id: str) -> Optional[NarrativeConfig]:
    """Display game type selection menu (Original Story Mode vs Mystery Mode).
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        None if Original Story Mode selected,
        NarrativeConfig (randomly chosen) if Mystery Mode selected
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAME TYPE[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Choose how you want to experience the crisis:")
    console.print("")
    
    # Display option 1: Original Story Mode
    console.print(f"[{COLORS['warning']} bold]1. Original Story Mode[/{COLORS['warning']} bold]")
    console.print("   Play the standard story mode as designed. Experience the crisis through")
    console.print("   the eyes of the Prime Minister as events unfold.")
    console.print("")
    
    # Display option 2: Mystery Mode
    console.print(f"[{COLORS['warning']} bold]2. Mystery Mode[/{COLORS['warning']} bold]")
    console.print("   A hidden narrative guides AI agent behaviour. Foreign leaders and")
    console.print("   diplomats may have secret motivations that aren't immediately apparent.")
    console.print("   You must deduce the truth from their actions and responses.")
    console.print("")
    console.print(f"   [{COLORS['danger']}]⚠ The narrative is randomly selected and hidden from you![/{COLORS['danger']}]")
    console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select game type (enter number)", type=int, default=1)
            if choice == 1:
                # Original Story Mode - no secret narrative
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Original Story Mode selected[/{COLORS['success']} bold]")
                console.print("")
                return None
            elif choice == 2:
                # Mystery Mode - randomly select narrative
                narratives = load_narrative_configs(scenario_id)
                
                if narratives:
                    import random
                    selected_narrative = random.choice(narratives)
                    console.print("")
                    console.print(f"[{COLORS['success']} bold]✓ Mystery Mode activated[/{COLORS['success']} bold]")
                    console.print("")
                    # DO NOT tell player which narrative was selected
                    return selected_narrative
                else:
                    # Fallback if no narratives available - treat as Original Mode
                    console.print("")
                    console.print(f"[{COLORS['warning']}]Mystery Mode unavailable - using Original Story Mode[/{COLORS['warning']}]")
                    console.print("")
                    return None
            else:
                console.print(f"[{COLORS['danger']}]Please enter 1 or 2[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


@app.command(rich_help_panel="GAMEPLAY")
def play(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed for determinism"),
    load_save: str = typer.Option(None, "--load", help="Load game from save file"),
    stochastic_injects: bool = typer.Option(True, "--stochastic-injects/--no-stochastic-injects", help="Generate injects dynamically (enabled by default)"),
    intro_only: bool = typer.Option(False, "--intro-only", help="Display intro and exit"),
    variant: str = typer.Option(None, "--variant", help="Scenario variant (e.g., 'standard', 'fast_start')"),
    difficulty: str = typer.Option(None, "--difficulty", help="Difficulty level (e.g., 'standard', 'challenging', 'brutal')"),
    play_mode: str = typer.Option(None, "--play-mode", help="Gameplay mode (e.g., 'classic', 'immersive', 'emergent')"),
    flash_only: bool = typer.Option(False, "--flash-only", help="Use Flash model for all LLM calls (5x faster, cheaper)"),
):
    """Play the wargame interactively."""
    
    # Get current colors for loop
    COLORS = theme_manager.get_colors()

    # Configure LLM model if flash_only flag is set
    if flash_only:
        from llm.model_config import get_model_config
        config = get_model_config()
        config.use_flash_for_all()
        typer.echo("")
        typer.echo("[Flash-only mode enabled - using gemini-2.5-flash for all calls]")
        typer.echo("")
    
    # If no variant specified and not loading a save, show selection menu
    if variant is None and load_save is None:
        variant = select_scenario_variant(scenario)
    elif variant is None:
        variant = "standard"  # Default for loaded games
    
    # If no play mode specified and not loading a save, show selection menu
    if play_mode is None and load_save is None:
        play_mode = select_play_mode()
    elif play_mode is None:
        play_mode = "immersive"  # Default for loaded games
    
    # If no difficulty specified and not loading a save, show selection menu
    if difficulty is None and load_save is None:
        difficulty = select_difficulty(scenario)
    elif difficulty is None:
        difficulty = "standard"  # Default for loaded games
    
    # Select game type (Original or Mystery mode) - only for new games
    selected_narrative = None
    if load_save is None:
        selected_narrative = select_narrative(scenario)  # Returns None for Original, NarrativeConfig for Mystery
    
    # Display intro with pauses
    if intro_only or load_save is None:
        intro_lines = get_intro_lines(200)
        
        # Split intro into sections (scenes)
        # Scene markers are lines with "## SCENE"
        current_section = []
        sections = []
        
        for line in intro_lines:
            if "===" in line and current_section:
                # Start of new scene - save previous and start new
                sections.append(current_section)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Only add final section if it has content beyond just a separator
        if current_section and len([l for l in current_section if l.strip() and "===" not in l]) > 0:
            sections.append(current_section)
        
        # Display each scene
        for i, scene in enumerate(sections):
            # Clear screen at start of EVERY scene (including title)
            typer.clear()
            
            skip_rest = False
            prev_line_blank = False
            for line in scene:
                if skip_rest:
                    # User pressed SPACE - print remaining lines instantly
                    # Check if line has Rich markup
                    if "[/" in line and "[" in line:
                        console.print(line)
                    else:
                        typer.echo(line)
                    continue
                    
                if "===" in line:
                    # Structural element - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip() == "":
                    # Blank line
                    if not prev_line_blank:
                        typer.echo("")
                    prev_line_blank = True
                elif line.strip().startswith("# "):
                    # Title - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip().startswith("## YOUR ROLE"):
                    # Section header - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                else:
                    # All other text (narrative)
                    # Check if line contains Rich markup
                    if "[/" in line and "[" in line:
                        # Has Rich markup - use console.print with brief pause
                        import time
                        console.print(line)
                        time.sleep(0.3)  # Brief pause for readability
                        prev_line_blank = False
                    else:
                        # Plain text - stream it
                        skipped = scroll_text(line, delay=0.02)
                        if skipped:
                            skip_rest = True  # Skip rest of scene
                        prev_line_blank = False
            
            # Pause after each scene
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
        
        typer.echo("")
    
    if intro_only:
        return
    
    rng = Random(seed)
    root = Path(__file__).resolve().parents[1]  # cli/main.py -> project root
    
    # For NEW games, load and display Turn 1 briefing as part of intro sequence
    # This makes the COBRA briefing flow seamlessly from the YOUR ROLE section
    first_briefing_as_intro = (load_save is None)
    
    # Load or create world state
    if load_save:
        save_path = Path(load_save)
        try:
            scenario, world, transcript, loaded_play_mode, loaded_narrative_state = load_game(save_path)
            # Use loaded play_mode if available, otherwise use command-line arg
            if loaded_play_mode:
                play_mode = loaded_play_mode
            typer.echo(f"Loaded game from {save_path}")
            typer.echo(f"Resuming at Turn {world.turn}")
            typer.echo("")
            
            # Use loaded narrative state if available, otherwise create new
            if loaded_narrative_state:
                narrative_state = loaded_narrative_state
            else:
                # Create narrative state from loaded world (legacy saves)
                narrative_state = create_initial_narrative_state(
                    metrics=world.metrics.copy(),
                    play_mode=play_mode,
                    game_time=f"Turn {world.turn}"
                )
                narrative_state.turn = world.turn
            
        except (FileNotFoundError, ValueError) as e:
            typer.echo(f"Error loading save: {e}", err=True)
            raise typer.Exit(1)
    else:
        # New game
        initial_conditions = load_initial_conditions(scenario, root)
        initial_metrics = initial_conditions.get("initial_metrics", {})
        
        world = WorldState(
            turn=1,
            scene=1,
            difficulty=difficulty,
            narrative=selected_narrative,  # Set the secret narrative truth
            metrics=Metrics(
                escalation_risk=initial_metrics.get("escalation_risk", 60),
                domestic_stability=initial_metrics.get("domestic_stability", 50),
                alliance_cohesion=initial_metrics.get("alliance_cohesion", 40),
                casualties_mil=initial_metrics.get("casualties_mil", 2),
                casualties_civ=initial_metrics.get("casualties_civ", 0),
            ),
            flags={},
            posture={},
        )
        
        # Initialize state actor system for multi-agent simulation
        try:
            from models.state_actors import load_actors_from_yaml
            actor_yaml_path = root / "data" / "state_actors.yaml"
            world.actor_system = load_actors_from_yaml(str(actor_yaml_path))
            console.print(f"[{COLORS['success']}]✓ Multi-agent actor system initialized[/{COLORS['success']}]")
        except Exception as e:
            console.print(f"[{COLORS['warning']}]Warning: Could not load actor system: {e}[/{COLORS['warning']}]")
            world.actor_system = None
        
        # Initialize narrative state system
        narrative_state = create_initial_narrative_state(
            metrics=world.metrics.copy(),
            play_mode=play_mode,
            game_time=initial_conditions.get("metadata", {}).get("start_time", "Sunday 5th October 2025, 17:00")
        )
        
        transcript = []
    
    # Load scenario configuration for variant-specific turn files
    scenario_config = get_scenario_config(scenario, variant, root)
    stochastic_from_turn = scenario_config.get("stochastic_from", 7)
    
    # Main game loop
    while True:
        # Refresh colors at start of loop in case theme changed
        COLORS = theme_manager.get_colors()
        
        # Capture metrics at START of turn (before inject effects)
        from copy import deepcopy
        turn_start_metrics = deepcopy(world.metrics)
        
        # Auto-enable stochastic generation when reaching the transition point
        if world.turn >= stochastic_from_turn:
            if not stochastic_injects:
                # First time reaching stochastic content - show transition message
                stochastic_injects = True
                console.print("")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print(f"[{COLORS['primary']} bold]ENTERING DYNAMIC SCENARIO GENERATION[/{COLORS['primary']} bold]")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print("")
                console.print("The scripted scenario has concluded. From this point forward,")
                console.print("events will be dynamically generated based on your decisions.")
                console.print("")
                wait_for_space("Press SPACE to continue...")
                console.print("")
        
        # Determine if we should use stochastic generation for this turn
        use_stochastic = stochastic_injects and world.turn >= stochastic_from_turn
        
        # Get turn filename based on scenario variant
        turn_filename = get_turn_filename(world.turn, scenario_config)
        
        # Briefing phase (with player input function for diplomatic encounters)
        # For Turn 1 of new games: suppress panel display and effect boxes (will be streamed in intro flow)
        is_turn1_intro = (first_briefing_as_intro and world.turn == 1)
        inject, briefing_lines = run_turn_briefing(
            world, 
            scenario, 
            use_stochastic, 
            rng, 
            root, 
            transcript,
            get_player_input=lambda prompt: typer.prompt(prompt).strip(),
            turn_filename=turn_filename,
            silent_effects=is_turn1_intro,  # Hide effect boxes for Turn 1 intro
            suppress_display=is_turn1_intro  # Suppress panel so we can stream the text
        )
        
        # Clear screen and display briefing at top
        # BUT: if this is Turn 1 of a new game, don't clear (flows from intro)
        if not (first_briefing_as_intro and world.turn == 1):
            typer.clear()
        else:
            # First briefing of new game - add separator but don't clear
            typer.echo("")
            typer.echo("=" * 79)
            typer.echo("")
        
        # Split briefing into scene-setting and actual briefing
        # Look for "The National Security Advisor" or similar transition line
        # BUT: for Turn 1 of new games, don't split - show everything in one flow
        scene_setting_end = -1
        if not (first_briefing_as_intro and world.turn == 1):
            for i, line in enumerate(briefing_lines):
                if "National Security Advisor" in line and ("clears" in line or "begins" in line):
                    scene_setting_end = i
                    break
        
        # Display scene-setting part with streaming
        skip_rest = False
        for i, line in enumerate(briefing_lines):
            # Stop at the transition line
            if scene_setting_end > 0 and i >= scene_setting_end:
                break
                
            if skip_rest:
                # User pressed SPACE - print rest instantly
                # Check if line has Rich markup
                if "[/" in line and "[" in line:
                    console.print(line)
                else:
                    typer.echo(line)
                continue
            
            # Scroll the turn number header
            if i == 1 and line.strip().startswith("TURN"):
                skipped = scroll_text(line, delay=0.05)
                if skipped:
                    skip_rest = True
            # Stream narrative text (not structural elements)
            elif line.strip() and not line.strip().startswith("==="):
                # Check if line contains Rich markup
                if "[/" in line and "[" in line:
                    # Has Rich markup - use console.print with brief pause
                    import time
                    console.print(line)
                    time.sleep(0.3)
                else:
                    # Plain text - stream it
                    skipped = scroll_text(line, delay=0.02)
                    if skipped:
                        skip_rest = True
            else:
                typer.echo(line)
        
        # Pause after scene-setting (only if we found a split point)
        if scene_setting_end > 0:
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
            
            # Display rest of briefing (the actual intelligence report)
            typer.echo("")
            for i in range(scene_setting_end, len(briefing_lines)):
                typer.echo(briefing_lines[i])
        
        transcript.extend(briefing_lines)
        
        # Show intelligence briefing (Immersive/Emergent modes only)
        if play_mode in ["immersive", "emergent"] and world.turn > 1:
            from engine.intelligence import generate_intelligence_briefing
            intel_lines = generate_intelligence_briefing(narrative_state, world, rng, detailed=False)
            typer.echo("")
            for line in intel_lines:
                console.print(line)
            typer.echo("")
        
        # Pause before discussion phase
        typer.echo("")
        wait_for_space("Press SPACE to begin discussion phase...")
        
        # After Turn 1 intro briefing is shown, reset the flag
        if first_briefing_as_intro and world.turn == 1:
            first_briefing_as_intro = False
        
        # Clear screen and show discussion phase at top
        typer.clear()
        typer.echo("")  # Buffer line BEFORE Rich output
        
        if RICH_ENABLED:
            console.print(phase_header("DISCUSSION", world.turn))
            typer.echo("")
            typer.echo("  Ask questions or type /decide when ready")
            console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
            typer.echo("")
            console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
            console.print("=" * 79)
            console.print("")
            console.print("Ask advisors questions, or type '/decide' when ready.")
            console.print("Type '/menu' for commands, '/advise' for all advisors, '/resources' for forces.")
        
        typer.echo("")
        
        # Discussion phase loop - DASHBOARD MODE
        from cli.dashboard import WargameDashboard
        from rich.live import Live
        
        dashboard = WargameDashboard(world, console)
        questions = []
        
        with Live(dashboard.layout, console=console, refresh_per_second=2) as live:
            while True:
                # Update dashboard
                dashboard.update()
                
                # Get input (pause live updates)
                live.stop()
                user_input = console.input(f"[{COLORS['primary']}]>[/] ").strip()
                live.start()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["/decide", "decide", "decision"]:
                break
            
            if user_input.lower() in ["/quit", "quit"]:
                typer.echo("Exiting game.")
                raise typer.Exit(0)
            
            if user_input.lower() in ["/save", "save"]:
                save_path = save_game(world, transcript, scenario, f"turn_{world.turn:03d}", root, play_mode, narrative_state)
                typer.echo(f"Game saved to {save_path}")
                continue
            
            if user_input.lower() in ["/theme", "theme"]:
                typer.echo("")
                console.print("Available themes:")
                console.print("  1. Standard (Cyan/Blue)")
                console.print("  2. DEFCON 1 (Red/Alert)")
                console.print("  3. Retro (Green Phosphor)")
                console.print("  4. Slate (Black/White Monochrome)")
                typer.echo("")
                
                theme_choice = typer.prompt("Select theme (1-4)").strip()
                theme_map = {"1": "standard", "2": "defcon1", "3": "retro", "4": "slate"}
                
                if theme_choice in theme_map:
                    theme_name = theme_map[theme_choice]
                    theme_manager.set_theme(theme_name)
                    COLORS = theme_manager.get_colors()
                    console.print(f"[{COLORS['success']}]Theme changed to {theme_name.title()}[/{COLORS['success']}]")
                    # Refresh current view
                    typer.clear()
                    if RICH_ENABLED:
                        console.print(phase_header("DISCUSSION", world.turn))
                        typer.echo("")
                        typer.echo("  Ask questions or type /decide when ready")
                        console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
                        typer.echo("")
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("[bold red]Invalid selection[/bold red]")
                continue

            if user_input.lower() in ["/status", "status"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Display based on play mode
                    if play_mode == "classic":
                        # Show metrics table (includes turn, phase, influence)
                        console.print(metrics_table(world))
                    elif play_mode == "immersive":
                        # Show vibes
                        typer.echo("═" * 60)
                        typer.echo("SITUATION ASSESSMENT")
                        typer.echo("═" * 60)
                        typer.echo("")
                        vibes = narrative_state.get_situation_vibes()
                        for vibe in vibes:
                            typer.echo(vibe.to_string())
                        typer.echo("")
                        
                        # Show character attitudes
                        typer.echo("═" * 60)
                        typer.echo("ADVISOR ATTITUDES")
                        typer.echo("═" * 60)
                        typer.echo("")
                        for char_id, char_attitude in narrative_state.characters.items():
                            trust_level = char_attitude.trust // 20
                            trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                            relationship_symbol = {
                                "allied": "✓",
                                "neutral": "○",
                                "hostile": "✗",
                                "unknown": "?"
                            }.get(char_attitude.relationship, "○")
                            typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
                    elif play_mode == "emergent":
                        # Show narrative summary
                        typer.echo("═" * 60)
                        typer.echo(narrative_state.situation_summary)
                        typer.echo("═" * 60)
                    
                    # Show active flags if any
                    if world.flags:
                        typer.echo("")
                        console.print(f"[{COLORS['warning']} bold]ACTIVE RISK FLAGS:[/{COLORS['warning']} bold]")
                        for flag, value in world.flags.items():
                            if value:
                                console.print(f"  [{COLORS['warning']}]{SYMBOLS['warning']} {flag.replace('_', ' ').title()}[/{COLORS['warning']}]")
                else:
                    # Fallback to plain text
                    typer.echo("=" * 60)
                    typer.echo("CURRENT SITUATION")
                    typer.echo("=" * 60)
                    typer.echo("")
                    typer.echo(f"Turn: {world.turn}")
                    typer.echo(f"Phase: {world.phase}")
                    typer.echo("")
                    typer.echo("Metrics:")
                    typer.echo(f"  Escalation Risk:      {world.metrics.escalation_risk}/100")
                    typer.echo(f"  Domestic Stability:   {world.metrics.domestic_stability}/100")
                    typer.echo(f"  Alliance Cohesion:    {world.metrics.alliance_cohesion}/100")
                    typer.echo(f"  Military Casualties:  {world.metrics.casualties_mil}")
                    typer.echo(f"  Civilian Casualties:  {world.metrics.casualties_civ}")
                    typer.echo("")
                    
                    # Calculate influence
                    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
                    influence = int((influence_raw - 50) / 5)
                    influence = max(-10, min(10, influence))
                    influence_sign = "+" if influence >= 0 else ""
                    typer.echo(f"Public Sentiment (Influence): {influence_sign}{influence}/10")
                    typer.echo("")
                    
                    if world.flags:
                        typer.echo("Active Risk Flags:")
                        for flag, value in world.flags.items():
                            if value:
                                typer.echo(f"  ! {flag.replace('_', ' ').title()}")
                        typer.echo("")
                
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/call "):
                # Handle diplomatic call
                country_input = user_input[6:].strip().upper()
                
                # Map common names to country codes
                country_map = {
                    "US": "US", "USA": "US", "AMERICA": "US", "UNITED STATES": "US",
                    "FRANCE": "France", "FRENCH": "France",
                    "GERMANY": "Germany", "GERMAN": "Germany",
                    "POLAND": "Poland", "POLISH": "Poland",
                    "RUSSIA": "Russia", "RUSSIAN": "Russia",
                    "UKRAINE": "Ukraine", "UKRAINIAN": "Ukraine",
                    "IRELAND": "Ireland", "IRISH": "Ireland"
                }
                
                country = country_map.get(country_input, country_input.capitalize())
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]Connecting to {country}...[/{COLORS['success']} bold]")
                
                # Run diplomatic encounter (with real-time printing)
                encounter_transcript, cohesion_delta = run_diplomatic_encounter(
                    world,
                    country,
                    required=False,
                    context=None,
                    llm_generate=generate_text,
                    rng=rng,
                    root_path=root,
                    full_transcript=transcript,
                    get_player_input=lambda prompt: typer.prompt(prompt).strip(),
                    print_fn=typer.echo  # Print in real-time
                )
                
                # Transcript already printed, just save it
                transcript.extend(encounter_transcript)
                
                # Apply alliance cohesion change
                from engine.utils import clamp, clamp_metrics
                from engine.flags import update_world_flags
                
                world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion + cohesion_delta)
                clamp_metrics(world.metrics)
                update_world_flags(world)
                
                continue
            
            if user_input.lower() in ["/advise", "advise"]:
                # Get advice from all advisors
                typer.echo("")
                
                if RICH_ENABLED:
                    # Top border
                    box = BOX["round"]
                    title = " COBRA ADVISORY PANEL "
                    title_len = len(title)
                    left_pad = (WIDTH - title_len - 2) // 2
                    right_pad = WIDTH - title_len - left_pad - 2
                    console.print(f"[{COLORS['accent']} bold]{box['tl']}{box['h'] * left_pad}{title}{box['h'] * right_pad}{box['tr']}[/{COLORS['accent']} bold]")
                    typer.echo("")
                else:
                    typer.echo("=" * 79)
                    typer.echo("COBRA ADVISORY PANEL")
                    typer.echo("=" * 79)
                    typer.echo("")
                
                typer.echo("Requesting input from all advisors on the current situation...")
                typer.echo("")
                
                # Ask each advisor for their assessment
                # Add conciseness instruction to keep responses brief
                advisors = [
                    ("National Security Advisor", "NSA, what's your assessment of the current situation and recommended course of action? [Please be concise - 3-4 sentences maximum]"),
                    ("Chief of the Defence Staff", "CDS, what are our military options and constraints? [Please be concise - 3-4 sentences maximum]"),
                    ("Foreign Secretary", "Foreign Secretary, what's the diplomatic landscape and alliance status? [Please be concise - 3-4 sentences maximum]"),
                    ("Home Secretary", "Home Secretary, what are the domestic security concerns? [Please be concise - 3-4 sentences maximum]"),
                    ("Attorney General", "Attorney General, what are the legal constraints and considerations? [Please be concise - 3-4 sentences maximum]")
                ]
                
                for advisor_name, question in advisors:
                    # Separator between advisors
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                    else:
                        typer.echo("─" * 79)
                    
                    console.print(f"  [{COLORS['secondary']} bold]{advisor_name.upper()}[/{COLORS['secondary']} bold]")
                    typer.echo("")
                    
                    # Get response from this advisor
                    discussion_lines = run_turn_discussion(world, scenario, [question], rng, root, transcript)
                    for line in discussion_lines:
                        # Skip the "Prime Minister:" echo and strip the conciseness instruction
                        if not line.startswith("Prime Minister:"):
                            # Remove the [Please be concise...] instruction from display
                            display_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            if display_line:  # Only display non-empty lines
                                # Format response with structure
                                if ":" in display_line:
                                    advisor_role, rest = display_line.split(":", 1)
                                    if RICH_ENABLED:
                                        formatted = format_advisor_response("", rest)
                                        console.print(formatted)
                                    else:
                                        console.print(f"[{COLORS['secondary']} bold]{advisor_role}:[/{COLORS['secondary']} bold]", end="")
                                        console.print(rest)
                                else:
                                    typer.echo(display_line)
                        else:
                            # For transcript, clean up the question
                            clean_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            transcript.append(clean_line)
                            continue
                    # Only add non-question lines to transcript (questions already added above)
                    transcript.extend([l for l in discussion_lines if not l.startswith("Prime Minister:")])
                    typer.echo("")
                
                if RICH_ENABLED:
                    # Bottom border
                    console.print(f"[{COLORS['accent']} bold]{box['bl']}{box['h'] * (WIDTH - 2)}{box['br']}[/{COLORS['accent']} bold]")
                else:
                    typer.echo("=" * 79)
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/resources", "resources"]:
                # Display UK forces and stockpiles
                initial_conditions = load_initial_conditions(scenario, root)
                
                typer.echo("")
                
                if RICH_ENABLED:
                    forces_table, stockpiles_table = resources_tables(initial_conditions)
                    console.print(forces_table)
                    typer.echo("")
                    console.print(stockpiles_table)
                    typer.echo("")
                    continue
                
                # Fallback to plain text
                typer.echo("=" * 79)
                typer.echo("UK MILITARY RESOURCES")
                typer.echo("=" * 79)
                typer.echo("")
                
                # Display stockpiles
                stockpiles = initial_conditions.get("stockpiles", {})
                if stockpiles:
                    typer.echo("AMMUNITION STOCKPILES:")
                    typer.echo("")
                    
                    # Air Defence
                    air_defence = stockpiles.get("air_defence_missiles", {})
                    if air_defence:
                        typer.echo("  Air Defence:")
                        for weapon, data in air_defence.items():
                            count = data.get("count", 0)
                            note = data.get("note", "")
                            typer.echo(f"    • {weapon.replace('_', ' ').title()}: {count}")
                            if note:
                                typer.echo(f"      {note}")
                        typer.echo("")
                    
                    # Naval Strike
                    typer.echo("  Naval Strike:")
                    tomahawk = stockpiles.get("tomahawk_cruise_missiles", {})
                    if tomahawk:
                        typer.echo(f"    • Tomahawk Cruise Missiles: {tomahawk.get('count', 0)}")
                        typer.echo(f"      {tomahawk.get('note', '')}")
                    harpoon = stockpiles.get("harpoon_anti_ship", {})
                    if harpoon:
                        typer.echo(f"    • Harpoon Anti-Ship: {harpoon.get('count', 0)}")
                        typer.echo(f"      {harpoon.get('note', '')}")
                    typer.echo("")
                    
                    # Air-Launched
                    typer.echo("  Air-Launched Precision:")
                    storm_shadow = stockpiles.get("storm_shadow_cruise_missiles", {})
                    if storm_shadow:
                        typer.echo(f"    • Storm Shadow: {storm_shadow.get('count', 0)}")
                        typer.echo(f"      {storm_shadow.get('note', '')}")
                    paveway = stockpiles.get("paveway_laser_guided_bombs", {})
                    if paveway:
                        typer.echo(f"    • Paveway LGBs: {paveway.get('count', 0)}")
                        typer.echo(f"      {paveway.get('note', '')}")
                    typer.echo("")
                    
                    # Anti-Submarine
                    typer.echo("  Anti-Submarine:")
                    spearfish = stockpiles.get("spearfish_torpedoes", {})
                    if spearfish:
                        typer.echo(f"    • Spearfish Torpedoes: {spearfish.get('count', 0)}")
                        typer.echo(f"      {spearfish.get('note', '')}")
                    stingray = stockpiles.get("stingray_lightweight_torpedoes", {})
                    if stingray:
                        typer.echo(f"    • Stingray Torpedoes: {stingray.get('count', 0)}")
                        typer.echo(f"      {stingray.get('note', '')}")
                    typer.echo("")
                
                # Display forces
                uk_forces = initial_conditions.get("uk_forces", {})
                if uk_forces:
                    naval = uk_forces.get("naval", [])
                    if naval:
                        typer.echo("NAVAL FORCES:")
                        typer.echo("")
                        for unit in naval:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            typer.echo(f"  • {unit_id} ({unit_type})")
                            typer.echo(f"    Location: {location}")
                            typer.echo(f"    Status: {status}")
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            typer.echo("")
                    
                    air = uk_forces.get("air", [])
                    if air:
                        typer.echo("AIR FORCES:")
                        typer.echo("")
                        for unit in air:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            
                            # Display unit header
                            typer.echo(f"  • {unit_id}")
                            
                            # Show type and role
                            if unit_type:
                                role = unit.get("role", "")
                                if role:
                                    typer.echo(f"    Type: {unit_type} ({role})")
                                else:
                                    typer.echo(f"    Type: {unit_type}")
                            
                            # Show location if present
                            if location:
                                typer.echo(f"    Location: {location}")
                            
                            # Show aircraft counts if present
                            aircraft_count = unit.get("aircraft_count")
                            operational_aircraft = unit.get("operational_aircraft")
                            if aircraft_count is not None:
                                if operational_aircraft is not None:
                                    typer.echo(f"    Aircraft: {operational_aircraft}/{aircraft_count} operational")
                                else:
                                    typer.echo(f"    Aircraft: {aircraft_count}")
                            
                            # Show status
                            typer.echo(f"    Status: {status}")
                            
                            # Show note if present
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            
                            typer.echo("")
                
                typer.echo("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/intel"):
                # Intelligence command - detailed actor assessment
                typer.echo("")
                
                # Parse command: /intel or /intel <country_code>
                parts = user_input.lower().split()
                if len(parts) == 1:
                    # Show available actors
                    if world.actor_system:
                        typer.echo("Available countries for intelligence assessment:")
                        typer.echo("")
                        for code, actor in world.actor_system.actors.items():
                            typer.echo(f"  /intel {code.lower()} - {actor.full_name}")
                        typer.echo("")
                    else:
                        typer.echo("Intelligence system not available.")
                else:
                    # Show detailed assessment for specific actor
                    country_code = parts[1].upper()
                    if world.actor_system:
                        from engine.intelligence import generate_actor_detailed_assessment
                        intel_lines = generate_actor_detailed_assessment(country_code, world, world.turn)
                        for line in intel_lines:
                            console.print(line)
                    else:
                        typer.echo("Intelligence system not available.")
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/llm", "llm", "/settings", "settings"]:
                # Open LLM model settings menu
                typer.echo("")
                typer.echo("Opening LLM Model Settings...")
                typer.echo("")
                model_settings_menu()
                # After returning from settings, clear and redisplay the discussion phase
                typer.clear()
                typer.echo("")
                if RICH_ENABLED:
                    console.print(phase_header("DISCUSSION", world.turn))
                    typer.echo("")
                    typer.echo("  Ask questions or type /decide when ready")
                    console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /intel  /llm[/{COLORS['muted']}]")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("=" * 79)
                    console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
                    console.print("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower() in ["/menu", "menu", "/help", "help"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Show advisor panel
                    console.print(advisor_menu_panel())
                    typer.echo("")
                    
                    # Show diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    console.print(diplomatic_contacts_table(available_contacts))
                    typer.echo("")
                    
                    # Show metrics guide
                    console.print(metrics_guide_panel())
                    typer.echo("")
                    
                    # Show commands
                    console.print(command_menu())
                    typer.echo("")
                    
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                else:
                    # Fallback to plain text
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]AVAILABLE ADVISORS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• National Security Advisor (NSA)")
                    typer.echo("  - Intelligence assessment, strategic planning, threat analysis")
                    typer.echo("  - Example: 'NSA, what's your assessment of Russian intentions?'")
                    typer.echo("")
                    typer.echo("• Chief of the Defence Staff (CDS)")
                    typer.echo("  - Military operations, force readiness, deployment options")
                    typer.echo("  - Example: 'CDS, what are our air defence capabilities?'")
                    typer.echo("")
                    typer.echo("• Foreign Secretary")
                    typer.echo("  - Diplomacy, alliance management, NATO coordination")
                    typer.echo("  - Example: 'Foreign Secretary, can we count on US support?'")
                    typer.echo("")
                    typer.echo("• Home Secretary")
                    typer.echo("  - Domestic security, civil protection, public messaging")
                    typer.echo("  - Example: 'Home Secretary, how do we reassure the public?'")
                    typer.echo("")
                    typer.echo("• Attorney General")
                    typer.echo("  - Legal framework, international law, rules of engagement")
                    typer.echo("  - Example: 'Attorney General, what are our legal constraints?'")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['success']} bold]DIPLOMATIC CONTACTS[/{COLORS['success']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    
                    # List available diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    if available_contacts:
                        for country, access_level, title in available_contacts:
                            if access_level == "leader":
                                console.print(f"[{COLORS['warning']} bold]  * LEADER[/{COLORS['warning']} bold] - {country}: {title}")
                            else:
                                console.print(f"  • Diplomat - {country}: {title}")
                            console.print(f"    Command: /call {country.lower()}")
                            typer.echo("")
                    else:
                        typer.echo("  No diplomatic contacts available (Alliance Cohesion too low)")
                        typer.echo("")
                    
                    console.print("=" * 60)
                    console.print(f"[{COLORS['warning']} bold]METRICS GUIDE[/{COLORS['warning']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• Escalation Risk (0-100)")
                    typer.echo("  Likelihood of conflict escalating to full-scale war")
                    typer.echo("  HIGH = Danger of Russian attack or nuclear exchange")
                    typer.echo("")
                    typer.echo("• Domestic Stability (0-100)")
                    typer.echo("  Public confidence, economic stability, infrastructure security")
                    typer.echo("  LOW = Civil unrest, panic, political pressure")
                    typer.echo("")
                    typer.echo("• Alliance Cohesion (0-100)")
                    typer.echo("  Strength of NATO solidarity and allied support")
                    typer.echo("  HIGH = Access to leaders, Article 5 support likely")
                    typer.echo("  LOW = Isolated, limited diplomatic access")
                    typer.echo("")
                    typer.echo("• Influence (-10 to +10)")
                    typer.echo("  Your political capital and public sentiment")
                    typer.echo("  Derived from: (Stability + Cohesion) / 2")
                    typer.echo("  Currently: Informational only (future: affects options)")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]COMMANDS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    console.print("")
                    console.print(f"[{COLORS['primary']}]  /menu or /help[/{COLORS['primary']}]     - Show this menu")
                    console.print(f"[{COLORS['primary']}]  /status[/{COLORS['primary']}]            - Show current metrics and situation")
                    console.print(f"[{COLORS['primary']}]  /advise[/{COLORS['primary']}]            - Get input from all advisors at once")
                    console.print(f"[{COLORS['primary']}]  /resources[/{COLORS['primary']}]         - Show UK forces and ammunition stockpiles")
                    console.print(f"[{COLORS['primary']}]  /call <country>[/{COLORS['primary']}]    - Contact a foreign leader or diplomat")
                    console.print(f"[{COLORS['primary']}]  /decide[/{COLORS['primary']}]            - Make your decision")
                    console.print(f"[{COLORS['primary']}]  /theme[/{COLORS['primary']}]             - Change UI theme")
                    console.print(f"[{COLORS['primary']}]  /save[/{COLORS['primary']}]              - Save game and continue")
                    console.print(f"[{COLORS['primary']}]  /quit[/{COLORS['primary']}]              - Exit game")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                
                typer.echo("")
                continue
            
            # Handle question
            questions.append(user_input)
            dashboard.add_message("PM", user_input)
            
            discussion_lines = run_turn_discussion(world, scenario, [user_input], rng, root, transcript)
            
            typer.echo("")  # Space before response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                typer.echo("")
            
            for line in discussion_lines:
                # Skip echoing the player's question (they just typed it)
                if not line.startswith("Prime Minister:"):
                    if ":" in line:
                        advisor_name, rest = line.split(":", 1)
                        
                        # Print advisor name
                        console.print(f"  [{COLORS['secondary']} bold]{advisor_name}[/{COLORS['secondary']} bold]")
                        typer.echo("")
                        
                        # Format response with structure
                        if RICH_ENABLED:
                            formatted = format_advisor_response("", rest)
                            console.print(formatted)
                        else:
                            typer.echo(rest)
                    else:
                        typer.echo(line)
            
            transcript.extend(discussion_lines)
            
            typer.echo("")  # Space after response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
            
            typer.echo("")
        
        # Decision phase loop - allows returning to discussion if decision is cancelled
        decision_confirmed = False
        while not decision_confirmed:
            # Decision phase - clear screen and start at top
            typer.clear()
            typer.echo("")  # Buffer line
            
            if RICH_ENABLED:
                console.print(phase_header("DECISION", world.turn))
                typer.echo("")
                typer.echo("  Enter your decision (or 'cancel' to return to discussion)")
            else:
                console.print("=" * 79)
                console.print(f"[{COLORS['emphasis']} bold]TURN {world.turn}: DECISION PHASE[/{COLORS['emphasis']} bold]")
                console.print("=" * 79)
                console.print("")
                console.print("Enter your decision (or 'cancel' to return to discussion):")
            
            typer.echo("")
            
            action = typer.prompt("Decision>").strip()
            
            if action.lower() == "cancel":
                # Return to discussion phase
                break
            
            if not action:
                typer.echo("No action entered. Returning to discussion.")
                typer.echo("")
                wait_for_space("Press SPACE to return to discussion...")
                break
            
            # Interpret and get pushback
            interpretation, pushback, critical_concerns, decision_lines = run_turn_decision(world, scenario, action, rng, root, transcript)
            transcript.extend(decision_lines)
            
            # Display decision with improved UX
            display_decision_summary(action, interpretation, show_details=False)
            
            # Option to see full details
            see_details = typer.prompt("", default="").strip().lower()
            if see_details == "details":
                display_decision_summary(action, interpretation, show_details=True)
                console.print("")
            
            # Handle critical omissions with selective addressing
            if critical_concerns:
                action_code, selected_indices = display_critical_concerns_with_selection(critical_concerns)
                
                if action_code == 'D':
                    # Return to discussion
                    typer.echo("")
                    typer.echo("Returning to discussion phase.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break
                
                elif action_code == 'M':
                    # Modify manually
                    typer.echo("")
                    typer.echo("Decision cancelled. Please enter a modified decision.")
                    typer.echo("")
                    continue
                
                elif action_code in ['A', 'S'] and selected_indices:
                    # Apply selected recommendations
                    console.print("")
                    console.print(f"[{COLORS['success']}]Applying {len(selected_indices)} recommendation(s)...[/{COLORS['success']}]")
                    console.print("")
                    
                    # Append recommendations
                    enhanced_decision = append_recommendations_to_decision(action, critical_concerns, selected_indices)
                    
                    # Show enhanced decision
                    from rich.panel import Panel
                    console.print(Panel(f"[italic]{enhanced_decision}[/italic]", title="[bold]ENHANCED DECISION[/bold]", border_style="white"))
                    console.print("")
                    
                    # Confirm
                    confirm = typer.confirm("Proceed with enhanced decision?", default=True)
                    
                    if not confirm:
                        console.print("")
                        console.print("Decision cancelled.")
                        console.print("")
                        continue
                    
                    # Update action for adjudication
                    action = enhanced_decision
                    
                    # Re-interpret
                    console.print("")
                    console.print("Re-interpreting enhanced decision...")
                    console.print("")
                    
                    interpretation, pushback, critical_concerns_2, decision_lines_2 = run_turn_decision(world, scenario, action, rng, root, transcript)
                    transcript.extend(decision_lines_2)
                    
                    # Display new interpretation
                    display_decision_summary(action, interpretation, show_details=False)
                    
                    # If STILL have concerns, warn
                    if critical_concerns_2:
                        console.print("")
                        console.print(f"[{COLORS['warning']}]⚠ Warning: Critical concerns remain.[/{COLORS['warning']}]")
                        console.print("")
                        # Let player proceed or go back
                        cont = typer.confirm("Proceed anyway?", default=False)
                        if not cont:
                            continue
                    
                    decision_confirmed = True
                
                else:  # 'I' - Ignore
                    typer.echo("")
                    typer.echo(f"[{COLORS['warning']}]Proceeding despite all concerns...[/{COLORS['warning']}]")
                    typer.echo("")
                    decision_confirmed = True
            
            # Confirm decision (regular pushback, if any)
            elif pushback:
                typer.echo("")
                confirm = typer.confirm("Proceed with this decision despite concerns?", default=True)
                if not confirm:
                    typer.echo("")
                    typer.echo("Decision cancelled. Returning to discussion.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break  # Break inner loop, return to discussion
                else:
                    decision_confirmed = True  # Proceed to adjudication
            else:
                decision_confirmed = True  # No pushback, proceed to adjudication
        
        # If decision was cancelled, go back to discussion phase
        if not decision_confirmed:
            continue
        
        # Adjudication phase - clear screen and start at top
        typer.clear()
        typer.echo("")  # Buffer line
        
        if RICH_ENABLED:
            console.print(phase_header("ADJUDICATION", world.turn))
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['success']} bold]TURN {world.turn}: ADJUDICATION[/{COLORS['success']} bold]")
            console.print("=" * 79)
        
        typer.echo("")  # Buffer line
        
        # Run LLM-driven adjudication with narrative quality assessment
        try:
            actor_responses = []
            
            if world.actor_system:
                # Use multi-agent simulation
                from engine.narrative_adjudication import adjudicate_with_actor_simulation
                
                final_effects, actor_responses, character_responses, reasoning = adjudicate_with_actor_simulation(
                    narrative_state,
                    world.actor_system,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            else:
                # Use standard narrative adjudication
                final_effects, character_responses, reasoning = adjudicate_with_narrative(
                    narrative_state,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            
            # Display quality reasoning
            typer.echo("")
            if RICH_ENABLED:
                console.print(Panel(format_markdown(reasoning), title=f"[{COLORS['accent']} bold]ACTION ASSESSMENT[/]", border_style=COLORS['accent']))
            else:
                typer.echo("=" * 60)
                typer.echo("ACTION ASSESSMENT")
                typer.echo("=" * 60)
                typer.echo("")
                typer.echo(reasoning)
            typer.echo("")
            
            # Display effects
            if RICH_ENABLED:
                console.print(f"[{COLORS['accent']} bold]EFFECTS[/]")
                console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
            else:
                typer.echo("=" * 60)
                typer.echo("EFFECTS")
                typer.echo("=" * 60)
            typer.echo("")
            
            for metric, delta in final_effects.items():
                if RICH_ENABLED:
                    color = COLORS['success'] if delta > 0 else COLORS['danger'] if delta < 0 else COLORS['muted']
                    console.print(f"  [{color}]{metric}: {delta:+d}[/{color}]")
                else:
                    typer.echo(f"  {metric}: {delta:+d}")
            typer.echo("")
            
            # Display character responses
            if character_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]ADVISOR REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("ADVISOR REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for char_name, response in character_responses:
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['secondary']} bold]{char_name}:[/{COLORS['secondary']} bold]")
                        console.print(f"  \"{response}\"")
                    else:
                        typer.echo(f"{char_name}:")
                        typer.echo(f"  \"{response}\"")
                    typer.echo("")
            
            # Display international reactions (multi-agent simulation)
            if actor_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]INTERNATIONAL REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("INTERNATIONAL REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for response in actor_responses:
                    trust_delta = response.trust_change
                    actor_id = response.actor_id
                    
                    # Get full name if available
                    actor_name = actor_id
                    if world.actor_system:
                        actor = world.actor_system.get_actor(actor_id)
                        if actor:
                            actor_name = actor.full_name
                    
                    if RICH_ENABLED:
                        color = COLORS['success'] if trust_delta > 0 else COLORS['danger'] if trust_delta < 0 else COLORS['muted']
                        console.print(f"[{COLORS['primary']} bold]{actor_name}:[/{COLORS['primary']} bold] [{color}]({trust_delta:+d})[/{color}]")
                        console.print(f"  \"{response.public_response}\"")
                    else:
                        typer.echo(f"{actor_name}: ({trust_delta:+d})")
                        typer.echo(f"  \"{response.public_response}\"")
                    typer.echo("")
            
            # Sync world metrics with narrative state (keep both in sync)
            world.metrics.escalation_risk = narrative_state.hidden_metrics.escalation_risk
            world.metrics.domestic_stability = narrative_state.hidden_metrics.domestic_stability
            world.metrics.alliance_cohesion = narrative_state.hidden_metrics.alliance_cohesion
            world.metrics.casualties_mil = narrative_state.hidden_metrics.casualties_mil
            world.metrics.casualties_civ = narrative_state.hidden_metrics.casualties_civ
            
            # Build transcript for save file
            adjudication_lines = [
                "Action Assessment:",
                reasoning,
                "",
                "Effects:"
            ]
            for metric, delta in final_effects.items():
                adjudication_lines.append(f"  {metric}: {delta:+d}")
            adjudication_lines.append("")
            
            if character_responses:
                adjudication_lines.append("Advisor Reactions:")
                for char_name, response in character_responses:
                    adjudication_lines.append(f"{char_name}: \"{response}\"")
                adjudication_lines.append("")
                
            if actor_responses:
                adjudication_lines.append("International Reactions:")
                for response in actor_responses:
                    adjudication_lines.append(f"{response.actor_id}: \"{response.public_response}\"")
                adjudication_lines.append("")
            
            transcript.extend(adjudication_lines)
        
        except Exception as e:
            # Fallback to primitive system on error
            if RICH_ENABLED:
                console.print(f"[{COLORS['warning']}][WARNING] LLM adjudication failed: {e}[/{COLORS['warning']}]")
                console.print(f"[{COLORS['warning']}][INFO] Falling back to keyword-based adjudication[/{COLORS['warning']}]")
            else:
                typer.echo(f"[WARNING] LLM adjudication failed: {e}")
                typer.echo("[INFO] Falling back to keyword-based adjudication")
            typer.echo("")
            
            adjudication_lines = run_turn_adjudication_fallback(world, action, interpretation, rng)
            for line in adjudication_lines:
                typer.echo(line)
            transcript.extend(adjudication_lines)
            
            # Sync narrative state from world (reverse sync in fallback mode)
            narrative_state.update_hidden_metrics({
                "escalation_risk": world.metrics.escalation_risk,
                "domestic_stability": world.metrics.domestic_stability,
                "alliance_cohesion": world.metrics.alliance_cohesion,
                "casualties_mil": world.metrics.casualties_mil,
                "casualties_civ": world.metrics.casualties_civ
            })
        
        # Narrative state turn already updated by adjudicate_with_narrative()
        narrative_state.turn = world.turn
        
        # Display based on play mode
        typer.echo("")
        if play_mode == "classic":
            # Classic mode: Show raw metrics with deltas
            if RICH_ENABLED:
                console.print(metrics_table(world, show_deltas=True, previous_metrics=turn_start_metrics))
                typer.echo("")  # Buffer after table
        elif play_mode == "immersive":
            # Immersive mode: Show vibes + character attitudes
            typer.echo("═" * 60)
            typer.echo("SITUATION ASSESSMENT")
            typer.echo("═" * 60)
            typer.echo("")
            
            vibes = narrative_state.get_situation_vibes()
            for vibe in vibes:
                typer.echo(vibe.to_string())
            
            typer.echo("")
            typer.echo("═" * 60)
            typer.echo("ADVISOR ATTITUDES")
            typer.echo("═" * 60)
            typer.echo("")
            
            for char_id, char_attitude in narrative_state.characters.items():
                # Create visual trust bar
                trust_level = char_attitude.trust // 20  # 0-5 scale
                trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                relationship_symbol = {
                    "allied": "✓",
                    "neutral": "○",
                    "hostile": "✗",
                    "unknown": "?"
                }.get(char_attitude.relationship, "○")
                
                typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
            
            typer.echo("")
        elif play_mode == "emergent":
            # Emergent mode: Narrative summary only
            typer.echo("═" * 60)
            typer.echo(narrative_state.situation_summary)
            typer.echo("═" * 60)
            typer.echo("")
        
        # Auto-save after each turn
        save_path = save_game(world, transcript, scenario, "autosave", root, play_mode, narrative_state)
        
        # Advance turn
        world.turn += 1
        world.scene = world.turn  # Keep scene in sync for legacy compatibility
        world.discussion_transcript = []
        
        typer.echo("")
        typer.echo("=" * 60)
        typer.echo(f"Turn {world.turn - 1} complete. Auto-saved to {save_path.name}")
        typer.echo("=" * 60)
        typer.echo("")
        
        # Continue to next turn with spacebar
        try:
            wait_for_space("Press SPACE to continue to next turn (or Ctrl+C to exit)...")
        except KeyboardInterrupt:
            typer.echo("\nGame paused. Use --load to resume.")
            break


@app.command(rich_help_panel="GAMEPLAY")
def batch(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed"),
    action: str = typer.Option("Deploy defensive forces", help="Action to take"),
):
    """Run a single turn in batch mode (for testing)."""
    
    transcript = run_single_scene(scenario, seed, "llm")
    for line in transcript:
        typer.echo(line)


@app.command(rich_help_panel="UTILITY")
def settings():
    """Configure LLM model settings (Flash vs Pro per system)."""
    console.print("\n[bold cyan]LLM Model Settings[/bold cyan]\n")
    console.print("Configure which systems use Flash (fast/cheap) vs Pro (sophisticated/expensive)\n")
    
    model_settings_menu()


@app.command(rich_help_panel="UTILITY")
def intro():
    """Display the intro text."""
    for line in get_intro_lines(200):
        typer.echo(line)


if __name__ == "__main__":
    app()

```

```python
"""Interactive CLI for the wargame with two-phase turn structure.

Supports:
- Interactive mode: discussion → decision → adjudication
- Batch mode: run with pre-defined action
- Save/load game state
- Stochastic inject generation
"""

import typer
from pathlib import Path
from random import Random
from typing import Optional
import sys
import os

# CRITICAL: Import msvcrt FIRST on Windows (before Rich)
if sys.platform == "win32":
    import msvcrt

# Allow running this file directly
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# THEN import Rich (after msvcrt is loaded)
from cli.rich_ui import (
    console, phase_header, metrics_table,
    advisor_menu_panel, diplomatic_contacts_table,
    resources_tables, command_menu, metrics_guide_panel,
    format_markdown, RICH_ENABLED
)
from cli.theme import theme_manager, COLORS, SYMBOLS, BOX, WIDTH
from cli.formatters import format_advisor_response
from models.world import WorldState, Metrics
from models.narrative_state import NarrativeState, create_initial_narrative_state, PlayMode
from models.narrative import NarrativeConfig
from engine.scenario_loader import list_available_scenarios, get_scenario_config, get_turn_filename, load_narrative_configs
from engine.sim_loop import (
    run_turn_briefing,
    run_turn_discussion,
    run_turn_decision,
    run_turn_adjudication as run_turn_adjudication_fallback,  # Renamed for fallback
    run_single_scene
)
from engine.narrative_adjudication import adjudicate_with_narrative
from engine.intro import get_intro_lines
from engine.persistence import save_game, load_game
from engine.initial_conditions import load_initial_conditions
from engine.diplomacy import run_diplomatic_encounter, list_available_diplomatic_contacts
from llm.router import generate_text
from cli.model_settings_menu import model_settings_menu

# Task 2.5: Enable Rich help panel
app = typer.Typer(
    rich_markup_mode="rich", 
    help="FALSE FLAG: THE WARGAME - LLM-driven crisis simulation",
    no_args_is_help=True
)


def scroll_text(text: str, delay: float = 0.03, allow_skip: bool = True) -> bool:
    """Print text character by character with optional skip.
    
    Args:
        text: Text to scroll
        delay: Delay between characters (seconds)
        allow_skip: If True, pressing SPACE skips to end of scene
        
    Returns:
        True if user pressed SPACE to skip, False otherwise
    """
    import msvcrt
    import sys
    
    for i, char in enumerate(text):
        # Check if user pressed SPACE to skip rest of scene
        if allow_skip and msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                # Print rest of line and return skip signal
                sys.stdout.write(text[i:])
                sys.stdout.flush()
                print()
                return True  # Signal to skip rest of scene
            # Ignore other keys, continue scrolling
        
        sys.stdout.write(char)
        sys.stdout.flush()
        
        # Slightly longer pause after punctuation
        if char in '.!?':
            import time
            time.sleep(delay * 3)
        elif char in ',;:':
            import time
            time.sleep(delay * 2)
        else:
            import time
            time.sleep(delay)
    
    print()  # Newline at end
    return False  # No skip


def wait_for_space(prompt: str = "Press SPACE to continue...") -> None:
    """Wait for user to press spacebar to continue."""
    import msvcrt  # Windows-specific
    typer.echo("")
    typer.echo(prompt)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':  # Spacebar
                typer.echo("")
                break


def parse_interpretation_simple(interpretation: str) -> dict:
    """Parse LLM interpretation into key sections for display.
    
    Args:
        interpretation: Full interpretation text
    
    Returns:
        Dict with parsed sections
    """
    sections = {
        "summary": "",
        "forces": [],
        "timeline": "",
        "concerns": ""
    }
    
    lines = interpretation.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("INTERPRETATION:"):
            sections["summary"] = line.replace("INTERPRETATION:", "").strip()
        elif line.startswith("FORCES INVOLVED:"):
            current_section = "forces"
        elif line.startswith("TIMELINE:"):
            current_section = "timeline"
        elif line.startswith("FEASIBILITY:"):
            if "impossible" in line.lower() or "requires clarification" in line.lower():
                sections["concerns"] = line.replace("FEASIBILITY:", "").strip()
            current_section = None
        elif current_section == "forces" and line and line.startswith("*"):
            # Extract force name from bullet point
            force = line.lstrip("* ").split(":")[0] if ":" in line else line.lstrip("* ")
            if force and len(sections["forces"]) < 5:  # Max 5 forces shown
                sections["forces"].append(force)
        elif current_section == "timeline" and line:
            sections["timeline"] = line
    
    return sections


def display_decision_summary(action: str, interpretation: str, show_details: bool = False):
    """Display decision interpretation in player-friendly format.
    
    Args:
        action: Player's original decision text
        interpretation: Full LLM interpretation
        show_details: If True, show full interpretation
    """
    COLORS = theme_manager.get_colors()
    
    # Show player's exact words in a box
    console.print("")
    from rich.panel import Panel
    console.print(Panel(f"[italic]{action}[/italic]", title="[bold]YOUR DECISION[/bold]", border_style="white"))
    console.print("")
    
    if show_details:
        # Show full interpretation
        console.print(Panel(format_markdown(interpretation), title="[bold]FULL INTERPRETATION (DETAILED)[/bold]", border_style="blue"))
        console.print("")
    else:
        # Show simplified summary
        parsed = parse_interpretation_simple(interpretation)
        
        # Build content for panel
        content = []
        
        # Show summary if we extracted one
        if parsed["summary"]:
            content.append(parsed["summary"])
            content.append("")
        
        # Show key forces
        if parsed["forces"]:
            content.append(f"[{COLORS['success']}]Forces Deployed:[/{COLORS['success']}]")
            for force in parsed["forces"]:
                content.append(f"  • {force}")
            content.append("")
        
        # Show timeline
        if parsed["timeline"]:
            content.append(f"[{COLORS['accent']}]Estimated Timeline:[/{COLORS['accent']}] {parsed['timeline']}")
            content.append("")
        
        # Show concerns
        if parsed["concerns"]:
            content.append(f"[{COLORS['warning']}]⚠ Operational Concerns: {parsed['concerns']}[/{COLORS['warning']}]")
            content.append("")
        
        content.append(f"[{COLORS['muted']}](Type 'details' to see full interpretation)[/{COLORS['muted']}]")
        
        console.print(Panel("\n".join(content), title="[bold]📋 OPERATIONAL ORDER[/bold]", border_style="cyan"))


def display_critical_concerns_with_selection(critical_concerns: list) -> tuple:
    """Display critical concerns and let player select which to address.
    
    Args:
        critical_concerns: List of (role, concern, recommendation) tuples
    
    Returns:
        Tuple of (action_code, selected_indices)
        action_code: 'A' (all), 'S' (select), 'M' (modify), 'I' (ignore), 'D' (discussion)
        selected_indices: List of 0-based indices of selected concerns
    """
    from rich.panel import Panel
    COLORS = theme_manager.get_colors()
    
    console.print("")
    console.print(Panel(f"Advisors have raised {len(critical_concerns)} critical concerns regarding your decision.", 
                        title=f"[{COLORS['warning']} bold]⚠️ CRITICAL ADVISORIES[/]", 
                        border_style=COLORS['warning']))
    console.print("")
    
    # Display each concern with number
    for idx, (role, concern, recommendation) in enumerate(critical_concerns, 1):
        console.print(f"[{COLORS['warning']} bold][{idx}] {role}[/{COLORS['warning']} bold]")
        console.print(f"  {concern}")
        console.print(f"  [{COLORS['primary']}]→ RECOMMENDATION: \"{recommendation}\"[/{COLORS['primary']}]")
        console.print("")
        console.print(f"[{COLORS['muted']}]" + "─" * 40 + f"[/{COLORS['muted']}]")
        console.print("")
    
    # Get selection
    console.print("Which concerns would you like to address?")
    console.print("")
    console.print(f"  [{COLORS['primary']}]A[/{COLORS['primary']}] - Apply ALL recommendations to my decision")
    console.print(f"  [{COLORS['primary']}]S[/{COLORS['primary']}] - Select specific recommendations")
    console.print(f"  [{COLORS['primary']}]M[/{COLORS['primary']}] - Modify decision manually instead")
    console.print(f"  [{COLORS['primary']}]I[/{COLORS['primary']}] - Ignore all and proceed anyway")
    console.print(f"  [{COLORS['primary']}]D[/{COLORS['primary']}] - Return to discussion phase")
    console.print("")
    
    choice = typer.prompt("Choose", type=str).strip().upper()
    
    if choice == "A":
        return ('A', list(range(len(critical_concerns))))
    elif choice == "S":
        console.print("")
        console.print("Enter concern numbers separated by spaces (e.g., '1 3')")
        selection = typer.prompt("Select").strip()
        try:
            indices = [int(x) - 1 for x in selection.split()]
            valid_indices = [i for i in indices if 0 <= i < len(critical_concerns)]
            return ('S', valid_indices)
        except ValueError:
            console.print(f"[{COLORS['danger']}]Invalid selection.[/{COLORS['danger']}]")
            return ('M', [])
    elif choice == "M":
        return ('M', [])
    elif choice == "I":
        return ('I', [])
    elif choice == "D":
        return ('D', [])
    else:
        console.print(f"[{COLORS['warning']}]Invalid choice. Please try again.[/{COLORS['warning']}]")
        return display_critical_concerns_with_selection(critical_concerns)


def append_recommendations_to_decision(original_decision: str, critical_concerns: list, selected_indices: list) -> str:
    """Append selected recommendations to original decision.
    
    Args:
        original_decision: Player's original decision text
        critical_concerns: Full list of concerns
        selected_indices: Indices of concerns to address
    
    Returns:
        Enhanced decision text
    """
    if not selected_indices:
        return original_decision
    
    additions = []
    for idx in selected_indices:
        role, concern, recommendation = critical_concerns[idx]
        additions.append(f"- {recommendation}")
    
    enhanced = original_decision
    enhanced += "\n\nAdditionally:"
    enhanced += "\n" + "\n".join(additions)
    
    return enhanced


def select_scenario_variant(scenario_id: str) -> str:
    """Display interactive scenario selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected variant key (e.g., 'standard', 'fast_start')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT SCENARIO[/{COLORS['primary']} bold]")
    console.print("")
    
    # Load available scenarios
    scenarios = list_available_scenarios(scenario_id)
    
    if len(scenarios) == 0:
        # No scenarios.yaml found - use default
        return "standard"
    
    # Display scenario options
    for idx, (key, config) in enumerate(scenarios, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        difficulty = config.get("difficulty", "")
        estimated_time = config.get("estimated_time", "")
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        if difficulty:
            console.print(f"   Difficulty: {difficulty}")
        if estimated_time:
            console.print(f"   Estimated Time: {estimated_time}")
        console.print(f"   {description}")
        
        # Show key features
        features = config.get("features", [])
        if features:
            console.print("")
            for feature in features[:3]:  # Show first 3 features
                console.print(f"   - {feature}")
        
        if recommended:
            console.print("")
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    console.print("")
    while True:
        try:
            choice = typer.prompt("Select scenario (enter number)", type=int)
            if 1 <= choice <= len(scenarios):
                selected_key = scenarios[choice - 1][0]
                selected_name = scenarios[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(scenarios)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_play_mode() -> str:
    """Display interactive gameplay mode selection menu.
    
    Returns:
        Selected mode key (e.g., 'classic', 'immersive', 'emergent')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAMEPLAY MODE[/{COLORS['primary']} bold]")
    console.print("")
    
    modes = [
        ("classic", {
            "name": "Classic Wargame",
            "description": "Traditional experience with visible metrics and mechanical effects",
            "features": [
                "See numerical impact of your decisions",
                "Clear thresholds and win conditions",
                "Strategic resource management focus"
            ],
            "recommended": "Traditional wargame players, first playthrough"
        }),
        ("immersive", {
            "name": "Immersive Narrative",
            "description": "Character-driven drama with hidden metrics guiding the story",
            "features": [
                "Visual 'vibes' instead of raw numbers",
                "Character attitudes and relationships",
                "Narrative consequences take center stage"
            ],
            "recommended": "Story-focused players, replay value"
        }),
        ("emergent", {
            "name": "Emergent Drama (Experimental)",
            "description": "Maximum LLM freedom with minimal structure",
            "features": [
                "Pure narrative immersion",
                "Every playthrough unique",
                "Unpredictable emergent outcomes"
            ],
            "recommended": "Experimental players, maximum replayability"
        })
    ]
    
    for idx, (key, config) in enumerate(modes, 1):
        console.print(f"[{COLORS['warning']} bold]{idx}. {config['name']}[/{COLORS['warning']} bold]")
        console.print(f"   {config['description']}")
        console.print("")
        for feature in config['features']:
            console.print(f"   - {feature}")
        console.print("")
        console.print(f"   Recommended for: {config['recommended']}")
        console.print("")
    
    while True:
        try:
            choice = typer.prompt("Select gameplay mode (enter number)", type=int, default=2)
            if 1 <= choice <= len(modes):
                selected_key = modes[choice - 1][0]
                selected_name = modes[choice - 1][1]['name']
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(modes)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_difficulty(scenario_id: str) -> str:
    """Display interactive difficulty selection menu.
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        Selected difficulty key (e.g., 'standard', 'challenging', 'brutal')
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT DIFFICULTY[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Difficulty affects scenario effect magnitudes (crisis intensity).")
    console.print("Player action impacts remain the same across all difficulties.")
    console.print("")
    
    # Load difficulty definitions from scenarios.yaml
    root = Path(__file__).resolve().parents[1]
    scenario_path = root / "data" / "scenarios" / scenario_id / "scenarios.yaml"
    
    difficulties = []
    if scenario_path.exists():
        try:
            import yaml
            with open(scenario_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                difficulties_dict = data.get("difficulties", {})
                # Convert to list of tuples for consistent ordering
                difficulties = [
                    ("standard", difficulties_dict.get("standard", {})),
                    ("challenging", difficulties_dict.get("challenging", {})),
                    ("brutal", difficulties_dict.get("brutal", {}))
                ]
        except Exception:
            pass
    
    # Default if no difficulties found
    if not difficulties:
        difficulties = [
            ("standard", {"name": "Standard", "description": "Balanced challenge", "multiplier": 0.65}),
            ("challenging", {"name": "Challenging", "description": "Tight margins", "multiplier": 0.85}),
            ("brutal", {"name": "Brutal", "description": "Maximum intensity", "multiplier": 1.0})
        ]
    
    # Display difficulty options
    for idx, (key, config) in enumerate(difficulties, 1):
        name = config.get("name", key.title())
        description = config.get("description", "")
        multiplier = config.get("multiplier", 1.0)
        recommended = config.get("recommended_for", "")
        
        console.print(f"[{COLORS['warning']} bold]{idx}. {name}[/{COLORS['warning']} bold]")
        console.print(f"   Effect Multiplier: {multiplier}x")
        console.print(f"   {description}")
        
        if recommended:
            console.print(f"   Recommended for: {recommended}")
        
        console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select difficulty (enter number)", type=int, default=1)
            if 1 <= choice <= len(difficulties):
                selected_key = difficulties[choice - 1][0]
                selected_name = difficulties[choice - 1][1].get("name", selected_key)
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Selected: {selected_name}[/{COLORS['success']} bold]")
                console.print("")
                
                return selected_key
            else:
                console.print(f"[{COLORS['danger']}]Please enter a number between 1 and {len(difficulties)}[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


def select_narrative(scenario_id: str) -> Optional[NarrativeConfig]:
    """Display game type selection menu (Original Story Mode vs Mystery Mode).
    
    Args:
        scenario_id: Base scenario identifier
    
    Returns:
        None if Original Story Mode selected,
        NarrativeConfig (randomly chosen) if Mystery Mode selected
    """
    COLORS = theme_manager.get_colors()
    
    typer.clear()
    console.print("")
    console.print(f"[{COLORS['danger']} bold]# FALSE FLAG: THE WARGAME[/{COLORS['danger']} bold]")
    console.print("=" * 79)
    console.print("")
    console.print(f"[{COLORS['primary']} bold]SELECT GAME TYPE[/{COLORS['primary']} bold]")
    console.print("")
    console.print("Choose how you want to experience the crisis:")
    console.print("")
    
    # Display option 1: Original Story Mode
    console.print(f"[{COLORS['warning']} bold]1. Original Story Mode[/{COLORS['warning']} bold]")
    console.print("   Play the standard story mode as designed. Experience the crisis through")
    console.print("   the eyes of the Prime Minister as events unfold.")
    console.print("")
    
    # Display option 2: Mystery Mode
    console.print(f"[{COLORS['warning']} bold]2. Mystery Mode[/{COLORS['warning']} bold]")
    console.print("   A hidden narrative guides AI agent behaviour. Foreign leaders and")
    console.print("   diplomats may have secret motivations that aren't immediately apparent.")
    console.print("   You must deduce the truth from their actions and responses.")
    console.print("")
    console.print(f"   [{COLORS['danger']}]⚠ The narrative is randomly selected and hidden from you![/{COLORS['danger']}]")
    console.print("")
    
    # Get user selection
    while True:
        try:
            choice = typer.prompt("Select game type (enter number)", type=int, default=1)
            if choice == 1:
                # Original Story Mode - no secret narrative
                console.print("")
                console.print(f"[{COLORS['success']} bold]✓ Original Story Mode selected[/{COLORS['success']} bold]")
                console.print("")
                return None
            elif choice == 2:
                # Mystery Mode - randomly select narrative
                narratives = load_narrative_configs(scenario_id)
                
                if narratives:
                    import random
                    selected_narrative = random.choice(narratives)
                    console.print("")
                    console.print(f"[{COLORS['success']} bold]✓ Mystery Mode activated[/{COLORS['success']} bold]")
                    console.print("")
                    # DO NOT tell player which narrative was selected
                    return selected_narrative
                else:
                    # Fallback if no narratives available - treat as Original Mode
                    console.print("")
                    console.print(f"[{COLORS['warning']}]Mystery Mode unavailable - using Original Story Mode[/{COLORS['warning']}]")
                    console.print("")
                    return None
            else:
                console.print(f"[{COLORS['danger']}]Please enter 1 or 2[/{COLORS['danger']}]")
        except (ValueError, KeyboardInterrupt):
            console.print(f"[{COLORS['danger']}]Invalid input. Please enter a number.[/{COLORS['danger']}]")


@app.command(rich_help_panel="GAMEPLAY")
def play(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed for determinism"),
    load_save: str = typer.Option(None, "--load", help="Load game from save file"),
    stochastic_injects: bool = typer.Option(True, "--stochastic-injects/--no-stochastic-injects", help="Generate injects dynamically (enabled by default)"),
    intro_only: bool = typer.Option(False, "--intro-only", help="Display intro and exit"),
    variant: str = typer.Option(None, "--variant", help="Scenario variant (e.g., 'standard', 'fast_start')"),
    difficulty: str = typer.Option(None, "--difficulty", help="Difficulty level (e.g., 'standard', 'challenging', 'brutal')"),
    play_mode: str = typer.Option(None, "--play-mode", help="Gameplay mode (e.g., 'classic', 'immersive', 'emergent')"),
    flash_only: bool = typer.Option(False, "--flash-only", help="Use Flash model for all LLM calls (5x faster, cheaper)"),
):
    """Play the wargame interactively."""
    
    # Get current colors for loop
    COLORS = theme_manager.get_colors()

    # Configure LLM model if flash_only flag is set
    if flash_only:
        from llm.model_config import get_model_config
        config = get_model_config()
        config.use_flash_for_all()
        typer.echo("")
        typer.echo("[Flash-only mode enabled - using gemini-2.5-flash for all calls]")
        typer.echo("")
    
    # If no variant specified and not loading a save, show selection menu
    if variant is None and load_save is None:
        variant = select_scenario_variant(scenario)
    elif variant is None:
        variant = "standard"  # Default for loaded games
    
    # If no play mode specified and not loading a save, show selection menu
    if play_mode is None and load_save is None:
        play_mode = select_play_mode()
    elif play_mode is None:
        play_mode = "immersive"  # Default for loaded games
    
    # If no difficulty specified and not loading a save, show selection menu
    if difficulty is None and load_save is None:
        difficulty = select_difficulty(scenario)
    elif difficulty is None:
        difficulty = "standard"  # Default for loaded games
    
    # Select game type (Original or Mystery mode) - only for new games
    selected_narrative = None
    if load_save is None:
        selected_narrative = select_narrative(scenario)  # Returns None for Original, NarrativeConfig for Mystery
    
    # Display intro with pauses
    if intro_only or load_save is None:
        intro_lines = get_intro_lines(200)
        
        # Split intro into sections (scenes)
        # Scene markers are lines with "## SCENE"
        current_section = []
        sections = []
        
        for line in intro_lines:
            if "===" in line and current_section:
                # Start of new scene - save previous and start new
                sections.append(current_section)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Only add final section if it has content beyond just a separator
        if current_section and len([l for l in current_section if l.strip() and "===" not in l]) > 0:
            sections.append(current_section)
        
        # Display each scene
        for i, scene in enumerate(sections):
            # Clear screen at start of EVERY scene (including title)
            typer.clear()
            
            skip_rest = False
            prev_line_blank = False
            for line in scene:
                if skip_rest:
                    # User pressed SPACE - print remaining lines instantly
                    # Check if line has Rich markup
                    if "[/" in line and "[" in line:
                        console.print(line)
                    else:
                        typer.echo(line)
                    continue
                    
                if "===" in line:
                    # Structural element - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip() == "":
                    # Blank line
                    if not prev_line_blank:
                        typer.echo("")
                    prev_line_blank = True
                elif line.strip().startswith("# "):
                    # Title - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                elif line.strip().startswith("## YOUR ROLE"):
                    # Section header - print instantly
                    typer.echo(line)
                    prev_line_blank = False
                else:
                    # All other text (narrative)
                    # Check if line contains Rich markup
                    if "[/" in line and "[" in line:
                        # Has Rich markup - use console.print with brief pause
                        import time
                        console.print(line)
                        time.sleep(0.3)  # Brief pause for readability
                        prev_line_blank = False
                    else:
                        # Plain text - stream it
                        skipped = scroll_text(line, delay=0.02)
                        if skipped:
                            skip_rest = True  # Skip rest of scene
                        prev_line_blank = False
            
            # Pause after each scene
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
        
        typer.echo("")
    
    if intro_only:
        return
    
    rng = Random(seed)
    root = Path(__file__).resolve().parents[1]  # cli/main.py -> project root
    
    # For NEW games, load and display Turn 1 briefing as part of intro sequence
    # This makes the COBRA briefing flow seamlessly from the YOUR ROLE section
    first_briefing_as_intro = (load_save is None)
    
    # Load or create world state
    if load_save:
        save_path = Path(load_save)
        try:
            scenario, world, transcript, loaded_play_mode, loaded_narrative_state = load_game(save_path)
            # Use loaded play_mode if available, otherwise use command-line arg
            if loaded_play_mode:
                play_mode = loaded_play_mode
            typer.echo(f"Loaded game from {save_path}")
            typer.echo(f"Resuming at Turn {world.turn}")
            typer.echo("")
            
            # Use loaded narrative state if available, otherwise create new
            if loaded_narrative_state:
                narrative_state = loaded_narrative_state
            else:
                # Create narrative state from loaded world (legacy saves)
                narrative_state = create_initial_narrative_state(
                    metrics=world.metrics.copy(),
                    play_mode=play_mode,
                    game_time=f"Turn {world.turn}"
                )
                narrative_state.turn = world.turn
            
        except (FileNotFoundError, ValueError) as e:
            typer.echo(f"Error loading save: {e}", err=True)
            raise typer.Exit(1)
    else:
        # New game
        initial_conditions = load_initial_conditions(scenario, root)
        initial_metrics = initial_conditions.get("initial_metrics", {})
        
        world = WorldState(
            turn=1,
            scene=1,
            difficulty=difficulty,
            narrative=selected_narrative,  # Set the secret narrative truth
            metrics=Metrics(
                escalation_risk=initial_metrics.get("escalation_risk", 60),
                domestic_stability=initial_metrics.get("domestic_stability", 50),
                alliance_cohesion=initial_metrics.get("alliance_cohesion", 40),
                casualties_mil=initial_metrics.get("casualties_mil", 2),
                casualties_civ=initial_metrics.get("casualties_civ", 0),
            ),
            flags={},
            posture={},
        )
        
        # Initialize state actor system for multi-agent simulation
        try:
            from models.state_actors import load_actors_from_yaml
            actor_yaml_path = root / "data" / "state_actors.yaml"
            world.actor_system = load_actors_from_yaml(str(actor_yaml_path))
            console.print(f"[{COLORS['success']}]✓ Multi-agent actor system initialized[/{COLORS['success']}]")
        except Exception as e:
            console.print(f"[{COLORS['warning']}]Warning: Could not load actor system: {e}[/{COLORS['warning']}]")
            world.actor_system = None
        
        # Initialize narrative state system
        narrative_state = create_initial_narrative_state(
            metrics=world.metrics.copy(),
            play_mode=play_mode,
            game_time=initial_conditions.get("metadata", {}).get("start_time", "Sunday 5th October 2025, 17:00")
        )
        
        transcript = []
    
    # Load scenario configuration for variant-specific turn files
    scenario_config = get_scenario_config(scenario, variant, root)
    stochastic_from_turn = scenario_config.get("stochastic_from", 7)
    
    # Main game loop
    while True:
        # Refresh colors at start of loop in case theme changed
        COLORS = theme_manager.get_colors()
        
        # Capture metrics at START of turn (before inject effects)
        from copy import deepcopy
        turn_start_metrics = deepcopy(world.metrics)
        
        # Auto-enable stochastic generation when reaching the transition point
        if world.turn >= stochastic_from_turn:
            if not stochastic_injects:
                # First time reaching stochastic content - show transition message
                stochastic_injects = True
                console.print("")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print(f"[{COLORS['primary']} bold]ENTERING DYNAMIC SCENARIO GENERATION[/{COLORS['primary']} bold]")
                console.print(f"[{COLORS['primary']}]" + "=" * 79 + f"[/{COLORS['primary']}]")
                console.print("")
                console.print("The scripted scenario has concluded. From this point forward,")
                console.print("events will be dynamically generated based on your decisions.")
                console.print("")
                wait_for_space("Press SPACE to continue...")
                console.print("")
        
        # Determine if we should use stochastic generation for this turn
        use_stochastic = stochastic_injects and world.turn >= stochastic_from_turn
        
        # Get turn filename based on scenario variant
        turn_filename = get_turn_filename(world.turn, scenario_config)
        
        # Briefing phase (with player input function for diplomatic encounters)
        # For Turn 1 of new games: suppress panel display and effect boxes (will be streamed in intro flow)
        is_turn1_intro = (first_briefing_as_intro and world.turn == 1)
        inject, briefing_lines = run_turn_briefing(
            world, 
            scenario, 
            use_stochastic, 
            rng, 
            root, 
            transcript,
            get_player_input=lambda prompt: typer.prompt(prompt).strip(),
            turn_filename=turn_filename,
            silent_effects=is_turn1_intro,  # Hide effect boxes for Turn 1 intro
            suppress_display=is_turn1_intro  # Suppress panel so we can stream the text
        )
        
        # Clear screen and display briefing at top
        # BUT: if this is Turn 1 of a new game, don't clear (flows from intro)
        if not (first_briefing_as_intro and world.turn == 1):
            typer.clear()
        else:
            # First briefing of new game - add separator but don't clear
            typer.echo("")
            typer.echo("=" * 79)
            typer.echo("")
        
        # Split briefing into scene-setting and actual briefing
        # Look for "The National Security Advisor" or similar transition line
        # BUT: for Turn 1 of new games, don't split - show everything in one flow
        scene_setting_end = -1
        if not (first_briefing_as_intro and world.turn == 1):
            for i, line in enumerate(briefing_lines):
                if "National Security Advisor" in line and ("clears" in line or "begins" in line):
                    scene_setting_end = i
                    break
        
        # Display scene-setting part with streaming
        skip_rest = False
        for i, line in enumerate(briefing_lines):
            # Stop at the transition line
            if scene_setting_end > 0 and i >= scene_setting_end:
                break
                
            if skip_rest:
                # User pressed SPACE - print rest instantly
                # Check if line has Rich markup
                if "[/" in line and "[" in line:
                    console.print(line)
                else:
                    typer.echo(line)
                continue
            
            # Scroll the turn number header
            if i == 1 and line.strip().startswith("TURN"):
                skipped = scroll_text(line, delay=0.05)
                if skipped:
                    skip_rest = True
            # Stream narrative text (not structural elements)
            elif line.strip() and not line.strip().startswith("==="):
                # Check if line contains Rich markup
                if "[/" in line and "[" in line:
                    # Has Rich markup - use console.print with brief pause
                    import time
                    console.print(line)
                    time.sleep(0.3)
                else:
                    # Plain text - stream it
                    skipped = scroll_text(line, delay=0.02)
                    if skipped:
                        skip_rest = True
            else:
                typer.echo(line)
        
        # Pause after scene-setting (only if we found a split point)
        if scene_setting_end > 0:
            typer.echo("")
            wait_for_space("Press SPACE to continue...")
            
            # Display rest of briefing (the actual intelligence report)
            typer.echo("")
            for i in range(scene_setting_end, len(briefing_lines)):
                typer.echo(briefing_lines[i])
        
        transcript.extend(briefing_lines)
        
        # Show intelligence briefing (Immersive/Emergent modes only)
        if play_mode in ["immersive", "emergent"] and world.turn > 1:
            from engine.intelligence import generate_intelligence_briefing
            intel_lines = generate_intelligence_briefing(narrative_state, world, rng, detailed=False)
            typer.echo("")
            for line in intel_lines:
                console.print(line)
            typer.echo("")
        
        # Pause before discussion phase
        typer.echo("")
        wait_for_space("Press SPACE to begin discussion phase...")
        
        # After Turn 1 intro briefing is shown, reset the flag
        if first_briefing_as_intro and world.turn == 1:
            first_briefing_as_intro = False
        
        # Clear screen and show discussion phase at top
        typer.clear()
        typer.echo("")  # Buffer line BEFORE Rich output
        
        if RICH_ENABLED:
            console.print(phase_header("DISCUSSION", world.turn))
            typer.echo("")
            typer.echo("  Ask questions or type /decide when ready")
            console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
            typer.echo("")
            console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
            console.print("=" * 79)
            console.print("")
            console.print("Ask advisors questions, or type '/decide' when ready.")
            console.print("Type '/menu' for commands, '/advise' for all advisors, '/resources' for forces.")
        
        typer.echo("")
        
        # Discussion phase loop - DASHBOARD MODE
        from cli.dashboard import WargameDashboard
        from rich.live import Live
        
        dashboard = WargameDashboard(world, console)
        questions = []
        
        with Live(dashboard.layout, console=console, refresh_per_second=2) as live:
            while True:
                # Update dashboard
                dashboard.update()
                
                # Get input (pause live updates)
                live.stop()
                user_input = console.input(f"[{COLORS['primary']}]>[/] ").strip()
                live.start()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["/decide", "decide", "decision"]:
                break
            
            if user_input.lower() in ["/quit", "quit"]:
                typer.echo("Exiting game.")
                raise typer.Exit(0)
            
            if user_input.lower() in ["/save", "save"]:
                save_path = save_game(world, transcript, scenario, f"turn_{world.turn:03d}", root, play_mode, narrative_state)
                typer.echo(f"Game saved to {save_path}")
                continue
            
            if user_input.lower() in ["/theme", "theme"]:
                typer.echo("")
                console.print("Available themes:")
                console.print("  1. Standard (Cyan/Blue)")
                console.print("  2. DEFCON 1 (Red/Alert)")
                console.print("  3. Retro (Green Phosphor)")
                console.print("  4. Slate (Black/White Monochrome)")
                typer.echo("")
                
                theme_choice = typer.prompt("Select theme (1-4)").strip()
                theme_map = {"1": "standard", "2": "defcon1", "3": "retro", "4": "slate"}
                
                if theme_choice in theme_map:
                    theme_name = theme_map[theme_choice]
                    theme_manager.set_theme(theme_name)
                    COLORS = theme_manager.get_colors()
                    console.print(f"[{COLORS['success']}]Theme changed to {theme_name.title()}[/{COLORS['success']}]")
                    # Refresh current view
                    typer.clear()
                    if RICH_ENABLED:
                        console.print(phase_header("DISCUSSION", world.turn))
                        typer.echo("")
                        typer.echo("  Ask questions or type /decide when ready")
                        console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /llm[/{COLORS['muted']}]")
                        typer.echo("")
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("[bold red]Invalid selection[/bold red]")
                continue

            if user_input.lower() in ["/status", "status"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Display based on play mode
                    if play_mode == "classic":
                        # Show metrics table (includes turn, phase, influence)
                        console.print(metrics_table(world))
                    elif play_mode == "immersive":
                        # Show vibes
                        typer.echo("═" * 60)
                        typer.echo("SITUATION ASSESSMENT")
                        typer.echo("═" * 60)
                        typer.echo("")
                        vibes = narrative_state.get_situation_vibes()
                        for vibe in vibes:
                            typer.echo(vibe.to_string())
                        typer.echo("")
                        
                        # Show character attitudes
                        typer.echo("═" * 60)
                        typer.echo("ADVISOR ATTITUDES")
                        typer.echo("═" * 60)
                        typer.echo("")
                        for char_id, char_attitude in narrative_state.characters.items():
                            trust_level = char_attitude.trust // 20
                            trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                            relationship_symbol = {
                                "allied": "✓",
                                "neutral": "○",
                                "hostile": "✗",
                                "unknown": "?"
                            }.get(char_attitude.relationship, "○")
                            typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
                    elif play_mode == "emergent":
                        # Show narrative summary
                        typer.echo("═" * 60)
                        typer.echo(narrative_state.situation_summary)
                        typer.echo("═" * 60)
                    
                    # Show active flags if any
                    if world.flags:
                        typer.echo("")
                        console.print(f"[{COLORS['warning']} bold]ACTIVE RISK FLAGS:[/{COLORS['warning']} bold]")
                        for flag, value in world.flags.items():
                            if value:
                                console.print(f"  [{COLORS['warning']}]{SYMBOLS['warning']} {flag.replace('_', ' ').title()}[/{COLORS['warning']}]")
                else:
                    # Fallback to plain text
                    typer.echo("=" * 60)
                    typer.echo("CURRENT SITUATION")
                    typer.echo("=" * 60)
                    typer.echo("")
                    typer.echo(f"Turn: {world.turn}")
                    typer.echo(f"Phase: {world.phase}")
                    typer.echo("")
                    typer.echo("Metrics:")
                    typer.echo(f"  Escalation Risk:      {world.metrics.escalation_risk}/100")
                    typer.echo(f"  Domestic Stability:   {world.metrics.domestic_stability}/100")
                    typer.echo(f"  Alliance Cohesion:    {world.metrics.alliance_cohesion}/100")
                    typer.echo(f"  Military Casualties:  {world.metrics.casualties_mil}")
                    typer.echo(f"  Civilian Casualties:  {world.metrics.casualties_civ}")
                    typer.echo("")
                    
                    # Calculate influence
                    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
                    influence = int((influence_raw - 50) / 5)
                    influence = max(-10, min(10, influence))
                    influence_sign = "+" if influence >= 0 else ""
                    typer.echo(f"Public Sentiment (Influence): {influence_sign}{influence}/10")
                    typer.echo("")
                    
                    if world.flags:
                        typer.echo("Active Risk Flags:")
                        for flag, value in world.flags.items():
                            if value:
                                typer.echo(f"  ! {flag.replace('_', ' ').title()}")
                        typer.echo("")
                
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/call "):
                # Handle diplomatic call
                country_input = user_input[6:].strip().upper()
                
                # Map common names to country codes
                country_map = {
                    "US": "US", "USA": "US", "AMERICA": "US", "UNITED STATES": "US",
                    "FRANCE": "France", "FRENCH": "France",
                    "GERMANY": "Germany", "GERMAN": "Germany",
                    "POLAND": "Poland", "POLISH": "Poland",
                    "RUSSIA": "Russia", "RUSSIAN": "Russia",
                    "UKRAINE": "Ukraine", "UKRAINIAN": "Ukraine",
                    "IRELAND": "Ireland", "IRISH": "Ireland"
                }
                
                country = country_map.get(country_input, country_input.capitalize())
                
                console.print("")
                console.print(f"[{COLORS['success']} bold]Connecting to {country}...[/{COLORS['success']} bold]")
                
                # Run diplomatic encounter (with real-time printing)
                encounter_transcript, cohesion_delta = run_diplomatic_encounter(
                    world,
                    country,
                    required=False,
                    context=None,
                    llm_generate=generate_text,
                    rng=rng,
                    root_path=root,
                    full_transcript=transcript,
                    get_player_input=lambda prompt: typer.prompt(prompt).strip(),
                    print_fn=typer.echo  # Print in real-time
                )
                
                # Transcript already printed, just save it
                transcript.extend(encounter_transcript)
                
                # Apply alliance cohesion change
                from engine.utils import clamp, clamp_metrics
                from engine.flags import update_world_flags
                
                world.metrics.alliance_cohesion = clamp(world.metrics.alliance_cohesion + cohesion_delta)
                clamp_metrics(world.metrics)
                update_world_flags(world)
                
                continue
            
            if user_input.lower() in ["/advise", "advise"]:
                # Get advice from all advisors
                typer.echo("")
                
                if RICH_ENABLED:
                    # Top border
                    box = BOX["round"]
                    title = " COBRA ADVISORY PANEL "
                    title_len = len(title)
                    left_pad = (WIDTH - title_len - 2) // 2
                    right_pad = WIDTH - title_len - left_pad - 2
                    console.print(f"[{COLORS['accent']} bold]{box['tl']}{box['h'] * left_pad}{title}{box['h'] * right_pad}{box['tr']}[/{COLORS['accent']} bold]")
                    typer.echo("")
                else:
                    typer.echo("=" * 79)
                    typer.echo("COBRA ADVISORY PANEL")
                    typer.echo("=" * 79)
                    typer.echo("")
                
                typer.echo("Requesting input from all advisors on the current situation...")
                typer.echo("")
                
                # Ask each advisor for their assessment
                # Add conciseness instruction to keep responses brief
                advisors = [
                    ("National Security Advisor", "NSA, what's your assessment of the current situation and recommended course of action? [Please be concise - 3-4 sentences maximum]"),
                    ("Chief of the Defence Staff", "CDS, what are our military options and constraints? [Please be concise - 3-4 sentences maximum]"),
                    ("Foreign Secretary", "Foreign Secretary, what's the diplomatic landscape and alliance status? [Please be concise - 3-4 sentences maximum]"),
                    ("Home Secretary", "Home Secretary, what are the domestic security concerns? [Please be concise - 3-4 sentences maximum]"),
                    ("Attorney General", "Attorney General, what are the legal constraints and considerations? [Please be concise - 3-4 sentences maximum]")
                ]
                
                for advisor_name, question in advisors:
                    # Separator between advisors
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                    else:
                        typer.echo("─" * 79)
                    
                    console.print(f"  [{COLORS['secondary']} bold]{advisor_name.upper()}[/{COLORS['secondary']} bold]")
                    typer.echo("")
                    
                    # Get response from this advisor
                    discussion_lines = run_turn_discussion(world, scenario, [question], rng, root, transcript)
                    for line in discussion_lines:
                        # Skip the "Prime Minister:" echo and strip the conciseness instruction
                        if not line.startswith("Prime Minister:"):
                            # Remove the [Please be concise...] instruction from display
                            display_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            if display_line:  # Only display non-empty lines
                                # Format response with structure
                                if ":" in display_line:
                                    advisor_role, rest = display_line.split(":", 1)
                                    if RICH_ENABLED:
                                        formatted = format_advisor_response("", rest)
                                        console.print(formatted)
                                    else:
                                        console.print(f"[{COLORS['secondary']} bold]{advisor_role}:[/{COLORS['secondary']} bold]", end="")
                                        console.print(rest)
                                else:
                                    typer.echo(display_line)
                        else:
                            # For transcript, clean up the question
                            clean_line = line.replace("[Please be concise - 3-4 sentences maximum]", "").strip()
                            transcript.append(clean_line)
                            continue
                    # Only add non-question lines to transcript (questions already added above)
                    transcript.extend([l for l in discussion_lines if not l.startswith("Prime Minister:")])
                    typer.echo("")
                
                if RICH_ENABLED:
                    # Bottom border
                    console.print(f"[{COLORS['accent']} bold]{box['bl']}{box['h'] * (WIDTH - 2)}{box['br']}[/{COLORS['accent']} bold]")
                else:
                    typer.echo("=" * 79)
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/resources", "resources"]:
                # Display UK forces and stockpiles
                initial_conditions = load_initial_conditions(scenario, root)
                
                typer.echo("")
                
                if RICH_ENABLED:
                    forces_table, stockpiles_table = resources_tables(initial_conditions)
                    console.print(forces_table)
                    typer.echo("")
                    console.print(stockpiles_table)
                    typer.echo("")
                    continue
                
                # Fallback to plain text
                typer.echo("=" * 79)
                typer.echo("UK MILITARY RESOURCES")
                typer.echo("=" * 79)
                typer.echo("")
                
                # Display stockpiles
                stockpiles = initial_conditions.get("stockpiles", {})
                if stockpiles:
                    typer.echo("AMMUNITION STOCKPILES:")
                    typer.echo("")
                    
                    # Air Defence
                    air_defence = stockpiles.get("air_defence_missiles", {})
                    if air_defence:
                        typer.echo("  Air Defence:")
                        for weapon, data in air_defence.items():
                            count = data.get("count", 0)
                            note = data.get("note", "")
                            typer.echo(f"    • {weapon.replace('_', ' ').title()}: {count}")
                            if note:
                                typer.echo(f"      {note}")
                        typer.echo("")
                    
                    # Naval Strike
                    typer.echo("  Naval Strike:")
                    tomahawk = stockpiles.get("tomahawk_cruise_missiles", {})
                    if tomahawk:
                        typer.echo(f"    • Tomahawk Cruise Missiles: {tomahawk.get('count', 0)}")
                        typer.echo(f"      {tomahawk.get('note', '')}")
                    harpoon = stockpiles.get("harpoon_anti_ship", {})
                    if harpoon:
                        typer.echo(f"    • Harpoon Anti-Ship: {harpoon.get('count', 0)}")
                        typer.echo(f"      {harpoon.get('note', '')}")
                    typer.echo("")
                    
                    # Air-Launched
                    typer.echo("  Air-Launched Precision:")
                    storm_shadow = stockpiles.get("storm_shadow_cruise_missiles", {})
                    if storm_shadow:
                        typer.echo(f"    • Storm Shadow: {storm_shadow.get('count', 0)}")
                        typer.echo(f"      {storm_shadow.get('note', '')}")
                    paveway = stockpiles.get("paveway_laser_guided_bombs", {})
                    if paveway:
                        typer.echo(f"    • Paveway LGBs: {paveway.get('count', 0)}")
                        typer.echo(f"      {paveway.get('note', '')}")
                    typer.echo("")
                    
                    # Anti-Submarine
                    typer.echo("  Anti-Submarine:")
                    spearfish = stockpiles.get("spearfish_torpedoes", {})
                    if spearfish:
                        typer.echo(f"    • Spearfish Torpedoes: {spearfish.get('count', 0)}")
                        typer.echo(f"      {spearfish.get('note', '')}")
                    stingray = stockpiles.get("stingray_lightweight_torpedoes", {})
                    if stingray:
                        typer.echo(f"    • Stingray Torpedoes: {stingray.get('count', 0)}")
                        typer.echo(f"      {stingray.get('note', '')}")
                    typer.echo("")
                
                # Display forces
                uk_forces = initial_conditions.get("uk_forces", {})
                if uk_forces:
                    naval = uk_forces.get("naval", [])
                    if naval:
                        typer.echo("NAVAL FORCES:")
                        typer.echo("")
                        for unit in naval:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            typer.echo(f"  • {unit_id} ({unit_type})")
                            typer.echo(f"    Location: {location}")
                            typer.echo(f"    Status: {status}")
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            typer.echo("")
                    
                    air = uk_forces.get("air", [])
                    if air:
                        typer.echo("AIR FORCES:")
                        typer.echo("")
                        for unit in air:
                            unit_id = unit.get("id", "Unknown")
                            unit_type = unit.get("type", "")
                            location = unit.get("location", "")
                            status = unit.get("status", "")
                            
                            # Display unit header
                            typer.echo(f"  • {unit_id}")
                            
                            # Show type and role
                            if unit_type:
                                role = unit.get("role", "")
                                if role:
                                    typer.echo(f"    Type: {unit_type} ({role})")
                                else:
                                    typer.echo(f"    Type: {unit_type}")
                            
                            # Show location if present
                            if location:
                                typer.echo(f"    Location: {location}")
                            
                            # Show aircraft counts if present
                            aircraft_count = unit.get("aircraft_count")
                            operational_aircraft = unit.get("operational_aircraft")
                            if aircraft_count is not None:
                                if operational_aircraft is not None:
                                    typer.echo(f"    Aircraft: {operational_aircraft}/{aircraft_count} operational")
                                else:
                                    typer.echo(f"    Aircraft: {aircraft_count}")
                            
                            # Show status
                            typer.echo(f"    Status: {status}")
                            
                            # Show note if present
                            if unit.get("note"):
                                typer.echo(f"    Note: {unit.get('note')}")
                            
                            typer.echo("")
                
                typer.echo("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower().startswith("/intel"):
                # Intelligence command - detailed actor assessment
                typer.echo("")
                
                # Parse command: /intel or /intel <country_code>
                parts = user_input.lower().split()
                if len(parts) == 1:
                    # Show available actors
                    if world.actor_system:
                        typer.echo("Available countries for intelligence assessment:")
                        typer.echo("")
                        for code, actor in world.actor_system.actors.items():
                            typer.echo(f"  /intel {code.lower()} - {actor.full_name}")
                        typer.echo("")
                    else:
                        typer.echo("Intelligence system not available.")
                else:
                    # Show detailed assessment for specific actor
                    country_code = parts[1].upper()
                    if world.actor_system:
                        from engine.intelligence import generate_actor_detailed_assessment
                        intel_lines = generate_actor_detailed_assessment(country_code, world, world.turn)
                        for line in intel_lines:
                            console.print(line)
                    else:
                        typer.echo("Intelligence system not available.")
                
                typer.echo("")
                continue
            
            if user_input.lower() in ["/llm", "llm", "/settings", "settings"]:
                # Open LLM model settings menu
                typer.echo("")
                typer.echo("Opening LLM Model Settings...")
                typer.echo("")
                model_settings_menu()
                # After returning from settings, clear and redisplay the discussion phase
                typer.clear()
                typer.echo("")
                if RICH_ENABLED:
                    console.print(phase_header("DISCUSSION", world.turn))
                    typer.echo("")
                    typer.echo("  Ask questions or type /decide when ready")
                    console.print(f"  [{COLORS['muted']}]Quick: /status  /menu  /advise  /resources  /intel  /llm[/{COLORS['muted']}]")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                else:
                    console.print("=" * 79)
                    console.print(f"[{COLORS['accent']} bold]TURN {world.turn}: DISCUSSION PHASE[/{COLORS['accent']} bold]")
                    console.print("=" * 79)
                typer.echo("")
                continue
            
            if user_input.lower() in ["/menu", "menu", "/help", "help"]:
                typer.echo("")
                
                if RICH_ENABLED:
                    # Show advisor panel
                    console.print(advisor_menu_panel())
                    typer.echo("")
                    
                    # Show diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    console.print(diplomatic_contacts_table(available_contacts))
                    typer.echo("")
                    
                    # Show metrics guide
                    console.print(metrics_guide_panel())
                    typer.echo("")
                    
                    # Show commands
                    console.print(command_menu())
                    typer.echo("")
                    
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                else:
                    # Fallback to plain text
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]AVAILABLE ADVISORS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• National Security Advisor (NSA)")
                    typer.echo("  - Intelligence assessment, strategic planning, threat analysis")
                    typer.echo("  - Example: 'NSA, what's your assessment of Russian intentions?'")
                    typer.echo("")
                    typer.echo("• Chief of the Defence Staff (CDS)")
                    typer.echo("  - Military operations, force readiness, deployment options")
                    typer.echo("  - Example: 'CDS, what are our air defence capabilities?'")
                    typer.echo("")
                    typer.echo("• Foreign Secretary")
                    typer.echo("  - Diplomacy, alliance management, NATO coordination")
                    typer.echo("  - Example: 'Foreign Secretary, can we count on US support?'")
                    typer.echo("")
                    typer.echo("• Home Secretary")
                    typer.echo("  - Domestic security, civil protection, public messaging")
                    typer.echo("  - Example: 'Home Secretary, how do we reassure the public?'")
                    typer.echo("")
                    typer.echo("• Attorney General")
                    typer.echo("  - Legal framework, international law, rules of engagement")
                    typer.echo("  - Example: 'Attorney General, what are our legal constraints?'")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['success']} bold]DIPLOMATIC CONTACTS[/{COLORS['success']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    
                    # List available diplomatic contacts
                    available_contacts = list_available_diplomatic_contacts(world, root)
                    if available_contacts:
                        for country, access_level, title in available_contacts:
                            if access_level == "leader":
                                console.print(f"[{COLORS['warning']} bold]  * LEADER[/{COLORS['warning']} bold] - {country}: {title}")
                            else:
                                console.print(f"  • Diplomat - {country}: {title}")
                            console.print(f"    Command: /call {country.lower()}")
                            typer.echo("")
                    else:
                        typer.echo("  No diplomatic contacts available (Alliance Cohesion too low)")
                        typer.echo("")
                    
                    console.print("=" * 60)
                    console.print(f"[{COLORS['warning']} bold]METRICS GUIDE[/{COLORS['warning']} bold]")
                    console.print("=" * 60)
                    typer.echo("")
                    typer.echo("• Escalation Risk (0-100)")
                    typer.echo("  Likelihood of conflict escalating to full-scale war")
                    typer.echo("  HIGH = Danger of Russian attack or nuclear exchange")
                    typer.echo("")
                    typer.echo("• Domestic Stability (0-100)")
                    typer.echo("  Public confidence, economic stability, infrastructure security")
                    typer.echo("  LOW = Civil unrest, panic, political pressure")
                    typer.echo("")
                    typer.echo("• Alliance Cohesion (0-100)")
                    typer.echo("  Strength of NATO solidarity and allied support")
                    typer.echo("  HIGH = Access to leaders, Article 5 support likely")
                    typer.echo("  LOW = Isolated, limited diplomatic access")
                    typer.echo("")
                    typer.echo("• Influence (-10 to +10)")
                    typer.echo("  Your political capital and public sentiment")
                    typer.echo("  Derived from: (Stability + Cohesion) / 2")
                    typer.echo("  Currently: Informational only (future: affects options)")
                    typer.echo("")
                    console.print("=" * 60)
                    console.print(f"[{COLORS['accent']} bold]COMMANDS[/{COLORS['accent']} bold]")
                    console.print("=" * 60)
                    console.print("")
                    console.print(f"[{COLORS['primary']}]  /menu or /help[/{COLORS['primary']}]     - Show this menu")
                    console.print(f"[{COLORS['primary']}]  /status[/{COLORS['primary']}]            - Show current metrics and situation")
                    console.print(f"[{COLORS['primary']}]  /advise[/{COLORS['primary']}]            - Get input from all advisors at once")
                    console.print(f"[{COLORS['primary']}]  /resources[/{COLORS['primary']}]         - Show UK forces and ammunition stockpiles")
                    console.print(f"[{COLORS['primary']}]  /call <country>[/{COLORS['primary']}]    - Contact a foreign leader or diplomat")
                    console.print(f"[{COLORS['primary']}]  /decide[/{COLORS['primary']}]            - Make your decision")
                    console.print(f"[{COLORS['primary']}]  /theme[/{COLORS['primary']}]             - Change UI theme")
                    console.print(f"[{COLORS['primary']}]  /save[/{COLORS['primary']}]              - Save game and continue")
                    console.print(f"[{COLORS['primary']}]  /quit[/{COLORS['primary']}]              - Exit game")
                    typer.echo("")
                    console.print(f"[{COLORS['muted']}]NOTE: You may also ask general questions without naming a specific advisor.[/{COLORS['muted']}]")
                
                typer.echo("")
                continue
            
            # Handle question
            questions.append(user_input)
            dashboard.add_message("PM", user_input)
            
            discussion_lines = run_turn_discussion(world, scenario, [user_input], rng, root, transcript)
            
            typer.echo("")  # Space before response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
                typer.echo("")
            
            for line in discussion_lines:
                # Skip echoing the player's question (they just typed it)
                if not line.startswith("Prime Minister:"):
                    if ":" in line:
                        advisor_name, rest = line.split(":", 1)
                        
                        # Add to dashboard conversation log
                        dashboard.add_message(advisor_name.strip(), rest.strip())
                        
                        # Print advisor name
                        console.print(f"  [{COLORS['secondary']} bold]{advisor_name}[/{COLORS['secondary']} bold]")
                        typer.echo("")
                        
                        # Format response with structure
                        if RICH_ENABLED:
                            formatted = format_advisor_response("", rest)
                            console.print(formatted)
                        else:
                            typer.echo(rest)
                    else:
                        typer.echo(line)
            
            transcript.extend(discussion_lines)
            
            typer.echo("")  # Space after response
            
            if RICH_ENABLED:
                console.print(f"[{COLORS['muted']}]" + "─" * 79 + f"[/{COLORS['muted']}]")
            
            typer.echo("")
        
        # Decision phase loop - allows returning to discussion if decision is cancelled
        decision_confirmed = False
        while not decision_confirmed:
            # Decision phase - clear screen and start at top
            typer.clear()
            typer.echo("")  # Buffer line
            
            if RICH_ENABLED:
                console.print(phase_header("DECISION", world.turn))
                typer.echo("")
                typer.echo("  Enter your decision (or 'cancel' to return to discussion)")
            else:
                console.print("=" * 79)
                console.print(f"[{COLORS['emphasis']} bold]TURN {world.turn}: DECISION PHASE[/{COLORS['emphasis']} bold]")
                console.print("=" * 79)
                console.print("")
                console.print("Enter your decision (or 'cancel' to return to discussion):")
            
            typer.echo("")
            
            action = typer.prompt("Decision>").strip()
            
            if action.lower() == "cancel":
                # Return to discussion phase
                break
            
            if not action:
                typer.echo("No action entered. Returning to discussion.")
                typer.echo("")
                wait_for_space("Press SPACE to return to discussion...")
                break
            
            # Interpret and get pushback
            interpretation, pushback, critical_concerns, decision_lines = run_turn_decision(world, scenario, action, rng, root, transcript)
            transcript.extend(decision_lines)
            
            # Display decision with improved UX
            display_decision_summary(action, interpretation, show_details=False)
            
            # Option to see full details
            see_details = typer.prompt("", default="").strip().lower()
            if see_details == "details":
                display_decision_summary(action, interpretation, show_details=True)
                console.print("")
            
            # Handle critical omissions with selective addressing
            if critical_concerns:
                action_code, selected_indices = display_critical_concerns_with_selection(critical_concerns)
                
                if action_code == 'D':
                    # Return to discussion
                    typer.echo("")
                    typer.echo("Returning to discussion phase.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break
                
                elif action_code == 'M':
                    # Modify manually
                    typer.echo("")
                    typer.echo("Decision cancelled. Please enter a modified decision.")
                    typer.echo("")
                    continue
                
                elif action_code in ['A', 'S'] and selected_indices:
                    # Apply selected recommendations
                    console.print("")
                    console.print(f"[{COLORS['success']}]Applying {len(selected_indices)} recommendation(s)...[/{COLORS['success']}]")
                    console.print("")
                    
                    # Append recommendations
                    enhanced_decision = append_recommendations_to_decision(action, critical_concerns, selected_indices)
                    
                    # Show enhanced decision
                    from rich.panel import Panel
                    console.print(Panel(f"[italic]{enhanced_decision}[/italic]", title="[bold]ENHANCED DECISION[/bold]", border_style="white"))
                    console.print("")
                    
                    # Confirm
                    confirm = typer.confirm("Proceed with enhanced decision?", default=True)
                    
                    if not confirm:
                        console.print("")
                        console.print("Decision cancelled.")
                        console.print("")
                        continue
                    
                    # Update action for adjudication
                    action = enhanced_decision
                    
                    # Re-interpret
                    console.print("")
                    console.print("Re-interpreting enhanced decision...")
                    console.print("")
                    
                    interpretation, pushback, critical_concerns_2, decision_lines_2 = run_turn_decision(world, scenario, action, rng, root, transcript)
                    transcript.extend(decision_lines_2)
                    
                    # Display new interpretation
                    display_decision_summary(action, interpretation, show_details=False)
                    
                    # If STILL have concerns, warn
                    if critical_concerns_2:
                        console.print("")
                        console.print(f"[{COLORS['warning']}]⚠ Warning: Critical concerns remain.[/{COLORS['warning']}]")
                        console.print("")
                        # Let player proceed or go back
                        cont = typer.confirm("Proceed anyway?", default=False)
                        if not cont:
                            continue
                    
                    decision_confirmed = True
                
                else:  # 'I' - Ignore
                    typer.echo("")
                    typer.echo(f"[{COLORS['warning']}]Proceeding despite all concerns...[/{COLORS['warning']}]")
                    typer.echo("")
                    decision_confirmed = True
            
            # Confirm decision (regular pushback, if any)
            elif pushback:
                typer.echo("")
                confirm = typer.confirm("Proceed with this decision despite concerns?", default=True)
                if not confirm:
                    typer.echo("")
                    typer.echo("Decision cancelled. Returning to discussion.")
                    typer.echo("")
                    wait_for_space("Press SPACE to return to discussion...")
                    break  # Break inner loop, return to discussion
                else:
                    decision_confirmed = True  # Proceed to adjudication
            else:
                decision_confirmed = True  # No pushback, proceed to adjudication
        
        # If decision was cancelled, go back to discussion phase
        if not decision_confirmed:
            continue
        
        # Adjudication phase - clear screen and start at top
        typer.clear()
        typer.echo("")  # Buffer line
        
        if RICH_ENABLED:
            console.print(phase_header("ADJUDICATION", world.turn))
        else:
            console.print("=" * 79)
            console.print(f"[{COLORS['success']} bold]TURN {world.turn}: ADJUDICATION[/{COLORS['success']} bold]")
            console.print("=" * 79)
        
        typer.echo("")  # Buffer line
        
        # Run LLM-driven adjudication with narrative quality assessment
        try:
            actor_responses = []
            
            if world.actor_system:
                # Use multi-agent simulation
                from engine.narrative_adjudication import adjudicate_with_actor_simulation
                
                final_effects, actor_responses, character_responses, reasoning = adjudicate_with_actor_simulation(
                    narrative_state,
                    world.actor_system,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            else:
                # Use standard narrative adjudication
                final_effects, character_responses, reasoning = adjudicate_with_narrative(
                    narrative_state,
                    action,
                    interpretation,
                    rng,
                    llm_generate_fn=generate_text,
                    world_narrative=world.narrative
                )
            
            # Display quality reasoning
            typer.echo("")
            if RICH_ENABLED:
                console.print(Panel(format_markdown(reasoning), title=f"[{COLORS['accent']} bold]ACTION ASSESSMENT[/]", border_style=COLORS['accent']))
            else:
                typer.echo("=" * 60)
                typer.echo("ACTION ASSESSMENT")
                typer.echo("=" * 60)
                typer.echo("")
                typer.echo(reasoning)
            typer.echo("")
            
            # Display effects
            if RICH_ENABLED:
                console.print(f"[{COLORS['accent']} bold]EFFECTS[/]")
                console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
            else:
                typer.echo("=" * 60)
                typer.echo("EFFECTS")
                typer.echo("=" * 60)
            typer.echo("")
            
            for metric, delta in final_effects.items():
                if RICH_ENABLED:
                    color = COLORS['success'] if delta > 0 else COLORS['danger'] if delta < 0 else COLORS['muted']
                    console.print(f"  [{color}]{metric}: {delta:+d}[/{color}]")
                else:
                    typer.echo(f"  {metric}: {delta:+d}")
            typer.echo("")
            
            # Display character responses
            if character_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]ADVISOR REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("ADVISOR REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for char_name, response in character_responses:
                    if RICH_ENABLED:
                        console.print(f"[{COLORS['secondary']} bold]{char_name}:[/{COLORS['secondary']} bold]")
                        console.print(f"  \"{response}\"")
                    else:
                        typer.echo(f"{char_name}:")
                        typer.echo(f"  \"{response}\"")
                    typer.echo("")
            
            # Display international reactions (multi-agent simulation)
            if actor_responses:
                if RICH_ENABLED:
                    console.print(f"[{COLORS['accent']} bold]INTERNATIONAL REACTIONS[/]")
                    console.print(f"[{COLORS['accent']}]" + "═" * 60 + f"[/{COLORS['accent']}]")
                else:
                    typer.echo("=" * 60)
                    typer.echo("INTERNATIONAL REACTIONS")
                    typer.echo("=" * 60)
                typer.echo("")
                
                for response in actor_responses:
                    trust_delta = response.trust_change
                    actor_id = response.actor_id
                    
                    # Get full name if available
                    actor_name = actor_id
                    if world.actor_system:
                        actor = world.actor_system.get_actor(actor_id)
                        if actor:
                            actor_name = actor.full_name
                    
                    if RICH_ENABLED:
                        color = COLORS['success'] if trust_delta > 0 else COLORS['danger'] if trust_delta < 0 else COLORS['muted']
                        console.print(f"[{COLORS['primary']} bold]{actor_name}:[/{COLORS['primary']} bold] [{color}]({trust_delta:+d})[/{color}]")
                        console.print(f"  \"{response.public_response}\"")
                    else:
                        typer.echo(f"{actor_name}: ({trust_delta:+d})")
                        typer.echo(f"  \"{response.public_response}\"")
                    typer.echo("")
            
            # Sync world metrics with narrative state (keep both in sync)
            world.metrics.escalation_risk = narrative_state.hidden_metrics.escalation_risk
            world.metrics.domestic_stability = narrative_state.hidden_metrics.domestic_stability
            world.metrics.alliance_cohesion = narrative_state.hidden_metrics.alliance_cohesion
            world.metrics.casualties_mil = narrative_state.hidden_metrics.casualties_mil
            world.metrics.casualties_civ = narrative_state.hidden_metrics.casualties_civ
            
            # Build transcript for save file
            adjudication_lines = [
                "Action Assessment:",
                reasoning,
                "",
                "Effects:"
            ]
            for metric, delta in final_effects.items():
                adjudication_lines.append(f"  {metric}: {delta:+d}")
            adjudication_lines.append("")
            
            if character_responses:
                adjudication_lines.append("Advisor Reactions:")
                for char_name, response in character_responses:
                    adjudication_lines.append(f"{char_name}: \"{response}\"")
                adjudication_lines.append("")
                
            if actor_responses:
                adjudication_lines.append("International Reactions:")
                for response in actor_responses:
                    adjudication_lines.append(f"{response.actor_id}: \"{response.public_response}\"")
                adjudication_lines.append("")
            
            transcript.extend(adjudication_lines)
        
        except Exception as e:
            # Fallback to primitive system on error
            if RICH_ENABLED:
                console.print(f"[{COLORS['warning']}][WARNING] LLM adjudication failed: {e}[/{COLORS['warning']}]")
                console.print(f"[{COLORS['warning']}][INFO] Falling back to keyword-based adjudication[/{COLORS['warning']}]")
            else:
                typer.echo(f"[WARNING] LLM adjudication failed: {e}")
                typer.echo("[INFO] Falling back to keyword-based adjudication")
            typer.echo("")
            
            adjudication_lines = run_turn_adjudication_fallback(world, action, interpretation, rng)
            for line in adjudication_lines:
                typer.echo(line)
            transcript.extend(adjudication_lines)
            
            # Sync narrative state from world (reverse sync in fallback mode)
            narrative_state.update_hidden_metrics({
                "escalation_risk": world.metrics.escalation_risk,
                "domestic_stability": world.metrics.domestic_stability,
                "alliance_cohesion": world.metrics.alliance_cohesion,
                "casualties_mil": world.metrics.casualties_mil,
                "casualties_civ": world.metrics.casualties_civ
            })
        
        # Narrative state turn already updated by adjudicate_with_narrative()
        narrative_state.turn = world.turn
        
        # Display based on play mode
        typer.echo("")
        if play_mode == "classic":
            # Classic mode: Show raw metrics with deltas
            if RICH_ENABLED:
                console.print(metrics_table(world, show_deltas=True, previous_metrics=turn_start_metrics))
                typer.echo("")  # Buffer after table
        elif play_mode == "immersive":
            # Immersive mode: Show vibes + character attitudes
            typer.echo("═" * 60)
            typer.echo("SITUATION ASSESSMENT")
            typer.echo("═" * 60)
            typer.echo("")
            
            vibes = narrative_state.get_situation_vibes()
            for vibe in vibes:
                typer.echo(vibe.to_string())
            
            typer.echo("")
            typer.echo("═" * 60)
            typer.echo("ADVISOR ATTITUDES")
            typer.echo("═" * 60)
            typer.echo("")
            
            for char_id, char_attitude in narrative_state.characters.items():
                # Create visual trust bar
                trust_level = char_attitude.trust // 20  # 0-5 scale
                trust_bar = "█" * trust_level + "░" * (5 - trust_level)
                relationship_symbol = {
                    "allied": "✓",
                    "neutral": "○",
                    "hostile": "✗",
                    "unknown": "?"
                }.get(char_attitude.relationship, "○")
                
                typer.echo(f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}")
            
            typer.echo("")
        elif play_mode == "emergent":
            # Emergent mode: Narrative summary only
            typer.echo("═" * 60)
            typer.echo(narrative_state.situation_summary)
            typer.echo("═" * 60)
            typer.echo("")
        
        # Auto-save after each turn
        save_path = save_game(world, transcript, scenario, "autosave", root, play_mode, narrative_state)
        
        # Advance turn
        world.turn += 1
        world.scene = world.turn  # Keep scene in sync for legacy compatibility
        world.discussion_transcript = []
        
        typer.echo("")
        typer.echo("=" * 60)
        typer.echo(f"Turn {world.turn - 1} complete. Auto-saved to {save_path.name}")
        typer.echo("=" * 60)
        typer.echo("")
        
        # Continue to next turn with spacebar
        try:
            wait_for_space("Press SPACE to continue to next turn (or Ctrl+C to exit)...")
        except KeyboardInterrupt:
            typer.echo("\nGame paused. Use --load to resume.")
            break


@app.command(rich_help_panel="GAMEPLAY")
def batch(
    scenario: str = typer.Option("war_game_2025", help="Scenario identifier"),
    seed: int = typer.Option(42, help="Random seed"),
    action: str = typer.Option("Deploy defensive forces", help="Action to take"),
):
    """Run a single turn in batch mode (for testing)."""
    
    transcript = run_single_scene(scenario, seed, "llm")
    for line in transcript:
        typer.echo(line)


@app.command(rich_help_panel="UTILITY")
def settings():
    """Configure LLM model settings (Flash vs Pro per system)."""
    console.print("\n[bold cyan]LLM Model Settings[/bold cyan]\n")
    console.print("Configure which systems use Flash (fast/cheap) vs Pro (sophisticated/expensive)\n")
    
    model_settings_menu()


@app.command(rich_help_panel="UTILITY")
def intro():
    """Display the intro text."""
    for line in get_intro_lines(200):
        typer.echo(line)


if __name__ == "__main__":
    app()

```

Excellent! Now let me check for any linter errors:

Perfect! No linter errors. Now let's test that the dashboard CLI works:

We need to activate the Python environment first. Let me check for a virtual environment:

Let me test if the original CLI works first (to verify the environment is set up):

The dependencies aren't installed. Let me check the requirements and install them:

Excellent! Dependencies installed. Now let's test the dashboard CLI:

There's an indentation error in `rich_ui.py`. Let me fix that:

```python
"""Rich UI components for enhanced CLI display.

Provides professional ASCII-only tables, panels, and formatting while preserving
compatibility with existing narrative scrolling and keyboard systems.
"""

import os
import sys
from typing import Optional, Any, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich import box

from cli.theme import theme_manager, SYMBOLS, BOX, WIDTH, progress_bar
from cli.formatters import format_metric_status

# Environment variable killswitch for instant rollback
RICH_ENABLED = os.getenv("WARGAME_RICH_UI", "true").lower() == "true"

# Initialize console with Windows compatibility
# CRITICAL: force_interactive=False to preserve msvcrt.kbhit() behavior
console = Console(
    legacy_windows=(sys.platform == "win32"),
    force_terminal=True,
    force_interactive=False,  # Essential for SPACE-to-skip!
    color_system="windows" if sys.platform == "win32" else "auto"  # Force Windows colour support
)


def phase_header(phase_name: str, turn: int) -> str:
    """Generate clean phase header with ASCII rounded box.
    
    Args:
        phase_name: Name of phase (BRIEFING, DISCUSSION, DECISION, ADJUDICATION)
        turn: Current turn number
        
    Returns:
        Formatted header string or Panel object
    """
    if not RICH_ENABLED:
        return f"TURN {turn}: {phase_name} PHASE"
    
    # Get dynamic colors
    COLORS = theme_manager.get_colors()
    
    # Phase colors
    phase_colors = {
        "BRIEFING": COLORS["accent"],
        "DISCUSSION": COLORS["primary"],
        "DECISION": "magenta",
        "ADJUDICATION": COLORS["success"]
    }
    
    color = phase_colors.get(phase_name, COLORS["success"]) # Default fallback safe color
    
    return Panel(
        f"[bold]TURN {turn} │ {phase_name} PHASE[/bold]",
        style=f"{color}",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False
    )


def metrics_table(world, show_deltas: bool = False, 
                  previous_metrics: Optional[Any] = None) -> Table:
    """Generate professional metrics display with ASCII symbols and bars.
    
    Args:
        world: WorldState object
        show_deltas: If True and previous_metrics provided, show changes
        previous_metrics: Previous Metrics object for delta calculation
        
    Returns:
        Rich Table object or plain string if Rich disabled
    """
    if not RICH_ENABLED:
        # Fallback to plain text
        lines = []
        lines.append(f"Turn: {world.turn}")
        lines.append(f"Phase: {world.phase}")
        lines.append(f"Escalation Risk: {world.metrics.escalation_risk}/100")
        lines.append(f"Domestic Stability: {world.metrics.domestic_stability}/100")
        lines.append(f"Alliance Cohesion: {world.metrics.alliance_cohesion}/100")
        lines.append(f"Military Casualties: {world.metrics.casualties_mil}")
        lines.append(f"Civilian Casualties: {world.metrics.casualties_civ}")
        return "\n".join(lines)
    
    COLORS = theme_manager.get_colors()
    
    # Title with turn and phase
    phase_display = world.phase.upper() if hasattr(world, 'phase') else "UNKNOWN"
    title = f"[{COLORS['accent']} bold]SITUATION REPORT │ Turn {world.turn} │ {phase_display} PHASE[/{COLORS['accent']} bold]"
    
    table = Table(title=title, border_style=COLORS["secondary"], show_header=True, padding=(0, 1), box=box.ROUNDED)
    table.add_column("", style=COLORS["secondary"], no_wrap=True, width=3)  # Symbol
    table.add_column("Metric", style=COLORS["normal"], no_wrap=True)
    table.add_column("Value", justify="right", style=COLORS["normal"], width=6)
    table.add_column("Bar", justify="left", width=12)
    table.add_column("Status", justify="left", style=COLORS["normal"], width=10)
    
    if show_deltas and previous_metrics:
        table.add_column("Change", justify="right", style=COLORS["warning"], width=8)
    
    def format_risk_value(value: int) -> str:
        """Color-code risk value (high is bad)."""
        if value >= 70:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value >= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_stability_value(value: int) -> str:
        """Color-code stability/cohesion value (low is bad)."""
        if value <= 30:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value <= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_delta(delta: int) -> str:
        """Format delta with color and sign."""
        if delta > 0:
            return f"[{COLORS['success']}]+{delta}[/{COLORS['success']}]"
        elif delta < 0:
            return f"[{COLORS['danger']}]{delta}[/{COLORS['danger']}]"
        else:
            return f"[{COLORS['muted']}]±0[/{COLORS['muted']}]"
    
    # Escalation Risk (high is bad)
    risk_val = world.metrics.escalation_risk
    risk_str = format_risk_value(risk_val)
    risk_bar = progress_bar(risk_val, 100, 10)
    risk_status = format_metric_status(risk_val, 'risk')
    
    row = [SYMBOLS["risk"], "Escalation Risk", risk_str, risk_bar, risk_status]
    if show_deltas and previous_metrics:
        delta = risk_val - previous_metrics.escalation_risk
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Domestic Stability (low is bad)
    stability_val = world.metrics.domestic_stability
    stability_str = format_stability_value(stability_val)
    stability_bar = progress_bar(stability_val, 100, 10)
    stability_status = format_metric_status(stability_val, 'stability')
    
    row = [SYMBOLS["stability"], "Domestic Stability", stability_str, stability_bar, stability_status]
    if show_deltas and previous_metrics:
        delta = stability_val - previous_metrics.domestic_stability
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Alliance Cohesion (low is bad)
    cohesion_val = world.metrics.alliance_cohesion
    cohesion_str = format_stability_value(cohesion_val)
    cohesion_bar = progress_bar(cohesion_val, 100, 10)
    cohesion_status = format_metric_status(cohesion_val, 'cohesion')
    
    row = [SYMBOLS["cohesion"], "Alliance Cohesion", cohesion_str, cohesion_bar, cohesion_status]
    if show_deltas and previous_metrics:
        delta = cohesion_val - previous_metrics.alliance_cohesion
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Casualties
    casualties_total = world.metrics.casualties_mil + world.metrics.casualties_civ
    casualties_str = f"{casualties_total}"
    casualties_detail = f"{world.metrics.casualties_mil} mil │ {world.metrics.casualties_civ} civ"
    
    row = [SYMBOLS["casualties"], "Casualties", casualties_str, casualties_detail, ""]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for casualties
    table.add_row(*row)
    
    # Calculate and add influence
    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
    influence = int((influence_raw - 50) / 5)
    influence = max(-10, min(10, influence))
    
    # Color-code influence
    if influence >= 5:
        influence_str = f"[{COLORS['metric_good']}]+{influence}[/{COLORS['metric_good']}]"
    elif influence >= 0:
        influence_str = f"[{COLORS['metric_neutral']}]+{influence}[/{COLORS['metric_neutral']}]"
    elif influence >= -5:
        influence_str = f"[{COLORS['metric_bad']}]{influence}[/{COLORS['metric_bad']}]"
    else:
        influence_str = f"[{COLORS['metric_critical']}]{influence}[/{COLORS['metric_critical']}]"
    
    influence_status = format_metric_status(influence, 'influence')
    
    row = [SYMBOLS["influence"], "Influence", influence_str, "", influence_status]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for influence (it's derived)
    table.add_row(*row)
    
    return table


def advisor_menu_panel() -> Panel:
    """Generate formatted advisor hierarchy panel using Tree view.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Use /menu to see advisor list"
    
    COLORS = theme_manager.get_colors()
    
    # Create tree structure
    tree = Tree(f"[{COLORS['accent']} bold]COBRA CABINET STRUCTURE[/]", guide_style=COLORS['secondary'])
    
    # Strategic/Intel Node
    strategic = tree.add(f"[{COLORS['primary']} bold]Strategic & Intelligence[/]")
    strategic.add(f"[{COLORS['highlight']}]National Security Advisor (NSA)[/]\n[dim]Threat analysis, strategic coordination[/]")
    
    # Military Node
    military = tree.add(f"[{COLORS['danger']} bold]Military Operations[/]")
    military.add(f"[{COLORS['highlight']}]Chief of the Defence Staff (CDS)[/]\n[dim]Force deployment, military options[/]")
    
    # Diplomatic Node
    diplomatic = tree.add(f"[{COLORS['success']} bold]Foreign Affairs[/]")
    diplomatic.add(f"[{COLORS['highlight']}]Foreign Secretary[/]\n[dim]Diplomacy, alliances, NATO[/]")
        
    # Domestic/Legal Node
    domestic = tree.add(f"[{COLORS['warning']} bold]Domestic & Legal[/]")
    domestic.add(f"[{COLORS['highlight']}]Home Secretary[/]\n[dim]Civil order, public messaging[/]")
    domestic.add(f"[{COLORS['highlight']}]Attorney General[/]\n[dim]Legal frameworks, international law[/]")
    
    return Panel(
        tree,
        title=f"[{COLORS['accent']} bold]ADVISOR HIERARCHY[/]",
        border_style=COLORS['accent'],
        box=box.ROUNDED,
        padding=(1, 2)
    )


def diplomatic_contacts_table(contacts: List[Tuple[str, str, str]]) -> Panel:
    """Generate diplomatic contacts panel using a tree view.
    
    Args:
        contacts: List of (country, access_level, title) tuples
        
    Returns:
        Rich Panel object with Tree
    """
    if not RICH_ENABLED:
        return "Diplomatic contacts available"
    
    COLORS = theme_manager.get_colors()
    
    if not contacts:
        return Panel(
            f"[{COLORS['muted']}]No diplomatic contacts available (Alliance Cohesion too low)[/]",
            title=f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/]",
            border_style=COLORS['success'],
            box=box.ROUNDED
        )
    
    # Define groupings
    alliances = {
        "NATO Allies": ["US", "France", "Germany", "Poland"],
        "Adversaries": ["Russia"],
        "Partners & Others": ["Ukraine", "Ireland"]
    }
    
    tree = Tree(f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/{COLORS['success']} bold]", guide_style=COLORS['secondary'])
    
    # Create nodes
    nodes = {
        "NATO Allies": tree.add(f"[{COLORS['secondary']} bold]NATO Alliance[/]"),
        "Adversaries": tree.add(f"[{COLORS['danger']} bold]Adversaries[/]"),
        "Partners & Others": tree.add(f"[{COLORS['muted']} bold]Partners & Others[/]")
    }
    
    # Sort contacts to ensure consistent order
    contacts.sort(key=lambda x: x[0])
    
    for country, access_level, title in contacts:
        # Determine group
        group = "Partners & Others"
        for g_name, countries in alliances.items():
            if country in countries:
                group = g_name
                break
        
        # Format status
            if access_level == "leader":
                marker = SYMBOLS["leader"]
            status = f"[{COLORS['warning']}]LEADER[/]"
            else:
                marker = SYMBOLS["diplomat"]
            status = f"[{COLORS['muted']}]DIPLOMAT[/]"
            
        # Add to appropriate node
        # Format: [Symbol] Country: Title (STATUS) -> /command
        nodes[group].add(
            f"{marker} {country}: {title} ({status})  [{COLORS['primary']}]/call {country.lower()}[/]"
        )
    
    # Remove empty nodes
    # Rich Tree doesn't support easy removal, so we rebuild if we want to be clean,
    # or just leave them (showing empty categories is fine for info).
    # Let's leave them to show structure.
    
    return Panel(
        tree,
        title=f"[{COLORS['success']} bold]SECURE LINES[/]",
        border_style=COLORS['success'],
        box=box.ROUNDED,
        padding=(0, 1)
    )


def resources_tables(initial_conditions: dict) -> Tuple[Table, Table]:
    """Generate forces and stockpiles tables.
    
    Args:
        initial_conditions: Initial conditions dict with uk_forces and stockpiles
        
    Returns:
        Tuple of (forces_table, stockpiles_table)
    """
    if not RICH_ENABLED:
        return ("UK Forces", "UK Stockpiles")
    
    COLORS = theme_manager.get_colors()
    
    # Forces table
    forces_table = Table(
        title=f"[{COLORS['accent']} bold]UK MILITARY FORCES[/{COLORS['accent']} bold]",
        border_style=COLORS["secondary"],
        show_header=True,
        box=box.ROUNDED
    )
    forces_table.add_column("Unit", style=COLORS["secondary"], no_wrap=True)
    forces_table.add_column("Type", style=COLORS["normal"])
    forces_table.add_column("Location", style=COLORS["muted"])
    forces_table.add_column("Status", style=COLORS["normal"])
    
    uk_forces = initial_conditions.get("uk_forces", {})
    
    # Naval forces
    for unit in uk_forces.get("naval", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Air forces
    for unit in uk_forces.get("air", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Add aircraft count if present
        aircraft_count = unit.get("aircraft_count")
        operational_aircraft = unit.get("operational_aircraft")
        if aircraft_count is not None:
            if operational_aircraft is not None:
                unit_type += f" ({operational_aircraft}/{aircraft_count})"
            else:
                unit_type += f" ({aircraft_count})"
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower() or "reduced" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Stockpiles table (USING TREE STRUCTURE NOW)
    stockpiles = initial_conditions.get("stockpiles", {})
    
    stock_tree = Tree(
        f"[{COLORS['accent']} bold]AMMUNITION STOCKPILES[/{COLORS['accent']} bold]",
        guide_style=COLORS['secondary']
    )
    
    # Group stockpiles by category
    categories = [
        ("Air Defence", ["aster_15", "aster_30", "sea_ceptor"]),
        ("Naval Strike", ["tomahawk_cruise_missiles", "harpoon_anti_ship"]),
        ("Air-Launched", ["storm_shadow_cruise_missiles", "paveway_laser_guided_bombs"]),
        ("Anti-Submarine", ["spearfish_torpedoes", "stingray_lightweight_torpedoes"]),
    ]
    
    for category, weapons in categories:
        cat_node = stock_tree.add(f"[{COLORS['emphasis']}]{category}[/]")
        
        for weapon_key in weapons:
            weapon_data = stockpiles.get(weapon_key, {})
            if weapon_data:
                name = weapon_key.replace('_', ' ').title()
                count = weapon_data.get("count", 0)
                note = weapon_data.get("note", "")
                
                # Color-code count
                if count >= 100:
                    count_colored = f"[{COLORS['success']}]{count}[/{COLORS['success']}]"
                elif count >= 50:
                    count_colored = f"[{COLORS['warning']}]{count}[/{COLORS['warning']}]"
                else:
                    count_colored = f"[{COLORS['danger']}]{count}[/{COLORS['danger']}]"
                
                cat_node.add(f"{name}: {count_colored} [italic muted]({note})[/]")
    
    # Return formatted panel instead of table for consistency
    stockpiles_panel = Panel(
        stock_tree,
        border_style=COLORS["secondary"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    return (forces_table, stockpiles_panel)


def command_menu() -> Panel:
    """Generate command reference menu.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Commands: /status /menu /advise /resources /call /decide /save /quit"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Command", style=COLORS['primary'])
    table.add_column("Description", style=COLORS['muted'])
    
    # Commands
    commands = [
        ("/status", "Show current metrics and situation"),
        ("/menu", "Display this help"),
        ("/advise", "Get input from all advisors"),
        ("/resources", "View UK forces and stockpiles"),
        ("/call <country>", "Contact foreign leader"),
        ("/decide", "Make your decision"),
        ("/theme", "Change UI color theme"),
        ("/llm", "Configure LLM model settings (Pro/Flash)"),
        ("/save", "Save game"),
        ("/quit", "Exit game"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return Panel(
        table,
        title="[magenta bold]COMMANDS[/]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2)
    )


def metrics_guide_panel() -> Panel:
    """Generate metrics explanation panel.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Metrics guide available in /menu"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Metric", style=f"{COLORS['secondary']} bold", ratio=1)
    table.add_column("Description", style=COLORS['muted'], ratio=2)
    
    # Metrics
    metrics = [
        (f"{SYMBOLS['risk']} Escalation Risk", 
         "Likelihood of full-scale war.\n[bold]HIGH = Danger[/]"),
        (f"{SYMBOLS['stability']} Domestic Stability",
         "Public confidence & economy.\n[bold]LOW = Unrest[/]"),
        (f"{SYMBOLS['cohesion']} Alliance Cohesion",
         "NATO solidarity.\n[bold]LOW = Isolation[/]"),
        (f"{SYMBOLS['influence']} Influence",
         "Political capital.\nDerived from Stability + Cohesion"),
    ]
    
    for name, desc in metrics:
        table.add_row(name, desc)
        table.add_row("", "") # Spacer
        
    return Panel(
        table,
        title=f"[{COLORS['warning']} bold]METRICS GUIDE[/]",
        border_style=COLORS['warning'],
        box=box.ROUNDED,
        padding=(0, 2)
    )

```

```python
"""Rich UI components for enhanced CLI display.

Provides professional ASCII-only tables, panels, and formatting while preserving
compatibility with existing narrative scrolling and keyboard systems.
"""

import os
import sys
from typing import Optional, Any, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich import box

from cli.theme import theme_manager, SYMBOLS, BOX, WIDTH, progress_bar
from cli.formatters import format_metric_status

# Environment variable killswitch for instant rollback
RICH_ENABLED = os.getenv("WARGAME_RICH_UI", "true").lower() == "true"

# Initialize console with Windows compatibility
# CRITICAL: force_interactive=False to preserve msvcrt.kbhit() behavior
console = Console(
    legacy_windows=(sys.platform == "win32"),
    force_terminal=True,
    force_interactive=False,  # Essential for SPACE-to-skip!
    color_system="windows" if sys.platform == "win32" else "auto"  # Force Windows colour support
)


def phase_header(phase_name: str, turn: int) -> str:
    """Generate clean phase header with ASCII rounded box.
    
    Args:
        phase_name: Name of phase (BRIEFING, DISCUSSION, DECISION, ADJUDICATION)
        turn: Current turn number
        
    Returns:
        Formatted header string or Panel object
    """
    if not RICH_ENABLED:
        return f"TURN {turn}: {phase_name} PHASE"
    
    # Get dynamic colors
    COLORS = theme_manager.get_colors()
    
    # Phase colors
    phase_colors = {
        "BRIEFING": COLORS["accent"],
        "DISCUSSION": COLORS["primary"],
        "DECISION": "magenta",
        "ADJUDICATION": COLORS["success"]
    }
    
    color = phase_colors.get(phase_name, COLORS["success"]) # Default fallback safe color
    
    return Panel(
        f"[bold]TURN {turn} │ {phase_name} PHASE[/bold]",
        style=f"{color}",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False
    )


def metrics_table(world, show_deltas: bool = False, 
                  previous_metrics: Optional[Any] = None) -> Table:
    """Generate professional metrics display with ASCII symbols and bars.
    
    Args:
        world: WorldState object
        show_deltas: If True and previous_metrics provided, show changes
        previous_metrics: Previous Metrics object for delta calculation
        
    Returns:
        Rich Table object or plain string if Rich disabled
    """
    if not RICH_ENABLED:
        # Fallback to plain text
        lines = []
        lines.append(f"Turn: {world.turn}")
        lines.append(f"Phase: {world.phase}")
        lines.append(f"Escalation Risk: {world.metrics.escalation_risk}/100")
        lines.append(f"Domestic Stability: {world.metrics.domestic_stability}/100")
        lines.append(f"Alliance Cohesion: {world.metrics.alliance_cohesion}/100")
        lines.append(f"Military Casualties: {world.metrics.casualties_mil}")
        lines.append(f"Civilian Casualties: {world.metrics.casualties_civ}")
        return "\n".join(lines)
    
    COLORS = theme_manager.get_colors()
    
    # Title with turn and phase
    phase_display = world.phase.upper() if hasattr(world, 'phase') else "UNKNOWN"
    title = f"[{COLORS['accent']} bold]SITUATION REPORT │ Turn {world.turn} │ {phase_display} PHASE[/{COLORS['accent']} bold]"
    
    table = Table(title=title, border_style=COLORS["secondary"], show_header=True, padding=(0, 1), box=box.ROUNDED)
    table.add_column("", style=COLORS["secondary"], no_wrap=True, width=3)  # Symbol
    table.add_column("Metric", style=COLORS["normal"], no_wrap=True)
    table.add_column("Value", justify="right", style=COLORS["normal"], width=6)
    table.add_column("Bar", justify="left", width=12)
    table.add_column("Status", justify="left", style=COLORS["normal"], width=10)
    
    if show_deltas and previous_metrics:
        table.add_column("Change", justify="right", style=COLORS["warning"], width=8)
    
    def format_risk_value(value: int) -> str:
        """Color-code risk value (high is bad)."""
        if value >= 70:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value >= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_stability_value(value: int) -> str:
        """Color-code stability/cohesion value (low is bad)."""
        if value <= 30:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value <= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_delta(delta: int) -> str:
        """Format delta with color and sign."""
        if delta > 0:
            return f"[{COLORS['success']}]+{delta}[/{COLORS['success']}]"
        elif delta < 0:
            return f"[{COLORS['danger']}]{delta}[/{COLORS['danger']}]"
        else:
            return f"[{COLORS['muted']}]±0[/{COLORS['muted']}]"
    
    # Escalation Risk (high is bad)
    risk_val = world.metrics.escalation_risk
    risk_str = format_risk_value(risk_val)
    risk_bar = progress_bar(risk_val, 100, 10)
    risk_status = format_metric_status(risk_val, 'risk')
    
    row = [SYMBOLS["risk"], "Escalation Risk", risk_str, risk_bar, risk_status]
    if show_deltas and previous_metrics:
        delta = risk_val - previous_metrics.escalation_risk
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Domestic Stability (low is bad)
    stability_val = world.metrics.domestic_stability
    stability_str = format_stability_value(stability_val)
    stability_bar = progress_bar(stability_val, 100, 10)
    stability_status = format_metric_status(stability_val, 'stability')
    
    row = [SYMBOLS["stability"], "Domestic Stability", stability_str, stability_bar, stability_status]
    if show_deltas and previous_metrics:
        delta = stability_val - previous_metrics.domestic_stability
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Alliance Cohesion (low is bad)
    cohesion_val = world.metrics.alliance_cohesion
    cohesion_str = format_stability_value(cohesion_val)
    cohesion_bar = progress_bar(cohesion_val, 100, 10)
    cohesion_status = format_metric_status(cohesion_val, 'cohesion')
    
    row = [SYMBOLS["cohesion"], "Alliance Cohesion", cohesion_str, cohesion_bar, cohesion_status]
    if show_deltas and previous_metrics:
        delta = cohesion_val - previous_metrics.alliance_cohesion
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Casualties
    casualties_total = world.metrics.casualties_mil + world.metrics.casualties_civ
    casualties_str = f"{casualties_total}"
    casualties_detail = f"{world.metrics.casualties_mil} mil │ {world.metrics.casualties_civ} civ"
    
    row = [SYMBOLS["casualties"], "Casualties", casualties_str, casualties_detail, ""]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for casualties
    table.add_row(*row)
    
    # Calculate and add influence
    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
    influence = int((influence_raw - 50) / 5)
    influence = max(-10, min(10, influence))
    
    # Color-code influence
    if influence >= 5:
        influence_str = f"[{COLORS['metric_good']}]+{influence}[/{COLORS['metric_good']}]"
    elif influence >= 0:
        influence_str = f"[{COLORS['metric_neutral']}]+{influence}[/{COLORS['metric_neutral']}]"
    elif influence >= -5:
        influence_str = f"[{COLORS['metric_bad']}]{influence}[/{COLORS['metric_bad']}]"
    else:
        influence_str = f"[{COLORS['metric_critical']}]{influence}[/{COLORS['metric_critical']}]"
    
    influence_status = format_metric_status(influence, 'influence')
    
    row = [SYMBOLS["influence"], "Influence", influence_str, "", influence_status]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for influence (it's derived)
    table.add_row(*row)
    
    return table


def advisor_menu_panel() -> Panel:
    """Generate formatted advisor hierarchy panel using Tree view.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Use /menu to see advisor list"
    
    COLORS = theme_manager.get_colors()
    
    # Create tree structure
    tree = Tree(f"[{COLORS['accent']} bold]COBRA CABINET STRUCTURE[/]", guide_style=COLORS['secondary'])
    
    # Strategic/Intel Node
    strategic = tree.add(f"[{COLORS['primary']} bold]Strategic & Intelligence[/]")
    strategic.add(f"[{COLORS['highlight']}]National Security Advisor (NSA)[/]\n[dim]Threat analysis, strategic coordination[/]")
    
    # Military Node
    military = tree.add(f"[{COLORS['danger']} bold]Military Operations[/]")
    military.add(f"[{COLORS['highlight']}]Chief of the Defence Staff (CDS)[/]\n[dim]Force deployment, military options[/]")
    
    # Diplomatic Node
    diplomatic = tree.add(f"[{COLORS['success']} bold]Foreign Affairs[/]")
    diplomatic.add(f"[{COLORS['highlight']}]Foreign Secretary[/]\n[dim]Diplomacy, alliances, NATO[/]")
        
    # Domestic/Legal Node
    domestic = tree.add(f"[{COLORS['warning']} bold]Domestic & Legal[/]")
    domestic.add(f"[{COLORS['highlight']}]Home Secretary[/]\n[dim]Civil order, public messaging[/]")
    domestic.add(f"[{COLORS['highlight']}]Attorney General[/]\n[dim]Legal frameworks, international law[/]")
    
    return Panel(
        tree,
        title=f"[{COLORS['accent']} bold]ADVISOR HIERARCHY[/]",
        border_style=COLORS['accent'],
        box=box.ROUNDED,
        padding=(1, 2)
    )


def diplomatic_contacts_table(contacts: List[Tuple[str, str, str]]) -> Panel:
    """Generate diplomatic contacts panel using a tree view.
    
    Args:
        contacts: List of (country, access_level, title) tuples
        
    Returns:
        Rich Panel object with Tree
    """
    if not RICH_ENABLED:
        return "Diplomatic contacts available"
    
    COLORS = theme_manager.get_colors()
    
    if not contacts:
        return Panel(
            f"[{COLORS['muted']}]No diplomatic contacts available (Alliance Cohesion too low)[/]",
            title=f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/]",
            border_style=COLORS['success'],
            box=box.ROUNDED
        )
    
    # Define groupings
    alliances = {
        "NATO Allies": ["US", "France", "Germany", "Poland"],
        "Adversaries": ["Russia"],
        "Partners & Others": ["Ukraine", "Ireland"]
    }
    
    tree = Tree(f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/{COLORS['success']} bold]", guide_style=COLORS['secondary'])
    
    # Create nodes
    nodes = {
        "NATO Allies": tree.add(f"[{COLORS['secondary']} bold]NATO Alliance[/]"),
        "Adversaries": tree.add(f"[{COLORS['danger']} bold]Adversaries[/]"),
        "Partners & Others": tree.add(f"[{COLORS['muted']} bold]Partners & Others[/]")
    }
    
    # Sort contacts to ensure consistent order
    contacts.sort(key=lambda x: x[0])
    
    for country, access_level, title in contacts:
        # Determine group
        group = "Partners & Others"
        for g_name, countries in alliances.items():
            if country in countries:
                group = g_name
                break
        
        # Format status
        if access_level == "leader":
            marker = SYMBOLS["leader"]
            status = f"[{COLORS['warning']}]LEADER[/]"
        else:
            marker = SYMBOLS["diplomat"]
            status = f"[{COLORS['muted']}]DIPLOMAT[/]"
            
        # Add to appropriate node
        # Format: [Symbol] Country: Title (STATUS) -> /command
        nodes[group].add(
            f"{marker} {country}: {title} ({status})  [{COLORS['primary']}]/call {country.lower()}[/]"
        )
    
    # Remove empty nodes
    # Rich Tree doesn't support easy removal, so we rebuild if we want to be clean,
    # or just leave them (showing empty categories is fine for info).
    # Let's leave them to show structure.
    
    return Panel(
        tree,
        title=f"[{COLORS['success']} bold]SECURE LINES[/]",
        border_style=COLORS['success'],
        box=box.ROUNDED,
        padding=(0, 1)
    )


def resources_tables(initial_conditions: dict) -> Tuple[Table, Table]:
    """Generate forces and stockpiles tables.
    
    Args:
        initial_conditions: Initial conditions dict with uk_forces and stockpiles
        
    Returns:
        Tuple of (forces_table, stockpiles_table)
    """
    if not RICH_ENABLED:
        return ("UK Forces", "UK Stockpiles")
    
    COLORS = theme_manager.get_colors()
    
    # Forces table
    forces_table = Table(
        title=f"[{COLORS['accent']} bold]UK MILITARY FORCES[/{COLORS['accent']} bold]",
        border_style=COLORS["secondary"],
        show_header=True,
        box=box.ROUNDED
    )
    forces_table.add_column("Unit", style=COLORS["secondary"], no_wrap=True)
    forces_table.add_column("Type", style=COLORS["normal"])
    forces_table.add_column("Location", style=COLORS["muted"])
    forces_table.add_column("Status", style=COLORS["normal"])
    
    uk_forces = initial_conditions.get("uk_forces", {})
    
    # Naval forces
    for unit in uk_forces.get("naval", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Air forces
    for unit in uk_forces.get("air", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Add aircraft count if present
        aircraft_count = unit.get("aircraft_count")
        operational_aircraft = unit.get("operational_aircraft")
        if aircraft_count is not None:
            if operational_aircraft is not None:
                unit_type += f" ({operational_aircraft}/{aircraft_count})"
            else:
                unit_type += f" ({aircraft_count})"
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower() or "reduced" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Stockpiles table (USING TREE STRUCTURE NOW)
    stockpiles = initial_conditions.get("stockpiles", {})
    
    stock_tree = Tree(
        f"[{COLORS['accent']} bold]AMMUNITION STOCKPILES[/{COLORS['accent']} bold]",
        guide_style=COLORS['secondary']
    )
    
    # Group stockpiles by category
    categories = [
        ("Air Defence", ["aster_15", "aster_30", "sea_ceptor"]),
        ("Naval Strike", ["tomahawk_cruise_missiles", "harpoon_anti_ship"]),
        ("Air-Launched", ["storm_shadow_cruise_missiles", "paveway_laser_guided_bombs"]),
        ("Anti-Submarine", ["spearfish_torpedoes", "stingray_lightweight_torpedoes"]),
    ]
    
    for category, weapons in categories:
        cat_node = stock_tree.add(f"[{COLORS['emphasis']}]{category}[/]")
        
        for weapon_key in weapons:
            weapon_data = stockpiles.get(weapon_key, {})
            if weapon_data:
                name = weapon_key.replace('_', ' ').title()
                count = weapon_data.get("count", 0)
                note = weapon_data.get("note", "")
                
                # Color-code count
                if count >= 100:
                    count_colored = f"[{COLORS['success']}]{count}[/{COLORS['success']}]"
                elif count >= 50:
                    count_colored = f"[{COLORS['warning']}]{count}[/{COLORS['warning']}]"
                else:
                    count_colored = f"[{COLORS['danger']}]{count}[/{COLORS['danger']}]"
                
                cat_node.add(f"{name}: {count_colored} [italic muted]({note})[/]")
    
    # Return formatted panel instead of table for consistency
    stockpiles_panel = Panel(
        stock_tree,
        border_style=COLORS["secondary"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    return (forces_table, stockpiles_panel)


def command_menu() -> Panel:
    """Generate command reference menu.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Commands: /status /menu /advise /resources /call /decide /save /quit"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Command", style=COLORS['primary'])
    table.add_column("Description", style=COLORS['muted'])
    
    # Commands
    commands = [
        ("/status", "Show current metrics and situation"),
        ("/menu", "Display this help"),
        ("/advise", "Get input from all advisors"),
        ("/resources", "View UK forces and stockpiles"),
        ("/call <country>", "Contact foreign leader"),
        ("/decide", "Make your decision"),
        ("/theme", "Change UI color theme"),
        ("/llm", "Configure LLM model settings (Pro/Flash)"),
        ("/save", "Save game"),
        ("/quit", "Exit game"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return Panel(
        table,
        title="[magenta bold]COMMANDS[/]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2)
    )


def metrics_guide_panel() -> Panel:
    """Generate metrics explanation panel.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Metrics guide available in /menu"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Metric", style=f"{COLORS['secondary']} bold", ratio=1)
    table.add_column("Description", style=COLORS['muted'], ratio=2)
    
    # Metrics
    metrics = [
        (f"{SYMBOLS['risk']} Escalation Risk", 
         "Likelihood of full-scale war.\n[bold]HIGH = Danger[/]"),
        (f"{SYMBOLS['stability']} Domestic Stability",
         "Public confidence & economy.\n[bold]LOW = Unrest[/]"),
        (f"{SYMBOLS['cohesion']} Alliance Cohesion",
         "NATO solidarity.\n[bold]LOW = Isolation[/]"),
        (f"{SYMBOLS['influence']} Influence",
         "Political capital.\nDerived from Stability + Cohesion"),
    ]
    
    for name, desc in metrics:
        table.add_row(name, desc)
        table.add_row("", "") # Spacer
        
    return Panel(
        table,
        title=f"[{COLORS['warning']} bold]METRICS GUIDE[/]",
        border_style=COLORS['warning'],
        box=box.ROUNDED,
        padding=(0, 2)
    )

```

Perfect! Now let's test the dashboard CLI again:

```python
"""Rich UI components for enhanced CLI display.

Provides professional ASCII-only tables, panels, and formatting while preserving
compatibility with existing narrative scrolling and keyboard systems.
"""

import os
import sys
from typing import Optional, Any, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich.markdown import Markdown
from rich import box

from cli.theme import theme_manager, SYMBOLS, BOX, WIDTH, progress_bar
from cli.formatters import format_metric_status

# Environment variable killswitch for instant rollback
RICH_ENABLED = os.getenv("WARGAME_RICH_UI", "true").lower() == "true"

# Initialize console with Windows compatibility
# CRITICAL: force_interactive=False to preserve msvcrt.kbhit() behavior
console = Console(
    legacy_windows=(sys.platform == "win32"),
    force_terminal=True,
    force_interactive=False,  # Essential for SPACE-to-skip!
    color_system="windows" if sys.platform == "win32" else "auto"  # Force Windows colour support
)


def phase_header(phase_name: str, turn: int) -> str:
    """Generate clean phase header with ASCII rounded box.
    
    Args:
        phase_name: Name of phase (BRIEFING, DISCUSSION, DECISION, ADJUDICATION)
        turn: Current turn number
        
    Returns:
        Formatted header string or Panel object
    """
    if not RICH_ENABLED:
        return f"TURN {turn}: {phase_name} PHASE"
    
    # Get dynamic colors
    COLORS = theme_manager.get_colors()
    
    # Phase colors
    phase_colors = {
        "BRIEFING": COLORS["accent"],
        "DISCUSSION": COLORS["primary"],
        "DECISION": "magenta",
        "ADJUDICATION": COLORS["success"]
    }
    
    color = phase_colors.get(phase_name, COLORS["success"]) # Default fallback safe color
    
    return Panel(
        f"[bold]TURN {turn} │ {phase_name} PHASE[/bold]",
        style=f"{color}",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False
    )


def metrics_table(world, show_deltas: bool = False, 
                  previous_metrics: Optional[Any] = None) -> Table:
    """Generate professional metrics display with ASCII symbols and bars.
    
    Args:
        world: WorldState object
        show_deltas: If True and previous_metrics provided, show changes
        previous_metrics: Previous Metrics object for delta calculation
        
    Returns:
        Rich Table object or plain string if Rich disabled
    """
    if not RICH_ENABLED:
        # Fallback to plain text
        lines = []
        lines.append(f"Turn: {world.turn}")
        lines.append(f"Phase: {world.phase}")
        lines.append(f"Escalation Risk: {world.metrics.escalation_risk}/100")
        lines.append(f"Domestic Stability: {world.metrics.domestic_stability}/100")
        lines.append(f"Alliance Cohesion: {world.metrics.alliance_cohesion}/100")
        lines.append(f"Military Casualties: {world.metrics.casualties_mil}")
        lines.append(f"Civilian Casualties: {world.metrics.casualties_civ}")
        return "\n".join(lines)
    
    COLORS = theme_manager.get_colors()
    
    # Title with turn and phase
    phase_display = world.phase.upper() if hasattr(world, 'phase') else "UNKNOWN"
    title = f"[{COLORS['accent']} bold]SITUATION REPORT │ Turn {world.turn} │ {phase_display} PHASE[/{COLORS['accent']} bold]"
    
    table = Table(title=title, border_style=COLORS["secondary"], show_header=True, padding=(0, 1), box=box.ROUNDED)
    table.add_column("", style=COLORS["secondary"], no_wrap=True, width=3)  # Symbol
    table.add_column("Metric", style=COLORS["normal"], no_wrap=True)
    table.add_column("Value", justify="right", style=COLORS["normal"], width=6)
    table.add_column("Bar", justify="left", width=12)
    table.add_column("Status", justify="left", style=COLORS["normal"], width=10)
    
    if show_deltas and previous_metrics:
        table.add_column("Change", justify="right", style=COLORS["warning"], width=8)
    
    def format_risk_value(value: int) -> str:
        """Color-code risk value (high is bad)."""
        if value >= 70:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value >= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_stability_value(value: int) -> str:
        """Color-code stability/cohesion value (low is bad)."""
        if value <= 30:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value <= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_delta(delta: int) -> str:
        """Format delta with color and sign."""
        if delta > 0:
            return f"[{COLORS['success']}]+{delta}[/{COLORS['success']}]"
        elif delta < 0:
            return f"[{COLORS['danger']}]{delta}[/{COLORS['danger']}]"
        else:
            return f"[{COLORS['muted']}]±0[/{COLORS['muted']}]"
    
    # Escalation Risk (high is bad)
    risk_val = world.metrics.escalation_risk
    risk_str = format_risk_value(risk_val)
    risk_bar = progress_bar(risk_val, 100, 10)
    risk_status = format_metric_status(risk_val, 'risk')
    
    row = [SYMBOLS["risk"], "Escalation Risk", risk_str, risk_bar, risk_status]
    if show_deltas and previous_metrics:
        delta = risk_val - previous_metrics.escalation_risk
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Domestic Stability (low is bad)
    stability_val = world.metrics.domestic_stability
    stability_str = format_stability_value(stability_val)
    stability_bar = progress_bar(stability_val, 100, 10)
    stability_status = format_metric_status(stability_val, 'stability')
    
    row = [SYMBOLS["stability"], "Domestic Stability", stability_str, stability_bar, stability_status]
    if show_deltas and previous_metrics:
        delta = stability_val - previous_metrics.domestic_stability
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Alliance Cohesion (low is bad)
    cohesion_val = world.metrics.alliance_cohesion
    cohesion_str = format_stability_value(cohesion_val)
    cohesion_bar = progress_bar(cohesion_val, 100, 10)
    cohesion_status = format_metric_status(cohesion_val, 'cohesion')
    
    row = [SYMBOLS["cohesion"], "Alliance Cohesion", cohesion_str, cohesion_bar, cohesion_status]
    if show_deltas and previous_metrics:
        delta = cohesion_val - previous_metrics.alliance_cohesion
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Casualties
    casualties_total = world.metrics.casualties_mil + world.metrics.casualties_civ
    casualties_str = f"{casualties_total}"
    casualties_detail = f"{world.metrics.casualties_mil} mil │ {world.metrics.casualties_civ} civ"
    
    row = [SYMBOLS["casualties"], "Casualties", casualties_str, casualties_detail, ""]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for casualties
    table.add_row(*row)
    
    # Calculate and add influence
    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
    influence = int((influence_raw - 50) / 5)
    influence = max(-10, min(10, influence))
    
    # Color-code influence
    if influence >= 5:
        influence_str = f"[{COLORS['metric_good']}]+{influence}[/{COLORS['metric_good']}]"
    elif influence >= 0:
        influence_str = f"[{COLORS['metric_neutral']}]+{influence}[/{COLORS['metric_neutral']}]"
    elif influence >= -5:
        influence_str = f"[{COLORS['metric_bad']}]{influence}[/{COLORS['metric_bad']}]"
    else:
        influence_str = f"[{COLORS['metric_critical']}]{influence}[/{COLORS['metric_critical']}]"
    
    influence_status = format_metric_status(influence, 'influence')
    
    row = [SYMBOLS["influence"], "Influence", influence_str, "", influence_status]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for influence (it's derived)
    table.add_row(*row)
    
    return table


def advisor_menu_panel() -> Panel:
    """Generate formatted advisor hierarchy panel using Tree view.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Use /menu to see advisor list"
    
    COLORS = theme_manager.get_colors()
    
    # Create tree structure
    tree = Tree(f"[{COLORS['accent']} bold]COBRA CABINET STRUCTURE[/]", guide_style=COLORS['secondary'])
    
    # Strategic/Intel Node
    strategic = tree.add(f"[{COLORS['primary']} bold]Strategic & Intelligence[/]")
    strategic.add(f"[{COLORS['highlight']}]National Security Advisor (NSA)[/]\n[dim]Threat analysis, strategic coordination[/]")
    
    # Military Node
    military = tree.add(f"[{COLORS['danger']} bold]Military Operations[/]")
    military.add(f"[{COLORS['highlight']}]Chief of the Defence Staff (CDS)[/]\n[dim]Force deployment, military options[/]")
    
    # Diplomatic Node
    diplomatic = tree.add(f"[{COLORS['success']} bold]Foreign Affairs[/]")
    diplomatic.add(f"[{COLORS['highlight']}]Foreign Secretary[/]\n[dim]Diplomacy, alliances, NATO[/]")
        
    # Domestic/Legal Node
    domestic = tree.add(f"[{COLORS['warning']} bold]Domestic & Legal[/]")
    domestic.add(f"[{COLORS['highlight']}]Home Secretary[/]\n[dim]Civil order, public messaging[/]")
    domestic.add(f"[{COLORS['highlight']}]Attorney General[/]\n[dim]Legal frameworks, international law[/]")
    
    return Panel(
        tree,
        title=f"[{COLORS['accent']} bold]ADVISOR HIERARCHY[/]",
        border_style=COLORS['accent'],
        box=box.ROUNDED,
        padding=(1, 2)
    )


def diplomatic_contacts_table(contacts: List[Tuple[str, str, str]]) -> Panel:
    """Generate diplomatic contacts panel using a tree view.
    
    Args:
        contacts: List of (country, access_level, title) tuples
        
    Returns:
        Rich Panel object with Tree
    """
    if not RICH_ENABLED:
        return "Diplomatic contacts available"
    
    COLORS = theme_manager.get_colors()
    
    if not contacts:
        return Panel(
            f"[{COLORS['muted']}]No diplomatic contacts available (Alliance Cohesion too low)[/]",
            title=f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/]",
            border_style=COLORS['success'],
            box=box.ROUNDED
        )
    
    # Define groupings
    alliances = {
        "NATO Allies": ["US", "France", "Germany", "Poland"],
        "Adversaries": ["Russia"],
        "Partners & Others": ["Ukraine", "Ireland"]
    }
    
    tree = Tree(f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/{COLORS['success']} bold]", guide_style=COLORS['secondary'])
    
    # Create nodes
    nodes = {
        "NATO Allies": tree.add(f"[{COLORS['secondary']} bold]NATO Alliance[/]"),
        "Adversaries": tree.add(f"[{COLORS['danger']} bold]Adversaries[/]"),
        "Partners & Others": tree.add(f"[{COLORS['muted']} bold]Partners & Others[/]")
    }
    
    # Sort contacts to ensure consistent order
    contacts.sort(key=lambda x: x[0])
    
    for country, access_level, title in contacts:
        # Determine group
        group = "Partners & Others"
        for g_name, countries in alliances.items():
            if country in countries:
                group = g_name
                break
        
        # Format status
        if access_level == "leader":
            marker = SYMBOLS["leader"]
            status = f"[{COLORS['warning']}]LEADER[/]"
        else:
            marker = SYMBOLS["diplomat"]
            status = f"[{COLORS['muted']}]DIPLOMAT[/]"
            
        # Add to appropriate node
        # Format: [Symbol] Country: Title (STATUS) -> /command
        nodes[group].add(
            f"{marker} {country}: {title} ({status})  [{COLORS['primary']}]/call {country.lower()}[/]"
        )
    
    # Remove empty nodes
    # Rich Tree doesn't support easy removal, so we rebuild if we want to be clean,
    # or just leave them (showing empty categories is fine for info).
    # Let's leave them to show structure.
    
    return Panel(
        tree,
        title=f"[{COLORS['success']} bold]SECURE LINES[/]",
        border_style=COLORS['success'],
        box=box.ROUNDED,
        padding=(0, 1)
    )


def resources_tables(initial_conditions: dict) -> Tuple[Table, Table]:
    """Generate forces and stockpiles tables.
    
    Args:
        initial_conditions: Initial conditions dict with uk_forces and stockpiles
        
    Returns:
        Tuple of (forces_table, stockpiles_table)
    """
    if not RICH_ENABLED:
        return ("UK Forces", "UK Stockpiles")
    
    COLORS = theme_manager.get_colors()
    
    # Forces table
    forces_table = Table(
        title=f"[{COLORS['accent']} bold]UK MILITARY FORCES[/{COLORS['accent']} bold]",
        border_style=COLORS["secondary"],
        show_header=True,
        box=box.ROUNDED
    )
    forces_table.add_column("Unit", style=COLORS["secondary"], no_wrap=True)
    forces_table.add_column("Type", style=COLORS["normal"])
    forces_table.add_column("Location", style=COLORS["muted"])
    forces_table.add_column("Status", style=COLORS["normal"])
    
    uk_forces = initial_conditions.get("uk_forces", {})
    
    # Naval forces
    for unit in uk_forces.get("naval", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Air forces
    for unit in uk_forces.get("air", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Add aircraft count if present
        aircraft_count = unit.get("aircraft_count")
        operational_aircraft = unit.get("operational_aircraft")
        if aircraft_count is not None:
            if operational_aircraft is not None:
                unit_type += f" ({operational_aircraft}/{aircraft_count})"
            else:
                unit_type += f" ({aircraft_count})"
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower() or "reduced" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Stockpiles table (USING TREE STRUCTURE NOW)
    stockpiles = initial_conditions.get("stockpiles", {})
    
    stock_tree = Tree(
        f"[{COLORS['accent']} bold]AMMUNITION STOCKPILES[/{COLORS['accent']} bold]",
        guide_style=COLORS['secondary']
    )
    
    # Group stockpiles by category
    categories = [
        ("Air Defence", ["aster_15", "aster_30", "sea_ceptor"]),
        ("Naval Strike", ["tomahawk_cruise_missiles", "harpoon_anti_ship"]),
        ("Air-Launched", ["storm_shadow_cruise_missiles", "paveway_laser_guided_bombs"]),
        ("Anti-Submarine", ["spearfish_torpedoes", "stingray_lightweight_torpedoes"]),
    ]
    
    for category, weapons in categories:
        cat_node = stock_tree.add(f"[{COLORS['emphasis']}]{category}[/]")
        
        for weapon_key in weapons:
            weapon_data = stockpiles.get(weapon_key, {})
            if weapon_data:
                name = weapon_key.replace('_', ' ').title()
                count = weapon_data.get("count", 0)
                note = weapon_data.get("note", "")
                
                # Color-code count
                if count >= 100:
                    count_colored = f"[{COLORS['success']}]{count}[/{COLORS['success']}]"
                elif count >= 50:
                    count_colored = f"[{COLORS['warning']}]{count}[/{COLORS['warning']}]"
                else:
                    count_colored = f"[{COLORS['danger']}]{count}[/{COLORS['danger']}]"
                
                cat_node.add(f"{name}: {count_colored} [italic muted]({note})[/]")
    
    # Return formatted panel instead of table for consistency
    stockpiles_panel = Panel(
        stock_tree,
        border_style=COLORS["secondary"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    return (forces_table, stockpiles_panel)


def command_menu() -> Panel:
    """Generate command reference menu.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Commands: /status /menu /advise /resources /call /decide /save /quit"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Command", style=COLORS['primary'])
    table.add_column("Description", style=COLORS['muted'])
    
    # Commands
    commands = [
        ("/status", "Show current metrics and situation"),
        ("/menu", "Display this help"),
        ("/advise", "Get input from all advisors"),
        ("/resources", "View UK forces and stockpiles"),
        ("/call <country>", "Contact foreign leader"),
        ("/decide", "Make your decision"),
        ("/theme", "Change UI color theme"),
        ("/llm", "Configure LLM model settings (Pro/Flash)"),
        ("/save", "Save game"),
        ("/quit", "Exit game"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return Panel(
        table,
        title="[magenta bold]COMMANDS[/]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2)
    )


def metrics_guide_panel() -> Panel:
    """Generate metrics explanation panel.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Metrics guide available in /menu"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Metric", style=f"{COLORS['secondary']} bold", ratio=1)
    table.add_column("Description", style=COLORS['muted'], ratio=2)
    
    # Metrics
    metrics = [
        (f"{SYMBOLS['risk']} Escalation Risk", 
         "Likelihood of full-scale war.\n[bold]HIGH = Danger[/]"),
        (f"{SYMBOLS['stability']} Domestic Stability",
         "Public confidence & economy.\n[bold]LOW = Unrest[/]"),
        (f"{SYMBOLS['cohesion']} Alliance Cohesion",
         "NATO solidarity.\n[bold]LOW = Isolation[/]"),
        (f"{SYMBOLS['influence']} Influence",
         "Political capital.\nDerived from Stability + Cohesion"),
    ]
    
    for name, desc in metrics:
        table.add_row(name, desc)
        table.add_row("", "") # Spacer
        
    return Panel(
        table,
        title=f"[{COLORS['warning']} bold]METRICS GUIDE[/]",
        border_style=COLORS['warning'],
        box=box.ROUNDED,
        padding=(0, 2)
    )

```

```python
"""Rich UI components for enhanced CLI display.

Provides professional ASCII-only tables, panels, and formatting while preserving
compatibility with existing narrative scrolling and keyboard systems.
"""

import os
import sys
from typing import Optional, Any, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich.markdown import Markdown
from rich import box

from cli.theme import theme_manager, SYMBOLS, BOX, WIDTH, progress_bar
from cli.formatters import format_metric_status

# Environment variable killswitch for instant rollback
RICH_ENABLED = os.getenv("WARGAME_RICH_UI", "true").lower() == "true"

# Initialize console with Windows compatibility
# CRITICAL: force_interactive=False to preserve msvcrt.kbhit() behavior
console = Console(
    legacy_windows=(sys.platform == "win32"),
    force_terminal=True,
    force_interactive=False,  # Essential for SPACE-to-skip!
    color_system="windows" if sys.platform == "win32" else "auto"  # Force Windows colour support
)


def format_markdown(text: str) -> Markdown:
    """Format markdown text for Rich display.
    
    Args:
        text: Markdown-formatted text string
        
    Returns:
        Rich Markdown object for rendering
    """
    return Markdown(text)


def phase_header(phase_name: str, turn: int) -> str:
    """Generate clean phase header with ASCII rounded box.
    
    Args:
        phase_name: Name of phase (BRIEFING, DISCUSSION, DECISION, ADJUDICATION)
        turn: Current turn number
        
    Returns:
        Formatted header string or Panel object
    """
    if not RICH_ENABLED:
        return f"TURN {turn}: {phase_name} PHASE"
    
    # Get dynamic colors
    COLORS = theme_manager.get_colors()
    
    # Phase colors
    phase_colors = {
        "BRIEFING": COLORS["accent"],
        "DISCUSSION": COLORS["primary"],
        "DECISION": "magenta",
        "ADJUDICATION": COLORS["success"]
    }
    
    color = phase_colors.get(phase_name, COLORS["success"]) # Default fallback safe color
    
    return Panel(
        f"[bold]TURN {turn} │ {phase_name} PHASE[/bold]",
        style=f"{color}",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False
    )


def metrics_table(world, show_deltas: bool = False, 
                  previous_metrics: Optional[Any] = None) -> Table:
    """Generate professional metrics display with ASCII symbols and bars.
    
    Args:
        world: WorldState object
        show_deltas: If True and previous_metrics provided, show changes
        previous_metrics: Previous Metrics object for delta calculation
        
    Returns:
        Rich Table object or plain string if Rich disabled
    """
    if not RICH_ENABLED:
        # Fallback to plain text
        lines = []
        lines.append(f"Turn: {world.turn}")
        lines.append(f"Phase: {world.phase}")
        lines.append(f"Escalation Risk: {world.metrics.escalation_risk}/100")
        lines.append(f"Domestic Stability: {world.metrics.domestic_stability}/100")
        lines.append(f"Alliance Cohesion: {world.metrics.alliance_cohesion}/100")
        lines.append(f"Military Casualties: {world.metrics.casualties_mil}")
        lines.append(f"Civilian Casualties: {world.metrics.casualties_civ}")
        return "\n".join(lines)
    
    COLORS = theme_manager.get_colors()
    
    # Title with turn and phase
    phase_display = world.phase.upper() if hasattr(world, 'phase') else "UNKNOWN"
    title = f"[{COLORS['accent']} bold]SITUATION REPORT │ Turn {world.turn} │ {phase_display} PHASE[/{COLORS['accent']} bold]"
    
    table = Table(title=title, border_style=COLORS["secondary"], show_header=True, padding=(0, 1), box=box.ROUNDED)
    table.add_column("", style=COLORS["secondary"], no_wrap=True, width=3)  # Symbol
    table.add_column("Metric", style=COLORS["normal"], no_wrap=True)
    table.add_column("Value", justify="right", style=COLORS["normal"], width=6)
    table.add_column("Bar", justify="left", width=12)
    table.add_column("Status", justify="left", style=COLORS["normal"], width=10)
    
    if show_deltas and previous_metrics:
        table.add_column("Change", justify="right", style=COLORS["warning"], width=8)
    
    def format_risk_value(value: int) -> str:
        """Color-code risk value (high is bad)."""
        if value >= 70:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value >= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_stability_value(value: int) -> str:
        """Color-code stability/cohesion value (low is bad)."""
        if value <= 30:
            return f"[{COLORS['metric_critical']}]{value}[/{COLORS['metric_critical']}]"
        elif value <= 50:
            return f"[{COLORS['metric_bad']}]{value}[/{COLORS['metric_bad']}]"
        else:
            return f"[{COLORS['metric_good']}]{value}[/{COLORS['metric_good']}]"
    
    def format_delta(delta: int) -> str:
        """Format delta with color and sign."""
        if delta > 0:
            return f"[{COLORS['success']}]+{delta}[/{COLORS['success']}]"
        elif delta < 0:
            return f"[{COLORS['danger']}]{delta}[/{COLORS['danger']}]"
        else:
            return f"[{COLORS['muted']}]±0[/{COLORS['muted']}]"
    
    # Escalation Risk (high is bad)
    risk_val = world.metrics.escalation_risk
    risk_str = format_risk_value(risk_val)
    risk_bar = progress_bar(risk_val, 100, 10)
    risk_status = format_metric_status(risk_val, 'risk')
    
    row = [SYMBOLS["risk"], "Escalation Risk", risk_str, risk_bar, risk_status]
    if show_deltas and previous_metrics:
        delta = risk_val - previous_metrics.escalation_risk
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Domestic Stability (low is bad)
    stability_val = world.metrics.domestic_stability
    stability_str = format_stability_value(stability_val)
    stability_bar = progress_bar(stability_val, 100, 10)
    stability_status = format_metric_status(stability_val, 'stability')
    
    row = [SYMBOLS["stability"], "Domestic Stability", stability_str, stability_bar, stability_status]
    if show_deltas and previous_metrics:
        delta = stability_val - previous_metrics.domestic_stability
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Alliance Cohesion (low is bad)
    cohesion_val = world.metrics.alliance_cohesion
    cohesion_str = format_stability_value(cohesion_val)
    cohesion_bar = progress_bar(cohesion_val, 100, 10)
    cohesion_status = format_metric_status(cohesion_val, 'cohesion')
    
    row = [SYMBOLS["cohesion"], "Alliance Cohesion", cohesion_str, cohesion_bar, cohesion_status]
    if show_deltas and previous_metrics:
        delta = cohesion_val - previous_metrics.alliance_cohesion
        row.append(format_delta(delta))
    table.add_row(*row)
    
    # Casualties
    casualties_total = world.metrics.casualties_mil + world.metrics.casualties_civ
    casualties_str = f"{casualties_total}"
    casualties_detail = f"{world.metrics.casualties_mil} mil │ {world.metrics.casualties_civ} civ"
    
    row = [SYMBOLS["casualties"], "Casualties", casualties_str, casualties_detail, ""]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for casualties
    table.add_row(*row)
    
    # Calculate and add influence
    influence_raw = (world.metrics.domestic_stability + world.metrics.alliance_cohesion) / 2.0
    influence = int((influence_raw - 50) / 5)
    influence = max(-10, min(10, influence))
    
    # Color-code influence
    if influence >= 5:
        influence_str = f"[{COLORS['metric_good']}]+{influence}[/{COLORS['metric_good']}]"
    elif influence >= 0:
        influence_str = f"[{COLORS['metric_neutral']}]+{influence}[/{COLORS['metric_neutral']}]"
    elif influence >= -5:
        influence_str = f"[{COLORS['metric_bad']}]{influence}[/{COLORS['metric_bad']}]"
    else:
        influence_str = f"[{COLORS['metric_critical']}]{influence}[/{COLORS['metric_critical']}]"
    
    influence_status = format_metric_status(influence, 'influence')
    
    row = [SYMBOLS["influence"], "Influence", influence_str, "", influence_status]
    if show_deltas and previous_metrics:
        row.append("")  # No delta for influence (it's derived)
    table.add_row(*row)
    
    return table


def advisor_menu_panel() -> Panel:
    """Generate formatted advisor hierarchy panel using Tree view.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Use /menu to see advisor list"
    
    COLORS = theme_manager.get_colors()
    
    # Create tree structure
    tree = Tree(f"[{COLORS['accent']} bold]COBRA CABINET STRUCTURE[/]", guide_style=COLORS['secondary'])
    
    # Strategic/Intel Node
    strategic = tree.add(f"[{COLORS['primary']} bold]Strategic & Intelligence[/]")
    strategic.add(f"[{COLORS['highlight']}]National Security Advisor (NSA)[/]\n[dim]Threat analysis, strategic coordination[/]")
    
    # Military Node
    military = tree.add(f"[{COLORS['danger']} bold]Military Operations[/]")
    military.add(f"[{COLORS['highlight']}]Chief of the Defence Staff (CDS)[/]\n[dim]Force deployment, military options[/]")
    
    # Diplomatic Node
    diplomatic = tree.add(f"[{COLORS['success']} bold]Foreign Affairs[/]")
    diplomatic.add(f"[{COLORS['highlight']}]Foreign Secretary[/]\n[dim]Diplomacy, alliances, NATO[/]")
        
    # Domestic/Legal Node
    domestic = tree.add(f"[{COLORS['warning']} bold]Domestic & Legal[/]")
    domestic.add(f"[{COLORS['highlight']}]Home Secretary[/]\n[dim]Civil order, public messaging[/]")
    domestic.add(f"[{COLORS['highlight']}]Attorney General[/]\n[dim]Legal frameworks, international law[/]")
    
    return Panel(
        tree,
        title=f"[{COLORS['accent']} bold]ADVISOR HIERARCHY[/]",
        border_style=COLORS['accent'],
        box=box.ROUNDED,
        padding=(1, 2)
    )


def diplomatic_contacts_table(contacts: List[Tuple[str, str, str]]) -> Panel:
    """Generate diplomatic contacts panel using a tree view.
    
    Args:
        contacts: List of (country, access_level, title) tuples
        
    Returns:
        Rich Panel object with Tree
    """
    if not RICH_ENABLED:
        return "Diplomatic contacts available"
    
    COLORS = theme_manager.get_colors()
    
    if not contacts:
        return Panel(
            f"[{COLORS['muted']}]No diplomatic contacts available (Alliance Cohesion too low)[/]",
            title=f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/]",
            border_style=COLORS['success'],
            box=box.ROUNDED
        )
    
    # Define groupings
    alliances = {
        "NATO Allies": ["US", "France", "Germany", "Poland"],
        "Adversaries": ["Russia"],
        "Partners & Others": ["Ukraine", "Ireland"]
    }
    
    tree = Tree(f"[{COLORS['success']} bold]DIPLOMATIC CHANNELS[/{COLORS['success']} bold]", guide_style=COLORS['secondary'])
    
    # Create nodes
    nodes = {
        "NATO Allies": tree.add(f"[{COLORS['secondary']} bold]NATO Alliance[/]"),
        "Adversaries": tree.add(f"[{COLORS['danger']} bold]Adversaries[/]"),
        "Partners & Others": tree.add(f"[{COLORS['muted']} bold]Partners & Others[/]")
    }
    
    # Sort contacts to ensure consistent order
    contacts.sort(key=lambda x: x[0])
    
    for country, access_level, title in contacts:
        # Determine group
        group = "Partners & Others"
        for g_name, countries in alliances.items():
            if country in countries:
                group = g_name
                break
        
        # Format status
        if access_level == "leader":
            marker = SYMBOLS["leader"]
            status = f"[{COLORS['warning']}]LEADER[/]"
        else:
            marker = SYMBOLS["diplomat"]
            status = f"[{COLORS['muted']}]DIPLOMAT[/]"
            
        # Add to appropriate node
        # Format: [Symbol] Country: Title (STATUS) -> /command
        nodes[group].add(
            f"{marker} {country}: {title} ({status})  [{COLORS['primary']}]/call {country.lower()}[/]"
        )
    
    # Remove empty nodes
    # Rich Tree doesn't support easy removal, so we rebuild if we want to be clean,
    # or just leave them (showing empty categories is fine for info).
    # Let's leave them to show structure.
    
    return Panel(
        tree,
        title=f"[{COLORS['success']} bold]SECURE LINES[/]",
        border_style=COLORS['success'],
        box=box.ROUNDED,
        padding=(0, 1)
    )


def resources_tables(initial_conditions: dict) -> Tuple[Table, Table]:
    """Generate forces and stockpiles tables.
    
    Args:
        initial_conditions: Initial conditions dict with uk_forces and stockpiles
        
    Returns:
        Tuple of (forces_table, stockpiles_table)
    """
    if not RICH_ENABLED:
        return ("UK Forces", "UK Stockpiles")
    
    COLORS = theme_manager.get_colors()
    
    # Forces table
    forces_table = Table(
        title=f"[{COLORS['accent']} bold]UK MILITARY FORCES[/{COLORS['accent']} bold]",
        border_style=COLORS["secondary"],
        show_header=True,
        box=box.ROUNDED
    )
    forces_table.add_column("Unit", style=COLORS["secondary"], no_wrap=True)
    forces_table.add_column("Type", style=COLORS["normal"])
    forces_table.add_column("Location", style=COLORS["muted"])
    forces_table.add_column("Status", style=COLORS["normal"])
    
    uk_forces = initial_conditions.get("uk_forces", {})
    
    # Naval forces
    for unit in uk_forces.get("naval", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Air forces
    for unit in uk_forces.get("air", []):
        unit_id = unit.get("id", "Unknown").replace("_", " ")
        unit_type = unit.get("type", "").replace("_", " ")
        location = unit.get("location", "").replace("_", " ")
        status = unit.get("status", "").replace("_", " ")
        
        # Add aircraft count if present
        aircraft_count = unit.get("aircraft_count")
        operational_aircraft = unit.get("operational_aircraft")
        if aircraft_count is not None:
            if operational_aircraft is not None:
                unit_type += f" ({operational_aircraft}/{aircraft_count})"
            else:
                unit_type += f" ({aircraft_count})"
        
        # Color-code status
        if "operational" in status.lower():
            status_colored = f"[{COLORS['success']}]{status}[/{COLORS['success']}]"
        elif "limited" in status.lower() or "reduced" in status.lower():
            status_colored = f"[{COLORS['warning']}]{status}[/{COLORS['warning']}]"
        else:
            status_colored = status
        
        forces_table.add_row(unit_id, unit_type, location, status_colored)
    
    # Stockpiles table (USING TREE STRUCTURE NOW)
    stockpiles = initial_conditions.get("stockpiles", {})
    
    stock_tree = Tree(
        f"[{COLORS['accent']} bold]AMMUNITION STOCKPILES[/{COLORS['accent']} bold]",
        guide_style=COLORS['secondary']
    )
    
    # Group stockpiles by category
    categories = [
        ("Air Defence", ["aster_15", "aster_30", "sea_ceptor"]),
        ("Naval Strike", ["tomahawk_cruise_missiles", "harpoon_anti_ship"]),
        ("Air-Launched", ["storm_shadow_cruise_missiles", "paveway_laser_guided_bombs"]),
        ("Anti-Submarine", ["spearfish_torpedoes", "stingray_lightweight_torpedoes"]),
    ]
    
    for category, weapons in categories:
        cat_node = stock_tree.add(f"[{COLORS['emphasis']}]{category}[/]")
        
        for weapon_key in weapons:
            weapon_data = stockpiles.get(weapon_key, {})
            if weapon_data:
                name = weapon_key.replace('_', ' ').title()
                count = weapon_data.get("count", 0)
                note = weapon_data.get("note", "")
                
                # Color-code count
                if count >= 100:
                    count_colored = f"[{COLORS['success']}]{count}[/{COLORS['success']}]"
                elif count >= 50:
                    count_colored = f"[{COLORS['warning']}]{count}[/{COLORS['warning']}]"
                else:
                    count_colored = f"[{COLORS['danger']}]{count}[/{COLORS['danger']}]"
                
                cat_node.add(f"{name}: {count_colored} [italic muted]({note})[/]")
    
    # Return formatted panel instead of table for consistency
    stockpiles_panel = Panel(
        stock_tree,
        border_style=COLORS["secondary"],
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    return (forces_table, stockpiles_panel)


def command_menu() -> Panel:
    """Generate command reference menu.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Commands: /status /menu /advise /resources /call /decide /save /quit"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Command", style=COLORS['primary'])
    table.add_column("Description", style=COLORS['muted'])
    
    # Commands
    commands = [
        ("/status", "Show current metrics and situation"),
        ("/menu", "Display this help"),
        ("/advise", "Get input from all advisors"),
        ("/resources", "View UK forces and stockpiles"),
        ("/call <country>", "Contact foreign leader"),
        ("/decide", "Make your decision"),
        ("/theme", "Change UI color theme"),
        ("/llm", "Configure LLM model settings (Pro/Flash)"),
        ("/save", "Save game"),
        ("/quit", "Exit game"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
        
    return Panel(
        table,
        title="[magenta bold]COMMANDS[/]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2)
    )


def metrics_guide_panel() -> Panel:
    """Generate metrics explanation panel.
    
    Returns:
        Rich Panel object
    """
    if not RICH_ENABLED:
        return "Metrics guide available in /menu"
    
    COLORS = theme_manager.get_colors()
    
    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column("Metric", style=f"{COLORS['secondary']} bold", ratio=1)
    table.add_column("Description", style=COLORS['muted'], ratio=2)
    
    # Metrics
    metrics = [
        (f"{SYMBOLS['risk']} Escalation Risk", 
         "Likelihood of full-scale war.\n[bold]HIGH = Danger[/]"),
        (f"{SYMBOLS['stability']} Domestic Stability",
         "Public confidence & economy.\n[bold]LOW = Unrest[/]"),
        (f"{SYMBOLS['cohesion']} Alliance Cohesion",
         "NATO solidarity.\n[bold]LOW = Isolation[/]"),
        (f"{SYMBOLS['influence']} Influence",
         "Political capital.\nDerived from Stability + Cohesion"),
    ]
    
    for name, desc in metrics:
        table.add_row(name, desc)
        table.add_row("", "") # Spacer
        
    return Panel(
        table,
        title=f"[{COLORS['warning']} bold]METRICS GUIDE[/]",
        border_style=COLORS['warning'],
        box=box.ROUNDED,
        padding=(0, 2)
    )

```

Excellent! Now let's test the dashboard CLI:

Another indentation error in the codebase. Let me fix it:

```python
"""LLM router for provider-agnostic text generation and legacy proposal selection.

Supports multiple LLM providers:
- mock (default): Deterministic mock responses for testing
- offline: Pre-recorded responses
- gemini: Google Gemini 2.5 Flash/Pro (requires GOOGLE_API_KEY)
- openai: OpenAI API (future)
- anthropic: Anthropic API (future)

Configuration priority:
1. Environment variable WARGAME_LLM (if set)
2. config.py LLM_PROVIDER (if file exists)
3. Default to "mock"

Model selection per context:
- Configured via llm.model_config
- Allows Flash vs Pro per system (advisor, inject, diplomacy, etc.)
"""

import os
import time
from random import Random
from typing import Optional
from collections import deque

from llm.mock_driver import MockDeterministicDriver
from llm.offline_driver import OfflineDriver
from llm.model_config import LLMContext, get_model_config


class RateLimiter:
    """Rate limiter for API calls to prevent hitting provider limits.
    
    Google Gemini free tier: 2 requests per minute (RPM)
    Google Gemini paid tier: 1000 requests per minute
    """
    
    def __init__(self, requests_per_minute: int = 2):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()  # Track timestamps of recent requests
        self.window_seconds = 60.0  # 1 minute window
    
    def wait_if_needed(self, verbose: bool = True):
        """Wait if necessary to stay within rate limits.
        
        Args:
            verbose: If True, print messages when waiting
        """
        now = time.time()
        
        # Remove requests older than the window
        while self.request_times and (now - self.request_times[0]) > self.window_seconds:
            self.request_times.popleft()
        
        # If we've hit the limit, wait until the oldest request expires
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_time = self.window_seconds - (now - oldest_request)
            
            if wait_time > 0:
                if verbose:
                    print(f"\n[Rate Limit] Waiting {wait_time:.1f}s to stay within {self.requests_per_minute} requests/min limit...")
                time.sleep(wait_time + 0.1)  # Add small buffer
        
        # Record this request
        self.request_times.append(time.time())


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(model_name: Optional[str] = None) -> Optional[RateLimiter]:
    """Get or create the global rate limiter.
    
    Args:
        model_name: Model being used (determines RPM limit)
    
    Returns:
        RateLimiter instance if using a rate-limited provider, None otherwise
    """
    global _rate_limiter
    
    # Check provider
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    # Only rate limit for real API providers
    if provider not in ["gemini"]:
        return None
    
    # Determine RPM based on model (free tier limits)
    # Flash: 10 RPM, Pro: 2 RPM (from Google AI Studio dashboard)
    rpm = int(os.getenv("GEMINI_RPM", "0"))  # 0 = auto-detect
    
    if rpm == 0:  # Auto-detect based on model
        if model_name and "flash" in model_name.lower():
            rpm = 10  # Flash models: 10 RPM
        else:
            rpm = 2   # Pro models: 2 RPM
    
    # Create rate limiter if not exists or if RPM changed
    if _rate_limiter is None or _rate_limiter.requests_per_minute != rpm:
        _rate_limiter = RateLimiter(requests_per_minute=rpm)
    
    return _rate_limiter


def _get_text_driver(model_name: Optional[str] = None):
    """Get LLM driver for text generation.
    
    Args:
        model_name: Optional specific model to use (e.g., "gemini-2.5-pro")
    
    Returns driver that supports generate_text method.
    """
    # Priority 1: Environment variable (for overrides)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    
    # Priority 2: config.py (if no env var set)
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    if provider == "offline":
        return OfflineDriver()
    
    if provider == "gemini":
        try:
            from llm.gemini_driver import GeminiDriver
            return GeminiDriver(model_name=model_name)
        except (ImportError, RuntimeError, ValueError) as e:
            print(f"[WARNING] Failed to initialize Gemini driver: {e}")
            print("[WARNING] Falling back to mock driver")
            return MockDeterministicDriver()
    
    # Default to mock for testing
    return MockDeterministicDriver()


def generate_text(
    prompt: str, 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """Generate text using configured LLM provider.
    
    Args:
        prompt: Prompt text
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection (e.g., LLMContext.INJECT_GENERATION)
        model_override: Optional explicit model name (overrides context-based selection)
        system_instruction: Optional system instruction for the model
        temperature: Optional temperature override
        max_tokens: Optional max tokens override
    
    Returns:
        Generated text response
    """
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None  # Use driver default
    
    # Apply rate limiting before making request (model-specific limits)
    rate_limiter = get_rate_limiter(model_name)
    if rate_limiter:
        rate_limiter.wait_if_needed(verbose=True)
    
    driver = _get_text_driver(model_name)
    
    # Show spinner if requested (and not in mock mode)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    use_spinner = show_spinner and provider not in ["mock", "offline"]
    
    # Helper to call driver with optional args
    def call_driver():
        if hasattr(driver, 'generate_text'):
            # Check if driver accepts additional args
            import inspect
            sig = inspect.signature(driver.generate_text)
            kwargs = {}
            if 'system_instruction' in sig.parameters and system_instruction:
                kwargs['system_instruction'] = system_instruction
            if 'temperature' in sig.parameters and temperature is not None:
                kwargs['temperature'] = temperature
            if 'max_tokens' in sig.parameters and max_tokens is not None:
                kwargs['max_tokens'] = max_tokens
                
            return driver.generate_text(prompt, rng, **kwargs)
        return f"[LLM response to: {prompt[:50]}...]"
    
    if use_spinner:
        try:
            # Use rich console status instead of custom Spinner class
            from cli.rich_ui import console
            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                return call_driver()
        except ImportError:
            # If rich import fails, try legacy Spinner
            try:
                from cli.spinner import Spinner
                with Spinner("Thinking"):
                    return call_driver()
            except ImportError:
                pass
    
    # No spinner - direct call
    return call_driver()


def batch_generate_text(
    prompts: list[str], 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None
) -> list[str]:
    """Generate multiple text responses in parallel using configured LLM provider.
    
    NOTE: For rate-limited providers, this will wait between requests.
    
    Args:
        prompts: List of prompt texts to generate responses for
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection
        model_override: Optional explicit model name
    
    Returns:
        List of generated text responses in same order as prompts
    """
    if not prompts:
        return []
    
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None
    
    # Get rate limiter (will apply per request in sequential mode, model-specific)
    rate_limiter = get_rate_limiter(model_name)
    
    driver = _get_text_driver(model_name)
    
    # Show spinner if requested (and not in mock mode)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    use_spinner = show_spinner and provider not in ["mock", "offline"]
    
    # Helper for batch call
    def call_batch():
    if hasattr(driver, 'batch_generate_text'):
            return driver.batch_generate_text(prompts, rng)
        # Fallback sequential
        results = []
        for prompt in prompts:
            if rate_limiter:
                rate_limiter.wait_if_needed(verbose=False)
            if hasattr(driver, 'generate_text'):
                results.append(driver.generate_text(prompt, rng))
            else:
                results.append(f"[LLM response to: {prompt[:50]}...]")
        return results

        if use_spinner:
        try:
            from cli.rich_ui import console
            with console.status(f"[bold cyan]Simulating {len(prompts)} actors...[/bold cyan]", spinner="dots"):
                return call_batch()
        except ImportError:
            try:
                from cli.spinner import Spinner
                with Spinner(f"Simulating {len(prompts)} actors"):
                    return call_batch()
            except ImportError:
                pass
        
    return call_batch()

```

```python
"""LLM router for provider-agnostic text generation and legacy proposal selection.

Supports multiple LLM providers:
- mock (default): Deterministic mock responses for testing
- offline: Pre-recorded responses
- gemini: Google Gemini 2.5 Flash/Pro (requires GOOGLE_API_KEY)
- openai: OpenAI API (future)
- anthropic: Anthropic API (future)

Configuration priority:
1. Environment variable WARGAME_LLM (if set)
2. config.py LLM_PROVIDER (if file exists)
3. Default to "mock"

Model selection per context:
- Configured via llm.model_config
- Allows Flash vs Pro per system (advisor, inject, diplomacy, etc.)
"""

import os
import time
from random import Random
from typing import Optional
from collections import deque

from llm.mock_driver import MockDeterministicDriver
from llm.offline_driver import OfflineDriver
from llm.model_config import LLMContext, get_model_config


class RateLimiter:
    """Rate limiter for API calls to prevent hitting provider limits.
    
    Google Gemini free tier: 2 requests per minute (RPM)
    Google Gemini paid tier: 1000 requests per minute
    """
    
    def __init__(self, requests_per_minute: int = 2):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()  # Track timestamps of recent requests
        self.window_seconds = 60.0  # 1 minute window
    
    def wait_if_needed(self, verbose: bool = True):
        """Wait if necessary to stay within rate limits.
        
        Args:
            verbose: If True, print messages when waiting
        """
        now = time.time()
        
        # Remove requests older than the window
        while self.request_times and (now - self.request_times[0]) > self.window_seconds:
            self.request_times.popleft()
        
        # If we've hit the limit, wait until the oldest request expires
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_time = self.window_seconds - (now - oldest_request)
            
            if wait_time > 0:
                if verbose:
                    print(f"\n[Rate Limit] Waiting {wait_time:.1f}s to stay within {self.requests_per_minute} requests/min limit...")
                time.sleep(wait_time + 0.1)  # Add small buffer
        
        # Record this request
        self.request_times.append(time.time())


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(model_name: Optional[str] = None) -> Optional[RateLimiter]:
    """Get or create the global rate limiter.
    
    Args:
        model_name: Model being used (determines RPM limit)
    
    Returns:
        RateLimiter instance if using a rate-limited provider, None otherwise
    """
    global _rate_limiter
    
    # Check provider
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    # Only rate limit for real API providers
    if provider not in ["gemini"]:
        return None
    
    # Determine RPM based on model (free tier limits)
    # Flash: 10 RPM, Pro: 2 RPM (from Google AI Studio dashboard)
    rpm = int(os.getenv("GEMINI_RPM", "0"))  # 0 = auto-detect
    
    if rpm == 0:  # Auto-detect based on model
        if model_name and "flash" in model_name.lower():
            rpm = 10  # Flash models: 10 RPM
        else:
            rpm = 2   # Pro models: 2 RPM
    
    # Create rate limiter if not exists or if RPM changed
    if _rate_limiter is None or _rate_limiter.requests_per_minute != rpm:
        _rate_limiter = RateLimiter(requests_per_minute=rpm)
    
    return _rate_limiter


def _get_text_driver(model_name: Optional[str] = None):
    """Get LLM driver for text generation.
    
    Args:
        model_name: Optional specific model to use (e.g., "gemini-2.5-pro")
    
    Returns driver that supports generate_text method.
    """
    # Priority 1: Environment variable (for overrides)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    
    # Priority 2: config.py (if no env var set)
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    if provider == "offline":
        return OfflineDriver()
    
    if provider == "gemini":
        try:
            from llm.gemini_driver import GeminiDriver
            return GeminiDriver(model_name=model_name)
        except (ImportError, RuntimeError, ValueError) as e:
            print(f"[WARNING] Failed to initialize Gemini driver: {e}")
            print("[WARNING] Falling back to mock driver")
            return MockDeterministicDriver()
    
    # Default to mock for testing
    return MockDeterministicDriver()


def generate_text(
    prompt: str, 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """Generate text using configured LLM provider.
    
    Args:
        prompt: Prompt text
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection (e.g., LLMContext.INJECT_GENERATION)
        model_override: Optional explicit model name (overrides context-based selection)
        system_instruction: Optional system instruction for the model
        temperature: Optional temperature override
        max_tokens: Optional max tokens override
    
    Returns:
        Generated text response
    """
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None  # Use driver default
    
    # Apply rate limiting before making request (model-specific limits)
    rate_limiter = get_rate_limiter(model_name)
    if rate_limiter:
        rate_limiter.wait_if_needed(verbose=True)
    
    driver = _get_text_driver(model_name)
    
    # Show spinner if requested (and not in mock mode)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    use_spinner = show_spinner and provider not in ["mock", "offline"]
    
    # Helper to call driver with optional args
    def call_driver():
        if hasattr(driver, 'generate_text'):
            # Check if driver accepts additional args
            import inspect
            sig = inspect.signature(driver.generate_text)
            kwargs = {}
            if 'system_instruction' in sig.parameters and system_instruction:
                kwargs['system_instruction'] = system_instruction
            if 'temperature' in sig.parameters and temperature is not None:
                kwargs['temperature'] = temperature
            if 'max_tokens' in sig.parameters and max_tokens is not None:
                kwargs['max_tokens'] = max_tokens
                
            return driver.generate_text(prompt, rng, **kwargs)
        return f"[LLM response to: {prompt[:50]}...]"
    
    if use_spinner:
        try:
            # Use rich console status instead of custom Spinner class
            from cli.rich_ui import console
            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                return call_driver()
        except ImportError:
            # If rich import fails, try legacy Spinner
            try:
                from cli.spinner import Spinner
                with Spinner("Thinking"):
                    return call_driver()
            except ImportError:
                pass
    
    # No spinner - direct call
    return call_driver()


def batch_generate_text(
    prompts: list[str], 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None
) -> list[str]:
    """Generate multiple text responses in parallel using configured LLM provider.
    
    NOTE: For rate-limited providers, this will wait between requests.
    
    Args:
        prompts: List of prompt texts to generate responses for
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection
        model_override: Optional explicit model name
    
    Returns:
        List of generated text responses in same order as prompts
    """
    if not prompts:
        return []
    
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None
    
    # Get rate limiter (will apply per request in sequential mode, model-specific)
    rate_limiter = get_rate_limiter(model_name)
    
    driver = _get_text_driver(model_name)
    
    # Show spinner if requested (and not in mock mode)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    use_spinner = show_spinner and provider not in ["mock", "offline"]
    
    # Helper for batch call
    def call_batch():
        if hasattr(driver, 'batch_generate_text'):
            return driver.batch_generate_text(prompts, rng)
        # Fallback sequential
        results = []
        for prompt in prompts:
            if rate_limiter:
                rate_limiter.wait_if_needed(verbose=False)
            if hasattr(driver, 'generate_text'):
                results.append(driver.generate_text(prompt, rng))
            else:
                results.append(f"[LLM response to: {prompt[:50]}...]")
        return results

        if use_spinner:
        try:
            from cli.rich_ui import console
            with console.status(f"[bold cyan]Simulating {len(prompts)} actors...[/bold cyan]", spinner="dots"):
                return call_batch()
        except ImportError:
            try:
                from cli.spinner import Spinner
                with Spinner(f"Simulating {len(prompts)} actors"):
                    return call_batch()
            except ImportError:
                pass
        
    return call_batch()

```

Let me run a lint check on the entire llm/router.py file to find all indentation issues:

```python
"""LLM router for provider-agnostic text generation and legacy proposal selection.

Supports multiple LLM providers:
- mock (default): Deterministic mock responses for testing
- offline: Pre-recorded responses
- gemini: Google Gemini 2.5 Flash/Pro (requires GOOGLE_API_KEY)
- openai: OpenAI API (future)
- anthropic: Anthropic API (future)

Configuration priority:
1. Environment variable WARGAME_LLM (if set)
2. config.py LLM_PROVIDER (if file exists)
3. Default to "mock"

Model selection per context:
- Configured via llm.model_config
- Allows Flash vs Pro per system (advisor, inject, diplomacy, etc.)
"""

import os
import time
from random import Random
from typing import Optional
from collections import deque

from llm.mock_driver import MockDeterministicDriver
from llm.offline_driver import OfflineDriver
from llm.model_config import LLMContext, get_model_config


class RateLimiter:
    """Rate limiter for API calls to prevent hitting provider limits.
    
    Google Gemini free tier: 2 requests per minute (RPM)
    Google Gemini paid tier: 1000 requests per minute
    """
    
    def __init__(self, requests_per_minute: int = 2):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()  # Track timestamps of recent requests
        self.window_seconds = 60.0  # 1 minute window
    
    def wait_if_needed(self, verbose: bool = True):
        """Wait if necessary to stay within rate limits.
        
        Args:
            verbose: If True, print messages when waiting
        """
        now = time.time()
        
        # Remove requests older than the window
        while self.request_times and (now - self.request_times[0]) > self.window_seconds:
            self.request_times.popleft()
        
        # If we've hit the limit, wait until the oldest request expires
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_time = self.window_seconds - (now - oldest_request)
            
            if wait_time > 0:
                if verbose:
                    print(f"\n[Rate Limit] Waiting {wait_time:.1f}s to stay within {self.requests_per_minute} requests/min limit...")
                time.sleep(wait_time + 0.1)  # Add small buffer
        
        # Record this request
        self.request_times.append(time.time())


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(model_name: Optional[str] = None) -> Optional[RateLimiter]:
    """Get or create the global rate limiter.
    
    Args:
        model_name: Model being used (determines RPM limit)
    
    Returns:
        RateLimiter instance if using a rate-limited provider, None otherwise
    """
    global _rate_limiter
    
    # Check provider
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    # Only rate limit for real API providers
    if provider not in ["gemini"]:
        return None
    
    # Determine RPM based on model (free tier limits)
    # Flash: 10 RPM, Pro: 2 RPM (from Google AI Studio dashboard)
    rpm = int(os.getenv("GEMINI_RPM", "0"))  # 0 = auto-detect
    
    if rpm == 0:  # Auto-detect based on model
        if model_name and "flash" in model_name.lower():
            rpm = 10  # Flash models: 10 RPM
        else:
            rpm = 2   # Pro models: 2 RPM
    
    # Create rate limiter if not exists or if RPM changed
    if _rate_limiter is None or _rate_limiter.requests_per_minute != rpm:
        _rate_limiter = RateLimiter(requests_per_minute=rpm)
    
    return _rate_limiter


def _get_text_driver(model_name: Optional[str] = None):
    """Get LLM driver for text generation.
    
    Args:
        model_name: Optional specific model to use (e.g., "gemini-2.5-pro")
    
    Returns driver that supports generate_text method.
    """
    # Priority 1: Environment variable (for overrides)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    
    # Priority 2: config.py (if no env var set)
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    if provider == "offline":
        return OfflineDriver()
    
    if provider == "gemini":
        try:
            from llm.gemini_driver import GeminiDriver
            return GeminiDriver(model_name=model_name)
        except (ImportError, RuntimeError, ValueError) as e:
            print(f"[WARNING] Failed to initialize Gemini driver: {e}")
            print("[WARNING] Falling back to mock driver")
            return MockDeterministicDriver()
    
    # Default to mock for testing
    return MockDeterministicDriver()


def generate_text(
    prompt: str, 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """Generate text using configured LLM provider.
    
    Args:
        prompt: Prompt text
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection (e.g., LLMContext.INJECT_GENERATION)
        model_override: Optional explicit model name (overrides context-based selection)
        system_instruction: Optional system instruction for the model
        temperature: Optional temperature override
        max_tokens: Optional max tokens override
    
    Returns:
        Generated text response
    """
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None  # Use driver default
    
    # Apply rate limiting before making request (model-specific limits)
    rate_limiter = get_rate_limiter(model_name)
    if rate_limiter:
        rate_limiter.wait_if_needed(verbose=True)
    
    driver = _get_text_driver(model_name)
    
    # Show spinner if requested (and not in mock mode)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    use_spinner = show_spinner and provider not in ["mock", "offline"]
    
    # Helper to call driver with optional args
    def call_driver():
        if hasattr(driver, 'generate_text'):
            # Check if driver accepts additional args
            import inspect
            sig = inspect.signature(driver.generate_text)
            kwargs = {}
            if 'system_instruction' in sig.parameters and system_instruction:
                kwargs['system_instruction'] = system_instruction
            if 'temperature' in sig.parameters and temperature is not None:
                kwargs['temperature'] = temperature
            if 'max_tokens' in sig.parameters and max_tokens is not None:
                kwargs['max_tokens'] = max_tokens
                
            return driver.generate_text(prompt, rng, **kwargs)
        return f"[LLM response to: {prompt[:50]}...]"
    
    if use_spinner:
        try:
            # Use rich console status instead of custom Spinner class
            from cli.rich_ui import console
            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                return call_driver()
        except ImportError:
            # If rich import fails, try legacy Spinner
            try:
                from cli.spinner import Spinner
                with Spinner("Thinking"):
                    return call_driver()
            except ImportError:
                pass
    
    # No spinner - direct call
    return call_driver()


def batch_generate_text(
    prompts: list[str], 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None
) -> list[str]:
    """Generate multiple text responses in parallel using configured LLM provider.
    
    NOTE: For rate-limited providers, this will wait between requests.
    
    Args:
        prompts: List of prompt texts to generate responses for
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection
        model_override: Optional explicit model name
    
    Returns:
        List of generated text responses in same order as prompts
    """
    if not prompts:
        return []
    
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None
    
    # Get rate limiter (will apply per request in sequential mode, model-specific)
    rate_limiter = get_rate_limiter(model_name)
    
    driver = _get_text_driver(model_name)
    
    # Show spinner if requested (and not in mock mode)
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    
    use_spinner = show_spinner and provider not in ["mock", "offline"]
    
    # Helper for batch call
    def call_batch():
        if hasattr(driver, 'batch_generate_text'):
            return driver.batch_generate_text(prompts, rng)
        # Fallback sequential
        results = []
        for prompt in prompts:
            if rate_limiter:
                rate_limiter.wait_if_needed(verbose=False)
            if hasattr(driver, 'generate_text'):
                results.append(driver.generate_text(prompt, rng))
            else:
                results.append(f"[LLM response to: {prompt[:50]}...]")
        return results
    
    if use_spinner:
        try:
            from cli.rich_ui import console
            with console.status(f"[bold cyan]Simulating {len(prompts)} actors...[/bold cyan]", spinner="dots"):
                return call_batch()
        except ImportError:
            try:
                from cli.spinner import Spinner
                with Spinner(f"Simulating {len(prompts)} actors"):
                    return call_batch()
            except ImportError:
                pass
        
    return call_batch()

```

Perfect! Now let's test the dashboard CLI:

---

**User**

lets go please

