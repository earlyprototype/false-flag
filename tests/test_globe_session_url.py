"""Behavior checks for the Situation Globe session URL."""

import subprocess
from pathlib import Path


REPO = Path(__file__).parent.parent
GLOBE = REPO / "api" / "globe.html"


def test_globe_attach_preserves_last_successful_session_url():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("async function attach(id)");
const end = html.indexOf('$("sessionInput").addEventListener', start);
assert.notEqual(start, -1, "attach function not found");
assert.notEqual(end, -1, "attach handler boundary not found");

const elements = {
  sessionInput: { value: "failed-session" },
  sessionBadge: { textContent: "session good-ses…" },
  btnAttach: {},
};
let currentUrl = "?game=good-session";
let historyCalls = 0;
let renderCalls = 0;
let connectCalls = 0;
let requestedUrl = null;

const context = vm.createContext({
  encodeURIComponent,
  fetch: async url => {
    requestedUrl = url;
    return { ok: false, status: 404 };
  },
  history: {
    replaceState(_state, _title, url) {
      currentUrl = url;
      historyCalls += 1;
    },
  },
  $: id => elements[id],
  renderResources: () => { renderCalls += 1; },
  connectStream: () => { connectCalls += 1; },
  flashLive: () => {},
  setStatus: () => {},
  esc: value => value,
});

vm.runInContext(`
  let attachSeq = 0;
  let sessionId = "good-session";
  const theatreEtags = new Map();
  let source = {
    closed: false,
    close() { this.closed = true; },
  };
`, context);
vm.runInContext(html.slice(start, end), context);
vm.runInContext('$("btnAttach").onclick()', context);

