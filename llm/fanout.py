"""Answering a group of prompts that do not depend on one another.

A turn issues roughly fifteen LLM calls, and most of them are not waiting on
each other: the five advisors scanning for critical omissions never read each
other's answers, nor do the international actors, nor the advisors reacting
to an adjudicated decision. They ran one after another all the same, because
every call site reached for the router's single-call ``generate_text`` and
the concurrent path beside it - ``batch_generate_text``, a thread pool
implemented in both live drivers - had no callers anywhere in the game.

This module is the join between the two. Call sites keep taking an injected
single-call function, so tests and the mock driver are unaffected; when a
batch function is supplied as well, the group is fanned out instead.
"""

from collections.abc import Mapping, Set
from random import Random
from typing import Any, Callable, List, Optional

from llm.parse_health import record_fallback


def _component(context: Any) -> str:
    """Parse-health component for a group: the LLMContext family value."""
    value = getattr(context, "value", None)
    return value if isinstance(value, str) else "fanout"


def generate_group(
    prompts: List[str],
    llm_generate_fn: Callable,
    rng: Random,
    llm_batch_fn: Optional[Callable] = None,
    context: Any = None,
    max_tokens: Optional[int] = None,
) -> List[str]:
    """Answer every prompt in ``prompts``, concurrently where possible.

    Args:
        prompts: Independent prompts. Order is preserved in the result.
        llm_generate_fn: Single-call function, used when no batch function is
            given and as the shape every existing call site already injects.
        rng: Random number generator. Order is deterministic within either
            execution path; provider drivers do not promise identical random
            consumption between batch and sequential modes.
        llm_batch_fn: Optional concurrent function (the router's
            ``batch_generate_text``). Absent, the group runs sequentially.
        context: Optional LLMContext for per-context model selection.
        max_tokens: Optional output cap applied to every prompt.

    Returns:
        One response per prompt, in order.

        The two paths mark a failure differently, and a caller has to test
        for both. A failed sequential call or whole batch yields an empty
        string in each affected slot, rather than losing the rest of the
        group. On the batch path a live driver may instead catch a
        per-prompt exception inside its thread pool and return
        ``"[ERROR: ...]"`` in that prompt's slot.

        The marker matters because it is truthy and well-formed enough to
        survive: fed to a parser that shrugs at unrecognised text, it can
        end up quoted as an advisor's line. Each fan-out consumer must guard
        both failure shapes.
    """
    if not prompts:
        return []

    kwargs = {}
    if context is not None:
        kwargs["context"] = context
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if llm_batch_fn is not None:
        try:
            raw_results = llm_batch_fn(prompts, rng, **kwargs)
            if isinstance(raw_results, (str, bytes, bytearray, Mapping, Set)):
                raise TypeError("batch result must be a response sequence")
            results = list(raw_results)
        except Exception as e:
            print(f"[WARN] LLM batch failed: {e}")
            record_fallback(
                _component(context),
                f"batch call failed: {type(e).__name__}")
            return [""] * len(prompts)
        # Every caller pairs this with its input using zip, so a short list
        # silently drops the trailing advisors or actors rather than failing.
        # The sequential path below always returns len(prompts); the batch
        # path has to promise the same thing.
        if len(results) != len(prompts):
            print(f"[WARN] batch returned {len(results)} responses for "
                  f"{len(prompts)} prompts")
            for _ in range(max(0, len(prompts) - len(results))):
                record_fallback(_component(context), "batch slot padded empty")
            results = (results + [""] * len(prompts))[:len(prompts)]
        return results

    results = []
    for prompt in prompts:
        try:
            results.append(llm_generate_fn(prompt, rng, **kwargs))
        except Exception as e:
            print(f"[WARN] LLM call failed: {e}")
            record_fallback(_component(context),
                            f"sequential call failed: {type(e).__name__}")
            results.append("")
    return results
