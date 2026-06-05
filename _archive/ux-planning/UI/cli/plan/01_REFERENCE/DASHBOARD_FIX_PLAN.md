# Dashboard Fix Implementation Plan
**FALSE FLAG: THE WARGAME - Dashboard Repair Roadmap**

**Date:** 2025-11-23  
**Status:** BROKEN - Needs Architectural Fixes  
**Priority:** HIGH

---

## Issues Identified During Testing

### Critical Issues

1. **Live() Overwrites Command Output**
   - **Problem:** `Rich.Live()` refreshes 2x/second, erasing any `typer.echo()` or `console.print()` output
   - **Impact:** `/menu`, `/advise`, `/status`, `/resources` commands execute but output vanishes immediately
   - **Severity:** CRITICAL - Makes dashboard unusable

2. **Empty COBRA BRIEFING Panel**
   - **Problem:** Turn inject/briefing text not pre-populated in dashboard
   - **Impact:** Player enters discussion phase with no context
   - **Severity:** CRITICAL - No narrative flow

3. **Missing DEFCON Colour Scheme**
   - **Problem:** Dashboard uses default colours, not the high-contrast DEFCON scheme from design guide
   - **Impact:** Visually boring, defeats ADHD-friendly design goals
   - **Severity:** MAJOR - Doesn't match design specification

4. **Commands Appear to Fail**
   - **Problem:** User types command, sees prompt redraw, nothing happens
   - **Impact:** Feels broken, confusing UX
   - **Severity:** CRITICAL - User trust destroyed

---

## Root Cause Analysis

### Architecture Problem: Rich.Live() vs Interactive Commands

**The Issue:**
```python
with Live(dashboard.layout, refresh_per_second=2) as live:
    while True:
        dashboard.update()  # Redraws ENTIRE screen
        
        live.stop()
        user_input = console.input("> ")
        live.start()
        
        if user_input == "/menu":
            console.print(menu_panel())  # ← Gets erased by next update()!
            # Live resumes, overwrites output
```

**Why It Fails:**
- `Live()` continuously repaints the dashboard layout
- Any output printed outside the dashboard panels disappears
- Commands that expect to show multi-line output (like `/advise` with 5 advisor responses) can't work

**What We Need Instead:**
- Commands must UPDATE dashboard panels, not print to console
- OR commands must pause Live, show full-screen overlay, then resume
- OR commands must use modal panels within the dashboard structure

---

## Fix Strategy

### Phase 1: Make Commands Work (Priority 1)

**Approach:** Modal overlays that pause Live updates

```python
def show_command_overlay(title, content_fn):
    """Show full-screen overlay, pausing dashboard."""
    live.stop()  # Pause live updates
    
    # Clear screen
    console.clear()
    
    # Show overlay
    panel = Panel(
        content_fn(),
        title=title,
        border_style=COLORS['primary']
    )
    console.print(panel)
    
    # Wait for user
    console.input("\nPress ENTER to return to dashboard...")
    
    # Resume dashboard
    console.clear()
    live.start()
```

**Commands to Fix:**
- `/menu` → Show advisor list, diplomatic contacts, metrics guide as overlay
- `/advise` → Collect all 5 advisor responses, show in overlay panel
- `/status` → Full metrics + flags as overlay
- `/resources` → Forces/stockpiles tables as overlay

**Implementation:**
1. Create `dashboard_modal.py` with overlay functions
2. Modify command handlers in `main_dashboard.py` to use overlays
3. Add "Press ENTER to return" instruction
4. Clear screen before resuming dashboard

---

### Phase 2: Populate COBRA BRIEFING (Priority 1)

**Problem:** Briefing panel starts empty - player has no context

**Solution:** Pre-populate with turn inject

```python
# In run_turn_briefing (before discussion):
briefing_lines = run_turn_briefing(world, scenario, rng, root, transcript)

# BEFORE entering Live():
dashboard = WargameDashboard(world, console)

# Add briefing to conversation log
for line in briefing_lines:
    if ":" in line:
        speaker, message = line.split(":", 1)
        dashboard.add_message(speaker.strip(), message.strip())
    else:
        dashboard.add_message("NARRATOR", line)

# NOW start Live() with populated dashboard
with Live(dashboard.layout, ...) as live:
    ...
```

**Fallback:** If briefing too long (>15 lines), show last 15 lines + indicator:

```python
dashboard.add_message("SYSTEM", "[Earlier briefing scrolled - type /briefing to review]")
```

**Add `/briefing` command:** Shows full turn inject in overlay

---

### Phase 3: Apply DEFCON Colour Scheme (Priority 2)

**Current:** Dashboard uses `theme_manager.get_colors()` which defaults to "standard"

**Fix:** Force DEFCON scheme in dashboard mode

