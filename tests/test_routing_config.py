"""Tests for provider-aware model routing and persistent rate limiters.

Covers:
- resolve_model_name across providers and env configuration (ER-019)
- The router resolving context -> tier -> per-provider model name, with the
  driver cache holding at most one driver per tier
- --flash-only's mechanism (use_flash_for_all) selecting the FLASH-mapped
  model on openai_compat
- OpenAICompatDriver accepting resolved per-tier names while still
  discarding raw gemini tier names (safety net)
- Rate limiters keyed (provider, rpm): Flash/Pro alternation preserves each
  limiter's request history (ER-032 regression)
- RateLimiter thread safety under a fake clock: 8 threads never exceed the
  RPM cap in any 60-second window
- max_tokens reaching drivers through the batch sequential fallback and the
  **kwargs catch-all (ER-011)
- GeminiDriver mapping system_instruction/temperature/max_tokens into the
  SDK's generation config (SDK mocked - google-generativeai is not installed)

These tests force code paths via monkeypatching rather than real config,
since config.py may not exist in the test environment.
"""

import threading
from collections import deque
from random import Random
from types import SimpleNamespace

import pytest

from llm import router
from llm import gemini_driver
from llm.mock_driver import MockDeterministicDriver
from llm.model_config import (
    LLMContext, ModelTier, ModelConfig,
    resolve_model_name, set_model_config, reset_to_defaults,
)
from llm.openai_compat_driver import OpenAICompatDriver


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    """Isolate provider config, model config and router caches per test."""
    for var in (
        "WARGAME_LLM",
        "GEMINI_RPM",
        "OPENAI_COMPAT_BASE_URL",
        "OPENAI_COMPAT_API_KEY",
        "OPENAI_COMPAT_MODEL",
        "OPENAI_COMPAT_MODEL_FLASH",
        "OPENAI_COMPAT_MODEL_PRO",
        "OPENAI_COMPAT_RPM",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(router.time, "sleep", lambda seconds: None)
    router._driver_cache.clear()
    router._rate_limiters.clear()
    reset_to_defaults()
    yield
    router._driver_cache.clear()
    router._rate_limiters.clear()
    reset_to_defaults()


# ---------------------------------------------------------------------------
# resolve_model_name (ER-019)
# ---------------------------------------------------------------------------

def test_resolve_gemini_uses_tier_table():
    assert resolve_model_name("gemini", ModelTier.FLASH) == "gemini-2.5-flash"
    assert resolve_model_name("gemini", ModelTier.PRO) == "gemini-2.5-pro"


def test_resolve_mock_and_offline_have_no_model_name():
    for provider in ("mock", "offline"):
        assert resolve_model_name(provider, ModelTier.FLASH) is None
        assert resolve_model_name(provider, ModelTier.PRO) is None


def test_resolve_openai_compat_unconfigured_is_none():
    assert resolve_model_name("openai_compat", ModelTier.FLASH) is None
    assert resolve_model_name("openai_compat", ModelTier.PRO) is None


def test_resolve_openai_compat_per_tier_env(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_FLASH", "provider/small")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_PRO", "provider/large")
    assert resolve_model_name("openai_compat", ModelTier.FLASH) == "provider/small"
    assert resolve_model_name("openai_compat", ModelTier.PRO) == "provider/large"


def test_resolve_openai_compat_falls_back_to_single_model(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "provider/only")
    assert resolve_model_name("openai_compat", ModelTier.FLASH) == "provider/only"
    assert resolve_model_name("openai_compat", ModelTier.PRO) == "provider/only"


def test_resolve_openai_compat_partial_tier_config(monkeypatch):
    """A configured tier wins; the other tier falls back to the single model."""
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_FLASH", "provider/small")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "provider/only")
    assert resolve_model_name("openai_compat", ModelTier.FLASH) == "provider/small"
    assert resolve_model_name("openai_compat", ModelTier.PRO) == "provider/only"


# ---------------------------------------------------------------------------
# Router: context -> tier -> per-provider model name
# ---------------------------------------------------------------------------

def _capture_constructions(monkeypatch):
    """Route driver construction to the mock, recording requested names."""
    requested = []

    def fake_construct(provider, model_name=None):
        requested.append(model_name)
        return MockDeterministicDriver()

    monkeypatch.setattr(router, "_construct_text_driver", fake_construct)
    return requested


def test_router_resolves_context_tier_on_openai_compat(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_FLASH", "provider/small")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_PRO", "provider/large")
    requested = _capture_constructions(monkeypatch)

    # ADVISOR_QA defaults to PRO, DECISION_INTERPRETATION to FLASH
    router.generate_text("q", Random(1), show_spinner=False,
                         context=LLMContext.ADVISOR_QA)
    router.generate_text("q", Random(1), show_spinner=False,
                         context=LLMContext.DECISION_INTERPRETATION)

    assert requested == ["provider/large", "provider/small"]


def test_router_driver_cache_holds_at_most_two_tier_drivers(monkeypatch):
    """With per-tier names every context maps onto one of two drivers, not a
    separate identical driver per gemini tier name plus a default."""
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_FLASH", "provider/small")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_PRO", "provider/large")
    _capture_constructions(monkeypatch)

    for context in LLMContext:
        router.generate_text("q", Random(1), show_spinner=False, context=context)

    assert len(router._driver_cache) == 2
    assert set(router._driver_cache) == {
        ("openai_compat", "provider/small"),
        ("openai_compat", "provider/large"),
    }


