"""OpenAI-compatible chat-completions driver.

One driver that speaks the de-facto standard `/chat/completions` protocol,
unlocking any provider that exposes an OpenAI-style endpoint:

- OpenRouter        https://openrouter.ai/api/v1   (free ":free" models)
- Groq              https://api.groq.com/openai/v1
- Cerebras          https://api.cerebras.ai/v1
- Mistral           https://api.mistral.ai/v1
- Ollama (local)    http://localhost:11434/v1      (no API key needed)
- LM Studio (local) http://localhost:1234/v1       (no API key needed)

Configuration (environment variable first, then config.py):
- OPENAI_COMPAT_BASE_URL  e.g. "https://openrouter.ai/api/v1"  (required)
- OPENAI_COMPAT_API_KEY   provider API key (optional for local servers)
- OPENAI_COMPAT_MODEL     model id, e.g. "qwen3:8b" (required)

Uses the `requests` package (already a core dependency) - no provider SDK.
Errors are raised to the router, which retries once and then degrades
gracefully to the mock driver, same as the Gemini driver.
"""

import os
import re as _re
import time
from random import Random
from typing import Optional

import requests

def _retry_delay_seconds(response):
    """Extract a rate-limit recovery delay from a 429 (header or body).

    Returns None when the response names no usable window, in which case
    the caller falls through to the normal error path.
    """
    headers = getattr(response, "headers", None) or {}
    ra = headers.get("retry-after")
    if ra:
        try:
            return float(ra)
        except (TypeError, ValueError):
            pass
    text = getattr(response, "text", "") or ""
    m = _re.search(r"try again in (?:(\d+)m)?([\d.]+)s", text)
    if m:
        minutes = int(m.group(1) or 0)
        return minutes * 60 + float(m.group(2))
    return None


# Seconds before a hung request is abandoned (matches the Gemini driver).
# Overridable for slow local backends — CPU-only Ollama inference routinely
# needs longer than a hosted endpoint.
REQUEST_TIMEOUT = int(os.environ.get("OPENAI_COMPAT_TIMEOUT", "60"))


def _truncate(text: str, limit: int = 300) -> str:
    """Truncate long strings (e.g. response bodies) for error messages."""
    if len(text) <= limit:
        return text
    return text[:limit] + "... [truncated]"


def _config_value(env_name: str, config_name: str, default: Optional[str] = None) -> Optional[str]:
    """Resolve a setting from the environment first, then config.py."""
    value = os.getenv(env_name)
    if value:
        return value
    try:
        import config
        value = getattr(config, config_name, None)
        if value:
            return value
    except ImportError:
        pass
    return default


