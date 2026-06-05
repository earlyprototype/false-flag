# Modern CLI Design Guide
**FALSE FLAG: THE WARGAME - Terminal Interface Design System**

*Inspired by: Vercel CLI, GitHub CLI, pnpm, Claude CLI, and Gemini CLI*

---

## Core Philosophy

> "A professional command interface should feel like a control panel, not a log file."

**Key Principles:**
1. **Spatial Anchoring:** Information stays in fixed zones
2. **Live Updates:** Screen rewrites instead of scrolling
3. **Restrained Animation:** Subtle, purposeful motion only
4. **Information Density:** Show essentials, hide details until needed
5. **ADHD-Friendly:** High contrast, clear hierarchy, predictable structure

---

## Visual Design System

### Layout Pattern: The Dashboard

```
╭───────────────────────────────────────────────────────────────────╮
│ HEADER (Fixed)                                                    │
│ Context: Turn, Phase, Time, Alert Level                          │
╰───────────────────────────────────────────────────────────────────╯
╭──────────────────────╮╭──────────────────────────────────────────╮
│ SIDEBAR (Fixed)      ││ MAIN CONTENT (Scrollable)                │
│                      ││                                          │
│ • Live Metrics       ││ • Narrative text                         │
│ • Status Indicators  ││ • Dialogue exchanges                     │
│ • Active Flags       ││ • Scene descriptions                     │
│                      ││                                          │
╰──────────────────────╯╰──────────────────────────────────────────╯
╭───────────────────────────────────────────────────────────────────╮
│ FOOTER (Fixed)                                                    │
│ Contextual Commands: /status /decide /call /quit                 │
╰───────────────────────────────────────────────────────────────────╯
```

**Zones:**
- **Header (3 lines):** Always visible context (where am I?)
- **Sidebar (30 chars wide):** Live-updating metrics
- **Main (flexible):** Scrolling content area
- **Footer (3 lines):** Available commands

---

## Colour Schemes

### Scheme 1: DEFCON (High Contrast ADHD-Optimised)
**Primary Palette:**
```python
DEFCON_COLORS = {
    # Core Functional Colours
    'primary':     '#FF6B35',  # Deep Orange - Interactive elements
    'secondary':   '#004E89',  # Navy Blue - Labels, structure
    'accent':      '#1A659E',  # Steel Blue - Phase headers
    
    # Status Colours (High Contrast)
    'critical':    '#FF0000',  # Pure Red - Danger, critical warnings
    'warning':     '#FFB627',  # Amber - Cautions, elevated risk
    'success':     '#00D9A3',  # Teal - Positive outcomes
    'neutral':     '#A8DADC',  # Light Blue - Stable states
    
    # UI Support
    'background':  '#0A0E27',  # Dark Navy - Background
    'text':        '#F1FAEE',  # Off-White - Primary text
    'muted':       '#457B9D',  # Muted Blue - Secondary info
    'border':      '#FF6B35',  # Deep Orange - Box borders
}
```

**Accessibility:**
- **Contrast Ratios:** All text meets WCAG AAA (7:1 minimum)
- **Colour Blindness:** Orange/Blue pairing works for all types
- **ADHD Support:** High contrast reduces cognitive load

**Usage:**
```python
# Interactive elements (commands, links)
console.print("[#FF6B35]/status[/#FF6B35]")

# Critical alerts
console.print("[#FF0000 bold]⚠ DEFCON 1 - NUCLEAR THREAT[/#FF0000 bold]")

# Positive feedback
console.print("[#00D9A3]✓ Alliance cohesion increased[/#00D9A3]")

# Borders and structure
Panel("Content", border_style="#FF6B35")
```

---

### Scheme 2: Professional Calm (Current Default)
**Primary Palette:**
```python
CALM_COLORS = {
    'primary':     'bright_cyan',    # Commands, interactive
    'secondary':   'cyan',           # Labels, advisor names
    'accent':      'bright_blue',    # Phase headers
    'success':     'green',          # Positive outcomes
    'warning':     'yellow',         # Cautions
    'danger':      'red',            # Critical warnings
    'muted':       'bright_black',   # Secondary info
    'normal':      'white',          # Default text
}
```

**When to Use:**
- Lower-stress scenarios
- Long play sessions (reduced eye strain)
- Users sensitive to high-contrast displays

---

### Scheme 3: Monochrome (Accessibility Fallback)
**Greyscale Palette:**
```python
MONO_COLORS = {
    'primary':     'bright_white',
    'secondary':   'white',
    'accent':      'bright_white',
    'success':     'bright_white',
    'warning':     'white',
    'danger':      'bright_white',
    'muted':       'bright_black',
    'normal':      'white',
}
```

