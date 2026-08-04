/* FALSE FLAG - the playable page.
 *
 * Everything here is UI. The game itself lives in a Web Worker; this file
 * only speaks to it, and the message contract is fixed:
 *
 *   page -> worker : {type:'boot'}
 *                    {type:'newGame', config:{scenario, playMode, mysteryMode, seed}}
 *                    {type:'decide', text}
 *                    {type:'ask', advisor, text}
 *                    {type:'call', country, text}
 *                    {type:'endTurn'}
 *                    {type:'setKey', key}        // '' or null -> mock driver
 *                    {type:'save'} / {type:'load', data}
 *
 *   worker -> page : {type:'booting', pct, note}
 *                    {type:'ready'}
 *                    {type:'output', ansi}       // raw ANSI, rendered here
 *                    {type:'state', turn, metricsVisible, metrics}
 *                    {type:'awaiting', kind}     // decision|question|confirm|none
 *                    {type:'ending', verdict, title, debrief}
 *                    {type:'error', message, fatal}
 *
 * Two things are handled beyond that list, both additive:
 *   - {type:'saved', data} - the reply to a save request. The contract names
 *     the request but not where the bytes come back; if no worker ever sends
 *     it, Save simply asks and nothing else happens.
 *   - extra keys on `state` (finalTurn, advisors, contacts). When the engine
 *     sends who is in the room and which capitals are reachable, the pickers
 *     follow it; otherwise the markup's defaults stand.
 */
