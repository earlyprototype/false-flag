# CLI Development Master Plan
**FALSE FLAG: THE WARGAME - CLI System Development Tracker**

**Version:** 1.0  
**Created:** 2025-11-23  
**Status:** Active Development

---

## 📊 Development Status Overview

| Phase | Status | Progress | Priority | ETA |
|-------|--------|----------|----------|-----|
| Phase 0: Foundation | ✓ Complete | 100% | - | Done |
| Phase 1: Rich Upgrade | ✓ Complete | 100% | - | Done |
| Phase 2: Dashboard Deploy | ✓ Complete | 100% | - | Done |
| **Phase 2.5: Dashboard Fixes** | 🔧 In Progress | 0% | **CRITICAL** | **5 days** |
| Phase 3: Enhancements | 📅 Planned | 0% | Medium | TBD |

---

## 🎯 Current Focus: Phase 2.5 Dashboard Fixes

**Goal:** Make dashboard mode usable by fixing 4 critical issues

**Timeline:** 3-5 days  
**Started:** [Not yet started]  
**Target Completion:** [TBD]

### Critical Issues
- [ ] Commands don't display output (Live() erases console)
- [ ] COBRA BRIEFING panel starts empty
- [ ] DEFCON colours not applied
- [ ] Confusing UX (commands appear to fail)

**See:** `02_PHASE_PLANS/Phase_2.5_Dashboard_Fixes.md` for detailed plan

---

## 📁 Documentation Structure

```
UX/UI/cli/
│
├── 00_CLI_MASTER_PLAN.md                    ← YOU ARE HERE (Overview & Status)
│
├── 01_REFERENCE/
│   ├── CLI_DEVELOPMENT_PACKAGE.md           (Master technical reference)
│   ├── MODERN_CLI_DESIGN_GUIDE.md           (Design system)
│   └── DASHBOARD_FIX_PLAN.md                (Technical deep-dive)
│
├── 02_PHASE_PLANS/
│   ├── Phase_0_Foundation.md                (Complete)
│   ├── Phase_1_Rich_Upgrade.md              (Complete)
│   ├── Phase_2_Dashboard_Deploy.md          (Complete)
│   ├── Phase_2.5_Dashboard_Fixes.md         (ACTIVE - detailed tasks)
│   └── Phase_3_Enhancements.md              (Future)
│
├── 03_DAILY_LOGS/
│   ├── 2025-11-23_Phase_2.5_Day_1.md        (Daily progress reports)
│   ├── 2025-11-24_Phase_2.5_Day_2.md
│   └── ...
│
├── 04_TESTING/
│   ├── Test_Checklist_Dashboard.md          (Manual testing procedures)
│   ├── Test_Results_Phase_2.5.md            (Test outcomes)
│   └── Bug_Reports.md                       (Issue tracking)
│
├── 05_COMPLETED/
│   ├── Phase_0_Retrospective.md             (Lessons learned)
│   ├── Phase_1_Retrospective.md
│   └── Phase_2_Retrospective.md
│
└── README.txt                               (Quick start guide)
```

---

## 🔄 Development Workflow

### Daily Process

**Morning (Start of Work):**
1. Read previous day's log in `03_DAILY_LOGS/`
2. Review current phase plan in `02_PHASE_PLANS/`
3. Set 2-3 concrete goals for today
4. Update status in master plan (this file)

**During Work:**
5. Make changes to code files
6. Document decisions/blockers in daily log
7. Check off completed tasks in phase plan

**Evening (End of Work):**
8. Update daily log with progress
9. Update phase plan with completed tasks
10. Update master plan status percentages
11. Note any blockers or changes needed

---

## 📈 Progress Tracking

### Phase 2.5: Dashboard Fixes

**Week 1: Critical Fixes**

| Day | Focus Area | Tasks | Status |
|-----|------------|-------|--------|
| **Day 1** | Modal Overlay Setup | Create `dashboard_modal.py`, implement `show_overlay()` | ⏳ Not Started |
| **Day 2** | Command Refactoring | Refactor `/menu`, `/advise`, `/status`, `/resources` | ⏳ Not Started |
| **Day 3** | Briefing Population | Pre-populate COBRA BRIEFING, add `/briefing` command | ⏳ Not Started |
| **Day 4** | DEFCON Colours | Force theme, update all panels | ⏳ Not Started |
| **Day 5** | Integration Testing | Full playthrough, bug fixing | ⏳ Not Started |

