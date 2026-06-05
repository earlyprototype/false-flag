# Phase 2.5: Dashboard Fixes
**FALSE FLAG: THE WARGAME - Dashboard Repair Implementation**

**Phase:** 2.5  
**Status:** 🔧 Ready to Start  
**Priority:** CRITICAL  
**Timeline:** 3-5 days  
**Started:** [Not yet]  
**Completed:** [Not yet]

---

## 🎯 Phase Objectives

**Primary Goal:** Fix 4 critical dashboard issues blocking user testing

**Success Criteria:**
- [ ] All commands (`/menu`, `/advise`, `/status`, `/resources`) work and display output
- [ ] Turn briefing pre-populated in COBRA BRIEFING panel
- [ ] DEFCON colour scheme applied (high contrast orange/blue/red)
- [ ] Dashboard doesn't erase command output
- [ ] Can complete full turn using dashboard mode
- [ ] No visual glitches or flickering

---

## 🐛 Critical Issues to Fix

### Issue 1: Commands Don't Display Output
**Severity:** CRITICAL  
**Problem:** `Rich.Live()` refreshes 2x/second, erasing console output  
**Impact:** `/menu`, `/advise`, `/status`, `/resources` execute but output vanishes  
**Fix:** Modal overlay system that pauses Live updates

### Issue 2: Empty COBRA BRIEFING Panel
**Severity:** CRITICAL  
**Problem:** Turn inject/briefing text not pre-populated  
**Impact:** Player enters discussion with no context  
**Fix:** Pre-populate dashboard with briefing before starting Live

### Issue 3: Missing DEFCON Colour Scheme
**Severity:** MAJOR  
**Problem:** Dashboard uses default colours, not high-contrast DEFCON  
**Impact:** Doesn't meet ADHD-friendly design goals  
**Fix:** Force DEFCON theme in dashboard init

### Issue 4: Confusing UX
**Severity:** CRITICAL  
**Problem:** Commands appear to do nothing  
**Impact:** User trust destroyed  
**Fix:** Overlays make commands visible, return to dashboard clear

---

## 📅 Implementation Schedule

### Day 1: Modal Overlay System (Foundation)

**Time Estimate:** 4-6 hours

**Tasks:**

1. **Create Modal System** (2 hours)
   - [ ] Create file: `cli/dashboard_modal.py`
   - [ ] Implement `show_overlay(console, live, title, content, colors)`
   - [ ] Test pause/resume of Live updates
   - [ ] Test screen clearing and restoration

2. **Test Import & Basic Functionality** (1 hour)
   - [ ] Verify imports work: `from cli.dashboard_modal import show_overlay`
   - [ ] Create test overlay with dummy content
   - [ ] Verify Live pauses correctly
   - [ ] Verify console clears/restores

3. **Implement `/menu` Command** (1 hour)
   - [ ] Modify `main_dashboard.py` menu handler
   - [ ] Use `show_overlay()` pattern
   - [ ] Test: type `/menu`, see overlay, press ENTER, return to dashboard
   - [ ] Verify no flickering

4. **Documentation** (30 mins)
   - [ ] Update daily log with progress
   - [ ] Document any issues encountered
   - [ ] Note decisions made (e.g. overlay timing, screen clear behaviour)

**Deliverables:**
- `cli/dashboard_modal.py` (new file)
- `/menu` command working with overlay
- Day 1 log in `03_DAILY_LOGS/`

**Success Check:**
- [ ] `/menu` displays in overlay
- [ ] Dashboard resumes after ENTER
- [ ] No visual glitches

---

### Day 2: Refactor All Commands (Scale Up)

**Time Estimate:** 5-7 hours

**Tasks:**

1. **Implement `/advise` Command** (2 hours)
   - [ ] Modify advisor query loop in `main_dashboard.py`
   - [ ] Collect all 5 advisor responses
   - [ ] Display in overlay panel
   - [ ] Test with various questions
   - [ ] Verify formatting looks good

2. **Implement `/status` Command** (1 hour)
   - [ ] Create status overlay content
   - [ ] Include metrics, vibes, flags
   - [ ] Use `show_overlay()` pattern
   - [ ] Test display

3. **Implement `/resources` Command** (1 hour)
   - [ ] Create resources overlay content
   - [ ] Include forces and stockpiles tables
   - [ ] Use `show_overlay()` pattern
   - [ ] Test display

