# CLI Development Package
**FALSE FLAG: THE WARGAME - Complete CLI System**

**Version:** 1.0  
**Date:** 2025-11-23  
**Status:** Comprehensive CLI Documentation & Roadmap

---

## 📋 Package Overview

This package documents the **entire CLI system** for FALSE FLAG: THE WARGAME, including:

- **Core CLI** (`cli/main.py`) - Scrolling interactive terminal
- **Rich UI System** (`cli/rich_ui.py`) - Modern terminal components
- **Theme Engine** (`cli/theme.py`) - Multi-theme colour system
- **Text Formatting** (`cli/formatters.py`) - Narrative formatting utilities
- **Dashboard UI** (`cli/dashboard.py`) - Persistent layout system (experimental)
- **Design System** - Visual language and ADHD-friendly principles

**Purpose:** Unified reference for CLI development, enhancement, and maintenance.

---

## 🎯 CLI System Architecture

### Component Map

```
FALSE FLAG CLI SYSTEM
│
├── CORE INTERFACE
│   ├── cli/main.py                    (Primary entry point)
│   ├── cli/main_dashboard.py          (Dashboard variant - experimental)
│   └── cli/launcher.py                (Future: Mode selector)
│
├── RENDERING LAYER
│   ├── cli/rich_ui.py                 (Rich components library)
│   │   ├── phase_header()
│   │   ├── metrics_table()
│   │   ├── advisor_menu_panel()
│   │   ├── diplomatic_contacts_table()
│   │   ├── resources_tables()
│   │   └── command_menu()
│   │
│   ├── cli/dashboard.py               (Dashboard layout manager)
│   │   └── WargameDashboard class
│   │
│   └── cli/formatters.py              (Text utilities)
│       ├── format_advisor_response()
│       └── wrap_text()
│
├── STYLING LAYER
│   ├── cli/theme.py                   (Theme manager)
│   │   ├── ThemeManager class
│   │   ├── THEMES (defcon, standard, retro, slate)
│   │   ├── SYMBOLS (ASCII icons)
│   │   └── progress_bar()
│   │
│   └── cli/spinner.py                 (Loading indicators)
│
└── INTERACTION LAYER
    ├── typer (CLI framework)
    ├── Rich (Terminal UI)
    └── console.input() (User input)
```

---

## 🏗️ CLI Evolution Timeline

### Phase 0: Original CLI (Pre-Rich) **DEPRECATED**
- Plain text output
- Basic typer interface
- No colours or formatting
- **Status:** Replaced by Phase 1

### Phase 1: Rich Upgrade (Current Stable) **✓ COMPLETE**
**Files:** `cli/main.py`, `cli/rich_ui.py`, `cli/theme.py`, `cli/formatters.py`

**Enhancements:**
- ✓ Rich library integration
- ✓ Panel-based layouts for phases
- ✓ Colour-coded advisors
- ✓ Multi-theme support (DEFCON, Standard, Retro, Slate)
- ✓ Progress bars for metrics
- ✓ Formatted tables (resources, diplomacy)
- ✓ Box drawing characters
- ✓ Markdown rendering

**Key Features:**
```python
# Phase headers
console.print(phase_header("DISCUSSION", world.turn))

# Metrics display
console.print(metrics_table(world))

# Themed output
console.print(f"[{COLORS['primary']}]/status[/]")

# Progress bars
progress_bar(risk, 100, width=10)
```

**Status:** Stable, production-ready, user-tested

---

### Phase 2: Dashboard UI (Experimental) ⚠️ BLOCKED
**Files:** `cli/main_dashboard.py`, `cli/dashboard.py`

**Goal:** Persistent screen layout with fixed zones (like tmux/split-pane UIs)

**Layout:**
```
╭─────────────────────────────────────────────╮
│ HEADER: TURN | PHASE | TIME                 │
├──────────────────┬──────────────────────────┤
│ SIDEBAR          │ MAIN PANEL               │
│ - Metrics        │ - Conversation           │
│ - Risk bars      │ - Briefings              │
│ - Flags          │ - Dialogue               │
├──────────────────┴──────────────────────────┤
│ FOOTER: Available commands                  │
╰─────────────────────────────────────────────╯
```

**Status:** 
- Implementation: Complete (Phase 1)
- Automated testing: ✓ PASSED (8/8 unit, 5/5 integration)
- Manual testing: ✗ CRITICAL ISSUES (4 blockers)
- **BLOCKED:** Requires Phase 2.5 fixes before user testing

