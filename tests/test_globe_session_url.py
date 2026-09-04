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
const start = html.indexOf("function updateSessionUrl(");
const end = html.indexOf('$("sessionInput").addEventListener', start);
assert.notEqual(start, -1, "attach function not found");
assert.notEqual(end, -1, "attach handler boundary not found");

const elements = {
  sessionInput: { value: "failed-session" },
  sessionBadge: { textContent: "session good-ses…" },
  btnAttach: {},
};
let currentUrl = "/globe?game=good-session&ionToken=token#view";
let historyCalls = 0;
let renderCalls = 0;
let connectCalls = 0;
let requestedUrl = null;
const location = new URL("https://example.test" + currentUrl);

const context = vm.createContext({
  URLSearchParams,
  encodeURIComponent,
  location,
  fetch: async url => {
    requestedUrl = url;
    return { ok: false, status: 404 };
  },
  history: {
    replaceState(_state, _title, url) {
      currentUrl = url;
      location.href = new URL(url, location).href;
      historyCalls += 1;
    },
  },
  $: id => elements[id],
  renderTheatre: () => { renderCalls += 1; },
  connectStream: () => { connectCalls += 1; },
  flashLive: () => {},
  setStatus: () => {},
  esc: value => value,
});

vm.runInContext(`
  let attachSeq = 0;
  let sessionId = "good-session";
  const theatreEtags = new Map();
  let lastRenderedTheatre = { id: "good-session", data: {} };
  let source = {
    closed: false,
    close() { this.closed = true; },
  };
`, context);
vm.runInContext(html.slice(start, end), context);

(async () => {
  vm.runInContext('$("btnAttach").onclick()', context);
  await new Promise(setImmediate);
  const state = vm.runInContext("({ sessionId, sourceClosed: source.closed })", context);
  assert.equal(currentUrl, "/globe?game=good-session&ionToken=token#view");
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
  historyCalls = 0;
  await vm.runInContext('attach("new-session")', context);
  assert.equal(currentUrl, "/globe?game=new-session&ionToken=token#view");
  assert.equal(historyCalls, 1);
  assert.equal(requestedUrl, "/game/new-session/theatre");
  assert.equal(renderCalls, 1);
  assert.equal(connectCalls, 1);
  assert.equal(vm.runInContext('theatreEtags.get("new-session")', context), '"good-etag"');

  // Another control changes the URL between attaches; preserve its latest values.
  context.history.replaceState(null, "",
    "/globe?game=new-session&ionToken=updated&overlay=weather#latest");
  await vm.runInContext('attach("next-session")', context);
  assert.equal(currentUrl,
    "/globe?game=next-session&ionToken=updated&overlay=weather#latest");
  assert.equal(historyCalls, 3);
  assert.equal(requestedUrl, "/game/next-session/theatre");
  assert.equal(renderCalls, 2);
  assert.equal(connectCalls, 2);
  assert.equal(vm.runInContext("sessionId", context), "next-session");
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


def test_globe_attach_render_failure_preserves_previous_session():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("function updateSessionUrl(");
const end = html.indexOf('$("btnAttach").onclick', start);
assert.notEqual(start, -1, "attach function not found");
assert.notEqual(end, -1, "attach handler boundary not found");

const elements = {
  sessionInput: { value: "" },
  sessionBadge: { textContent: "session prior-seâ€¦" },
};
let currentUrl = "/globe?game=prior-session&ionToken=token#view";
let historyCalls = 0;
let connectCalls = 0;
const location = new URL("https://example.test" + currentUrl);

const context = vm.createContext({
  URLSearchParams,
  location,
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
      location.href = new URL(url, location).href;
      historyCalls += 1;
    },
  },
  $: id => elements[id],
  renderTheatre: () => { throw new Error("render failed"); },
  connectStream: () => { connectCalls += 1; },
  flashLive: () => {},
  setStatus: () => {},
  esc: value => value,
});

