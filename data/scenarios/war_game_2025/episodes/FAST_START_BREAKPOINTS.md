# Fast Start Scenario - Dramatic Breakpoints

## Overview

The Fast Start scenario includes strategic `[PAUSE]` markers that trigger "Press SPACE to continue" prompts for dramatic pacing and tension building.

---

## Turn 1: COBRA Briefing + Breaking Development

### Breakpoint 1: After Initial Briefing
**Location:** After NSA's opening briefing, before breaking news  
**Line:** "Prime Minister... we have a breaking development."  
**Purpose:** Build suspense before the submarine revelation

### Breakpoint 2: After Submarine Details
**Location:** After Foreign Secretary reports Russian Ambassador refusal  
**Purpose:** Let the gravity of alliance fracturing sink in before NSA's assessment

---

## Turn 2: Infrastructure Attack + NATO Response

### Breakpoint 1: After Home Secretary's Warning
**Location:** After reports of vigilante groups and social order fraying  
**Purpose:** Emphasise domestic crisis before military escalation discussion

### Breakpoint 2: Before NATO Phone Call
**Location:** After Foreign Secretary's phone rings  
**Purpose:** Build anticipation for the critical US conversation

### Breakpoint 3: After US Call Ends
**Location:** After US NSA's request for proof  
**Purpose:** Allow player to process alliance fracturing before NSA's final assessment

---

## Turn 3: Ballistic Missile Launch

### Breakpoint 1: After Scene Setting
**Location:** After rushing to COBRA, before CDS briefing  
**Purpose:** Let the urgency of the moment register

### Breakpoint 2: After NSA's War Warning
**Location:** After "we are effectively at war" statement  
**Purpose:** Emphasise the gravity before discussing public alert

### Breakpoint 3: Before Trajectory Update
**Location:** Before CDS's final trajectory confirmation  
**Purpose:** Build tension before the 4-minute countdown

---

## Pacing Strategy

**Turn 1:** 2 breakpoints (gradual reveal)  
**Turn 2:** 3 breakpoints (escalating complexity)  
**Turn 3:** 3 breakpoints (maximum tension)

**Total:** 8 strategic pauses across 3 turns

---

## Design Rationale

1. **Dramatic Reveals:** Pauses before major information drops
2. **Emotional Processing:** Time to absorb gravity of situations
3. **Tension Building:** Suspense before critical moments
4. **Decision Framing:** Space to consider implications before prompts
5. **ADHD-Friendly:** Clear scene transitions with natural break points

---

## Technical Implementation

The `[PAUSE]` markers are processed by the CLI's briefing display logic:
- Triggers `wait_for_space()` function
- Displays "Press SPACE to continue..."
- Prevents text scrolling until player is ready
- Maintains immersion and pacing control

---

## Comparison with Standard Scenario

**Standard Campaign:** Fewer breakpoints per turn (1-2), spread over 6 turns  
**Fast Start:** More breakpoints per turn (2-3), compressed into 3 turns

This maintains dramatic pacing while accelerating the timeline.



