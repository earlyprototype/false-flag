"""Truncation detection: a reply cut on its output cap is counted, not silent.

The original incident: the situation summary hit its max_tokens cap and the
game showed a mid-sentence synopsis with nothing anywhere saying so. The
class fix: drivers surface the provider's finish reason through a meta_out
dict, and the router turns "length"/"MAX_TOKENS" into a parse-health
truncation event keyed by call family - for every call site at once.

Also here: the browser bridge's fault-probe wrapper must be
signature-transparent. Its old bare (*args, **kwargs) facade told the
router the driver accepted everything, so the router forwarded meta_out
into a driver method that rejected it - a TypeError (and silent mock
fallback) on every live browser call.
"""

import importlib.util
import inspect
import json
import sys
from pathlib import Path
from random import Random

import pytest

from llm import parse_health, router
from llm.model_config import LLMContext
from llm.openai_compat_driver import OpenAICompatDriver

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    parse_health.reset()
    monkeypatch.delenv("WARGAME_CALL_LOG", raising=False)
    yield
    parse_health.reset()


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def completion(text, finish_reason):
    return {"choices": [{"message": {"content": text},
                         "finish_reason": finish_reason}]}


class TestOpenAICompatDriverFillsMeta:
    @pytest.fixture
    def driver(self, monkeypatch):
        monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "https://example.invalid/v1")
        monkeypatch.setenv("OPENAI_COMPAT_MODEL", "test-model")
        return OpenAICompatDriver()

    def test_finish_reason_reaches_meta_out(self, driver, monkeypatch):
        monkeypatch.setattr(
            "llm.openai_compat_driver.requests.post",
            lambda *a, **k: FakeResponse(completion("cut off mid", "length")))
        meta = {}
        text = driver.generate_text("p", Random(1), meta_out=meta)
        assert text == "cut off mid"
        assert meta["finish_reason"] == "length"

    def test_a_clean_stop_is_reported_too(self, driver, monkeypatch):
        monkeypatch.setattr(
            "llm.openai_compat_driver.requests.post",
            lambda *a, **k: FakeResponse(completion("done.", "stop")))
        meta = {}
        driver.generate_text("p", Random(1), meta_out=meta)
        assert meta["finish_reason"] == "stop"

    def test_batch_fills_one_meta_per_prompt(self, driver, monkeypatch):
        replies = {"a": completion("first", "stop"),
                   "b": completion("second half missi", "length")}

        def fake_post(url, headers=None, json=None, timeout=None):
            prompt = json["messages"][-1]["content"]
            return FakeResponse(replies[prompt])

        monkeypatch.setattr("llm.openai_compat_driver.requests.post", fake_post)
        metas = [{}, {}]
        out = driver.batch_generate_text(["a", "b"], Random(1), meta_out=metas)
        assert out == ["first", "second half missi"]
        assert [m["finish_reason"] for m in metas] == ["stop", "length"]


class TestReasoningControl:
    """OPENAI_COMPAT_REASONING: hidden reasoning must not eat the reply's
    token budget. The first live shakedown watched a thinking model return
    EMPTY completions on every small-capped call."""

    def _payload_sent(self, monkeypatch, env_value):
        monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "https://example.invalid/v1")
        monkeypatch.setenv("OPENAI_COMPAT_MODEL", "test-model")
        if env_value is not None:
            monkeypatch.setenv("OPENAI_COMPAT_REASONING", env_value)
        else:
            monkeypatch.delenv("OPENAI_COMPAT_REASONING", raising=False)
        driver = OpenAICompatDriver()
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured.update(json)
            return FakeResponse(completion("ok", "stop"))

        monkeypatch.setattr("llm.openai_compat_driver.requests.post", fake_post)
        driver.generate_text("p", Random(1))
        return captured

    def test_off_disables_reasoning(self, monkeypatch):
        payload = self._payload_sent(monkeypatch, "off")
        assert payload["reasoning"] == {"enabled": False}

    def test_effort_levels_pass_through(self, monkeypatch):
        payload = self._payload_sent(monkeypatch, "low")
        assert payload["reasoning"] == {"effort": "low"}

    def test_unset_sends_nothing(self, monkeypatch):
        payload = self._payload_sent(monkeypatch, None)
        assert "reasoning" not in payload


