# WebXR first pass

`/vr?game=<session-id>` shows the campaign's Cesium globe and public captions
on the existing world-locked room screen. Desktop rendering, public updates,
same-session reload and the live 2D fallback pass.
Physical Quest entry, readability, performance and sleep recovery remain
unverified. This pass does not complete the XR stream.

## Cesium evidence — 5 September 2026

Implementation commit: `9d7857d7ff8e41200672c52f130940f06a843f50` on
`prototype/webxr-first-pass`. Production changes in this continuation are
confined to `api/vr.html`; the server route is unchanged.

The existing localhost process 64776 remained healthy and held campaign
`12b6bb83-8f1d-4405-a79f-6ab16ca76f44`, ending at **turn 3 / discussion**.
Check its identity, `/health` and public theatre endpoint before reusing it;
a restart loses this in-memory campaign. No new campaign was created for this
continuation. The live URL is
`http://localhost:8001/vr?game=12b6bb83-8f1d-4405-a79f-6ab16ca76f44`.

| Check | Observed result |
|---|---|
| Actual room texture | Chrome showed the Cesium map inside the room mesh, alongside a real Attorney General caption. The campaign loaded 18 forces and 15 stockpile lines; 14 forces plotted and four unresolved/status locations were not plotted. |
| Public update | A separate public discussion produced the question and five adviser responses. A public decision changed the open room from turn 2 / discussion to turn 3 / briefing without reload. Static base plots remained static; this is not movement evidence. |
| Reload and next briefing | Both `screen=board` and `screen=globe` restored the same campaign at turn 3 / briefing. Its next public briefing changed it to turn 3 / discussion and delivered “Major Power Station Explosion”. Earlier captions were absent after reload, as expected. |
| Manual fallback | Unchecking Show Cesium globe displayed current paged resources and retained captions. This choice persisted across reload; rechecking restored Cesium. |
| Browser failure/recovery | A temporary local test changed only the library URL to an unavailable same-origin script. Its real load error displayed “Cesium download failed” and the 2D board. A new public discussion delivered six captions while the map was unavailable. The test URL was immediately reverted and is not committed; reload restored Cesium on the same campaign. |
| Request evidence | A temporary observation wrapper logged actual same-origin `fetch` and `EventSource` calls during attach and a public update, preserving their arguments. All 12 captured requests were GETs to this campaign's public theatre/stream paths; no writes or facilitator paths occurred. The wrapper was removed and is not committed. This is a client trace, not a server access log. |
| Focused checks | `python -m pytest tests/test_vr.py -q`: **1 passed**, two existing dependency warnings. `node tests/test_vr_client.cjs`: **passed**, including full module syntax, captions/visibility, gazetteer parity, source choice, old-frame rejection, retained campaign/captions after renderer failure, and per-snapshot timeout. `git diff --check`: passed. No broad suite ran. |
| Review | General and JavaScript reviewers reported no blocking findings; the final focused Node check passed. The existing Python route was not changed. |
| Device | No present Quest/Oculus/Android/ADB device was reported by Windows. `adb` was absent from PATH and the usual Android SDK platform-tools location. Physical entry, browser version, legibility, performance and sleep recovery remain pending. |

Local artifacts in the ignored `dev-scripts/play-verify/` directory are
`webxr-cesium-captions.png`, `webxr-cesium-board.png`,
`webxr-cesium-unavailable.png` and `webxr-cesium-requests.json`. They are not
published in the PR. `webxr-server.log` is the historical 2D-pass capture; it
did not update during this continuation and is not evidence for this journey.

## Cesium screen source

Pinned Cesium **1.132.0** reuses the shipped globe's keyless OSM imagery,
ellipsoid, coarse gazetteer, theatre view and display-only unit fan. Its ordinary
`CesiumWidget` has the default animation loop disabled. The Three.js callback
renders Cesium first; synchronous `postRender` copies the completed WebGL frame
into an isolated 2D canvas, then the room board. Three.js uploads that board in
the same task. Idle Cesium frames are not copied; `preserveDrawingBuffer` stays
false. A copied frame belongs to one accepted snapshot; new state uses the live
board until its globe frame is ready.

Library loading and initial frame production each have a 15-second timeout.
Tile, WebGL or copy failures visibly latch the live board until reload. The
bounded startup check rejects a blank/dark centre pixel for this fixed OSM
theatre view; it is not general imagery-health detection. Pending tiles refine
the map. Waiting for every pending tile prevented the initial desktop proof
despite usable imagery, so that condition is not used to accept frames.

OSM attribution and its copyright URL are painted into headset-visible content.
The referrer policy sends only the site origin, keeping the campaign query out
of external requests. Co-located map labels overlap at the fixed theatre zoom;
full names and resource fields remain available in the paged board and HTML
view. Map-label legibility still needs physical measurement.

