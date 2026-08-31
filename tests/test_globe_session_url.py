"""Behavior checks for the Situation Globe session URL."""

import subprocess
from pathlib import Path


REPO = Path(__file__).parent.parent
GLOBE = REPO / "api" / "globe.html"


def test_failed_attach_keeps_last_successful_session_url():
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

const context = vm.createContext({
  encodeURIComponent,
  fetch: async () => ({ ok: false, status: 404 }),
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
});
"""

    result = subprocess.run(
        ["node", "-e", script, str(GLOBE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
