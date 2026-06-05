# FALSE FLAG Web UI - Deployment Package

**Project:** FALSE FLAG: THE WARGAME - Web Interface  
**Target Aesthetic:** Indiana Jones and the Fate of Atlantis (1992) SCUMM Interface  
**Date:** 23 November 2025  
**Status:** Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Visual Aesthetic](#visual-aesthetic)
3. [Technical Stack](#technical-stack)
4. [Complete File Structure](#complete-file-structure)
5. [Tailwind Configuration](#tailwind-configuration)
6. [Component Library](#component-library)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Reference Documentation](#reference-documentation)

---

## Executive Summary

### Project Goal
Create a web-based interface for FALSE FLAG: THE WARGAME that translates the existing CLI experience into a browser-based application while preserving the tactical, serious tone of a political crisis simulation.

### Chosen Aesthetic
**Indiana Jones and the Fate of Atlantis (1992)** - SCUMM Interface

**Why This Works:**
- 256-color VGA palette (smooth gradients, NOT blocky 8-bit pixels)
- Painterly panels with soft depth (professional, not cartoony)
- Proven adventure game UI layout (scene/commands/inventory)
- Adaptable color scheme (warm browns → cold war blues/greys)
- Serious, sophisticated feel appropriate for political thriller

**What This Is NOT:**
- ❌ Chunky 8-bit pixel art (too "game-y")
- ❌ Corporate dashboard (too sterile)
- ❌ Modern flat design (no character)
- ❌ Flashy animations (distracting)

---

## Visual Aesthetic

### Reference Game
**Indiana Jones and the Fate of Atlantis (1992)**
- Search: "Indiana Jones Fate of Atlantis SCUMM interface"
- Study: Verb menu layout, panel styling, color use

### Color Palette Adaptation

#### Original Indy Atlantis (Warm Adventure)
```css
--desert-sand: #D4A76A;
--stone-grey: #8B8B7A;
--leather-brown: #704214;
--parchment: #E8DCC0;
--aged-gold: #B8860B;
```

#### FALSE FLAG Adaptation (Cold War Tactical)
```css
/* DEFCON Theme (Primary) */
--bunker-concrete: #4A5568;
--alert-orange: #FF6B35;
--tactical-navy: #004E89;
--steel-blue: #1A659E;
--document-cream: #E8E5DA;
--classified-red: #DC2626;
--shadow-black: #0F172A;
--phosphor-accent: #22D3AA;

/* Standard Theme (Alternative) */
--primary: #22d3ee;      /* Cyan */
--secondary: #3b82f6;    /* Blue */
--success: #22c55e;      /* Green */
--warning: #eab308;      /* Yellow */
--danger: #ef4444;       /* Red */
--muted: #78716c;        /* Stone */

/* Retro Theme (Monochrome Option) */
--phosphor-green: #00FF00;
--screen-glow: rgba(0, 255, 0, 0.3);
--crt-shadow: rgba(0, 51, 0, 0.1);

/* Slate Theme (High Contrast) */
--slate-white: #F8F9FA;
--slate-grey: #6C757D;
--slate-black: #212529;
```

### Typography Stack

#### Primary (Headings/Commands)
```css
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&display=swap');

h1, h2, h3, .command-text {
  font-family: 'Crimson Text', 'Georgia', serif;
  font-weight: 600;
  letter-spacing: 0.02em;
}
```

#### Secondary (Body/Narrative)
```css
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&display=swap');

body, p, .narrative-text {
  font-family: 'Libre Baskerville', 'Times New Roman', serif;
  line-height: 1.6;
}
```

#### Monospace (Data/Metrics)
```css
.metrics, .data-display, code {
  font-family: 'IBM Plex Mono', 'Courier New', monospace;
  font-variant-numeric: tabular-nums;
}
```

### Visual Style Principles

1. **Painterly Panels**
   - Soft gradients (NOT flat or glossy)
   - Subtle drop shadows for depth
   - 2px border-radius (barely noticeable)
   - Dithered backgrounds for texture

2. **Smooth Transitions**
   - 0.3-0.6s ease curves
   - No jarring animations
   - Typewriter text effect (character-by-character)

3. **Restrained Color**
   - 3-4 colors per screen maximum
   - Color = function, not decoration
   - High contrast for readability

4. **ADHD-Friendly**
   - Chunked information
   - Visual anchors (symbols, icons)
   - Breathing room (generous whitespace)
   - Progress indicators

---

## Technical Stack

### Recommended Framework
```bash
Next.js 14+ (App Router)
React 18+
TypeScript 5+
Tailwind CSS 3.4+
Shadcn UI (component base)
Framer Motion (animations)
```

### Why This Stack?
- **Next.js** - Server-side rendering, API routes, deployment ready
- **Shadcn** - Unstyled components, full customization
- **Tailwind** - Utility-first styling, theme system
- **Framer Motion** - Smooth animations, typewriter effects
- **TypeScript** - Type safety for game state

### Installation Commands
```bash
# Create Next.js project
npx create-next-app@latest false-flag-web --typescript --tailwind --app

cd false-flag-web

# Install Shadcn
npx shadcn-ui@latest init

# Install additional dependencies
npm install framer-motion
npm install @radix-ui/react-icons
npm install class-variance-authority
npm install clsx tailwind-merge

# Install fonts
# (Google Fonts auto-loaded via next/font)
```

---

## Complete File Structure

```
false-flag-web/
├── app/
│   ├── layout.tsx                 # Root layout, font imports
│   ├── page.tsx                   # Home/game page
│   ├── globals.css                # Tailwind + custom CSS
│   └── api/
│       ├── llm/route.ts          # LLM proxy endpoint
│       ├── game-state/route.ts   # Game state management
│       └── save/route.ts         # Save/load functionality
│
├── components/
│   ├── game/
│   │   ├── SceneViewport.tsx     # Main narrative area
│   │   ├── CommandBar.tsx        # SCUMM-style command buttons
│   │   ├── StatusBar.tsx         # Metrics display
│   │   ├── PhaseHeader.tsx       # Turn/phase indicator
│   │   └── ConversationLog.tsx   # Message history
│   │
│   ├── panels/
│   │   ├── StatusPanel.tsx       # /status modal
│   │   ├── AdvisorPanel.tsx      # /advise modal
│   │   ├── ResourcesPanel.tsx    # /resources modal
│   │   ├── DiplomacyPanel.tsx    # /call modal
│   │   ├── MenuPanel.tsx         # /menu modal
│   │   └── ThemePanel.tsx        # /theme modal
│   │
│   ├── narrative/
│   │   ├── TypewriterText.tsx    # Character-by-character reveal
│   │   ├── IntelChannel.tsx      # Briefing/intel/breaking indicator
│   │   ├── MetricChanges.tsx     # Delta display
│   │   └── NarrativeOutcome.tsx  # Adjudication display
│   │
│   ├── input/
│   │   ├── QuestionInput.tsx     # Discussion phase input
│   │   ├── DecisionInput.tsx     # Decision phase input
│   │   └── DiplomaticInput.tsx   # Diplomacy conversation input
│   │
│   ├── metrics/
│   │   ├── MetricsTable.tsx      # Full metrics display
│   │   ├── MetricIndicator.tsx   # Single metric (icon + value)
│   │   ├── ProgressBar.tsx       # ASCII-style progress bar
│   │   └── StatusBadge.tsx       # CRITICAL/ELEVATED/STABLE labels
│   │
│   └── ui/                        # Shadcn base components
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── separator.tsx
│       ├── badge.tsx
│       ├── progress.tsx
│       ├── tabs.tsx
│       └── accordion.tsx
│
├── lib/
│   ├── game-state.ts             # Game state management
│   ├── llm-client.ts             # LLM API integration
│   ├── typewriter.ts             # Typewriter effect logic
│   ├── theme-manager.ts          # Theme switching logic
│   └── utils.ts                  # Helper functions
│
├── types/
│   ├── game.ts                   # Game state TypeScript interfaces
│   ├── metrics.ts                # Metrics types
│   └── narrative.ts              # Narrative types
│
├── config/
│   ├── advisors.ts               # Advisor definitions
│   ├── diplomatic-contacts.ts    # Country/diplomat data
│   └── commands.ts               # Command definitions
│
├── public/
│   ├── fonts/                    # Custom fonts (if needed)
│   └── sounds/                   # UI sound effects (optional)
│
├── tailwind.config.ts            # Tailwind theme configuration
├── components.json               # Shadcn configuration
└── tsconfig.json                 # TypeScript configuration
```

---

## Tailwind Configuration

### Complete `tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss"

const config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // SCUMM Cold War Palette
        scumm: {
          // DEFCON Theme
          defcon: {
            bg: '#0F172A',           // Deep navy/black
            panel: {
              dark: '#1E293B',       // Panel background
              light: '#334155',      // Panel highlight
            },
            orange: '#FF6B35',       // Alert orange
            navy: '#004E89',         // Tactical navy
            steel: '#1A659E',        // Steel blue
            teal: '#22D3AA',         // Accent teal
            cream: '#E8E5DA',        // Document/text
            red: '#DC2626',          // Critical red
            amber: '#FFB627',        // Warning amber
          },
          
          // Standard Theme
          standard: {
            primary: '#22d3ee',      // Cyan
            secondary: '#3b82f6',    // Blue
            success: '#22c55e',      // Green
            warning: '#eab308',      // Yellow
            danger: '#ef4444',       // Red
            muted: '#78716c',        // Stone
          },
          
          // Retro Theme
          retro: {
            green: '#00FF00',
            glow: 'rgba(0, 255, 0, 0.3)',
            shadow: 'rgba(0, 51, 0, 0.1)',
          },
          
          // Slate Theme
          slate: {
            white: '#F8F9FA',
            grey: '#6C757D',
            black: '#212529',
          },
          
          // Common
          border: {
            soft: '#3D2817',
            hard: '#704214',
          },
        },
        
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        'scumm': '2px',  // Subtle, not sharp but not round
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        'scumm': '2px 2px 4px rgba(0,0,0,0.4)',
        'scumm-inset': 'inset 1px 1px 2px rgba(255,255,255,0.1)',
        'scumm-hover': '3px 3px 6px rgba(0,0,0,0.5)',
      },
      fontFamily: {
        crimson: ['"Crimson Text"', 'Georgia', 'serif'],
        libre: ['"Libre Baskerville"', 'Times New Roman', 'serif'],
        mono: ['"IBM Plex Mono"', 'Courier New', 'monospace'],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-in": {
          from: { opacity: "0", transform: "translateY(20px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in": "slide-in 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config

export default config
```

### Global CSS (`app/globals.css`)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 210 40% 3%;
    --foreground: 45 10% 92%;

    --card: 222 47% 11%;
    --card-foreground: 45 10% 92%;

    --popover: 222 47% 11%;
    --popover-foreground: 45 10% 92%;

    --primary: 197 71% 52%;
    --primary-foreground: 210 40% 3%;

    --secondary: 217 91% 60%;
    --secondary-foreground: 45 10% 92%;

    --muted: 215 14% 34%;
    --muted-foreground: 217 10% 64%;

    --accent: 199 81% 55%;
    --accent-foreground: 45 10% 92%;

    --destructive: 0 84% 60%;
    --destructive-foreground: 45 10% 92%;

    --border: 215 14% 34%;
    --input: 215 14% 34%;
    --ring: 197 71% 52%;

    --radius: 0.125rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground font-libre;
  }
  
  h1, h2, h3, h4, h5, h6 {
    @apply font-crimson;
  }
  
  code, pre {
    @apply font-mono;
  }
}

@layer components {
  /* SCUMM Panel Styling */
  .scumm-panel {
    background: linear-gradient(
      135deg,
      theme('colors.scumm.defcon.panel.dark') 0%,
      theme('colors.scumm.defcon.panel.light') 100%
    );
    border: 2px solid theme('colors.scumm.border.soft');
    border-radius: theme('borderRadius.scumm');
    box-shadow: 
      inset 1px 1px 0 rgba(255,255,255,0.1),
      2px 2px 4px rgba(0,0,0,0.4);
  }
  
  /* SCUMM Button Styling */
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
  
  /* Dithered Background Effect */
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
  
  /* Readable Text on Textured Backgrounds */
  .readable-text {
    text-shadow: 
      1px 1px 1px rgba(0,0,0,0.8),
      -1px -1px 1px rgba(255,255,255,0.1);
  }
  
  /* Scanline Overlay (optional CRT effect) */
  .scanlines::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
      0deg,
      rgba(0,0,0,0.1) 0px,
      transparent 1px,
      transparent 2px,
      rgba(0,0,0,0.1) 3px
    );
    pointer-events: none;
    opacity: 0.3;
  }
}

/* Typewriter Cursor */
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.typewriter-cursor {
  display: inline-block;
  width: 8px;
  height: 1em;
  background: currentColor;
  margin-left: 2px;
  animation: blink 1s infinite;
}
```

---

## Component Library

### 1. Layout Components

#### `SceneViewport.tsx`
```typescript
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SceneViewportProps {
  children: ReactNode;
  className?: string;
}

export function SceneViewport({ children, className }: SceneViewportProps) {
  return (
    <div className={cn(
      "scumm-panel",
      "h-[60vh] overflow-y-auto",
      "p-6 space-y-4",
      className
    )}>
      {children}
    </div>
  );
}
```

#### `CommandBar.tsx`
```typescript
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CommandBarProps {
  children: ReactNode;
  className?: string;
}

export function CommandBar({ children, className }: CommandBarProps) {
  return (
    <div className={cn(
      "scumm-panel",
      "h-[20vh] grid grid-cols-4 gap-2 p-4",
      className
    )}>
      {children}
    </div>
  );
}

interface CommandButtonProps {
  onClick?: () => void;
  disabled?: boolean;
  icon?: string;
  variant?: 'default' | 'primary' | 'warning';
  children: ReactNode;
}

export function CommandButton({ 
  onClick, 
  disabled, 
  icon, 
  variant = 'default',
  children 
}: CommandButtonProps) {
  const variantStyles = {
    default: 'text-scumm-defcon-cream',
    primary: 'text-scumm-defcon-orange border-scumm-defcon-orange',
    warning: 'text-scumm-defcon-amber border-scumm-defcon-amber',
  };
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "scumm-button",
        "font-crimson font-semibold uppercase tracking-wide",
        "flex flex-col items-center justify-center",
        "text-sm",
        variantStyles[variant]
      )}
    >
      {icon && <span className="text-2xl mb-1">{icon}</span>}
      <span>{children}</span>
    </button>
  );
}
```

#### `StatusBar.tsx`
```typescript
import { Metrics } from '@/types/game';
import { MetricIndicator } from './metrics/MetricIndicator';

interface StatusBarProps {
  metrics: Metrics;
  turn: number;
  phase: string;
}

export function StatusBar({ metrics, turn, phase }: StatusBarProps) {
  return (
    <div className="scumm-panel h-[20vh] flex items-center justify-between px-6">
      <div className="flex gap-6">
        <MetricIndicator 
          icon="▲" 
          label="Risk" 
          value={metrics.escalation_risk}
          type="risk"
        />
        <MetricIndicator 
          icon="■" 
          label="Stability" 
          value={metrics.domestic_stability}
          type="stability"
        />
        <MetricIndicator 
          icon="&" 
          label="Cohesion" 
          value={metrics.alliance_cohesion}
          type="cohesion"
        />
      </div>
      
      <div className="font-mono text-scumm-defcon-cream">
        <div className="text-sm text-scumm-muted">Turn {turn}</div>
        <div className="font-semibold uppercase">{phase}</div>
      </div>
    </div>
  );
}
```

### 2. Narrative Components

#### `TypewriterText.tsx`
```typescript
'use client';

import { useState, useEffect } from 'react';

interface TypewriterTextProps {
  text: string;
  speed?: number; // ms per character
  onComplete?: () => void;
  allowSkip?: boolean;
}

export function TypewriterText({ 
  text, 
  speed = 30, 
  onComplete,
  allowSkip = true 
}: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isSkipped, setIsSkipped] = useState(false);

  useEffect(() => {
    if (isSkipped) {
      setDisplayedText(text);
      onComplete?.();
      return;
    }

    if (currentIndex < text.length) {
      const char = text[currentIndex];
      
      // Calculate delay based on punctuation
      let delay = speed;
      if (['.', '!', '?'].includes(char)) delay *= 3;
      else if ([',', ';', ':'].includes(char)) delay *= 2;

      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + char);
        setCurrentIndex(prev => prev + 1);
      }, delay);

      return () => clearTimeout(timeout);
    } else {
      onComplete?.();
    }
  }, [currentIndex, text, speed, isSkipped, onComplete]);

  useEffect(() => {
    if (!allowSkip) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !isSkipped) {
        e.preventDefault();
        setIsSkipped(true);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [allowSkip, isSkipped]);

  return (
    <div className="font-libre text-scumm-defcon-cream leading-relaxed">
      {displayedText}
      {currentIndex < text.length && !isSkipped && (
        <span className="typewriter-cursor" />
      )}
      {allowSkip && !isSkipped && (
        <div className="text-xs text-scumm-muted mt-2">
          Press SPACE to skip
        </div>
      )}
    </div>
  );
}
```

#### `PhaseHeader.tsx`
```typescript
import { cn } from '@/lib/utils';

interface PhaseHeaderProps {
  turn: number;
  phase: string;
  hint?: string;
  className?: string;
}

export function PhaseHeader({ turn, phase, hint, className }: PhaseHeaderProps) {
  const phaseColors = {
    BRIEFING: 'text-scumm-defcon-steel',
    DISCUSSION: 'text-scumm-defcon-teal',
    DECISION: 'text-scumm-defcon-orange',
    ADJUDICATION: 'text-scumm-defcon-amber',
  };

  return (
    <div className={cn("border-b-2 border-scumm-border-soft pb-4 mb-4", className)}>
      <h1 className={cn(
        "font-crimson text-3xl font-bold uppercase tracking-wider",
        phaseColors[phase as keyof typeof phaseColors] || 'text-scumm-defcon-cream'
      )}>
        Turn {turn} │ {phase} Phase
      </h1>
      {hint && (
        <p className="text-sm text-scumm-muted mt-2 font-mono">
          {hint}
        </p>
      )}
    </div>
  );
}
```

### 3. TypeScript Types

#### `types/game.ts`
```typescript
export interface Metrics {
  escalation_risk: number;
  domestic_stability: number;
  alliance_cohesion: number;
  casualties_mil: number;
  casualties_civ: number;
}

export type Phase = 'briefing' | 'discussion' | 'decision' | 'adjudication';
export type PlayMode = 'classic' | 'immersive' | 'emergent';
export type Theme = 'standard' | 'defcon' | 'retro' | 'slate';

export interface GameState {
  turn: number;
  phase: Phase;
  metrics: Metrics;
  playMode: PlayMode;
  theme: Theme;
  conversation: Message[];
  activePanel: string | null;
  flags: Record<string, boolean>;
}

export interface Message {
  id: string;
  speaker: string;
  content: string;
  type: 'player' | 'advisor' | 'system' | 'narrator';
  timestamp: number;
}

export interface DiplomaticContact {
  country: string;
  name: string;
  title: string;
  accessLevel: 'leader' | 'diplomat';
  relationshipScore: number;
}
```

---

## Implementation Roadmap

### Phase 1: MVP (Week 1-2)
**Goal:** Playable basic game flow

- [ ] Set up Next.js project with Tailwind
- [ ] Install Shadcn and configure theme
- [ ] Implement three-panel layout (viewport/commands/status)
- [ ] Create PhaseHeader component
- [ ] Create CommandBar with 8 buttons
- [ ] Create StatusBar with metrics
- [ ] Implement TypewriterText component
- [ ] Basic discussion input/output
- [ ] Connect to LLM API (proxy through Next.js API route)

**Deliverable:** Can play through one turn (briefing → discussion → decision → adjudication)

### Phase 2: Core Features (Week 3-4)
**Goal:** All game mechanics functional

- [ ] Implement all modal panels:
  - [ ] Status panel (/status)
  - [ ] Advisor panel (/advise)
  - [ ] Resources panel (/resources)
  - [ ] Menu panel (/menu)
  - [ ] Theme panel (/theme)
- [ ] Diplomatic encounter UI (/call)
- [ ] Decision input with interpretation
- [ ] Adjudication display with metric deltas
- [ ] Metric change animations
- [ ] Save/load functionality
- [ ] Theme switcher (4 themes from CLI)

**Deliverable:** Feature parity with CLI version

### Phase 3: Polish (Week 5-6)
**Goal:** Professional, polished experience

- [ ] Keyboard shortcuts (Ctrl+S, Ctrl+M, etc.)
- [ ] Mobile responsive layout
- [ ] Immersive mode character attitudes
- [ ] Advanced animations (smooth transitions)
- [ ] Accessibility enhancements (ARIA labels, focus management)
- [ ] Sound effects (optional, subtle)
- [ ] Loading states and error handling
- [ ] Performance optimization

**Deliverable:** Production-ready web application

### Phase 4: Deployment (Week 7)
**Goal:** Live, accessible application

- [ ] Optimize build
- [ ] Set up backend API
- [ ] Deploy to Vercel/Netlify
- [ ] Set up analytics (optional)
- [ ] User testing
- [ ] Bug fixes

**Deliverable:** Live URL, user documentation

---

## Reference Documentation

### Research Documents (in `filing/visual-examples/`)
1. **README.md** - Overview and navigation
2. **03_INSPIRATION_REFERENCES.md** - Visual references (DEFCON, WarGames, Indy Atlantis)
3. **04_COMPONENT_MAPPING.md** - CLI → Web component translation
4. **05_SMOOTH_RETRO_OPTIONS.md** - Alternative aesthetic approaches
5. **06_INDY_ATLANTIS_AESTHETIC.md** - Primary aesthetic guide
6. **07_WEB_LAYOUT_DESIGN.md** - Complete game mechanics mapping

### CLI Source Code (Reference)
- `cli/theme.py` - Color palette definitions
- `cli/rich_ui.py` - UI component implementations
- `cli/formatters.py` - Text formatting logic
- `cli/main.py` - Game loop and command handling

### Key Resources
- **Shadcn UI:** https://ui.shadcn.com/
- **Tailwind CSS:** https://tailwindcss.com/
- **Framer Motion:** https://www.framer.com/motion/
- **Next.js:** https://nextjs.org/

### Visual References
- Search: "Indiana Jones Fate of Atlantis SCUMM interface"
- Search: "DEFCON game UI screenshot"
- Search: "LucasArts adventure game interface"

---

## Quick Start Commands

```bash
# 1. Create project
npx create-next-app@latest false-flag-web --typescript --tailwind --app

# 2. Navigate to project
cd false-flag-web

# 3. Install Shadcn
npx shadcn-ui@latest init
# Select: Default style, Zinc color, CSS variables: yes

# 4. Install dependencies
npm install framer-motion @radix-ui/react-icons class-variance-authority clsx tailwind-merge

# 5. Add Shadcn components
npx shadcn-ui@latest add button card dialog separator badge progress tabs accordion

# 6. Copy Tailwind config from this document

# 7. Copy global CSS from this document

# 8. Start building components!
```

---

## Support & Questions

**Primary Contact:** Development team  
**Documentation:** This deployment package + reference docs in `filing/visual-examples/`  
**Source Material:** CLI codebase in `cli/` directory

---

**END OF DEPLOYMENT PACKAGE**


