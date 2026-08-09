"""The batch path must survive platforms that cannot start threads.

Pyodide (the browser build) refuses thread creation: ThreadPoolExecutor
raises ``RuntimeError: can't start new thread`` at the first submit. Before
the sequential fallback, every batch call in the browser — ask-all, the
around-the-table reactions — died instantly and the router silently swapped
in mock advisors while the fault notice blamed the network.

These tests force that exact failure and assert the batch still answers
every prompt, in order, through the single-call path.
"""
from random import Random

import pytest

import concurrent.futures as cf


class _ThreadlessExecutor:
    """Stands in for ThreadPoolExecutor on a no-threads platform."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def submit(self, *args, **kwargs):
        raise RuntimeError("can't start new thread")


@pytest.fixture
def threadless(monkeypatch):
    monkeypatch.setattr(cf, "ThreadPoolExecutor", _ThreadlessExecutor)


def test_openai_compat_batch_falls_back_sequentially(threadless, monkeypatch):
    from llm.openai_compat_driver import OpenAICompatDriver

    driver = OpenAICompatDriver.__new__(OpenAICompatDriver)

    calls = []

    def fake_generate(prompt, rng, max_tokens=None, meta_out=None):
        calls.append(prompt)
        if meta_out is not None:
            meta_out["finish_reason"] = "stop"
        return f"answer to {prompt}"

    monkeypatch.setattr(driver, "generate_text", fake_generate)

    prompts = ["alpha", "bravo", "charlie", "delta", "echo"]
    meta = [{} for _ in prompts]
    results = driver.batch_generate_text(prompts, Random(42), meta_out=meta)

    assert results == [f"answer to {p}" for p in prompts]
    assert calls == prompts  # every prompt answered, in order, live
    assert all(m.get("finish_reason") == "stop" for m in meta)
    assert not any(str(r).startswith("[ERROR:") for r in results)


def test_gemini_batch_falls_back_sequentially(threadless):
    from llm.gemini_driver import GeminiDriver

    driver = GeminiDriver.__new__(GeminiDriver)
    # The gemini batch talks to the SDK model directly, not generate_text.
    driver.generation_config = object()

    class _Resp:
        candidates = []

        def __init__(self, text):
            self.text = text

    class _Model:
        def generate_content(self, prompt, generation_config=None,
                             request_options=None):
            return _Resp(f"answer to {prompt}")

    driver.model = _Model()

    prompts = ["one", "two", "three"]
    results = driver.batch_generate_text(prompts, Random(7))

    assert results == [f"answer to {p}" for p in prompts]
    assert not any(str(r).startswith("[ERROR:") for r in results)
