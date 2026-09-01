"""Browser-side game bridge: drives GameManager and renders raw ANSI.

This module is the Python half of the FALSE FLAG web build. It is bundled
into ``game.zip`` alongside ``engine/``, ``models/``, ``llm/``, ``agents/``
and ``data/``, and imported inside a Pyodide runtime that lives in a Web
Worker (``docs/worker.js``).

Design rules
------------
* **No cli/ imports.** The whole port rests on the fact that
  ``engine.game_manager`` pulls in zero rich/typer/click/requests.
* **Raw ANSI out, always.** Rendering ANSI to HTML is the page's job, not
  this module's. Everything here emits 16-colour SGR sequences so the page
  can map them onto the game's palette (``PALETTE`` in ``docs/ansi.js``).
* **Pure Python, no JS.** ``WebGame`` takes an ``emit`` callable and never
  touches the browser directly, so the whole protocol is unit-testable from
  pytest (see ``tests/test_web_bridge.py``).
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import re
import textwrap
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

# Python stdout in the worker goes to the browser console only — never to the
# page — so these traces are safe diagnostics for a build with no other way to
# see where a slow turn is spending its time.
_T0 = time.time()


def trace(label: str) -> None:
    print(f"[trace {time.time() - _T0:8.2f}s] {label}")

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------

RESET = "\x1b[0m"

# 16-colour SGR only. The site's terminal theme already maps these onto the
# Operation Tuman palette, so the page gets the game's real colours for free.
AMBER = "\x1b[93m"      # bright yellow -> amber   (headers, emphasis)
ACCENT = "\x1b[91m"      # bright red    -> orange  (titles, alerts)
TEAL = "\x1b[92m"        # bright green  -> teal    (good news)
DIM = "\x1b[90m"         # bright black  -> muted   (chrome, metadata)
INK = "\x1b[97m"         # bright white  -> ink     (body text)
SIG = "\x1b[96m"         # bright cyan             (speaker names)
DANGER = "\x1b[31m"      # red                     (bad news)
BOLD = "\x1b[1m"
ITALIC = "\x1b[3m"

DEFAULT_WIDTH = 84
MIN_WIDTH = 40
MAX_WIDTH = 200

# The one endpoint the shared key is ever allowed to talk to (ER-028).
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def clamp_width(width: Any, default: int = DEFAULT_WIDTH) -> int:
    """A column width that every consumer of it can survive.

    ``AnsiPen`` has always clamped its own copy, but ``WebGame.width`` is used
    raw in two other places — ``str.center(self.width)`` and
    ``textwrap.wrap(..., self.width - 2)``. The second raises ``ValueError``
    for a width below 3, and it runs in the ``finally`` of ``handle``, which
    is documented to never raise; the escape would surface to the player as a
    worker-level fault instead of a game error. So clamp once, at the point
    the config is read, to the same bounds ``AnsiPen`` uses.

    A width that is not a number at all (``"wide"``, ``None``, a dict) falls
    back to ``default`` rather than blowing up a whole newGame.
    """
    try:
        value = int(width)
    except (TypeError, ValueError):
        value = default
    return max(MIN_WIDTH, min(MAX_WIDTH, value))


def _c(colour: str, text: str) -> str:
    return f"{colour}{text}{RESET}"


# A line that starts a new block rather than continuing the previous one.
_BLOCK_START = ("-", "*", "•", "·", ">", "#", "=", "○", "✓", "✗", "†", "▲", "■")

# A short leading label ("INTERPRETATION:", "Action Quality:", "Reasoning:").
# The engine emits these as record-style lines; merging them into a paragraph
# turns a structured assessment into mush.
_LABEL_RE = re.compile(r"^[A-Z][A-Za-z0-9 '/&()-]{0,30}:(\s|$)")


def _reflow(text: str) -> List[str]:
    """Undo soft line breaks inside paragraphs; keep real structure.

    Blank lines separate paragraphs. Bullets, headings and rules start a new
    block (and absorb their own continuation lines). Everything else in a run
    is joined so it can be re-wrapped to the caller's width.
    """
    blocks: List[str] = []
    buf: List[str] = []

    def flush():
        if buf:
            blocks.append(" ".join(buf))
            buf.clear()

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            flush()
            blocks.append("")
            continue
        if line.startswith(("===", "---", "***")):
            flush()
            blocks.append(line)       # a rule or banner stands alone
            continue
        if line.startswith(_BLOCK_START):
            flush()
            buf.append(line)          # continuation lines join this bullet
            continue
        if line.endswith(":") and len(line) < 60:
            flush()
            blocks.append(line)       # a heading owns its line
            continue
        if _LABEL_RE.match(line):
            flush()
            buf.append(line)          # labelled record; continuations join it
            continue
        buf.append(line)
    flush()

    # Collapse runs of blank separators.
    out: List[str] = []
    for b in blocks:
        if not b and out and not out[-1]:
            continue
        out.append(b)
    return out


class AnsiPen:
    """Accumulates ANSI text at a fixed column width.

    Everything is fixed-width: this is a terminal game, and the box drawing,
    the aligned metric tables and the rules all depend on a column being a
    column. A previous revision gave narrative blocks a "flow" mode that the
    page re-set as book-face prose at its own measure; that turned the game
    into a web document and is gone.
    """

    def __init__(self, width: int = DEFAULT_WIDTH):
        self.width = clamp_width(width)
        self._parts: List[str] = []

    def raw(self, text: str = "") -> "AnsiPen":
        self._parts.append(text)
        return self

    def blank(self, n: int = 1) -> "AnsiPen":
        for _ in range(n):
            self._parts.append("")
        return self

    def rule(self, char: str = "─", colour: str = DIM) -> "AnsiPen":
        return self.raw(_c(colour, char * self.width))

    def banner(self, text: str, colour: str = AMBER) -> "AnsiPen":
        """A centred, ruled section banner."""
        label = f" {text.strip().upper()} "
        pad = max(0, self.width - len(label))
        left = pad // 2
        right = pad - left
        return self.raw(_c(colour, BOLD + "═" * left + label + "═" * right))

    def section(self, text: str, colour: str = AMBER) -> "AnsiPen":
        """A left-aligned minor heading with a trailing rule to the margin."""
        label = f"── {text.strip().upper()} "
        return self.raw(_c(colour, label + "─" * max(0, self.width - len(label))))

    def wrap(self, text: str, colour: str = "", indent: str = "",
             subsequent: Optional[str] = None, reflow: bool = True) -> "AnsiPen":
        """Word-wrap prose, preserving paragraph breaks.

        Scenario text arrives hard-wrapped for an 80-column terminal. Re-
        wrapping each of those physical lines on its own leaves a ragged
        column of orphans ("beneath", "clinical", "map"), so by default the
        soft line breaks inside a paragraph are undone first.
        """
        if text is None:
            return self
        sub = indent if subsequent is None else subsequent
        avail = max(20, self.width - len(sub))
        blocks = _reflow(str(text)) if reflow else \
            [ln.rstrip() for ln in str(text).replace("\r\n", "\n").split("\n")]
        for block in blocks:
            if not block.strip():
                self.blank()
                continue
            wrapped = textwrap.wrap(
                block.strip(), width=avail,
                initial_indent=indent, subsequent_indent=sub,
                break_long_words=False, break_on_hyphens=False,
            ) or [indent + block.strip()]
            for line in wrapped:
                self.raw(_c(colour, line) if colour else line)
        return self

    def speaker(self, name: str, text: str, colour: str = SIG) -> "AnsiPen":
        self.raw(_c(colour, BOLD + name.upper()))
        self.wrap(text, colour=INK, indent="  ", subsequent="  ")
        self.blank()
        return self

    def text(self) -> str:
        return "\n".join(self._parts)


def _delta(metric: str, value: int) -> str:
    """Signed metric delta, coloured by whether it is good or bad news.

    Polarity is per-metric and comes from ``engine.utils`` — the same table
    the terminal build colours from — because the five metrics do not agree
    about which way is up. A rise in escalation risk or casualties is an
    alert; a rise in domestic stability or alliance cohesion is good news.
    """
    from engine.utils import delta_is_good

    if not value:
        return _c(DIM, "0")
    text = f"+{value}" if value > 0 else str(value)
    good = delta_is_good(metric, value)
    if good is None:
        # A metric with no declared polarity: show the move, claim nothing.
        return _c(AMBER, text)
    return _c(TEAL if good else ACCENT, text)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

AWAIT_NONE = "none"          # busy, booting, or the campaign is over
AWAIT_DECISION = "decision"  # the turn is open: decide / ask / call
AWAIT_QUESTION = "question"  # a diplomatic call is live; next `call` continues it
AWAIT_CONFIRM = "confirm"    # decision resolved; send endTurn to advance
AWAIT_PAUSE = "pause"        # a beat has played; send `continue` for the next
AWAIT_ORDER = "order"        # `/decide` was typed bare: the next line is the order

# The command set, in the CLI's own words and order (cli/rich_ui.command_menu
# and the /menu block in cli/main.py). The browser build parses input here
# rather than in the page for the same reason the CLI parses it in one place:
# a second copy in JavaScript would drift, and the terminal would start
# disagreeing with itself about what it accepts.
#
# /theme and /llm are deliberately absent. The CLI changes rich's palette and
# opens a model-settings menu; this build has one palette and picks its model
# on the way in, so offering them would be a promise the page cannot keep.
COMMANDS = [
    ("/menu", "Show this list (also /help)"),
    ("/status", "Current metrics and situation"),
    ("/status advisors", "Advisor trust and standing"),
    ("/advise", "Every advisor reports (/advise concise for brief)"),
    ("/askall <question>", "Put one question to the whole room"),
    ("/resources", "UK forces and stockpiles"),
    ("/intel [country]", "Intelligence on foreign actors"),
    ("/call <country>", "Contact a foreign leader or diplomat"),
    ("/decide", "Give the order"),
    ("/save", "Save the campaign"),
    ("/quit", "Leave the crisis room"),
]

# The CLI accepts these bare as well as slashed ("status", "/status").
# Not "intel": cli/main.py matches only the slashed form, so bare "intel"
# is a question to the room there — and therefore here.
_BARE_ALIASES = {"menu", "help", "status", "advise", "resources",
                 "decide", "decision", "save", "quit",
                 # Handled below with an explanation rather than silently sent
                 # to the model as a question; the CLI takes these bare too.
                 "theme", "llm", "settings",
                 # The one two-word bare form the CLI accepts.
                 "status advisors"}

# /advise asks each seat its own question, which is what makes it different
# from /askall putting one question to everyone. Text mirrors cli/main.py.
_ADVISE_ROUNDS = [
    ("national_security_advisor",
     "NSA, what's your assessment of the current situation and recommended "
     "course of action?"),
    ("chief_defence_staff",
     "CDS, what are our military options and constraints?"),
    ("foreign_secretary",
     "Foreign Secretary, what's the diplomatic landscape and alliance status?"),
    ("home_secretary",
     "Home Secretary, what are the domestic security concerns?"),
    ("attorney_general",
     "Attorney General, what are the legal constraints and considerations?"),
]

# Player-facing labels for the advisors the question router understands.
ADVISORS = [
    {"id": "chief_defence_staff", "label": "Chief of the Defence Staff", "cue": "CDS"},
    {"id": "national_security_advisor", "label": "National Security Adviser", "cue": "NSA"},
    {"id": "foreign_secretary", "label": "Foreign Secretary", "cue": "Foreign Secretary"},
    {"id": "home_secretary", "label": "Home Secretary", "cue": "Home Secretary"},
    {"id": "attorney_general", "label": "Attorney General", "cue": "Attorney General"},
]
_ADVISOR_CUE = {a["id"]: a["cue"] for a in ADVISORS}
_ADVISOR_CUE.update({a["label"].lower(): a["cue"] for a in ADVISORS})

# The scenario roster carries the cabinet titles above, so a seated advisor is
# already named correctly by the time a line reaches the page. A model asked
# for pushback or a critical concern is not bound by the roster, though, and
# will sometimes answer as the abstracted persona the prompts once used — so
# normalise on the way out rather than seating "LEGAL ADVISOR" next to the
# Attorney General the picker just offered. Mirrors
# cli/display_utils._ROLE_DISPLAY_TITLES; the browser build cannot import cli.
_PERSONA_ROLE_TITLES = {
    "military commander": "Chief of the Defence Staff",
    "intelligence coordinator": "National Security Adviser",
    "national security advisor": "National Security Adviser",
    "diplomatic lead": "Foreign Secretary",
    "domestic security": "Home Secretary",
    "legal advisor": "Attorney General",
    "government leader": "Prime Minister",
}


def display_role(role: str) -> str:
    """Cabinet title for a speaker label. Unknown names pass through."""
    text = str(role or "").strip()
    return _PERSONA_ROLE_TITLES.get(text.lower(), text)

# The whole-room target, reached by opening a line with "everyone," or by
# /askall. Not in ADVISORS: it has no routing cue — ask() branches on the id
# instead, and every seated advisor answers (one LLM call each; see
# GameManager.process_question_all).
ASK_ALL = {"id": "all", "label": "Everyone — the whole room answers"}

VARIANTS = {"standard", "fast_start"}


# ---------------------------------------------------------------------------
# Live-endpoint faults
# ---------------------------------------------------------------------------
#
# A live endpoint can refuse: the key was revoked, its spend limit was reached,
# the free-tier allowance is spent, the network went. ``llm/router.py`` is
# deliberately resilient about that — it retries once and then answers from the
# deterministic offline driver, so a turn never dies half-written. In the
# terminal build the warning it prints lands in front of the player. In the
# browser the same print goes to the developer console, which nobody has open,
# and the only symptom is advisors who have quietly stopped reading what was
# actually written.
#
# So: watch the driver, record every refusal, and say so on the page in words.
# Nothing here changes what the game does — the exception is re-raised and the
# router's own fallback still runs. This only makes the failure audible.

_LLM_FAULTS: List[str] = []
_HTTP_CODE_RE = re.compile(r"HTTP (\d{3})")
_BATCH_ERROR_PREFIX = "[ERROR:"

# Faults that never got as far as an HTTP request. The call was never issued,
# so a notice blaming OpenRouter — or the player's connection — sends them
# hunting for a problem that is not there. That is not a hypothetical: a
# browser running a cached pre-bb55a91 bundle failed every batched call on
# Pyodide's missing thread support and was told, five advisors at a time, that
# the network had gone.
_THREAD_FAULT_RE = re.compile(r"can'?t start new thread"
                              r"|can not start new thread"
                              r"|thread can only be started once", re.IGNORECASE)
_CONFIG_FAULT_RE = re.compile(r"OPENAI_COMPAT_(?:BASE_URL|MODEL|API_KEY)"
                              r"|not found in environment or config", re.IGNORECASE)


def classify_local_fault(faults: List[str]) -> str:
    """Name the kind of fault that never reached the wire.

    Returns ``'threads'`` (this build could not start the calls),
    ``'config'`` (there was no endpoint to call) or ``''`` — the last
    meaning nothing here rules out a genuine network or endpoint fault.
    """
    blob = " ".join(faults)
    if _THREAD_FAULT_RE.search(blob):
        return "threads"
    if _CONFIG_FAULT_RE.search(blob):
        return "config"
    return ""


def _watch_calls(fn: Callable) -> Callable:
    """Record failures from one driver method, then let them propagate.

    The wrapper takes on the wrapped method's signature: the router
    inspects driver signatures to decide which optional arguments to
    forward, and a bare ``*args, **kwargs`` facade would tell it the
    driver accepts everything - forwarding arguments the real method then
    rejects, turning every live call into a TypeError.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - re-raised immediately below
            _LLM_FAULTS.append(str(exc))
            raise
        # batch_generate_text catches per-prompt failures itself and returns
        # them as "[ERROR: ...]" strings, so nothing is raised for those.
        if isinstance(result, list):
            for item in result:
                if isinstance(item, str) and item.startswith(_BATCH_ERROR_PREFIX):
                    _LLM_FAULTS.append(item)
        return result

    functools.update_wrapper(wrapper, fn)
    wrapper.__signature__ = inspect.signature(fn)  # type: ignore[attr-defined]
    wrapper._ff_watched = True  # type: ignore[attr-defined]
    return wrapper


