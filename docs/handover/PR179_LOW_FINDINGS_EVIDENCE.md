# Shared-session recovery follow-up

All four LOW findings from [PR #179](https://github.com/earlyprototype/false-flag/pull/179#issuecomment-5546176205)
are addressed on `fix/179-low-findings`, based on `main` at `0c713a0`.

| Finding | Result | Focused proof |
|---|---|---|
| Broken restored stream repeatedly probes session existence | At most five probes per restore; native SSE reconnection continues | Eight failures with HTTP 200, HTTP 503 or rejected fetch each produce five probes; later stream readiness still succeeds |
| Delayed 404 discards an unsubmitted replacement ID | Detaching clears the old session and URL while retaining different input text | A pending 404 resolves after replacement text is entered; session clears and that text remains |
| Globe failure tests lack browser globals and the URL helper | Both harnesses provide browser URL state; the attach-only slice includes the helper | Each failure case subsequently attaches successfully, reaching the real URL update path |
| Globe location mock stays stale after URL changes | `replaceState` updates a real `URL` object in the harness | Two successful attaches preserve a changed token, added query parameter and changed hash |

The production change is confined to `api/dataflow.html`. Globe behaviour,
engine rules, player presentations, Mystery, DTDL and server contracts are
unchanged.

## Runnable checks

```powershell
python -m pytest tests/test_dashboard_capability.py tests/test_globe_session_url.py -q
git diff --check
```

The focused checks passed on 5 September 2026. Both new dataflow regressions
failed on their respective unfixed behaviours before passing with the changes.
No broad suite was run.

## Browser evidence

Headless Chromium used the real FastAPI server at `127.0.0.1:8017` with
`WARGAME_LLM=mock`. The dashboard created campaign
`2f768ce6-05ef-47a0-bcc0-0a73227728b2`; dataflow and the keyless globe attached
through their normal controls.

- Five-adviser discussion, decision interpretation and commitment advanced
  the campaign to turn two, visible on all three pages.
- Reload restored the same session on all three pages, preserving the unrelated
  `proof` query parameter and `#keep` fragment. The globe restored turn two,
  phase briefing, 18 units, 14 plotted and four unresolved.
- A deliberately closed first SSE response on a further reload made each
  browser stream retry automatically against the real API. This was an
  injected stream interruption, not a physical network outage.
- The later-turn briefing endpoint, discussion, interpretation and commitment
  advanced that same campaign to turn three on every page. No JavaScript page
  errors were captured.

The runnable browser journey, result JSON and three screenshots are retained
in the outer workspace at `.claude/evidence/recovery-179-2026-09-05/`.
The journey accepts an installed `playwright-core` path as its first argument
and requires the local mock API server above.

## Remaining acceptance limits

Dataflow's turn badge is blank immediately after reload and appears on the
next state update. This existing limitation remains: the proof establishes
session restoration and subsequent live delivery, not restoration of every
dataflow display value. Live-event history is not replayed.

The API-backed player remains unselected. This follow-up does not complete the
Shared Campaign & Surfaces stream. Kanbanger acceptance and GitHub merge remain
human decisions; repository auto-merge was verified disabled.