def test_flash_only_mechanism_selects_flash_model_on_openai_compat(monkeypatch):
    """--flash-only calls use_flash_for_all(); on openai_compat that must now
    actually select the FLASH-mapped model for every context."""
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_FLASH", "provider/small")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL_PRO", "provider/large")
    requested = _capture_constructions(monkeypatch)

    config = ModelConfig()
    config.use_flash_for_all()
    set_model_config(config)

    for context in (LLMContext.ADVISOR_QA, LLMContext.INJECT_GENERATION,
                    LLMContext.QUALITY_ASSESSMENT):
        router.generate_text("q", Random(1), show_spinner=False, context=context)

    assert requested == ["provider/small"]  # cached after the first call
    assert set(router._driver_cache) == {("openai_compat", "provider/small")}


def test_router_passes_none_model_on_mock_provider(monkeypatch):
    """mock/offline have no model names: every context shares one driver."""
    monkeypatch.setenv("WARGAME_LLM", "mock")
    requested = _capture_constructions(monkeypatch)

    router.generate_text("q", Random(1), show_spinner=False,
                         context=LLMContext.ADVISOR_QA)
    router.generate_text("q", Random(1), show_spinner=False,
                         context=LLMContext.DECISION_INTERPRETATION)

    assert requested == [None]
    assert set(router._driver_cache) == {("mock", None)}


def test_new_contexts_are_routable(monkeypatch):
    """The four ER-005 contexts resolve through the tier table like any other."""
    monkeypatch.setenv("WARGAME_LLM", "gemini")
    requested = _capture_constructions(monkeypatch)

    for context in (LLMContext.QUALITY_ASSESSMENT, LLMContext.ACTOR_SIMULATION,
                    LLMContext.SITUATION_SUMMARY, LLMContext.NARRATOR):
        router.generate_text("q", Random(1), show_spinner=False, context=context)

    assert requested == ["gemini-2.5-pro", "gemini-2.5-flash"]


# ---------------------------------------------------------------------------
# OpenAICompatDriver model-name handling
# ---------------------------------------------------------------------------

def test_openai_compat_driver_accepts_resolved_tier_name(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "https://fake-provider.test/v1")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "provider/only")

    driver = OpenAICompatDriver(model_name="provider/large")
    assert driver.model_name == "provider/large"


def test_openai_compat_driver_still_discards_raw_gemini_names(monkeypatch):
    """Safety net: a raw gemini tier name must not be sent to the endpoint."""
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "https://fake-provider.test/v1")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "provider/only")

    driver = OpenAICompatDriver(model_name="gemini-2.5-pro")
    assert driver.model_name == "provider/only"


# ---------------------------------------------------------------------------
# Rate limiters keep their history (ER-032)
# ---------------------------------------------------------------------------

def test_alternating_tiers_reuse_persistent_limiters(monkeypatch):
    """Flash/Pro alternation must reuse two limiters, each keeping its
    request history. The old single-slot swap discarded the history on every
    tier switch - reproduced here as the regression assert."""
    monkeypatch.setenv("WARGAME_LLM", "gemini")

    flash = router.get_rate_limiter("gemini-2.5-flash")
    assert flash.requests_per_minute == 10
    flash.request_times.append(1000.0)  # a recorded request

    pro = router.get_rate_limiter("gemini-2.5-pro")
    assert pro.requests_per_minute == 2
    assert pro is not flash

    # Regression: switching back must return the SAME flash limiter with its
    # history intact (the old code returned a fresh one with zero recorded)
    flash_again = router.get_rate_limiter("gemini-2.5-flash")
    assert flash_again is flash
    assert list(flash_again.request_times) == [1000.0]

    # And the pro limiter survives the same round trip
    assert router.get_rate_limiter("gemini-2.5-pro") is pro


