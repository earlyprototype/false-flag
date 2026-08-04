#!/usr/bin/env python3
"""Play the browser build to a real ending in headless Chromium.

Serves ``docs/`` on one port and a cross-origin fake OpenAI-compatible LLM on
another (a genuinely different origin, so the browser runs a real CORS
preflight against it — the same code path OpenRouter takes). Then drives the
worker through the page<->worker contract until the campaign ends, and prints
the evidence.

    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 dev-scripts/verify_play.py

Flags:
    --mode MODE      play mode (default immersive)
    --scenario NAME  fast_start | standard (default fast_start)
    --seed N         RNG seed (default 3)
    --live           also run the turn against the fake LLM endpoint
    --headed         show the browser
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE_PORT = 8788
LLM_PORT = 8789  # different port => different origin => real CORS preflight
CDN_PORT = 8790  # jsDelivr stand-in: cross-origin Pyodide with the same CORS

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization,Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


class FakeLLM(http.server.BaseHTTPRequestHandler):
    """Stand-in for OpenRouter with the CORS posture OpenRouter really sends."""

    hits = 0
    auth_seen = None

    def log_message(self, *a):  # noqa: A003
        pass

    def _reply(self, payload: bytes, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        self._reply(json.dumps({"hits": FakeLLM.hits,
                                "auth": FakeLLM.auth_seen}).encode())

    def do_POST(self):
        FakeLLM.hits += 1
        FakeLLM.auth_seen = self.headers.get("Authorization")
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8", "replace")
        req = json.loads(body) if body else {}
        prompt = (req.get("messages") or [{}])[-1].get("content", "")
        # Answer in the shape the game's parsers expect where it matters, and
        # make it obvious in the transcript that this came off the wire.
        reply = (
            "[LIVE-ENDPOINT] The Cabinet Office notes your direction. "
            "Assessment follows established lines; the risk of miscalculation "
            f"is acknowledged. (prompt_chars={len(prompt)})"
        )
        self._reply(json.dumps({
            "id": "verify-1",
            "choices": [{"message": {"role": "assistant", "content": reply},
                         "finish_reason": "stop"}],
            "usage": {"total_tokens": 42},
        }).encode())


class QuietSite(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # noqa: A003
        pass

    def end_headers(self):
        # Not required for this build (no SharedArrayBuffer), but harmless and
        # mirrors what a cross-origin-isolated deploy would send.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class ThreadedServer(socketserver.ThreadingTCPServer):
    # Chromium opens several sockets in parallel (and preconnects). A
    # single-threaded server accepts them one at a time and can sit on an idle
    # keep-alive connection while the real request waits — which looks exactly
    # like "the worker hung" and is not.
    allow_reuse_address = True
    daemon_threads = True


class CorsStatic(http.server.SimpleHTTPRequestHandler):
    """Serves the vendored runtime with the CORS posture jsDelivr sends."""

    def log_message(self, *a):  # noqa: A003
        pass

    def end_headers(self):
        for k, v in CORS.items():
            self.send_header(k, v)
        super().end_headers()


def serve_cdn_sim():
    root = ROOT / "docs" / "play" / "pyodide"
    if not root.is_dir():
        return None
    srv = ThreadedServer(("127.0.0.1", CDN_PORT),
                         functools.partial(CorsStatic, directory=str(root)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{CDN_PORT}/"


def serve():
    site = ThreadedServer(
        ("127.0.0.1", SITE_PORT),
        functools.partial(QuietSite, directory=str(DOCS)),
    )
    threading.Thread(target=site.serve_forever, daemon=True).start()
    llm = ThreadedServer(("127.0.0.1", LLM_PORT), FakeLLM)
    threading.Thread(target=llm.serve_forever, daemon=True).start()
    return site, llm


DECISIONS = [
    "Order the Type 45 north to escort the cable ships, and brief the House at 0900.",
    "Request NATO Article 4 consultations and put the QRA on ten-minute readiness.",
    "Release the intelligence on the Severomorsk attack to allied capitals only.",
    "Hold the line: no escalation, but move the carrier group within air cover.",
    "Convene COBRA, harden the landing stations, and open a private channel to Moscow.",
    "Reinforce the GIUK gap with P-8 coverage and keep the submarines at sea.",
    "Publicly reaffirm Article 5 and quietly seek an off-ramp through Paris.",
    "Stand down the surge, keep the alliance together, and let the crisis cool.",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="immersive")
    ap.add_argument("--scenario", default="fast_start")
    ap.add_argument("--seed", default="3")
    ap.add_argument("--mystery", action="store_true")
    ap.add_argument("--live", action="store_true",
                    help="drive one turn against the fake cross-origin LLM")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--cdn-sim", action="store_true",
                    help="load Pyodide cross-origin (jsDelivr stand-in) instead "
                         "of from the vendored copy")
    ap.add_argument("--max-turns", type=int, default=25)
    args = ap.parse_args()

    serve()
    page_url = f"http://127.0.0.1:{SITE_PORT}/play/engine-harness.html"
    if args.cdn_sim:
        cdn = serve_cdn_sim()
        if not cdn:
            print("no vendored runtime to serve as a CDN stand-in; run "
                  "dev-scripts/fetch_pyodide.py first", file=sys.stderr)
            return 2
        page_url += "?pyodide=" + cdn
    from playwright.sync_api import sync_playwright

    transcript_chunks: list[str] = []
    report: dict = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ.get(
                "FF_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"),
            headless=not args.headed,
            args=["--no-sandbox"],
        )
        page = browser.new_page()
        page.on("pageerror", lambda e: print("PAGEERROR:", e))
        verbose = os.environ.get("FF_VERBOSE") == "1"
        page.on("console", lambda m: print("CONSOLE:", m.type, m.text)
                if (verbose or m.type in ("error", "warning")) else None)

        t0 = time.time()
        page.goto(page_url)
        page.wait_for_function("window.FF && window.FF.ready === true", timeout=300_000)
        boot_s = time.time() - t0
        report["boot_seconds"] = round(boot_s, 1)
        report["boot_progress"] = page.evaluate(
            "window.FF.booting.map(b => b.pct + '% ' + b.note)")
        report["pyodide_source"] = "cross-origin (CDN stand-in)" if args.cdn_sim \
            else "vendored (same-origin)"

        if args.live:
            page.evaluate(
                """([base]) => window.FF.send({type:'setKey',
                       key:'sk-or-v1-verify-harness-key',
                       baseUrl: base, model:'openai/gpt-4o-mini'})""",
                [f"http://127.0.0.1:{LLM_PORT}/v1"],
            )
            page.wait_for_timeout(400)

        def act(expr: str, arg=None, timeout=300_000):
            """Send one message and wait for the worker to actually answer it.

            Waiting only on ``awaiting !== 'none'`` is not a wait at all after
            the first turn: the condition is already true when the next action
            is sent, so ``wait_for_function`` returns on its first poll without
            a single new worker message — and ``turns_played`` then counts work
            this harness never observed, which is the one thing this script
            exists to produce evidence for.

            ``window.FF.msgs`` is append-only, so its length taken *before* the
            action is a marker: the wait is only satisfied once new worker
            traffic has arrived past that mark AND the session has settled back
            into a state that accepts input (or ended).
            """
            mark = page.evaluate("window.FF.msgs.length")
            if arg is None:
                page.evaluate(expr)
            else:
                page.evaluate(expr, arg)
            page.wait_for_function(
                """([mark]) => window.FF.msgs.length > mark &&
                     (window.FF.awaiting !== 'none' ||
                      window.FF.ending !== null)""",
                arg=[mark], timeout=timeout)

        act(
            """([mode, scenario, seed, mystery]) => {
                 window.FF.send({type:'newGame', config:{
                   scenario, playMode: mode, seed: Number(seed),
                   mysteryMode: mystery}});
               }""",
            [args.mode, args.scenario, args.seed, args.mystery],
        )

        # One question and one diplomatic call, so those paths are exercised
        # by a real game rather than only by unit tests.
        act("""() => window.FF.send({type:'ask',
            advisor:'chief_defence_staff',
            text:'What can we actually put to sea tonight?'})""")
        report["asked_adviser"] = True

        act("""() => window.FF.send({type:'call', country:'USA',
            text:'I need to know whether Article 5 is on the table.'})""")
        report["call_awaiting"] = page.evaluate("window.FF.awaiting")
        act("""() => window.FF.send({type:'call', country:'USA',
            text:'Thank you'})""")

        # Save/load round trip mid-campaign.
        page.evaluate("() => window.FF.send({type:'save'})")
        page.wait_for_function(
            "window.FF.msgs.some(m => m.type === 'save' && m.data)", timeout=60_000)
        report["save_bytes"] = page.evaluate(
            "window.FF.msgs.filter(m => m.type==='save').slice(-1)[0].data.length")

        turns = 0
        while turns < args.max_turns:
            if page.evaluate("window.FF.ending !== null"):
                break
            decision = DECISIONS[turns % len(DECISIONS)]
            act("([t]) => window.FF.send({type:'decide', text:t})", [decision])
            turns += 1
            if page.evaluate("window.FF.ending !== null"):
                break
            act("() => window.FF.send({type:'endTurn'})")

        report["turns_played"] = turns
        report["ending"] = page.evaluate("window.FF.ending")
        report["state"] = page.evaluate("window.FF.state")
        report["errors"] = page.evaluate("window.FF.errors")
        report["output_chunks"] = page.evaluate(
            "window.FF.msgs.filter(m => m.type === 'output').length")
        transcript_chunks = page.evaluate(
            "window.FF.msgs.filter(m => m.type==='output').map(m => m.ansi)")
        report["awaiting_final"] = page.evaluate("window.FF.awaiting")
        report["elapsed_seconds"] = round(time.time() - t0, 1)

        # CONTROL PROBE: does this browser have outbound network at all?
        # Distinguishes "our code is broken" from "the sandbox blocks egress".
        report["control_external_fetch"] = page.evaluate(
            """async () => {
                 try {
                   const r = await fetch('https://api.github.com/zen',
                                         {cache:'no-store'});
                   return 'HTTP ' + r.status;
                 } catch (e) { return 'BLOCKED: ' + e.message; }
               }""")
        report["control_local_cross_origin_fetch"] = page.evaluate(
            """async ([u]) => {
                 try { const r = await fetch(u); return 'HTTP ' + r.status +
                       ' ' + await r.text(); }
                 catch (e) { return 'BLOCKED: ' + e.message; }
               }""", [f"http://127.0.0.1:{LLM_PORT}/hits"])

        browser.close()

    report["llm_endpoint_hits"] = FakeLLM.hits
    report["llm_auth_header_seen"] = (FakeLLM.auth_seen or "")[:24]

    out = ROOT / "dev-scripts" / "play-verify"
    out.mkdir(exist_ok=True)
    (out / "transcript.ansi").write_text("\n".join(transcript_chunks), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== VERIFY REPORT ===")
    print(json.dumps(report, indent=2)[:6000])
    print(f"\nfull ANSI transcript: {out / 'transcript.ansi'} "
          f"({sum(len(c) for c in transcript_chunks):,} chars)")

    ok = bool(report.get("ending")) and not report.get("errors")
    print("\nRESULT:", "PASS — played to a real ending" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