4. **Polish Overlay System** (1-2 hours)
   - [ ] Ensure consistent styling across all overlays
   - [ ] Add visual indicators (borders, titles)
   - [ ] Test rapid command switching (e.g. `/menu` → `/status` → `/advise`)
   - [ ] Fix any edge cases

5. **Documentation** (30 mins)
   - [ ] Update daily log
   - [ ] Note any patterns or refactoring opportunities
   - [ ] Document command response times

**Deliverables:**
- All 4 commands working with overlays
- Day 2 log

**Success Check:**
- [ ] `/menu` works
- [ ] `/advise` works
- [ ] `/status` works
- [ ] `/resources` works
- [ ] All return cleanly to dashboard

---

### Day 3: Briefing Population & Context

**Time Estimate:** 4-5 hours

**Tasks:**

1. **Pre-populate COBRA BRIEFING** (2 hours)
   - [ ] Modify discussion phase entry in `main_dashboard.py`
   - [ ] Capture briefing lines from `run_turn_briefing()`
   - [ ] Parse speaker and message
   - [ ] Add to dashboard conversation log BEFORE starting Live
   - [ ] Test briefing appears immediately

2. **Add `/briefing` Command** (1 hour)
   - [ ] Implement new command to review full turn inject
   - [ ] Store briefing text in dashboard state
   - [ ] Display in overlay
   - [ ] Test scrolling for long briefings

3. **Improve Conversation Log Display** (1 hour)
   - [ ] Format messages with speaker colours
   - [ ] Add timestamps (optional)
   - [ ] Ensure readability (spacing, line breaks)
   - [ ] Test with 20+ messages

4. **Documentation** (30 mins)
   - [ ] Update daily log
   - [ ] Document briefing format decisions
   - [ ] Note any parsing issues

**Deliverables:**
- Briefing pre-populated in COBRA BRIEFING panel
- `/briefing` command working
- Day 3 log

**Success Check:**
- [ ] Briefing visible when entering discussion
- [ ] `/briefing` shows full inject
- [ ] Conversation log readable

---

### Day 4: DEFCON Colour Application

**Time Estimate:** 3-4 hours

**Tasks:**

1. **Force DEFCON Theme** (1 hour)
   - [ ] Modify `cli/dashboard.py` `__init__`
   - [ ] Add `theme_manager.set_theme("defcon")`
   - [ ] Store `self.COLORS` for all render methods
   - [ ] Test theme loads correctly

2. **Update Header Rendering** (30 mins)
   - [ ] Apply deep orange border (`#FF6B35`)
   - [ ] Use high-contrast text colours
   - [ ] Test visibility

3. **Update Sidebar Rendering** (1 hour)
   - [ ] Apply conditional metric colours:
     - Risk: Red (>70), Amber (>50), Teal (<50)
     - Stability: Red (<30), Amber (<50), Teal (>50)
     - Cohesion: Red (<30), Amber (<50), Teal (>50)
   - [ ] Use DEFCON colour palette
   - [ ] Test metric colour transitions

4. **Update Main Panel Rendering** (30 mins)
   - [ ] Apply colour to speaker names
   - [ ] Use DEFCON colours for borders
   - [ ] Test readability

5. **Update Footer Rendering** (30 mins)
   - [ ] Apply muted colours to commands
   - [ ] Ensure high contrast
   - [ ] Test footer visibility

6. **Visual Testing** (30 mins)
   - [ ] Compare to design guide colour specs
   - [ ] Test on different terminal backgrounds
   - [ ] Verify WCAG contrast ratios
   - [ ] Take screenshots for documentation

7. **Documentation** (30 mins)
   - [ ] Update daily log
   - [ ] Document colour choices
   - [ ] Note any accessibility considerations

**Deliverables:**
- DEFCON colours applied throughout dashboard
- Day 4 log

**Success Check:**
- [ ] Orange borders visible
- [ ] Metrics colour-coded (red/amber/teal)
- [ ] High contrast maintained
- [ ] No eye strain

---

### Day 5: Integration Testing & Polish

**Time Estimate:** 5-6 hours

**Tasks:**

1. **Full Playthrough Test** (2 hours)
   - [ ] Start new game in dashboard mode
   - [ ] Play through complete turn
   - [ ] Use all commands multiple times
   - [ ] Note any bugs or glitches
   - [ ] Document user experience