**When to Use:**
- Accessibility requirements
- Colour-blind users
- E-ink displays or limited terminals

---

## Typography System

### Text Hierarchy

```python
# Level 1: Phase Headers (3 lines tall)
╭─────────────────────────────────────────╮
│ [BOLD BRIGHT_CYAN]                      │
│   TURN 004 │ DISCUSSION PHASE           │
│ [/]                                     │
╰─────────────────────────────────────────╯

# Level 2: Section Headers
[BOLD]SITUATION REPORT[/]

# Level 3: Labels
[CYAN]Risk Level:[/] ELEVATED

# Level 4: Body Text
Standard text with no formatting

# Level 5: Muted Text (timestamps, IDs)
[BRIGHT_BLACK]Last updated: 17:32[/]
```

### Indentation Rules
```python
# No indent: Headers
SITUATION REPORT

# 2 spaces: Primary content
  Risk: ELEVATED

# 4 spaces: Nested content
    ▲▲▲▲▲▲▁▁▁▁ (62/100)

# 6 spaces: Sub-nested (rare)
      • 7 SSBNs deployed
```

---

## Symbols & Icons

### Status Indicators
```python
SYMBOLS = {
    # Metrics
    'risk':        '▲',  # Triangle - Threat level
    'stability':   '■',  # Square - Foundation
    'cohesion':    '&',  # Ampersand - Alliance
    'casualties':  '†',  # Dagger - Deaths
    'influence':   '+',  # Plus - Political capital
    
    # Status
    'success':     '✓',  # Check mark
    'failure':     '✗',  # X mark
    'warning':     '!',  # Exclamation
    'info':        'i',  # Information
    'pending':     '~',  # Tilde - In progress
    
    # Actions
    'action':      '→',  # Arrow - Recommendation
    'note':        '*',  # Asterisk - Note
    
    # Entities
    'leader':      '#',  # Hash - Head of state
    'diplomat':    '•',  # Bullet - Ambassador
}
```

### Progress Bars
```python
def progress_bar(value: int, max_value: int, width: int = 10) -> str:
    """
    Visual progress indicator using █ and ▁
    
    Examples:
    - 60/100 (10 wide) → ██████▁▁▁▁
    - 30/100 (10 wide) → ███▁▁▁▁▁▁▁
    - 90/100 (10 wide) → █████████▁
    """
    filled = int((value / max_value) * width)
    return '█' * filled + '▁' * (width - filled)
```

---

## Animation Principles

### 1. Live Metric Updates
```python
# BEFORE: Scrolling mode (creates clutter)
print("Risk: 60")
time.sleep(5)
print("Risk: 65")  # New line appears

# AFTER: Live mode (updates in-place)
with Live(dashboard.layout, refresh_per_second=2):
    dashboard.metrics.risk = 60
    time.sleep(5)
    dashboard.metrics.risk = 65  # Same line changes
```

### 2. Spinners (During LLM Calls)
```python
# Rich provides built-in spinners:
from rich.spinner import Spinner

spinner = Spinner("dots", text="Generating response...")
# Cycles: ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

**Rules:**
- **Use sparingly:** Only for operations >2 seconds
- **Descriptive text:** "Generating response..." not "Loading..."
- **Stop on completion:** Replace with ✓ or result

### 3. Colour Transitions
```python
# Metric changes colour to indicate state change
# Before: [cyan]Risk: 60[/cyan] (Normal)
# After:  [red bold]Risk: 75[/red bold] (Critical)
```

**Rules:**
- Transition from **dim → bright** when updated
- Use **colour + symbol** (not colour alone)
- Maintain colour for 3-5 seconds before dimming

---

## Information Density

### The "At-a-Glance" Test
**Goal:** User should assess situation in <3 seconds

**Good Example (Sidebar):**
```
SITUATION REPORT
▲ Risk:      CRITICAL 75  ██████████
■ Stability: WEAK 35      ███▁▁▁▁▁▁▁
& Cohesion:  UNSTABLE 25  ██▁▁▁▁▁▁▁▁
! 3 ACTIVE FLAGS
```
✓ All critical info visible  
✓ Colour-coded states  
✓ Visual bars for quick scanning

**Bad Example (Information Overload):**
```
DETAILED METRICS BREAKDOWN
Escalation Risk: 75/100 (Previous: 60, Delta: +15)
  - Threshold: 80 (DEFCON 2)
  - Rate of change: +5 per turn
  - Projected: 90 by Turn 6