---

#### Phase 2 Implementation Guide

**Objective:** Build dashboard in parallel with original CLI (zero risk approach)

**File Structure After Implementation:**
```
cli/
├── main.py              ← Original (UNTOUCHED)
├── main_dashboard.py    ← Dashboard version (COPY + MODIFY)
├── dashboard.py         ← Dashboard layout class (NEW)
├── rich_ui.py           ← Shared components
├── theme.py             ← Themes (shared)
└── formatters.py        ← Text utils (shared)

tests/
├── test_dashboard.py    ← Dashboard unit tests (NEW)
└── test_cli_modes.py    ← Integration tests (NEW)
```

**Day 1: Create Dashboard Class**

Create `cli/dashboard.py`:

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
        """Render top bar: TURN | PHASE | TIME."""
        from cli.theme import theme_manager
        COLORS = theme_manager.get_colors()
        
        content = f"TURN {self.world.turn:03d} │ DISCUSSION PHASE │ 17:00 HRS"
        
        return Panel(
            f"[{COLORS['emphasis']} bold]{content}[/]",
            style=COLORS['primary'],
            box=box.ROUNDED,
            padding=(0, 2)
        )
    
    def render_sidebar(self) -> Panel:
        """Render left panel with live metrics."""
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
        """Render center panel with scrolling conversation."""
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
        """Render bottom bar with available commands."""
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

**Test the import:**
```powershell
python -c "from cli.dashboard import WargameDashboard; print('OK')"
```

**Day 2: Create Dashboard CLI**

```powershell
# Copy main.py to main_dashboard.py
Copy-Item cli/main.py cli/main_dashboard.py
```

Then modify ONLY the discussion phase section (~line 974):

```python
# FIND:
        # Discussion phase loop
        questions = []
        while True:
            user_input = typer.prompt(">").strip()

# REPLACE WITH:
        # Discussion phase loop - DASHBOARD MODE
        from cli.dashboard import WargameDashboard
        from rich.live import Live
        
        dashboard = WargameDashboard(world, console)
        questions = []
        
        with Live(dashboard.layout, console=console, refresh_per_second=2) as live:
            while True:
                dashboard.update()
                
                live.stop()
                user_input = console.input(f"[{COLORS['primary']}]>[/] ").strip()
                live.start()
                
                if not user_input:
                    continue
                
                dashboard.add_message("PM", user_input)
                
                # (Keep all original command handlers)
```

**Test both CLIs:**
```powershell
python -m cli.main --help              # Original
python -m cli.main_dashboard --help    # Dashboard
```

**Day 3: Create Tests**

See `tests/test_dashboard.py` and `tests/test_cli_modes.py` (already created)

**Rollback Strategy:**

If dashboard doesn't work:
```powershell
Remove-Item cli/main_dashboard.py
Remove-Item cli/dashboard.py
# Original CLI still works perfectly
```

---

### Phase 2.5: Dashboard Fixes (In Progress) 🔧
**Current Priority**

**Critical Issues Identified:**

1. **Commands Don't Display Output** - Rich.Live() erases console output
2. **Empty COBRA BRIEFING Panel** - Turn briefing not pre-populated
3. **DEFCON Colours Not Applied** - Dashboard uses default theme
4. **Confusing UX** - Commands appear to fail

**Fix Strategy:**
- Modal overlay system for commands (pauses Live updates)
- Pre-populate dashboard with turn briefing
- Force DEFCON theme in dashboard mode
- Timeline: 3-5 days

**Detailed Implementation:** See `DASHBOARD_FIX_PLAN.md` for:
- Root cause analysis
- Step-by-step implementation (Day 1-5)
- Code examples for modal overlays
- Testing procedures
- Success criteria

---

### Phase 3: CLI Enhancements (Future) 📅

**Potential Features:**
- Split-pane mode (narrative + status sidebar only)
- Keyboard shortcuts (Ctrl+S = status)
- Command history (up/down arrows)
- Autocomplete for commands
- Animated transitions
- Sound effects (optional)
- Screen reader support
- Custom keybindings
- Macro system
- Session recording/playback

**Priority:** TBD (after Phase 2.5 complete)

---

## 📂 File Reference Guide

### Core Interface Files

#### `cli/main.py` (2006 lines) **STABLE**
**Purpose:** Primary CLI entry point - scrolling interface