vm.runInContext(`
  let attachSeq = 0;
  let sessionId = "prior-session";
  const theatreEtags = new Map([["prior-session", '"prior-etag"']]);
  let lastRenderedTheatre = { id: "prior-session", data: {} };
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

  assert.equal(currentUrl, "/globe?game=prior-session&ionToken=token#view");
  assert.equal(historyCalls, 0);
  assert.equal(state.sessionId, "prior-session");
  assert.equal(elements.sessionBadge.textContent, "session prior-seâ€¦");
  assert.equal(state.sameSource, true);
  assert.equal(state.priorSourceClosed, false);
  assert.equal(connectCalls, 0);
  assert.equal(state.priorEtag, '"prior-etag"');
  assert.equal(state.candidateEtag, undefined);

  context.renderTheatre = () => {};
  await vm.runInContext('attach("candidate-session")', context);
  assert.equal(vm.runInContext("sessionId", context), "candidate-session");
  assert.equal(currentUrl, "/globe?game=candidate-session&ionToken=token#view");
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


def test_globe_attach_render_failure_restores_previous_display():
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf('let sessionId = params.get("game") || "";');
const end = html.indexOf('$("btnAttach").onclick', start);
assert.notEqual(start, -1, "session state not found");
assert.notEqual(end, -1, "attach handler boundary not found");

const priorData = {
  schema_version: 1,
  session_id: "prior-session",
  turn: 1,
  phase: "discussion",
  forces: [{
    id: "prior-unit", branch: "naval", unit_type: "frigate", location: "Portsmouth",
    status: "ready", role: null, readiness_turns: null, notes: null,
  }],
  stockpiles: [{ category: "fuel", name: "prior-stock", count: 10, note: null }],
};
const candidateData = {
  schema_version: 1,
  session_id: "candidate-session",
  turn: 2,
  phase: "decision",
  forces: [{
    id: "candidate-unit", branch: "air", unit_type: "fighter", location: "RAF Marham",
    status: "ready", role: null, readiness_turns: null, notes: null,
  }],
  stockpiles: [{ category: "fuel", name: "candidate-stock", count: 5, note: null }],
};
const displayed = { map: null, tray: null, status: null };
const renders = [];
const flashes = [];
let currentUrl = "/globe?game=prior-session&ionToken=token#view";
let historyCalls = 0;
let setStatusCalls = 0;
let connectCalls = 0;
const location = new URL("https://example.test" + currentUrl);

const elements = {
  sessionInput: { value: "" },
  sessionBadge: { textContent: "session prior-seâ€¦" },
};
const priorSource = {
  closed: false,
  close() { this.closed = true; },
};

const context = vm.createContext({
  URLSearchParams,
  location,
  encodeURIComponent,
  params: { get: name => name === "game" ? "prior-session" : null },
  fetch: async () => ({
    ok: true,
    status: 200,
    headers: { get: name => name.toLowerCase() === "etag" ? '"candidate-etag"' : null },
    json: async () => candidateData,
  }),
  history: {
    replaceState(_state, _title, url) {
      currentUrl = url;
      location.href = new URL(url, location).href;
      historyCalls += 1;
    },
  },
  $: id => elements[id],
  esc: value => value,
  priorData,
  priorSource,
  captureRender: (id, data) => {
    renders.push(id);
    displayed.map = data.forces[0].id;
    displayed.tray = data.stockpiles[0].name;
    displayed.status = `turn ${data.turn} ${data.phase}`;
    if (id === "candidate-session") throw new Error("candidate render failed");
  },
  captureStatus: value => {
    setStatusCalls += 1;
    displayed.status = value;
  },
  captureFlash: (kind, note) => { flashes.push([kind, note]); },
  captureConnect: () => { connectCalls += 1; },
  EventSource: class {},
  setTimeout,
  clearTimeout,
});

vm.runInContext(html.slice(start, end), context);
vm.runInContext(`
  renderResources = captureRender;
  setStatus = captureStatus;
  flashLive = captureFlash;
  connectStream = captureConnect;
  source = priorSource;
  theatreEtags.set("prior-session", '"prior-etag"');
  if (typeof renderTheatre === "function") renderTheatre("prior-session", priorData);
  else renderResources("prior-session", priorData);
`, context);

(async () => {
  await vm.runInContext('attach("candidate-session")', context);
  const state = vm.runInContext(`({
    sessionId,
    sameSource: source === priorSource,
    priorSourceClosed: priorSource.closed,
    priorEtag: theatreEtags.get("prior-session"),
    candidateEtag: theatreEtags.get("candidate-session"),
  })`, context);

  assert.deepEqual(displayed, {
    map: "prior-unit",
    tray: "prior-stock",
    status: "turn 1 discussion",
  });
  assert.deepEqual(renders, ["prior-session", "candidate-session", "prior-session"]);
  assert.deepEqual(flashes, [["attach failed", "candidate render failed"]]);
  assert.equal(setStatusCalls, 0, "restored status must not be overwritten by the error");
  assert.equal(currentUrl, "/globe?game=prior-session&ionToken=token#view");
  assert.equal(historyCalls, 0);
  assert.equal(state.sessionId, "prior-session");
  assert.equal(elements.sessionBadge.textContent, "session prior-seâ€¦");
  assert.equal(state.sameSource, true);
  assert.equal(state.priorSourceClosed, false);
  assert.equal(connectCalls, 0);
  assert.equal(state.priorEtag, '"prior-etag"');
  assert.equal(state.candidateEtag, undefined);

  vm.runInContext("renderResources = () => {}", context);
  await vm.runInContext('attach("candidate-session")', context);
  assert.equal(vm.runInContext("sessionId", context), "candidate-session");
  assert.equal(currentUrl, "/globe?game=candidate-session&ionToken=token#view");
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
  renderTheatre: () => {
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


def test_globe_revalidates_after_every_stream_ready_signal():
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
let latestSource = null;

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
  assert.equal(typeof latestSource.listeners.stream_ready, "function");

  latestSource.listeners.stream_ready({ data: "{}" });
  await new Promise(setImmediate);
  assert.equal(requests.length, 1, "initial ready must revalidate the snapshot");

  latestSource.listeners.stream_ready({ data: "{}" });
  await new Promise(setImmediate);
  assert.equal(requests.length, 2, "reconnect ready must revalidate again");
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
