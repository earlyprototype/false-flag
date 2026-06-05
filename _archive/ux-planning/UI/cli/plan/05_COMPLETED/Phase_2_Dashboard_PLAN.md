# CLI Dashboard Implementation Plan
**Inspired by: Vercel CLI, GitHub CLI, and Modern Terminal UIs**

## Objective
Transform the FALSE FLAG CLI from a "scrolling log" (typewriter mode) into a **persistent dashboard** (live layout mode) that feels like a professional command & control interface.

---

## Design Principles (Learned from Exemplars)

### 1. **Spatial Anchoring** (Vercel/GitHub CLI Pattern)
Modern CLIs use **fixed zones** instead of continuous scrolling:
- **Header:** Always visible at top (context: turn, phase, time)
- **Sidebar:** Persistent metrics that update in-place
- **Main:** Scrolling content area (narrative, dialogue)
- **Footer:** Always-visible command hints

### 2. **Live Updates** (Ink/Bubble Tea Pattern)
Instead of printing new lines, **rewrite the screen**:
- Metrics change colour instantly (no reprinting tables)
- Spinners animate in-place during LLM calls
- Progress bars update smoothly

### 3. **Restrained Animation** (Professional Calm)
- No flashing colours or distracting effects
- Smooth transitions (fade-in text, not instant)
- Subtle state changes (dim -> bright on update)

### 4. **Information Density** (Claude/Gemini CLI Pattern)
- Show **just enough** data per screen
- Use collapsible sections for details
- Avoid overwhelming the user with 200-line dumps

---

## Technical Stack

### **Rich vs Textual (Decision)**
**Current:** We use `Rich` for formatting (colours, tables, panels).  
**Upgrade Path:** Add `Textual` (by the same author) for full TUI capabilities.

| Feature | Rich | Textual |
|---------|------|---------|
| Static output | ✅ Yes | ✅ Yes |
| Tables/Panels | ✅ Yes | ✅ Yes |
| Live updating | ⚠️ Limited (`Live` context) | ✅ Full (reactive framework) |
| Layout management | ⚠️ Manual (`Layout`) | ✅ Built-in (flexbox/grid) |
| Event handling | ❌ No | ✅ Yes (keyboard, mouse) |
| Learning curve | Low | Medium |

**DECISION:** Start with **Rich.Live + Rich.Layout** (low-risk upgrade), then migrate to **Textual** if we need more interactivity (e.g., clickable menus).

---

## Implementation Plan

### **Phase 1: Proof of Concept (Non-Invasive)**
**Goal:** Build a minimal dashboard for the **Discussion Phase** only, without touching the narrative scrolling system.

#### 1.1 Create `cli/dashboard.py`
A new file that encapsulates the dashboard logic:
```python
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

class WargameDashboard:
    def __init__(self, world, console):
        self.world = world
        self.console = console
        self.layout = Layout()
        
        # Define layout structure
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["body"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="main", ratio=1)
        )
    
    def render_header(self):
        """Fixed header: TURN 4 | DISCUSSION | 17:00 HRS"""
        # Return a Panel with turn/phase/time
        pass
    
    def render_sidebar(self):
        """Fixed sidebar: Live metrics"""
        # Return a Table with Risk/Stability/Cohesion
        pass
    
    def render_main(self, content):
        """Scrolling main area"""
        # Return a Panel with the current dialogue
        pass
    
    def render_footer(self):
        """Fixed footer: Available commands"""
        # Return a Panel with /status /decide /quit
        pass
    
    def update(self, new_content):
        """Update the dashboard with new content"""
        self.layout["header"].update(self.render_header())
        self.layout["sidebar"].update(self.render_sidebar())
        self.layout["main"].update(self.render_main(new_content))
        self.layout["footer"].update(self.render_footer())
```

#### 1.2 Integrate into `cli/main.py` (Discussion Phase Only)
In the discussion phase loop, wrap the interaction in a `Live` context:
```python
# BEFORE (current scrolling mode):
while True:
    user_input = typer.prompt(">")
    # ... handle commands ...
    # Print advisor response
    console.print(advisor_response)

# AFTER (dashboard mode):
dashboard = WargameDashboard(world, console)
conversation_log = []  # Store dialogue history

with Live(dashboard.layout, console=console, refresh_per_second=4):
    while True:
        # Input happens OUTSIDE the Live context (pause updates)
        # Use a custom input handler that doesn't interfere with Live
        user_input = prompt_in_dashboard(">")
        
        conversation_log.append(f"PM: {user_input}")
        
        # Get advisor response
        advisor_response = run_turn_discussion(...)
        conversation_log.append(f"Advisor: {advisor_response}")
        
        # Update dashboard
        dashboard.update(conversation_log[-10:])  # Show last 10 messages
```

**CRITICAL:** The `Live` context needs to be paused during `typer.prompt()` calls. This requires a custom input function that temporarily exits `Live`, gets input, then re-enters.

#### 1.3 Testing
- Run a game and enter the discussion phase
- Verify that:
  - Header shows correct turn/phase
  - Sidebar updates when metrics change (e.g., after `/call USA`)
  - Main area scrolls dialogue
  - Footer shows available commands