2. **Bug Fixes** (2 hours)
   - [ ] Fix any issues found in playthrough
   - [ ] Test fixes
   - [ ] Regression test (ensure fixes don't break other features)

3. **Performance Tuning** (1 hour)
   - [ ] Check Live refresh rate (2 Hz optimal?)
   - [ ] Optimize render methods if slow
   - [ ] Test on slower systems if possible

4. **Final Polish** (1 hour)
   - [ ] Ensure consistent spacing
   - [ ] Fix any alignment issues
   - [ ] Verify all text is readable
   - [ ] Check for typos in UI text

5. **Documentation** (1 hour)
   - [ ] Update daily log
   - [ ] Create test results document
   - [ ] Update Phase 2.5 status to Complete
   - [ ] Write Phase 2.5 retrospective

**Deliverables:**
- Fully functional dashboard mode
- Test results document
- Day 5 log
- Phase 2.5 retrospective

**Success Check:**
- [ ] Complete turn playable in dashboard
- [ ] All commands work
- [ ] No critical bugs
- [ ] Ready for user testing

---

## 🧪 Testing Procedures

### Manual Test Checklist

**Dashboard Startup:**
- [ ] Dashboard layout renders correctly
- [ ] Header shows correct turn/phase
- [ ] Sidebar shows metrics
- [ ] COBRA BRIEFING shows turn inject
- [ ] Footer shows commands

**Command Testing:**
- [ ] `/menu` - Displays overlay, returns to dashboard
- [ ] `/advise` - Shows all advisor responses, returns to dashboard
- [ ] `/status` - Shows full metrics, returns to dashboard
- [ ] `/resources` - Shows forces/stockpiles, returns to dashboard
- [ ] `/briefing` - Shows full turn inject, returns to dashboard
- [ ] Questions - Appear in conversation log with responses

**Visual Testing:**
- [ ] DEFCON colours applied (orange borders)
- [ ] Metrics colour-coded (red/amber/teal)
- [ ] No flickering
- [ ] No text cutoff
- [ ] Readable on dark background

**Full Turn:**
- [ ] Can complete briefing → discussion → decision → adjudication
- [ ] Dashboard survives phase transitions
- [ ] No crashes or hangs

---

## 📊 Progress Tracking

| Task Category | Total Tasks | Completed | Progress |
|--------------|-------------|-----------|----------|
| Day 1: Modal System | 10 | 0 | ░░░░░░░░░░ 0% |
| Day 2: Commands | 15 | 0 | ░░░░░░░░░░ 0% |
| Day 3: Briefing | 12 | 0 | ░░░░░░░░░░ 0% |
| Day 4: Colours | 14 | 0 | ░░░░░░░░░░ 0% |
| Day 5: Testing | 13 | 0 | ░░░░░░░░░░ 0% |
| **TOTAL** | **64** | **0** | **░░░░░░░░░░ 0%** |

---

## 🚨 Known Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Overlay pattern feels clunky | Medium | High | Get user feedback early, consider alternatives |
| Live() still erases content | Low | Critical | Thorough testing of pause/resume pattern |
| DEFCON colours too intense | Medium | Low | Keep theme switcher, gather feedback |
| Timeline exceeds 5 days | Medium | Medium | Focus on must-haves first, defer nice-to-haves |
| Breaks original CLI | Low | Critical | Never modify `cli/main.py` |

---

## 🔗 Reference Documents

**Technical Deep-Dive:**
- `../01_REFERENCE/DASHBOARD_FIX_PLAN.md` - Root cause analysis, detailed fixes

**Design System:**
- `../01_REFERENCE/MODERN_CLI_DESIGN_GUIDE.md` - DEFCON colours, layout patterns

**Overall Context:**
- `../01_REFERENCE/CLI_DEVELOPMENT_PACKAGE.md` - Full system architecture

**Master Plan:**
- `../00_CLI_MASTER_PLAN.md` - Overall development status

---

## 📝 Daily Log Format

Create logs in: `../03_DAILY_LOGS/YYYY-MM-DD_Phase_2.5_Day_N.md`

Use template from master plan.

---

## ✅ Definition of Done

Phase 2.5 is complete when:
- [ ] All 64 tasks checked off
- [ ] All success criteria met
- [ ] Full turn playable in dashboard mode
- [ ] Test checklist 100% passed
- [ ] Daily logs written for all 5 days
- [ ] Retrospective document created
- [ ] Original CLI still works (regression test)
- [ ] Ready to merge/deploy

---

**Last Updated:** 2025-11-23  
**Next Review:** Daily during implementation  
**Owner:** Development Team

