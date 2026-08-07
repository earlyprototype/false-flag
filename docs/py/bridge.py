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
    """Accumulates ANSI text at a fixed column width."""

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
        """A left-aligned minor heading with a trailing rule."""
        label = f"── {text.strip().upper()} "
        tail = max(0, self.width - len(label))
        return self.raw(_c(colour, label + "─" * tail))

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


def describe_llm_faults(faults: List[str], source: str) -> str:
    """Turn raw driver errors into one sentence a player can act on.

    ``source`` is 'shared' (the owner's key, unlocked with a passphrase),
    'own' (a key the player pasted) or '' (unknown).
    """
    codes = set()
    for fault in faults:
        match = _HTTP_CODE_RE.search(fault)
        if match:
            codes.add(int(match.group(1)))

    if source == "shared":
        whose, subject = "the shared key", "The shared key"
    elif source == "own":
        whose, subject = "your key", "Your key"
    else:
        whose, subject = "the key", "The key"

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
        what = (f"OpenRouter is rate-limiting {whose} (HTTP 429) — too many "
                f"requests, or the allowance on it is spent for now.")
        fix = "Give it a minute and carry on; it may come back on its own."
    elif codes:
        code = sorted(codes)[0]
        what = f"OpenRouter refused the request (HTTP {code})."
        fix = "It may be temporary. Carry on and see."
    else:
        what = (f"The call to OpenRouter failed before it got an answer "
                f"(using {whose}).")
        fix = "That is usually the network. Carry on and see."

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

    def out(self, pen: AnsiPen) -> None:
        body = pen.text()
        if body.strip():
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
        self.out(pen)

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
        from engine.opening import get_opening_scenes

        beats: List[Callable[[], None]] = [
            (lambda s=scene: self._emit_scene(s)) for scene in get_opening_scenes(200)
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
        self.out(pen)

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
            advisors=ADVISORS,
            # Only channels the current alliance standing actually opens.
            contacts=[
                {"code": c["country"], "title": c["title"], "access": c["access"]}
                for c in gm.list_diplomatic_channels()
            ],
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

        pen = AnsiPen(self.width)
        pen.blank()
        pen.banner(
            f"TURN {gm.world.turn} OF {gm.campaign_final_turn}"
            if gm.endings_enabled else f"TURN {gm.world.turn}",
            AMBER)
        pen.blank()

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
        pen = AnsiPen(self.width)
        if report:
            pen.wrap("\n".join(report), colour=INK)
            pen.blank()

        # Scenario effects are declared as ranges ("10..15") and resolved at
        # apply time, so report the change that actually landed rather than
        # the declaration.
        if self.metrics_visible():
            after = self._metrics_snapshot()
            moved = {k: after[k] - before[k] for k in after if after[k] != before[k]}
            if moved:
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

        pen = AnsiPen(self.width)
        pen.section("YOUR MOVE", AMBER)
        pen.wrap("Question your advisers, place a diplomatic call, or give the "
                 "order. Whatever you type as a decision is what the Cabinet acts on.",
                 colour=DIM)
        pen.blank()
        self.out(pen)

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

        # The question router matches on keywords, so naming the adviser in
        # the question itself is how you address one directly.
        cue = _ADVISOR_CUE.get((advisor or "").strip().lower())
        prompt = f"{cue}, {question}" if cue else question

        pen = AnsiPen(self.width)
        pen.section("DISCUSSION", DIM)
        pen.speaker("Prime Minister", question, colour=AMBER)
        self.out(pen)

        lines = gm.process_question(prompt)

        pen = AnsiPen(self.width)
        for line in lines:
            if line.startswith("Prime Minister:"):
                continue
            if ":" in line:
                role, said = line.split(":", 1)
                pen.speaker(role.strip(), said.strip())
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
                        pen.speaker(role.strip(), said.strip())
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

        concerns = list(result.get("critical_concerns") or [])
        if concerns:
            pen = AnsiPen(self.width)
            pen.section("CRITICAL ADVISORY", DANGER)
            for c in concerns:
                pen.speaker(c["role"], c["concern"], colour=DANGER)
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
                    pen.speaker(str(item[0]), str(item[1]))
                elif isinstance(item, dict):
                    pen.speaker(str(item.get("role", "Adviser")),
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

    # -- save / load -------------------------------------------------------

    def save(self) -> None:
        gm = self.gm
        data = json.dumps(gm.to_dict("browser"), default=str)
        pen = AnsiPen(self.width)
        pen.raw(_c(DIM, f"[ SAVED — turn {gm.world.turn}, {len(data):,} bytes ]")).blank()
        self.out(pen)
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
        self.out(pen)

        self.push_state()
        if self.gm.is_over():
            self._emit_ending()
        else:
            self.start_briefing()

    # -- dispatch ----------------------------------------------------------

    NEEDS_GAME = {"decide", "ask", "call", "endTurn", "save", "continue"}

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
        message = describe_llm_faults(faults, self.key_source)

        pen = AnsiPen(self.width)
        pen.blank()
        pen.rule("─", DANGER)
        for line in textwrap.wrap("!! " + message, self.width - 2):
            pen.raw(_c(DANGER, "  " + line))
        pen.rule("─", DANGER)
        pen.blank()
        self.out(pen)

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
        pen = AnsiPen(self.width)
        pen.raw(_c(DIM, f"[ parse health: {delta} model "
                        f"field{'s' if delta != 1 else ''} defaulted this turn ]"))
        self.out(pen)
