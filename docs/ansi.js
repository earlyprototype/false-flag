/* FALSE FLAG - live ANSI to HTML, in the browser.
 *
 * The engine emits real terminal output: truecolor SGR, the sixteen named
 * ANSI colours, 256-colour indices, and a great deal of box drawing. This is
 * the renderer that turns that into HTML, live, as a turn is computed.
 *
 * Two things it is careful about:
 *
 *  - The Tuman palette. A terminal emulator's default sixteen render almost
 *    black on this ground, so PALETTE below maps them onto the game's own
 *    colours (cli/theme.py's `defcon`) — which is why `bold red` comes back
 *    as Operation Tuman orange. docs/play.css takes its page-chrome tokens
 *    from this same table, so the pane and the page around it agree.
 *  - One shared class map. Every distinct style becomes a `.tN` rule in a
 *    single stylesheet instead of an inline `style=` attribute, so a long
 *    transcript stays small and the DOM stays cheap to append to.
 *
 * Bold does not brighten the colour (Rich does not, and the game's captures
 * rely on `bold red` staying red). Cursor movement, erase and OSC sequences
 * are dropped: this pane is a scrolling transcript, not an addressable
 * screen.
 *
 * On SGR 7 (reverse) with no colour set this swaps in the ground colour,
 * which is what a terminal does. The game emits no SGR 7, so nothing on
 * screen depends on it.
 */