_PROBE_INSTALLED = False


def install_fault_probe() -> None:
    """Wrap live drivers so their refusals can be reported to the player.

    Installed lazily, the first time a real key is set, so a mock-driver
    session (and every test that runs one) is untouched.
    """
    global _PROBE_INSTALLED
    if _PROBE_INSTALLED:
        return
    import llm.router as router

    original = router._construct_text_driver

    def watched(provider: str, model_name: Optional[str] = None):
        driver = original(provider, model_name)
        if provider != "openai_compat":
            return driver
        for name in ("generate_text", "batch_generate_text"):
            fn = getattr(driver, name, None)
            if fn is None or getattr(fn, "_ff_watched", False):
                continue
            setattr(driver, name, _watch_calls(fn))
        return driver

    router._construct_text_driver = watched
    _PROBE_INSTALLED = True


@functools.lru_cache(maxsize=1)
def _call_aliases() -> tuple:
    """Every name the switchboard answers to, longest first.

    Read from the engine's own alias table so this cannot drift from what
    ``start_diplomacy`` will actually resolve.
    """
    try:
        from engine.diplomacy import COUNTRY_ALIASES
    except Exception:
        return ()
    return tuple(sorted((a.upper() for a in COUNTRY_ALIASES),
                        key=lambda a: -len(a.split())))


def _split_call_target(rest: str) -> tuple:
    """Separate the country from anything to be said as the line opens.

    Country names have spaces in them — "united states" is a real alias — so
    the argument cannot simply be split on the first space: that dialled
    "united" and said "states" on the line. Match the longest known name at
    the front instead, and treat whatever follows as the opening remark.

    A quoted name is taken whole, for a country the alias table has not heard
    of. Failing both, the first word is the country and the rest is the
    remark, which is what ``/call <code> <message>`` has always meant.
    """
    rest = rest.strip()
    if rest[:1] in ('"', "'"):
        quote = rest[0]
        closing = rest.find(quote, 1)
        if closing != -1:
            return rest[1:closing].strip(), rest[closing + 1:].strip()

    words = rest.split()
    for alias in _call_aliases():
        span = alias.split()
        if [w.upper() for w in words[:len(span)]] == span:
            return " ".join(words[:len(span)]), " ".join(words[len(span):])

    head, _, tail = rest.partition(" ")
    return head.strip(), tail.strip()


