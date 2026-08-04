#!/usr/bin/env python3
"""End-to-end proof of the password-protected shared-key path.

Nothing here is mocked except the model endpoint and the key itself. The
encryptor page is driven from ``file://`` exactly as the owner would drive it,
the blob it produces is served to an unmodified ``docs/index.html``, and
the decrypted key is followed all the way to the ``Authorization`` header of a
real HTTP request made by the browser.

    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
        .venv/bin/python dev-scripts/verify_shared_key.py

Eight things are proved, in order:

  1  UNLOCK      the encryptor seals a dummy key; the play page decrypts it
                 with the right passphrase and plays a turn against a fake
                 endpoint that asserts the header carries that exact key.
  2  WRONG       a wrong passphrase fails with one uninformative sentence and
                 leaves no key material behind.
  3  NO LEAK     after a successful unlock, localStorage, sessionStorage and
                 the whole serialised DOM are dumped and searched for the key.
  4  REFUSED     the endpoint is made to answer 401 and then 429 mid-campaign.
                 The page must say so in plain words — not hang, not fail
                 silently, and not quietly serve canned advisors as if
                 nothing had happened.
  5  NO WAY IN   there is no "play without a key" control anywhere on the
                 page, and no campaign can be started without a key. The
                 offline driver survives only as the engine's fallback when
                 a live call is refused, which is what check 4 exercises.
  6  ABSENT      with no shared-key.json served, the passphrase option does
                 not appear at all and the own-key path is the only way in —
                 and it still plays a real turn against the endpoint.
  7  WEAK PASS   the encryptor still refuses a sub-64-bit passphrase, and the
                 override that allows one is off by default, must be ticked
                 deliberately, and is withdrawn by any edit to the passphrase.
  8  NO ORACLE   a blob carrying one extra field — a decryptable, otherwise
                 perfect blob with a "hint" bolted on — is not offered at all.
                 The blob is public, so any field beyond the ciphertext hands
                 out for free something only the passphrase should buy. The
                 encryptor refuses to write one (check 1 asserts its output is
                 exactly the six fields), but the encryptor is not what a
                 hostile or careless blob meets: the page is.

HOW THE OPENROUTER CALL IS INTERCEPTED
--------------------------------------
The play page deliberately offers no way to point the engine at a different
base URL — a page that let a query string choose where the key is sent would
be an exfiltration primitive. So the interception happens below the page, at
the browser: Chromium is launched with

    --host-resolver-rules=MAP openrouter.ai 127.0.0.1:<port>
    --ignore-certificate-errors

and a local TLS server answers as openrouter.ai. The page's code path is
completely unmodified, including the CORS preflight that a real cross-origin
POST with an Authorization header triggers.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import re
import shutil
import socketserver
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ENCRYPTOR = ROOT / "dev-scripts" / "encrypt-key.html"

SITE_PORT = 8791          # docs/, with a shared-key.json injected
BARE_PORT = 8792          # docs/, with no shared-key.json at all
LLM_PORT = 8793           # TLS, answering as openrouter.ai
EXTRA_PORT = 8794         # docs/, with a shared-key.json carrying a 7th field

DUMMY_KEY = "sk-or-v1-DUMMY-FOR-TESTING"
OWN_KEY = "sk-or-v1-A-DIFFERENT-DUMMY-KEY-0000"
WRONG_PASS = "not-the-passphrase-at-all-9876"
# The passphrase the owner asked for. It is a well-known slogan and scores far
# under the 64-bit floor, which is the point: the encryptor must refuse it
# until a human ticks a box saying they have read what that costs.
WEAK_PASS = "slavaUkraini"

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Title,HTTP-Referer",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Max-Age": "600",
}


# ---------------------------------------------------------------- fake model


class FakeOpenRouter(http.server.BaseHTTPRequestHandler):
    """Answers as https://openrouter.ai/api/v1 and records what it was sent.

    ``mode`` switches the whole endpoint between answering normally and
    refusing, so the page's behaviour when a key is exhausted, revoked or
    rate-limited can be observed rather than assumed. It is a class attribute
    because the handler is instantiated per request.
    """

    hits = 0
    mode = "ok"              # 'ok' | '401' | '429'
    auths: ClassVar[list[str]] = []
    paths: ClassVar[list[str]] = []

    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
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
        self.send_header("Content-Length", "0")
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        FakeOpenRouter.hits += 1
        FakeOpenRouter.auths.append(self.headers.get("Authorization") or "")
        FakeOpenRouter.paths.append(self.path)
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        if FakeOpenRouter.mode == "401":
            # OpenRouter's shape for a revoked/limit-reached key.
            self._reply(json.dumps({"error": {
                "code": 401,
                "message": "No auth credentials found"}}).encode(), 401)
            return
        if FakeOpenRouter.mode == "429":
            # Deliberately no Retry-After: the driver would otherwise sleep
            # out the named window before retrying, and this check is about
            # what the page says, not about how patiently it waits.
            self._reply(json.dumps({"error": {
                "code": 429,
                "message": "Rate limit exceeded"}}).encode(), 429)
            return
        self._reply(json.dumps({
            "id": "shared-key-verify-1",
            "choices": [{"message": {"role": "assistant",
                                     "content": "[SHARED-KEY-ENDPOINT] The room "
                                                "notes your direction and the risk "
                                                "of miscalculation."},
                         "finish_reason": "stop"}],
            "usage": {"total_tokens": 21},
        }).encode())


class ThreadedServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def make_cert(tmp: Path) -> tuple[Path, Path]:
    key, crt = tmp / "fake.key", tmp / "fake.crt"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(crt), "-days", "2",
         "-subj", "/CN=openrouter.ai",
         "-addext", "subjectAltName=DNS:openrouter.ai"],
        check=True, capture_output=True)
    return key, crt


def serve_llm(tmp: Path):
    key, crt = make_cert(tmp)
    srv = ThreadedServer(("127.0.0.1", LLM_PORT), FakeOpenRouter)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(crt), keyfile=str(key))
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ------------------------------------------------------------------- the site


class SiteWithBlob(http.server.SimpleHTTPRequestHandler):
    """docs/, plus one file that is never written to the working tree.

    The blob is held in memory so this script can never leave a
    ``docs/shared-key.json`` behind — that file is the owner's to create,
    with his own key, on his own machine. The interception is also
    unconditional in the other direction: if the owner's real blob is sitting
    in the working tree, this handler answers ``/shared-key.json`` from memory
    (or 404s) and never serves, reads or opens it.
    """

    blob: bytes | None = None

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/shared-key.json":
            if self.blob is None:
                self.send_error(404, "Not Found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(self.blob)))
            self.end_headers()
            self.wfile.write(self.blob)
            return
        super().do_GET()


def serve_site(port: int, blob: bytes | None):
    handler = type("H", (SiteWithBlob,), {"blob": blob})
    srv = ThreadedServer(("127.0.0.1", port),
                         functools.partial(handler, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ----------------------------------------------------------------- the checks


def chromium_path() -> str:
    explicit = os.environ.get("FF_CHROMIUM")
    if explicit:
        return explicit
    base = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    for name in sorted((p.name for p in base.glob("chromium-*")), reverse=True):
        # Playwright renamed the directory to chrome-linux64 in newer builds;
        # both layouts turn up under the same PLAYWRIGHT_BROWSERS_PATH.
        for layout in ("chrome-linux", "chrome-linux64"):
            exe = base / name / layout / "chrome"
            if exe.exists():
                return str(exe)
    raise SystemExit("no Chromium under PLAYWRIGHT_BROWSERS_PATH")


BLOB_FIELDS = {"v", "kdf", "iterations", "salt", "iv", "ct"}


def seal_with_the_encryptor(browser, report: dict, failures: list[str]) -> tuple[str, str]:
    """Drive dev-scripts/encrypt-key.html from file:// and take the blob."""
    page = browser.new_page()
    page.on("pageerror", lambda e: report.setdefault("encryptor_errors", []).append(str(e)))
    page.goto(ENCRYPTOR.as_uri())

    report["encryptor_wordlist"] = page.evaluate("window.FF_SEAL.words")
    report["encryptor_bits_per_word"] = round(page.evaluate("window.FF_SEAL.wordBits"), 2)

    # Weak passphrases must be refused, and the refusal must be the reason the
    # Encrypt button is dead.
    page.fill("#keyIn", DUMMY_KEY)
    weak = []
    for bad in ("password", "hunter2", "correct horse", "aaaaaaaaaaaaaaaaaaaaaaaa",
                "operation-tuman"):
        page.fill("#phraseIn", bad)
        weak.append({
            "passphrase": bad,
            "bits": round(page.evaluate("window.FF_SEAL.estimateBits(document.getElementById('phraseIn').value)"), 1),
            "encrypt_enabled": page.is_enabled("#doEncrypt"),
            "note": page.inner_text("#gateNote"),
        })
    report["weak_passphrases_refused"] = weak
    # Recording the refusal is not enough: assert it. The key is already in
    # #keyIn, so the only thing that can be holding the gate shut is the
    # passphrase — check both that the estimator rates it below the floor and
    # that the gate is actually shut.
    accepted = [w["passphrase"] for w in weak if w["encrypt_enabled"]]
    if accepted:
        failures.append("the encryptor offered to encrypt under weak "
                        "passphrases: " + json.dumps(accepted))
    overrated = [w["passphrase"] for w in weak if w["bits"] >= 64]
    if overrated:
        failures.append("weak passphrases scored at or above the 64-bit "
                        "floor: " + json.dumps(overrated))
    page.fill("#phraseIn", "")

    page.click("#genWords")
    passphrase = page.input_value("#phraseOut")
    # A generated passphrase must never be shown the override at all.
    report["weak_box_hidden_for_generated_passphrase"] = page.is_hidden("#weakBox")
    if not report["weak_box_hidden_for_generated_passphrase"]:
        failures.append("the weak-passphrase override was offered for a "
                        "generated passphrase")
    report["generated_passphrase_words"] = len(passphrase.split("-"))
    report["generated_passphrase_bits"] = page.inner_text("#phraseBits")
    # The generated phrase is a test fixture, not a secret; print it so the
    # run is reproducible from the log.
    report["generated_passphrase"] = passphrase

    page.click("#doEncrypt")
    page.wait_for_selector("#result:not([hidden])", timeout=30_000)
    report["encryptor_verdict"] = page.inner_text("#verifyNote").strip()
    blob = page.input_value("#blobOut")
    report["blob"] = json.loads(blob)
    page.close()

    b = report["blob"]
    assert b["v"] == 1 and b["kdf"] == "PBKDF2-SHA256", b
    assert b["iterations"] >= 600_000, b["iterations"]
    assert len(_b64len(b["salt"])) == 16, "salt must be 16 bytes"
    assert len(_b64len(b["iv"])) == 12, "iv must be 12 bytes"
    # ciphertext = plaintext + 16-byte GCM tag
    assert len(_b64len(b["ct"])) == len(DUMMY_KEY) + 16, "ct length"
    assert DUMMY_KEY not in blob and passphrase not in blob, "blob leaks plaintext"
    # An allowlist, not a blacklist: any field beyond these six is a potential
    # wrong-passphrase oracle, whatever it happens to be called.
    if set(b) != BLOB_FIELDS:
        failures.append(
            "the blob's fields must be exactly "
            f"{sorted(BLOB_FIELDS)}, got {sorted(b)} — anything else is a "
            "potential wrong-passphrase oracle")
    return passphrase, blob


