# CLI Development Documentation
**FALSE FLAG: THE WARGAME - Terminal Interface**

---

## Quick Start

**Current Status:** Phase 2.5 (Dashboard Fixes) - Ready to start  
**See:** `00_CLI_MASTER_PLAN.md` for complete overview

---

## Folder Structure

```
UX/UI/cli/
│
├── 00_CLI_MASTER_PLAN.md              ★ START HERE - Status & roadmap
│
├── 01_REFERENCE/                      Active reference documentation
│   ├── CLI_DEVELOPMENT_PACKAGE.md     (Complete system architecture)
│   ├── MODERN_CLI_DESIGN_GUIDE.md     (Design system & colours)
│   └── DASHBOARD_FIX_PLAN.md          (Technical deep-dive)
│
├── 02_PHASE_PLANS/                    Development phases
│   └── Phase_2.5_Dashboard_Fixes.md   (Current active work)
│
├── 03_DAILY_LOGS/                     Daily progress reports
│   └── TEMPLATE_Daily_Log.md          (Use this template)
│
├── 04_TESTING/                        Testing documentation
│   └── (Create test checklists here)
│
└── 05_COMPLETED/                      Historical archive
    ├── README.md
    ├── Phase_1_Rich_Upgrade_COMPLETE.md
    ├── Phase_2_Dashboard_PLAN.md
    └── Phase_2_Dashboard_STATUS.md
```

---

## What You Need to Know

### CLI System Has Two Modes

1. **Original Scrolling CLI** (`cli/main.py`)
   - Status: ✓ Stable, production-ready
   - Use: Default, safe, works perfectly

2. **Dashboard CLI** (`cli/main_dashboard.py`)
   - Status: ⚠️ Broken, needs Phase 2.5 fixes
   - Use: Experimental, not ready for users

---

## Current Development

**Phase 2.5: Dashboard Fixes**
- **Goal:** Fix 4 critical dashboard issues
- **Timeline:** 3-5 days
- **See:** `02_PHASE_PLANS/Phase_2.5_Dashboard_Fixes.md`

**Critical Issues:**
1. Commands don't display output
2. COBRA BRIEFING panel empty
3. DEFCON colours not applied
4. Confusing UX

---

## How to Use This System

### For Development Work:
1. Read `00_CLI_MASTER_PLAN.md` for status
2. Read current phase plan in `02_PHASE_PLANS/`
3. Create daily log in `03_DAILY_LOGS/` (use template)
4. Make changes to code files
5. Update progress in daily log and phase plan
6. Update master plan percentages

### For Reference:
- **Architecture:** `01_REFERENCE/CLI_DEVELOPMENT_PACKAGE.md`
- **Design System:** `01_REFERENCE/MODERN_CLI_DESIGN_GUIDE.md`
- **Technical Details:** `01_REFERENCE/DASHBOARD_FIX_PLAN.md`

### For Historical Context:
- See `05_COMPLETED/` for past phases

---

## Code Files Location

**CLI Code:**
- `cli/main.py` - Original CLI (DO NOT MODIFY)
- `cli/main_dashboard.py` - Dashboard variant (MODIFY HERE)
- `cli/dashboard.py` - Dashboard layout class
- `cli/rich_ui.py` - Shared UI components
- `cli/theme.py` - Theme system
- `cli/formatters.py` - Text utilities
- `cli/spinner.py` - Loading indicators

**Tests:**
- `tests/test_dashboard.py` - Dashboard unit tests
- `tests/test_cli_modes.py` - Integration tests

---

## Quick Links

- [Master Plan](00_CLI_MASTER_PLAN.md) - Overall status
- [Phase 2.5 Plan](02_PHASE_PLANS/Phase_2.5_Dashboard_Fixes.md) - Current work
- [CLI Package](01_REFERENCE/CLI_DEVELOPMENT_PACKAGE.md) - Technical reference
- [Design Guide](01_REFERENCE/MODERN_CLI_DESIGN_GUIDE.md) - Visual system

---

**Last Updated:** 2025-11-23  
**Maintained By:** Development Team

