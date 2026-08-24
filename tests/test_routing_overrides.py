"""Tests for the runtime routing override registry (llm/routing_overrides)
and its consultation by the router's resolution path.

The reroute matrix must let an operator pin one context to a tier, an
explicit model, or a different provider - without touching the defaults or
any other context - and clearing must restore exactly the default routing.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from llm import router, routing_overrides
from llm.model_config import (
    LLMContext, ModelTier, get_model_config, reset_to_defaults,
)


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    """Every test starts from default routing and a mock provider."""
    monkeypatch.setenv("WARGAME_LLM", "mock")
    monkeypatch.delenv("WARGAME_CALL_LOG", raising=False)
    routing_overrides.clear_all()
    reset_to_defaults()
    yield
    routing_overrides.clear_all()
    reset_to_defaults()


# --- registry semantics ---------------------------------------------------

def test_no_override_resolves_default_tier():
    context = LLMContext.ADVISOR_QA  # PRO by default
    assert routing_overrides.get_override(context) is None
    assert routing_overrides.effective_tier(context) is ModelTier.PRO


def test_tier_override_changes_effective_tier_for_that_context_only():
    routing_overrides.set_override(LLMContext.ADVISOR_QA, tier=ModelTier.FLASH)
    assert routing_overrides.effective_tier(LLMContext.ADVISOR_QA) is ModelTier.FLASH
    # A neighbouring context keeps its default.
    assert routing_overrides.effective_tier(LLMContext.QUALITY_ASSESSMENT) is ModelTier.PRO
    # The defaults table itself is untouched.
    assert get_model_config().get_tier_for_context(LLMContext.ADVISOR_QA) is ModelTier.PRO


def test_clear_override_restores_default():
    routing_overrides.set_override(LLMContext.NARRATOR, tier=ModelTier.PRO)
    assert routing_overrides.effective_tier(LLMContext.NARRATOR) is ModelTier.PRO
    assert routing_overrides.clear_override(LLMContext.NARRATOR) is True
    assert routing_overrides.effective_tier(LLMContext.NARRATOR) is ModelTier.FLASH
    # Clearing twice reports nothing to clear.
    assert routing_overrides.clear_override(LLMContext.NARRATOR) is False


def test_empty_override_is_rejected():
    with pytest.raises(ValueError):
        routing_overrides.set_override(LLMContext.NARRATOR)


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError):
        routing_overrides.set_override(LLMContext.NARRATOR, provider="banana")


def test_snapshot_is_json_ready():
    routing_overrides.set_override(LLMContext.NARRATOR, tier=ModelTier.PRO,
                                   model="some-model")
    snap = routing_overrides.snapshot()
    assert snap == {
        "narrator": {"tier": "pro", "provider": None, "model": "some-model"},
    }


# --- router resolution path -----------------------------------------------

def test_router_resolves_tier_override_on_gemini_names():
    """On the gemini provider a FLASH-pinned PRO context must resolve to the
    flash model name."""
    context = LLMContext.ADVISOR_QA  # PRO by default -> gemini-2.5-pro
    assert router._resolve_call_model("gemini", context, None) == "gemini-2.5-pro"
    routing_overrides.set_override(context, tier=ModelTier.FLASH)
    assert router._resolve_call_model("gemini", context, None) == "gemini-2.5-flash"


def test_router_resolves_model_override_verbatim():
    context = LLMContext.NARRATOR
    routing_overrides.set_override(context, model="exp/some-exact-model")
    assert router._resolve_call_model("gemini", context, None) == "exp/some-exact-model"


def test_explicit_call_site_override_still_wins():
    """The generate_text(model_override=...) argument outranks the registry."""
    context = LLMContext.NARRATOR
    routing_overrides.set_override(context, model="registry-model")
    assert router._resolve_call_model(
        "gemini", context, "call-site-model") == "call-site-model"


def test_router_resolves_provider_override():
    context = LLMContext.NARRATOR
    assert router._resolve_call_provider(context) == "mock"  # WARGAME_LLM
    routing_overrides.set_override(context, provider="offline")
    assert router._resolve_call_provider(context) == "offline"
    # Other contexts keep the configured provider.
    assert router._resolve_call_provider(LLMContext.ADVISOR_QA) == "mock"


def test_no_context_resolves_configured_provider():
    assert router._resolve_call_provider(None) == "mock"
    assert router._resolve_call_model("mock", None, None) is None


def test_generate_text_end_to_end_with_override(monkeypatch):
    """A rerouted context still generates (mock provider), and the call log
    listener sees the overridden tier - the matrix is observable."""
    from random import Random
    from llm import call_log

    routing_overrides.set_override(LLMContext.NARRATOR, tier=ModelTier.PRO)

    seen = []
    call_log.add_listener(seen.append)
    try:
        reply = router.generate_text(
            "One line of atmosphere.", Random(1), show_spinner=False,
            context=LLMContext.NARRATOR)
    finally:
        call_log.remove_listener(seen.append)

    assert isinstance(reply, str) and reply
    assert len(seen) == 1
    assert seen[0]["family"] == "narrator"
    assert seen[0]["tier"] == "pro"  # the override, not the FLASH default


def test_thread_safety_smoke():
    """Concurrent set/clear/read must not corrupt the registry."""
    errors = []

    def worker(index: int):
        try:
            context = list(LLMContext)[index % len(list(LLMContext))]
            for _ in range(200):
                routing_overrides.set_override(context, tier=ModelTier.FLASH)
                routing_overrides.effective_tier(context)
                routing_overrides.snapshot()
                routing_overrides.clear_override(context)
        except Exception as e:  # pragma: no cover - failure reporting
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