Uncheck **Show Cesium globe** for the live 2D board; `?screen=board` preserves
the choice across reload. Recheck it to restore Cesium. In VR, the left trigger
cycles the globe and resource pages; the right trigger advances captions.
Device cadence measurements identify the active source and reset their window
when that source changes. A 2D measurement is not Cesium performance evidence.

Implementation references checked:
[CesiumWidget render](https://github.com/CesiumGS/cesium/blob/1.132/packages/engine/Source/Widget/CesiumWidget.js),
[Scene postRender](https://github.com/CesiumGS/cesium/blob/1.132/packages/engine/Source/Scene/Scene.js),
[OSM tile policy](https://operations.osmfoundation.org/policies/tiles/),
[Meta USB debugging](https://developers.meta.com/horizon/documentation/web/browser-remote-debugging/)
and [Meta localhost WebXR](https://developers.meta.com/horizon/documentation/web/port-vr-xr/).

## Run

Use this branch's worktree with the existing Python dependencies. Keep the
existing listeners on 8000 and 8765 untouched. After checking 8001 is free:

```powershell
$env:WARGAME_LLM = 'mock'
python -m uvicorn api.server:app --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001/vr?game=<supplied-session-id>`. A verification driver
may create one disposable campaign and play public actions outside this page.
The room itself only reads `GET /game/{id}/theatre` and `GET /stream/{id}`.
The mock provider is deterministic test data, not evidence of live adviser
reasoning. The CDN imports require an internet connection; if 3D loading fails,
the HTML campaign view still works.

For an authorized, USB-connected Quest 3, identify the intended device with
`adb devices`, then run `adb -s <device> reverse tcp:8001 tcp:8001`. In Quest
Browser open `http://localhost:8001/vr?game=<same-session-id>` and click Enter VR.
The wearer handles device permission dialogs and physical interaction.
Developer Mode or account changes on a borrowed headset require its owner's
permission. Keep this unauthenticated API on localhost; a network deployment
needs HTTPS and the project's separate authentication work.

## Reading and recovery

The screen is a 1920 × 1080 canvas on a fixed 4.8 × 2.7 metre plane, centred
3.2 metres ahead. Five labelled seat positions surround the viewer. There is
no locomotion, automatic camera movement, flicker or visual effect.

Screen text size is adjustable before entry and persists in `?text=`. Resources
wrap and page without shrinking. The left controller trigger cycles the globe
and resource pages; the right trigger advances captions. Desktop controls also offer previous
pages, pause and latest caption. Captions advance automatically after at least
10 seconds, allowing 70 ms per character on the visible page. The HTML view
contains all current resource fields and the retained caption text.

The caption buffer keeps at most 20 events of 12,000 characters each. Removal of
older events and shortening of oversized captions are visible. The public
contract supplies no complete transcript-history replay: reload restores current
theatre state and resumes arriving captions. Earlier or missed dialogue may be
unavailable. Initial queued events reach only the first subscriber. Physical
sleep recovery still requires verification.

The page revalidates on `stream_ready`, campaign events, return from background
or VR visibility changes, and every 15 seconds while visible. During an immersive
session, XR visibility governs reading timers and recovery even if the document
itself reports hidden. Requests coalesce
without losing notifications received during a fetch. A theatre ETag is accepted
only after its validated snapshot is rendered. Failed updates visibly mark the
retained snapshot as last known state. Missing/invalid sessions never create a
campaign.

## Pinned entry behaviour

Three.js and its standard `VRButton` are both **0.157.0**. The inspected
[r157 VRButton source](https://raw.githubusercontent.com/mrdoob/three.js/r157/examples/jsm/webxr/VRButton.js)
has no automatic `offerSession` path. Its remembered-permission `button.click()`
is blocked by a capture-phase trusted-click check; entry and re-entry require
the wearer to activate Enter VR. Standard r157 internally requests optional
`local-floor`, `bounded-floor`, `hand-tracking` and `layers`; the room implements
no hand-tracking controls or XRQuadLayer screen. No VRButton fork or native XR
API patch is used.

## Initial 2D-board evidence

| Check | Observed result |
|---|---|
| Base | `0c713a012549e85d6c2e10a3030826bf6ee29d9c`, branch `prototype/webxr-first-pass` |
| Focused route | `python -m pytest tests/test_vr.py -q` — **1 passed**, 2 existing dependency deprecation warnings, 5 September 2026. The test forbids `GameManager` construction and verifies sessions are unchanged. |
| Caption regression check | `node tests/test_vr_client.cjs` — passed. Actual inline-script functions preserve back-navigation when a new caption arrives, stop reading timers for hidden/blurred XR, and allow visible XR even when the document is hidden. This is a logic check, not device evidence. |
| JavaScript syntax | Inline module piped to `node --input-type=module --check` — passed |
| Runtime used | Python 3.12.10; FastAPI 0.135.1; uvicorn 0.49.0; Pydantic 2.13.4; sse-starlette 3.4.4; pytest 9.1.1; httpx 0.28.1. Existing installed runtime, not a fresh pinned-requirements environment. |
| Desktop session, URL, turn/phase/resources | Chrome at `http://localhost:8001/vr?game=12b6bb83-8f1d-4405-a79f-6ab16ca76f44`: turn 1 / discussion, 18 forces and 15 stockpile lines loaded. The WebGL room initialized without a headset. |
| Real public transcript and snapshot change | A public `/game/discussion` action outside the room delivered the question and five adviser responses. A public `/game/decision` action changed the existing tab to turn 2 / briefing without reloading. After reload, the next public briefing changed it to turn 2 / discussion and displayed “Russian Submarine Surfaces Near UK Waters”. The campaign used the deterministic mock provider. |
| Reload/reconnect to same ID | Reload retained `12b6bb83-8f1d-4405-a79f-6ab16ca76f44`, restored turn 2 / briefing and reconnected captions. The next briefing arrived on that same session. Earlier caption history was absent after reload, consistent with the public contract. |
| Reading controls | A long public briefing paged forward to page 2 and back to page 1 while paused. Changing text scale to 1.1 retained the same `game` value in the URL. |
| No campaign writes/facilitator requests | Source review confirms only the two public campaign GET endpoints. The isolated server log contains four intentional verification-driver POSTs (new, discussion, decision, briefing); the remaining campaign requests are public theatre/stream GETs, including successful 200/304 revalidation. No facilitator request occurred. |
| Desktop console | No warnings or errors reported during the final live-briefing check. The server recorded an unrelated browser favicon 404. |
| Screenshots/recordings | Local desktop capture: `dev-scripts/play-verify/webxr-desktop-captions.png`, showing turn 1 and the live CDS caption in the 3D screen. Access log: `dev-scripts/play-verify/webxr-server.log`. These artifacts are ignored local files, not files published in the PR. No Quest recording or photos exist yet. |
| Quest model | Owner confirmed Meta Quest 3; physical connection pending |
| Quest Browser version | Pending actual device inspection |
| User-triggered immersive entry and re-entry | Pending physical Quest recording/photos |
| World-locked screen, five labels, text legibility | Pending wearer observation at intended viewing distance |
| FPS and frame time | Pending device run. The page's Device measurement reports XR animation callback cadence and mean interval over at least 10 seconds of visible VR. Visibility/session changes reset the measurement; long visible frames remain counted. This is neither display refresh rate nor CPU/GPU render time. |
| Sleep recovery | Pending: record sleep duration, same campaign ID, returned turn/phase, resumed new public caption and outcome |
| Review | General code, Python and JavaScript reviews completed; identified caption timer issues were corrected and rechecked. No remaining actionable code blocker was reported. |
| Human review | Leave the PR draft while Quest acceptance is pending. Repository auto-merge is off and `Arm Auto-Merge` is disabled. The draft commit uses `[skip ci]` to honor the no-broad-suite instruction; required GitHub CI remains pending for a later non-skipped commit and human merge decision. General CI and branch protection are unchanged. |

## Repeat the desktop journey

With the isolated mock server running, create and drive the disposable campaign
from a separate PowerShell terminal. None of these writes belongs in `/vr`:

```powershell
$webxrCampaign = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/game/new' -ContentType 'application/json' -Body '{"scenario_id":"war_game_2025","play_mode":"immersive","facilitator":false}'
$webxrId = $webxrCampaign.session_id
"http://localhost:8001/vr?game=$webxrId"
```

Open that URL and verify the campaign ID, turn, phase and public resources. Then:

```powershell
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/game/discussion' -ContentType 'application/json' -Body (@{session_id=$webxrId; question='Give a brief public readiness update.'; advisor='all'} | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/game/decision' -ContentType 'application/json' -Body (@{session_id=$webxrId; action_text='Request NATO Article 4 consultations and reinforce air policing.'} | ConvertTo-Json)
```

Observe arriving captions and turn 2 / briefing without reloading. Reload the
same URL, verify the same ID and turn, then request its actual next briefing:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/game/$webxrId/briefing"
```

Verify turn 2 / discussion and the new public briefing caption. Use Pause,
Next, Previous and text-size controls to check readable paging. The Quest test
must repeat the campaign connection on the physical headset and add the pending
device evidence above.

Cesium is implemented; XRQuadLayer, WebRTC, avatars and game controls remain
outside this pass. The next physical step is to connect the Quest 3 by a
data-capable USB cable and have the wearer handle permission prompts. Keep the
Kanbanger task in DOING and PR #181 draft until device acceptance exists.
Update commits use `[skip ci]`; skipped required CI is pending, not passed.
Human merge requires a later non-skipped commit and passing required checks.