class LengthStopDriver:
    """Stand-in driver that always reports a cap-hit."""

    def generate_text(self, prompt, rng, max_tokens=None, meta_out=None):
        if meta_out is not None:
            meta_out["finish_reason"] = "length"
        return "truncated repl"

    def batch_generate_text(self, prompts, rng, max_tokens=None, meta_out=None):
        for i in range(len(prompts)):
            if meta_out is not None:
                meta_out[i]["finish_reason"] = "MAX_TOKENS" if i else "STOP"
        return ["ok"] * len(prompts)


class TestRouterRecordsTruncation:
    def test_single_call_records_under_the_family_name(self, monkeypatch):
        monkeypatch.setenv("WARGAME_LLM", "mock")
        monkeypatch.setattr(router, "_get_text_driver",
                            lambda model_name=None: LengthStopDriver())
        router.generate_text("p", Random(1), show_spinner=False,
                             context=LLMContext.SITUATION_SUMMARY)
        snap = parse_health.snapshot()
        assert snap["truncations"] == {"situation_summary": 1}

    def test_batch_records_only_the_cut_replies(self, monkeypatch):
        monkeypatch.setenv("WARGAME_LLM", "mock")
        monkeypatch.setattr(router, "_get_text_driver",
                            lambda model_name=None: LengthStopDriver())
        router.batch_generate_text(["a", "b"], Random(1), show_spinner=False,
                                   context=LLMContext.ACTOR_SIMULATION)
        snap = parse_health.snapshot()
        assert snap["truncations"] == {"actor_simulation": 1}

    def test_finish_reason_lands_in_the_call_log(self, tmp_path, monkeypatch):
        target = tmp_path / "calls.jsonl"
        monkeypatch.setenv("WARGAME_CALL_LOG", str(target))
        monkeypatch.setenv("WARGAME_LLM", "mock")
        monkeypatch.setattr(router, "_get_text_driver",
                            lambda model_name=None: LengthStopDriver())
        router.generate_text("p", Random(1), show_spinner=False,
                             context=LLMContext.SITUATION_SUMMARY)
        with open(target, encoding="utf-8") as f:
            rec = json.loads(f.readline())
        assert rec["finish_reason"] == "length"


def _load_bridge():
    if "ff_web_bridge_trunc" in sys.modules:
        return sys.modules["ff_web_bridge_trunc"]
    spec = importlib.util.spec_from_file_location(
        "ff_web_bridge_trunc", REPO / "docs" / "py" / "bridge.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ff_web_bridge_trunc"] = module
    spec.loader.exec_module(module)
    return module


class TestBridgeProbeSignatureTransparency:
    def test_the_wrapper_keeps_the_wrapped_signature(self):
        bridge = _load_bridge()

        def narrow(prompt, rng, max_tokens=None):
            return "ok"

        wrapped = bridge._watch_calls(narrow)
        sig = inspect.signature(wrapped)
        assert "meta_out" not in sig.parameters
        assert not any(p.kind is inspect.Parameter.VAR_KEYWORD
                       for p in sig.parameters.values())

    def test_the_router_no_longer_typeerrors_through_the_probe(self, monkeypatch):
        """Regression for the live browser failure: a wrapped driver method
        without meta_out must not be handed meta_out by the router."""
        bridge = _load_bridge()
        calls = []

        class NarrowDriver:
            def generate_text(self, prompt, rng, max_tokens=None):
                calls.append(prompt)
                return "live reply"

        driver = NarrowDriver()
        driver.generate_text = bridge._watch_calls(driver.generate_text)
        monkeypatch.setenv("WARGAME_LLM", "mock")
        monkeypatch.setattr(router, "_get_text_driver",
                            lambda model_name=None: driver)
        result = router.generate_text("p", Random(1), show_spinner=False,
                                      context=LLMContext.NARRATOR,
                                      max_tokens=150)
        assert result == "live reply"
        assert calls == ["p"]
        # No TypeError happened, so nothing fell back to the mock driver
        assert parse_health.snapshot()["fallbacks"] == {}
