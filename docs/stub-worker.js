/* FALSE FLAG - offline stand-in for the engine worker.
 *
 * The real worker runs the Python engine under Pyodide. This one replays a
 * recorded campaign (docs/stub-data.js, captured from the game itself at
 * 78 columns against the mock LLM driver) so the page can be built, driven
 * and tested end to end without it. It speaks exactly the same message
 * contract, so swapping ?engine=stub for the real worker changes nothing on
 * the page side.
 *
 *   page -> worker : boot | newGame | decide | ask | call | endTurn
 *                    setKey | save | load
 *   worker -> page : booting | ready | output | state | awaiting
 *                    ending | error
 *
 * Everything it sends back is a recording. It does not read what you typed -
 * that is the whole point of the key prompt on the page.
 */
'use strict';

importScripts('stub-data.js', 'assets.js');

var D = self.FF_STUB_DATA;
var A = self.FF_ASSETS;
var WIDTH = 78;

var C = {
  muted: '\u001b[38;2;69;123;157m',
  normal: '\u001b[38;2;241;250;238m',
  amber: '\u001b[1;38;2;255;182;39m',
  accent: '\u001b[1;38;2;255;107;53m',
  teal: '\u001b[38;2;0;217;163m',
  red: '\u001b[1;38;2;255;59;48m',
  off: '\u001b[0m'
};

function send(msg) { self.postMessage(msg); }
function out(ansi) { send({ type: 'output', ansi: ansi }); }

function wrap(text, width) {
  var words = String(text).split(/\s+/).filter(Boolean);
  var lines = [], line = '';
  for (var i = 0; i < words.length; i++) {
    var w = words[i];
    if (!line.length) { line = w; continue; }
    if (line.length + 1 + w.length <= width) { line += ' ' + w; }
    else { lines.push(line); line = w; }
  }
  if (line.length) lines.push(line);
  return lines.length ? lines : [''];
}

function pad(s, n) { while (s.length < n) s += ' '; return s; }
function repeat(ch, n) { return n > 0 ? new Array(n + 1).join(ch) : ''; }

/* A rounded panel in the game's own shape: ╭─ TITLE ─╮ ... ╰─╯ */
function panel(title, body) {
  var inner = WIDTH - 4;
  var t = ' ' + title + ' ';
  var left = Math.floor((WIDTH - 2 - t.length) / 2);
  var right = WIDTH - 2 - t.length - left;
  var rows = [C.muted + '╭' + repeat('─', left) + C.off + C.amber + t +
              C.off + C.muted + repeat('─', right) + '╮' + C.off];
  wrap(body, inner).forEach(function (ln) {
    rows.push(C.muted + '│ ' + C.off + C.normal + pad(ln, inner) + C.off +
              C.muted + ' │' + C.off);
  });
  rows.push(C.muted + '╰' + repeat('─', WIDTH - 2) + '╯' + C.off);
  return rows.join('\n');
}

/* ──●──[ LABEL ]────────── , the game's phase rule. */
function rule(label) {
  var head = '──●──[ ' + label + ' ]';
  return '\n' + C.accent + head + C.off + C.muted +
         repeat('─', Math.max(2, WIDTH - head.length - 4)) + ' ·─·' + C.off + '\n';
}

// ---------------------------------------------------------------------------

var BOOT = [
  [4, 'fetching the runtime'],
  [18, 'unpacking python'],
  [34, 'loading pydantic'],
  [48, 'loading pyyaml'],
  [62, 'mounting /game'],
  [74, 'reading scenario: war game 2025'],
  [86, 'waking the cabinet'],
  [96, 'secure terminal ready']
];

var state = {
  turn: 0,
  metricsVisible: true,
  keySet: false,
  phase: 'idle',   // idle | decision | confirm | over
  onCall: null,    // country on the open line, if any
  timer: null
};

var METRICS = [
  { escalation_risk: 58, domestic_stability: 50, alliance_cohesion: 44,
    casualties_mil: 2, casualties_civ: 0 },
  { escalation_risk: 66, domestic_stability: 47, alliance_cohesion: 51,
    casualties_mil: 2, casualties_civ: 0 },
  { escalation_risk: 71, domestic_stability: 43, alliance_cohesion: 55,
    casualties_mil: 6, casualties_civ: 1 }
];

function pushState() {
  send({
    type: 'state',
    turn: state.turn,
    metricsVisible: state.metricsVisible,
    metrics: METRICS[Math.max(0, Math.min(state.turn - 1, METRICS.length - 1))]
  });
}

function awaiting(kind) {
  if (kind !== 'none') state.phase = kind;
  send({ type: 'awaiting', kind: kind });
}

/* Sequence a list of [delayMs, fn] steps; one timer at a time so a reset
   cannot leave two campaigns interleaving. */
function schedule(steps) {
  if (state.timer) { clearTimeout(state.timer); state.timer = null; }
  var i = 0;
  function next() {
    if (i >= steps.length) { state.timer = null; return; }
    var step = steps[i++];
    state.timer = setTimeout(function () { step[1](); next(); }, step[0]);
  }
  next();
}

function boot() {
  var steps = BOOT.map(function (b) {
    return [170, function () {
      send({ type: 'booting', pct: b[0], note: b[1] });
    }];
  });
  steps.push([200, function () {
    send({ type: 'booting', pct: 100, note: 'ready' });
    send({ type: 'ready' });
  }]);
  schedule(steps);
}

