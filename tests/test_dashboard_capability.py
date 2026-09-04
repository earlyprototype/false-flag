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
const start = html.indexOf("function setSession(");
const end = html.indexOf("function connectStream()", start);
assert.notEqual(start, -1, "session setter not found");

const values = new Map();
let rememberedUrl = null;
const elements = {
  sessionInput: { value: "" },
  sessionBadge: { innerHTML: "" },
};
const context = vm.createContext({
  URLSearchParams,
  encodeURIComponent,
  location: {search: ""},
  history: {replaceState: (_state, _title, url) => { rememberedUrl = url; }},
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
assert.equal(rememberedUrl, "?game=shared-session");
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
const start = html.indexOf("function attach(");
const end = html.indexOf("function setStatus", start);
assert.notEqual(start, -1, "dataflow attach function not found");

let latestSource = null;
let rememberedUrl = null;
class FakeEventSource {
  constructor(url) { this.url = url; this.listeners = {}; latestSource = this; }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  close() {}
}
const elements = {
  sessBadge: { textContent: "" },
  turnBadge: { textContent: "" },
};
const context = vm.createContext({
  URLSearchParams,
  location: {search: ""},
  history: {replaceState: (_state, _title, url) => { rememberedUrl = url; }},
  encodeURIComponent,
  EventSource: FakeEventSource,
  sessionStorage: {getItem: () => null, setItem() {}},
  $: id => elements[id],
  clearRunState() {}, renderAll() {}, pulse() {}, renderLive() {},
  renderDtdl() {}, NODE_BY_ID: {}, CTX_NODE: {}, callCounts: {},
  lastCall: {}, selected: null, dtdlOn: false, DTDL_MAP: {},
});
vm.runInContext(`
  let sessionId = null;
  let es = null;
  let facilitatorCapability = null;
`, context);
vm.runInContext(html.slice(start, end), context);

vm.runInContext('attach("shared session")', context);
assert.equal(rememberedUrl, "?game=shared%20session");
assert.equal(
  latestSource.url,
  "/stream/shared%20session/facilitator"
);
latestSource.listeners.stream_ready({data: '{"viewer":"facilitator"}'});
assert.match(elements.sessBadge.textContent, /operator/);

vm.runInContext('attach("public session")', context);
assert.equal(latestSource.url, "/stream/public%20session/facilitator");
latestSource.listeners.stream_ready({data: '{"viewer":"public"}'});
assert.match(elements.sessBadge.textContent, /public/);
''', DATAFLOW)


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