**In `cli/dashboard.py`:**

```python
from cli.theme import theme_manager

class WargameDashboard:
    def __init__(self, world, console):
        # Force DEFCON theme for dashboard
        theme_manager.set_theme("defcon")
        self.COLORS = theme_manager.get_colors()
        
        # ... rest of init
```

**Update Panels:**

```python
def render_header(self):
    return Panel(
        f"[{self.COLORS['emphasis']} bold]{content}[/]",
        style=self.COLORS['primary'],  # Deep orange border
        box=box.HEAVY,  # Use heavy box for DEFCON aesthetic
        padding=(0, 2)
    )

def render_sidebar(self):
    # Risk - red when high
    if risk >= 70:
        risk_style = f"[{self.COLORS['metric_critical']} bold]"
    elif risk >= 50:
        risk_style = f"[{self.COLORS['metric_bad']}]"
    else:
        risk_style = f"[{self.COLORS['metric_good']}]"
    
    table.add_row(
        f"{SYMBOLS['risk']} RISK",
        f"{risk_style}{risk}[/]",
        progress_bar(risk, 100, 10, danger=True)
    )
```

**DEFCON Colours Reference:**
- `primary`: #FF6B35 (Deep Orange) - Borders, interactive
- `critical`: #FF0000 (Pure Red) - High risk
- `warning`: #FFB627 (Amber) - Medium risk
- `success`: #00D9A3 (Teal) - Low risk
- `secondary`: #004E89 (Navy Blue) - Labels

---

### Phase 4: Enhanced Conversation Display (Priority 3)

**Current:** Last 15 messages, plain text

**Better:** Format with speaker colours, timestamps, visual hierarchy

```python
def render_main(self):
    content_lines = []
    
    for msg in self.conversation_log[-15:]:
        # Already formatted with colours from add_message()
        content_lines.append(msg)
    
    # Add separator between messages
    formatted = "\n\n".join(content_lines)  # Double-space for readability
    
    # If no messages, show helpful hint
    if not content_lines:
        formatted = f"[{self.COLORS['muted']} italic]Ask advisors questions or type /advise for panel input[/]"
    
    return Panel(
        formatted,
        title=f"[{self.COLORS['accent']} bold]COBRA BRIEFING[/]",
        border_style=self.COLORS['secondary'],
        box=box.ROUNDED,
        padding=(1, 2),
        height=20  # Fixed height
    )
```

**Colour Code Speakers:**
- PM: `emphasis` (bright)
- NSA: `secondary` 
- CDS: `warning` (amber - military)
- Foreign Sec: `success` (teal - diplomacy)
- Home Sec: `primary` (orange - domestic)
- Attorney General: `muted` (grey - legal)

---

### Phase 5: Add Command Hints in Context (Priority 3)

**Update Footer Dynamically:**

```python
def render_footer(self):
    # Show relevant commands based on context
    if len(self.conversation_log) == 0:
        hints = "/advise to get panel input  |  Ask questions  |  /decide when ready"
    else:
        hints = "/status  /menu  /resources  /call <country>  /decide  /quit"
    
    return Panel(
        f"[{self.COLORS['muted']}]{hints}[/]",
        style=self.COLORS['border'],
        box=box.ROUNDED,
        padding=(0, 2)
    )
```

---

## Implementation Checklist

### Week 1: Critical Fixes

**Day 1-2: Command Overlays**
- [ ] Create `cli/dashboard_modal.py`
- [ ] Implement `show_command_overlay(title, content_fn)`
- [ ] Refactor `/menu` to use overlay
- [ ] Refactor `/advise` to use overlay
- [ ] Refactor `/status` to use overlay
- [ ] Refactor `/resources` to use overlay
- [ ] Test all commands work and return to dashboard

**Day 3: Briefing Population**
- [ ] Modify discussion phase entry to pre-populate dashboard
- [ ] Add `/briefing` command to review full inject
- [ ] Test briefing appears in COBRA BRIEFING panel
- [ ] Test conversation log scrolls correctly

**Day 4: DEFCON Colours**
- [ ] Force DEFCON theme in dashboard init
- [ ] Update all panel borders to deep orange
- [ ] Apply conditional colouring to metrics (red/amber/teal)
- [ ] Update speaker colours in add_message()
- [ ] Test high-contrast appearance

**Day 5: Testing & Polish**
- [ ] Run through full turn with dashboard
- [ ] Verify all commands work
- [ ] Check colour contrast
- [ ] Get ADHD user feedback
- [ ] Fix any visual glitches

---

### Week 2: Enhancements

**Optional Improvements:**
- [ ] Add `/briefing` overlay to review turn inject
- [ ] Animated progress bars for metrics
- [ ] Flash border red when risk exceeds threshold
- [ ] Add turn history (previous turn summary)
- [ ] Keyboard shortcuts (Ctrl+S = status, etc.)