**Status Key:**
- ⏳ Not Started
- 🔧 In Progress
- ✓ Complete
- ⚠️ Blocked
- ✗ Abandoned

---

## 📝 Reporting Templates

### Daily Log Template
**Location:** `03_DAILY_LOGS/YYYY-MM-DD_Phase_X_Day_N.md`

```markdown
# Phase X.X - Day N Progress Report
**Date:** YYYY-MM-DD  
**Focus:** [Main objective for the day]

## Goals
- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## Completed
- [x] Task completed
- [x] Another task

## In Progress
- [ ] Partially done task (60% complete)

## Blockers
- Issue encountered (e.g. "Rich.Live() behaviour unclear")

## Decisions Made
- Decision 1: [Why]
- Decision 2: [Why]

## Tomorrow's Focus
- Priority 1
- Priority 2

## Time Spent
- Code: X hours
- Testing: X hours
- Documentation: X hours
**Total:** X hours
```

---

### Phase Completion Report Template
**Location:** `05_COMPLETED/Phase_X_Retrospective.md`

```markdown
# Phase X Retrospective
**Completed:** YYYY-MM-DD  
**Duration:** X days  
**Status:** ✓ Success / ⚠️ Partial / ✗ Failed

## Objectives
- [x] Objective 1
- [x] Objective 2

## What Went Well
- Thing 1
- Thing 2

## What Didn't Go Well
- Problem 1
- Problem 2

## Lessons Learned
- Lesson 1
- Lesson 2

## Recommendations for Future Phases
- Recommendation 1
- Recommendation 2

## Metrics
- Code changes: X files modified
- Testing: X tests run, X passed
- Bugs found: X critical, X major, X minor
```

---

## 🎯 Success Criteria

### Phase 2.5 (Dashboard Fixes)
- [ ] All commands work and display output
- [ ] Turn briefing visible in COBRA BRIEFING panel
- [ ] DEFCON colour scheme applied throughout
- [ ] No flickering or visual glitches
- [ ] Can complete full turn using dashboard
- [ ] ADHD testers report usability improvement

### Overall CLI System
- [ ] Original scrolling CLI remains stable
- [ ] Dashboard mode is production-ready alternative
- [ ] All 4 themes work in both modes
- [ ] Documentation is comprehensive
- [ ] Test coverage >80%

---

## 🚨 Risk Management

### Current Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Modal overlay pattern feels clunky | Medium | User testing, consider hybrid approach |
| Dashboard breaks original CLI | High | Never modify `cli/main.py` directly |
| Timeline slips beyond 5 days | Medium | Focus on Phase 1 fixes first, defer enhancements |
| DEFCON colours too intense | Low | Keep theme switcher, gather feedback |

---

## 🔗 Quick Links

**Reference Docs:**
- [CLI Development Package](01_REFERENCE/CLI_DEVELOPMENT_PACKAGE.md) - Complete system reference
- [Design Guide](01_REFERENCE/MODERN_CLI_DESIGN_GUIDE.md) - Visual system
- [Dashboard Fix Plan](01_REFERENCE/DASHBOARD_FIX_PLAN.md) - Technical deep-dive

**Active Work:**
- [Phase 2.5 Plan](02_PHASE_PLANS/Phase_2.5_Dashboard_Fixes.md) - Current tasks
- [Today's Log](03_DAILY_LOGS/) - Daily progress
- [Test Checklist](04_TESTING/Test_Checklist_Dashboard.md) - Testing procedures

**Code Files:**
- `cli/main.py` - Original CLI (DO NOT MODIFY)
- `cli/main_dashboard.py` - Dashboard variant (MODIFY HERE)
- `cli/dashboard.py` - Dashboard layout class
- `cli/rich_ui.py` - Shared components
- `cli/theme.py` - Theme system

---

## 📞 Next Steps

**Immediate Actions (Today):**
1. Create folder structure: `01_REFERENCE/`, `02_PHASE_PLANS/`, etc.
2. Move existing docs to `01_REFERENCE/`
3. Create Phase 2.5 detailed plan
4. Create daily log template
5. Set start date and begin Day 1

**This Week:**
- Complete Phase 2.5 dashboard fixes
- Document all decisions
- Test thoroughly
- Get user feedback

**Next Week:**
- Phase 2.5 retrospective
- Decide on Phase 3 scope
- Plan enhancements or pivot to web UI

---

**Last Updated:** 2025-11-23  
**Updated By:** Development Team  
**Next Review:** Daily during Phase 2.5

