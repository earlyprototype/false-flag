# Phase 4: Visual Convergence & Polish
**Status:** PENDING (blocked by Phase 3)  
**Goal:** SCUMM aesthetic fully realised, CLI Dashboard complete  
**Estimated Duration:** 3-4 weeks  

---

## Overview

Final phase brings visual and architectural refinement:
- **Web UI:** Refactor into clean component architecture with SCUMM styling
- **CLI Dashboard:** Implement Rich.Layout persistent dashboard
- **Cross-platform:** Semantic alignment (same metrics, same advisors, same themes)
- **Polish:** Animations, keyboard shortcuts, accessibility, performance

---

## Exit Criteria

- [ ] Web UI refactored into modular components (not monolithic page.tsx)
- [ ] All Web components use SCUMM panel/button classes consistently
- [ ] CLI Dashboard (`main_dashboard.py`) functional with Rich.Layout
- [ ] Theme semantics aligned between CLI and Web (same color meanings)
- [ ] Keyboard shortcuts work across all panels
- [ ] Mobile responsive layout (bonus goal)
- [ ] Accessibility audit passed
- [ ] Performance optimised (sub-100ms interactions)

---

## Task Breakdown

### 1. Web UI Refactoring

#### 1.1 Extract SceneViewport Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/game/SceneViewport.tsx` (create)
- `frontend/app/page.tsx` (refactor)

**Current:** All narrative display logic in page.tsx

**Target:** Clean component interface
```typescript
<SceneViewport>
  {messages.map(msg => (
    <Message key={msg.id} {...msg} />
  ))}
</SceneViewport>
```

**Tasks:**
- [ ] Extract viewport container with scrolling logic
- [ ] Apply SCUMM panel styling
- [ ] Handle auto-scroll to bottom on new messages
- [ ] Add scroll-lock toggle (for reading history)
- [ ] Move to `components/game/SceneViewport.tsx`

---

#### 1.2 Extract CommandBar Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/game/CommandBar.tsx` (create)
- `frontend/app/page.tsx` (refactor)

**Current:** Command buttons inline in page.tsx

**Target:**
```typescript
<CommandBar phase={currentPhase}>
  <CommandButton 
    icon="📋" 
    onClick={openStatus}
    shortcut="Ctrl+S"
  >
    STATUS
  </CommandButton>
  {/* ... more buttons */}
</CommandBar>
```

**Tasks:**
- [ ] Extract command grid layout
- [ ] Create CommandButton subcomponent with SCUMM styling
- [ ] Implement keyboard shortcut system
- [ ] Disable buttons based on phase (e.g. EXECUTE only in DECISION)
- [ ] Add hover tooltips showing shortcuts
- [ ] Move to `components/game/CommandBar.tsx`

---

#### 1.3 Extract StatusBar Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/game/StatusBar.tsx` (create)
- `frontend/components/metrics/MetricIndicator.tsx` (create)
- `frontend/app/page.tsx` (refactor)

**Target:**
```typescript
<StatusBar 
  turn={turn} 
  phase={phase} 
  metrics={metrics}
/>
```

**Tasks:**
- [ ] Extract metrics display logic
- [ ] Create MetricIndicator subcomponent (icon + value + trend arrow)
- [ ] Apply SCUMM panel styling
- [ ] Add color coding (red for high risk, green for high stability)
- [ ] Move to `components/game/StatusBar.tsx`

---

#### 1.4 Extract PhaseHeader Component
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/game/PhaseHeader.tsx` (create)
- `frontend/app/page.tsx` (refactor)

**Target:**
```typescript
<PhaseHeader 
  turn={turn} 
  phase={phase}
  hint="Ask your advisors questions or request analysis"
/>
```

**Tasks:**
- [ ] Extract phase display logic
- [ ] Add phase-specific color coding (defined in WEB_UI_DEPLOYMENT_PACKAGE)
- [ ] Add helpful hints per phase
- [ ] Style with Crimson Text font
- [ ] Move to `components/game/PhaseHeader.tsx`

---

#### 1.5 Refactor page.tsx into Clean Architecture
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/page.tsx` (major refactor)

**Before:** 700+ line monolith  
**After:** Clean composition
```typescript
export default function GamePage() {
  // State management
  const [gameState, setGameState] = useState<GameState>()
  const [activePanel, setActivePanel] = useState<string | null>(null)
  
  return (
    <GameLayout>
      <PhaseHeader turn={turn} phase={phase} />
      
      <SceneViewport>
        {messages.map(msg => <Message {...msg} />)}
      </SceneViewport>
      
      <CommandBar phase={phase}>
        {/* Command buttons */}
      </CommandBar>
      
      <StatusBar turn={turn} phase={phase} metrics={metrics} />
      
      {/* Panels */}
      <StatusPanel isOpen={activePanel === 'status'} ... />
      <DiplomacyPanel isOpen={activePanel === 'diplomacy'} ... />
      {/* etc */}
    </GameLayout>
  )
}
```

