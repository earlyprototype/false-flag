"""LLM router for provider-agnostic text generation and legacy proposal selection.

Supports multiple LLM providers:
- mock (default): Deterministic mock responses for testing
- offline: Pre-recorded responses
- gemini: Google Gemini 2.5 Flash/Pro (requires GOOGLE_API_KEY)
- openai_compat: Any OpenAI-compatible chat-completions endpoint --
  OpenRouter, Groq, Cerebras, Mistral, Ollama, LM Studio, ...
  (requires OPENAI_COMPAT_BASE_URL + OPENAI_COMPAT_MODEL; see
  docs/LLM_PROVIDERS.md)

Configuration priority:
1. Environment variable WARGAME_LLM (if set)
2. config.py LLM_PROVIDER (if file exists)
3. Default to "mock"

Model selection per context:
- Configured via llm.model_config
- Allows Flash vs Pro per system (advisor, inject, diplomacy, etc.)
- Tiers resolve to provider-specific model names via resolve_model_name,
  so the table works on gemini and openai_compat alike
"""

import os
import threading
import time
from random import Random
from typing import Optional
from collections import deque

from llm.mock_driver import MockDeterministicDriver
from llm.offline_driver import OfflineDriver
from llm.model_config import LLMContext, get_model_config, resolve_model_name


# Injectable clock, so tests can drive the rate limiter with a fake clock
# instead of real sleeps. Looked up at call time (module globals), which is
# what lets monkeypatching router._now / router._sleep take effect.
_now = time.time
_sleep = time.sleep


class RateLimiter:
    """Rate limiter for API calls to prevent hitting provider limits.

    Google Gemini free tier: 2 requests per minute (RPM)
    Google Gemini paid tier: 1000 requests per minute
    """

    def __init__(self, requests_per_minute: int = 2):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()  # Track timestamps of recent requests
        self.window_seconds = 60.0  # 1 minute window
        self._lock = threading.Lock()  # Guards request_times

    def wait_if_needed(self, verbose: bool = True):
        """Wait if necessary to stay within rate limits.

        Thread-safe: the check-and-record runs under a lock, while any
        sleeping happens outside it with a re-check loop, so one waiting
        caller neither blocks the others nor lets them slip past the cap.
        A slot is only ever claimed under the lock, which is what makes the
        cap hold when a thread pool drives this limiter concurrently.

        Args:
            verbose: If True, print messages when waiting
        """
        while True:
            with self._lock:
                now = _now()

                # Remove requests older than the window
                while self.request_times and (now - self.request_times[0]) > self.window_seconds:
                    self.request_times.popleft()

                # Under the limit: claim a slot and go
                if len(self.request_times) < self.requests_per_minute:
                    self.request_times.append(now)
                    return

                # At the limit: wait until the oldest request expires
                oldest_request = self.request_times[0]
                wait_time = self.window_seconds - (now - oldest_request)

            if verbose and wait_time > 0:
                print(f"\n[Rate Limit] Waiting {wait_time:.1f}s to stay within {self.requests_per_minute} requests/min limit...")
            _sleep(max(wait_time, 0.0) + 0.1)  # Small buffer, then re-check


# Rate limiters keyed by (provider, rpm). Keeping one limiter per rate -
# rather than one global limiter rebuilt whenever the rate changes - means
# Flash/Pro alternation reuses two persistent limiters, each of which keeps
# its record of recent requests (ER-032: the old single-slot swap discarded
# that history on every tier switch).
_rate_limiters: dict = {}

# Cache of constructed text drivers, keyed by (provider, model_name).
# Reusing drivers avoids re-initialising the API client on every call and
# ensures fallback warnings (e.g. missing API key) print once, not per call.
_driver_cache: dict = {}


def _get_provider() -> str:
    """Determine the configured LLM provider.

    Priority: WARGAME_LLM env var, then config.py LLM_PROVIDER, then "mock".
    """
    provider = os.getenv("WARGAME_LLM", "").lower().strip()
    if not provider:
        try:
            import config
            provider = getattr(config, "LLM_PROVIDER", "mock").lower().strip()
        except ImportError:
            provider = "mock"
    return provider


def _record_truncation_if_cut(meta: dict,
                              context: Optional[LLMContext],
                              provider: str) -> None:
    """Count a reply the model stopped on its output cap.

    Drivers fill meta['finish_reason'] ("length" on OpenAI-compatible
    endpoints, "MAX_TOKENS" on Gemini); this is the single place that
    turns it into a parse-health event, keyed by call family so the
    counter says *which* output was cut.
    """
    reason = meta.get('finish_reason')
    if isinstance(reason, str) and reason.lower() in ("length", "max_tokens"):
        from llm.parse_health import record_truncation
        record_truncation(context.value if context else provider, reason)