setImmediate(() => {
  const state = vm.runInContext("({ sessionId, sourceClosed: source.closed })", context);
  assert.equal(currentUrl, "?game=good-session");
  assert.equal(historyCalls, 0);
  assert.equal(state.sessionId, "good-session");
  assert.equal(state.sourceClosed, false);
  assert.equal(elements.sessionBadge.textContent, "session good-ses…");
  assert.equal(renderCalls, 0);
  assert.equal(connectCalls, 0);
  assert.equal(requestedUrl, "/game/failed-session/theatre");

  context.fetch = async url => {
    requestedUrl = url;
    return {
      ok: true,
      status: 200,
      headers: { get: name => name.toLowerCase() === "etag" ? '"good-etag"' : null },
      json: async () => ({}),
    };
  };
  currentUrl = "?game=good-session&ionToken=token#view";
  historyCalls = 0;
  vm.runInContext('attach("good-session")', context);

  setImmediate(() => {
    assert.equal(currentUrl, "?game=good-session&ionToken=token#view");
    assert.equal(historyCalls, 0);
    assert.equal(requestedUrl, "/game/good-session/theatre");
    assert.equal(renderCalls, 1);
    assert.equal(connectCalls, 1);
    assert.equal(vm.runInContext('theatreEtags.get("good-session")', context), '"good-etag"');
  });
});
"""

    result = subprocess.run(
        ["node", "-e", script, str(GLOBE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_globe_attach_render_failure_preserves_previous_session():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("async function attach(id)");
const end = html.indexOf('$("btnAttach").onclick', start);
assert.notEqual(start, -1, "attach function not found");
assert.notEqual(end, -1, "attach handler boundary not found");

const elements = {
  sessionInput: { value: "" },
  sessionBadge: { textContent: "session prior-seâ€¦" },
};
let currentUrl = "?game=prior-session&ionToken=token#view";
let historyCalls = 0;
let connectCalls = 0;

const context = vm.createContext({
  encodeURIComponent,
  fetch: async () => ({
    ok: true,
    status: 200,
    headers: { get: name => name.toLowerCase() === "etag" ? '"candidate-etag"' : null },
    json: async () => ({
      schema_version: 1,
      session_id: "candidate-session",
      turn: 2,
      phase: "decision",
      forces: [],
      stockpiles: [],
    }),
  }),
  history: {
    replaceState(_state, _title, url) {
      currentUrl = url;
      historyCalls += 1;
    },
  },
  $: id => elements[id],
  renderResources: () => { throw new Error("render failed"); },
  connectStream: () => { connectCalls += 1; },
  flashLive: () => {},
  setStatus: () => {},
  esc: value => value,
});

vm.runInContext(`
  let attachSeq = 0;
  let sessionId = "prior-session";
  const theatreEtags = new Map([["prior-session", '"prior-etag"']]);
  const priorSource = {
    closed: false,
    close() { this.closed = true; },
  };
  let source = priorSource;
`, context);
vm.runInContext(html.slice(start, end), context);

(async () => {
  await vm.runInContext('attach("candidate-session")', context);
  const state = vm.runInContext(`({
    sessionId,
    sameSource: source === priorSource,
    priorSourceClosed: priorSource.closed,
    priorEtag: theatreEtags.get("prior-session"),
    candidateEtag: theatreEtags.get("candidate-session"),
  })`, context);

  assert.equal(currentUrl, "?game=prior-session&ionToken=token#view");
  assert.equal(historyCalls, 0);
  assert.equal(state.sessionId, "prior-session");
  assert.equal(elements.sessionBadge.textContent, "session prior-seâ€¦");
  assert.equal(state.sameSource, true);
  assert.equal(state.priorSourceClosed, false);
  assert.equal(connectCalls, 0);
  assert.equal(state.priorEtag, '"prior-etag"');
  assert.equal(state.candidateEtag, undefined);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
"""

    result = subprocess.run(
        ["node", "-e", script, str(GLOBE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_globe_revalidates_theatre_after_stream_notification():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("async function loadTheatre()");
const end = html.indexOf("async function attach(id)", start);
assert.notEqual(start, -1, "loadTheatre function not found");
assert.notEqual(end, -1, "session feed boundary not found");

const requests = [];
const responses = [
  {
    ok: true,
    status: 200,
    headers: { get: name => name.toLowerCase() === "etag" ? '"etag-a"' : null },
    json: async () => ({ forces: [{ id: "unit-a" }], stockpiles: [] }),
  },
  {
    ok: true,
    status: 200,
    headers: { get: name => name.toLowerCase() === "etag" ? '"etag-a"' : null },
    json: async () => ({ forces: [{ id: "unit-a" }], stockpiles: [] }),
  },
  {
    ok: false,
    status: 304,
    headers: { get: name => name.toLowerCase() === "etag" ? '"etag-a"' : null },
  },
];
let latestSource = null;
let renderCalls = 0;
let renderFails = true;

class FakeEventSource {
  constructor(url) {
    this.url = url;
    this.listeners = {};
    latestSource = this;
  }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  close() {}
}

const context = vm.createContext({
  encodeURIComponent,
  EventSource: FakeEventSource,
  fetch: async (url, options = {}) => {
    requests.push({ url, options });
    return responses.shift();
  },
  setTimeout: handler => { handler(); return 1; },
  clearTimeout: () => {},
  renderResources: () => {
    renderCalls += 1;
    if (renderFails) throw new Error("render failed");
  },
  flashLive: () => {},
});

vm.runInContext(`
  let sessionId = "session-a";
  let source = null, refetchTimer = null;
  const theatreEtags = new Map();
  let theatreLoadPromise = null, theatreLoadQueued = false;
`, context);
vm.runInContext(html.slice(start, end), context);

(async () => {
  await assert.rejects(vm.runInContext("loadTheatre()", context), /render failed/);
  assert.equal(vm.runInContext('theatreEtags.get("session-a")', context), undefined);

  renderFails = false;
  await vm.runInContext("loadTheatre()", context);
  assert.equal(renderCalls, 2);
  assert.equal(requests[1].url, "/game/session-a/theatre");
  assert.equal(requests[1].options.headers?.["If-None-Match"], undefined);
  assert.equal(vm.runInContext('theatreEtags.get("session-a")', context), '"etag-a"');

  vm.runInContext("connectStream()", context);
  latestSource.listeners.state_update({ data: '{"turn": 1}' });
  await new Promise(setImmediate);

  assert.equal(requests[2].url, "/game/session-a/theatre");
  assert.equal(requests[2].options.headers["If-None-Match"], '"etag-a"');
  assert.equal(renderCalls, 2, "304 must keep the current plotted view");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
"""

    result = subprocess.run(
        ["node", "-e", script, str(GLOBE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_globe_serializes_busy_theatre_revalidations_with_one_trailing_fetch():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf('let sessionId = params.get("game") || "";');
const end = html.indexOf("// Bursts", start);
assert.notEqual(start, -1, "session state not found");
assert.notEqual(end, -1, "loadTheatre boundary not found");

const requests = [];
const pending = [];
const rendered = [];
const context = vm.createContext({
  encodeURIComponent,
  params: { get: name => name === "game" ? "session-a" : null },
  fetch: (url, options = {}) => new Promise(resolve => {
    requests.push({ url, options });
    pending.push(resolve);
  }),
  captureRender: (_id, data) => { rendered.push(data.turn); },
  captureFlash: () => {},
});

vm.runInContext(html.slice(start, end), context);
vm.runInContext("renderResources = captureRender; flashLive = captureFlash", context);

const response = (etag, turn) => ({
  ok: true,
  status: 200,
  headers: { get: name => name.toLowerCase() === "etag" ? etag : null },
  json: async () => ({ turn, forces: [], stockpiles: [] }),
});

(async () => {
  const first = vm.runInContext("loadTheatre()", context);
  await new Promise(setImmediate);
  assert.equal(requests.length, 1);

  const duringFirstA = vm.runInContext("loadTheatre()", context);
  const duringFirstB = vm.runInContext("loadTheatre()", context);
  await new Promise(setImmediate);
  assert.equal(requests.length, 1, "busy calls must not start parallel fetches");

  pending.shift()(response('"etag-1"', 1));
  await new Promise(setImmediate);
  assert.equal(requests.length, 2, "busy calls must guarantee one trailing fetch");

  const duringTrailingA = vm.runInContext("loadTheatre()", context);
  const duringTrailingB = vm.runInContext("loadTheatre()", context);
  await new Promise(setImmediate);
  assert.equal(requests.length, 2, "calls during the trailing fetch must coalesce");

  pending.shift()(response('"etag-2"', 2));
  await new Promise(setImmediate);
  assert.equal(requests.length, 3, "calls during a trailing fetch must not be dropped");

  pending.shift()(response('"etag-3"', 3));
  await Promise.all([first, duringFirstA, duringFirstB, duringTrailingA, duringTrailingB]);

  assert.deepEqual(rendered, [1, 2, 3]);
  assert.equal(vm.runInContext('theatreEtags.get("session-a")', context), '"etag-3"');
  assert.equal(requests.length, 3);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
"""

    result = subprocess.run(
        ["node", "-e", script, str(GLOBE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_globe_revalidates_after_every_stream_open_with_handlers_installed():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf('let sessionId = params.get("game") || "";');
const end = html.indexOf("async function attach(id)", start);
assert.notEqual(start, -1, "session state not found");
assert.notEqual(end, -1, "session feed boundary not found");

const requests = [];
const openRegistration = [];
let latestSource = null;

class FakeEventSource {
  constructor(url) {
    this.url = url;
    this.listeners = {};
    latestSource = this;
  }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  close() {}
  set onopen(handler) {
    openRegistration.push(Object.keys(this.listeners).sort());
    this.openHandler = handler;
  }
}

const context = vm.createContext({
  encodeURIComponent,
  EventSource: FakeEventSource,
  params: { get: name => name === "game" ? "session-a" : null },
  fetch: async (url, options = {}) => {
    requests.push({ url, options });
    return { ok: false, status: 304 };
  },
  setTimeout,
  clearTimeout,
  captureRender: () => {},
  captureFlash: () => {},
});

vm.runInContext(html.slice(start, end), context);
vm.runInContext("renderResources = captureRender; flashLive = captureFlash", context);

(async () => {
  vm.runInContext("connectStream()", context);
  assert.deepEqual(openRegistration, [[
    "adjudication", "diplomacy", "ending", "inject_fired", "intel", "llm_call",
    "parse_health", "state_update", "system", "transcript",
  ]], "open handler must be installed after all stream handlers");

  latestSource.openHandler();
  await new Promise(setImmediate);
  assert.equal(requests.length, 1, "initial open must revalidate the snapshot");

  latestSource.openHandler();
  await new Promise(setImmediate);
  assert.equal(requests.length, 2, "EventSource reconnect must revalidate again");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
"""

    result = subprocess.run(
        ["node", "-e", script, str(GLOBE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