**Tasks:**
- [ ] Move state management to `lib/game-state.ts`
- [ ] Extract panel open/close logic into hooks
- [ ] Reduce page.tsx to < 200 lines (just composition)
- [ ] Add code comments for major sections

---

### 2. SCUMM Styling Application

#### 2.1 Apply Consistent Panel Styling
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- All panel components in `components/panels/`

**Current:** Mix of Shadcn default styles and custom classes

**Target:** All panels use `.scumm-panel` class
```typescript
<Dialog>
  <DialogContent className="scumm-panel">
    {/* content */}
  </DialogContent>
</Dialog>
```

**Tasks:**
- [ ] Audit all panel components
- [ ] Apply `scumm-panel` class to panel containers
- [ ] Remove conflicting default styles
- [ ] Test all panels for visual consistency
- [ ] Verify in all 4 themes (DEFCON/Standard/Retro/Slate)

---

#### 2.2 Apply Consistent Button Styling
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `components/game/CommandBar.tsx`
- All panel components with buttons

**Target:** All buttons use `.scumm-button` class
```typescript
<button className="scumm-button">
  EXECUTE
</button>
```

**Tasks:**
- [ ] Audit all button elements
- [ ] Apply `scumm-button` class
- [ ] Add variant support (default/primary/warning from WEB_UI_DEPLOYMENT)
- [ ] Verify hover/active/disabled states work
- [ ] Test keyboard navigation (tab order, focus rings)

---

#### 2.3 Typography Consistency
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `app/globals.css` (verify)
- All component files

**Target Typography (from WEB_UI_DEPLOYMENT):**
- **Headings/Commands:** Crimson Text (serif, 600 weight)
- **Body/Narrative:** Libre Baskerville (serif, 400 weight)
- **Data/Metrics:** IBM Plex Mono (monospace, tabular-nums)

**Tasks:**
- [ ] Verify font imports in layout.tsx
- [ ] Apply `font-crimson` to all h1-h6 and command text
- [ ] Apply `font-libre` to narrative/dialogue text
- [ ] Apply `font-mono` to metrics, data displays
- [ ] Remove any inconsistent font classes

---

### 3. CLI Dashboard Implementation

#### 3.1 Create dashboard.py
**Owner:** CLI Developer  
**Status:** ⏸ PENDING  
**Files:**
- `cli/dashboard.py` (create)

**Architecture (from DASHBOARD_DEPLOYMENT_PACKAGE):**
```python
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel

class GameDashboard:
    def __init__(self, game_manager):
        self.game = game_manager
        self.layout = self._build_layout()
    
    def _build_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=5)
        )
        layout["main"].split_row(
            Layout(name="transcript", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        return layout
    
    def render_header(self):
        # Turn, phase, time
        pass
    
    def render_transcript(self):
        # Scrolling message log
        pass
    
    def render_sidebar(self):
        # Metrics, advisors, flags
        pass
    
    def render_footer(self):
        # Command buttons / input
        pass
```

**Tasks:**
- [ ] Create dashboard.py with GameDashboard class
- [ ] Implement 4-panel layout (header/transcript/sidebar/footer)
- [ ] Render turn/phase in header
- [ ] Render message log in transcript (last 20 messages)
- [ ] Render metrics/advisors in sidebar
- [ ] Render command prompt in footer
- [ ] Use Professional Calm theme colors

---

#### 3.2 Create main_dashboard.py
**Owner:** CLI Developer  
**Status:** ⏸ PENDING  
**Files:**
- `cli/main_dashboard.py` (create)

**Entry Point:**
```python
from cli.dashboard import GameDashboard
from engine.game_manager import GameManager

def main():
    game = GameManager(...)
    dashboard = GameDashboard(game)
    
    with Live(dashboard.layout, refresh_per_second=4):
        # Game loop
        while not game.is_over():
            user_input = get_input()
            process_command(user_input)
            dashboard.update()
```

**Tasks:**
- [ ] Create main_dashboard.py entry point
- [ ] Initialize GameManager
- [ ] Initialize GameDashboard
- [ ] Implement Live refresh loop
- [ ] Handle user input without breaking layout
- [ ] Process commands through GameManager
- [ ] Update dashboard after each action