Domestic Stability: 35/100 (Previous: 45, Delta: -10)
  - Public confidence: LOW
  - Economic impact: MODERATE
  - Infrastructure: DEGRADED
...
```
✗ Too much detail  
✗ Requires reading  
✗ Cognitive overload

**Solution:** Summary in sidebar, details on `/status` command

---

## ADHD-Friendly Design Features

### 1. Visual Anchors
**Problem:** User loses place when scrolling  
**Solution:** Fixed header always shows context
```
╭────────────────────────────────────╮
│ TURN 004 │ DISCUSSION │ 17:00 HRS │ ← Always visible
╰────────────────────────────────────╯
```

### 2. Chunking
**Problem:** Walls of text are overwhelming  
**Solution:** Break into digestible blocks
```
NSA: [Short paragraph]

[Blank line]

CDS: [Short paragraph]

[Blank line]
```

### 3. Predictable Structure
**Problem:** Inconsistent layouts cause confusion  
**Solution:** Same zones in every phase
- Header = always top
- Metrics = always left sidebar
- Dialogue = always main area
- Commands = always footer

### 4. High Contrast Borders
**Problem:** Hard to see where sections begin/end  
**Solution:** Use deep orange borders (DEFCON scheme)
```
╭─────────────────────╮  ← Bright orange border
│ COBRA BRIEFING      │
╰─────────────────────╯
```

### 5. Progress Indicators
**Problem:** Waiting without feedback causes anxiety  
**Solution:** Show progress for all operations
```
⠋ Generating response...  ← Spinner
█████▁▁▁▁▁ Analysing...   ← Progress bar
```

### 6. Reduced Motion (Optional)
**Problem:** Animations can be distracting  
**Solution:** Environment variable to disable
```python
WARGAME_REDUCED_MOTION=true  # No spinners, instant updates
```

---

## Implementation Guidelines

### Using Rich.Live for Dashboard

```python
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel

class WargameDashboard:
    def __init__(self):
        self.layout = Layout()
        
        # Split into zones
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="main", ratio=1)
        )
    
    def render(self):
        """Update all zones"""
        self.layout["header"].update(self.render_header())
        self.layout["sidebar"].update(self.render_sidebar())
        self.layout["main"].update(self.render_main())
        self.layout["footer"].update(self.render_footer())
        
        return self.layout
    
    def run(self):
        """Main loop with live updates"""
        with Live(self.layout, refresh_per_second=2) as live:
            while True:
                # Update dashboard
                self.render()
                
                # Handle input (pause live updates)
                live.stop()
                user_input = console.input("> ")
                live.start()
                
                # Process input...
```

### Input Handling in Live Mode

**Challenge:** `typer.prompt()` blocks terminal  
**Solution:** Use `console.input()` with pause/resume

```python
with Live(dashboard.layout) as live:
    while True:
        live.stop()  # Pause dashboard
        user_input = console.input("> ")
        live.start()  # Resume dashboard
        
        # Process input
        response = get_advisor_response(user_input)
        dashboard.add_message(response)
```

---

## Responsive Design

### Terminal Width Adaptation

```python
def get_layout_mode(width: int) -> str:
    """Choose layout based on terminal width"""
    if width >= 120:
        return "full"      # Header | Sidebar | Main | Footer
    elif width >= 80:
        return "compact"   # Header | Main | Footer (no sidebar)
    else:
        return "minimal"   # Main only (no fixed zones)
```

**Full Mode (120+ chars):**
```
╭─ HEADER ─────────────────────────────────────────────────╮
│ TURN 004 │ DISCUSSION │ 17:00 HRS                        │
╰──────────────────────────────────────────────────────────╯
╭─ SIDEBAR ───╮╭─ MAIN ────────────────────────────────────╮
│ Metrics     ││ Dialogue                                  │
╰─────────────╯╰───────────────────────────────────────────╯
```

**Compact Mode (80-119 chars):**
```
╭─ HEADER ─────────────────────────────────────╮
│ TURN 004 │ DISCUSSION                        │
╰───────────────────────────────────────────────╯
╭─ MAIN ────────────────────────────────────────╮
│ Dialogue                                      │
│ [Metrics at top or via /status command]      │
╰───────────────────────────────────────────────╯
```

**Minimal Mode (<80 chars):**
```
TURN 004 | DISCUSSION
─────────────────────
Dialogue...
```

---

## Testing & Quality Assurance

### Visual Test Suite
```python
# test_dashboard.py
def test_header_always_visible():
    """Header must remain visible during scroll"""
    assert dashboard.layout["header"].visible == True

