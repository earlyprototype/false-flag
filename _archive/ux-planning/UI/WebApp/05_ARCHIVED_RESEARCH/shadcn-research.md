# Shadcn Component Research Report
**FALSE FLAG: THE WARGAME - Web UI Research**  
**Date:** 22 November 2025  
**Aesthetic Target:** Professional Calm / Wargame / CLI (ASCII-only, dark mode, tactical, data-dense)

---

## How Shadcn Works (Corrected Understanding)

Shadcn is a **component library**, not a plugin system. You:
1. Install individual components via CLI: `npx shadcn add [component]`
2. Can use third-party registries: `npx shadcn add @registry/component`
3. Components are copied to your project (not npm packages)
4. Full ownership and customization

---

## Phase 1: Official Shadcn Components

### Official Components (For Wargame UI)

**Install:** `npx shadcn add [component-name]`

#### Data Display Components
1. **Table** - For metrics, resources, diplomatic contacts
   - Install: `npx shadcn add table`
   - Use Case: Main data grid (like `cli/rich_ui.py` tables)
   
2. **Chart** - Built with Recharts
   - Install: `npx shadcn add chart`
   - Use Case: Escalation risk timeline, casualty trends
   - Status: ✓ OFFICIAL COMPONENT

3. **Card** - Container for panels
   - Install: `npx shadcn add card`
   - Use Case: Metric cards, advisor panels

#### CLI-Style Components
4. **Command** - Command palette (CMDK)
   - Install: `npx shadcn add command`
   - Use Case: Quick command access (`/status`, `/advise`, etc.)
   - **Aesthetic Match: 10/10** - This IS a CLI component
   - **Priority: HIGHEST**

5. **Separator** - Visual dividers
   - Install: `npx shadcn add separator`
   - Use Case: Section breaks (like your CLI `───` lines)

6. **Badge** - Status indicators
   - Install: `npx shadcn add badge`
   - Use Case: "CRITICAL", "ELEVATED" labels

#### Interactive Components
7. **Dialog** - Modal panels
   - Install: `npx shadcn add dialog`
   - Use Case: Decision confirmations, intel briefings

8. **Tabs** - Multi-view switcher
   - Install: `npx shadcn add tabs`
   - Use Case: Switch between Metrics / Resources / Advisors

---

## Phase 2: Third-Party Component Registries

**All registries verified via:** https://ui.shadcn.com/docs/directory

### Registries Relevant to Wargame Aesthetic

#### 1. @8bitcn (Retro/Terminal)
- **Install:** `npx shadcn add @8bitcn/[component]`
- **Aesthetic:** 8-bit/retro pixelated style
- **Aesthetic Match:** 8/10 (Retro terminal, "WarGames" vibe)
- **Status:** ✓ OFFICIAL REGISTRY
- **Best For:** If you want 1980s terminal aesthetic

#### 2. @animate-ui (Subtle Motion)
- **Install:** `npx shadcn add @animate-ui/[component]`
- **Aesthetic:** Fully animated React components
- **Aesthetic Match:** 6/10 (Useful for typewriter effects, may be too flashy)
- **Status:** ✓ OFFICIAL REGISTRY
- **Use Case:** Typing animations for advisor text, fade transitions

#### 3. @basecn (Clean Foundation)
- **Install:** `npx shadcn add @basecn/[component]`
- **Aesthetic:** Base UI powered components
- **Aesthetic Match:** 7/10 (Clean, functional, customizable)
- **Status:** ✓ OFFICIAL REGISTRY
- **Use Case:** Solid foundation if you want to build custom styling

### Registries NOT Suitable

#### @aceternity (REJECT)
- **Reason:** "Modern landing page" aesthetic - too flashy for tactical interface
- **Aesthetic Match:** 3/10

#### @assistant-ui (IRRELEVANT)
- **Reason:** AI chat primitives - not applicable to wargame interface
- **Aesthetic Match:** N/A

#### @better-upload (IRRELEVANT)
- **Reason:** File upload utility - no UI aesthetic impact
- **Aesthetic Match:** N/A

---