---

#### 3.3 Integrate with Existing CLI
**Owner:** CLI Developer  
**Status:** ⏸ PENDING  
**Files:**
- `cli/main.py` (add dashboard mode option)

**CLI Launcher:**
```bash
python -m cli.main play              # Classic scrolling CLI
python -m cli.main dashboard         # New Rich layout dashboard
```

**Tasks:**
- [ ] Add `dashboard` command to cli/main.py
- [ ] Import and call main_dashboard.main()
- [ ] Ensure classic `play` mode unaffected
- [ ] Document both modes in CLI help

---

### 4. Semantic Alignment (CLI ↔ Web)

#### 4.1 Metrics Naming Consistency
**Owner:** Both (coordination)  
**Status:** ⏸ PENDING  

**Goal:** Same metric names, same icons, same color semantics

**Checklist:**
- [ ] Audit metric names in CLI vs Web
- [ ] Standardise on canonical names (e.g. "escalation_risk" not "risk_level")
- [ ] Align icon choices (e.g. ▲ for risk, ■ for stability)
- [ ] Align color coding (red=danger, green=good, amber=warning)
- [ ] Document canonical metrics in 03_TECHNICAL_SPECS/

---

#### 4.2 Advisor Role Consistency
**Owner:** Both (coordination)  
**Status:** ⏸ PENDING  

**Goal:** Same advisor roles, same trust scale, same relationship categories

**Checklist:**
- [ ] List all advisor roles (NSA, CDS, FCO, etc.)
- [ ] Ensure both interfaces use same role codes
- [ ] Standardise trust scale (0-100)
- [ ] Standardise relationship categories (professional/supportive/cautious/adversarial)
- [ ] Document in 03_TECHNICAL_SPECS/

---

#### 4.3 Theme Semantic Alignment
**Owner:** Both (coordination)  
**Status:** ⏸ PENDING  

**Goal:** DEFCON theme in Web matches Professional Calm in CLI (semantically)

**Checklist:**
- [ ] Map DEFCON theme colors to CLI Professional Calm palette
- [ ] Ensure "alert orange" means the same thing in both
- [ ] Ensure "critical red" has same usage
- [ ] Document theme mappings in 03_TECHNICAL_SPECS/

---

### 5. Polish & Enhancements

#### 5.1 Keyboard Shortcuts System
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/lib/keyboard-shortcuts.ts` (create)
- `frontend/app/page.tsx` (integrate)

**Target Shortcuts:**
- `Ctrl+S` - Open STATUS panel
- `Ctrl+R` - Open RESOURCES panel
- `Ctrl+D` - Open DIPLOMACY panel
- `Ctrl+A` - Open ADVISE panel
- `Ctrl+I` - Open INTEL panel
- `Ctrl+M` - Open MENU panel
- `Ctrl+T` - Open THEME panel
- `Escape` - Close active panel
- `Enter` - Submit input (context-dependent)

**Tasks:**
- [ ] Create useKeyboardShortcuts hook
- [ ] Register all shortcuts
- [ ] Prevent conflicts with browser shortcuts
- [ ] Show shortcuts in command button tooltips
- [ ] Add keyboard shortcuts help panel (Ctrl+?)

---

#### 5.2 Typewriter Effect Polish
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/components/narrative/TypewriterText.tsx` (enhance)

**Current:** Basic character-by-character reveal

**Enhancements:**
- [ ] Add variable speed (faster for common words, slower for dramatic moments)
- [ ] Add punctuation pauses (longer at . ! ?)
- [ ] Add skip-to-end on click (not just spacebar)
- [ ] Add completion sound effect (optional, subtle)
- [ ] Add "Continue" prompt after completion

---

#### 5.3 Animation Smoothness
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `frontend/app/globals.css` (animations)
- All components using Framer Motion

**Tasks:**
- [ ] Audit all transitions for jank
- [ ] Use CSS transforms (not left/top for movement)
- [ ] Apply will-change hints for animated properties
- [ ] Cap animations at 60fps
- [ ] Add prefers-reduced-motion support
- [ ] Test on low-end devices

---

#### 5.4 Mobile Responsive Layout (Bonus)
**Owner:** Frontend  
**Status:** ⏸ PENDING (stretch goal)  

**Tasks:**
- [ ] Test on mobile viewport (375px width)
- [ ] Stack layout vertically on mobile
- [ ] Make command buttons larger (easier to tap)
- [ ] Make panels full-screen on mobile
- [ ] Adjust font sizes for readability
- [ ] Test on real mobile device

---