def _resolve_call_model(provider: str,
                        context: Optional[LLMContext],
                        model_override: Optional[str]) -> Optional[str]:
    """Model name for one dispatch: explicit override, else context tier
    resolved through the provider-aware table (ER-019).

    Returns None when neither is given, or when the provider has no notion
    of a model name (mock/offline) - the driver's own default then applies.
    """
    if model_override:
        return model_override
    if context:
        tier = get_model_config().get_tier_for_context(context)
        return resolve_model_name(provider, tier)
    return None


def get_rate_limiter(model_name: Optional[str] = None) -> Optional[RateLimiter]:
    """Get or create the global rate limiter.

    Args:
        model_name: Model being used (determines RPM limit)

    Returns:
        RateLimiter instance if using a rate-limited provider, None otherwise
    """
    # Check provider
    provider = _get_provider()

    # Only rate limit for real API providers
    if provider not in ["gemini", "openai_compat"]:
        return None

    if provider == "openai_compat":
        # RPM from OPENAI_COMPAT_RPM (env var, then config.py).
        # 0 / unset = no rate limiting (right for local Ollama/LM Studio);
        # hosted free tiers should set it (OpenRouter: 20, Groq: 30, ...).
        rpm = int(os.getenv("OPENAI_COMPAT_RPM", "0"))
        if rpm == 0:
            try:
                import config
                rpm = int(getattr(config, "OPENAI_COMPAT_RPM", 0) or 0)
            except ImportError:
                pass
        if rpm <= 0:
            return None
    else:
        # Determine RPM based on model (free tier limits)
        # Flash: 10 RPM, Pro: 2 RPM (from Google AI Studio dashboard)
        rpm = int(os.getenv("GEMINI_RPM", "0"))  # 0 = auto-detect

        if rpm == 0:  # Auto-detect based on model
            if model_name and "flash" in model_name.lower():
                rpm = 10  # Flash models: 10 RPM
            else:
                rpm = 2   # Pro models: 2 RPM (conservative default for None)

    # One persistent limiter per (provider, rpm): alternating tiers reuse
    # their own limiters instead of rebuilding one and losing its history
    key = (provider, rpm)
    limiter = _rate_limiters.get(key)
    if limiter is None:
        limiter = RateLimiter(requests_per_minute=rpm)
        _rate_limiters[key] = limiter

    return limiter


def _construct_text_driver(provider: str, model_name: Optional[str] = None):
    """Construct a fresh LLM driver for the given provider/model.

    Args:
        provider: Provider name (e.g., "mock", "offline", "gemini")
        model_name: Optional specific model to use (e.g., "gemini-2.5-pro")

    Returns driver that supports generate_text method.
    """
    if provider == "offline":
        return OfflineDriver()

    if provider == "gemini":
        try:
            from llm.gemini_driver import GeminiDriver
            return GeminiDriver(model_name=model_name)
        except (ImportError, RuntimeError, ValueError) as e:
            print(f"[WARNING] Failed to initialize Gemini driver: {e}")
            print("[WARNING] Falling back to mock driver")
            return MockDeterministicDriver()

    if provider == "openai_compat":
        try:
            from llm.openai_compat_driver import OpenAICompatDriver
            return OpenAICompatDriver(model_name=model_name)
        except (ImportError, RuntimeError, ValueError) as e:
            print(f"[WARNING] Failed to initialize OpenAI-compatible driver: {e}")
            print("[WARNING] Falling back to mock driver")
            return MockDeterministicDriver()

    # Default to mock for testing
    return MockDeterministicDriver()


def _get_text_driver(model_name: Optional[str] = None):
    """Get LLM driver for text generation (cached per provider+model).

    Args:
        model_name: Optional specific model to use (e.g., "gemini-2.5-pro")

    Returns driver that supports generate_text method. A different
    model_name constructs (and caches) a separate driver instance.
    """
    provider = _get_provider()
    cache_key = (provider, model_name)

    driver = _driver_cache.get(cache_key)
    if driver is None:
        driver = _construct_text_driver(provider, model_name)
        _driver_cache[cache_key] = driver

    return driver