**Key Functions:**
- `play()` - Main game loop
- `batch()` - Non-interactive testing mode
- `intro()` - Display intro text
- `settings()` - LLM configuration

**Game Flow:**
```python
def play():
    # 1. Scenario selection
    # 2. Difficulty selection
    # 3. LLM configuration
    # 4. Intro sequence
    
    while game_active:
        # 5. Turn briefing
        # 6. Discussion phase  ← Command loop
        # 7. Decision phase
        # 8. Adjudication
```

**Commands Available:**
- `/decide` - End discussion, make decision
- `/quit` - Exit game
- `/save` - Save game state
- `/theme` - Change colour scheme
- `/status` - Show metrics
- `/menu` - Show command menu
- `/advise` - Get all advisor input
- `/resources` - Display forces/stockpiles
- `/call <country>` - Diplomatic encounter
- `/llm` - Change LLM settings
- Questions → Run through discussion system

**Dependencies:**
- typer (CLI framework)
- Rich (terminal UI)
- Engine (game logic)
- Models (data structures)

**Status:** Production-ready, do not modify without backup

---

#### `cli/main_dashboard.py` (2006 lines) **EXPERIMENTAL**
**Purpose:** Dashboard variant of main.py

**Differences from main.py:**
- Discussion phase uses `WargameDashboard` + `Rich.Live()`
- All other phases identical to main.py
- Commands need modal overlay pattern (not yet implemented)

**Status:** Broken, requires Phase 2.5 fixes

---

### Rendering Layer Files

#### `cli/rich_ui.py` (534 lines) **STABLE**
**Purpose:** Library of Rich UI components

**Components:**

```python
# Phase headers
phase_header(phase_name: str, turn: int) -> Panel

# Metrics display
metrics_table(world: WorldState) -> Table

# Advisor panel
advisor_menu_panel() -> Panel

# Diplomatic contacts
diplomatic_contacts_table(contacts: List) -> Table

# Military resources
resources_tables(initial_conditions: dict) -> Tuple[Table, Table]

# Command menu
command_menu() -> Panel

# Metrics guide
metrics_guide_panel() -> Panel

# Markdown formatting
format_markdown(text: str) -> str
```

**Usage Example:**
```python
from cli.rich_ui import console, phase_header, metrics_table

# Show phase
console.print(phase_header("BRIEFING", world.turn))

# Show metrics
console.print(metrics_table(world))
```

**Status:** Stable, shared by both CLIs

---

#### `cli/dashboard.py` (187 lines) ⚠️ EXPERIMENTAL
**Purpose:** Dashboard layout manager using Rich.Live + Rich.Layout

**Class:** `WargameDashboard`

**Methods:**
```python
class WargameDashboard:
    def __init__(self, world, console):
        # Create layout structure
        
    def render_header(self) -> Panel:
        # TURN | PHASE | TIME
        
    def render_sidebar(self) -> Panel:
        # Metrics with progress bars
        
    def render_main(self) -> Panel:
        # Conversation log (last 15 messages)
        
    def render_footer(self) -> Panel:
        # Available commands
        
    def update(self):
        # Refresh all panels
        
    def add_message(self, speaker: str, message: str):
        # Add to conversation log
```

**Usage:**
```python
dashboard = WargameDashboard(world, console)

with Live(dashboard.layout, refresh_per_second=2) as live:
    while True:
        dashboard.update()
        user_input = console.input("> ")
        dashboard.add_message("PM", user_input)
```

**Status:** Implemented but broken, needs Phase 2.5 fixes

---

#### `cli/formatters.py` **STABLE**
**Purpose:** Text formatting utilities

**Functions:**
```python
# Format advisor responses with indentation
format_advisor_response(advisor_name: str, response: str) -> str

# Wrap text to terminal width
wrap_text(text: str, width: int) -> str
```

**Status:** Stable, minimal

---

### Styling Layer Files

#### `cli/theme.py` (195 lines) **STABLE**
**Purpose:** Multi-theme colour system