#### 5.5 Accessibility Audit
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Tasks:**
- [ ] Run Lighthouse accessibility audit
- [ ] Add ARIA labels to all interactive elements
- [ ] Ensure all buttons have accessible names
- [ ] Test keyboard navigation (tab order)
- [ ] Test screen reader (NVDA/VoiceOver)
- [ ] Ensure color contrast meets WCAG AA (4.5:1)
- [ ] Add focus visible styles
- [ ] Add skip-to-content link

---

#### 5.6 Performance Optimisation
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Tasks:**
- [ ] Run Lighthouse performance audit
- [ ] Lazy load panel components (not needed until opened)
- [ ] Memoize expensive components (React.memo)
- [ ] Debounce rapid state updates
- [ ] Optimise re-renders (React DevTools Profiler)
- [ ] Code-split routes
- [ ] Compress images (if any)
- [ ] Minify production build

---

### 6. Testing & Validation

#### 6.1 Cross-Platform Smoke Test
**Owner:** QA  
**Status:** ⏸ PENDING  

**Test Protocol:**
1. **CLI Classic Test**
   - Run `python -m cli.main play`
   - Complete one full turn
   - Verify all commands work
   
2. **CLI Dashboard Test**
   - Run `python -m cli.main dashboard`
   - Complete one full turn
   - Verify layout renders correctly
   - Verify all commands work
   
3. **Web UI Test**
   - Open Web UI in browser
   - Complete one full turn
   - Verify all panels work
   - Verify all themes work
   
4. **Comparison Test**
   - Use same decisions in all 3 interfaces
   - Compare outcomes (should be identical)
   - Compare metrics (should match)

**Acceptance:** All three interfaces produce same game outcomes.

---

#### 6.2 Visual Consistency Audit
**Owner:** Frontend  
**Status:** ⏸ PENDING  

**Checklist:**
- [ ] All panels use scumm-panel class
- [ ] All buttons use scumm-button class
- [ ] All headings use font-crimson
- [ ] All narrative uses font-libre
- [ ] All metrics use font-mono
- [ ] All colors match theme palette
- [ ] No default Shadcn styles leaking through

---

### 7. Documentation

#### 7.1 Update Component Library Reference
**Owner:** Frontend  
**Status:** ⏸ PENDING  
**Files:**
- `03_TECHNICAL_SPECS/Component_Library.md`

**Tasks:**
- [ ] Document all refactored components
- [ ] Add architecture diagram (component tree)
- [ ] Add usage examples for each component
- [ ] Document SCUMM styling classes

---

#### 7.2 Create CLI Dashboard Guide
**Owner:** CLI Developer  
**Status:** ⏸ PENDING  
**Files:**
- `UX/UI/cli/DASHBOARD_USER_GUIDE.md` (create)

**Tasks:**
- [ ] Document dashboard layout sections
- [ ] Document keyboard shortcuts
- [ ] Add screenshots (if possible in terminal)
- [ ] Document how to switch between classic and dashboard modes

---

## Dependencies

**Blocks:**
- Production release

**Blocked By:**
- Phase 3 complete (all features implemented)

**External Dependencies:**
- Rich library (for CLI Dashboard)
- Framer Motion (for Web animations)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Refactoring breaks existing Web UI | High | Incremental refactor, test after each component extraction |
| CLI Dashboard performance poor on slow terminals | Medium | Profile and optimise, reduce refresh rate if needed |
| SCUMM styling inconsistent across themes | Medium | Test all components in all themes before release |
| Mobile layout too cramped | Low | Make mobile responsive a stretch goal, not blocker |

---

## Success Metrics

- **Web UI codebase** maintainable (page.tsx < 200 lines)
- **SCUMM aesthetic** consistent across all components
- **CLI Dashboard** functional and pleasant to use
- **Semantic alignment** between CLI and Web (same names, same meanings)
- **Accessibility score** 90+ on Lighthouse
- **Performance score** 90+ on Lighthouse

---

## Notes

**Why This Matters:**
Phase 4 is about craftsmanship. Earlier phases built features; this phase makes the game feel cohesive, polished, and professional. It's the difference between a prototype and a product.

**ADHD-Friendly Approach:**
- Split into 3 parallel streams: Web Refactor, CLI Dashboard, Polish
- Web Refactor has clear component extraction checkpoints
- CLI Dashboard is self-contained (won't affect Web work)
- Polish tasks can be cherry-picked based on energy/interest
- Each task has clear "done" criteria

---

**Previous Phase:** [Phase_3_Diplomacy_Meta.md](Phase_3_Diplomacy_Meta.md)  
**Completion:** This is the final phase before production release