def test_unknown_model_gets_conservative_pro_rate(monkeypatch):
    """A context-less call (model_name None) keeps the conservative Pro rate
    and shares the Pro limiter rather than building another."""
    monkeypatch.setenv("WARGAME_LLM", "gemini")

    default = router.get_rate_limiter(None)
    assert default.requests_per_minute == 2
    assert router.get_rate_limiter("gemini-2.5-pro") is default


def test_openai_compat_limiter_keyed_by_provider(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "openai_compat")
    monkeypatch.setenv("OPENAI_COMPAT_RPM", "20")

    limiter = router.get_rate_limiter("provider/large")
    assert limiter.requests_per_minute == 20
    assert router.get_rate_limiter("provider/small") is limiter
    assert ("openai_compat", 20) in router._rate_limiters


# ---------------------------------------------------------------------------
# RateLimiter thread safety under a fake clock
# ---------------------------------------------------------------------------

class FakeClock:
    """Thread-safe fake clock: sleeping advances time instead of waiting."""

    def __init__(self, start: float = 1000.0):
        self._t = start
        self._lock = threading.Lock()

    def now(self) -> float:
        with self._lock:
            return self._t

    def sleep(self, seconds: float) -> None:
        with self._lock:
            self._t += max(seconds, 0.0)


class RecordingDeque(deque):
    """Deque that logs every append (appends happen under the limiter lock)."""

    def __init__(self, log):
        super().__init__()
        self.log = log

    def append(self, item):
        self.log.append(item)
        super().append(item)


def test_thread_hammer_never_exceeds_rpm_in_any_window(monkeypatch):
    """8 threads through one limiter: no 60s window ever admits more than
    the configured requests-per-minute."""
    clock = FakeClock()
    monkeypatch.setattr(router, "_now", clock.now)
    monkeypatch.setattr(router, "_sleep", clock.sleep)

    rpm = 6
    limiter = router.RateLimiter(requests_per_minute=rpm)
    admitted = []
    limiter.request_times = RecordingDeque(admitted)

    calls_per_thread = 12
    threads = [
        threading.Thread(
            target=lambda: [limiter.wait_if_needed(verbose=False)
                            for _ in range(calls_per_thread)]
        )
        for _ in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not any(t.is_alive() for t in threads), "limiter deadlocked"

    assert len(admitted) == 8 * calls_per_thread
    times = sorted(admitted)
    # Admission requires the (i)th-previous request to have left the window,
    # so any rpm+1 consecutive admissions must span strictly more than 60s.
    for i in range(len(times) - rpm):
        assert times[i + rpm] - times[i] > limiter.window_seconds - 1e-6


def test_wait_if_needed_sleeps_outside_the_lock(monkeypatch):
    """A sleeping waiter must not hold the lock (a later PR runs this under
    a thread pool; a sleep under the lock would serialise everything)."""
    clock = FakeClock()
    monkeypatch.setattr(router, "_now", clock.now)

    limiter = router.RateLimiter(requests_per_minute=1)
    limiter.wait_if_needed(verbose=False)  # claim the only slot

    lock_free_during_sleep = []

    def probing_sleep(seconds):
        lock_free_during_sleep.append(limiter._lock.acquire(blocking=False))
        if lock_free_during_sleep[-1]:
            limiter._lock.release()
        clock.sleep(seconds)

    monkeypatch.setattr(router, "_sleep", probing_sleep)
    limiter.wait_if_needed(verbose=False)  # must wait, sleeping unlocked

    assert lock_free_during_sleep and all(lock_free_during_sleep)


# ---------------------------------------------------------------------------
# max_tokens through the batch fallback and **kwargs drivers (ER-011)
# ---------------------------------------------------------------------------

class KwargsRecordingDriver:
    """Driver with a **kwargs catch-all and no batch entry point, so the
    router's sequential fallback path handles batches."""

    def __init__(self):
        self.calls = []

    def generate_text(self, prompt, rng, **kwargs):
        self.calls.append(kwargs)
        return f"response to {prompt}"


def test_batch_fallback_forwards_max_tokens_to_kwargs_driver(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")
    driver = KwargsRecordingDriver()
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)

    results = router.batch_generate_text(["a", "b"], Random(1),
                                         show_spinner=False, max_tokens=150)

    assert results == ["response to a", "response to b"]
    assert driver.calls == [{"max_tokens": 150}, {"max_tokens": 150}]


def test_batch_fallback_calls_bare_without_max_tokens(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")
    driver = KwargsRecordingDriver()
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)

    router.batch_generate_text(["a"], Random(1), show_spinner=False)

    assert driver.calls == [{}]


def test_generate_text_forwards_all_options_to_kwargs_driver(monkeypatch):
    monkeypatch.setenv("WARGAME_LLM", "mock")
    driver = KwargsRecordingDriver()
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)

    router.generate_text("a", Random(1), show_spinner=False,
                         system_instruction="sys", temperature=0.3,
                         max_tokens=400)

    assert driver.calls == [{"system_instruction": "sys", "temperature": 0.3,
                             "max_tokens": 400}]


