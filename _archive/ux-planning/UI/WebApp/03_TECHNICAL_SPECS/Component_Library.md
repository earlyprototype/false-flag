# Component Library Reference
**Purpose:** Component specifications extracted from WEB_UI_DEPLOYMENT_PACKAGE  
**Status:** Reference material - components to be implemented in Phase 4  

---

## Table of Contents

1. [Layout Components](#layout-components)
2. [Narrative Components](#narrative-components)
3. [Panel Components](#panel-components)
4. [Metric Components](#metric-components)
5. [Input Components](#input-components)
6. [SCUMM Styling Classes](#scumm-styling-classes)

---

## Layout Components

### SceneViewport
**Purpose:** Main narrative/transcript display area

**Props:**
```typescript
interface SceneViewportProps {
  children: ReactNode;
  className?: string;
}
```

**Usage:**
```typescript
<SceneViewport>
  {messages.map(msg => <Message key={msg.id} {...msg} />)}
</SceneViewport>
```

**Styling:**
- Height: 60vh
- Overflow: auto (scrollable)
- Padding: 1.5rem
- SCUMM panel background
- Auto-scroll to bottom on new messages

**File:** `frontend/components/game/SceneViewport.tsx`  
**Status:** To be implemented in Phase 4

---

### CommandBar
**Purpose:** SCUMM-style command button grid

**Props:**
```typescript
interface CommandBarProps {
  children: ReactNode;
  className?: string;
  phase?: Phase;
}
```

**Usage:**
```typescript
<CommandBar phase="discussion">
  <CommandButton onClick={openStatus} icon="📋">
    STATUS
  </CommandButton>
  <CommandButton onClick={openAdvise} icon="💬">
    ADVISE
  </CommandButton>
  {/* ... more buttons */}
</CommandBar>
```

**Layout:**
- Height: 20vh
- Grid: 4 columns, equal spacing
- Gap: 0.5rem
- Padding: 1rem

**File:** `frontend/components/game/CommandBar.tsx`  
**Status:** To be implemented in Phase 4

---

### CommandButton
**Purpose:** Individual command button

**Props:**
```typescript
interface CommandButtonProps {
  onClick?: () => void;
  disabled?: boolean;
  icon?: string;
  variant?: 'default' | 'primary' | 'warning';
  shortcut?: string;
  children: ReactNode;
}
```

**Variants:**
- `default` - Cream text on panel background
- `primary` - Orange text/border (for main actions)
- `warning` - Amber text/border (for critical actions)

**Styling Classes:**
- Base: `.scumm-button`
- Font: `font-crimson` (serif, uppercase)
- Hover: Slight lift, enhanced shadow
- Disabled: 40% opacity, greyscale filter

**File:** `frontend/components/game/CommandBar.tsx` (subcomponent)  
**Status:** To be implemented in Phase 4

---

### StatusBar
**Purpose:** Bottom bar showing metrics and phase

**Props:**
```typescript
interface StatusBarProps {
  metrics: Metrics;
  turn: number;
  phase: string;
}
```

**Layout:**
- Height: 10-15vh
- Flexbox: metrics left, turn/phase right
- SCUMM panel styling

**Contains:**
- 3-4 key metrics (Risk, Stability, Cohesion)
- Turn number
- Current phase name

**File:** `frontend/components/game/StatusBar.tsx`  
**Status:** To be implemented in Phase 4

---

### PhaseHeader
**Purpose:** Page header showing current turn and phase

**Props:**
```typescript
interface PhaseHeaderProps {
  turn: number;
  phase: string;
  hint?: string;
  className?: string;
}
```

**Phase Colors:**
```typescript
const phaseColors = {
  BRIEFING: 'text-scumm-defcon-steel',
  DISCUSSION: 'text-scumm-defcon-teal',
  DECISION: 'text-scumm-defcon-orange',
  ADJUDICATION: 'text-scumm-defcon-amber',
}
```

**Styling:**
- Font: Crimson Text, 3xl, bold, uppercase
- Bottom border: 2px solid
- Spacing: pb-4 mb-4

**File:** `frontend/components/game/PhaseHeader.tsx`  
**Status:** Partially implemented (see page.tsx)

---

## Narrative Components

### TypewriterText
**Purpose:** Character-by-character text reveal

**Props:**
```typescript
interface TypewriterTextProps {
  text: string;
  speed?: number;        // ms per character (default: 30)
  onComplete?: () => void;
  allowSkip?: boolean;   // spacebar to skip (default: true)
}
```

**Features:**
- Variable speed based on punctuation
- Period/exclamation: 3x delay
- Comma/semicolon: 2x delay
- Spacebar to skip to end
- Blinking cursor while typing

**Styling:**
- Font: Libre Baskerville (body serif)
- Color: Document cream
- Line height: 1.6 (relaxed)

**File:** `frontend/components/narrative/TypewriterText.tsx`  
**Status:** Reference implementation in WEB_UI_DEPLOYMENT_PACKAGE

---

### IntelChannel
**Purpose:** Indicator for briefing/intel/breaking news

**Props:**
```typescript
interface IntelChannelProps {
  type: 'briefing' | 'intel' | 'breaking';
  title: string;
}
```

**Visual:**
- Small label/badge above narrative text
- Color-coded by type
- Monospace font for "classified" feel

**File:** `frontend/components/narrative/IntelChannel.tsx`  
**Status:** To be designed and implemented

---

### MetricChanges
**Purpose:** Display metric deltas after decisions

**Props:**
```typescript
interface MetricChangesProps {
  changes: Record<string, number>;  // { "escalation_risk": +5, ... }
  animate?: boolean;
}
```

**Visual:**
- Show ↑/↓ arrows
- Color: red for negative, green for positive
- Animate entrance with slide-in

**File:** `frontend/components/narrative/MetricChanges.tsx`  
**Status:** To be implemented

---

### NarrativeOutcome
**Purpose:** Display adjudication results

**Props:**
```typescript
interface NarrativeOutcomeProps {
  outcome: {
    narrative: string;
    effects: string[];
    reactions: { role: string; reaction: string }[];
  };
}
```

**Sections:**
1. Main narrative (typewriter)
2. Effects list (bulleted)
3. Advisor reactions (quoted)
4. International reactions

**File:** `frontend/components/narrative/NarrativeOutcome.tsx`  
**Status:** To be implemented

---

## Panel Components

All panel components use Shadcn Dialog as base and apply SCUMM styling.

### StatusPanel
**Purpose:** Full status overview (metrics, advisors, flags)

**Props:**
```typescript
interface StatusPanelProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}
```

**Tabs:**
1. **Metrics** - Full metrics table
2. **Advisors** - Trust bars and relationships
3. **Flags** - Active crisis flags

**File:** `frontend/components/panels/StatusPanel.tsx`  
**Status:** Partially implemented (needs Phase 2 enhancements)

---

### AdvisorPanel
**Purpose:** View all advisors and their roles

**Props:**
```typescript
interface AdvisorPanelProps {
  isOpen: boolean;
  onClose: () => void;
  advisors: Advisor[];
}
```

**Display:**
- List of advisors with roles
- Brief description of expertise
- Status (active/absent)

**File:** `frontend/components/panels/AdvisorPanel.tsx`  
**Status:** To be implemented

---

### ResourcesPanel
**Purpose:** View forces and stockpiles

**Props:**
```typescript
interface ResourcesPanelProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}
```

**Tabs:**
1. **Forces** - Military units table
2. **Stockpiles** - Munitions/equipment table

**File:** `frontend/components/panels/ResourcesPanel.tsx`  
**Status:** Partially implemented (needs defensive data handling)

---

### DiplomacyPanel
**Purpose:** Diplomatic contact management and calls

**Props:**
```typescript
interface DiplomacyPanelProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}
```

**Modes:**
1. **Contact Selection** - Choose who to call
2. **Call in Progress** - Dialogue display

**File:** `frontend/components/panels/DiplomacyPanel.tsx`  
**Status:** Stub exists (Phase 3 will enhance)

---

### MenuPanel
**Purpose:** Game menu (save, load, settings, help)

**Props:**
```typescript
interface MenuPanelProps {
  isOpen: boolean;
  onClose: () => void;
}
```

**Options:**
- Save Game
- Load Game
- Settings (LLM config)
- Theme Selector
- Keyboard Shortcuts
- About/Help

**File:** `frontend/components/panels/MenuPanel.tsx`  
**Status:** To be implemented (Phase 3)

---

### ThemePanel
**Purpose:** Theme selection

**Props:**
```typescript
interface ThemePanelProps {
  isOpen: boolean;
  onClose: () => void;
  currentTheme: Theme;
  onThemeChange: (theme: Theme) => void;
}
```

**Themes:**
1. DEFCON (default) - Cold war blues/greys
2. Standard - Cyan/blue accents
3. Retro - Phosphor green monochrome
4. Slate - High contrast B&W

**File:** `frontend/components/panels/ThemePanel.tsx`  
**Status:** To be implemented (Phase 3)

---

## Metric Components

### MetricIndicator
**Purpose:** Single metric display with icon

**Props:**
```typescript
interface MetricIndicatorProps {
  icon: string;
  label: string;
  value: number;
  type: 'risk' | 'stability' | 'cohesion' | 'casualties';
  showTrend?: boolean;
}
```

**Color Coding:**
- **Risk:** High = red, Low = green
- **Stability:** High = green, Low = red
- **Cohesion:** High = green, Low = amber
- **Casualties:** Any = red

**File:** `frontend/components/metrics/MetricIndicator.tsx`  
**Status:** To be implemented

---

### ProgressBar
**Purpose:** ASCII-style progress/level bar

**Props:**
```typescript
interface ProgressBarProps {
  value: number;      // 0-100
  max?: number;       // default: 100
  variant?: 'default' | 'danger' | 'success';
  showLabel?: boolean;
}
```

**Visual:**
```
Risk: ████████░░ 65/100
```

**File:** `frontend/components/metrics/ProgressBar.tsx`  
**Status:** To be implemented

---

### StatusBadge
**Purpose:** Status label (CRITICAL/ELEVATED/STABLE)

**Props:**
```typescript
interface StatusBadgeProps {
  status: 'critical' | 'elevated' | 'stable' | 'unknown';
  label?: string;
}
```

**Colors:**
- Critical: Red background
- Elevated: Amber background
- Stable: Green background
- Unknown: Grey background

**File:** `frontend/components/metrics/StatusBadge.tsx`  
**Status:** To be implemented

---

### MetricsTable
**Purpose:** Full metrics display (all metrics)

**Props:**
```typescript
interface MetricsTableProps {
  metrics: Metrics;
  showDescriptions?: boolean;
}
```

**Layout:**
- Table with metric name, value, status
- Optional descriptions column
- Color-coded values

**File:** `frontend/components/metrics/MetricsTable.tsx`  
**Status:** To be implemented

---

## Input Components

### QuestionInput
**Purpose:** Discussion phase question input

**Props:**
```typescript
interface QuestionInputProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Features:**
- Textarea with auto-resize
- Submit on Ctrl+Enter
- Character count (optional)

**File:** `frontend/components/input/QuestionInput.tsx`  
**Status:** Exists in page.tsx (to be extracted)

---

### DecisionInput
**Purpose:** Decision phase action input

**Props:**
```typescript
interface DecisionInputProps {
  onSubmit: (decision: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

**Features:**
- Large textarea
- Submit button: "EXECUTE" (primary variant)
- Warning styling (decision is irreversible)

**File:** `frontend/components/input/DecisionInput.tsx`  
**Status:** Exists in page.tsx (to be extracted)

---

### DiplomaticInput
**Purpose:** Diplomatic conversation input

**Props:**
```typescript
interface DiplomaticInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  options?: string[];  // Pre-defined response options
}
```

**Modes:**
1. Free-form text input
2. Multiple choice (if options provided)

**File:** `frontend/components/input/DiplomaticInput.tsx`  
**Status:** To be implemented (Phase 3)

---

## SCUMM Styling Classes

### Panel Styling
```css
.scumm-panel {
  background: linear-gradient(
    135deg,
    theme('colors.scumm.defcon.panel.dark') 0%,
    theme('colors.scumm.defcon.panel.light') 100%
  );
  border: 2px solid theme('colors.scumm.border.soft');
  border-radius: theme('borderRadius.scumm');  /* 2px */
  box-shadow: 
    inset 1px 1px 0 rgba(255,255,255,0.1),
    2px 2px 4px rgba(0,0,0,0.4);
}
```

### Button Styling
```css
.scumm-button {
  background: linear-gradient(
    180deg,
    theme('colors.scumm.defcon.panel.light') 0%,
    theme('colors.scumm.defcon.panel.dark') 100%
  );
  border: 1px solid theme('colors.scumm.border.hard');
  box-shadow: theme('boxShadow.scumm');
  text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
  transition: all 0.15s ease;
}

.scumm-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: theme('boxShadow.scumm-hover');
}

.scumm-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.scumm-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  filter: grayscale(0.8);
}
```

### Dithered Background
```css
.dithered-bg {
  background-image: 
    linear-gradient(
      135deg,
      theme('colors.scumm.defcon.navy') 0%,
      theme('colors.scumm.defcon.steel') 50%,
      theme('colors.scumm.defcon.navy') 100%
    );
  background-size: 4px 4px;
}
```

### Readable Text on Textured Backgrounds
```css
.readable-text {
  text-shadow: 
    1px 1px 1px rgba(0,0,0,0.8),
    -1px -1px 1px rgba(255,255,255,0.1);
}
```

### Typewriter Cursor
```css
.typewriter-cursor {
  display: inline-block;
  width: 8px;
  height: 1em;
  background: currentColor;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
```

---

## Typography Classes

From `globals.css`:

```css
h1, h2, h3, h4, h5, h6 {
  @apply font-crimson;  /* Crimson Text serif */
}

body, p {
  @apply font-libre;  /* Libre Baskerville serif */
}

code, pre, .metrics {
  @apply font-mono;  /* IBM Plex Mono */
}
```

---

## Implementation Priority

### Phase 0-1 (Current)
- Use existing components in page.tsx
- Apply defensive data handling

### Phase 2
- Implement StatusPanel enhancements (tabs, trust, flags)
- Implement IntelligencePanel (new)

### Phase 3
- Implement enhanced DiplomacyPanel
- Implement MenuPanel
- Implement ThemePanel

### Phase 4 (Refactor)
- Extract SceneViewport
- Extract CommandBar + CommandButton
- Extract StatusBar
- Extract PhaseHeader
- Apply SCUMM styling consistently
- Implement all metric components
- Implement all input components

---

**Source:** WEB_UI_DEPLOYMENT_PACKAGE.md  
**Last Updated:** 23 Nov 2025  
**Next Update:** After Phase 4 implementation