- Ensure SPACE-to-skip still works in briefing phase (untouched)

---

### **Phase 2: Expand to All Phases**
Once the discussion phase works, apply the same pattern to:
- **Briefing Phase:** Header + Main (no sidebar needed for narrative)
- **Decision Phase:** Header + Main + Footer (decision prompt)
- **Adjudication Phase:** Header + Main (effects display)

**Narrative Scrolling (Intro/Briefing):** Keep the existing `scroll_text()` system. The dashboard is **opt-in** for interactive phases only.

---

### **Phase 3: Advanced Features (Post-MVP)**
Once the basic dashboard is stable:
- **Live Spinners:** Show a spinner in the sidebar during LLM calls
- **Collapsible Panels:** Add a `/intel` panel that can be toggled
- **Hotkeys:** `F1` = Help, `F2` = Metrics, `Ctrl+S` = Save
- **Textual Migration:** If we need clickable menus or more complex layouts, migrate to the Textual framework

---

## Design Mockup (Discussion Phase)

```
╭─────────────────────────────────────────────────────────────────────────╮
│ TURN 004 │ DISCUSSION PHASE │ 17:00 HRS │ DEFCON 3                      │
╰─────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────╮╭───────────────────────────────────────────╮
│ SITUATION REPORT         ││ COBRA BRIEFING                            │
│                          ││                                           │
│ ▲ Risk:      ELEVATED 62 ││ NSA: Prime Minister, Russian submarine    │
│ ■ Stability: WEAK 45     ││ activity has increased 40% in the last    │
│ & Cohesion:  STABLE 52   ││ 6 hours. We assess...                     │
│ † Casualties: 2 mil      ││                                           │
│ + Influence:  +1         ││ > NSA, what's the threat level?           │
│                          ││                                           │
│ FLAGS:                   ││ NSA: CRITICAL. If they continue on this   │
│ ! US Commitment Uncertain││ trajectory, they could be in strike       │
│                          ││ range within 12 hours...                  │
╰──────────────────────────╯╰───────────────────────────────────────────╯
╭─────────────────────────────────────────────────────────────────────────╮
│ /status /menu /advise /resources /decide /save /quit                    │
╰─────────────────────────────────────────────────────────────────────────╯
> _
```

---

## Risk Mitigation

### **Risk 1: Input Handling Conflicts**
**Problem:** `typer.prompt()` and `Live` both control the terminal.  
**Solution:** Use `console.input()` (Rich's built-in input) or temporarily suspend `Live` during input.

### **Risk 2: Windows Compatibility**
**Problem:** `msvcrt.kbhit()` (used for SPACE-to-skip) might conflict with `Live`.  
**Solution:** Test thoroughly on Windows. Keep the keyboard handling in the narrative phase (which doesn't use `Live`).

### **Risk 3: Performance**
**Problem:** Redrawing the screen 4x per second might lag on slow terminals.  
**Solution:** Set `refresh_per_second=2` (default is 4). Profile if needed.

### **Risk 4: Breaking Existing Saves**
**Problem:** None. The dashboard is a **presentation layer only**. All game logic stays in `engine/`.  
**Solution:** No changes to `WorldState` or save format.

---

## Success Criteria

### **Minimum Viable Dashboard (Phase 1)**
- [ ] Header displays turn, phase, time
- [ ] Sidebar displays live metrics (Risk, Stability, Cohesion)
- [ ] Main area displays last 10 dialogue exchanges
- [ ] Footer displays available commands
- [ ] User can type commands and see responses
- [ ] Existing game logic (saves, adjudication) unaffected

### **Full Implementation (Phase 2)**
- [ ] Dashboard works in all interactive phases (Discussion, Decision)
- [ ] Narrative scrolling (Intro, Briefing) unchanged
- [ ] SPACE-to-skip functionality preserved
- [ ] Windows/PowerShell compatibility verified

### **Polish (Phase 3)**
- [ ] Live spinner during LLM calls
- [ ] Smooth metric updates (fade transitions)
- [ ] Hotkey support (F1 = Help)
- [ ] Optional Textual migration for advanced features

---

## Implementation Schedule

### **Week 1: Foundation**
- Day 1-2: Build `WargameDashboard` class
- Day 3-4: Test in isolated script (no game integration)
- Day 5: Integrate into discussion phase (behind feature flag)

### **Week 2: Expansion**
- Day 1-3: Extend to Decision/Adjudication phases
- Day 4-5: Testing and bug fixes

### **Week 3: Polish**
- Day 1-2: Add spinners and animations
- Day 3-5: User testing and refinement

---

## Feature Flag Strategy

**Environment Variable:** `WARGAME_DASHBOARD_MODE`
- `"legacy"` (default): Current scrolling mode
- `"dashboard"`: New persistent layout mode

This allows:
1. Safe rollback if bugs are found
2. A/B testing with users
3. Gradual migration (discussion phase first, then all phases)

---

## Next Steps

**Immediate Action:** Create `cli/dashboard.py` with the basic `WargameDashboard` class (Phase 1.1).

**User Approval Required:** Should I proceed with building the dashboard class?

