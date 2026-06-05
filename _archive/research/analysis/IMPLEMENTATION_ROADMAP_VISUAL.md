# Visual Implementation Roadmap: Post-Playtest Fixes
**Date**: 12 November 2025  
**Purpose**: Quick-reference visual timeline

---

## Timeline Overview

```
WEEKS 1-2: CRITICAL FIXES (Phase 1)
├─ Week 1
│  ├─ Days 1-4: Nuclear Command Chain System ⚛️
│  └─ Days 5-8: Incoming Diplomatic Calls System 📞
│
└─ Week 2
   ├─ Days 9-10: Game Over & Victory Conditions 🏁
   ├─ Days 11-12: Inject Generation Safety Net 🛡️
   └─ Days 13-14: Advisor Termination System 👥

WEEK 3: HIGH PRIORITY (Phase 2)
├─ Day 15: Metrics Display Fix 📊
├─ Days 16-17: Context Isolation System 🔒
├─ Day 18: Decision Flow Fix 🔄
├─ Day 19: Score Timing Fix ⏱️
└─ Days 20-21: Testing & Bug Fixes 🧪

WEEK 4: POLISH (Phase 3)
├─ Days 22-23: UI Formatting Fixes 🎨
├─ Days 24-25: Testing & Refinement ✨
└─ Days 26-28: Full Regression Testing 🔍

WEEKS 5-6: ENHANCEMENTS (Phase 4) [OPTIONAL]
├─ Bilateral Relationships 🌍
├─ International Briefing 📰
├─ Enhanced Commands ⌨️
└─ Amend Decision 📝
```

---

## Phase 1 Critical Path

```
Nuclear Command Chain (3-4 days)
───────────────────────────────────────────────────────────────
│ Create engine/nuclear_protocol.py                           │
│ ├─ NuclearOrderType enum                                    │
│ ├─ NuclearAuthority tracker                                 │
│ ├─ detect_nuclear_language()                                │
│ └─ process_nuclear_action()                                 │
│                                                              │
│ Integrate into game loop                                    │
│ ├─ Decision phase detection                                 │
│ ├─ Warning UI                                               │
│ └─ Adjudication consequences                                │
│                                                              │
│ OUTCOME: Nuclear threats have real consequences ✓          │
───────────────────────────────────────────────────────────────

Incoming Calls (3-4 days)
───────────────────────────────────────────────────────────────
│ Create engine/incoming_calls.py                             │
│ ├─ IncomingCall model                                       │
│ ├─ IncomingCallQueue with urgency                           │
│ └─ check_for_triggered_calls()                              │
│                                                              │
│ Integrate into turn flow                                    │
│ ├─ After briefing (urgent calls)                            │
│ ├─ After decision (trigger check)                           │
│ └─ Cannot-defer logic for urgent                            │
│                                                              │
│ OUTCOME: NPCs can initiate contact ✓                       │
───────────────────────────────────────────────────────────────

Game Over Conditions (2-3 days)
───────────────────────────────────────────────────────────────
│ Create engine/game_over.py                                  │
│ ├─ GameOverReason enum                                      │
│ ├─ check_game_over_conditions()                             │
│ └─ Assessment generators                                    │
│                                                              │
│ Defeat conditions                                           │
│ ├─ Alliance < 20%                                           │
│ ├─ Domestic < 15%                                           │
│ ├─ Constitutional crisis                                    │
│ └─ Nuclear strike                                           │
│                                                              │
│ Victory conditions                                          │
│ ├─ Diplomatic resolution                                    │
│ ├─ Russian withdrawal                                       │
│ └─ NATO success                                             │
│                                                              │
│ OUTCOME: Clear stakes, win/loss conditions ✓               │
───────────────────────────────────────────────────────────────

Inject Safety Net (1-2 days)
───────────────────────────────────────────────────────────────
│ Enhance llm/inject_generator.py                             │
│ ├─ Impossible state detection                               │
│ ├─ Safety guidelines in prompt                              │
│ └─ Fallback inject pool                                     │
│                                                              │
│ OUTCOME: Never fails, always continues ✓                   │
───────────────────────────────────────────────────────────────

Advisor Termination (2 days)
───────────────────────────────────────────────────────────────
│ Update models/world.py & agents/conversation.py             │
│ ├─ AdvisorStatus tracking                                   │
│ ├─ Replacement system                                       │
│ └─ Constitutional crisis at 5+ firings                      │
│                                                              │
│ OUTCOME: Consequences for extreme actions ✓                │
───────────────────────────────────────────────────────────────
```

