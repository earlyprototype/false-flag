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
    ok: false,
    status: 304,
    headers: { get: name => name.toLowerCase() === "etag" ? '"etag-a"' : null },
  },
];
let latestSource = null;
let renderCalls = 0;

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
  renderResources: () => { renderCalls += 1; },
  flashLive: () => {},
});

vm.runInContext(`
  let sessionId = "session-a";
  let source = null, refetchTimer = null;
  const theatreEtags = new Map();
`, context);
vm.runInContext(html.slice(start, end), context);

(async () => {
  await vm.runInContext("loadTheatre()", context);
  assert.equal(renderCalls, 1);
  assert.equal(requests[0].url, "/game/session-a/theatre");
  assert.equal(requests[0].options.headers?.["If-None-Match"], undefined);
  assert.equal(vm.runInContext('theatreEtags.get("session-a")', context), '"etag-a"');

  vm.runInContext("connectStream()", context);
  latestSource.listeners.state_update({ data: '{"turn": 1}' });
  await new Promise(setImmediate);

  assert.equal(requests[1].url, "/game/session-a/theatre");
  assert.equal(requests[1].options.headers["If-None-Match"], '"etag-a"');
  assert.equal(renderCalls, 1, "304 must keep the current plotted view");
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
