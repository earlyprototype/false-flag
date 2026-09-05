"""Browser-behaviour checks for the facilitator capability transport."""

import subprocess
from pathlib import Path


REPO = Path(__file__).parent.parent
DASHBOARD = REPO / "api" / "dashboard.html"
DATAFLOW = REPO / "api" / "dataflow.html"


def _run_node(script, page=DASHBOARD):
    result = subprocess.run(
        ["node", "-e", script, str(page)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_dashboard_sends_capability_on_its_stream_and_control_requests():
    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const apiStart = html.indexOf("async function api(");
const apiEnd = html.indexOf("function setStatus", apiStart);
const streamStart = html.indexOf("function connectStream()");
const streamEnd = html.indexOf('$("btnNew")', streamStart);
assert.notEqual(apiStart, -1, "api helper not found");
assert.notEqual(streamStart, -1, "stream connector not found");

let request = null;
let latestSource = null;
class FakeEventSource {
  constructor(url) { this.url = url; latestSource = this; }
  addEventListener() {}
  close() {}
}
const context = vm.createContext({
  encodeURIComponent,
  EventSource: FakeEventSource,
  fetch: async (path, options) => {
    request = { path, options };
    return { ok: true, text: async () => "{}" };
  },
  addLedgerRow() {}, recordMetrics() {}, renderDtdlLive() {},
  dtdlCounts: { inject_triggered: 0, participant_action: 0 },
});
vm.runInContext(`
  let sessionId = "shared-session";
  let source = null;
  let facilitatorCapability = "secret / +";
`, context);
vm.runInContext(html.slice(apiStart, apiEnd), context);
vm.runInContext(html.slice(streamStart, streamEnd), context);

(async () => {
  await vm.runInContext('api("POST", "/game/shared-session/inject", {headline:"x"})', context);
  assert.equal(request.options.headers["X-Facilitator-Capability"], "secret / +");

  vm.runInContext("connectStream()", context);
  assert.equal(
    latestSource.url,
    "/stream/shared-session/facilitator"
  );
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
''')


def test_dashboard_restores_only_its_session_scoped_capability():
    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("function updateSessionUrl(");
const end = html.indexOf("function connectStream()", start);
assert.notEqual(start, -1, "session setter not found");

const values = new Map();
let rememberedUrl = null;
const location = new URL("https://example.test/dashboard?ionToken=abc#view");
const elements = {
  sessionInput: { value: "" },
  sessionBadge: { innerHTML: "" },
};
const context = vm.createContext({
  URLSearchParams,
  encodeURIComponent,
  location,
  history: {replaceState: (_state, _title, url) => {
    rememberedUrl = url;
    location.href = new URL(url, location).href;
  }},
  sessionStorage: {
    getItem: key => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
  },
  $: id => elements[id],
  esc: value => value,
  resetView() {}, connectStream() {},
});
vm.runInContext(`
  let sessionId = null;
  let facilitator = false;
  let facilitatorCapability = null;
`, context);
vm.runInContext(html.slice(start, end), context);

vm.runInContext('setSession("shared-session", "secret")', context);
assert.equal(rememberedUrl, "/dashboard?ionToken=abc&game=shared-session#view");
assert.equal(
  values.get("false-flag:facilitator:shared-session"), "secret");
assert.equal(vm.runInContext("facilitatorCapability", context), "secret");
assert.equal(vm.runInContext("facilitator", context), true);

vm.runInContext("facilitatorCapability = null; facilitator = false", context);
vm.runInContext('setSession("shared-session")', context);
assert.equal(vm.runInContext("facilitatorCapability", context), "secret");

vm.runInContext('setSession("player-session")', context);
assert.equal(vm.runInContext("facilitatorCapability", context), null);
assert.equal(vm.runInContext("facilitator", context), false);
''')


def test_dataflow_uses_the_cookie_scoped_operator_stream():
    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("function updateSessionUrl(");
const end = html.indexOf("function setStatus", start);
assert.notEqual(start, -1, "dataflow attach function not found");

let latestSource = null;
let rememberedUrl = null;
const location = new URL("https://example.test/dataflow?ionToken=abc#view");
class FakeEventSource {
  static CLOSED = 2;
  constructor(url) { this.readyState = 0; this.url = url; this.listeners = {}; latestSource = this; }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  close() {}
}
const elements = {
  sessInput: { value: "" },
  sessBadge: { textContent: "" },
  turnBadge: { textContent: "" },
};
const context = vm.createContext({
  URLSearchParams,
  location,
  history: {replaceState: (_state, _title, url) => {
    rememberedUrl = url;
    location.href = new URL(url, location).href;
  }},
  encodeURIComponent,
  EventSource: FakeEventSource,
  sessionStorage: {getItem: () => null, setItem() {}},
  $: id => elements[id],
  clearRunState() {}, renderAll() {}, pulse() {}, renderLive() {},
  renderDtdl() {}, NODE_BY_ID: {}, CTX_NODE: {}, callCounts: {},
  lastCall: {}, selected: null, dtdlOn: false, DTDL_MAP: {}, setStatus() {},
});
vm.runInContext(`
  let sessionId = null;
  let es = null;
  let facilitatorCapability = null;
`, context);
vm.runInContext(html.slice(start, end), context);

vm.runInContext('attach("shared session")', context);
assert.equal(rememberedUrl, null, "unverified session must not replace the URL");
assert.equal(
  latestSource.url,
  "/stream/shared%20session/facilitator"
);
latestSource.listeners.stream_ready({data: '{"viewer":"facilitator"}'});
assert.equal(rememberedUrl, "/dataflow?ionToken=abc&game=shared+session#view");
assert.match(elements.sessBadge.textContent, /operator/);

vm.runInContext('attach("public session")', context);
assert.equal(rememberedUrl, "/dataflow?ionToken=abc&game=shared+session#view");
assert.equal(latestSource.url, "/stream/public%20session/facilitator");
latestSource.onerror();
assert.equal(rememberedUrl, "/dataflow?ionToken=abc&game=shared+session#view");
latestSource.listeners.stream_ready({data: '{"viewer":"public"}'});
assert.equal(rememberedUrl, "/dataflow?ionToken=abc&game=public+session#view");
assert.match(elements.sessBadge.textContent, /public/);
''', DATAFLOW)


def test_supporting_pages_clear_only_confirmed_missing_sessions():
    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const apiStart = html.indexOf("async function api(");
const apiEnd = html.indexOf("function setStatus", apiStart);
const urlStart = html.indexOf("function updateSessionUrl(");
const sessionStart = html.indexOf("function setSession(", urlStart);
const restoreStart = html.indexOf("async function restoreSessionFromUrl()");
const restoreEnd = html.indexOf("/* ----------------------------------------------------------------- ledger", restoreStart);

function harness(status) {
  const urls = [];
  const location = new URL("https://example.test/dashboard?ionToken=abc&game=saved#view");
  const elements = {sessionInput: {value: ""}, sessionBadge: {textContent: ""}};
  const context = vm.createContext({
    URLSearchParams,
    location,
    history: {replaceState: (_state, _title, url) => {
      urls.push(url);
      location.href = new URL(url, location).href;
    }},
    $: id => elements[id],
    fetch: async () => ({
      ok: false, status, statusText: "Unavailable",
      text: async () => status === 404 ? '{"detail":"Session not found"}' : "",
    }),
    setSession() {}, seedFromState() {},
  });
  vm.runInContext(
    "let sessionRequestVersion = 0; let facilitatorCapability = null;",
    context,
  );
  vm.runInContext(html.slice(apiStart, apiEnd), context);
  vm.runInContext(html.slice(urlStart, sessionStart), context);
  vm.runInContext(html.slice(restoreStart, restoreEnd), context);
  return {context, urls, elements};
}

(async () => {
  let h = harness(404);
  await vm.runInContext("restoreSessionFromUrl()", h.context);
  assert.deepEqual(h.urls, ["/dashboard?ionToken=abc#view"]);
  assert.match(h.elements.sessionBadge.textContent, /attach failed/);

  h = harness(503);
  await vm.runInContext("restoreSessionFromUrl()", h.context);
  assert.deepEqual(h.urls, []);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
''')

    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("function updateSessionUrl(");
const end = html.indexOf("function setStatus", start);

function harness(probe, savedId = "saved") {
  const urls = [];
  const timers = [];
  const location = new URL("https://example.test/dataflow?ionToken=abc&game=saved#view");
  location.searchParams.set("game", savedId);
  let latestSource = null;
  class FakeEventSource {
    static CLOSED = 2;
    constructor() { this.readyState = 0; this.listeners = {}; latestSource = this; }
    addEventListener(name, listener) { this.listeners[name] = listener; }
    close() { this.readyState = FakeEventSource.CLOSED; }
  }
  const elements = {
    sessInput: {value: ""}, sessBadge: {textContent: ""}, turnBadge: {textContent: ""},
  };
  const context = vm.createContext({
    URLSearchParams,
    location,
    history: {replaceState: (_state, _title, url) => {
      urls.push(url);
      location.href = new URL(url, location).href;
    }},
    encodeURIComponent,
    EventSource: FakeEventSource,
    fetch: () => typeof probe === "function"
      ? probe() : Promise.resolve({status: probe}),
    setTimeout: callback => { timers.push(callback); },
    sessionStorage: {getItem: () => null, setItem() {}},
    $: id => elements[id],
    clearRunState() {}, renderAll() {}, pulse() {}, renderLive() {}, renderDtdl() {},
    NODE_BY_ID: {}, CTX_NODE: {}, callCounts: {}, lastCall: {}, selected: null,
    dtdlOn: false, DTDL_MAP: {}, setStatus() {},
  });
  vm.runInContext(
    "let sessionId = null; let es = null; let facilitatorCapability = null;",
    context,
  );
  vm.runInContext(html.slice(start, end), context);
  vm.runInContext("restoreSessionFromUrl()", context);
  return {context, source: () => latestSource, urls, elements, timers};
}

async function flushRetryTimers(h) {
  for (let retry = 0; retry < 3 && h.timers.length; retry += 1) {
    h.timers.shift()();
    await new Promise(resolve => setImmediate(resolve));
  }
  assert.equal(h.timers.length, 0, "terminal retries must stop within the budget");
}

(async () => {
  let h = harness(404);
  h.source().onerror();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(h.urls, ["/dataflow?ionToken=abc#view"]);
  assert.equal(vm.runInContext("sessionId", h.context), null);
  assert.equal(h.elements.sessInput.value, "");
  assert.equal(h.elements.sessBadge.textContent, "no session");

  h = harness(404);
  h.elements.sessInput.value = " saved ";
  h.source().onerror();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.elements.sessInput.value, "",
    "whitespace around the old ID does not make it a replacement draft");

  h = harness(404, " saved ");
  h.source().onerror();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.elements.sessInput.value, "",
    "an unchanged whitespace-padded ID from the URL must clear on 404");
  assert.deepEqual(h.urls, ["/dataflow?ionToken=abc#view"]);

  h = harness(503);
  h.source().onerror();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(h.urls, []);

  const probeResults = [503, 404];
  h = harness(() => Promise.resolve({status: probeResults.shift()}));
  h.source().onerror();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(h.urls, []);
  h.source().onerror();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(h.urls, ["/dataflow?ionToken=abc#view"]);

  for (const result of [200, 503, new Error("network down")]) {
    let probes = 0;
    h = harness(() => {
      probes += 1;
      return result instanceof Error
        ? Promise.reject(result) : Promise.resolve({status: result});
    });
    for (let attempt = 0; attempt < 8; attempt += 1) {
      h.source().onerror();
      await new Promise(resolve => setImmediate(resolve));
    }
    assert.equal(probes, 5, "persistent stream failure must stop existence probes");
    assert.deepEqual(h.urls, [], "inconclusive probes must keep the saved URL");
    assert.equal(vm.runInContext("sessionId", h.context), "saved");
    h.source().listeners.stream_ready({data: '{"viewer":"public"}'});
    assert.match(h.elements.sessBadge.textContent, /public/);
    assert.deepEqual(h.urls, ["/dataflow?ionToken=abc&game=saved#view"]);
  }

  for (const finalResult of [404, 200, 401, 403, 429, 503, new Error("still offline")]) {
    let probes = 0;
    h = harness(() => {
      probes += 1;
      if (probes <= 5) return Promise.reject(new Error("server down"));
      return finalResult instanceof Error
        ? Promise.reject(finalResult) : Promise.resolve({status: finalResult});
    });
    for (let attempt = 0; attempt < 8; attempt += 1) {
      h.source().onerror();
      await new Promise(resolve => setImmediate(resolve));
    }
    assert.equal(probes, 5);
    h.source().readyState = 2;
    for (let attempt = 0; attempt < 3; attempt += 1) {
      h.source().onerror();
      await new Promise(resolve => setImmediate(resolve));
    }
    await flushRetryTimers(h);
    const retryable = finalResult instanceof Error || (finalResult >= 400 && finalResult !== 404);
    assert.equal(probes, retryable ? 8 : 6, "terminal checks must stay within their three-attempt budget");
    assert.equal(vm.runInContext("sessionId", h.context), finalResult === 404 ? null : "saved");
    assert.deepEqual(h.urls, finalResult === 404 ? ["/dataflow?ionToken=abc#view"] : []);
  }

  for (const transientResult of [401, 403, 429, 503, new Error("terminal network blip")]) {
    let probes = 0;
    h = harness(() => {
      probes += 1;
      if (probes <= 5) return Promise.reject(new Error("server down"));
      if (probes === 6) return transientResult instanceof Error
        ? Promise.reject(transientResult) : Promise.resolve({status: transientResult});
      return Promise.resolve({status: 404});
    });
    for (let attempt = 0; attempt < 5; attempt += 1) {
      h.source().onerror();
      await new Promise(resolve => setImmediate(resolve));
    }
    h.source().readyState = 2;
    h.source().onerror();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(h.timers.length, 1, "an inconclusive terminal check must schedule a retry");
    await flushRetryTimers(h);
    assert.equal(probes, 7);
    assert.equal(vm.runInContext("sessionId", h.context), null);
    assert.equal(h.elements.sessInput.value, "");
    assert.deepEqual(h.urls, ["/dataflow?ionToken=abc#view"]);
  }

  for (const pendingResult of [503, new Error("last probe failed")]) {
    let finishPendingProbe;
    let probes = 0;
    h = harness(() => {
      probes += 1;
      if (probes < 5) return Promise.reject(new Error("server down"));
      if (probes === 5) return new Promise((resolve, reject) => {
        finishPendingProbe = () => pendingResult instanceof Error
          ? reject(pendingResult) : resolve({status: pendingResult});
      });
      return Promise.resolve({status: 404});
    });
    for (let attempt = 0; attempt < 5; attempt += 1) {
      h.source().onerror();
      await new Promise(resolve => setImmediate(resolve));
    }
    h.source().readyState = 2;
    h.source().onerror();
    assert.equal(probes, 5, "the final probe must not overlap a pending probe");
    finishPendingProbe();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(probes, 6, "an inconclusive pending probe must not swallow the final check");
    assert.equal(vm.runInContext("sessionId", h.context), null);
    assert.deepEqual(h.urls, ["/dataflow?ionToken=abc#view"]);
  }

  for (const manualId of [null, "manual-session"]) {
    h = harness(404);
    if (manualId) vm.runInContext(`attach(${JSON.stringify(manualId)})`, h.context);
    h.source().listeners.stream_ready({data: '{"viewer":"public"}'});
    h.source().readyState = 2;
    h.source().onerror();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(vm.runInContext("sessionId", h.context), null,
      "terminal session loss must clear a previously connected session");
    assert.equal(h.elements.sessInput.value, "");
    assert.equal(h.urls.at(-1), "/dataflow?ionToken=abc#view");
  }

  for (const manualId of ["saved", "missing-manual"]) {
    h = harness(404);
    vm.runInContext(`attach(${JSON.stringify(manualId)})`, h.context);
    h.source().readyState = 2;
    h.source().onerror();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(vm.runInContext("sessionId", h.context), null,
      "a confirmed missing manual attachment must clear its session status");
    assert.equal(h.elements.sessBadge.textContent, "no session");
    assert.equal(h.elements.sessInput.value, manualId, "keep the typed ID available for correction");
    assert.deepEqual(h.urls, manualId === "saved" ? ["/dataflow?ionToken=abc#view"] : [],
      "a failed replacement must preserve the last working session URL");
  }

  let resolveProbe;
  let postReadyProbes = 0;
  h = harness(() => {
    postReadyProbes += 1;
    return postReadyProbes === 1
      ? new Promise(resolve => { resolveProbe = resolve; }) : Promise.resolve({status: 200});
  });
  h.source().onerror();
  h.source().listeners.stream_ready({data: '{"viewer":"public"}'});
  h.source().readyState = 2;
  h.source().onerror();
  assert.equal(postReadyProbes, 1, "closure after readiness must still respect an in-flight probe");
  resolveProbe({status: 404});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(postReadyProbes, 2, "closure after readiness still needs its own final probe");
  assert.equal(vm.runInContext("sessionId", h.context), "saved",
    "a pre-readiness 404 must not override the newer final probe's HTTP 200");
  assert.deepEqual(h.urls, ["/dataflow?ionToken=abc&game=saved#view"]);

  h = harness(() => new Promise(resolve => { resolveProbe = resolve; }));
  h.source().onerror();
  vm.runInContext('attach("saved")', h.context);
  h.source().listeners.stream_ready({data: '{"viewer":"public"}'});
  resolveProbe({status: 404});
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(h.urls, ["/dataflow?ionToken=abc&game=saved#view"]);

  h = harness(() => new Promise(resolve => { resolveProbe = resolve; }));
  h.source().onerror();
  h.elements.sessInput.value = "replacement session draft";
  resolveProbe({status: 404});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(vm.runInContext("sessionId", h.context), null);
  assert.deepEqual(h.urls, ["/dataflow?ionToken=abc#view"]);
  assert.equal(h.elements.sessInput.value, "replacement session draft",
    "a delayed 404 must preserve an unsubmitted replacement ID");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
''', DATAFLOW)


def test_dashboard_restore_cannot_override_a_newer_attach_attempt():
    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const urlStart = html.indexOf("function updateSessionUrl(");
const sessionStart = html.indexOf("function setSession(", urlStart);
const start = html.indexOf('$("btnNew").onclick');
const end = html.indexOf("/* ----------------------------------------------------------------- ledger", start);
assert.notEqual(start, -1, "dashboard session handlers not found");

function harness() {
  const pending = new Map();
  const attached = [];
  const urls = [];
  const location = new URL("https://example.test/dashboard?game=old-session");
  const elements = {
    btnNew: {}, btnAttach: {}, btnDemo: {}, btnDemoStop: {}, btnResetView: {},
    sessionInput: {value: ""}, sessionBadge: {textContent: ""},
  };
  let context;
  context = vm.createContext({
    URLSearchParams,
    encodeURIComponent,
    location,
    history: {replaceState: (_state, _title, url) => {
      urls.push(url);
      location.href = new URL(url, location).href;
    }},
    $: id => elements[id],
    api: (_method, path) => new Promise((resolve, reject) => {
      pending.set(path, {resolve, reject});
    }),
    setSession: id => {
      attached.push(id);
      vm.runInContext(`sessionId = ${JSON.stringify(id)}`, context);
    },
    seedFromState() {}, resetView() {}, alert() {},
  });
  vm.runInContext(`
    let sessionId = null;
    let sessionRequestVersion = 0;
    let mode = "immersive";
    let mystery = false;
  `, context);
  vm.runInContext(html.slice(urlStart, sessionStart), context);
  vm.runInContext(html.slice(start, end), context);
  return {pending, attached, elements, context, urls};
}

function startRestoreThenAttach(h) {
  const restore = vm.runInContext("restoreSessionFromUrl()", h.context);
  h.elements.sessionInput.value = "new-session";
  const attach = vm.runInContext('$("btnAttach").onclick()', h.context);
  return {restore, attach};
}

(async () => {
  let h = harness();
  let {restore, attach} = startRestoreThenAttach(h);
  h.pending.get("/game/old-session").resolve({turn: 2, metrics: {}});
  await restore;
  assert.deepEqual(h.attached, [], "old restore must not win after Attach starts");
  h.pending.get("/game/new-session").resolve({turn: 1, metrics: {}});
  await attach;
  assert.deepEqual(h.attached, ["new-session"]);

  h = harness();
  ({restore, attach} = startRestoreThenAttach(h));
  const missing = new Error("old session missing");
  missing.status = 404;
  h.pending.get("/game/old-session").reject(missing);
  await restore;
  assert.deepEqual(h.urls, [], "stale 404 must not clear the newer session URL");
  assert.doesNotMatch(h.elements.sessionBadge.textContent, /attach failed/);
  h.pending.get("/game/new-session").resolve({turn: 1, metrics: {}});
  await attach;
  assert.deepEqual(h.attached, ["new-session"]);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
''')


def test_dashboard_keeps_metric_history_ordered_by_turn():
    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("function recordMetrics(");
const end = html.indexOf("function drawCharts(", start);
assert.notEqual(start, -1, "metric recorder not found");

const context = vm.createContext({
  series: {escalation_risk: []},
  drawCharts() {},
});
vm.runInContext(html.slice(start, end), context);
vm.runInContext(`
  recordMetrics({turn: 3, metrics: {escalation_risk: 30}});
  recordMetrics({turn: 1, metrics: {escalation_risk: 10}});
  recordMetrics({turn: 2, metrics: {escalation_risk: 20}});
  recordMetrics({turn: 2, metrics: {escalation_risk: 21}});
`, context);

const points = JSON.parse(vm.runInContext(
  "JSON.stringify(series.escalation_risk)", context));
assert.deepEqual(points, [
  {turn: 1, v: 10},
  {turn: 2, v: 21},
  {turn: 3, v: 30},
]);
''')


def test_supporting_pages_restore_the_game_query_on_boot():
    dashboard_html = DASHBOARD.read_text(encoding="utf-8")
    dataflow_html = DATAFLOW.read_text(encoding="utf-8")
    assert dashboard_html.index("restoreSessionFromUrl();") > dashboard_html.index("boot */")
    assert dataflow_html.index("restoreSessionFromUrl();") > dataflow_html.index("loadLayout();")

    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("async function restoreSessionFromUrl()");
const end = html.indexOf("/* ----------------------------------------------------------------- ledger", start);
assert.notEqual(start, -1, "dashboard URL restore function not found");

let requested = null;
let attached = null;
let seeded = null;
const elements = {sessionInput: {value: ""}, sessionBadge: {textContent: ""}};
const context = vm.createContext({
  URLSearchParams,
  encodeURIComponent,
  location: {search: "?game=shared%20session"},
  $: id => elements[id],
  api: async (method, path) => {
    requested = {method, path};
    return {turn: 2, metrics: {escalation_risk: 51}};
  },
  setSession: id => { attached = id; },
  seedFromState: state => { seeded = state; },
});
vm.runInContext("let sessionId = null; let sessionRequestVersion = 0;", context);
vm.runInContext(html.slice(start, end), context);

(async () => {
  await vm.runInContext("restoreSessionFromUrl()", context);
  assert.deepEqual(requested, {method: "GET", path: "/game/shared%20session"});
  assert.equal(attached, "shared session");
  assert.equal(seeded.turn, 2);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
''')

    _run_node(r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("function restoreSessionFromUrl()");
const end = html.indexOf("function setStatus", start);
assert.notEqual(start, -1, "dataflow URL restore function not found");

let attached = null;
const elements = {sessInput: {value: ""}};
const context = vm.createContext({
  URLSearchParams,
  location: {search: "?game=shared%20session"},
  $: id => elements[id],
  attach: id => { attached = id; },
});
vm.runInContext(html.slice(start, end), context);
vm.runInContext("restoreSessionFromUrl()", context);
assert.equal(elements.sessInput.value, "shared session");
assert.equal(attached, "shared session");
''', DATAFLOW)


def test_dataflow_treats_server_model_names_as_text():
    html = DATAFLOW.read_text(encoding="utf-8")

    assert "d2.textContent = last" in html
    assert "kv.textContent = `default tier" in html
    assert "d2.innerHTML = last" not in html
    assert "kv.innerHTML = `default tier" not in html
