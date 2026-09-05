// Run: node tests/test_vr_client.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname, "../api/vr.html"), "utf8");
const script = html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, "The VR page must contain its client module");
const bootstrap = script.indexOf("\nif (validId) {");
assert.ok(bootstrap > 0, "Stop before network and Three.js startup");

const timers = new Map();
let timerId = 0;
const ink = {
  measureText: text => ({ width: text.length * 18 }),
  fillRect() {}, fillText() {}, drawImage() {}
};
const element = () => ({
  dataset: {}, getContext: () => ink,
  append() {}, addEventListener() {}, setAttribute() {}
});
const elements = new Map();
const context = vm.createContext({
  URLSearchParams,
  location: { search: "?game=review", pathname: "/vr" },
  document: {
    hidden: false,
    createElement: element,
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    },
    addEventListener() {}
  },
  window: { addEventListener() {} },
  setTimeout(callback) { timers.set(++timerId, callback); return timerId; },
  clearTimeout(id) { timers.delete(id); },
  setInterval() {}
});
const run = code => vm.runInContext(code, context, { filename: "api/vr.html" });
run('"use strict";\n' + script.slice(0, bootstrap));

function tickCaption() {
  assert.equal(timers.size, 1, "Exactly one caption timer should be armed");
  const [id, callback] = timers.entries().next().value;
  timers.delete(id);
  callback();
}

run('addCaption({content: "First", event_seq: 1}); addCaption({content: "Second", event_seq: 2});');
tickCaption();
assert.equal(run("captions[captionIndex].content"), "Second");
tickCaption();
assert.equal(timers.size, 0, "Reading the final caption should finish the timer");
elements.get("captionPrev").onclick();
run('addCaption({content: "Third", event_seq: 3});');
assert.equal(run("captions[captionIndex].content"), "First", "An arriving caption must not interrupt back-navigation");
assert.equal(timers.size, 1, "Back-navigation should restart automatic paging");

run('xrSession = {visibilityState: "hidden"}; armCaptionTimer();');
assert.equal(timers.size, 0, "Hidden XR must stop paging even when the document is visible");
elements.get("captionLatest").onclick();
assert.equal(timers.size, 0, "Selecting a caption must not restart hidden XR paging");
run('xrSession.visibilityState = "visible"; armCaptionTimer();');
tickCaption();
run('xrSession.visibilityState = "hidden"; addCaption({content: "Fourth", event_seq: 4});');
assert.equal(timers.size, 0, "Arriving captions must not restart hidden XR paging");
run('xrSession.visibilityState = "visible"; document.hidden = true; armCaptionTimer();');
assert.equal(timers.size, 1, "Visible XR must keep paging when the document is hidden");
run('xrSession.visibilityState = "visible-blurred"; armCaptionTimer();');
assert.equal(timers.size, 0, "Blurred XR must stop paging");
run("xrSession = null; armCaptionTimer();");
assert.equal(timers.size, 0, "A hidden desktop page must stop paging after XR ends");

console.log("VR client check passed: caption navigation and XR visibility.");