def check_weak_override(browser, report: dict, failures: list[str]) -> None:
    """The sub-threshold passphrase must cost a deliberate, specific tick.

    Nothing here writes a blob anywhere: the encryptor is driven, the result
    is read out of the page's own textarea, and the page is closed.
    """
    page = browser.new_page()
    page.on("pageerror", lambda e: report.setdefault("encryptor_errors", []).append(str(e)))
    page.goto(ENCRYPTOR.as_uri())
    page.fill("#keyIn", DUMMY_KEY)
    page.fill("#phraseIn", WEAK_PASS)

    out: dict = {
        "passphrase": WEAK_PASS,
        "bits": round(page.evaluate(
            "window.FF_SEAL.estimateBits(document.getElementById('phraseIn').value)"), 1),
        "floor_bits": page.evaluate("window.FF_SEAL.minBits"),
        "override_visible": page.is_visible("#weakBox"),
        "override_checked_by_default": page.is_checked("#weakOk"),
        "encrypt_enabled_before_tick": page.is_enabled("#doEncrypt"),
        "gate_note_before_tick": page.inner_text("#gateNote").strip(),
        "warning_text": page.inner_text("#weakBox").strip(),
    }

    page.check("#weakOk")
    out["encrypt_enabled_after_tick"] = page.is_enabled("#doEncrypt")
    out["gate_note_after_tick"] = page.inner_text("#gateNote").strip()

    # Editing the passphrase must withdraw the consent given for the old one.
    page.fill("#phraseIn", WEAK_PASS + "x")
    out["override_checked_after_edit"] = page.is_checked("#weakOk")
    out["encrypt_enabled_after_edit"] = page.is_enabled("#doEncrypt")

    # And it really does seal, once accepted: round-trip through the page's
    # own verification step. The blob is read and dropped, never written.
    page.fill("#phraseIn", WEAK_PASS)
    page.check("#weakOk")
    page.click("#doEncrypt")
    page.wait_for_selector("#result:not([hidden])", timeout=60_000)
    blob = json.loads(page.input_value("#blobOut"))
    out["verdict"] = page.inner_text("#verifyNote").strip()
    out["blob_iterations"] = blob["iterations"]
    out["blob_fields"] = sorted(blob)
    page.close()
    report["weak_passphrase_override"] = out

    if out["bits"] >= out["floor_bits"]:
        failures.append(f"{WEAK_PASS!r} scored at or above the floor — the "
                        "estimator is flattering it")
    if out["override_checked_by_default"]:
        failures.append("the weak-passphrase override is ticked by default")
    if out["encrypt_enabled_before_tick"]:
        failures.append("a sub-threshold passphrase encrypted without the "
                        "override being ticked")
    if not out["override_visible"]:
        failures.append("the weak-passphrase warning was not shown")
    if not out["encrypt_enabled_after_tick"]:
        failures.append("ticking the override did not unlock Encrypt")
    if out["override_checked_after_edit"] or out["encrypt_enabled_after_edit"]:
        failures.append("editing the passphrase kept the old consent")
    if blob["iterations"] < 600_000:
        failures.append("the override weakened the KDF as well")
    if sorted(blob) != sorted(BLOB_FIELDS):
        failures.append(f"the override changed the blob shape: {sorted(blob)}")