---

## Dependency Map

```
CRITICAL PATH (must be sequential):
───────────────────────────────────────────────────────────────
Game Over System ◄─── Nuclear Protocol ◄─── Advisor Termination
      │                      │
      │                      └─── Incoming Calls
      │
      └─── Inject Safety Net (parallel)


PHASE 2 (can be parallel):
───────────────────────────────────────────────────────────────
Metrics Fix ║ Context Isolation ║ Decision Flow ║ Score Timing
 (1 day)    ║    (2 days)       ║   (1 day)     ║  (0.5 days)
```

---

## Progress Tracker

```
PHASE 1: CRITICAL FIXES
┌──────────────────────────────────────────────────────────┐
│ [    ] Nuclear Command Chain        Days 1-4             │
│ [    ] Incoming Calls               Days 5-8             │
│ [    ] Game Over Conditions         Days 9-10            │
│ [    ] Inject Safety Net            Days 11-12           │
│ [    ] Advisor Termination          Days 13-14           │
└──────────────────────────────────────────────────────────┘
Progress: ░░░░░░░░░░░░░░░░░░░░ 0%

PHASE 2: HIGH PRIORITY
┌──────────────────────────────────────────────────────────┐
│ [    ] Metrics Display Fix          Day 15               │
│ [    ] Context Isolation            Days 16-17           │
│ [    ] Decision Flow Fix            Day 18               │
│ [    ] Score Timing Fix             Day 19               │
│ [    ] Testing                      Days 20-21           │
└──────────────────────────────────────────────────────────┘
Progress: ░░░░░░░░░░░░░░░░░░░░ 0%

PHASE 3: POLISH
┌──────────────────────────────────────────────────────────┐
│ [    ] UI Formatting Fixes          Days 22-23           │
│ [    ] Testing & Refinement         Days 24-25           │
│ [    ] Full Regression Testing      Days 26-28           │
└──────────────────────────────────────────────────────────┘
Progress: ░░░░░░░░░░░░░░░░░░░░ 0%

PHASE 4: ENHANCEMENTS [OPTIONAL]
┌──────────────────────────────────────────────────────────┐
│ [    ] Bilateral Relationships      3-4 days             │
│ [    ] International Briefing       2-3 days             │
│ [    ] Enhanced Commands            1 day                │
│ [    ] Amend Decision               1 day                │
└──────────────────────────────────────────────────────────┘
Progress: ░░░░░░░░░░░░░░░░░░░░ 0%

OVERALL PROGRESS: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0/76 tasks
```

---

## Testing Gates

```
                  ┌─────────────────┐
                  │  START PHASE 1  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Build 5 Systems │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
             ┌────┤  TESTING GATE  ├────┐
             │    └─────────────────┘    │
             │                           │
     ✓ Nuclear scenarios      ✓ 20+ turn playthrough
     ✓ Incoming calls         ✓ Adversarial testing
     ✓ Game over conditions   ✓ Save/load
             │                           │
             └────────────┬──────────────┘
                          │
                   PASS? ─┤─ NO ──► Fix & Retest
                          │
                         YES
                          │
                          ▼
                  ┌─────────────────┐
                  │  START PHASE 2  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Build 4 Fixes  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
             ┌────┤  TESTING GATE  ├────┐
             │    └─────────────────┘    │
             │                           │
     ✓ Metrics display        ✓ Private conversations
     ✓ Decision flow          ✓ Full playthrough
             │                           │
             └────────────┬──────────────┘
                          │
                   PASS? ─┤─ NO ──► Fix & Retest
                          │
                         YES
                          │
                          ▼
                  ┌─────────────────┐
                  │  START PHASE 3  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Polish UI (5)   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
             ┌────┤  FINAL GATE    ├────┐
             │    └─────────────────┘    │
             │                           │
     ✓ Visual audit           ✓ UX review
     ✓ Regression suite       ✓ Release check
             │                           │
             └────────────┬──────────────┘
                          │
                   PASS? ─┤─ NO ──► Fix & Retest
                          │
                         YES
                          │
                          ▼
                  ┌─────────────────┐
                  │  RELEASE READY  │
                  │   (or Phase 4)   │
                  └─────────────────┘
```