def test_mock_and_offline_drivers_accept_and_ignore_options():
    from llm.offline_driver import OfflineDriver

    mock_result = MockDeterministicDriver().generate_text(
        "Any prompt", Random(1), system_instruction="sys", temperature=0.1,
        max_tokens=50)
    bare_result = MockDeterministicDriver().generate_text("Any prompt", Random(1))
    assert mock_result == bare_result

    offline_result = OfflineDriver().generate_text(
        "Any prompt", Random(1), system_instruction="sys", max_tokens=50)
    assert offline_result == "[Offline mode: No LLM response available]"


# ---------------------------------------------------------------------------
# GeminiDriver generation options (SDK mocked; not installed here)
# ---------------------------------------------------------------------------

class FakeGenerationConfig:
    def __init__(self, temperature=None, top_p=None, top_k=None,
                 max_output_tokens=None):
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens


class FakeGenerativeModel:
    generate_calls = []
    constructed = []

    def __init__(self, model_name, safety_settings=None, system_instruction=None):
        self.model_name = model_name
        self.system_instruction = system_instruction
        type(self).constructed.append(self)

    def generate_content(self, prompt, generation_config=None, request_options=None):
        type(self).generate_calls.append(
            {"prompt": prompt, "generation_config": generation_config,
             "system_instruction": self.system_instruction})
        return SimpleNamespace(text="generated", candidates=[])


@pytest.fixture
def fake_genai(monkeypatch):
    FakeGenerativeModel.generate_calls = []
    FakeGenerativeModel.constructed = []
    fake = SimpleNamespace(
        configure=lambda api_key: None,
        GenerativeModel=FakeGenerativeModel,
        GenerationConfig=FakeGenerationConfig,
    )
    monkeypatch.setattr(gemini_driver, "genai", fake, raising=False)
    monkeypatch.setattr(gemini_driver, "GENAI_AVAILABLE", True)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    return fake


def test_gemini_driver_maps_options_into_generation_config(fake_genai):
    driver = gemini_driver.GeminiDriver(model_name="gemini-2.5-flash")

    result = driver.generate_text(
        "A prompt", Random(1), system_instruction="Be the CDS.",
        temperature=0.2, max_tokens=150)

    assert result == "generated"
    call = FakeGenerativeModel.generate_calls[-1]
    assert call["generation_config"].max_output_tokens == 150
    assert call["generation_config"].temperature == 0.2
    assert call["system_instruction"] == "Be the CDS."


def test_gemini_driver_defaults_unchanged_without_overrides(fake_genai):
    driver = gemini_driver.GeminiDriver(model_name="gemini-2.5-flash")

    driver.generate_text("A prompt", Random(1))

    call = FakeGenerativeModel.generate_calls[-1]
    assert call["generation_config"] is driver.generation_config
    assert call["generation_config"].max_output_tokens == 2048
    assert call["system_instruction"] is None


def test_gemini_driver_batch_forwards_max_tokens(fake_genai):
    driver = gemini_driver.GeminiDriver(model_name="gemini-2.5-flash")

    results = driver.batch_generate_text(["a", "b"], Random(1), max_tokens=99)

    assert results == ["generated", "generated"]
    assert all(call["generation_config"].max_output_tokens == 99
               for call in FakeGenerativeModel.generate_calls)