def _b64len(s: str) -> bytes:
    import base64
    return base64.b64decode(s)


def leak_scan(page, needles: dict[str, str]) -> dict:
    """Dump every place a key could hide and search all of it."""
    dump = page.evaluate("""() => {
      const ls = {}, ss = {};
      try { for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i); ls[k] = localStorage.getItem(k); } } catch (e) {}
      try { for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i); ss[k] = sessionStorage.getItem(k); } } catch (e) {}
      const inputs = [...document.querySelectorAll('input,textarea')]
        .map(n => n.id + '=' + n.value);
      // FF_PLAY is the page's own automation surface and is supposed to expose
      // booleans and screen text only. Read every property it exposes (its
      // getters included) and call its zero-argument accessors, so a
      // regression that hung the key off it is caught by value and not merely
      // noted by name.
      const ff = {};
      try {
        const src = window.FF_PLAY || {};
        // Own properties, plus anything on a prototype of its own — but stop
        // at Object.prototype, whose methods are not FF_PLAY's surface.
        const names = new Set(Object.getOwnPropertyNames(src));
        for (let proto = Object.getPrototypeOf(src);
             proto && proto !== Object.prototype;
             proto = Object.getPrototypeOf(proto)) {
          Object.getOwnPropertyNames(proto).forEach(n => names.add(n));
        }
        names.delete('constructor');
        for (const k of names) {
          let v;
          try { v = src[k]; } catch (e) { v = '<<threw>>'; }
          if (typeof v === 'function') {
            try { v = v.length === 0 ? v.call(src) : '<<takes arguments>>'; }
            catch (e) { v = '<<threw>>'; }
          }
          try { ff[k] = JSON.parse(JSON.stringify(v === undefined ? null : v)); }
          catch (e) { ff[k] = String(v); }
        }
      } catch (e) {}
      return {
        localStorage: ls,
        sessionStorage: ss,
        cookie: document.cookie,
        dom: document.documentElement.outerHTML,
        inputValues: inputs,
        ffPlay: ff,
      };
    }""")
    haystacks = {
        "localStorage": json.dumps(dump["localStorage"]),
        "sessionStorage": json.dumps(dump["sessionStorage"]),
        "cookies": dump["cookie"],
        "DOM": dump["dom"],
        "input values": " ".join(dump["inputValues"]),
        "FF_PLAY": json.dumps(dump["ffPlay"]),
    }
    found = {}
    for what, needle in needles.items():
        hits = [name for name, hay in haystacks.items() if needle and needle in hay]
        found[what] = hits
    return {
        "localStorage_keys": sorted(dump["localStorage"]),
        "localStorage": dump["localStorage"],
        "sessionStorage": dump["sessionStorage"],
        "cookies": dump["cookie"],
        "dom_bytes": len(dump["dom"]),
        "input_values": dump["inputValues"],
        # Scanned in full above; abbreviated here so the transcript FF_PLAY.text()
        # returns does not swamp the report.
        "ff_play": {k: (v[:120] + f"…<{len(v)} chars>" if isinstance(v, str)
                        and len(v) > 120 else v)
                    for k, v in dump["ffPlay"].items()},
        "leaks": found,
    }