(function (global) {
  'use strict';

  // The sixteen named colours, mapped onto the game's palette.
  // Index 0-7 standard, 8-15 bright. Identical to TUMAN_TERMINAL.
  var PALETTE = [
    [11, 16, 23],     // 0  black
    [255, 59, 48],    // 1  red        --red
    [0, 180, 140],    // 2  green
    [214, 158, 60],   // 3  yellow
    [69, 123, 157],   // 4  blue       --dim
    [178, 132, 214],  // 5  magenta
    [69, 123, 157],   // 6  cyan       (classification chrome)
    [201, 214, 224],  // 7  white
    [124, 146, 166],  // 8  bright black - the game's "muted"
    [255, 107, 53],   // 9  bright red    --accent
    [0, 217, 163],    // 10 bright green  --teal
    [255, 182, 39],   // 11 bright yellow --amber
    [110, 171, 214],  // 12 bright blue
    [219, 163, 255],  // 13 bright magenta
    [0, 209, 205],    // 14 bright cyan
    [241, 250, 238]   // 15 bright white  --ink
  ];

  var GROUND = [11, 16, 23];       // pane background
  var DEFAULT_FG = [201, 214, 224]; // pane foreground

  // xterm-256: 0-15 from the table above, 16-231 the 6x6x6 cube,
  // 232-255 the greyscale ramp.
  var XTERM = (function () {
    var t = PALETTE.slice();
    var steps = [0, 95, 135, 175, 215, 255];
    for (var r = 0; r < 6; r++) {
      for (var g = 0; g < 6; g++) {
        for (var b = 0; b < 6; b++) t.push([steps[r], steps[g], steps[b]]);
      }
    }
    for (var i = 0; i < 24; i++) {
      var v = 8 + i * 10;
      t.push([v, v, v]);
    }
    return t;
  })();

  function hex(rgb) {
    var s = '#';
    for (var i = 0; i < 3; i++) {
      var v = Math.max(0, Math.min(255, Math.round(rgb[i]))).toString(16);
      s += v.length < 2 ? '0' + v : v;
    }
    return s;
  }

  // `dim` in a terminal is a blend toward the background, not an opacity:
  // opacity would let the pane's own border bleed through box drawing.
  function toward(rgb, target, amount) {
    return [
      rgb[0] + (target[0] - rgb[0]) * amount,
      rgb[1] + (target[1] - rgb[1]) * amount,
      rgb[2] + (target[2] - rgb[2]) * amount
    ];
  }

  var ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };
  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function (c) { return ESCAPES[c]; });
  }

  function blankState() {
    return {
      fg: null, bg: null, bold: false, dim: false, italic: false,
      underline: false, strike: false, reverse: false
    };
  }

  // ESC [ ... final  |  ESC ] ... BEL/ST  |  ESC <single char>
  var SEQ = /\x1b(?:\[([\x30-\x3f]*)([\x20-\x2f]*)([\x40-\x7e])|\][\s\S]*?(?:\x07|\x1b\\)|[\x40-\x5f])/g;

  /* Consume one SGR colour selector starting at `i` (the 38/48 itself).
     Handles both the classic `38;5;n` / `38;2;r;g;b` forms and the
     colon-delimited `38:2::r:g:b` form some emitters produce. Returns the
     colour and the index of the last parameter consumed. */
  function readColour(p, i) {
    var mode = p[i + 1];
    if (mode === 5) {
      var idx = p[i + 2] | 0;
      return { rgb: XTERM[idx] || DEFAULT_FG, next: i + 2 };
    }
    if (mode === 2) {
      // Skip an empty colour-space id if the colon form left one behind.
      var j = i + 2;
      if (p[j] === null && p.length > j + 3) j++;
      return {
        rgb: [p[j] | 0, p[j + 1] | 0, p[j + 2] | 0],
        next: j + 2
      };
    }
    return { rgb: null, next: i + 1 };
  }

  function applySgr(state, raw) {
    if (raw === '' || raw === null) raw = '0';
    var parts = raw.split(/[;:]/).map(function (x) {
      return x === '' ? null : parseInt(x, 10);
    });
    for (var i = 0; i < parts.length; i++) {
      var n = parts[i];
      if (n === null) n = 0;
      if (n === 0) {
        var fresh = blankState();
        for (var k in fresh) state[k] = fresh[k];
      } else if (n === 1) state.bold = true;
      else if (n === 2) state.dim = true;
      else if (n === 3) state.italic = true;
      else if (n === 4) state.underline = true;
      else if (n === 7) state.reverse = true;
      else if (n === 9) state.strike = true;
      else if (n === 21 || n === 22) { state.bold = false; state.dim = false; }
      else if (n === 23) state.italic = false;
      else if (n === 24) state.underline = false;
      else if (n === 27) state.reverse = false;
      else if (n === 29) state.strike = false;
      else if (n >= 30 && n <= 37) state.fg = PALETTE[n - 30];
      else if (n === 38) { var f = readColour(parts, i); state.fg = f.rgb; i = f.next; }
      else if (n === 39) state.fg = null;
      else if (n >= 40 && n <= 47) state.bg = PALETTE[n - 40];
      else if (n === 48) { var b = readColour(parts, i); state.bg = b.rgb; i = b.next; }
      else if (n === 49) state.bg = null;
      else if (n >= 90 && n <= 97) state.fg = PALETTE[n - 90 + 8];
      else if (n >= 100 && n <= 107) state.bg = PALETTE[n - 100 + 8];
      // Anything else (blink, fonts, underline colour) is ignored.
    }
  }

  function styleCss(state) {
    var fg = state.fg, bg = state.bg;
    if (state.reverse) {
      var swap = fg || DEFAULT_FG;
      fg = bg || GROUND;
      bg = swap;
    }
    if (state.dim) fg = toward(fg || DEFAULT_FG, GROUND, 0.45);
    var css = '';
    if (fg) css += 'color:' + hex(fg) + ';';
    if (bg) css += 'background:' + hex(bg) + ';';
    if (state.bold) css += 'font-weight:700;';
    if (state.italic) css += 'font-style:italic;';
    var deco = [];
    if (state.underline) deco.push('underline');
    if (state.strike) deco.push('line-through');
    if (deco.length) css += 'text-decoration:' + deco.join(' ') + ';';
    return css;
  }

  /**
   * @param {Object} [opts]
   * @param {string} [opts.prefix] class-name prefix, in case two renderers
   *        ever share a document.
   */
  function AnsiRenderer(opts) {
    opts = opts || {};
    this.prefix = opts.prefix || 't';
    this.state = blankState();
    this._classes = Object.create(null);
    this._n = 0;
    this._sheet = null;
  }

  AnsiRenderer.prototype._styleSheet = function () {
    if (!this._sheet) {
      var el = document.createElement('style');
      el.setAttribute('data-ansi', this.prefix);
      document.head.appendChild(el);
      this._sheet = el.sheet;
    }
    return this._sheet;
  };

  AnsiRenderer.prototype._classFor = function (css) {
    if (!css) return null;
    var known = this._classes[css];
    if (known) return known;
    var name = this.prefix + (this._n++);
    this._classes[css] = name;
    try {
      this._styleSheet().insertRule('.' + name + '{' + css + '}',
                                    this._sheet.cssRules.length);
    } catch (e) {
      // A malformed declaration should degrade to unstyled text, never throw
      // in the middle of a turn. The name is already cached above, so the
      // failed rule is not retried on every subsequent chunk.
    }
    return name;
  };

  /** Reset the SGR state (call between campaigns, not between chunks). */
  AnsiRenderer.prototype.reset = function () { this.state = blankState(); };

  /**
   * Render one chunk of raw ANSI to HTML. SGR state carries across calls,
   * so a stream split at an arbitrary byte still renders correctly.
   * @param {string} text
   * @returns {string} HTML
   */
  AnsiRenderer.prototype.render = function (text) {
    if (text === null || text === undefined) return '';
    text = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '');
    var out = [];
    var self = this;

    function emit(chunk) {
      if (!chunk) return;
      var cls = self._classFor(styleCss(self.state));
      if (cls) {
        out.push('<span class="' + cls + '">' + escapeHtml(chunk) + '</span>');
      } else {
        out.push(escapeHtml(chunk));
      }
    }

    var last = 0, m;
    SEQ.lastIndex = 0;
    while ((m = SEQ.exec(text)) !== null) {
      if (m.index > last) emit(text.slice(last, m.index));
      last = SEQ.lastIndex;
      // m[3] is the final byte of a CSI sequence; only 'm' is SGR. Everything
      // else (cursor moves, erases, private modes) is dropped.
      if (m[3] === 'm' && !/[\x3c-\x3f]/.test(m[1] || '')) {
        applySgr(this.state, m[1]);
      }
    }
    if (last < text.length) emit(text.slice(last));
    return out.join('');
  };

  /** Plain text with every escape sequence removed (used for copy/aria). */
  AnsiRenderer.strip = function (text) {
    return String(text === null || text === undefined ? '' : text)
      .replace(SEQ, '').replace(/\r/g, '');
  };

  AnsiRenderer.PALETTE = PALETTE;
  global.AnsiRenderer = AnsiRenderer;
})(typeof self !== 'undefined' ? self : this);
