"""Drive the Pyodide spike page in headless Chromium and dump the step results."""
import json
import sys
import threading
import functools
import http.server
import socketserver
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8777
LLM_PORT = 8778  # different port => genuinely cross-origin => real CORS preflight

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization,Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


class FakeOpenAIHandler(http.server.BaseHTTPRequestHandler):
    """Cross-origin stand-in for OpenRouter, with the same CORS posture
    OpenRouter actually advertises (verified by curl preflight)."""

    def log_message(self, *a):
        pass

    def _cors(self):
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    hits = 0

    def do_GET(self):
        payload = json.dumps({"hits": FakeOpenAIHandler.hits}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        FakeOpenAIHandler.hits += 1
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8", "replace")
        auth = self.headers.get("Authorization", "<none>")
        req = json.loads(body) if body else {}
        prompt = (req.get("messages") or [{}])[-1].get("content", "")
        reply = (
            "PROXY-FREE BROWSER LLM CALL OK. "
            f"auth_header_received={auth[:22]!r} "
            f"model={req.get('model')!r} prompt_chars={len(prompt)}"
        )
        payload = json.dumps(
            {
                "id": "spike-1",
                "choices": [{"message": {"role": "assistant", "content": reply},
                             "finish_reason": "stop"}],
                "usage": {"total_tokens": 42},
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=HERE)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    llm = socketserver.TCPServer(("127.0.0.1", LLM_PORT), FakeOpenAIHandler)
    threading.Thread(target=llm.serve_forever, daemon=True).start()
    return httpd


def main():
    serve()
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        launch_kwargs = dict(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox"],
        )
        # route the browser's outbound HTTPS through the session's agent proxy
        # so the external-network probes (CORS) actually leave the sandbox
        proxy = os.environ.get("HTTPS_PROXY")
        if proxy and os.environ.get("SPIKE_USE_PROXY") == "1":
            launch_kwargs["proxy"] = {"server": proxy, "bypass": "127.0.0.1,localhost"}
            # Chromium has no --ca-bundle flag; trust exactly the agent proxy's
            # CA by pinning its SPKI hash. This is NOT --ignore-certificate-errors:
            # every other authority is still verified normally.
            spki = os.environ.get("SPIKE_PROXY_CA_SPKI")
            if spki:
                launch_kwargs["args"].append(
                    f"--ignore-certificate-errors-spki-list={spki}"
                )
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.on("pageerror", lambda e: print("PAGEERROR:", e))
        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        try:
            page.wait_for_function("window.DONE === true", timeout=300000)
        except Exception as e:
            print("TIMEOUT waiting for completion:", e)
        results = page.evaluate("window.RESULTS")
        browser.close()

    for r in results:
        ms = f" [{r['ms']}ms]" if r.get("ms") is not None else ""
        print(f"{r['status']:5} {r['name']}{ms}")
        if r.get("detail"):
            for line in str(r["detail"]).splitlines():
                print("        " + line)
        print()
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