def describe_llm_faults(faults: List[str], source: str,
                        model: str = "") -> str:
    """Turn raw driver errors into one sentence a player can act on.

    ``source`` is 'shared' (the owner's key, unlocked with a passphrase),
    'own' (a key the player pasted) or '' (unknown). ``model`` is the
    OpenRouter model id the calls ran on, named in the notice so the player
    can see at a glance whether an oversubscribed ':free' model is the
    likely culprit.
    """
    codes = set()
    for fault in faults:
        match = _HTTP_CODE_RE.search(fault)
        if match:
            codes.add(int(match.group(1)))

    # Only consulted when no call came back with a status: a real HTTP code is
    # always the more specific story, and a mixed batch should be described by
    # the refusal that actually reached the wire.
    local = "" if codes else classify_local_fault(faults)

    if source == "shared":
        whose, subject = "the shared key", "The shared key"
    elif source == "own":
        whose, subject = "your key", "Your key"
    else:
        whose, subject = "the key", "The key"

    named = f" on {model}" if model else ""
    free_model = ":free" in (model or "")

    if codes & {401, 403}:
        code = sorted(codes & {401, 403})[0]
        what = (f"{subject} was rejected by OpenRouter (HTTP {code}) — it may "
                f"have been revoked, or it may have hit its spend limit.")
        fix = ("Nothing on this page can fix that; whoever published the "
               "passphrase has to issue a new key."
               if source == "shared" else
               "Reload and set a different key to carry on with live advisors.")
    elif 402 in codes:
        what = (f"OpenRouter says {whose} is out of credit (HTTP 402) — the "
                f"spend limit on it has been reached.")
        fix = ("Nothing on this page can fix that; whoever published the "
               "passphrase has to top it up or issue a new key."
               if source == "shared" else
               "Top the key up, or reload and set a different one.")
    elif 429 in codes:
        what = (f"OpenRouter is rate-limiting {whose}{named} (HTTP 429) — "
                f"too many requests, or the allowance is spent for now.")
        fix = ("Free models share one public allowance and it runs dry for "
               "everyone at once. Switch MODEL to a paid id and carry on, "
               "or try again much later."
               if free_model else
               "Give it a minute and carry on; it may come back on its own.")
    elif codes:
        code = sorted(codes)[0]
        what = f"OpenRouter refused the request{named} (HTTP {code})."
        fix = "It may be temporary. Carry on and see."
    elif local == "threads":
        # Nothing was sent. Saying "OpenRouter never answered" here is not a
        # vague description of a real fault, it is the wrong fault: the player
        # goes and checks an endpoint that was never called.
        what = ("The advisors' calls were never sent — this build could not "
                "start them. Nothing reached OpenRouter, so neither the "
                "endpoint nor your connection is at fault.")
        fix = ("This is fixed in the current build, and a browser still "
               "running a cached copy of the old one is the usual cause. "
               "Reload the page with a hard refresh (Ctrl-Shift-R, or "
               "Cmd-Shift-R on a Mac) to pick the new build up.")
    elif local == "config":
        what = ("The advisors' calls were never sent — no live endpoint is "
                "configured, so there was nothing to call.")
        fix = ("Reload and set a key (or a base URL and MODEL) to carry on "
               "with live advisors.")
    else:
        what = (f"The call to OpenRouter never got an answer "
                f"(using {whose}{named}).")
        fix = ("A ':free' model that is oversubscribed can queue until the "
               "connection gives up, which looks exactly like this. Switch "
               "MODEL to a paid id and carry on — or, if it really is the "
               "network, carrying on will simply work."
               if free_model else
               "That is usually the network. Carry on and see.")

    return (f"{what} The advisors answered from the offline stand-in for that "
            f"call, so they replied without reading what you wrote. {fix}")


