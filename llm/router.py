"""LLM router for provider-agnostic text generation and legacy proposal selection.

Supports multiple LLM providers:
- mock (default): Deterministic mock responses for testing
- offline: Pre-recorded responses
- gemini: Google Gemini 2.5 Flash/Pro (requires GOOGLE_API_KEY)
- openai: OpenAI API (future)
- anthropic: Anthropic API (future)

Configuration priority:
1. Environment variable WARGAME_LLM (if set)
2. config.py LLM_PROVIDER (if file exists)
3. Default to "mock"

Model selection per context:
- Configured via llm.model_config
- Allows Flash vs Pro per system (advisor, inject, diplomacy, etc.)
"""

import os
import time
from random import Random
from typing import Optional
from collections import deque

from llm.mock_driver import MockDeterministicDriver
from llm.offline_driver import OfflineDriver
from llm.model_config import LLMContext, get_model_config


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
    
    def wait_if_needed(self, verbose: bool = True):
        """Wait if necessary to stay within rate limits.
        
        Args:
            verbose: If True, print messages when waiting
        """
        now = time.time()
        
        # Remove requests older than the window
        while self.request_times and (now - self.request_times[0]) > self.window_seconds:
            self.request_times.popleft()
        
        # If we've hit the limit, wait until the oldest request expires
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = self.request_times[0]
            wait_time = self.window_seconds - (now - oldest_request)
            
            if wait_time > 0:
                if verbose:
                    print(f"\n[Rate Limit] Waiting {wait_time:.1f}s to stay within {self.requests_per_minute} requests/min limit...")
                time.sleep(wait_time + 0.1)  # Add small buffer
        
        # Record this request
        self.request_times.append(time.time())


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

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


def get_rate_limiter(model_name: Optional[str] = None) -> Optional[RateLimiter]:
    """Get or create the global rate limiter.

    Args:
        model_name: Model being used (determines RPM limit)

    Returns:
        RateLimiter instance if using a rate-limited provider, None otherwise
    """
    global _rate_limiter

    # Check provider
    provider = _get_provider()

    # Only rate limit for real API providers
    if provider not in ["gemini"]:
        return None
    
    # Determine RPM based on model (free tier limits)
    # Flash: 10 RPM, Pro: 2 RPM (from Google AI Studio dashboard)
    rpm = int(os.getenv("GEMINI_RPM", "0"))  # 0 = auto-detect
    
    if rpm == 0:  # Auto-detect based on model
        if model_name and "flash" in model_name.lower():
            rpm = 10  # Flash models: 10 RPM
        else:
            rpm = 2   # Pro models: 2 RPM
    
    # Create rate limiter if not exists or if RPM changed
    if _rate_limiter is None or _rate_limiter.requests_per_minute != rpm:
        _rate_limiter = RateLimiter(requests_per_minute=rpm)
    
    return _rate_limiter


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
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None  # Use driver default
    
    driver = _get_text_driver(model_name)

    # Apply rate limiting before making request (model-specific limits).
    # Mock/offline drivers never hit the network (including when they are
    # fallbacks for a failed Gemini init), so skip throttling entirely.
    if not isinstance(driver, (MockDeterministicDriver, OfflineDriver)):
        rate_limiter = get_rate_limiter(model_name)
        if rate_limiter:
            rate_limiter.wait_if_needed(verbose=True)

    # Show spinner if requested (and not in mock mode)
    provider = _get_provider()
    use_spinner = show_spinner and provider not in ["mock", "offline"]

    # Helper to call driver with optional args
    def call_driver():
        if hasattr(driver, 'generate_text'):
            # Check if driver accepts additional args
            import inspect
            sig = inspect.signature(driver.generate_text)
            kwargs = {}
            if 'system_instruction' in sig.parameters and system_instruction:
                kwargs['system_instruction'] = system_instruction
            if 'temperature' in sig.parameters and temperature is not None:
                kwargs['temperature'] = temperature
            if 'max_tokens' in sig.parameters and max_tokens is not None:
                kwargs['max_tokens'] = max_tokens

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
                return MockDeterministicDriver().generate_text(prompt, rng)

    if use_spinner:
        try:
            # Use rich console status instead of custom Spinner class
            from cli.rich_ui import console
            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                return call_driver_resilient()
        except ImportError:
            # If rich import fails, try legacy Spinner
            try:
                from cli.spinner import Spinner
                with Spinner("Thinking"):
                    return call_driver_resilient()
            except ImportError:
                pass

    # No spinner - direct call
    return call_driver_resilient()


def batch_generate_text(
    prompts: list[str], 
    rng: Random, 
    show_spinner: bool = True,
    context: Optional[LLMContext] = None,
    model_override: Optional[str] = None
) -> list[str]:
    """Generate multiple text responses in parallel using configured LLM provider.
    
    NOTE: For rate-limited providers, this will wait between requests.
    
    Args:
        prompts: List of prompt texts to generate responses for
        rng: Random number generator for determinism
        show_spinner: If True, show loading spinner during generation
        context: Optional usage context for model selection
        model_override: Optional explicit model name
    
    Returns:
        List of generated text responses in same order as prompts
    """
    if not prompts:
        return []
    
    # Determine model to use
    if model_override:
        model_name = model_override
    elif context:
        model_name = get_model_config().get_model_for_context(context)
    else:
        model_name = None
    
    driver = _get_text_driver(model_name)

    # Get rate limiter (will apply per request in sequential mode, model-specific).
    # Mock/offline drivers never hit the network, so skip throttling entirely.
    if isinstance(driver, (MockDeterministicDriver, OfflineDriver)):
        rate_limiter = None
    else:
        rate_limiter = get_rate_limiter(model_name)

    # Show spinner if requested (and not in mock mode)
    provider = _get_provider()
    use_spinner = show_spinner and provider not in ["mock", "offline"]

    # Helper for batch call
    def call_batch():
        if hasattr(driver, 'batch_generate_text'):
            # Retry once on failure, then fall back to the mock driver so a
            # runtime API error never crashes the game
            try:
                return driver.batch_generate_text(prompts, rng)
            except Exception:
                time.sleep(2)  # Short backoff before retrying once
                try:
                    return driver.batch_generate_text(prompts, rng)
                except Exception as e:
                    print(f"[WARNING] LLM batch call failed ({type(e).__name__}: {e}); "
                          "using offline advisor responses for this call")
                    return MockDeterministicDriver().batch_generate_text(prompts, rng)
        # Fallback sequential
        results = []
        for prompt in prompts:
            if rate_limiter:
                rate_limiter.wait_if_needed(verbose=False)
            if hasattr(driver, 'generate_text'):
                results.append(driver.generate_text(prompt, rng))
            else:
                results.append(f"[LLM response to: {prompt[:50]}...]")
        return results
    
    if use_spinner:
        try:
            from cli.rich_ui import console
            with console.status(f"[bold cyan]Simulating {len(prompts)} actors...[/bold cyan]", spinner="dots"):
                return call_batch()
        except ImportError:
            try:
                from cli.spinner import Spinner
                with Spinner(f"Simulating {len(prompts)} actors"):
                    return call_batch()
            except ImportError:
                pass
        
    return call_batch()
