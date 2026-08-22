"""Runtime, per-context model-routing overrides for the LLM router.

The default routing lives in llm.model_config (LLMContext -> ModelTier ->
provider model name). This registry lets an operator reroute any single
context at runtime - from the dashboard's reroute matrix - without touching
the defaults: pin a context to a tier, to an explicit model name, or to a
different provider entirely.

Resolution order the router applies per call (see router._resolve_call_model
and router._resolve_call_provider):

  1. explicit ``model_override`` argument at the call site (unchanged, wins)
  2. this registry's ``model`` for the context, verbatim
  3. this registry's ``tier`` for the context, resolved per provider
  4. the model_config default tier for the context, resolved per provider

The provider resolves as: registry ``provider`` for the context, else the
process-wide configured provider.

Thread-safe and process-wide: batch drivers dispatch from a thread pool and
the API mutates this from request handlers.
"""

import threading
from dataclasses import dataclass
from typing import Dict, Optional

from llm.model_config import LLMContext, ModelTier, get_model_config

#: Providers the router knows how to construct drivers for.
KNOWN_PROVIDERS = ("gemini", "openai_compat", "mock", "offline")

_lock = threading.Lock()
_overrides: Dict[LLMContext, "RoutingOverride"] = {}


@dataclass(frozen=True)
class RoutingOverride:
    """One context's reroute. Unset fields fall through to the defaults."""

    tier: Optional[ModelTier] = None
    provider: Optional[str] = None
    model: Optional[str] = None

    def is_empty(self) -> bool:
        return self.tier is None and self.provider is None and self.model is None


def set_override(context: LLMContext,
                 tier: Optional[ModelTier] = None,
                 provider: Optional[str] = None,
                 model: Optional[str] = None) -> RoutingOverride:
    """Install (replace) the override for one context.

    Raises ValueError on an unknown provider - failing fast at the API
    boundary beats a driver silently falling back to mock mid-campaign.
    """
    if provider is not None and provider not in KNOWN_PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider}'; expected one of {KNOWN_PROVIDERS}"
        )
    override = RoutingOverride(tier=tier, provider=provider, model=model)
    if override.is_empty():
        raise ValueError("Override must set at least one of tier/provider/model")
    with _lock:
        _overrides[context] = override
    return override


def get_override(context: Optional[LLMContext]) -> Optional[RoutingOverride]:
    """The override for a context, or None."""
    if context is None:
        return None
    with _lock:
        return _overrides.get(context)


def clear_override(context: LLMContext) -> bool:
    """Remove one context's override. Returns True if one existed."""
    with _lock:
        return _overrides.pop(context, None) is not None


def clear_all() -> None:
    with _lock:
        _overrides.clear()


def effective_tier(context: LLMContext) -> ModelTier:
    """The tier a call for this context resolves to: override, else default.

    A ``model`` override bypasses tiers entirely; callers that log the tier
    still get the tier the context would otherwise use.
    """
    override = get_override(context)
    if override and override.tier is not None:
        return override.tier
    return get_model_config().get_tier_for_context(context)


def snapshot() -> Dict[str, Dict[str, Optional[str]]]:
    """JSON-ready view of every installed override, keyed by context value."""
    with _lock:
        items = list(_overrides.items())
    return {
        context.value: {
            "tier": override.tier.value if override.tier else None,
            "provider": override.provider,
            "model": override.model,
        }
        for context, override in items
    }