def generate_text(
    prompt: str, 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """Generate text using configured LLM provider.
    
    Args:
        prompt: Prompt text
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection (e.g., LLMContext.INJECT_GENERATION)
        model_override: Optional explicit model name (overrides context-based selection)
        system_instruction: Optional system instruction for the model
        temperature: Optional temperature override
        max_tokens: Optional max tokens override
    
    Returns:
        Generated text response
    """
    # Determine model to use: override, else context tier resolved per provider
    provider = _get_provider()
    model_name = _resolve_call_model(provider, context, model_override)

    driver = _get_text_driver(model_name)

    # Apply rate limiting before making request (model-specific limits).
    # Mock/offline drivers never hit the network (including when they are
    # fallbacks for a failed Gemini init), so skip throttling entirely.
    if not isinstance(driver, (MockDeterministicDriver, OfflineDriver)):
        rate_limiter = get_rate_limiter(model_name)
        if rate_limiter:
            rate_limiter.wait_if_needed(verbose=True)

    # Show spinner if requested (and not in mock mode)
    use_spinner = show_spinner and provider not in ["mock", "offline"]

    # Out-param the driver fills with call metadata (finish_reason); the
    # resilient wrapper marks mock fallbacks in it too. Feeds the call log.
    meta: dict = {}

    # Helper to call driver with optional args
    def call_driver():
        if hasattr(driver, 'generate_text'):
            # Check if driver accepts additional args - by name, or via a
            # **kwargs catch-all (the mock/offline drivers accept-and-ignore)
            import inspect
            sig = inspect.signature(driver.generate_text)
            catch_all = any(p.kind is inspect.Parameter.VAR_KEYWORD
                            for p in sig.parameters.values())
            def accepts(name):
                return name in sig.parameters or catch_all
            kwargs = {}
            if accepts('system_instruction') and system_instruction:
                kwargs['system_instruction'] = system_instruction
            if accepts('temperature') and temperature is not None:
                kwargs['temperature'] = temperature
            if accepts('max_tokens') and max_tokens is not None:
                kwargs['max_tokens'] = max_tokens
            if accepts('meta_out'):
                kwargs['meta_out'] = meta

            return driver.generate_text(prompt, rng, **kwargs)
        return f"[LLM response to: {prompt[:50]}...]"

    # Resilient wrapper: retry once on failure, then fall back to the mock
    # driver so a runtime API error (429, network blip) never crashes the game
    def call_driver_resilient():
        try:
            return call_driver()
        except Exception:
            time.sleep(2)  # Short backoff before retrying once
            try:
                return call_driver()
            except Exception as e:
                print(f"[WARNING] LLM call failed ({type(e).__name__}: {e}); "
                      "using offline advisor response for this call")
                from llm.parse_health import record_fallback
                record_fallback("router", type(e).__name__)
                meta['fallback'] = True
                return MockDeterministicDriver().generate_text(prompt, rng)

    def call_and_log():
        from llm import call_log
        start = _now()
        result = call_driver_resilient()
        _record_truncation_if_cut(meta, context, provider)
        if call_log.enabled():
            tier = (get_model_config().get_tier_for_context(context).value
                    if context else None)
            call_log.record(
                family=context.value if context else None,
                tier=tier,
                provider=provider,
                model=model_name,
                prompt=prompt,
                reply=result,
                finish_reason=meta.get('finish_reason'),
                latency_ms=int((_now() - start) * 1000),
                fallback=bool(meta.get('fallback')),
            )
        return result

    if use_spinner:
        # Tuman sonar-sweep wait indicator (see cli/spinner.py). Only the
        # import sits in the try: a driver-side ImportError must propagate to
        # the resilient wrapper, not silently trigger a duplicate LLM call.
        try:
            from cli.spinner import Spinner
        except ImportError:
            pass
        else:
            with Spinner("AWAITING SECURE TRAFFIC"):
                return call_and_log()

    # No spinner - direct call
    return call_and_log()


def batch_generate_text(
    prompts: list[str],
    rng: Random,
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None,
    max_tokens: Optional[int] = None
) -> list[str]:
    """Generate multiple text responses in parallel using configured LLM provider.

    NOTE: On a rate-limited provider a slot is claimed for every prompt
    before the group is dispatched, so the limit still holds when the calls
    go out together.

    Args:
        prompts: List of prompt texts to generate responses for
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection
        model_override: Optional explicit model name
        max_tokens: Optional output cap applied to every prompt in the batch.
            Without this the batch path could not express what several call
            sites depend on - character responses are capped at 150 tokens -
            so those groups had no way to use it even though their calls are
            independent of one another.

    Returns:
        List of generated text responses in same order as prompts
    """
    if not prompts:
        return []
    
    # Determine model to use: override, else context tier resolved per provider
    provider = _get_provider()
    model_name = _resolve_call_model(provider, context, model_override)

    driver = _get_text_driver(model_name)

    # Get rate limiter (will apply per request in sequential mode, model-specific).
    # Mock/offline drivers never hit the network, so skip throttling entirely.
    if isinstance(driver, (MockDeterministicDriver, OfflineDriver)):
        rate_limiter = None
    else:
        rate_limiter = get_rate_limiter(model_name)

    # Show spinner if requested (and not in mock mode)
    use_spinner = show_spinner and provider not in ["mock", "offline"]

    # Per-prompt metadata out-params (finish_reason, fallback), filled by
    # drivers that support them; feeds the call log.
    metas: list = [{} for _ in prompts]

    # Only forward max_tokens / meta_out to callables that accept them - by
    # name, or via a **kwargs catch-all (the mock/offline drivers
    # accept-and-ignore). Passing an argument a signature does not admit
    # would turn a graceful fallback into a TypeError.
    def batch_kwargs(fn, meta_out=None):
        import inspect
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return {}
        catch_all = any(p.kind is inspect.Parameter.VAR_KEYWORD
                        for p in sig.parameters.values())
        def accepts(name):
            return name in sig.parameters or catch_all
        kwargs = {}
        if max_tokens is not None and accepts('max_tokens'):
            kwargs['max_tokens'] = max_tokens
        if meta_out is not None and accepts('meta_out'):
            kwargs['meta_out'] = meta_out
        return kwargs

    # Helper for batch call
    def call_batch():
        if hasattr(driver, 'batch_generate_text'):
            # Claim a rate-limit slot per prompt *before* dispatching. The
            # driver fans the group out across a thread pool and never sees
            # the limiter, so without this the whole group leaves at once and
            # blows straight through a configured RPM - which nothing noticed
            # while this function had no callers. Claiming up front keeps the
            # limit honest and still lets the group go out concurrently
            # whenever the limit is not actually binding.
            def claim_slots():
                if rate_limiter:
                    for _ in prompts:
                        rate_limiter.wait_if_needed(verbose=False)

            claim_slots()
            kwargs = batch_kwargs(driver.batch_generate_text, meta_out=metas)
            # Retry once on failure, then fall back to the mock driver so a
            # runtime API error never crashes the game
            try:
                return driver.batch_generate_text(prompts, rng, **kwargs)
            except Exception:
                time.sleep(2)  # Short backoff before retrying once
                try:
                    # The retry re-sends every prompt, so it has to be
                    # accounted for too. The first batch failure is most often
                    # the rate limit itself, which makes this the dispatch
                    # most likely to breach it.
                    claim_slots()
                    return driver.batch_generate_text(prompts, rng, **kwargs)
                except Exception as e:
                    print(f"[WARNING] LLM batch call failed ({type(e).__name__}: {e}); "
                          "using offline advisor responses for this call")
                    from llm.parse_health import record_fallback
                    record_fallback("router", f"batch {type(e).__name__}")
                    for m in metas:
                        m['fallback'] = True
                    return MockDeterministicDriver().batch_generate_text(prompts, rng)
        # Fallback sequential - forwards max_tokens where the signature
        # admits it, same as the batch path (ER-011: this used to call bare)
        results = []
        for i, prompt in enumerate(prompts):
            if rate_limiter:
                rate_limiter.wait_if_needed(verbose=False)
            if hasattr(driver, 'generate_text'):
                results.append(driver.generate_text(
                    prompt, rng,
                    **batch_kwargs(driver.generate_text, meta_out=metas[i])))
            else:
                results.append(f"[LLM response to: {prompt[:50]}...]")
        return results

    def batch_and_log(runner):
        from llm import call_log
        start = _now()
        results = runner()
        for m in metas:
            _record_truncation_if_cut(m, context, provider)
        if call_log.enabled():
            tier = (get_model_config().get_tier_for_context(context).value
                    if context else None)
            elapsed_ms = int((_now() - start) * 1000)
            for i, (p, r) in enumerate(zip(prompts, results)):
                m = metas[i] if i < len(metas) else {}
                call_log.record(
                    family=context.value if context else None,
                    tier=tier,
                    provider=provider,
                    model=model_name,
                    prompt=p,
                    reply=r,
                    finish_reason=m.get('finish_reason'),
                    latency_ms=elapsed_ms,
                    fallback=bool(m.get('fallback')),
                    batch_index=i,
                    batch_size=len(prompts),
                )
        return results
    
    if use_spinner:
        # Tuman sonar-sweep wait indicator (see cli/spinner.py). Only the
        # import sits in the try: a driver-side ImportError must propagate to
        # the resilient retry logic, not silently trigger a duplicate call.
        try:
            from cli.spinner import Spinner
        except ImportError:
            pass
        else:
            with Spinner(f"SIGNALS INBOUND ── {len(prompts)} STATIONS"):
                return batch_and_log(call_batch)

    return batch_and_log(call_batch)