**Themes Available:**
1. **DEFCON** (High-contrast ADHD-optimised)
   - Primary: Deep Orange (#FF6B35)
   - Critical: Pure Red (#FF0000)
   - Success: Teal (#00D9A3)
   - Background: Dark Navy (#0A0E27)

2. **Standard** (Professional calm)
   - Primary: Cyan (#00D9FF)
   - Success: Green (#00FF9C)
   - Warning: Amber (#FFB627)

3. **Retro** (Green phosphor terminal)
   - Monochrome green aesthetic
   - CRT simulation

4. **Slate** (Black/white monochrome)
   - Accessibility mode
   - High contrast

**Components:**
```python
# Theme manager (singleton)
theme_manager = ThemeManager()

# Get current colours
COLORS = theme_manager.get_colors()

# Switch theme
theme_manager.set_theme("defcon")

# Symbols (ASCII-only, no emoji)
SYMBOLS = {
    "risk": "▲",
    "stability": "■",
    "cohesion": "&",
    "casualties": "†",
    "warning": "!",
    # ... etc
}

# Progress bar
progress_bar(value: int, max_val: int, width: int) -> str
```

**Usage:**
```python
from cli.theme import theme_manager, COLORS, SYMBOLS

# Use themed colours
console.print(f"[{COLORS['primary']}]/status[/]")

# Use symbols
console.print(f"{SYMBOLS['risk']} Risk: 68")

# Show progress
bar = progress_bar(68, 100, 10)  # "██████░░░░"
```

**Status:** Stable, production-ready

---

#### `cli/spinner.py` **STABLE**
**Purpose:** Loading indicators for LLM calls

**Status:** Minimal, stable

---

## 🎨 Design System Integration

### Design Documents

**`MODERN_CLI_DESIGN_GUIDE.md`** - Master design reference

**Contents:**
- Core philosophy (spatial anchoring, live updates, ADHD-friendly)
- Layout patterns (dashboard, scrolling, hybrid)
- Colour schemes (DEFCON, Professional, Retro)
- Typography hierarchy
- Animation principles
- Accessibility guidelines
- Implementation examples

**Usage:** Reference when designing new CLI features

---

## 🔄 CLI Modes Comparison

### Scrolling Mode (`cli/main.py`) ✓
**Status:** Production, stable

**Pros:**
- Works reliably
- No visual glitches
- Familiar UX
- All commands work
- Battle-tested

**Cons:**
- Information scrolls away
- Hard to track metrics
- Need to type `/status` frequently
- Cognitive load (ADHD users)

**Best For:**
- First-time players
- Narrative focus
- Terminal accessibility needs
- Narrow terminals

---

### Dashboard Mode (`cli/main_dashboard.py`) ⚠️
**Status:** Experimental, blocked

**Pros (when fixed):**
- Metrics always visible
- No scrolling for UI elements
- Command hints visible
- ADHD-friendly
- Modern aesthetic

**Cons:**
- Currently broken (Phase 2.5 fixes needed)
- Commands don't work
- Briefing disappears
- Requires wider terminal (>80 cols)
- More complex code

**Best For:**
- Experienced players
- Metric-focused play
- Wide terminals (100+ cols)
- ADHD users (once fixed)

---

## 🛠️ Development Guidelines

### Modifying the CLI

**Golden Rules:**
1. **Never modify `cli/main.py` without backup** - It's the stable version
2. **Test in both modes** - If you touch shared files (rich_ui, theme)
3. **Keep dashboard optional** - Original CLI must always work
4. **Additive changes only** - Don't remove features
5. **Theme compatibility** - Work in all 4 themes
6. **Terminal width** - Support 80-120 cols minimum

---

### Adding New Commands

**Pattern:**
```python
# In cli/main.py (discussion phase loop)
if user_input.lower() in ["/newcmd", "newcmd"]:
    typer.echo("")
    
    if RICH_ENABLED:
        # Rich formatted output
        console.print(Panel("Command output", title="NEW COMMAND"))
    else:
        # Plain text fallback
        typer.echo("Command output")
    
    typer.echo("")
    continue
```

**For Dashboard Mode:**
```python
# Will need modal overlay pattern (once Phase 2.5 complete)
if user_input.lower() in ["/newcmd", "newcmd"]:
    from cli.dashboard_modal import show_overlay
    
    content = generate_command_output()
    show_overlay(console, live, "NEW COMMAND", content, COLORS)
    continue
```

---

### Adding New Themes

**Pattern:**
```python
# In cli/theme.py
THEMES["new_theme"] = {
    "primary": "#HEX",
    "secondary": "#HEX",
    "accent": "#HEX",
    "critical": "#HEX",
    "warning": "#HEX",
    "success": "#HEX",
    "neutral": "#HEX",
    "background": "#HEX",
    "text": "#HEX",
    "muted": "#HEX",
    "border": "#HEX",
    "emphasis": "#HEX",
    
    # Metric-specific
    "metric_critical": "#HEX",
    "metric_bad": "#HEX",
    "metric_neutral": "#HEX",
    "metric_good": "#HEX",
}
```

**Add to theme selection menu:**
```python
# In cli/main.py (theme command)
console.print("  5. New Theme Name")
theme_map = {"1": "standard", "2": "defcon1", "3": "retro", "4": "slate", "5": "new_theme"}
```

---

### Adding New Rich Components

**Pattern:**
```python
# In cli/rich_ui.py
def new_component_panel(data) -> Panel:
    """Create a panel for new feature.
    
    Args:
        data: Data to display
        
    Returns:
        Rich Panel
    """
    from cli.theme import theme_manager, COLORS, SYMBOLS
    COLORS = theme_manager.get_colors()
    
    content = f"[{COLORS['primary']}]{data}[/]"
    
    return Panel(
        content,
        title="[bold]NEW COMPONENT[/]",
        border_style=COLORS['border'],
        box=box.ROUNDED,
        padding=(1, 2)
    )
```

---

## 📊 Testing Strategy

### Test Levels

**Level 1: Unit Tests**
- Test individual components in isolation
- Rich UI components
- Theme manager
- Dashboard layout

**Files:** `tests/test_dashboard.py`, `tests/test_rich_ui.py` (future)

---

**Level 2: Integration Tests**
- Both CLIs can run
- Commands execute
- Themes switch
- Files are compatible

**Files:** `tests/test_cli_modes.py`

---

**Level 3: Manual Testing**
- Full gameplay in both modes
- Visual verification
- UX assessment
- ADHD user feedback

**Critical:** Automated tests gave false confidence in Phase 2. Manual testing essential.

---

### Testing Checklist

**Before Committing CLI Changes:**

- [ ] Original CLI (`cli/main.py`) still works
- [ ] Dashboard CLI (`cli/main_dashboard.py`) doesn't break further
- [ ] All 4 themes display correctly
- [ ] Commands work in both modes
- [ ] No visual glitches
- [ ] Terminal width 80-120 cols supported
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual smoke test complete
- [ ] Rollback tested

---

## 🚀 Development Roadmap

### Current State (November 2025)

**Production:**
- ✓ Scrolling CLI with Rich UI (cli/main.py)
- ✓ Multi-theme system (4 themes)
- ✓ Rich components library
- ✓ Text formatters
- ✓ All commands working

**Experimental:**
- ⚠️ Dashboard UI (broken, needs Phase 2.5 fixes)

---

### Short-term (Next 1-2 Weeks)

**Priority 1: Fix Dashboard**
- Implement modal overlay system
- Pre-populate COBRA BRIEFING
- Apply DEFCON colours
- Integration testing
- **Goal:** Dashboard usable for user testing

**Priority 2: Documentation**
- ✓ CLI_DEVELOPMENT_PACKAGE.md (this file)
- Update DASHBOARD_DEPLOYMENT_PACKAGE.md
- Create CLI troubleshooting guide

---

### Medium-term (Next 1-2 Months)

**Option A: Hybrid Mode**
- Keep scrolling narrative
- Add persistent status sidebar
- Best of both worlds
- Less risk than full dashboard

**Option B: Enhanced Scrolling**
- Improve original CLI
- Better command hints
- Inline metrics display
- Tab completion

**Option C: Both Modes Stable**
- Fix dashboard completely
- Keep both as options
- Let users choose

**Decision Point:** After Phase 2.5 and user testing

---

### Long-term (3+ Months)

**Potential Features:**
- Keyboard shortcuts
- Command history
- Session recording/playback
- Custom keybindings
- Screen reader support
- Internationalization
- Plugin system

---

## 📁 Package Contents

### Documentation Files

1. **`CLI_DEVELOPMENT_PACKAGE.md`** (This File) **★ MASTER**
   - Complete CLI system reference
   - Architecture overview
   - File-by-file guide
   - Development roadmap
   - **Dashboard deployment steps integrated**
   - **Fix plans integrated**
   - Testing procedures
   - Success criteria

2. **`MODERN_CLI_DESIGN_GUIDE.md`**
   - Design system
   - Colour schemes (DEFCON, Standard, Retro, Slate)
   - ADHD-friendly principles
   - Layout patterns
   - Implementation examples

3. **`DASHBOARD_FIX_PLAN.md`** (Detailed)
   - Extended Phase 2.5 analysis
   - Root cause deep-dive
   - Alternative approaches
   - Risk assessment

4. **`FULL_STACK_DEPLOYMENT_PACKAGE.md`**
   - CLI + Web App architecture
   - Feature parity matrix
   - Shared engine contract

5. **`DASHBOARD_DEPLOYMENT_PACKAGE.md`** (Archived)
   - Original dashboard-only deployment plan
   - **Superseded by this document**
   - Kept for historical reference

---

### Code Files

**Core:**
- `cli/main.py` (stable)
- `cli/main_dashboard.py` (experimental)

**Rendering:**
- `cli/rich_ui.py` (stable)
- `cli/dashboard.py` (experimental)
- `cli/formatters.py` (stable)

**Styling:**
- `cli/theme.py` (stable)
- `cli/spinner.py` (stable)

**Testing:**
- `tests/test_dashboard.py`
- `tests/test_cli_modes.py`
- `tests/TEST_RESULTS.md`

---

## 🔗 Related Systems

### Engine Layer
**Location:** `engine/`, `models/`  
**Contract:** CLI calls engine functions, engine returns data  
**Rule:** Never modify engine from CLI code

### Web UI Layer
**Location:** `api/`, `frontend/`  
**Relationship:** Parallel UI, shares engine  
**See:** `FULL_STACK_DEPLOYMENT_PACKAGE.md`

### Data Layer
**Location:** `data/scenarios/`  
**Format:** YAML scenario files  
**Rule:** CLI reads, never writes

---

## ⚠️ Known Issues

### Critical (Blocks Features)
1. Dashboard commands don't display output (Phase 2.5)
2. COBRA BRIEFING starts empty (Phase 2.5)
3. DEFCON colours not applied to dashboard (Phase 2.5)

### Major (Workarounds Exist)
- Dashboard requires wide terminal (>80 cols)
- Some symbols don't display on all terminals

### Minor (Low Impact)
- Theme switching doesn't persist across sessions
- No command autocomplete
- No keyboard shortcuts

**See:** `DASHBOARD_FIX_PLAN.md` for remediation

---

## 📞 Support & Resources

### If You Need To...

**Modify the original CLI:**
1. Backup `cli/main.py` first
2. Make changes incrementally
3. Test after each change
4. Commit frequently

**Add a new command:**
1. Read "Adding New Commands" section above
2. Implement in scrolling mode first
3. Test thoroughly
4. Add to dashboard mode (once Phase 2.5 complete)

**Change colours/themes:**
1. Modify `cli/theme.py`
2. Test in all 4 themes
3. Verify WCAG contrast ratios
4. Update design guide

**Fix a bug:**
1. Check if it affects both CLIs
2. Fix in original first
3. Test rollback capability
4. Document in TEST_RESULTS.md

---

## ✅ Final Checklist

**Before Deploying CLI Changes:**

**Code:**
- [ ] Original CLI works
- [ ] Dashboard doesn't break further
- [ ] All themes display correctly
- [ ] No regressions in commands
- [ ] Error handling present

**Testing:**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] ADHD users consulted (if UX change)

**Documentation:**
- [ ] Changes documented
- [ ] Known issues updated
- [ ] Roadmap adjusted if needed

**Safety:**
- [ ] Backup created
- [ ] Rollback tested
- [ ] Original CLI unaffected

---

---

## 🎯 Quick Start Guide

### I Want To...

**Understand the CLI system:**
→ Read "CLI System Architecture" section above

**Deploy the dashboard:**
→ Follow Phase 2 Implementation Guide (Day 1-3)

**Fix dashboard issues:**
→ Follow Phase 2.5 Fix Implementation (Day 1-5)

**Add a new command:**
→ See "Adding New Commands" in Development Guidelines

**Change themes/colours:**
→ See "Adding New Themes" in Development Guidelines

**Understand what's stable vs experimental:**
→ See "CLI Evolution Timeline" section

**Test my changes:**
→ See "Testing Strategy" section

---

**Package Version:** 1.0 (Master - All deployment steps integrated)  
**Last Updated:** 2025-11-23  
**Maintainer:** Development Team  
**Status:** ✓ Complete CLI System Documentation & Deployment Guide

**This is the MASTER CLI document. All deployment instructions are now integrated here.**

**Next Action:** Implement Phase 2.5 dashboard fixes (detailed steps included above)

