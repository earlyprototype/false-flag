Phase 1 (Decision Loop) is effectively complete on the backend and frontend code, BUT was not functional for you because of a port mismatch.

**The Fix:**
I have updated `frontend/app/page.tsx` to point to `http://localhost:8011` (where the working backend is actually running), instead of `8007`.

**Verification:**
1.  **Backend:** Smoke tests passed on port 8011 (API is up).
2.  **Frontend:** `page.tsx` now points to 8011.

**To see it work:**
Please refresh your browser. The Web UI should now connect.

**Next Steps:**
I will pause here to let you verify the fix. If it works, I will proceed to Phase 2 (Deep State & Intel).
