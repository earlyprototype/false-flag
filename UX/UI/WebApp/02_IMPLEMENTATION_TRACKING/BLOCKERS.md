# Development Blockers
**Last Updated:** 23 Nov 2025  

---

## Active Blockers

_No active blockers currently_

---

## Blocker Template

When adding a blocker, use this format:

```
### BLOCKER-001: [Short Description]
**Reported:** YYYY-MM-DD  
**Phase:** [Phase number]  
**Severity:** Critical | High | Medium | Low  
**Blocking:** [Task IDs or descriptions]  
**Owner:** [Who is responsible for resolving]  

**Description:**
[Detailed explanation of the blocker]

**Impact:**
[What cannot progress until this is resolved]

**Dependencies:**
- [External dependency 1]
- [External dependency 2]

**Mitigation Options:**
1. [Option 1]
2. [Option 2]

**Resolution Plan:**
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

**Target Resolution:** YYYY-MM-DD  
**Actual Resolution:** YYYY-MM-DD (when resolved)

---
```

---

## Resolved Blockers

### Example (Template Only - Delete This)

~~BLOCKER-000: Example Blocker~~  
**Resolved:** 2025-11-23  
**Resolution:** Implemented workaround, moved dependency to Phase 2

---

## Escalation Process

**If blocker persists for 3+ days:**
1. Reassess severity
2. Consider alternative approaches
3. Escalate to project lead
4. Update sprint timeline if needed

**Blocker Severity Definitions:**
- **Critical:** Blocks entire phase, no workaround possible
- **High:** Blocks multiple tasks, workaround exists but costly
- **Medium:** Blocks single task, workaround available
- **Low:** Slows progress but doesn't block completion

---

## Prevention Notes

**Common Blocker Categories:**
1. **External API Dependencies** - LLM API rate limits, downtime
2. **Data Format Issues** - Unexpected YAML structure, parsing failures
3. **Integration Conflicts** - Frontend/Backend contract mismatches
4. **Environment Setup** - Missing dependencies, config issues
5. **Design Decisions** - Unclear requirements, conflicting specs

**Prevention Strategies:**
- Define clear API contracts upfront (Phase 0 focus)
- Add schema validation early
- Use mocks for external dependencies during dev
- Document all assumptions explicitly
- Regular sync meetings (backend ↔ frontend)

---

**Last Updated:** 23 Nov 2025 16:30 GMT


