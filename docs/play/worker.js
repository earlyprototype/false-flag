/*
 * FALSE FLAG — browser engine worker
 * ==================================
 *
 * Boots Pyodide, unpacks the real game into a virtual filesystem, and drives
 * `engine.game_manager.GameManager` through the Python bridge in
 * `docs/play/py/bridge.py`. The page never touches Python; it speaks the
 * message protocol below.
 *
 * WHY A WORKER (not the page)
 * --------------------------
 * The LLM path is `requests` -> pyodide-http -> **synchronous XHR**, and the
 * router's resilience wrapper sleeps between retries with `time.sleep`. On the
 * main thread both freeze the tab solid — no spinner, no input, no scrolling.
 * In a worker they block only the worker, and the page stays responsive.
 *
 * Construct it as a CLASSIC worker — `new Worker('./worker.js')`. Pyodide is
 * loaded with `importScripts`, which does not exist in `{type:'module'}`
 * workers.
 *
 * PROTOCOL — page to worker
 * -------------------------
 *   {type:'boot'}
 *   {type:'newGame', config:{scenario?, playMode?, mysteryMode?, seed?}}
 *   {type:'decide',  text}              free-text order for the current turn
 *   {type:'ask',     advisor, text}     question to an adviser
 *   {type:'call',    country, text}     diplomatic call (repeat to continue it)
 *   {type:'endTurn'}
 *   {type:'setKey',  key}               '' or null => offline mock driver
 *   {type:'save'} / {type:'load', data}
 *
 * PROTOCOL — worker to page
 * -------------------------
 *   {type:'booting', pct, note}
 *   {type:'ready'}
 *   {type:'output',  ansi}              RAW ANSI. Rendering it is the page's job.
 *   {type:'state',   turn, metricsVisible, metrics}
 *   {type:'awaiting', kind}             'decision'|'question'|'confirm'|'none'
 *   {type:'ending',  verdict, title, debrief}
 *   {type:'error',   message, fatal}
 *
 * `awaiting` semantics:
 *   'none'      busy, booting, or the campaign is over — block input
 *   'decision'  the turn is open: decide / ask / call are all legal
 *   'question'  a diplomatic call is live; the next `call` continues it
 *               (send text 'end' or 'thank you' to hang up)
 *   'confirm'   the decision resolved; send `endTurn` to advance
 *
 * Extra keys beyond the contract are additive and safe to ignore: `state`
 * also carries phase/playMode/mysteryMode/scenario/variant/seed/finalTurn/
 * vibes/advisors/contacts/over; `ending` also carries endingId/narrative/
 * turns. The reply to `save` is emitted twice, as {type:'save', data} and
 * {type:'saved', data}, because the contract does not name it.
 *
 * API KEYS
 * --------
 * The key lives in this worker's process env and goes nowhere but the
 * Authorization header of the configured endpoint. The worker never persists
 * it — localStorage is the page's business, and the page must warn plainly
 * that a key pasted into a web page is readable by anything that can XSS the
 * page, so it should be spend-limited.
 *
 * PYODIDE HOSTING — jsDelivr CDN by default, vendoring supported
 * -------------------------------------------------------------
 * The runtime is ~16.5 MB (wasm + stdlib + wheels). Two options:
 *
 *   CDN (default). GitHub Pages serves ~160 KB of our own code; jsDelivr
 *   serves the runtime from a pinned, immutable version path. Costs: the
 *   site stops being zero-external-request, and the game's availability now
 *   depends on jsDelivr.
 *
 *   Vendored. `python3 dev-scripts/fetch_pyodide.py` writes docs/play/pyodide/
 *   and this worker prefers it automatically (see probeLocalPyodide). Costs:
 *   ~16.5 MB committed to the repository, forever, in git history.
 *
 * The probe means a vendored deploy needs no code change, and the CDN is only
 * ever contacted when there is no local copy.
 */