def wait_awaiting(page, kinds, timeout=420_000):
    page.wait_for_function(
        "([k]) => window.FF_PLAY && k.indexOf(window.FF_PLAY.awaiting) !== -1",
        arg=[list(kinds)], timeout=timeout)


def send_decision(page, text, timeout=420_000):
    """Type a decision and wait for the turn to actually resolve.

    ``FF_PLAY.awaiting`` still reads 'decision' for the instant between the
    click and the worker's first reply, so waiting on the state alone returns
    before any work has happened — which is precisely the thing this script
    exists to observe. Wait for the transcript to have grown *and* the session
    to have settled into 'confirm' (or ended).
    """
    before = page.evaluate("window.FF_PLAY.text().length")
    page.fill("#decideText", text)
    page.click("#sendDecide")
    page.wait_for_function(
        """([n]) => window.FF_PLAY.text().length > n &&
             (window.FF_PLAY.awaiting === 'confirm' || window.FF_PLAY.over)""",
        arg=[before], timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--skip-play", action="store_true",
                    help="skip the two engine boots (gate checks only)")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    report: dict = {}
    failures: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="ff-sharedkey-"))
    serve_llm(tmp)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chromium_path(),
            headless=not args.headed,
            args=["--no-sandbox",
                  "--ignore-certificate-errors",
                  # Chromium reads https_proxy from the environment on Linux,
                  # and proxy selection happens BEFORE name resolution — so a
                  # proxy in the environment silently defeats the MAP rule and
                  # the request leaves for the real openrouter.ai. Go direct.
                  "--no-proxy-server",
                  f"--host-resolver-rules=MAP openrouter.ai 127.0.0.1:{LLM_PORT}"],
        )

        # ---------------------------------------------------- 1. seal a key
        passphrase, blob = seal_with_the_encryptor(browser, report, failures)
        # ------------------------------- 7. the weak-passphrase override
        # (run here, while the encryptor is the only thing in flight)
        check_weak_override(browser, report, failures)
        serve_site(SITE_PORT, blob.encode())
        serve_site(BARE_PORT, None)
        # Check 8's blob: byte-for-byte the good one, plus a seventh field.
        # It would decrypt perfectly — that is the point. The page must refuse
        # to offer it because of the field, not because of the crypto.
        over_full = dict(json.loads(blob))
        over_full["hint"] = "the passphrase is three words about the weather"
        serve_site(EXTRA_PORT, json.dumps(over_full).encode())

        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page()
        console: list[str] = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
        page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))

        page.goto(f"http://127.0.0.1:{SITE_PORT}/index.html")
        page.wait_for_function("window.FF_PLAY && window.FF_PLAY.sharedOffered === true",
                               timeout=15_000)
        report["shared_panel_visible"] = page.is_visible("#sharedPanel")
        report["shared_panel_heading"] = page.inner_text("#sharedPanel .cap").strip()

        # ------------------------------------------- 2. a wrong passphrase
        page.fill("#sharedPass", WRONG_PASS)
        page.click("#unlockShared")
        page.wait_for_function(
            "() => document.getElementById('sharedState').textContent"
            ".indexOf('Working') === -1", timeout=60_000)
        report["wrong_passphrase_message"] = page.inner_text("#sharedState").strip()
        report["wrong_passphrase_unlocked"] = page.evaluate("window.FF_PLAY.sharedUnlocked")
        report["wrong_passphrase_start_button_hidden"] = page.is_hidden("#startShared")
        # The wrong passphrase is deliberately left in the field so a typo can
        # be corrected, so it is not part of the leak assertion — it is not key
        # material, and an input's value is never serialised into the DOM.
        report["after_wrong_passphrase"] = leak_scan(page, {
            "the dummy key": DUMMY_KEY,
            "the real passphrase": passphrase,
        })
        if report["wrong_passphrase_unlocked"]:
            failures.append("a wrong passphrase unlocked the key")
        if report["wrong_passphrase_message"] != "That passphrase did not work.":
            failures.append("the wrong-passphrase message is not the flat one")
        if not report["wrong_passphrase_start_button_hidden"]:
            failures.append("#startShared was exposed after a failed unlock")
        if any(report["after_wrong_passphrase"]["leaks"].values()):
            failures.append("material found after a failed unlock: " +
                            json.dumps(report["after_wrong_passphrase"]["leaks"]))

        # -------------------------------------------- 3. the right one, and
        #                                                  a full leak scan
        page.fill("#sharedPass", passphrase)
        page.click("#unlockShared")
        page.wait_for_function("window.FF_PLAY.sharedUnlocked === true", timeout=90_000)
        report["unlock_message"] = page.inner_text("#sharedState").strip()
        report["start_shared_visible"] = page.is_visible("#startShared")
        report["start_shared_is_primary"] = page.evaluate(
            "document.getElementById('startShared').classList.contains('primary')")
        report["remember_checkbox_in_shared_panel"] = page.evaluate(
            "document.querySelectorAll('#sharedPanel input[type=checkbox]').length")
        report["after_unlock"] = leak_scan(page, {
            "the dummy key": DUMMY_KEY,
            "a fragment of the dummy key": DUMMY_KEY[:16],
            "the passphrase": passphrase,
        })
        if any(report["after_unlock"]["leaks"].values()):
            failures.append("KEY MATERIAL LEAKED after unlock: " +
                            json.dumps(report["after_unlock"]["leaks"]))
        if report["remember_checkbox_in_shared_panel"] != 0:
            failures.append("the shared panel offers a remember-me")

        # ------------------------------- 4. play a turn on the shared key
        if not args.skip_play:
            t0 = time.time()
            page.click("#startShared")
            wait_awaiting(page, ["decision"])
            report["boot_seconds_shared"] = round(time.time() - t0, 1)
            report["worker_used"] = page.evaluate("window.FF_PLAY.worker")
            report["provider_banner"] = "\n".join(
                line for line in page.evaluate("window.FF_PLAY.text()").splitlines()
                if "MODEL" in line or "OFFLINE" in line)
            send_decision(page,
                          "Order the Type 45 north to escort the cable ships "
                          "and brief the House at 0900.")
            report["llm_hits"] = FakeOpenRouter.hits
            report["llm_paths_seen"] = sorted(set(FakeOpenRouter.paths))[:3]
            report["llm_auth_headers_seen"] = sorted(set(FakeOpenRouter.auths))
            report["transcript_mentions_live_endpoint"] = (
                "[SHARED-KEY-ENDPOINT]" in page.evaluate("window.FF_PLAY.text()"))
            if FakeOpenRouter.hits == 0:
                failures.append("the shared key never reached an endpoint")
            expected = f"Bearer {DUMMY_KEY}"
            if set(FakeOpenRouter.auths) != {expected}:
                failures.append(
                    f"Authorization header was {FakeOpenRouter.auths!r}, "
                    f"expected only {expected!r}")
            # After a turn has actually run, look again.
            report["after_playing"] = leak_scan(page, {
                "the dummy key": DUMMY_KEY,
                "the passphrase": passphrase,
            })
            if any(report["after_playing"]["leaks"].values()):
                failures.append("KEY MATERIAL LEAKED after playing: " +
                                json.dumps(report["after_playing"]["leaks"]))

        # ------------------- 5. the endpoint refuses: 401, then 429
        #
        # This is the path that matters most for a shared key: it is spent
        # from by strangers, so it WILL eventually be revoked, exhausted or
        # throttled. When that happens the engine falls back to the offline
        # driver (llm/router.py does this so a turn never dies half-written)
        # — and a page that let that happen silently would be lying, because
        # the advisors have stopped reading what the player wrote.
        if not args.skip_play:
            for code, must_say in (("401", ("rejected", "spend limit")),
                                   ("429", ("rate-limit", "429"))):
                page.evaluate("document.getElementById('alerts').innerHTML = ''")
                FakeOpenRouter.mode = code
                hits_before = FakeOpenRouter.hits
                t0 = time.time()
                page.click("#endTurn")
                wait_awaiting(page, ["decision", "confirm"])
                send_decision(page,
                              "Put the Typhoons on airborne alert and tell "
                              "Oslo before the press hear it.")
                alerts = page.inner_text("#alerts").strip()
                screen = page.evaluate("window.FF_PLAY.text()")
                report[f"refused_{code}"] = {
                    "seconds": round(time.time() - t0, 1),
                    "endpoint_calls": FakeOpenRouter.hits - hits_before,
                    "alert_text": alerts,
                    "in_transcript": any(
                        must in screen for must in must_say),
                    "awaiting_after": page.evaluate("window.FF_PLAY.awaiting"),
                    # The turn resolved, so Decide is correctly disabled until
                    # the player acknowledges: "can go on" means Continue is
                    # there, or the campaign has genuinely ended.
                    "can_go_on": page.is_visible("#endTurn")
                                 or page.evaluate("window.FF_PLAY.over"),
                }
                if not report[f"refused_{code}"]["can_go_on"]:
                    failures.append(
                        f"after a {code} there was no way to continue the turn")
                if not alerts:
                    failures.append(
                        f"the page said nothing at all when the endpoint "
                        f"answered {code} — a silent fallback to canned "
                        f"advisors is exactly what must not happen")
                elif not any(must.lower() in alerts.lower() for must in must_say):
                    failures.append(
                        f"the {code} message does not say what went wrong "
                        f"in plain words (wanted one of {must_say!r}): "
                        f"{alerts!r}")
                if "offline stand-in" not in alerts:
                    failures.append(
                        f"the {code} message does not say the advisors fell "
                        f"back to the offline stand-in: {alerts!r}")
                if report[f"refused_{code}"]["awaiting_after"] == "none":
                    failures.append(
                        f"the page stranded the player after a {code} — "
                        f"nothing is accepted and there is no way on")
            FakeOpenRouter.mode = "ok"

        report["console_mentions_key"] = [
            line for line in console
            if DUMMY_KEY in line or passphrase in line
        ]
        report["console_tail"] = console[-70:]
        if report["console_mentions_key"]:
            failures.append("the key or passphrase was logged to the console")
        ctx.close()

        # -------------------------- 6. no blob: the passphrase option must
        #                               not exist, and the own-key path must
        #                               then be the only way in
        ctx2 = browser.new_context(ignore_https_errors=True)
        bare = ctx2.new_page()
        bare.goto(f"http://127.0.0.1:{BARE_PORT}/index.html")
        bare.wait_for_function("window.FF_PLAY !== undefined", timeout=15_000)
        bare.wait_for_timeout(1500)   # let the 404 probe resolve
        report["absent_shared_offered"] = bare.evaluate("window.FF_PLAY.sharedOffered")
        report["absent_panel_visible"] = bare.is_visible("#sharedPanel")
        report["absent_start_shared_visible"] = bare.is_visible("#startShared")

        # There must be no way to start a campaign without a key — the
        # removed control by id, and any button still offering it by name.
        report["absent_startNoKey_exists"] = bare.evaluate(
            "document.getElementById('startNoKey') !== null")
        report["absent_start_buttons_before_key"] = bare.evaluate(
            """() => [...document.querySelectorAll('#gate button')]
                 .filter(b => b.offsetParent !== null)
                 .map(b => b.textContent.trim())""")
        report["absent_start_hint"] = bare.inner_text("#startHint").strip()
        report["absent_gate_mentions_playing_without_a_key"] = bool(re.search(
            r"without (?:a|using it) key|play without",
            bare.inner_text("#gate"), re.I))
        if report["absent_startNoKey_exists"]:
            failures.append("#startNoKey still exists")
        if report["absent_gate_mentions_playing_without_a_key"]:
            failures.append("the gate still offers playing without a key")

        # own-key path, unchanged
        report["absent_default_keystate"] = bare.inner_text("#keystate").strip()
        bare.fill("#apikey", OWN_KEY)
        bare.click("#useKey")
        report["absent_keystate_after_own_key"] = bare.inner_text("#keystate").strip()
        report["absent_startWithKey_visible"] = bare.is_visible("#startWithKey")
        report["absent_startWithKey_primary"] = bare.evaluate(
            "document.getElementById('startWithKey').classList.contains('primary')")
        report["absent_apikey_field_cleared"] = bare.input_value("#apikey") == ""
        # "Remember it" was off, so nothing may have been written.
        report["absent_localStorage_after_own_key"] = bare.evaluate(
            "() => Object.fromEntries(Object.entries(localStorage))")
        bare.click("text=Forget it")
        report["absent_keystate_after_forget"] = bare.inner_text("#keystate").strip()
        report["absent_start_buttons_after_forget"] = bare.evaluate(
            """() => [...document.querySelectorAll('#gate button')]
                 .filter(b => b.offsetParent !== null)
                 .map(b => b.textContent.trim())""")
        if any("without" in t.lower()
               for t in report["absent_start_buttons_after_forget"]):
            failures.append("a no-key start button reappeared after Forget it")

        if report["absent_shared_offered"] or report["absent_panel_visible"] \
                or report["absent_start_shared_visible"]:
            failures.append("the shared-key option appeared with no blob present")
        if not report["absent_startWithKey_visible"]:
            failures.append("the own-key path broke")
        if OWN_KEY in json.dumps(report["absent_localStorage_after_own_key"]):
            failures.append("an unremembered own key was written to localStorage")

        # The own-key path is now the only way in on a fork, so prove it
        # end to end rather than merely proving the button appears: set the
        # key again, play a turn, and check the endpoint saw THAT key.
        if not args.skip_play:
            bare.fill("#apikey", OWN_KEY)
            bare.click("#useKey")
            hits_before = FakeOpenRouter.hits
            auths_before = len(FakeOpenRouter.auths)
            t0 = time.time()
            bare.click("#startWithKey")
            wait_awaiting(bare, ["decision"])
            report["absent_ownkey_boot_seconds"] = round(time.time() - t0, 1)
            send_decision(bare, "Hold the line and convene COBRA at 0700.")
            own_auths = sorted(set(FakeOpenRouter.auths[auths_before:]))
            report["absent_ownkey_llm_hits"] = FakeOpenRouter.hits - hits_before
            report["absent_ownkey_auth_headers_seen"] = own_auths
            report["absent_ownkey_awaiting"] = bare.evaluate("window.FF_PLAY.awaiting")
            if report["absent_ownkey_llm_hits"] == 0:
                failures.append("the own key never reached an endpoint")
            if own_auths != [f"Bearer {OWN_KEY}"]:
                failures.append(
                    f"the own-key run sent {own_auths!r}, expected only "
                    f"Bearer {OWN_KEY!r}")

        ctx2.close()

        # ----------------- 8. an over-full blob is not offered at all
        #
        # The "no oracle in the blob" property has to be enforced where the
        # blob is consumed. Anything the file carries beyond the six fields
        # is readable by everyone who can read the file, so a `hint` — or a
        # verifier, or a key prefix, or a checksum — gives away for free
        # something only the passphrase is supposed to buy. This blob is
        # otherwise flawless: same ciphertext, same salt, same iterations,
        # and the real passphrase would open it.
        ctx3 = browser.new_context(ignore_https_errors=True)
        extra = ctx3.new_page()
        extra.goto(f"http://127.0.0.1:{EXTRA_PORT}/index.html")
        extra.wait_for_function("window.FF_PLAY !== undefined", timeout=15_000)
        extra.wait_for_timeout(1500)   # let the probe fetch and reject it
        report["extra_field_blob"] = {
            "served": sorted(over_full),
            "shared_offered": extra.evaluate("window.FF_PLAY.sharedOffered"),
            "panel_visible": extra.is_visible("#sharedPanel"),
            "start_shared_visible": extra.is_visible("#startShared"),
            "start_hint": extra.inner_text("#startHint").strip(),
            # The own-key panel is only demoted to "OR: ..." when a shared key
            # is on offer. Still being the primary way in is the page saying,
            # in its own layout, that it saw no usable blob.
            "own_panel_demoted": extra.evaluate(
                "document.getElementById('ownPanel')"
                ".classList.contains('secondary')"),
        }
        # Nothing may be derived from it either: an unlock attempt must be
        # impossible because the panel was never shown.
        if report["extra_field_blob"]["shared_offered"]:
            failures.append(
                "a blob with an extra field was accepted and offered — the "
                "'no oracle in the blob' rule is enforced only in the "
                "encryptor, which is not what a hostile blob meets")
        if report["extra_field_blob"]["panel_visible"] \
                or report["extra_field_blob"]["start_shared_visible"]:
            failures.append(
                "the passphrase panel appeared for a blob with an extra field")
        if report["extra_field_blob"]["own_panel_demoted"]:
            failures.append(
                "the page rearranged itself around a blob it must have rejected")
        ctx3.close()

        browser.close()

    shutil.rmtree(tmp, ignore_errors=True)

    out = ROOT / "dev-scripts" / "play-verify"
    out.mkdir(exist_ok=True)
    (out / "shared-key-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== SHARED KEY VERIFY ===")
    print(json.dumps(report, indent=2, default=str)[:14000])
    print(f"\nfull report: {out / 'shared-key-report.json'}")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
    print("\nRESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
