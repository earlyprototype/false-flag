// Run: node tests/test_vr_client.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { spawnSync } = require("node:child_process");

const html = fs.readFileSync(path.join(__dirname, "../api/vr.html"), "utf8");
const script = html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, "The VR page must contain its client module");
const syntax = spawnSync(process.execPath, ["--input-type=module", "--check"], { input: script, encoding: "utf8" });
assert.equal(syntax.status, 0, syntax.stderr);
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
  history: { replaceState() {} },
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

// Keep the bounded copy of authored coordinates equal to the shipped globe.
const globeHtml = fs.readFileSync(path.join(__dirname, "../api/globe.html"), "utf8");
const gazetteer = globeHtml.match(/const GAZETTEER = (\{[\s\S]*?\n\});/)[1];
assert.equal(run("JSON.stringify(GAZETTEER)"), vm.runInNewContext(`JSON.stringify(${gazetteer})`));
assert.equal(run('placeFor("RAF-Marham").lat'), 52.65);
assert.equal(run('placeFor("classified")'), null);
assert.equal(run('placeFor("constructor")'), null, "Prototype names are not authored locations");

run('xrSession = null; document.hidden = false; snapshot = {turn: 2, phase: "discussion", forces: []}; globeFrameData = snapshot;');
assert.equal(run("showingGlobe()"), true);
assert.equal(run("showingGlobe({...snapshot, turn: 3})"), false, "Old globe pixels must not accompany a new snapshot");
run("selectGlobe(false)");
assert.equal(run("showingGlobe()"), false);
assert.equal(elements.get("view").dataset.screen, "board");
assert.equal(run('params.get("game")'), "review", "Source selection must preserve the campaign ID");
run("selectGlobe(true)");
assert.equal(run("showingGlobe()"), true);

run(`
  const failedGlobe = { resize() {}, render() { throw new Error("WebGL copy failed"); }, destroy() { this.destroyed = true; } };
  globe = failedGlobe; globeData = snapshot; renderGlobe(1000);
`);
assert.equal(run("failedGlobe.destroyed"), true);
assert.equal(run("globe"), null);
assert.equal(elements.get("view").dataset.screen, "board");
assert.match(elements.get("globeStatus").textContent, /WebGL copy failed/);
assert.equal(run("snapshot.turn"), 2, "A globe failure must retain the live campaign snapshot");
run('addCaption({content: "Still connected after globe failure", event_seq: 5});');
assert.equal(run("captions.at(-1).content"), "Still connected after globe failure");

// Replace GPU plotting only: execute the actual render/timeout branch with a pending new snapshot.
run(`
  globeError = null; globeData = null; globeWaitStart = 1;
  globe = { resize() {}, render() {}, destroy() {} };
  plotGlobe = data => { globeData = data; globeFrameData = null; };
  renderGlobe(20000);
`);
assert.equal(run("globeError"), null, "A new snapshot must receive its own frame timeout");
run("renderGlobe(35001)");
assert.match(run("globeError.message"), /15 seconds/);
assert.equal(elements.get("view").dataset.screen, "board");

console.log("VR client check passed: captions, XR visibility, globe source identity, fallback and timeout.");