const PYODIDE_VERSION = '0.27.7';
// `new Worker('./worker.js?pyodide=<url>')` overrides the remote source — used
// to point at a mirror, and by dev-scripts/verify_play.py to exercise the
// cross-origin path without depending on jsDelivr being reachable.
const PYODIDE_CDN =
  new URLSearchParams(self.location.search).get('pyodide') ||
  `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYODIDE_LOCAL = './pyodide/';
const GAME_ARCHIVE = './game.zip';

// Packages loaded from wherever Pyodide itself came from.
const PACKAGES = ['pydantic', 'pyyaml', 'requests', 'pyodide-http'];

let pyodide = null;
let bridge = null;          // the Python WebGame instance
let booted = false;
let bootPromise = null;
let pendingKey = null;      // setKey arriving before boot finishes

// ---------------------------------------------------------------------------
// messaging
// ---------------------------------------------------------------------------

function send(msg) {
  self.postMessage(msg);
}

function booting(pct, note) {
  // Mirrored to the console so a boot that stalls is diagnosable even when
  // the page cannot render anything yet.
  console.log(`[boot ${pct}%] ${note}`);
  send({ type: 'booting', pct, note });
}

function fail(message, fatal) {
  send({ type: 'error', message: String(message), fatal: !!fatal });
}

// ---------------------------------------------------------------------------
// boot
// ---------------------------------------------------------------------------

async function probeLocalPyodide() {
  // A vendored copy wins over the CDN, so a self-hosted deploy makes zero
  // external requests without any code change.
  if (new URLSearchParams(self.location.search).get('pyodide')) return PYODIDE_CDN;
  try {
    const r = await fetch(PYODIDE_LOCAL + 'pyodide-lock.json', { method: 'GET' });
    if (r.ok) {
      const text = await r.text();
      JSON.parse(text);              // a 404 page dressed as 200 is not a lock file
      return PYODIDE_LOCAL;
    }
  } catch (e) { /* fall through to the CDN */ }
  return PYODIDE_CDN;
}

async function boot() {
  if (booted) { send({ type: 'ready' }); return; }
  if (bootPromise) return bootPromise;
  bootPromise = (async () => {
    booting(2, 'locating runtime');
    const indexURL = await probeLocalPyodide();
    const local = indexURL === PYODIDE_LOCAL;
    booting(5, local ? 'loading runtime (self-hosted)' : 'loading runtime (jsDelivr)');

    importScripts(indexURL + 'pyodide.js');
    pyodide = await loadPyodide({
      indexURL,
      // Python stdout/stderr are diagnostics, not game text. Game text only
      // ever reaches the page through emit() below.
      stdout: (s) => console.log('[py]', s),
      stderr: (s) => console.warn('[py]', s),
    });
    booting(38, 'runtime up — loading packages');

    await pyodide.loadPackage(PACKAGES);
    booting(58, 'packages loaded — unpacking game');

    // A missing game.zip on GitHub Pages answers 404 with an HTML body, which
    // unpackArchive then reports as an opaque "boot failed". Say what went
    // wrong instead.
    const zipResponse = await fetch(GAME_ARCHIVE);
    if (!zipResponse.ok) {
      throw new Error(
        `could not fetch ${GAME_ARCHIVE}: HTTP ${zipResponse.status} ` +
        `${zipResponse.statusText || ''} — the game bundle is missing from ` +
        `this deploy (build it with dev-scripts/build_play_bundle.py)`);
    }
    const zip = await zipResponse.arrayBuffer();
    try { pyodide.FS.mkdir('/game'); } catch (e) { /* already there */ }
    pyodide.unpackArchive(zip, 'zip', { extractDir: '/game' });
    booting(74, 'game unpacked — starting engine');

    // Bridge the Python emit() straight onto postMessage. Python runs
    // synchronously inside this worker, so output streams to the page as the
    // turn is computed rather than arriving in one lump at the end.
    pyodide.globals.set('js_emit', (json) => {
      try {
        send(JSON.parse(json));
      } catch (e) {
        fail('worker could not forward an engine message: ' + e, false);
      }
    });

    pyodide.runPython(`
import sys, os, json

sys.path.insert(0, "/game")
os.chdir("/game")

# Saves live in localStorage on the page side; the engine still wants a
# writable root for its own bookkeeping.
os.makedirs("/game/saves", exist_ok=True)

# Default to the deterministic mock driver: no API key must still be a
# playable game.
os.environ["WARGAME_LLM"] = "mock"
os.environ["WARGAME_RICH_UI"] = "false"

# requests -> XHR. The real OpenAICompatDriver is used completely unmodified;
# OpenRouter answers with access-control-allow-origin: *, so no proxy is
# needed. Patch before any driver is constructed.
import pyodide_http
pyodide_http.patch_all()

import bridge as _bridge

_game = _bridge.WebGame(lambda msg: js_emit(json.dumps(msg, default=str)))


def handle_json(raw):
    """Entry point for the worker. Takes JSON so no proxy crosses the border."""
    _game.handle(json.loads(raw))
`);
    bridge = pyodide.globals.get('handle_json');
    booting(96, 'engine ready');

    booted = true;
    if (pendingKey !== null) {
      dispatch({ type: 'setKey', ...pendingKey });
      pendingKey = null;
    }
    booting(100, 'ready');
    send({ type: 'ready' });
  })().catch((e) => {
    bootPromise = null;
    fail('boot failed: ' + (e && e.message ? e.message : e), true);
    e.__reported = true;   // don't let the dispatcher report it a second time
    throw e;
  });
  return bootPromise;
}

// ---------------------------------------------------------------------------
// dispatch
// ---------------------------------------------------------------------------

function dispatch(msg) {
  // JSON in, JSON out: nothing but strings crosses the JS/Python border, so
  // there are no proxy lifetimes to manage and no conversion surprises.
  // The Python side owns error handling and never raises; anything escaping
  // here is a worker-level fault.
  bridge(JSON.stringify(msg));
}

// Serialise everything: Pyodide is single-threaded and a turn can take many
// seconds against a live model. Without a queue, a second click would
// re-enter the interpreter mid-turn.
let chain = Promise.resolve();

self.onmessage = (event) => {
  const msg = event.data || {};
  chain = chain.then(async () => {
    try {
      if (msg.type === 'boot') {
        await boot();
        return;
      }
      if (!booted) {
        if (msg.type === 'setKey') {
          // Remember it; the page usually sends the key before booting.
          pendingKey = { key: msg.key, baseUrl: msg.baseUrl, model: msg.model };
          return;
        }
        await boot();
      }
      dispatch(msg);
    } catch (e) {
      if (!(e && e.__reported)) fail((e && e.stack) || String(e), !booted);
    }
  });
};