(function () {
  'use strict';

  // The Pyodide engine worker. A list, because the page does not care what
  // the file is called - only that it speaks the contract - and probing lets
  // this page be driven before the worker exists.
  var REAL_WORKER = ['worker.js'];
  var STUB_WORKER = 'stub-worker.js';
  var KEY_STORE = 'falseflag.openrouter.key';
  var WIDTH_STORE = 'falseflag.width';
  var COLS = 78;              // the game's own layout width
  var MAX_NODES = 2400;       // transcript trim point

  var $ = function (id) { return document.getElementById(id); };
  var el = {};
  [
    'gate', 'stage', 'apikey', 'remember', 'useKey', 'keystate',
    'sharedPanel', 'sharedPass', 'unlockShared', 'sharedState', 'startShared',
    'scenario', 'playMode', 'mysteryMode', 'seed', 'startNoKey', 'startWithKey',
    'screen', 'metrics', 'termTitle', 'termRef', 'widthToggle',
    'awaiting', 'awaitingTag', 'awaitingWhat', 'controls',
    'decideText', 'sendDecide', 'endTurn', 'advisor', 'askText', 'sendAsk',
    'country', 'callText', 'sendCall', 'saveGame', 'loadGame', 'loadFile',
    'abandon', 'alerts', 'endingSlot', 'stageTitle'
  ].forEach(function (id) { el[id] = $(id); });

  var A = window.FF_ASSETS || {};
  var ansi = new window.AnsiRenderer();

  var ui = {
    apiKey: null,        // in memory only unless "remember" was ticked
    sharedBlob: null,    // the published ciphertext, if this deploy has one
    sharedKey: null,     // decrypted owner's key — MEMORY ONLY, never stored
    booted: false,
    bootBuf: null,       // the boot frame, replaced in place until ready
    fatal: false,
    over: false,
    awaiting: 'none',
    busy: false,
    fit: true,
    perChar: null        // px of advance per px of font-size, measured once
  };

  // ------------------------------------------------------------- terminal

  function atBottom() {
    var s = el.screen;
    return s.scrollHeight - s.scrollTop - s.clientHeight < 48;
  }

  function scrollDown() { el.screen.scrollTop = el.screen.scrollHeight; }

  /** Append raw ANSI to the transcript, keeping the view pinned if it was. */
  function write(text) {
    var stick = atBottom();
    var frag = document.createElement('span');
    frag.innerHTML = ansi.render(text);
    el.screen.appendChild(frag);
    while (el.screen.childNodes.length > MAX_NODES) {
      el.screen.removeChild(el.screen.firstChild);
    }
    if (stick) scrollDown();
  }

  /** Replace the whole pane (used only while booting). */
  function paint(text) {
    el.screen.innerHTML = ansi.render(text);
    scrollDown();
  }

  /* Fit the 78-column layout to the pane. Box drawing only survives if a
     whole row fits, so the alternative to shrinking is sideways scrolling -
     which the WIDTH toggle offers for anyone who would rather read. */
  function measurePerChar() {
    if (ui.perChar) return ui.perChar;
    var probe = document.createElement('span');
    probe.style.cssText = 'position:absolute;visibility:hidden;white-space:pre;' +
      'font-size:100px;line-height:1;font-family:' +
      getComputedStyle(el.screen).fontFamily;
    probe.textContent = new Array(COLS + 1).join('M');
    document.body.appendChild(probe);
    ui.perChar = probe.getBoundingClientRect().width / COLS / 100;
    document.body.removeChild(probe);
    return ui.perChar;
  }

  function refit() {
    if (!ui.fit) {
      el.screen.classList.add('read');
      el.screen.style.removeProperty('font-size');
      return;
    }
    el.screen.classList.remove('read');
    var cs = getComputedStyle(el.screen);
    var avail = el.screen.clientWidth -
      parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    if (avail <= 0) return;
    // Half a column of headroom: with soft wrapping on, a 78-column box row
    // that is one sub-pixel too wide would fold in half.
    var size = avail / ((COLS + 0.5) * measurePerChar());
    size = Math.max(5.5, Math.min(14, size));
    el.screen.style.fontSize = size.toFixed(2) + 'px';
  }

  function setWidthMode(fit, remember) {
    ui.fit = !!fit;
    el.widthToggle.textContent = 'WIDTH: ' + (ui.fit ? 'FIT' : 'READ');
    el.widthToggle.setAttribute('aria-pressed', String(!ui.fit));
    el.widthToggle.title = ui.fit
      ? 'Showing all 78 columns. Tap for a larger, legible size that scrolls sideways.'
      : 'Legible size; the pane scrolls sideways. Tap to fit all 78 columns.';
    if (remember) {
      try { localStorage.setItem(WIDTH_STORE, ui.fit ? 'fit' : 'read'); }
      catch (e) { /* private mode */ }
    }
    refit();
  }

  el.widthToggle.addEventListener('click', function () {
    setWidthMode(!ui.fit, true);
  });
  window.addEventListener('resize', refit);
  window.addEventListener('orientationchange', function () {
    setTimeout(refit, 120);
  });

  // ----------------------------------------------------------- boot frame

  var C = {
    muted: '\u001b[38;2;69;123;157m',
    normal: '\u001b[38;2;241;250;238m',
    amber: '\u001b[1;38;2;255;182;39m',
    accent: '\u001b[1;38;2;255;107;53m',
    teal: '\u001b[38;2;0;217;163m',
    off: '\u001b[0m'
  };

  var bootLines = [];

  function bootFrame(pct, note) {
    var rows = [];
    if (A.strip) rows.push(A.strip);
    rows.push('');
    rows.push(C.accent + 'SECURE TERMINAL ── OPERATION TUMAN' + C.off);
    bootLines.forEach(function (l, i) {
      var done = i < bootLines.length - 1 || pct >= 100;
      var label = l.toUpperCase();
      var status = done ? 'OK' : '··';
      var dots = Math.max(2, COLS - label.length - status.length - 8);
      rows.push(C.muted + '> ' + C.off + C.normal + label + C.off +
                C.muted + ' ' + new Array(dots + 1).join('·') + ' ' + C.off +
                (done ? C.teal : C.muted) + status + C.off);
    });
    rows.push('');
    var filled = Math.round(Math.max(0, Math.min(100, pct)) / 100 * 46);
    rows.push(C.muted + '  [' + C.off + C.accent +
              new Array(filled + 1).join('█') + C.off + C.muted +
              new Array(46 - filled + 1).join('░') + ']' + C.off +
              C.amber + '  ' + String(Math.round(pct)) + '%' + C.off);
    rows.push('');
    if (A.fog && A.fog.length) {
      var idx = Math.min(A.fog.length - 1,
                         Math.floor(pct / 100 * A.fog.length));
      rows.push(A.fog[idx]);
    }
    return rows.join('\n');
  }

  function onBooting(pct, note) {
    if (note && bootLines[bootLines.length - 1] !== note) bootLines.push(note);
    ui.bootBuf = bootFrame(pct, note);
    paint(ui.bootBuf);
    setAwaiting('booting', 'BOOTING', 'Loading the engine — ' +
      (note || '') + ' (' + Math.round(pct) + '%)');
  }

  function onReady() {
    ui.booted = true;
    el.screen.innerHTML = '';
    ansi.reset();
    if (ui.bootBuf) write(ui.bootBuf + '\n');
    if (A.masthead) write('\n' + A.masthead + '\n');
    el.controls.hidden = false;
    send({ type: 'setKey', key: ui.keyForRun || '' });
    send({ type: 'newGame', config: campaignConfig() });
  }

  // --------------------------------------------------------------- status

  /* The four `awaiting` kinds, in the engine's own words:
       'decision' the turn is open - decide, ask and call are all legal
       'question' a diplomatic call is live; the next `call` continues it,
                  and 'end' hangs up
       'confirm'  the decision resolved; `endTurn` advances
       'none'     busy, booting, or the campaign is over - block input     */
  var AWAIT_COPY = {
    decision: ['AWAITING DECISION',
      'COBRA is waiting on you. Write what you are doing — a paragraph, in ' +
      'your own words. You can ask the room first; it costs nothing but time.'],
    question: ['LINE OPEN',
      'The call is still connected. Say the next thing, or send “end” to hang ' +
      'up and get back to the room.'],
    confirm: ['AWAITING ACKNOWLEDGEMENT',
      'The turn is resolved. Read it, then continue when you are ready.'],
    none: ['STANDBY', 'Nothing is expected from you right now.'],
    booting: ['BOOTING', 'Loading the engine.'],
    busy: ['WORKING', 'Sent. The room is thinking.'],
    over: ['CAMPAIGN OVER', 'The campaign has reached an ending.']
  };

  function setAwaiting(kind, tag, what) {
    var copy = AWAIT_COPY[kind] || AWAIT_COPY.none;
    el.awaitingTag.textContent = tag || copy[0];
    el.awaitingWhat.textContent = what || copy[1];
    el.awaiting.classList.toggle('busy', kind === 'busy' || kind === 'booting');
    el.awaiting.classList.toggle('over', kind === 'over');
  }

  function applyAwaiting(kind) {
    ui.awaiting = kind;
    ui.busy = false;
    if (ui.over) { setAwaiting('over'); return; }
    setAwaiting(kind);

    var live = kind === 'question';   // a call is in progress
    var open = kind === 'decision';
    var usable = !ui.fatal && !ui.over;

    el.sendDecide.disabled = !(usable && open);
    el.sendAsk.disabled = !(usable && open);
    el.sendCall.disabled = !(usable && (open || live));
    el.endTurn.hidden = kind !== 'confirm';
    el.endTurn.disabled = ui.fatal;

    el.country.disabled = live;       // you cannot redial mid-call
    el.sendCall.textContent = live ? 'Say it' : 'Place the call';
    var callLabel = document.querySelector('label[for="callText"]');
    if (callLabel) {
      callLabel.textContent = live
        ? 'THE LINE IS OPEN ── WHAT YOU SAY NEXT (“end” HANGS UP)'
        : 'WHAT YOU SAY ON THE LINE';
    }

    if (live) { selectTab('call'); el.callText.focus(); }
    if (kind === 'confirm') selectTab('decide');
  }

  function markBusy() {
    ui.busy = true;
    setAwaiting('busy');
    el.sendDecide.disabled = true;
    el.sendAsk.disabled = true;
    el.sendCall.disabled = true;
    el.endTurn.disabled = true;
  }

  function humanise(key) {
    return key.replace(/_/g, ' ').toUpperCase();
  }

  /* The engine may also send who is actually in the room and which capitals
     the current alliance standing has open. When it does, the pickers follow
     it rather than a hard-coded list; when it does not, the markup's defaults
     stand. `value` is preserved across a refresh so a live call is not
     silently redialled. */
  function repopulate(select, rows, valueKey, labelKeys) {
    if (!Array.isArray(rows) || !rows.length) return;
    var want = select.value;
    var built = rows.map(function (r) {
      if (typeof r === 'string') return { v: r, t: r };
      var label = null;
      for (var i = 0; i < labelKeys.length && !label; i++) label = r[labelKeys[i]];
      return { v: r[valueKey], t: label || r[valueKey] };
    }).filter(function (o) { return o.v; });
    var same = built.length === select.options.length &&
      built.every(function (o, i) { return select.options[i].value === o.v; });
    if (same) return;
    select.innerHTML = '';
    built.forEach(function (o) {
      var opt = document.createElement('option');
      opt.value = o.v;
      opt.textContent = o.t;
      select.appendChild(opt);
    });
    if (built.some(function (o) { return o.v === want; })) select.value = want;
  }

  function renderMetrics(turn, visible, metrics, extra) {
    extra = extra || {};
    var ref = 'TURN ' + (turn || '—');
    if (extra.finalTurn) ref += ' / ' + extra.finalTurn;
    el.termRef.textContent = ref;
    repopulate(el.advisor, extra.advisors, 'id', ['label', 'name']);
    repopulate(el.country, extra.contacts, 'code', ['title', 'name']);
    el.metrics.innerHTML = '';
    if (!visible) {
      var s = document.createElement('span');
      s.className = 'sealed';
      s.textContent = '── METRICS WITHHELD IN THIS MODE ──';
      el.metrics.appendChild(s);
      return;
    }
    if (!metrics || typeof metrics !== 'object') return;
    Object.keys(metrics).forEach(function (k) {
      var v = metrics[k];
      if (typeof v !== 'number' || !isFinite(v)) return;
      var wrap = document.createElement('span');
      wrap.className = 'm';
      var name = document.createElement('span');
      name.className = 'k';
      name.textContent = humanise(k);
      wrap.appendChild(name);
      // 0-100 reads as a gauge; anything else (casualty counts) is a number.
      if (v >= 0 && v <= 100 && /risk|stability|cohesion|support|unity/.test(k)) {
        var filled = Math.round(v / 100 * 10);
        var bar = document.createElement('span');
        bar.className = 'bar';
        bar.textContent = new Array(filled + 1).join('█') +
                          new Array(10 - filled + 1).join('░');
        wrap.appendChild(bar);
      }
      var val = document.createElement('span');
      val.className = 'v';
      val.textContent = String(v);
      wrap.appendChild(val);
      el.metrics.appendChild(wrap);
    });
  }

  function notify(message, fatal) {
    var box = document.createElement('div');
    box.className = 'alert';
    var b = document.createElement('b');
    b.textContent = fatal ? 'FAULT ── ' : 'NOTICE ── ';
    box.appendChild(b);
    box.appendChild(document.createTextNode(message));
    el.alerts.appendChild(box);
  }

  function showEnding(verdict, title, debrief) {
    ui.over = true;
    var box = document.createElement('div');
    box.className = 'ending';
    var v = document.createElement('div');
    v.className = 'verdict';
    v.textContent = '── AFTER ACTION ── VERDICT: ' + String(verdict || '').toUpperCase();
    var h = document.createElement('h2');
    h.textContent = title || 'CAMPAIGN ENDED';
    var p = document.createElement('p');
    p.textContent = debrief || '';
    var again = document.createElement('button');
    again.className = 'primary';
    again.textContent = 'Start a new campaign';
    again.addEventListener('click', function () { location.reload(); });
    box.appendChild(v); box.appendChild(h); box.appendChild(p); box.appendChild(again);
    el.endingSlot.appendChild(box);
    setAwaiting('over');
    el.sendDecide.disabled = true;
    el.sendAsk.disabled = true;
    el.sendCall.disabled = true;
    el.endTurn.hidden = true;
    box.scrollIntoView({ block: 'nearest' });
  }

  // --------------------------------------------------------------- worker

  var worker = null;
  var workerName = '';

  function send(msg) {
    if (!worker) return;
    try { worker.postMessage(msg); }
    catch (e) { notify('Could not reach the engine: ' + e.message, true); }
  }

  /* The engine worker downloads a Python runtime before it can say anything.
     If that stalls - slow link, blocked CDN - a page that only ever says
     BOOTING is lying by omission, so say so out loud. */
  function watchBoot() {
    var last = Date.now();
    var warned = false;
    ui.touch = function () { last = Date.now(); };
    var tick = setInterval(function () {
      if (ui.booted || ui.fatal) { clearInterval(tick); return; }
      if (!warned && Date.now() - last > 45000) {
        warned = true;
        notify('The engine has not reported progress for 45 seconds. It is ' +
               'fetching a Python runtime, which is a large download on a ' +
               'slow connection — give it a little longer, or reload with ' +
               '?engine=stub to play the offline demonstration instead.',
               false);
      }
    }, 5000);
  }

  function attach(url, isFallback) {
    worker = new Worker(url);
    workerName = url;
    watchBoot();
    worker.onmessage = function (ev) {
      var m = ev.data || {};
      if (ui.touch) ui.touch();
      switch (m.type) {
        case 'booting': onBooting(m.pct || 0, m.note); break;
        case 'ready':
          onReady();
          if (isFallback) {
            write(C.muted + '── Running the offline demonstration: the engine ' +
                  'worker was not available,\n   so this is a recorded ' +
                  'campaign.' + C.off + '\n');
          }
          break;
        case 'output': write(m.ansi); break;
        case 'state': renderMetrics(m.turn, m.metricsVisible !== false, m.metrics, m); break;
        case 'awaiting': applyAwaiting(m.kind || 'none'); break;
        case 'ending': showEnding(m.verdict, m.title, m.debrief); break;
        case 'error':
          notify(m.message || 'Unknown engine error', !!m.fatal);
          if (m.fatal) {
            ui.fatal = true;
            setAwaiting('over', 'HALTED', 'The engine stopped. Reload to try again.');
            el.sendDecide.disabled = true;
            el.sendAsk.disabled = true;
            el.sendCall.disabled = true;
            el.endTurn.disabled = true;
          } else if (ui.busy) {
            applyAwaiting(ui.awaiting);
          }
          break;
        case 'saved': offerDownload(m.data); break;
        default: break;
      }
    };
    worker.onerror = function (e) {
      e.preventDefault();
      notify('The engine worker failed: ' + (e.message || 'unknown error') +
             (ui.booted ? '' : ' — reload with ?engine=stub to play the ' +
                               'offline demonstration instead.'), true);
      ui.fatal = true;
      setAwaiting('over', 'HALTED', 'The engine stopped.');
    };
    send({ type: 'boot' });
  }

  /* Which worker?
       ?engine=stub    the recorded demonstration, always
       ?engine=real    the first real worker name, and an honest failure if
                       it is not there
       ?engine=foo.js  a specific same-directory worker file
       (nothing)       the first real worker that exists, else the stub.

     The last case is what lets this page be built and driven while the engine
     worker is written alongside it. When neither name exists the browser logs
     one 404 per probe; that stops as soon as the real worker lands. */
  function chooseWorker() {
    var want = new URLSearchParams(location.search).get('engine');
    if (want === 'stub') { attach(STUB_WORKER, false); return; }
    if (want && want !== 'real' && /^[\w.-]+\.js$/.test(want)) {
      attach(want, false);
      return;
    }
    if (want === 'real') { attach(REAL_WORKER[0], false); return; }
    var i = 0;
    (function probe() {
      if (i >= REAL_WORKER.length) { attach(STUB_WORKER, true); return; }
      var name = REAL_WORKER[i++];
      fetch(name, { method: 'GET', cache: 'no-store' })
        .then(function (r) { if (r.ok) attach(name, false); else probe(); })
        .catch(probe);
    })();
  }

  // ------------------------------------------------------------ save/load

  function offerDownload(data) {
    if (typeof data !== 'string' || !data.length) {
      notify('The engine returned an empty save.', false);
      return;
    }
    var blob = new Blob([data], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'false-flag-save.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  el.saveGame.addEventListener('click', function () { send({ type: 'save' }); });
  el.loadGame.addEventListener('click', function () { el.loadFile.click(); });
  el.loadFile.addEventListener('change', function () {
    var f = el.loadFile.files && el.loadFile.files[0];
    if (!f) return;
    var reader = new FileReader();
    reader.onload = function () { send({ type: 'load', data: String(reader.result) }); };
    reader.onerror = function () { notify('Could not read that file.', false); };
    reader.readAsText(f);
    el.loadFile.value = '';
  });

  el.abandon.addEventListener('click', function () {
    if (window.confirm('Abandon this campaign and go back to the setup screen?')) {
      location.reload();
    }
  });

  // ------------------------------------------------------------------ key

  /* The key is never shown back in full - not here, not in the field, not
     anywhere in the DOM. Short strings are masked entirely rather than
     accidentally displayed whole. */
  function maskKey(key) {
    if (!key) return '';
    var head = key.length >= 16 ? key.slice(0, 8) : '••••••••';
    var tail = key.length >= 12 ? key.slice(-4) : '••••';
    return head + '…' + tail;
  }

  /* Which start buttons exist, and which one is the obvious one to press.
     Your own key wins over the shared key when you have set both; the shared
     key wins over nothing. Only ever one primary. */
  function refreshStart() {
    var own = !!ui.apiKey;
    var shared = !!(el.startShared && ui.sharedKey);
    el.startWithKey.hidden = !own;
    if (el.startShared) el.startShared.hidden = !shared;

    el.startNoKey.textContent = (own || shared)
      ? 'Play without using it' : 'Play without a key';
    el.startNoKey.classList.toggle('primary', !own && !shared);
    el.startWithKey.classList.toggle('primary', own);
    if (el.startShared) el.startShared.classList.toggle('primary', shared && !own);
  }

  function showKeyState() {
    if (ui.apiKey) {
      el.keystate.innerHTML = '';
      el.keystate.appendChild(document.createTextNode('Key set: '));
      var b = document.createElement('b');
      b.textContent = maskKey(ui.apiKey);
      el.keystate.appendChild(b);
      el.keystate.appendChild(document.createTextNode(
        ' — advisors will reason about what you write. '));
      var drop = document.createElement('a');
      drop.href = '#';
      drop.textContent = 'Forget it';
      drop.addEventListener('click', function (e) {
        e.preventDefault();
        clearKey();
      });
      el.keystate.appendChild(drop);
    } else {
      el.keystate.textContent = 'No key set — the advisors will use the offline stand-in.';
    }
    refreshStart();
  }

  function clearKey() {
    ui.apiKey = null;
    try { localStorage.removeItem(KEY_STORE); } catch (e) { /* private mode */ }
    el.apikey.value = '';
    el.remember.checked = false;
    showKeyState();
  }

  el.useKey.addEventListener('click', function () {
    var v = el.apikey.value.trim();
    if (!v) { clearKey(); return; }
    ui.apiKey = v;
    // The field never shows the key again, here or anywhere else on the page.
    el.apikey.value = '';
    if (el.remember.checked) {
      try { localStorage.setItem(KEY_STORE, v); }
      catch (e) { notify('This browser refused to store the key; it will be ' +
                        'kept in memory for this tab only.', false); }
    } else {
      try { localStorage.removeItem(KEY_STORE); } catch (e) { /* ignore */ }
    }
    showKeyState();
  });

  el.apikey.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); el.useKey.click(); }
  });

  (function restoreKey() {
    var stored = null;
    try { stored = localStorage.getItem(KEY_STORE); } catch (e) { /* ignore */ }
    if (stored) { ui.apiKey = stored; el.remember.checked = true; }
    showKeyState();
  })();

  // ----------------------------------------------------------- shared key
  /* A deploy may ship the owner's OpenRouter key encrypted under a passphrase
   * he hands out separately (see dev-scripts/encrypt-key.html and the README).
   * The page is static — GitHub Pages has no server and can keep no secret —
   * so the only honest way to do this is to publish ciphertext and let the
   * passphrase, which is never published, be the thing that opens it.
   *
   *   PBKDF2-HMAC-SHA256(passphrase, salt, iterations) -> AES-256-GCM key
   *
   * A wrong passphrase derives a different AES key, the GCM tag does not
   * verify, and subtle.decrypt rejects. That rejection is the *only* check:
   * there is no verifier field, no plaintext canary and no format assertion
   * on the result, because any of those would answer questions an attacker
   * with the public blob is entitled to no answer to. All this page ever says
   * is that the passphrase did not work.
   *
   * The recovered key is held in `ui.sharedKey` and passed to the worker.
   * It is never written to localStorage or sessionStorage, never rendered
   * into the DOM (not even masked, unlike your own key), and never logged.
   * Closing the tab is the end of it.
   */
  var SHARED_BLOB = 'shared-key.json';
  var SHARED_MIN_ITERS = 100000;      // refuse a blob weakened below this
  var SHARED_MAX_ITERS = 10000000;    // and one that would wedge the tab

  function fromB64(s) {
    var bin = atob(s);
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function wellFormedBlob(j) {
    return !!j && j.v === 1 && j.kdf === 'PBKDF2-SHA256' &&
      typeof j.salt === 'string' && typeof j.iv === 'string' &&
      typeof j.ct === 'string' && j.ct.length > 0 &&
      typeof j.iterations === 'number' && isFinite(j.iterations) &&
      j.iterations >= SHARED_MIN_ITERS && j.iterations <= SHARED_MAX_ITERS;
  }

  function unsealShared(blob, pass) {
    var subtle = window.crypto && window.crypto.subtle;
    if (!subtle) return Promise.reject(new Error('no WebCrypto'));
    return subtle.importKey(
      'raw', new TextEncoder().encode(String(pass).normalize('NFKC')),
      'PBKDF2', false, ['deriveKey']
    ).then(function (base) {
      return subtle.deriveKey(
        { name: 'PBKDF2', salt: fromB64(blob.salt),
          iterations: blob.iterations, hash: 'SHA-256' },
        base, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
    }).then(function (key) {
      return subtle.decrypt(
        { name: 'AES-GCM', iv: fromB64(blob.iv), tagLength: 128 },
        key, fromB64(blob.ct));
    }).then(function (plain) {
      return new TextDecoder().decode(plain);
    });
  }

  function setSharedState(text, tone) {
    if (!el.sharedState) return;
    el.sharedState.textContent = text;
    el.sharedState.style.color = tone === 'bad' ? 'var(--red)'
      : tone === 'work' ? 'var(--dim)' : '';
  }

  /* Probe for the blob. No file, a 404, or anything that is not a blob of the
     shape above, and the option is never offered at all — which is what most
     forks of this repository will see. */
  (function probeShared() {
    if (!el.sharedPanel || !(window.crypto && window.crypto.subtle)) return;
    fetch(SHARED_BLOB, { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!wellFormedBlob(j)) return;
        ui.sharedBlob = j;
        el.sharedPanel.hidden = false;
      })
      .catch(function () { /* no shared key here; nothing to offer */ });
  })();

  function unlockShared() {
    var pass = el.sharedPass.value;
    if (!ui.sharedBlob || !pass) { el.sharedPass.focus(); return; }
    var button = el.unlockShared;
    var label = button.textContent;
    button.disabled = true;
    button.textContent = 'Working…';
    setSharedState('Working — the key stretching is slow on purpose.', 'work');
    unsealShared(ui.sharedBlob, pass).then(function (key) {
      if (!key) throw new Error('empty');
      ui.sharedKey = key;
      el.sharedPass.value = '';
      el.sharedPass.disabled = true;
      button.hidden = true;
      setSharedState('Unlocked. The key is in memory for this tab only — ' +
                     'it is not stored anywhere and reloading loses it.');
      refreshStart();
    }).catch(function () {
      // Deliberately the same, uninformative sentence for every failure.
      ui.sharedKey = null;
      setSharedState('That passphrase did not work.', 'bad');
      refreshStart();
    }).then(function () {
      if (!button.hidden) {
        button.disabled = false;
        button.textContent = label;
      }
    });
  }

  if (el.unlockShared) {
    el.unlockShared.addEventListener('click', unlockShared);
    el.sharedPass.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); unlockShared(); }
    });
  }

  // -------------------------------------------------------------- startup

  function campaignConfig() {
    var seed = parseInt(el.seed.value, 10);
    return {
      scenario: el.scenario.value,
      playMode: el.playMode.value,
      mysteryMode: el.mysteryMode.value === '1',
      seed: isFinite(seed) ? seed : 42
    };
  }

  /* `source` is 'own' (the key you pasted), 'shared' (the owner's key, if you
     unlocked it) or 'none' (the offline stand-in). */
  function beginCampaign(source) {
    // "Play without using it" leaves a stored key alone; it just is not sent
    // to the engine for this campaign.
    ui.keyForRun = source === 'own' ? (ui.apiKey || '')
      : source === 'shared' ? (ui.sharedKey || '')
      : '';
    el.gate.hidden = true;
    el.stage.hidden = false;
    el.stageTitle.textContent = 'PLAY ── ' +
      (el.mysteryMode.value === '1' ? 'NARRATIVE SEALED' : 'OPERATION TUMAN');
    el.termTitle.textContent = 'CABINET OFFICE BRIEFING ROOM A';
    var stored = null;
    try { stored = localStorage.getItem(WIDTH_STORE); } catch (e) { /* ignore */ }
    setWidthMode(stored !== 'read', false);
    setAwaiting('booting');
    chooseWorker();
    el.screen.focus();
  }

  el.startNoKey.addEventListener('click', function () { beginCampaign('none'); });
  el.startWithKey.addEventListener('click', function () { beginCampaign('own'); });
  if (el.startShared) {
    el.startShared.addEventListener('click', function () { beginCampaign('shared'); });
  }

  // ----------------------------------------------------------------- tabs

  var TABS = ['decide', 'ask', 'call'];
  function selectTab(name) {
    TABS.forEach(function (t) {
      var tab = $('tab-' + t), panel = $('panel-' + t);
      var on = t === name;
      tab.setAttribute('aria-selected', String(on));
      panel.hidden = !on;
    });
  }
  TABS.forEach(function (t) {
    $('tab-' + t).addEventListener('click', function () { selectTab(t); });
  });

  function submitDecision() {
    var text = el.decideText.value.trim();
    if (!text) { el.decideText.focus(); return; }
    markBusy();
    send({ type: 'decide', text: text });
    el.decideText.value = '';
  }

  el.sendDecide.addEventListener('click', submitDecision);

  /* Ctrl/Cmd+Enter sends from any of the three boxes. Plain Enter must stay a
     newline - the whole point is that you write a paragraph. */
  function sendOnCtrlEnter(box, button) {
    box.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!button.disabled) button.click();
      }
    });
  }
  sendOnCtrlEnter(el.decideText, el.sendDecide);
  sendOnCtrlEnter(el.askText, el.sendAsk);
  sendOnCtrlEnter(el.callText, el.sendCall);

  el.sendAsk.addEventListener('click', function () {
    var text = el.askText.value.trim();
    if (!text) { el.askText.focus(); return; }
    markBusy();
    send({ type: 'ask', advisor: el.advisor.value, text: text });
    el.askText.value = '';
  });

  el.sendCall.addEventListener('click', function () {
    var text = el.callText.value.trim();
    if (!text) { el.callText.focus(); return; }
    markBusy();
    send({ type: 'call', country: el.country.value, text: text });
    el.callText.value = '';
  });

  el.endTurn.addEventListener('click', function () {
    markBusy();
    send({ type: 'endTurn' });
  });

  // Expose a little state for automated driving of the page. Booleans and
  // screen text only — no key material, of either kind, ever leaves here.
  window.FF_PLAY = {
    get worker() { return workerName; },
    get awaiting() { return ui.awaiting; },
    get booted() { return ui.booted; },
    get over() { return ui.over; },
    get sharedOffered() { return !!ui.sharedBlob; },
    get sharedUnlocked() { return !!ui.sharedKey; },
    text: function () { return el.screen.textContent; }
  };
})();