class OpenAICompatDriver:
    """Driver for any OpenAI-compatible chat-completions endpoint.

    Plain HTTP via `requests` - no heavy SDK. The router's resilience
    wrapper (retry once, then fall back to the mock driver) handles any
    exception this driver raises.
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the driver.

        Args:
            model_name: Optional explicit model id. Gemini-style names
                (``gemini-*``) coming from the tier-based model config are
                ignored in favour of OPENAI_COMPAT_MODEL, so the game's
                Flash/Pro tier selection doesn't break other providers.

        Raises:
            ValueError: If OPENAI_COMPAT_BASE_URL or a model id is not
                configured (the router falls back to the mock driver).
        """
        base_url = _config_value("OPENAI_COMPAT_BASE_URL", "OPENAI_COMPAT_BASE_URL")
        if not base_url:
            raise ValueError(
                "OPENAI_COMPAT_BASE_URL not found in environment or config.py. "
                "Example: https://openrouter.ai/api/v1 or http://localhost:11434/v1. "
                "See docs/LLM_PROVIDERS.md."
            )
        self.base_url = base_url.rstrip("/")

        # Gemini tier names come from llm.model_config when the router picks
        # a model per context; they mean nothing to other providers.
        if model_name and not model_name.lower().startswith("gemini"):
            self.model_name = model_name
        else:
            self.model_name = _config_value("OPENAI_COMPAT_MODEL", "OPENAI_COMPAT_MODEL")
        if not self.model_name:
            raise ValueError(
                "OPENAI_COMPAT_MODEL not found in environment or config.py. "
                "Example: \"meta-llama/llama-3.3-70b-instruct:free\" (OpenRouter) "
                "or \"qwen3:8b\" (Ollama). See docs/LLM_PROVIDERS.md."
            )

        # Local servers (Ollama, LM Studio) don't need a key.
        self.api_key = _config_value("OPENAI_COMPAT_API_KEY", "OPENAI_COMPAT_API_KEY")

        temperature = _config_value("OPENAI_COMPAT_TEMPERATURE", "OPENAI_COMPAT_TEMPERATURE")
        max_tokens = _config_value("OPENAI_COMPAT_MAX_TOKENS", "OPENAI_COMPAT_MAX_TOKENS")
        self.temperature = float(temperature) if temperature is not None else 0.7
        self.max_tokens = int(max_tokens) if max_tokens is not None else 2048

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate_text(
        self,
        prompt: str,
        rng: Random,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a text response via the chat-completions endpoint.

        Args:
            prompt: Input prompt text
            rng: Random number generator (parity with other drivers; the
                seed is sent as ``seed`` where the provider supports it)
            system_instruction: Optional system message
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            Generated text response

        Raises:
            Exception: If the request fails or the response has no text.
                The router retries once, then falls back to the mock driver.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            # Best-effort determinism; OpenAI-compatible servers that don't
            # support seeding simply ignore the field.
            "seed": rng.randint(0, 2**31 - 1),
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 429:
                # Rate-limited: the provider names its recovery window
                # (Retry-After header, or "try again in Xs" in the body).
                # Waiting it out beats an instant doomed retry.
                delay = _retry_delay_seconds(response)
                if delay is not None and delay <= 120:
                    time.sleep(delay + 0.5)
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                        timeout=REQUEST_TIMEOUT,
                    )
            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}: {_truncate(response.text)}"
                )
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError(
                    f"No choices in response: {_truncate(repr(data))}"
                )
            message = choices[0].get("message") or {}
            text = message.get("content")
            if not text or not text.strip():
                raise RuntimeError(
                    f"Empty completion. Finish reason: "
                    f"{choices[0].get('finish_reason', 'UNKNOWN')}"
                )
            return text.strip()
        except Exception as e:
            # Keep the original type in the message and truncate payloads,
            # matching the Gemini driver's error convention.
            raise Exception(
                f"OpenAI-compatible API error ({type(e).__name__}): "
                f"{_truncate(str(e))}"
            ) from e

    def batch_generate_text(self, prompts: list[str], rng: Random) -> list[str]:
        """Generate multiple responses concurrently.

        Mirrors GeminiDriver.batch_generate_text: individual failures are
        returned as "[ERROR: ...]" strings so one bad call doesn't lose the
        whole batch.

        Args:
            prompts: List of prompt texts
            rng: Random number generator

        Returns:
            List of responses in the same order as prompts
        """
        if not prompts:
            return []

        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Pre-draw seeds so results don't depend on thread scheduling.
        seeds = [rng.randint(0, 2**31 - 1) for _ in prompts]

        def generate_single(index: int) -> str:
            try:
                return self.generate_text(prompts[index], Random(seeds[index]))
            except Exception as e:
                return f"[ERROR: {_truncate(str(e), 200)}]"

        # Keep concurrency modest: free-tier endpoints have tight RPM limits
        # and local servers process requests serially anyway.
        max_workers = min(len(prompts), 4)
        results: list = [None] * len(prompts)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(generate_single, i): i for i in range(len(prompts))
            }
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:  # pragma: no cover - generate_single catches
                    results[index] = f"[ERROR: {_truncate(str(e), 200)}]"

        return results

    def __repr__(self) -> str:
        return f"OpenAICompatDriver(base_url={self.base_url}, model={self.model_name})"
