"""Control-surface endpoints: reroute matrix, inject console, prompt editor.

The facilitator's levers, kept out of api/server.py so the game-flow
endpoints stay readable. Mounted onto the app by server.py; handlers import
the session table lazily to avoid an import cycle.

- /routing            runtime per-context model routing (llm/routing_overrides)
- /game/{id}/inject   fire a facilitator-authored inject into a live session
- /prompts            hot-edit the extracted prompt templates (llm/prompt_templates)
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.layers import Layer, layer_for_channel

router = APIRouter()


# --- Reroute matrix -------------------------------------------------------

class RoutingOverrideRequest(BaseModel):
    tier: Optional[str] = None      # "flash" | "pro"
    provider: Optional[str] = None  # gemini | openai_compat | mock | offline
    model: Optional[str] = None     # explicit model name, verbatim


def _context_or_404(context_value: str):
    from llm.model_config import LLMContext
    try:
        return LLMContext(context_value)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown LLM context '{context_value}'; expected one of "
                   f"{[c.value for c in LLMContext]}"
        )


@router.get("/routing")
async def get_routing_matrix() -> Dict[str, Any]:
    """The effective routing matrix: one row per LLMContext.

    ``effective_*`` is what the router will actually use for the next call
    of that family - default config with any runtime override applied.
    """
    from llm.model_config import LLMContext, get_model_config, resolve_model_name
    from llm.router import _get_provider
    from llm import routing_overrides

    config = get_model_config()
    default_provider = _get_provider()
    overrides = routing_overrides.snapshot()

    rows: List[Dict[str, Any]] = []
    for context in LLMContext:
        override = overrides.get(context.value)
        default_tier = config.get_tier_for_context(context)
        effective_tier = routing_overrides.effective_tier(context)
        effective_provider = (override or {}).get("provider") or default_provider
        effective_model = ((override or {}).get("model")
                           or resolve_model_name(effective_provider, effective_tier))
        rows.append({
            "context": context.value,
            "default_tier": default_tier.value,
            "effective_tier": effective_tier.value,
            "effective_provider": effective_provider,
            "effective_model": effective_model,
            "override": override,
        })
    return {"provider": default_provider, "contexts": rows}


@router.post("/routing/{context_value}")
async def set_routing_override(context_value: str,
                               request: RoutingOverrideRequest):
    """Install a runtime override for one context (tier/provider/model)."""
    from llm.model_config import ModelTier
    from llm import routing_overrides

    context = _context_or_404(context_value)

    tier = None
    if request.tier is not None:
        try:
            tier = ModelTier(request.tier.lower())
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown tier '{request.tier}'; expected one of "
                       f"{[t.value for t in ModelTier]}"
            )

    try:
        override = routing_overrides.set_override(
            context, tier=tier, provider=request.provider,
            model=request.model)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "status": "override_set",
        "context": context.value,
        "override": {
            "tier": override.tier.value if override.tier else None,
            "provider": override.provider,
            "model": override.model,
        },
    }


@router.delete("/routing/{context_value}")
async def clear_routing_override(context_value: str):
    """Clear one context's runtime override (back to the defaults)."""
    from llm import routing_overrides

    context = _context_or_404(context_value)
    existed = routing_overrides.clear_override(context)
    return {"status": "override_cleared" if existed else "no_override",
            "context": context.value}


# --- Inject console -------------------------------------------------------

class ManualInjectRequest(BaseModel):
    headline: str
    content: str
    channel: str = "briefing"   # briefing/intelligence/emergency/diplomatic/
                                # flash_alert/media/military (models/layers.py)
    # Optional metric effects, episode-file shape:
    # [{"metric": "escalation_risk", "delta": 5}, ...]
    effects: List[Dict[str, Any]] = []
    # Optional free-text target note (a country, a region); carried into the
    # description so advisors see it - the engine has no per-target routing.
    target: Optional[str] = None


@router.post("/game/{session_id}/inject")
async def fire_manual_inject(session_id: str, request: ManualInjectRequest):
    """Fire a facilitator-authored inject into a running session (EXCON).

    Delivery goes through GameManager.deliver_inject - the same primitives
    a scripted briefing inject uses (description into the transcript,
    effects onto the metrics, title into recent_injects) - and the event
    appears in the stream ledger like any other inject, on the layer its
    channel names.
    """
    from api.server import _session_or_404
    import time as _time

    session = _session_or_404(session_id)
    # EXCON lever: only sessions created WITH the facilitator flag accept
    # injects. A player session's id must not be enough to rewrite its
    # world (the flag is fixed at create time - see NewGameRequest).
    if not session.facilitator:
        raise HTTPException(
            status_code=403,
            detail="Inject console targets facilitator sessions only; "
                   "this session was created without the facilitator flag.")

    description = request.content
    if request.target:
        description = f"[{request.target}] {description}"

    inject = {
        "id": f"manual_{int(_time.time())}",
        "title": request.headline,
        "channel": request.channel,
        "description": description,
        "effects": request.effects or [],
    }

    try:
        # deliver_inject is a read-then-write on world.metrics; the session
        # lock keeps it atomic against the demo driver's thread and other
        # mutating endpoints.
        with session.lock:
            delivered = session.manager.deliver_inject(inject)
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inject delivery failed: {e}")

    layer = layer_for_channel(delivered["channel"])
    await session.push_event("transcript", {
        "type": "inject",
        "title": delivered["title"],
        "channel": delivered["channel"],
        "content": description,
        "manual": True,
    }, layer=layer)

    # The referee's record: what the console fired, including raw effects.
    await session.push_event("inject_fired", {
        "title": delivered["title"],
        "channel": delivered["channel"],
        "effects": request.effects or [],
        "target": request.target,
    }, layer=Layer.REFEREE)

    return {
        "status": "delivered",
        "title": delivered["title"],
        "channel": delivered["channel"],
        "layer": layer.value,
        "lines": delivered["lines"],
    }


# --- Prompt hot-edit ------------------------------------------------------

class PromptUpdateRequest(BaseModel):
    text: str


@router.get("/prompts")
async def list_prompt_families():
    """The hot-editable prompt families and whether each is edited."""
    from llm import prompt_templates
    return {"families": prompt_templates.families_summary()}


@router.get("/prompts/{family}")
async def get_prompt_template(family: str):
    """Current template text for one family (file if edited, else default)."""
    from llm import prompt_templates
    try:
        text = prompt_templates.get_template(family)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "family": family,
        "text": text,
        "placeholders": list(prompt_templates.PLACEHOLDERS[family]),
        "edited": prompt_templates.is_edited(family),
    }


@router.put("/prompts/{family}")
async def put_prompt_template(family: str, request: PromptUpdateRequest):
    """Persist an edited template. Rejects text that cannot format with the
    family's placeholder set (see llm/prompt_templates.validate_template)."""
    from llm import prompt_templates
    try:
        prompt_templates.set_template(family, request.text)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "saved", "family": family,
            "edited": prompt_templates.is_edited(family)}


@router.delete("/prompts/{family}")
async def reset_prompt_template(family: str):
    """Restore one family's canonical default template."""
    from llm import prompt_templates
    try:
        prompt_templates.reset_template(family)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "reset", "family": family}