---

## Risk Mitigation Strategy

```
HIGH RISK AREAS                     MITIGATION
───────────────────────────────────────────────────────────────
Nuclear system complexity           ► Start with simple detection
                                   ► Add complexity incrementally
                                   ► Test each threshold separately

Incoming calls integration          ► Build queue system first
                                   ► Test without triggers
                                   ► Add triggers one by one

Game over edge cases                ► Test all conditions in isolation
                                   ► Then test combinations
                                   ► Verify save/load with flags

LLM prompt engineering              ► Use Pro model (already active ✓)
                                   ► Add explicit safety guidelines
                                   ► Fallback system always available

Context isolation bugs              ► Private mode optional initially
                                   ► Public mode unchanged (safety)
                                   ► Test isolation thoroughly
```

---

## Success Metrics

```
AFTER PHASE 1 (CRITICAL)
┌──────────────────────────────────────────────────────────┐
│ ✓ Nuclear threats trigger consequences                   │
│ ✓ NPCs initiate contact appropriately                    │
│ ✓ Game ends with clear outcomes                          │
│ ✓ 20+ turn playthrough completes                         │
│ ✓ Advisor termination has impact                         │
└──────────────────────────────────────────────────────────┘
TARGET: Playable game with stakes

AFTER PHASE 2 (HIGH PRIORITY)
┌──────────────────────────────────────────────────────────┐
│ ✓ All Phase 1 criteria                                   │
│ ✓ Metrics display correctly after load                   │
│ ✓ Private advisor conversations work                     │
│ ✓ Decision flow is intuitive                             │
│ ✓ Score causation is clear                               │
└──────────────────────────────────────────────────────────┘
TARGET: Polished core gameplay

AFTER PHASE 3 (POLISH)
┌──────────────────────────────────────────────────────────┐
│ ✓ All Phase 2 criteria                                   │
│ ✓ No formatting issues                                   │
│ ✓ Professional UI throughout                             │
│ ✓ Smooth player experience                               │
│ ✓ No immersion breaks                                    │
└──────────────────────────────────────────────────────────┘
TARGET: Release-ready quality
```

---

## Quick Reference: File Changes

```
NEW FILES (6)
├─ engine/nuclear_protocol.py       [Phase 1, ~200 lines]
├─ engine/incoming_calls.py         [Phase 1, ~150 lines]
├─ engine/game_over.py              [Phase 1, ~250 lines]
└─ Phase 4: 3 optional new files

MAJOR MODIFICATIONS (8)
├─ models/world.py                  [Add 5 new fields]
├─ cli/main.py                      [Turn flow restructure]
├─ agents/conversation.py           [Context isolation]
├─ llm/inject_generator.py          [Safety net]
├─ engine/sim_loop.py               [Integration points]
├─ engine/persistence.py            [Save/load enhancements]
├─ llm/context_builder.py           [Private contexts]
└─ cli/rich_ui.py                   [UI improvements]

MINOR MODIFICATIONS (10+)
└─ Various UI, prompt, and integration files
```

---

**Use This Roadmap**: Print, reference, track progress visually  
**Update Progress**: Mark checkboxes as work completes  
**Share Status**: Visual representation for team updates

**Next Step**: Begin Day 1 of Phase 1 (Nuclear Command Chain)


