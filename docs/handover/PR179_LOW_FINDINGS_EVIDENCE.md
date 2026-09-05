# Shared-session recovery follow-up

All four LOW findings from [PR #179](https://github.com/earlyprototype/false-flag/pull/179#issuecomment-5546176205)
are addressed on `fix/179-low-findings`, based on `main` at `0c713a0`.
Separate terminal checks also address the [post-outage session-loss finding](https://github.com/earlyprototype/false-flag/pull/180#discussion_r3938684525).

| Finding | Result | Focused proof |
|---|---|---|
| Broken restored stream repeatedly probes session existence | At most five checks during restoration plus three terminal checks, with one-second delays after network failures or HTTP errors other than 404 | Reconnecting failures stop at five; terminal retries cover HTTP 401, 403, 429 and 503 and stop at three, including when closure arrives during another probe |
| Delayed 404 discards an unsubmitted replacement ID | Detaching clears the old session and URL while retaining different input text | A pending 404 preserves replacement text; surrounding spaces in the input or restored URL do not prevent the old ID clearing |
| Globe failure tests lack browser globals and the URL helper | Both harnesses provide browser URL state; the attach-only slice includes the helper | Each failure case subsequently attaches successfully, reaching the real URL update path |
| Location mocks stay stale after URL changes | History-writing harnesses in the two focused test files update a real `URL` object | Two successful globe attaches preserve a changed token, added query parameter and changed hash |
| Session loss after a successful connection leaves a stale ID | Terminal confirmation also covers previously connected sessions | Restored and manually attached sessions clear on confirmed terminal 404; an older pre-readiness 404 cannot override a later HTTP 200 |
| Failed manual attachment leaves a false session badge | Clear the missing candidate's status while retaining its typed ID and any different saved URL | Failed manual replacement clears the badge, preserves the input for correction and keeps the working campaign URL |

The production change is confined to `api/dataflow.html`. Globe behaviour,
engine rules, player presentations, Mystery, DTDL and server contracts are
unchanged.

## Runnable checks

```powershell
python -m pytest tests/test_dashboard_capability.py tests/test_globe_session_url.py -q
node --check dev-scripts/verify_shared_session_recovery.cjs
git diff --check
```

The focused checks passed on 5 September 2026. The new dataflow regressions
failed on their respective unfixed behaviours before passing with the changes.
An injected teardown exception also verifies that the session check reports
its failure on the page.
No broad local suite was run.

## Browser evidence

Headless Chromium used the real FastAPI server at `127.0.0.1:8017` with
`WARGAME_LLM=mock`. The dashboard created campaign
`03fafccd-a083-4ef7-aa74-cf4835b29551`; dataflow and the keyless globe attached
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
- For a missing session, five finite SSE responses and five aborted existence
  probes modelled an initial outage. The subsequent real API 404 closed the
  stream. Terminal checks received HTTP 503, then a network failure, then a
  real API 404: eight probes in total. The confirmed loss cleared the session ID
  and URL while preserving the unrelated query parameter and fragment.
- A second fault-injection case delivered `stream_ready` before the repeated
  interruptions. The same terminal sequence used three existence probes and
  cleared that previously connected session too.
- A manual replacement through Attach used the same three terminal checks.
  Its confirmed 404 cleared the session badge, retained the typed ID and kept
  the previous working campaign URL.

The [browser verification script](../../dev-scripts/verify_shared_session_recovery.cjs)
checks that the local API and every runtime routing override use the mock
provider before creating a campaign. With the project's Python dependencies,
Node.js, Playwright and its Chromium browser installed, start the server from
the repository root:

```powershell
$env:WARGAME_LLM = "mock"
python -m uvicorn api.server:app --host 127.0.0.1 --port 8017 --no-access-log
```

In another terminal at the repository root, run:

```powershell
node dev-scripts/verify_shared_session_recovery.cjs
```

The first optional argument is an installed `playwright` or `playwright-core`
module path when it is not locally resolvable. The second overrides the output
directory. By default, the result JSON and three screenshots go to the ignored
`dev-scripts/play-verify/shared-session-recovery/` directory. The script creates
a campaign in the local server and requires internet access for the globe's
map assets. The original capture is also retained in the outer workspace at
`.claude/evidence/recovery-179-2026-09-05/`.

## Remaining acceptance limits

After three inconclusive terminal results, automatic probing stops and the URL
is retained. Attach starts a fresh attempt.
Only a confirmed 404 permits automatic removal.

Dataflow's turn badge is blank immediately after reload and appears on the
next state update. This existing limitation remains: the proof establishes
session restoration and subsequent live delivery, not restoration of every
dataflow display value. Live-event history is not replayed.

The API-backed player remains unselected. This follow-up does not complete the
Shared Campaign & Surfaces stream. Kanbanger acceptance and GitHub merge remain
human decisions; repository auto-merge was verified disabled.