---

## Code Structure Changes

### New Files

**`cli/dashboard_modal.py`** (NEW)
```python
"""Modal overlay system for dashboard commands."""

from rich.panel import Panel
from rich.console import Console

def show_overlay(console, live, title, content, colors):
    """Show full-screen overlay, pausing dashboard.
    
    Args:
        console: Rich Console
        live: Rich Live instance
        title: Panel title
        content: Renderable content
        colors: Color dict from theme
    """
    live.stop()
    console.clear()
    
    panel = Panel(
        content,
        title=f"[{colors['accent']} bold]{title}[/]",
        border_style=colors['primary'],
        padding=(2, 4)
    )
    console.print(panel)
    console.print(f"\n[{colors['muted']}]Press ENTER to return to dashboard...[/]")
    console.input()
    
    console.clear()
    live.start()
```

### Modified Files

**`cli/dashboard.py`**
- Add DEFCON theme forcing
- Update colours in all render methods
- Add speaker-specific colour coding
- Improve conversation formatting

**`cli/main_dashboard.py`**
- Import dashboard_modal
- Refactor command handlers to use overlays
- Pre-populate dashboard with briefing
- Add `/briefing` command

---

## Testing Plan

### Unit Tests

**`tests/test_dashboard_modals.py`** (NEW)
```python
def test_overlay_pauses_live():
    """Verify overlay stops/starts Live correctly."""
    # Test that Live.stop() called
    # Test that console.clear() called
    # Test that Live.start() called after input

def test_overlay_displays_content():
    """Verify content renders in panel."""
    # Mock console and Live
    # Call show_overlay()
    # Verify Panel created with content
```

### Integration Tests

**Manual Testing Checklist:**
- [ ] Start dashboard mode
- [ ] Verify briefing appears in COBRA BRIEFING panel
- [ ] Type `/menu` - overlay appears, ENTER returns to dashboard
- [ ] Type `/advise` - all 5 advisors respond in overlay
- [ ] Type `/status` - full metrics appear
- [ ] Type `/resources` - forces/stockpiles appear
- [ ] Ask question - appears in log
- [ ] Advisor response - appears in log
- [ ] Type `/decide` - exits to decision phase
- [ ] Colours match DEFCON scheme (orange/blue/red)

---

## Success Criteria (Revised)

### Must Have (Critical)
- [ ] All commands (`/menu`, `/advise`, `/status`, `/resources`) work and display output
- [ ] Turn briefing pre-populated in COBRA BRIEFING panel
- [ ] Conversation log shows questions and responses
- [ ] DEFCON colour scheme applied (high contrast)
- [ ] Dashboard doesn't erase command output
- [ ] Can complete full turn using dashboard

### Should Have (Important)
- [ ] Commands use overlay pattern (clean UX)
- [ ] Speaker-specific colour coding
- [ ] `/briefing` command to review inject
- [ ] Contextual footer hints
- [ ] Smooth transitions (no flickering)

### Nice to Have (Optional)
- [ ] Animated metrics
- [ ] Turn history panel
- [ ] Keyboard shortcuts
- [ ] Terminal size detection/adaptation

---

## Risk Assessment

### Technical Risks

**Risk:** Modal overlays still feel clunky
**Mitigation:** User testing, consider alternative (split-pane?) approaches

**Risk:** DEFCON colours too intense for some users
**Mitigation:** Keep `/theme` command to switch back to standard

**Risk:** Terminal size issues (too narrow)
**Mitigation:** Detect width, use compact layout if < 100 cols

### Timeline Risks

**Risk:** 1 week may not be enough
**Mitigation:** Focus on Phase 1 (commands work) first, defer enhancements

---

## Rollback Plan

If fixes don't work by Week 1 end:

**Option 1:** Keep original CLI as default
```powershell
# main.py stays stable
# main_dashboard.py becomes experimental branch
```

**Option 2:** Hybrid approach
- Add status sidebar to original CLI
- Skip full dashboard complexity
- Faster to implement, less risky

**Option 3:** Defer dashboard to future milestone
- Document learnings
- Focus on other features (web UI, diplomacy)
- Revisit when Rich.Live() patterns better understood

---

## Next Steps

**Immediate Actions:**
1. Create `cli/dashboard_modal.py`
2. Implement overlay pattern for one command (`/menu`) as proof-of-concept
3. Test thoroughly
4. If successful, apply pattern to other commands
5. Add briefing population
6. Apply DEFCON colours
7. Full integration test

**Estimated Time:** 3-5 days of focused development

---

**Document Status:** READY FOR IMPLEMENTATION  
**Last Updated:** 2025-11-23  
**Author:** Development Team

