"""A local stand-in for an OpenAI-compatible endpoint that records what it is asked.

Exists to answer questions about the game's LLM traffic that no amount of
reading can settle: how many calls a turn really makes, how large each prompt
is, how much of each prompt is identical to the last one, and how much of a
turn's wall clock is calls waiting on each other.

It speaks just enough of `/chat/completions` to satisfy
``llm.openai_compat_driver``, returns format-correct answers for every prompt
shape the game issues (so nothing falls through to a parser fallback and
quietly changes the measurement), and writes one JSON line per request to
``--log``.

Usage:
    python3 dev-scripts/fake_openrouter.py --port 8099 --log calls.jsonl [--latency 0.6]

Each log line carries: seq, thread, t_start, t_end, prompt_chars, prompt_sha,
kind, and prefix_1k/prefix_4k (hashes of the first 1,000 / 4,000 characters).
Prompts themselves go to ``<log>.prompts``, one JSON string per line, so the
prefix analysis can be done offline instead of in the request path.
"""

import argparse
import hashlib
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


# Matched against the END of a prompt, never the whole of it. Most prompts
# embed the game transcript, and the transcript contains every marker every
# other call site uses — classifying on the full text attributes an advisor
# question to whatever happened to be quoted inside it.
_TAIL_MARKERS = [
    ("Your inject:", "inject_generation"),
    ("QUALITY MULTIPLIER:", "quality_assessment"),
    ("If you have redlines, enforce them.", "actor_simulation"),
    ("or NO_CONCERN):", "critical_omissions"),
    ("NO PUSHBACK", "advisor_pushback"),
    ("Your interpretation:", "decision_interpretation"),
    ("Your narrative bridge:", "narrator_bridge"),
    ("daily brief", "situation_summary"),
    ("in a COBRA briefing", "character_response"),
    ("The Prime Minister asks:", "advisor_qa"),
]

# How much of the prompt tail counts as "the instruction block". Every call
# site's own instructions fit well inside this; the transcript sits above it.
_TAIL_WINDOW = 2000


def classify(prompt: str) -> str:
    """Name the game call a prompt came from, by the marker in its tail."""
    tail = prompt[-_TAIL_WINDOW:]
    for marker, kind in _TAIL_MARKERS:
        if marker in tail:
            return kind
    if "diplomat" in tail.lower():
        return "diplomacy"
    return "unknown"


# One canned answer per call shape. Each is written to parse cleanly through
# the game's own parser, so a measurement run never silently degrades to a
# heuristic fallback and reports a call count for a turn that did not happen.
_RESPONSES = {
    "inject_generation": """```yaml
id: turn_000_inject
title: "Baltic Cable Survey Vessel Detected"
description: |
  A Russian-flagged survey vessel has been detected loitering above the
  Bornholm interconnector, transponder dark for the last nine hours.

  Norwegian maritime patrol confirms a second hull standing off to the east.
channel: intelligence
effects:
  - metric: escalation_risk
    delta: 3
```""",
    "quality_assessment": """QUALITY: adequate
REASONING: The decision holds the line without closing off options, though it leaves the alliance question unanswered for another day.
EFFECTS:
  escalation_risk: +2
  domestic_stability: -1
  alliance_cohesion: +1
QUALITY MULTIPLIER: 1.0""",
    "actor_simulation": """PUBLIC_RESPONSE: We note the United Kingdom's decision and will consult our partners.
PRIVATE_ASSESSMENT: London is buying time. We should let them.
TRUST_CHANGE: 2
WILL_SUPPORT: conditional
CONDITIONS: Formal consultation before any further deployment.
INTEL_SHARED: none""",
    "critical_omissions": "NO_CONCERN",
    "advisor_pushback": "NO PUSHBACK",
    "decision_interpretation": """INTERPRETATION: The PM orders a measured naval presence and opens a diplomatic channel.
FORCES INVOLVED: Type-45 destroyer, maritime patrol aircraft
RESOURCES CONSUMED: None
TIMELINE: immediate
FEASIBILITY: feasible""",
    "narrator_bridge": "The rain has not stopped since midnight. A duty officer sets down a folder and does not leave the room.",
    "situation_summary": "The crisis is contained but not resolved. NATO holds, for now, and the public mood is watchful rather than alarmed.",
    "character_response": "Understood, Prime Minister. We will have an assessment within the hour.",
    "advisor_qa": "Prime Minister, the picture is incomplete. I would not commit to a posture change on this intelligence alone.",
    "diplomacy": "We are listening, Prime Minister, but our patience is not unlimited.",
    "unknown": "Acknowledged.",
}


class _Handler(BaseHTTPRequestHandler):
    server_version = "FakeOpenRouter/1.0"

    def log_message(self, *args):  # silence per-request stderr noise
        pass

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            self.send_error(404, "only /chat/completions is served")
            return

        started = time.time()
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        prompt = "".join(
            m.get("content", "") for m in body.get("messages", [])
        )

        latency = self.server.latency
        if latency:
            time.sleep(latency)

        kind = classify(prompt)
        text = _RESPONSES.get(kind, _RESPONSES["unknown"])
        finished = time.time()

        with self.server.lock:
            self.server.seq += 1
            # Prompts are written out verbatim and the prefix analysis is done
            # offline by analyse_calls.py. Computing longest-common-prefix in
            # here looked tidier and quietly wrecked the thing it sat next to:
            # comparing every prompt against every earlier one is millions of
            # character comparisons per request, under the log lock, which
            # inflated a 47s campaign to 195s. Measurement must not perturb
            # what it measures.
            self.server.promptfile.write(json.dumps(prompt) + "\n")

            record = {
                "seq": self.server.seq,
                "thread": threading.current_thread().name,
                "t_start": round(started - self.server.t0, 4),
                "t_end": round(finished - self.server.t0, 4),
                "kind": kind,
                "model": body.get("model"),
                "prompt_chars": len(prompt),
                "prompt_sha": _sha(prompt),
                "prefix_1k": _sha(prompt[:1000]),
                "prefix_4k": _sha(prompt[:4000]),
                "authorization": bool(self.headers.get("Authorization")),
            }
            self.server.logfile.write(json.dumps(record) + "\n")
            self.server.logfile.flush()

        payload = json.dumps({
            "id": f"fake-{record['seq']}",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": len(prompt) // 4,
                      "completion_tokens": len(text) // 4},
        }).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def serve(port: int, log_path: str, latency: float):
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    server.latency = latency
    server.lock = threading.Lock()
    server.seq = 0
    server.t0 = time.time()
    server.logfile = open(log_path, "w", encoding="utf-8")
    server.promptfile = open(log_path + ".prompts", "w", encoding="utf-8")
    print(f"fake openrouter on http://127.0.0.1:{port}/v1 -> {log_path} "
          f"(latency {latency}s)", flush=True)
    try:
        server.serve_forever()
    finally:
        server.logfile.close()
        server.promptfile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--log", default="calls.jsonl")
    parser.add_argument("--latency", type=float, default=0.0,
                        help="seconds to hold each request, to model network time")
    args = parser.parse_args()
    serve(args.port, args.log, args.latency)
