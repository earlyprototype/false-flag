"""Tests for the OpenAI-compatible chat-completions driver.

Covers:
- Request shape (URL, headers, payload) with a mocked HTTP layer
- Response parsing (happy path, empty/missing content)
- Error handling: driver raises; router retries then falls back to mock
- Missing configuration falls back to the mock driver at construction
- Rate limiter integration via OPENAI_COMPAT_RPM
- Router provider selection for "openai_compat"
- A real HTTP round-trip against a tiny local stub server
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from random import Random

import pytest

from llm import router
from llm import openai_compat_driver
from llm.openai_compat_driver import OpenAICompatDriver
from llm.mock_driver import MockDeterministicDriver


BASE_URL = "https://fake-provider.test/v1"


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    """Isolate provider config and router caches per test."""
    for var in (
        "WARGAME_LLM",
        "OPENAI_COMPAT_BASE_URL",
        "OPENAI_COMPAT_API_KEY",
        "OPENAI_COMPAT_MODEL",
        "OPENAI_COMPAT_RPM",
        "OPENAI_COMPAT_TEMPERATURE",
        "OPENAI_COMPAT_MAX_TOKENS",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(router.time, "sleep", lambda seconds: None)
    router._driver_cache.clear()
    router._rate_limiter = None
    yield
    router._driver_cache.clear()
    router._rate_limiter = None


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text or json.dumps(self._payload)

    def json(self):
        return self._payload


def completion_payload(content="Prime Minister, the fleet is ready."):
    return {
        "choices": [
            {"message": {"role": "assistant", "content": content},
             "finish_reason": "stop"}
        ]
    }


def make_driver(monkeypatch, api_key="test-key", model="test-model"):
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    if api_key:
        monkeypatch.setenv("OPENAI_COMPAT_API_KEY", api_key)
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", model)
    return OpenAICompatDriver()


# ---------------------------------------------------------------------------
# Request shape
# ---------------------------------------------------------------------------

def test_request_shape(monkeypatch):
    """The driver must POST an OpenAI-style chat-completions payload."""
    driver = make_driver(monkeypatch)
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(url=url, headers=headers, payload=json, timeout=timeout)
        return FakeResponse(payload=completion_payload())

    monkeypatch.setattr(openai_compat_driver.requests, "post", fake_post)

    result = driver.generate_text(
        "What are our options, CDS?", Random(42),
        system_instruction="You are the Chief of the Defence Staff.",
        temperature=0.3, max_tokens=512,
    )

    assert result == "Prime Minister, the fleet is ready."
    assert captured["url"] == f"{BASE_URL}/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["timeout"] == openai_compat_driver.REQUEST_TIMEOUT

    payload = captured["payload"]
    assert payload["model"] == "test-model"
    assert payload["temperature"] == 0.3
    assert payload["max_tokens"] == 512
    assert isinstance(payload["seed"], int)
    assert payload["messages"] == [
        {"role": "system", "content": "You are the Chief of the Defence Staff."},
        {"role": "user", "content": "What are our options, CDS?"},
    ]


def test_no_api_key_omits_authorization_header(monkeypatch):
    """Local servers (Ollama/LM Studio) need no key - header must be absent."""
    driver = make_driver(monkeypatch, api_key=None)
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["headers"] = headers
        return FakeResponse(payload=completion_payload())

    monkeypatch.setattr(openai_compat_driver.requests, "post", fake_post)
    driver.generate_text("Any prompt", Random(1))

    assert "Authorization" not in captured["headers"]


def test_base_url_trailing_slash_normalised(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL + "/")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "m")
    driver = OpenAICompatDriver()
    assert driver.base_url == BASE_URL


def test_gemini_tier_model_names_are_ignored(monkeypatch):
    """Router-selected Gemini tier names must not leak to other providers."""
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "qwen3:8b")
    driver = OpenAICompatDriver(model_name="gemini-2.5-pro")
    assert driver.model_name == "qwen3:8b"

    explicit = OpenAICompatDriver(model_name="llama-3.3-70b-versatile")
    assert explicit.model_name == "llama-3.3-70b-versatile"


# ---------------------------------------------------------------------------
# Response parsing and errors
# ---------------------------------------------------------------------------

def test_response_content_is_stripped(monkeypatch):
    driver = make_driver(monkeypatch)
    monkeypatch.setattr(
        openai_compat_driver.requests, "post",
        lambda *a, **k: FakeResponse(payload=completion_payload("  padded  \n")),
    )
    assert driver.generate_text("p", Random(1)) == "padded"


@pytest.mark.parametrize("payload", [
    {},  # no choices at all
    {"choices": []},
    {"choices": [{"message": {"content": ""}, "finish_reason": "length"}]},
    {"choices": [{"message": {}, "finish_reason": "stop"}]},
])
def test_empty_or_malformed_response_raises(monkeypatch, payload):
    driver = make_driver(monkeypatch)
    monkeypatch.setattr(
        openai_compat_driver.requests, "post",
        lambda *a, **k: FakeResponse(payload=payload),
    )
    with pytest.raises(Exception, match="OpenAI-compatible API error"):
        driver.generate_text("p", Random(1))


def test_http_error_status_raises(monkeypatch):
    driver = make_driver(monkeypatch)
    monkeypatch.setattr(
        openai_compat_driver.requests, "post",
        lambda *a, **k: FakeResponse(status_code=429, payload={"error": "rate limited"}),
    )
    with pytest.raises(Exception, match="HTTP 429"):
        driver.generate_text("p", Random(1))


def test_network_error_raises(monkeypatch):
    driver = make_driver(monkeypatch)

    def boom(*a, **k):
        raise ConnectionError("connection refused")

    monkeypatch.setattr(openai_compat_driver.requests, "post", boom)
    with pytest.raises(Exception, match="ConnectionError"):
        driver.generate_text("p", Random(1))


def test_missing_base_url_raises_value_error(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "m")
    with pytest.raises(ValueError, match="OPENAI_COMPAT_BASE_URL"):
        OpenAICompatDriver()


def test_missing_model_raises_value_error(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    with pytest.raises(ValueError, match="OPENAI_COMPAT_MODEL"):
        OpenAICompatDriver()


# ---------------------------------------------------------------------------
# Batch generation
# ---------------------------------------------------------------------------

def test_batch_generate_text_preserves_order_and_isolates_errors(monkeypatch):
    driver = make_driver(monkeypatch)

    def fake_post(url, headers=None, json=None, timeout=None):
        prompt = json["messages"][-1]["content"]
        if prompt == "bad":
            return FakeResponse(status_code=500, payload={"error": "boom"})
        return FakeResponse(payload=completion_payload(f"reply to {prompt}"))

    monkeypatch.setattr(openai_compat_driver.requests, "post", fake_post)

    results = driver.batch_generate_text(["one", "bad", "three"], Random(7))

    assert len(results) == 3
    assert results[0] == "reply to one"
    assert results[1].startswith("[ERROR:")
    assert results[2] == "reply to three"


def test_batch_generate_text_empty_input(monkeypatch):
    driver = make_driver(monkeypatch)
    assert driver.batch_generate_text([], Random(1)) == []


# ---------------------------------------------------------------------------
# Router integration
# ---------------------------------------------------------------------------

def test_router_selects_openai_compat_driver(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "test-model")

    driver = router._construct_text_driver("openai_compat")
    assert isinstance(driver, OpenAICompatDriver)


def test_router_falls_back_to_mock_when_unconfigured(monkeypatch, capsys):
    """No base URL configured -> construction fails -> mock driver, no crash."""
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")

    driver = router._construct_text_driver("openai_compat")
    assert isinstance(driver, MockDeterministicDriver)
    assert "Falling back to mock driver" in capsys.readouterr().out


def test_router_generate_text_falls_back_to_mock_on_persistent_failure(monkeypatch):
    """API errors at call time must degrade to mock output, not crash."""
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "test-model")
    monkeypatch.setattr(
        openai_compat_driver.requests, "post",
        lambda *a, **k: FakeResponse(status_code=503, payload={"error": "down"}),
    )

    prompt = "What is your assessment, Foreign Secretary?"
    result = router.generate_text(prompt, Random(42), show_spinner=False)

    expected = MockDeterministicDriver().generate_text(prompt, Random(42))
    assert result == expected


def test_router_retries_once_then_succeeds(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "test-model")

    calls = {"n": 0}

    def flaky_post(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("transient blip")
        return FakeResponse(payload=completion_payload("recovered"))

    monkeypatch.setattr(openai_compat_driver.requests, "post", flaky_post)

    result = router.generate_text("Any prompt", Random(42), show_spinner=False)
    assert result == "recovered"
    assert calls["n"] == 2


# ---------------------------------------------------------------------------
# Rate limiter integration
# ---------------------------------------------------------------------------

def test_rate_limiter_disabled_by_default(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    assert router.get_rate_limiter("test-model") is None


def test_rate_limiter_uses_openai_compat_rpm(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_RPM", "18")
    limiter = router.get_rate_limiter("test-model")
    assert limiter is not None
    assert limiter.requests_per_minute == 18


def test_rate_limiter_consulted_on_generate(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", BASE_URL)
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_COMPAT_RPM", "30")
    monkeypatch.setattr(
        openai_compat_driver.requests, "post",
        lambda *a, **k: FakeResponse(payload=completion_payload()),
    )

    waited = {"n": 0}

    def record_wait(self, verbose=True):
        waited["n"] += 1

    monkeypatch.setattr(router.RateLimiter, "wait_if_needed", record_wait)
    router.generate_text("p", Random(1), show_spinner=False)
    assert waited["n"] == 1


def test_rate_limiter_not_consulted_for_mock_fallback(monkeypatch):
    """Unconfigured openai_compat falls back to mock: no throttling."""
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_RPM", "30")

    def fail_if_called(self, verbose=True):
        raise AssertionError("RateLimiter must not run for the mock fallback")

    monkeypatch.setattr(router.RateLimiter, "wait_if_needed", fail_if_called)
    result = router.generate_text("p", Random(1), show_spinner=False)
    assert isinstance(result, str) and result


# ---------------------------------------------------------------------------
# End-to-end against a local stub HTTP server
# ---------------------------------------------------------------------------

class StubHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        request = json.loads(self.rfile.read(length))
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"stub reply for model {request['model']}",
                },
                "finish_reason": "stop",
            }]
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep test output clean
        pass


def test_real_http_round_trip_against_local_stub(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", f"http://127.0.0.1:{port}/v1")
        monkeypatch.setenv("OPENAI_COMPAT_MODEL", "stub-model")
        driver = OpenAICompatDriver()
        result = driver.generate_text("Hello over real HTTP", Random(3))
        assert result == "stub reply for model stub-model"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_429_with_named_window_waits_and_retries(monkeypatch):
    """A 429 naming its recovery window is retried after that delay; the
    retry's success response is returned instead of an error."""
    driver = make_driver(monkeypatch)
    calls = []
    ok = FakeResponse(payload={
        "choices": [{"message": {"content": "recovered"}}]})
    limited = FakeResponse(
        status_code=429,
        payload={"error": {"message": "try again in 1.2s"}})

    def post(*a, **k):
        calls.append(1)
        return limited if len(calls) == 1 else ok

    slept = []
    monkeypatch.setattr(openai_compat_driver.requests, "post", post)
    monkeypatch.setattr(openai_compat_driver.time, "sleep",
                        lambda s: slept.append(s))
    assert driver.generate_text("p", Random(1)) == "recovered"
    assert len(calls) == 2 and slept and slept[0] >= 1.2