## Phase 3: Themes & Styling

### Dark Matter Theme
- **URL:** https://www.shadcn.io/theme/darkmatter
- **Type:** Tailwind theme configuration
- **Features:**
  - Deep black backgrounds
  - Monospace typography
  - Mission-control aesthetic
- **Aesthetic Match:** 10/10 - PERFECT match for "Professional Calm"
- **Status:** ✓ VERIFIED - Listed on official Shadcn themes
- **Implementation:** Add theme to `tailwind.config.ts`
- **Priority: HIGHEST** - Use this as base theme

### Tweakcn Theme Editor
- **URL:** https://tweakcn.com/
- **Purpose:** Visual theme editor for Shadcn
- **Use Case:** Generate custom theme matching `cli/theme.py` colors
- **Status:** ⚠ UNVERIFIED (third-party tool)

---

## Phase 4: Recommended Component Stack

### Core Components (Official Shadcn)
```bash
npx shadcn add command    # CLI-style command palette
npx shadcn add table      # Data tables for metrics
npx shadcn add chart      # Recharts integration
npx shadcn add card       # Panel containers
npx shadcn add badge      # Status labels
npx shadcn add separator  # Visual dividers
npx shadcn add dialog     # Modal panels
npx shadcn add tabs       # Multi-view switching
```

### Optional: Retro Registry (if you want 80s vibe)
```bash
npx shadcn add @8bitcn/button
npx shadcn add @8bitcn/card
# etc.
```

### Theme Configuration
- Use **Dark Matter** theme as base
- Customize with colors from `/cli/theme.py`:
  - Primary: `#22d3ee` (Cyan-400)
  - Accent: `#3b82f6` (Blue-500)
  - Background: `#0c0a09`
  - Border: `#44403c`

---

## Phase 5: Animation Layer (Framer Motion)

Shadcn components work with Framer Motion out of the box.

### Key Animations for Wargame Feel
- **Typewriter effect** for advisor text (matches `scroll_text()` in CLI)
- **Fade-in** for metrics updates (not jarring)
- **Slide transitions** for phase changes (Discussion → Decision)

**Install:** Already included in most Shadcn components
**Docs:** https://www.framer.com/motion/

---

## Recommended Implementation Plan

### Step 1: Initialize Shadcn with Dark Matter Theme
```bash
npx shadcn-ui@latest init
```
- Select "Dark Matter" theme during setup
- Or manually add theme to `tailwind.config.ts`

### Step 2: Add Core Components
```bash
npx shadcn add command table chart card badge separator dialog tabs
```

### Step 3: Custom Theme Overlay
Create `theme.ts` mapping your CLI colors:
```typescript
// Match cli/theme.py "Professional Calm" palette
export const wargameTheme = {
  primary: "#22d3ee",      // bright_cyan
  accent: "#3b82f6",       // bright_blue
  danger: "#ef4444",       // red
  warning: "#eab308",      // yellow
  success: "#22c55e",      // green
  muted: "#78716c",        // bright_black
  background: "#0c0a09",   // Rich black
  border: "#44403c",       // Stone-700
}
```

### Step 4: Build Custom Components
- **Terminal Output Component:** For narrative/advisor text
- **Metrics Dashboard:** Using `<Table>` + `<Card>` + `<Badge>`
- **Command Bar:** Using `<Command>` component

---

## What This Achieves

✓ **CLI Aesthetic:** Command palette, monospace fonts, dark theme  
✓ **Data-Dense:** Tables, charts, compact cards  
✓ **Professional Calm:** Cyan/blue/slate color scheme  
✓ **ADHD-Friendly:** Same design principles (chunking, visual anchors, scannable)

---

## Next Action Required

**Decision Point:** Do you want to:
1. **Start with Dark Matter theme** + official components (safest path)
2. **Explore @8bitcn registry** for retro aesthetic (more experimental)
3. **Build custom from scratch** on base Shadcn (most control, most work)

I recommend **Option 1** as it's verified, matches your aesthetic, and you can always add retro elements later.

---

## Files Created
- `filing/shadcn-research.md` - This research document

