#!/usr/bin/env python3
"""End-to-end proof of the password-protected shared-key path.

Nothing here is mocked except the model endpoint and the key itself. The
encryptor page is driven from ``file://`` exactly as the owner would drive it,
the blob it produces is served to an unmodified ``docs/play/index.html``, and
the decrypted key is followed all the way to the ``Authorization`` header of a
real HTTP request made by the browser.

    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
        .venv/bin/python dev-scripts/verify_shared_key.py

Four things are proved, in order:

  1  UNLOCK      the encryptor seals a dummy key; the play page decrypts it
                 with the right passphrase and plays a turn against a fake
                 endpoint that asserts the header carries that exact key.
  2  WRONG       a wrong passphrase fails with one uninformative sentence and
                 leaves no key material behind.
  3  NO LEAK     after a successful unlock, localStorage, sessionStorage and
                 the whole serialised DOM are dumped and searched for the key.
  4  ABSENT      with no shared-key.json served, the option does not appear
                 and the own-key and no-key paths behave exactly as before.

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

DUMMY_KEY = "sk-or-v1-DUMMY-FOR-TESTING"
OWN_KEY = "sk-or-v1-A-DIFFERENT-DUMMY-KEY-0000"
WRONG_PASS = "not-the-passphrase-at-all-9876"

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,X-Title,HTTP-Referer",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Max-Age": "600",
}


# ---------------------------------------------------------------- fake model


class FakeOpenRouter(http.server.BaseHTTPRequestHandler):
    """Answers as https://openrouter.ai/api/v1 and records what it was sent."""

    hits = 0
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
    ``docs/play/shared-key.json`` behind — that file is the owner's to create,
    with his own key, on his own machine.
    """

    blob: bytes | None = None

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/play/shared-key.json":
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
        exe = base / name / "chrome-linux" / "chrome"
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
        serve_site(SITE_PORT, blob.encode())
        serve_site(BARE_PORT, None)

        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page()
        console: list[str] = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
        page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))

        page.goto(f"http://127.0.0.1:{SITE_PORT}/play/index.html")
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

        report["console_mentions_key"] = [
            line for line in console
            if DUMMY_KEY in line or passphrase in line
        ]
        report["console_tail"] = console[-70:]
        if report["console_mentions_key"]:
            failures.append("the key or passphrase was logged to the console")
        ctx.close()

        # -------------------------- 5. no blob: the option must not exist,
        #                               and the other two paths must be intact
        ctx2 = browser.new_context(ignore_https_errors=True)
        bare = ctx2.new_page()
        bare.goto(f"http://127.0.0.1:{BARE_PORT}/play/index.html")
        bare.wait_for_function("window.FF_PLAY !== undefined", timeout=15_000)
        bare.wait_for_timeout(1500)   # let the 404 probe resolve
        report["absent_shared_offered"] = bare.evaluate("window.FF_PLAY.sharedOffered")
        report["absent_panel_visible"] = bare.is_visible("#sharedPanel")
        report["absent_start_shared_visible"] = bare.is_visible("#startShared")

        # own-key path, unchanged
        report["absent_default_keystate"] = bare.inner_text("#keystate").strip()
        report["absent_startNoKey_primary_before"] = bare.evaluate(
            "document.getElementById('startNoKey').classList.contains('primary')")
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

        if report["absent_shared_offered"] or report["absent_panel_visible"] \
                or report["absent_start_shared_visible"]:
            failures.append("the shared-key option appeared with no blob present")
        if not report["absent_startWithKey_visible"]:
            failures.append("the own-key path broke")
        if OWN_KEY in json.dumps(report["absent_localStorage_after_own_key"]):
            failures.append("an unremembered own key was written to localStorage")

        # no-key path, unchanged: it must still boot and reach a decision
        if not args.skip_play:
            # Taken *before* the click: a request made during boot, before the
            # engine has settled on the offline stand-in, is exactly the
            # regression this is here to catch, and a count read afterwards
            # would have already absorbed it.
            hits_before = FakeOpenRouter.hits
            t0 = time.time()
            bare.click("#startNoKey")
            wait_awaiting(bare, ["decision"])
            report["absent_nokey_boot_seconds"] = round(time.time() - t0, 1)
            report["absent_nokey_boot_llm_hits"] = FakeOpenRouter.hits - hits_before
            report["absent_nokey_awaiting"] = bare.evaluate("window.FF_PLAY.awaiting")
            report["absent_nokey_offline_banner"] = bool(re.search(
                r"OFFLINE MODE", bare.evaluate("window.FF_PLAY.text()")))
            send_decision(bare, "Hold the line and convene COBRA at 0700.")
            report["absent_nokey_extra_llm_hits"] = FakeOpenRouter.hits - hits_before
            if report["absent_nokey_boot_llm_hits"] != 0:
                failures.append("the no-key path contacted an endpoint during boot")
            if report["absent_nokey_extra_llm_hits"] != 0:
                failures.append("the no-key path contacted an endpoint")

        ctx2.close()
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
