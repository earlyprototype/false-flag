"""Tests for LLM router resilience.

Covers:
- Runtime fallback to the mock driver when the active driver keeps failing
- Retry-once behaviour for transient driver failures
- Driver caching (one construction across repeated generate_text calls)
- Rate limiter bypass when the active driver is the mock driver

These tests force code paths via monkeypatching rather than real config,
since config.py may not exist in the test environment.
"""

from random import Random

import pytest

from llm import router
from llm.mock_driver import MockDeterministicDriver


@pytest.fixture(autouse=True)
def clean_router_state(monkeypatch):
    """Force mock provider, clear caches, and skip retry backoff sleeps."""
    monkeypatch.setenv("WARGAME_LLM", "mock")
    monkeypatch.setattr(router.time, "sleep", lambda seconds: None)
    router._driver_cache.clear()
    yield
    router._driver_cache.clear()


class AlwaysFailingDriver:
    """Driver whose generate_text always raises (simulated API outage)."""

    def generate_text(self, prompt: str, rng: Random) -> str:
        raise RuntimeError("simulated API failure (429)")

    def batch_generate_text(self, prompts: list[str], rng: Random) -> list[str]:
        raise RuntimeError("simulated batch API failure (429)")


class FailOnceDriver:
    """Driver that fails on the first call, then succeeds (transient blip)."""

    def __init__(self):
        self.calls = 0

    def generate_text(self, prompt: str, rng: Random) -> str:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient network blip")
        return "recovered response"


class CountingMockDriver(MockDeterministicDriver):
    """Mock driver that counts how many times it is constructed."""

    constructions = 0

    def __init__(self):
        type(self).constructions += 1


def test_always_failing_driver_falls_back_to_mock(monkeypatch):
    """A driver that always raises must not crash generate_text."""
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: AlwaysFailingDriver())

    prompt = "What is your assessment, Foreign Secretary?"
    result = router.generate_text(prompt, Random(42), show_spinner=False)

    expected = MockDeterministicDriver().generate_text(prompt, Random(42))
    assert result == expected


def test_batch_always_failing_driver_falls_back_to_mock(monkeypatch):
    """A batch driver that always raises must not crash batch_generate_text."""
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: AlwaysFailingDriver())

    prompts = ["First advisor prompt", "Second advisor prompt"]
    results = router.batch_generate_text(prompts, Random(42), show_spinner=False)

    expected = MockDeterministicDriver().batch_generate_text(prompts, Random(42))
    assert results == expected


def test_transient_failure_retries_once_and_succeeds(monkeypatch):
    """A driver that fails once then succeeds should return the real result."""
    driver = FailOnceDriver()
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)

    result = router.generate_text("Any prompt", Random(42), show_spinner=False)

    assert result == "recovered response"
    assert driver.calls == 2


def test_driver_cache_constructs_once(monkeypatch):
    """Repeated generate_text calls must reuse one cached driver instance."""
    CountingMockDriver.constructions = 0
    monkeypatch.setattr(
        router, "_construct_text_driver",
        lambda provider, model_name=None: CountingMockDriver()
    )

    router.generate_text("First call", Random(1), show_spinner=False)
    router.generate_text("Second call", Random(2), show_spinner=False)

    assert CountingMockDriver.constructions == 1


def test_driver_cache_keyed_by_model_name(monkeypatch):
    """A different model_name must construct a separate driver."""
    CountingMockDriver.constructions = 0
    monkeypatch.setattr(
        router, "_construct_text_driver",
        lambda provider, model_name=None: CountingMockDriver()
    )

    router.generate_text("Call one", Random(1), show_spinner=False,
                         model_override="gemini-2.5-flash")
    router.generate_text("Call two", Random(2), show_spinner=False,
                         model_override="gemini-2.5-pro")
    router.generate_text("Call three", Random(3), show_spinner=False,
                         model_override="gemini-2.5-pro")

    assert CountingMockDriver.constructions == 2


def test_rate_limiter_bypassed_for_mock_driver(monkeypatch):
    """The rate limiter must not be consulted when the mock driver is active,
    even if the configured provider is a rate-limited one (fallback case)."""
    monkeypatch.setenv("WARGAME_LLM", "gemini")
    monkeypatch.setattr(
        router, "_construct_text_driver",
        lambda provider, model_name=None: MockDeterministicDriver()
    )

    def fail_if_called(self, verbose=True):
        raise AssertionError("RateLimiter.wait_if_needed must not be called for mock driver")

    monkeypatch.setattr(router.RateLimiter, "wait_if_needed", fail_if_called)

    result = router.generate_text("Any prompt", Random(42), show_spinner=False,
                                  model_override="gemini-2.5-pro")
    assert isinstance(result, str) and result

    results = router.batch_generate_text(["A prompt"], Random(42), show_spinner=False,
                                         model_override="gemini-2.5-pro")
    assert len(results) == 1