class WebGame:
    """Stateful driver for one browser session.

    ``emit`` is called with a plain dict per protocol message. The worker
    passes a function that JSON-encodes and ``postMessage``s it.
    """

    def __init__(self, emit: Callable[[Dict[str, Any]], None]):
        self._emit = emit
        self.gm = None
        self.width = DEFAULT_WIDTH
        self.awaiting = AWAIT_NONE
        self._call_seen = 0  # how many lines of the live call have been sent
        # Which key is behind the live endpoint, so a refusal can be described
        # to the right person. '' until setKey says.
        self.key_source = ""
        # Parse-health events already reported, so each turn's report only
        # covers that turn.
        self._parse_health_seen = 0
        # Beats waiting on the space bar. The engine is synchronous inside the
        # worker, so a paced sequence cannot block for input: it emits one
        # beat, parks the rest here, and resumes on the next `continue`.
        self._paused: List[Callable[[], None]] = []

    # -- plumbing ---------------------------------------------------------

    def emit(self, **msg: Any) -> None:
        self._emit(msg)

    def out(self, pen: AnsiPen, instant: bool = False) -> None:
        """Send one rendered block to the page.

        ``instant`` marks chrome — the masthead, prompts, state lines,
        fault banners — that the page must show whole rather than feed
        through its typewriter reveal. Narrative blocks (the default) are
        the ones the reveal paces. The key is only present when true, so
        the message shape is unchanged for every existing consumer.
        """
        body = pen.text()
        if body.strip():
            if instant:
                self.emit(type="output", ansi=body + RESET, instant=True)
            else:
                self.emit(type="output", ansi=body + RESET)

    def set_awaiting(self, kind: str) -> None:
        self.awaiting = kind
        self.emit(type="awaiting", kind=kind)

    # -- pacing ------------------------------------------------------------

    def queue(self, *beats: Callable[[], None]) -> None:
        """Park beats to be played one space-bar press apart."""
        self._paused.extend(beats)

    def start_briefing(self) -> None:
        """Run a briefing *through the queue*, so its pause state is emitted.

        ``play_next`` is the only thing that publishes ``AWAIT_PAUSE``. A
        briefing that splits parks its report beat, so calling
        ``run_briefing`` directly left the page on ``AWAIT_NONE`` with a beat
        pending — input blocked, reload the only way out.
        """
        self.queue(self.run_briefing)
        self.play_next()

    def play_next(self) -> None:
        """Play the next parked beat.

        A beat may park more of its own (the briefing does), so the decision
        to pause is taken after it runs. The last beat in a sequence is
        responsible for setting the awaiting state it hands back to — which
        is why this does not set one when the queue empties.
        """
        if not self._paused:
            return
        beat = self._paused.pop(0)
        beat()
        if self._paused:
            self.set_awaiting(AWAIT_PAUSE)

    def _emit_scene(self, scene: Any) -> None:
        """Render one beat of the cold open.

        The CLI draws an animated scene card and streams the body through a
        typewriter; here the card is static and the body arrives whole. Both
        read from the same ``engine.opening`` beats, so the pacing — where
        the breaks fall — is identical even though the rendering is not.
        """
        pen = AnsiPen(self.width)
        pen.blank()
        if scene.has_card:
            pen.section(f"SCENE {scene.numeral} ── {scene.title}", ACCENT)
            meta = "  ·  ".join(p for p in (scene.location, scene.timestamp) if p)
            if meta:
                pen.raw(_c(DIM, "  " + meta))
            pen.blank()

        # Headings inside the body ("## YOUR ROLE") become section rules;
        # everything between them is prose to be re-wrapped to this width.
        prose: List[str] = []

        def flush() -> None:
            if prose:
                pen.wrap("\n".join(prose), colour=INK)
                prose.clear()

        for line in scene.body:
            stripped = line.strip()
            if stripped.startswith("## "):
                flush()
                pen.blank()
                pen.section(stripped[3:], AMBER)
                pen.blank()
            else:
                prose.append(line)
        flush()

        pen.blank()
        self.out(pen)

    def error(self, message: str, fatal: bool = False) -> None:
        self.emit(type="error", message=message, fatal=bool(fatal))

    def reject(self, message: str, was_awaiting: str) -> None:
        """Refuse a malformed message and put the player back where they were.

        ``handle`` marks the session busy (``AWAIT_NONE``) before dispatching,
        so re-emitting ``self.awaiting`` from a rejection path emits the busy
        value — and the page blocks input on ``'none'`` (see
        ``docs/worker.js``), leaving reload as the only way out. The
        position to restore is the one captured *before* dispatch.
        """
        self.error(message)
        self.set_awaiting(was_awaiting)

    # -- LLM configuration -------------------------------------------------

    def set_key(self, key: Optional[str], base_url: Optional[str] = None,
                model: Optional[str] = None, source: Optional[str] = None) -> None:
        """Switch between the deterministic mock driver and a real endpoint.

        An empty/absent key means mock play, so a stranger with no API key
        can still play a whole campaign. The key only ever goes into this
        worker's process environment and from there into the Authorization
        header of the configured endpoint.

        HARD RULE (ER-028): when the key came from the shared blob, any
        ``base_url`` in the message is discarded — and so is anything an
        earlier own-key session left in the environment. The shared key
        only ever talks to OpenRouter; an endpoint override would let a
        tampered page redirect the owner's key (and its spend limit) to an
        arbitrary host. The model choice is honoured for both sources.
        """
        import llm.router as router

        key = (key or "").strip()
        self.key_source = (source or "").strip().lower()
        if key:
            install_fault_probe()
            if self.key_source == "shared":
                base_url = None
                os.environ["OPENAI_COMPAT_BASE_URL"] = OPENROUTER_BASE_URL
            os.environ["OPENAI_COMPAT_API_KEY"] = key
            os.environ["OPENAI_COMPAT_BASE_URL"] = (
                base_url or os.environ.get("OPENAI_COMPAT_BASE_URL")
                or OPENROUTER_BASE_URL
            )
            os.environ["OPENAI_COMPAT_MODEL"] = (
                model or os.environ.get("OPENAI_COMPAT_MODEL")
                or "openai/gpt-4o-mini"
            )
            # Thinking models spend their reply budget on hidden reasoning
            # and return EMPTY completions on capped calls (ER-071). The
            # fix is env-driven and this front end never set it, so the
            # play page still hit the defect the engine had already cured -
            # a silent diplomatic call was the visible symptom.
            os.environ.setdefault("OPENAI_COMPAT_REASONING", "off")
            os.environ["WARGAME_LLM"] = "openai_compat"
            provider_note = (
                f"LIVE MODEL: {os.environ['OPENAI_COMPAT_MODEL']} via "
                f"{os.environ['OPENAI_COMPAT_BASE_URL']}"
            )
        else:
            os.environ.pop("OPENAI_COMPAT_API_KEY", None)
            os.environ["WARGAME_LLM"] = "mock"
            provider_note = (
                "OFFLINE MODE — deterministic advisors, no API key, nothing "
                "leaves this browser."
            )

        # Drivers are cached per (provider, model); drop the cache so the
        # switch takes effect on the very next call.
        router._driver_cache.clear()

        pen = AnsiPen(self.width)
        pen.raw(_c(DIM, f"[ {provider_note} ]")).blank()
        self.out(pen, instant=True)

    def provider(self) -> str:
        import llm.router as router
        return router._get_provider()

    # -- lifecycle ---------------------------------------------------------

    def new_game(self, config: Optional[Dict[str, Any]] = None) -> None:
        config = dict(config or {})
        # Clamped here, not at each use: `self.width` is read raw by
        # `_emit_ending` (str.center) and `_report_llm_faults` (textwrap.wrap,
        # which rejects a width below 1), and the latter runs in `handle`'s
        # `finally`, where an exception would break the "never raises" contract.
        self.width = clamp_width(config.get("width") or DEFAULT_WIDTH)

        scenario = (config.get("scenario") or "war_game_2025").strip()
        variant = (config.get("variant") or "standard").strip()
        # The UI's single `scenario` field doubles as a variant picker: this
        # scenario pack ships one scenario id with two campaign lengths.
        if scenario in VARIANTS:
            scenario, variant = "war_game_2025", scenario
        if variant not in VARIANTS:
            variant = "standard"

        play_mode = (config.get("playMode") or config.get("play_mode")
                     or "immersive").strip().lower()
        if play_mode not in ("classic", "immersive", "emergent"):
            play_mode = "immersive"

        mystery = bool(config.get("mysteryMode", config.get("mystery_mode", False)))

        seed = config.get("seed")
        if seed in (None, ""):
            import random as _random
            seed = _random.randrange(1, 10_000_000)
        seed = int(seed)

        from engine.game_manager import GameManager

        self.gm = GameManager(
            scenario_id=scenario,
            variant=variant,
            difficulty=(config.get("difficulty") or "standard"),
            play_mode=play_mode,
            seed=seed,
            mystery_mode=mystery,
            # Leave the rule to the engine: Classic has the win/lose
            # thresholds its menu promises, Immersive and Emergent are
            # open-ended by design (cli/main.py:1964). This used to force
            # endings on in every mode so a browser session could always
            # reach a debrief — but that silently converted an open-ended
            # mode into a ten-turn one, which is not the front end's call
            # to make.
            endings=None,
        )
        self._call_seen = 0
        self._paused.clear()

        self._emit_masthead()
        self.push_state()

        # The cold open: four beats, one space-bar press apart, then turn 1
        # flows on from YOUR ROLE. Without it the campaign opened on the
        # briefing — five simultaneous crises and no idea who anyone was.
        # Taken through the GameManager passthrough, which strips the Rich
        # console markup this renderer would otherwise show raw.
        beats: List[Callable[[], None]] = [
            (lambda s=scene: self._emit_scene(s))
            for scene in self.gm.get_opening_scenes()
        ]
        self.queue(*beats, self.run_briefing)
        self.play_next()

    def _emit_masthead(self) -> None:
        gm = self.gm
        cfg = gm.scenario_config
        pen = AnsiPen(self.width)
        pen.blank()
        pen.banner("FALSE FLAG", ACCENT)
        pen.blank()
        pen.wrap("OPERATION TUMAN — UK CRISIS CABINET", colour=AMBER + BOLD)
        pen.blank()
        pen.raw(_c(DIM, f"  CAMPAIGN   {cfg.get('name', gm.variant)}"))
        pen.raw(_c(DIM, f"  MODE       {gm.play_mode.upper()}"
                        f"{'  ·  MYSTERY' if gm.mystery_mode else ''}"))
        # Only Classic is graded at a final turn; announcing a length in the
        # open-ended modes promises an ending that will never come.
        if gm.endings_enabled:
            pen.raw(_c(DIM, f"  LENGTH     {gm.campaign_final_turn} turns "
                            f"({cfg.get('scripted_turns', '?')} scripted)"))
        else:
            pen.raw(_c(DIM, f"  LENGTH     open-ended "
                            f"({cfg.get('scripted_turns', '?')} scripted, then "
                            f"it keeps going)"))
        pen.raw(_c(DIM, f"  SEED       {gm.seed}"))
        pen.raw(_c(DIM, f"  MODEL      {'live endpoint' if self.provider() == 'openai_compat' else 'offline (deterministic)'}"))
        pen.blank()
        pen.rule("═", DIM)
        pen.blank()
        self.out(pen, instant=True)

    # -- state -------------------------------------------------------------

    def metrics_visible(self) -> bool:
        return bool(self.gm) and self.gm.play_mode == "classic"

    def push_state(self) -> None:
        gm = self.gm
        if gm is None:
            self.emit(type="state", turn=0, metricsVisible=False, metrics=None)
            return

        m = gm.world.metrics
        metrics = {
            "escalation_risk": m.escalation_risk,
            "domestic_stability": m.domestic_stability,
            "alliance_cohesion": m.alliance_cohesion,
            "casualties_mil": m.casualties_mil,
            "casualties_civ": m.casualties_civ,
        } if self.metrics_visible() else None

        # Qualitative read-out, safe to show in metric-hiding modes.
        try:
            vibes = [
                {"name": v.name, "descriptor": v.descriptor}
                for v in gm.narrative_state.get_situation_vibes()
            ]
        except Exception:
            vibes = []

        self.emit(
            type="state",
            turn=gm.world.turn,
            metricsVisible=self.metrics_visible(),
            metrics=metrics,
            # Extra, non-secret context the UI may use or ignore.
            phase=gm.world.phase,
            playMode=gm.play_mode,
            mysteryMode=gm.mystery_mode,
            scenario=gm.scenario_id,
            variant=gm.variant,
            seed=gm.seed,
            # None in the open-ended modes: the page renders "TURN 4 / 10"
            # from this, and there is no 10 to render.
            finalTurn=gm.campaign_final_turn if gm.endings_enabled else None,
            vibes=vibes,
            # No advisor or contact rosters here: the picker that consumed them
            # is gone, and the terminal answers both questions in the
            # transcript instead (/menu, /status advisors). Sending lists
            # nothing reads meant calling list_diplomatic_channels() on every
            # state push for output that went straight in the bin.
            over=gm.is_over(),
        )

    # -- turn phases -------------------------------------------------------

    def _metrics_snapshot(self) -> Dict[str, int]:
        m = self.gm.world.metrics
        return {
            "escalation_risk": m.escalation_risk,
            "domestic_stability": m.domestic_stability,
            "alliance_cohesion": m.alliance_cohesion,
            "casualties_mil": m.casualties_mil,
            "casualties_civ": m.casualties_civ,
        }

    def run_briefing(self) -> None:
        gm = self.gm
        before = self._metrics_snapshot()
        mark = len(gm.transcript)
        trace(f"briefing turn {gm.world.turn} start")
        inject = gm.get_turn_briefing()
        trace(f"briefing turn {gm.world.turn} done: {inject.get('title')!r}")
        new_lines = gm.transcript[mark:]

        # The turn banner is chrome (fixed-width box drawing); the narrative
        # that follows is prose. Two pens so each can be styled as what it is.
        pen = AnsiPen(self.width)
        pen.blank()
        pen.banner(
            f"TURN {gm.world.turn} OF {gm.campaign_final_turn}"
            if gm.endings_enabled else f"TURN {gm.world.turn}",
            AMBER)
        pen.blank()
        self.out(pen)

        pen = AnsiPen(self.width)

        # The narrator bridge lands in the transcript as "[Narrator] ..."
        bridge = next(
            (ln for ln in reversed(new_lines) if ln.strip().startswith("[Narrator]")),
            None,
        )
        if bridge and gm.world.turn > 1:
            pen.wrap(bridge.strip()[len("[Narrator]"):].strip(),
                     colour=DIM + ITALIC)
            pen.blank()

        channel = (inject.get("channel") or "briefing").upper()
        channel_colour = {"BREAKING": DANGER, "INTEL": AMBER}.get(channel, SIG)
        title = str(inject.get("title") or "NO NEW DEVELOPMENTS")
        pen.raw(_c(channel_colour, f"[{channel}]") + " " + _c(ACCENT, BOLD + title.upper()))
        pen.blank()

        # The briefing sets the room, then hands over to the National Security
        # Advisor for the intelligence itself. A pause between the two stops
        # several simultaneous crises reading as one wall of text.
        #
        # Unlike the CLI this splits turn 1 as well. There the whole of turn 1
        # is paced by the typewriter it streams through; here nothing paces a
        # block of text but the break itself.
        from engine.opening import split_briefing

        description = str(inject.get("description") or
                          "The morning brief carries no new developments.")
        scene_setting, report = split_briefing(description.split("\n"))

        pen.wrap("\n".join(scene_setting), colour=INK)
        pen.blank()
        self.out(pen)

        finish = lambda: self._finish_briefing(report, new_lines, before)  # noqa: E731
        if report:
            self.queue(finish)
        else:
            finish()

    def _finish_briefing(self, report: List[str], new_lines: List[str],
                         before: Dict[str, int]) -> None:
        """The second half of a briefing: the report, then hand back to the player."""
        if report:
            pen = AnsiPen(self.width)
            pen.wrap("\n".join(report), colour=INK)
            pen.blank()
            self.out(pen)

        # Scenario effects are declared as ranges ("10..15") and resolved at
        # apply time, so report the change that actually landed rather than
        # the declaration. Column-aligned, so it stays a chrome pen.
        if self.metrics_visible():
            after = self._metrics_snapshot()
            moved = {k: after[k] - before[k] for k in after if after[k] != before[k]}
            if moved:
                pen = AnsiPen(self.width)
                pen.section("SITUATION SHIFT", DIM)
                for k, v in sorted(moved.items()):
                    pen.raw(f"  {_c(DIM, k.replace('_', ' ').title().ljust(22))}{_delta(k, v)}")
                pen.blank()
                self.out(pen)

        # Some injects carry a mandatory diplomatic encounter. The engine no
        # longer plays it out for us (it used to answer "Thank you." in the
        # player's name — ER-033): the briefing leaves the call live on
        # GameManager, so put the player on the line and hand them the turn
        # only when they have taken it.
        if self._required_call_live():
            encounter = self.gm.active_encounter
            self._call_seen = 0
            pen = AnsiPen(self.width)
            pen.blank()
            pen.section("INCOMING CALL — YOU MUST TAKE THIS", ACCENT)
            pen.wrap("The line is already open. Whatever you type next is "
                     "what you say on the call.", colour=DIM)
            self.out(pen)
            self._render_call(encounter.transcript)
            self.push_state()
            self.set_awaiting(AWAIT_QUESTION)
            return

        # An optional call the player placed themselves also survives a
        # save/load - and their next `call`, whatever country they name,
        # is routed into it. Without this block nothing on screen said the
        # line was still open, so that routing looked like a wrong number.
        encounter = self.gm.active_encounter if self.gm else None
        if encounter and encounter.active and self._call_seen == 0:
            pen = AnsiPen(self.width)
            pen.blank()
            pen.section("LINE STILL OPEN", ACCENT)
            pen.wrap("You were mid-call when the session was saved. A further "
                     "diplomatic message continues this conversation.",
                     colour=DIM)
            self.out(pen)
            self._render_call(encounter.transcript)

        pen = AnsiPen(self.width)
        pen.section("YOUR MOVE", AMBER)
        pen.wrap("Question your advisers, place a diplomatic call, or give the "
                 "order. Whatever you type as a decision is what the Cabinet acts on.",
                 colour=DIM)
        pen.blank()
        self.out(pen, instant=True)

        self.push_state()
        self.set_awaiting(AWAIT_DECISION)

    def _required_call_live(self) -> bool:
        """A scripted mandatory call is live: the player must answer it."""
        encounter = self.gm.active_encounter if self.gm else None
        return bool(encounter and encounter.active
                    and getattr(encounter, "required", False))

    def ask(self, advisor: Optional[str], text: str,
            was_awaiting: str = AWAIT_DECISION) -> None:
        gm = self.gm
        if self._required_call_live():
            self.reject("The President is waiting on the line.", AWAIT_QUESTION)
            return
        question = (text or "").strip()
        if not question:
            self.reject("Empty question.", was_awaiting)
            return

        pen = AnsiPen(self.width)
        pen.section("DISCUSSION", DIM)
        pen.speaker("Prime Minister", question, colour=AMBER)
        self.out(pen)

        if (advisor or "").strip().lower() == ASK_ALL["id"]:
            # The whole room: every seated advisor answers in role. One LLM
            # call per advisor, by design.
            lines = gm.process_question_all(question)
        else:
            # The question router matches on keywords, so naming the adviser
            # in the question itself is how you address one directly.
            cue = _ADVISOR_CUE.get((advisor or "").strip().lower())
            prompt = f"{cue}, {question}" if cue else question
            lines = gm.process_question(prompt)

        pen = AnsiPen(self.width)
        for line in lines:
            if line.startswith("Prime Minister:"):
                continue
            if ":" in line:
                role, said = line.split(":", 1)
                pen.speaker(display_role(role), said.strip())
            elif line.strip():
                pen.wrap(line, colour=INK)
        self.out(pen)

        self.push_state()
        self.set_awaiting(AWAIT_DECISION)

    def call(self, country: Optional[str], text: Optional[str],
             was_awaiting: str = AWAIT_DECISION) -> None:
        gm = self.gm
        message = (text or "").strip()
        encounter = gm.active_encounter
        live = bool(encounter and encounter.active)

        if not live:
            code = (country or "").strip().upper()
            if not code:
                self.reject("No country given for the diplomatic call.",
                            was_awaiting)
                return
            self._call_seen = 0
            result = gm.start_diplomacy(code)
            self._render_call(result["transcript"])
            if not result.get("active"):
                self.push_state()
                self.set_awaiting(AWAIT_DECISION)
                return
            if not message:
                # The two-stage flow: `call france` with nothing to say opens
                # the line, the counterpart speaks first (rendered above),
                # and the player's next input is spoken on the call — the
                # same shape the scripted required call has always had.
                pen = AnsiPen(self.width)
                pen.wrap("The line is open. Whatever you type next is what "
                         "you say on the call; “end” hangs up.",
                         colour=DIM)
                self.out(pen, instant=True)
                self.push_state()
                self.set_awaiting(AWAIT_QUESTION)
                return

        result = gm.process_diplomacy(message)
        if result.get("error"):
            self.error(str(result["error"]))
            self.set_awaiting(AWAIT_DECISION)
            return
        # process_turn/end already append the Prime Minister's own line and
        # the closing assessment to the encounter transcript, so rendering
        # the fresh tail is the whole job.
        self._render_call(result["transcript"])

        if result.get("active"):
            self.push_state()
            self.set_awaiting(AWAIT_QUESTION)
            return

        self._call_seen = 0
        self.push_state()
        self.set_awaiting(AWAIT_DECISION)

    def _render_call(self, transcript: List[str]) -> None:
        """Render only the lines of the call not already sent to the page."""
        fresh = transcript[self._call_seen:]
        self._call_seen = len(transcript)
        pen = AnsiPen(self.width)
        # Entries can themselves be multi-line (the closing assessment is
        # appended as one block), so flatten before rendering.
        for entry in fresh:
            for line in str(entry).split("\n"):
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("==="):
                    pen.blank()
                    pen.section(stripped.strip("= "), ACCENT)
                elif stripped.startswith("SIGNAL:"):
                    pen.wrap(stripped, colour=DANGER)
                    pen.blank()
                elif stripped.startswith("Prime Minister:"):
                    pen.speaker("Prime Minister", stripped.split(":", 1)[1].strip(),
                                colour=AMBER)
                elif ":" in stripped and len(stripped.split(":", 1)[0]) < 48:
                    role, said = stripped.split(":", 1)
                    if role.strip().isupper():
                        # A closing label ("DIPLOMATIC OUTCOME: NEUTRAL"), not a
                        # person — don't dress it up as someone speaking.
                        pen.raw(f"  {_c(DIM, role.strip().title().ljust(22))}"
                                f"{_c(INK, said.strip())}")
                    else:
                        pen.speaker(display_role(role), said.strip())
                else:
                    pen.wrap(stripped, colour=INK)
        pen.blank()
        self.out(pen)

    def decide(self, text: str, was_awaiting: str = AWAIT_DECISION) -> None:
        gm = self.gm
        if self._required_call_live():
            self.reject("The President is waiting on the line.", AWAIT_QUESTION)
            return
        action = (text or "").strip()
        if not action:
            self.reject("Empty decision.", was_awaiting)
            return

        pen = AnsiPen(self.width)
        pen.blank()
        pen.section("PRIME MINISTER'S DECISION", AMBER)
        pen.wrap(action, colour=AMBER)
        pen.blank()
        self.out(pen)

        trace(f"resolve turn {gm.world.turn} start")
        result = gm.resolve_decision(action)
        trace(f"resolve turn {gm.world.turn - 1} done")

        pen = AnsiPen(self.width)
        pen.section("ACTION ASSESSMENT", DIM)
        pen.wrap(result.get("interpretation") or "", colour=INK)
        pen.blank()
        if result.get("reasoning"):
            pen.wrap(str(result["reasoning"]), colour=DIM)
            pen.blank()
        self.out(pen)

        pushback = list(result.get("pushback") or [])
        if pushback:
            pen = AnsiPen(self.width)
            pen.section("ADVISOR CONCERNS", AMBER)
            for item in pushback:
                pen.speaker(display_role(item["role"]), item["concern"],
                            colour=AMBER)
            self.out(pen)

        concerns = list(result.get("critical_concerns") or [])
        if concerns:
            pen = AnsiPen(self.width)
            pen.section("CRITICAL ADVISORY", DANGER)
            for c in concerns:
                pen.speaker(display_role(c["role"]), c["concern"],
                            colour=DANGER)
                if c.get("recommendation"):
                    pen.wrap(f"→ {c['recommendation']}", colour=AMBER,
                             indent="  ", subsequent="    ")
                    pen.blank()
            self.out(pen)

        reactions = result.get("advisor_reactions") or []
        if reactions:
            pen = AnsiPen(self.width)
            pen.section("AROUND THE TABLE", DIM)
            for item in reactions:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    pen.speaker(display_role(item[0]), str(item[1]))
                elif isinstance(item, dict):
                    pen.speaker(display_role(item.get("role", "Adviser")),
                                str(item.get("response", "")))
            self.out(pen)

        intl = result.get("international_reactions") or []
        if intl:
            pen = AnsiPen(self.width)
            pen.section("INTERNATIONAL RESPONSE", DIM)
            for r in intl:
                name = str(r.get("actor_id", "?"))
                support = str(r.get("will_support") or "").lower()
                mark = {"yes": _c(TEAL, "✓"), "conditional": _c(AMBER, "○"),
                        "no": _c(DANGER, "✗")}.get(support, _c(DIM, "·"))
                pen.raw(f"{mark} {_c(SIG, BOLD + name)}")
                pen.wrap(str(r.get("public_response") or ""), colour=INK,
                         indent="  ", subsequent="  ")
                for cond in (r.get("conditions") or []):
                    pen.wrap(f"· {cond}", colour=DIM, indent="  ", subsequent="    ")
                pen.blank()
            self.out(pen)

        effects = result.get("effects") or {}
        if self.metrics_visible() and effects:
            pen = AnsiPen(self.width)
            pen.section("CONSEQUENCES", AMBER)
            for k, v in sorted(effects.items()):
                if isinstance(v, (int, float)):
                    pen.raw(f"  {_c(DIM, k.replace('_', ' ').title().ljust(22))}{_delta(k, int(v))}")
            pen.blank()
            self.out(pen)
        elif not self.metrics_visible():
            self._emit_vibes()

        if result.get("error"):
            self.error(f"Adjudication degraded: {result['error']}", fatal=False)

        self.push_state()

        if gm.is_over():
            self._emit_ending()
            return

        pen = AnsiPen(self.width)
        pen.rule("─", DIM)
        pen.wrap("End of turn. The night passes.", colour=DIM)
        pen.blank()
        self.out(pen)
        self.set_awaiting(AWAIT_CONFIRM)

    def _emit_vibes(self) -> None:
        gm = self.gm
        pen = AnsiPen(self.width)
        pen.section("THE MOOD IN THE ROOM", DIM)
        try:
            for v in gm.narrative_state.get_situation_vibes():
                pen.raw(f"  {_c(DIM, str(v.name).ljust(22))}{_c(INK, str(v.descriptor))}")
        except Exception:
            pass
        pen.blank()
        pen.section("ADVISER ATTITUDES", DIM)
        for row in self._advisor_rows():
            pen.raw("  " + row)
        pen.blank()
        self.out(pen)

    def _advisor_rows(self) -> List[str]:
        """Trust bars for the cabinet (mirrors cli/display_utils)."""
        rows: List[str] = []
        symbols = {"allied": _c(TEAL, "✓"), "neutral": _c(DIM, "○"),
                   "hostile": _c(DANGER, "✗"), "unknown": _c(DIM, "?")}
        for char_id, char in (self.gm.narrative_state.characters or {}).items():
            name = getattr(char, "name", None) or char_id.replace("_", " ").title()
            trust = int(getattr(char, "trust", 50) or 0)
            relationship = str(getattr(char, "relationship", "neutral"))
            level = max(0, min(5, trust // 20))
            bar = _c(AMBER, "█" * level) + _c(DIM, "░" * (5 - level))
            rows.append(f"{_c(SIG, str(name).ljust(30))} {bar} "
                        f"{symbols.get(relationship, _c(DIM, '○'))} "
                        f"{_c(DIM, relationship.upper())}")
        return rows

    def end_turn(self, was_awaiting: str = AWAIT_CONFIRM) -> None:
        gm = self.gm
        if gm.is_over():
            self._emit_ending()
            return
        if was_awaiting in (AWAIT_DECISION, AWAIT_QUESTION):
            # The player pressed "end turn" without giving an order. That is
            # itself a choice, and the Cabinet acts on it.
            self.decide("No new orders. Hold current posture and await developments.")
            return
        self.start_briefing()

    # -- ending ------------------------------------------------------------

    def _emit_ending(self) -> None:
        gm = self.gm
        ending = gm.ending
        debrief = gm.get_debrief_lines()

        verdict_colour = {"victory": TEAL, "partial": AMBER}.get(ending.verdict, DANGER)

        pen = AnsiPen(self.width)
        pen.blank(2)
        pen.rule("═", verdict_colour)
        pen.banner(ending.title, verdict_colour)
        pen.raw(_c(verdict_colour, BOLD +
                   f"{ending.verdict.upper()}  ──  {gm.world.turn - 1} TURNS".center(self.width)))
        pen.rule("═", verdict_colour)
        pen.blank()
        pen.wrap(ending.narrative, colour=INK)
        pen.blank()
        # The debrief's first four lines are its own ASCII header and the
        # narrative, both of which are rendered above.
        for line in debrief[4:]:
            if line.strip() == ending.narrative.strip():
                continue
            pen.raw(_c(DIM, line) if line.strip() else "")
        pen.blank()
        pen.raw(_c(DIM, "CAMPAIGN CLOSED — reload to start another."))
        pen.blank()
        self.out(pen)

        self.emit(
            type="ending",
            verdict=ending.verdict,
            title=ending.title,
            debrief="\n".join(debrief),
            endingId=ending.ending_id,
            narrative=ending.narrative,
            turns=gm.world.turn - 1,
        )
        self.set_awaiting(AWAIT_NONE)

    # -- the prompt --------------------------------------------------------
    #
    # One line in, exactly as the terminal build takes it. Free text is a
    # question to the room; a leading slash is a command. The browser used to
    # offer tabs and dropdowns instead, which was not a smaller interface —
    # it was the command layer missing, with pickers standing in for the six
    # commands nobody had ported.

    def submit(self, text: str, was_awaiting: str = AWAIT_DECISION) -> None:
        """Take one line from the prompt and do whatever the CLI would do."""
        line = (text or "").strip()
        if not line:
            self.set_awaiting(was_awaiting)
            return

        # A live call owns the prompt: everything typed is said on the line,
        # which is what the CLI does once an encounter is open.
        if was_awaiting == AWAIT_QUESTION or self._required_call_live():
            self.call(None, line, was_awaiting)
            return

        # `/decide` on its own armed the order prompt; this is that order.
        if was_awaiting == AWAIT_ORDER and not line.startswith("/"):
            self.decide(line, was_awaiting)
            return

        lowered = line.lower()
        # The whole line, not its first word. cli/main.py tests the entire
        # input against its bare forms, and it has to: "Decide whether we
        # escalate — what does the room think?" is a question, and matching on
        # the first word alone sent it to resolve_decision and burned the turn
        # on a line the player was still thinking out loud with.
        if not line.startswith("/") and lowered not in _BARE_ALIASES:
            # Free text is a question, and "everyone," / "all of you," opens
            # it to the room — the only two openers cli/main.py accepts.
            for opener in ("everyone,", "all of you,"):
                if lowered.startswith(opener):
                    self.ask(ASK_ALL["id"], line[len(opener):].strip(),
                             was_awaiting)
                    return
            self.ask(None, line, was_awaiting)
            return

        verb, _, rest = line.lstrip("/").partition(" ")
        verb, rest = verb.lower(), rest.strip()

        if verb in ("menu", "help"):
            self._cmd_menu(was_awaiting)
        elif verb == "status":
            self._cmd_status(rest, was_awaiting)
        elif verb == "advise":
            self._cmd_advise(rest, was_awaiting)
        elif verb == "askall":
            if not rest:
                self._notice("Usage: /askall <question> — every advisor "
                             "answers in role, one model call each.",
                             was_awaiting)
            else:
                self.ask(ASK_ALL["id"], rest, was_awaiting)
        elif verb == "resources":
            self._cmd_resources(was_awaiting)
        elif verb == "intel":
            self._cmd_intel(rest, was_awaiting)
        elif verb == "call":
            if not rest:
                self._notice("Usage: /call <country> — e.g. /call usa. "
                             "See /menu for who will take a call.",
                             was_awaiting)
            else:
                # The whole argument is the country: "united states" and
                # "russian federation" are both real aliases, and splitting on
                # the first space dialled "united" and said "states" on the
                # line. To speak as you dial, use quotes.
                country, message = _split_call_target(rest)
                self.call(country, message, was_awaiting)
        elif verb in ("decide", "decision") and not rest:
            # Bare only, as in the CLI: cli/main.py matches the whole line
            # against its exact decide forms, so "/decide <order>" is not a
            # decision there — it is answered "Unknown command". Trailing
            # text therefore falls through to the refusal below; taking it
            # as the order resolved a turn on a line the terminal refuses.
            pen = AnsiPen(self.width)
            pen.blank()
            pen.section("YOUR ORDER", AMBER)
            pen.wrap("Write what you are doing, in your own words — a "
                     "paragraph beats a sentence. Say what you are doing, "
                     "what you are not, and who you are telling.",
                     colour=DIM)
            pen.blank()
            self.out(pen, instant=True)
            self.set_awaiting(AWAIT_ORDER)
        elif verb == "save":
            self.save()
            self.set_awaiting(was_awaiting)
        elif verb == "quit":
            pen = AnsiPen(self.width)
            pen.blank()
            pen.wrap("Use ABANDON CAMPAIGN to leave, or /save first — this "
                     "turn's work has not reached a save yet.", colour=AMBER)
            pen.blank()
            self.out(pen, instant=True)
            self.set_awaiting(was_awaiting)
        elif verb in ("theme", "llm", "settings"):
            pen = AnsiPen(self.width)
            pen.blank()
            pen.wrap(f"/{verb} belongs to the terminal build. This one has a "
                     f"single palette, and its model is chosen on the way in.",
                     colour=DIM)
            pen.blank()
            self.out(pen, instant=True)
            self.set_awaiting(was_awaiting)
        else:
            self._notice(f"No such command: /{verb}. Type /menu for the "
                         f"list.", was_awaiting)

    # -- commands ----------------------------------------------------------

    def _notice(self, text: str, was_awaiting: str,
                colour: str = AMBER) -> None:
        """Answer a mistyped command in the transcript, where it was typed.

        ``reject`` raises a banner above the page, which is right for a
        protocol fault the player did not cause. A misremembered command is
        not that: the terminal answers it in line, and so does this.
        """
        pen = AnsiPen(self.width)
        pen.blank()
        pen.wrap(text, colour=colour, indent="  ", subsequent="  ")
        pen.blank()
        self.out(pen, instant=True)
        self.set_awaiting(was_awaiting)

    def _cmd_menu(self, was_awaiting: str) -> None:
        """The room, the switchboard and the commands — the CLI's own menu.

        The terminal's /menu prints three things: who is sitting at the table,
        who will take a call at the current alliance standing, and the command
        list. The picker this build replaced showed the first two on screen at
        all times, so dropping them here would lose them altogether.
        """
        pen = AnsiPen(self.width)
        pen.blank()

        pen.section("THE ROOM", AMBER)
        cue_width = max(len(a["cue"]) for a in ADVISORS)
        for advisor in ADVISORS:
            pen.raw("  " + _c(SIG, advisor["cue"].ljust(cue_width))
                    + "  " + _c(INK, advisor["label"]))
        pen.blank()
        pen.wrap("Open with a cue — “CDS, what are our options?” — and the "
                 "question goes to that seat alone. Open with “everyone,” and "
                 "the whole room answers.", colour=DIM, indent="  ",
                 subsequent="  ")
        pen.blank()

        pen.section("WHO WILL TAKE A CALL", AMBER)
        try:
            channels = list(self.gm.list_diplomatic_channels())
        except Exception:
            channels = []
        if channels:
            for channel in channels:
                code = str(channel.get("country", ""))
                mark = ("LEADER" if channel.get("access") == "leader"
                        else "Diplomat")
                pen.raw("  " + _c(SIG, f"/call {code.lower()}") + "  "
                        + _c(INK, str(channel.get("title", "")))
                        + _c(DIM, f"  ({mark})"))
        else:
            pen.wrap("Nobody. Alliance cohesion is too low for anyone abroad "
                     "to pick up.", colour=DIM, indent="  ", subsequent="  ")
        pen.blank()

        pen.section("COMMANDS", AMBER)
        width = max(len(cmd) for cmd, _ in COMMANDS)
        for cmd, desc in COMMANDS:
            pen.raw("  " + _c(SIG, cmd.ljust(width)) + "  " + _c(DIM, desc))
        pen.blank()
        pen.wrap("Anything else you type is a question to the room.",
                 colour=DIM, indent="  ", subsequent="  ")
        pen.blank()
        self.out(pen, instant=True)
        self.set_awaiting(was_awaiting)

    def _cmd_status(self, arg: str, was_awaiting: str) -> None:
        """Metrics in Classic, the mood and the room everywhere else."""
        gm = self.gm
        if arg.strip().lower().startswith("advis"):
            self._cmd_advisors(was_awaiting)
            return

        pen = AnsiPen(self.width)
        pen.blank()
        if self.metrics_visible():
            pen.section("SITUATION", AMBER)
            metrics = self._metrics_snapshot()
            for key in sorted(metrics):
                pen.raw("  " + _c(DIM, key.replace("_", " ").title().ljust(24))
                        + _c(INK, str(metrics[key])))
            pen.raw("  " + _c(DIM, "Turn".ljust(24)) + _c(INK, str(gm.world.turn)))
        else:
            # Immersive and Emergent do not show the player a number; the CLI
            # answers /status with the mood instead, and so does this.
            pen.section("SITUATION ASSESSMENT", AMBER)
            # VibeLevel is a model, not a string: str() on one prints its
            # repr — `name='Crisis Intensity' level=3 …` — straight at the
            # player. Read the two fields, the way _emit_vibes and push_state
            # already do.
            vibes = list(gm.narrative_state.get_situation_vibes())
            if vibes:
                for vibe in vibes:
                    pen.raw("  " + _c(DIM, str(vibe.name).ljust(22))
                            + _c(INK, str(vibe.descriptor)))
            else:
                pen.wrap("Nothing has moved far enough to read yet.",
                         colour=DIM, indent="  ")
            pen.raw("  " + _c(DIM, "Turn ") + _c(INK, str(gm.world.turn)))
        pen.blank()
        self.out(pen, instant=True)
        self.set_awaiting(was_awaiting)

    def _cmd_advisors(self, was_awaiting: str) -> None:
        """Where the room stands with you."""
        pen = AnsiPen(self.width)
        pen.blank()
        pen.section("ADVISOR ATTITUDES", AMBER)
        advisors = list(self.gm.get_advisors_state())
        if not advisors:
            pen.wrap("Nobody is seated yet.", colour=DIM, indent="  ")
        for advisor in advisors:
            name = display_role(str(advisor.get("name") or advisor.get("role")))
            trust = advisor.get("trust", 50)
            standing = str(advisor.get("relationship") or "professional")
            try:
                bar_len = max(0, min(10, round(int(trust) / 10)))
            except (TypeError, ValueError):
                bar_len = 0
            bar = "█" * bar_len + "·" * (10 - bar_len)
            colour = TEAL if bar_len >= 7 else AMBER if bar_len >= 4 else DANGER
            pen.raw("  " + _c(SIG, name.ljust(30)) + _c(colour, bar)
                    + " " + _c(DIM, f"{trust}  {standing}"))
            note = advisor.get("notes")
            if note:
                pen.wrap(str(note), colour=DIM, indent="    ", subsequent="    ")
        pen.blank()
        self.out(pen, instant=True)
        self.set_awaiting(was_awaiting)

    def _cmd_resources(self, was_awaiting: str) -> None:
        """UK forces and what is left in the magazines."""
        data = self.gm.get_resources()
        pen = AnsiPen(self.width)
        pen.blank()
        pen.section("UK FORCES", AMBER)
        forces = list(data.get("forces") or [])
        if not forces:
            pen.wrap("No force data in this scenario.", colour=DIM, indent="  ")
        for unit in forces:
            name = str(unit.get("id") or "unknown")
            where = str(unit.get("location") or "")
            state = str(unit.get("status") or "")
            pen.raw("  " + _c(SIG, name[:30].ljust(30))
                    + _c(INK, where[:26].ljust(26)) + _c(DIM, state))
            if unit.get("notes"):
                pen.wrap(str(unit["notes"]), colour=DIM,
                         indent="    ", subsequent="    ")
        pen.blank()
        pen.section("STOCKPILES", AMBER)
        stockpiles = list(data.get("stockpiles") or [])
        if not stockpiles:
            pen.wrap("No stockpile data in this scenario.", colour=DIM,
                     indent="  ")
        for item in stockpiles:
            label = str(item.get("name") or "").replace("_", " ").title()
            pen.raw("  " + _c(SIG, label[:34].ljust(34))
                    + _c(INK, str(item.get("count", 0)).rjust(6)) + "  "
                    + _c(DIM, str(item.get("category") or "").replace("_", " ")))
            if item.get("note"):
                pen.wrap(str(item["note"]), colour=DIM,
                         indent="    ", subsequent="    ")
        pen.blank()
        self.out(pen, instant=True)
        self.set_awaiting(was_awaiting)

    def _cmd_intel(self, arg: str, was_awaiting: str) -> None:
        """Who is out there, and — with a country code — what they intend."""
        gm = self.gm
        actors = list(gm.get_intel_actors())
        code = arg.strip().upper()
        pen = AnsiPen(self.width)
        pen.blank()

        if not code:
            pen.section("INTELLIGENCE", AMBER)
            for actor in actors:
                category = str(actor.get("category") or "neutral")
                colour = {"adversary": DANGER, "ally": TEAL}.get(category, INK)
                pen.raw("  " + _c(SIG, str(actor.get("code", "")).ljust(6))
                        + _c(colour, str(actor.get("name", ""))[:40].ljust(40))
                        + _c(DIM, category))
            pen.blank()
            pen.wrap("/intel <code> for a full assessment — e.g. /intel RUS.",
                     colour=DIM, indent="  ")
            pen.blank()
            self.out(pen, instant=True)
            self.set_awaiting(was_awaiting)
            return

        known = {str(a.get("code", "")).upper() for a in actors}
        if code not in known:
            self._notice(f"No intelligence file on {code}. "
                         f"Known: {', '.join(sorted(known)) or 'none'}.",
                         was_awaiting)
            return

        detail = gm.get_intel_detail(code)
        pen.section(f"INTELLIGENCE — {code}", AMBER)
        self._write_assessment(pen, detail)
        pen.blank()
        self.out(pen, instant=True)
        self.set_awaiting(was_awaiting)

    @staticmethod
    def _assessment_lines(detail: Any) -> List[str]:
        """The report body out of ``get_intel_detail``'s wrapper.

        ``generate_actor_detailed_assessment`` returns a finished report —
        rules, a header carrying the actor's name and the turn, then the
        assessment. ``get_intel_detail`` files that under
        ``assessment.raw`` and repeats the name and turn beside it as
        ``actor``/``code``/``confidence``/``last_updated``.

        The terminal prints the report and nothing else, so this digs the
        report back out. Walking the wrapper instead put its field names on
        screen — a bare "Raw" above the rules, and "Last Updated: 3" under
        them, both of which are schema, not intelligence.
        """
        raw: Any = detail
        if isinstance(raw, dict):
            raw = raw.get("assessment", raw)
        if isinstance(raw, dict):
            raw = raw.get("raw", raw)
        if isinstance(raw, str):
            return raw.replace("\r\n", "\n").split("\n")
        if isinstance(raw, list):
            return [str(line) for line in raw]
        return [] if raw in (None, "") else [str(raw)]

    def _write_assessment(self, pen: AnsiPen, detail: Any) -> None:
        """Print the assessment as the engine laid it out.

        Box drawing and rules mean this text was already set for a terminal.
        Re-wrapping it, or bulleting its lines, only breaks what it already
        did correctly.
        """
        lines = self._assessment_lines(detail)
        if not lines:
            pen.wrap("No assessment on file.", colour=DIM, indent="  ",
                     subsequent="  ")
            return
        for line in lines:
            pen.raw(_c(INK, line.rstrip()) if line.strip() else "")

    def _cmd_advise(self, arg: str, was_awaiting: str) -> None:
        """Every seat reports on the situation, each asked its own question."""
        arg = arg.strip().lower()
        if arg and arg != "concise":
            self._notice("Usage: /advise or /advise concise", was_awaiting)
            return
        brevity = ("[Answer in one or two sentences maximum]" if arg == "concise"
                   else "[Please be concise - 3-4 sentences maximum]")

        pen = AnsiPen(self.width)
        pen.blank()
        pen.section("COBRA ADVISORY PANEL", ACCENT)
        self.out(pen, instant=True)

        for _advisor_id, question in _ADVISE_ROUNDS:
            # The questions already open with the seat's own cue ("NSA, what's
            # your assessment…"), which is what routes them. Prefixing the cue
            # again sent "NSA, NSA, what's your assessment…" to the model.
            prompt = f"{question} {brevity}"
            lines = self.gm.process_question(prompt)
            pen = AnsiPen(self.width)
            for line in lines:
                # The instruction is scaffolding, not dialogue. The CLI strips
                # it for the same reason: the prompt is echoed back, and a
                # model that quotes it would put "[Please be concise …]" in
                # front of the player.
                line = line.replace(brevity, "").strip()
                if not line or line.startswith("Prime Minister:"):
                    continue
                if ":" in line:
                    role, said = line.split(":", 1)
                    pen.speaker(display_role(role), said.strip())
                else:
                    pen.wrap(line, colour=INK)
            self.out(pen)

        self.push_state()
        self.set_awaiting(was_awaiting)

    # -- save / load -------------------------------------------------------

    def save(self) -> None:
        gm = self.gm
        data = json.dumps(gm.to_dict("browser"), default=str)
        pen = AnsiPen(self.width)
        pen.raw(_c(DIM, f"[ SAVED — turn {gm.world.turn}, {len(data):,} bytes ]")).blank()
        self.out(pen, instant=True)
        # The protocol leaves the save reply unnamed; emit both spellings so
        # either reading of it works on the page side.
        self.emit(type="save", data=data, turn=gm.world.turn)
        self.emit(type="saved", data=data, turn=gm.world.turn)

    def load(self, data: Any) -> None:
        from engine.game_manager import GameManager

        if isinstance(data, str):
            data = json.loads(data)
        self.gm = GameManager.from_dict(data)
        self._call_seen = 0
        # Loading mid-beat abandons whatever the old campaign had queued;
        # left in place those beats would fire into the resumed one.
        self._paused.clear()

        pen = AnsiPen(self.width)
        pen.blank()
        pen.rule("═", DIM)
        pen.raw(_c(AMBER, BOLD + f"  RESUMED — TURN {self.gm.world.turn}"))
        pen.rule("═", DIM)
        pen.blank()
        self.out(pen, instant=True)

        self.push_state()
        if self.gm.is_over():
            self._emit_ending()
        else:
            self.start_briefing()

    # -- dispatch ----------------------------------------------------------

    NEEDS_GAME = {"decide", "ask", "call", "endTurn", "save", "continue",
                  "input"}

    def handle(self, msg: Dict[str, Any]) -> None:
        """Route one page->worker message. Never raises."""
        kind = str(msg.get("type") or "")
        was_awaiting = self.awaiting
        try:
            if kind in self.NEEDS_GAME and self.gm is None:
                self.error("No game in progress — send newGame first.")
                self.set_awaiting(AWAIT_NONE)
                return

            # endTurn during a pause would run start_briefing() while beats
            # from the last one are still queued, appending a second briefing
            # to a sequence already playing and re-applying its effects. The
            # page disables the control, so this only arrives from a stale
            # click or another client - put it back on the pause.
            #
            # Deliberately narrow. A blanket "reject everything but continue"
            # is worse than the bug: it silently swallows a decision the
            # player typed, and it stalled a full game in test.
            if kind == "endTurn" and was_awaiting == AWAIT_PAUSE and self._paused:
                self.set_awaiting(AWAIT_PAUSE)
                return

            if kind != "setKey":
                self.set_awaiting(AWAIT_NONE)  # busy

            if kind == "newGame":
                self.new_game(msg.get("config"))
            elif kind == "decide":
                self.decide(msg.get("text"), was_awaiting)
            elif kind == "ask":
                self.ask(msg.get("advisor"), msg.get("text"), was_awaiting)
            elif kind == "call":
                self.call(msg.get("country"), msg.get("text"), was_awaiting)
            elif kind == "input":
                # The prompt. One line, parsed the way the terminal parses it.
                self.submit(msg.get("text"), was_awaiting)
            elif kind == "endTurn":
                self.end_turn(was_awaiting)
            elif kind == "continue":
                # `handle` has already marked the session busy. With nothing
                # queued — a double space-press, a stale click — play_next
                # returns without publishing a state, leaving the page on
                # AWAIT_NONE with every control disabled. Put it back where
                # it was. Not an error: pressing space twice is not a fault.
                if was_awaiting == AWAIT_PAUSE and self._paused:
                    self.play_next()
                else:
                    self.set_awaiting(was_awaiting)
            elif kind == "setKey":
                self.set_key(msg.get("key"), msg.get("baseUrl"), msg.get("model"),
                             msg.get("source"))
            elif kind == "save":
                self.save()
                # Saving is not a move: put the player back where they were.
                self.set_awaiting(AWAIT_NONE if self.gm.is_over() else was_awaiting)
            elif kind == "load":
                self.load(msg.get("data"))
            else:
                self.reject(f"Unknown message type: {kind!r}", was_awaiting)
        except Exception as exc:  # noqa: BLE001 - the page must never be stranded
            self.error(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
                       fatal=(kind == "newGame"))
            # Drop whatever the aborted sequence had parked. Recovery hands
            # back an actionable state, so anything left queued would fire on
            # the next `continue` - beats from a turn that never finished,
            # played into one that has moved on.
            self._paused.clear()
            # Leave the player able to act again rather than frozen.
            if self.gm is not None and not self.gm.is_over():
                self.set_awaiting(AWAIT_DECISION)
            else:
                self.set_awaiting(AWAIT_NONE)
        finally:
            self._report_llm_faults()
            self._ensure_actionable(kind)

    def _ensure_actionable(self, kind: str) -> None:
        """Never leave a live campaign with every control disabled.

        ``AWAIT_NONE`` means "busy": ``handle`` sets it on the way in and each
        branch is expected to replace it with the state it hands back to.
        ``play_next`` makes the same assumption of every parked beat. Any path
        that forgets strands the page on STANDBY — no decision, no question,
        no call, and no way out but a reload. That is how a call the game says
        you *must* take becomes one you cannot answer.

        Rather than trusting every branch and every beat to remember, check on
        the way out and hand back whatever the session can actually do. A game
        that is over, or one that has not started, is legitimately idle.
        """
        if kind == "setKey" or self.gm is None:
            return
        if self.awaiting != AWAIT_NONE or self.gm.is_over():
            return
        encounter = self.gm.active_encounter
        if self._paused:
            recovered = AWAIT_PAUSE
        elif encounter is not None and getattr(encounter, "active", False):
            recovered = AWAIT_QUESTION
        else:
            recovered = AWAIT_DECISION
        print(f"[WARN] {kind!r} left the session with nothing to do; "
              f"recovering to {recovered!r}")
        self.set_awaiting(recovered)

    def _report_llm_faults(self) -> None:
        """Say out loud that the live endpoint refused, if it did.

        The router has already fallen back to the offline stand-in by the time
        this runs — the campaign is intact and playable. What it is not is
        what the player thought they were getting, and that is the thing worth
        one clear sentence.
        """
        self._report_parse_health()
        if not _LLM_FAULTS:
            return
        faults = list(_LLM_FAULTS)
        _LLM_FAULTS.clear()
        message = describe_llm_faults(
            faults, self.key_source,
            model=os.environ.get("OPENAI_COMPAT_MODEL", ""))

        pen = AnsiPen(self.width)
        pen.blank()
        pen.rule("─", DANGER)
        for line in textwrap.wrap("!! " + message, self.width - 2):
            pen.raw(_c(DANGER, "  " + line))
        pen.rule("─", DANGER)
        pen.blank()
        self.out(pen, instant=True)

        self.error(message, fatal=False)

    def _report_parse_health(self) -> None:
        """One dim line when this turn's model output needed tolerant defaults.

        The tolerant parsers already recovered what they could; this only
        notes how many fields still fell back, so a decorated-but-dropped
        answer is never invisible.
        """
        from llm import parse_health
        current = parse_health.total()
        delta = current - self._parse_health_seen
        self._parse_health_seen = current
        if delta <= 0:
            return
        # Developer telemetry belongs in the developer console, not the
        # player's transcript - a mechanics readout mid-fiction is an
        # immersion break whatever its diagnostic value. print() surfaces
        # in the worker console for anyone actually debugging.
        print(f"[parse health] {delta} model field(s) defaulted this turn")