def test_colour_contrast():
    """All text must meet WCAG AAA (7:1 ratio)"""
    for color in DEFCON_COLORS.values():
        assert contrast_ratio(color, background) >= 7.0

def test_width_adaptation():
    """Layout must adapt to terminal width"""
    for width in [60, 80, 100, 120]:
        layout = get_layout_mode(width)
        assert layout in ["minimal", "compact", "full"]
```

### User Testing Checklist
- [ ] Can user identify current turn in <1 second?
- [ ] Can user find available commands in <2 seconds?
- [ ] Can user assess situation risk in <3 seconds?
- [ ] Do colour transitions feel smooth (not jarring)?
- [ ] Are spinners visible but not distracting?
- [ ] Does dashboard work on Windows PowerShell?
- [ ] Does fallback work with `WARGAME_RICH_UI=false`?

---

## Configuration & Feature Flags

### Environment Variables
```bash
# Enable/disable Rich UI
export WARGAME_RICH_UI=true          # Default: true

# Choose colour scheme
export WARGAME_COLOR_SCHEME=defcon   # Options: defcon, calm, mono

# Enable/disable dashboard mode
export WARGAME_DASHBOARD_MODE=true   # Default: false (legacy scrolling)

# Accessibility options
export WARGAME_REDUCED_MOTION=false  # Disable animations
export WARGAME_HIGH_CONTRAST=true    # Force DEFCON scheme
```

### User Preferences File
```yaml
# config/ui_preferences.yaml
color_scheme: defcon
dashboard_mode: true
reduced_motion: false
refresh_rate: 2  # Updates per second
sidebar_width: 30
font_size: normal  # Affects spacing
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1)
- [x] Create `cli/theme.py` with DEFCON colour scheme
- [x] Create `cli/formatters.py` with text utilities
- [ ] Create `cli/dashboard.py` with `WargameDashboard` class

### Phase 2: Integration (Week 2)
- [ ] Integrate dashboard into discussion phase
- [ ] Test on Windows PowerShell
- [ ] Add feature flag for rollback

### Phase 3: Expansion (Week 3)
- [ ] Extend to all interactive phases
- [ ] Add spinners for LLM calls
- [ ] Polish animations

### Phase 4: User Testing (Week 4)
- [ ] A/B test with 5+ users
- [ ] Gather feedback on ADHD-friendliness
- [ ] Refine based on feedback

---

## Success Metrics

### Quantitative
- **Reduced time to assess situation:** From 10 seconds → <3 seconds
- **Command discovery:** 90%+ users find commands without `/help`
- **Error rate:** <5% mistyped commands (footer hints reduce errors)

### Qualitative
- **Professional feel:** "Looks like a real command center"
- **ADHD support:** "Easier to focus, less overwhelming"
- **Confidence:** "I know where I am and what I can do"

---

## References

### Inspiration Sources
1. **Vercel CLI** - Fixed header/footer pattern
2. **GitHub CLI** - Status bar, contextual commands
3. **pnpm** - Progress indicators, information density
4. **Claude CLI** - Professional calm aesthetic
5. **Gemini CLI** - Restrained animation
6. **Bubble Tea (Go)** - Live update architecture
7. **Ink (Node.js)** - React-style component model

### Design Systems
- **Tailwind CSS** - Colour function semantics
- **VSCode Dark+** - Syntax highlighting patterns
- **Nord/Dracula** - Low-contrast colour schemes
- **Material Design** - Accessibility guidelines (WCAG AAA)

### ADHD Research
- **Cognitive Load Theory** (Sweller, 1988)
- **Visual Hierarchy** (Gestalt Principles)
- **Attention & Focus** (Nielsen Norman Group)

---

## Appendix: Quick Reference

### Colour Palette (DEFCON Scheme)
```
PRIMARY:   #FF6B35 (Deep Orange)
SECONDARY: #004E89 (Navy Blue)
CRITICAL:  #FF0000 (Pure Red)
WARNING:   #FFB627 (Amber)
SUCCESS:   #00D9A3 (Teal)
MUTED:     #457B9D (Muted Blue)
```

### Symbol Set
```
▲ Risk    ■ Stability    & Cohesion    † Casualties    + Influence
✓ Success ✗ Failure      ! Warning     → Action        * Note
# Leader  • Diplomat     ~ Pending     i Info
```

### Layout Dimensions
```
Header:  3 lines (fixed)
Sidebar: 30 chars wide (fixed)
Footer:  3 lines (fixed)
Main:    Remaining space (flexible)
```

---

**Last Updated:** 2025-11-22  
**Version:** 1.0  
**Maintainer:** Development Team