function newGame(config) {
  config = config || {};
  state.turn = 1;
  // Mirrors bridge.py's `metrics_visible()`, which is `play_mode == "classic"`
  // — not "anything but immersive". The page offers three modes, and in
  // `emergent` the real engine withholds the metrics. A stub that showed a
  // gauge there would misreport the very selector it exists to exercise, so
  // this must be kept in step with the engine, not merely with the default.
  state.metricsVisible = config.playMode === 'classic';
  schedule([
    [120, function () {
      if (!state.keySet) {
        out(C.muted + '── OFFLINE DEMONSTRATION ── no key set. The cabinet ' +
            'below is a recording;\n   it does not read what you type. ' +
            'Add an OpenRouter key to change that.' + C.off + '\n');
      }
      if (config.mysteryMode) {
        out(C.red + '── MYSTERY MODE ── a narrative has been drawn and sealed. ' +
            'You are not cleared for it.' + C.off + '\n');
      }
      out(D.briefings[0]);
    }],
    [80, function () { pushState(); awaiting('decision'); }]
  ]);
}

function decide(text) {
  if (state.phase === 'over') return;
  schedule([
    [60, function () { out(rule('DECISION · TURN ' + state.turn)); }],
    [60, function () { out(panel('YOUR DECISION', text) + '\n'); }],
    [260, function () {
      if (state.turn === 1) out(D.orderPanel + '\n');
      out('\n' + D.adjudication);
    }],
    [140, function () {
      state.turn += 1;
      pushState();
      if (state.turn > 2) {
        out('\n' + A.debrief + '\n');
        send({
          type: 'ending',
          verdict: 'MIXED',
          title: 'THE FOG HOLDS',
          debrief: 'The alliance stayed in one room and the deterrent stayed ' +
                   'in its tubes. Moscow now knows what Britain will do at sea ' +
                   'and what it will not. Nobody has yet found out who was ' +
                   'wearing whose face.\n\nThis was the offline demonstration: ' +
                   'a recording, not a reading of what you wrote. Add an ' +
                   'OpenRouter key and the advisors answer you directly.'
        });
        state.phase = 'over';
        awaiting('none');
      } else {
        out('\n' + D.turnEnd);
        awaiting('confirm');
      }
    }]
  ]);
}

function ask(advisor, text) {
  if (state.phase === 'over') return;
  schedule([
    [60, function () {
      out('\n' + C.accent + '>: ' + C.off + C.amber + text + C.off + '\n');
    }],
    [280, function () { out('\n' + D.answer + '\n'); awaiting('decision'); }]
  ]);
}

/* Mirrors the real worker: the first `call` opens the line and leaves the
   page in `awaiting: 'question'`; further `call` messages continue it until
   the player says 'end'. */
function call(country, text) {
  if (state.phase === 'over') return;
  var opening = !state.onCall;
  // A `call` with no text is legal — it is how the line is opened before
  // anything is said — and bridge.py tolerates it with `(text or "").strip()`.
  // Calling .trim() on undefined here threw, and the try/catch around the
  // dispatcher turned that into {fatal:true}, halting the page over an input
  // the engine accepts.
  var said = (text === null || text === undefined) ? '' : String(text).trim();
  var hangup = /^(end|thank you|goodbye)\b/i.test(said);
  state.onCall = country;
  schedule([
    [60, function () {
      if (opening) {
        out(rule('DIPLOMATIC CALL · ' + country));
        out(C.muted + '  Line open. Encryption green.' + C.off + '\n');
      }
      if (said) {
        out(C.accent + '  PRIME MINISTER  ' + C.off + '\n');
        wrap(said, 72).forEach(function (l) { out(C.amber + '    ' + l + C.off + '\n'); });
      }
    }],
    [320, function () {
      if (hangup) {
        out(C.muted + '  Line closed.' + C.off + '\n');
        state.onCall = null;
        awaiting('decision');
        return;
      }
      out('\n' + C.accent + '  ' + country + ' ── OFFICE OF THE HEAD OF GOVERNMENT' + C.off + '\n');
      out(C.normal +
          '    "We hear you, Prime Minister. We will not say publicly what we\n' +
          '    have just said privately, and you should plan on that."' + C.off + '\n');
      awaiting('question');
    }]
  ]);
}

function endTurn() {
  if (state.phase === 'over') return;
  schedule([
    [120, function () { out('\n' + D.briefings[1]); }],
    [80, function () { pushState(); awaiting('decision'); }]
  ]);
}

self.onmessage = function (ev) {
  var m = ev.data || {};
  try {
    switch (m.type) {
      case 'boot': boot(); break;
      case 'newGame': newGame(m.config); break;
      case 'decide': decide(m.text); break;
      case 'ask': ask(m.advisor, m.text); break;
      case 'call': call(m.country, m.text); break;
      case 'endTurn': endTurn(); break;
      case 'setKey':
        state.keySet = !!(m.key && String(m.key).length);
        out(C.muted + '── ' + (state.keySet
              ? 'API key accepted. Advisors will reason about what you write.'
              : 'Running without a key: canned responses only.') + C.off + '\n');
        break;
      case 'save':
        // Contract extension: the page downloads whatever `data` it is given
        // and hands it straight back on `load`.
        send({ type: 'saved',
               data: JSON.stringify({ stub: true, turn: state.turn }) });
        out(C.teal + '── Campaign saved.' + C.off + '\n');
        break;
      case 'load':
        try {
          var save = JSON.parse(m.data);
          state.turn = save.turn || 1;
          pushState();
          out(C.teal + '── Campaign restored at turn ' + state.turn + '.' + C.off + '\n');
          awaiting('decision');
        } catch (e) {
          send({ type: 'error', message: 'That file is not a FALSE FLAG save.',
                 fatal: false });
        }
        break;
      default:
        send({ type: 'error', message: 'Unknown command: ' + m.type,
               fatal: false });
    }
  } catch (err) {
    send({ type: 'error', message: String(err && err.message || err),
           fatal: true });
  }
};
