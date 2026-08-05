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

from random import Random
from typing import Any, Callable, List, Optional


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
        rng: Random number generator. Both paths draw from it once per prompt,
            so a seeded campaign generates the same sequence either way.
        llm_batch_fn: Optional concurrent function (the router's
            ``batch_generate_text``). Absent, the group runs sequentially.
        context: Optional LLMContext for per-context model selection.
        max_tokens: Optional output cap applied to every prompt.

    Returns:
        One response per prompt, in order.

        The two paths mark a failure differently, and a caller has to test
        for both. On the sequential path a failed call yields an empty
        string, rather than losing the rest of the group. On the batch path
        the live driver catches each prompt's exception inside its thread
        pool and returns ``"[ERROR: ...]"`` in that prompt's slot - so it
        never raises, and the router's retry-then-mock fallback never sees
        it. That fallback covers only a batch call that fails as a whole.

        The marker matters because it is truthy and well-formed enough to
        survive: fed to a parser that shrugs at unrecognised text, it can
        end up quoted as an advisor's line. See the guard in
        ``engine/narrative_adjudication.py``.
    """
    if not prompts:
        return []

    kwargs = {}
    if context is not None:
        kwargs["context"] = context
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if llm_batch_fn is not None:
        results = list(llm_batch_fn(prompts, rng, **kwargs))
        # Every caller pairs this with its input using zip, so a short list
        # silently drops the trailing advisors or actors rather than failing.
        # The sequential path below always returns len(prompts); the batch
        # path has to promise the same thing.
        if len(results) != len(prompts):
            print(f"[WARN] batch returned {len(results)} responses for "
                  f"{len(prompts)} prompts")
            results = (results + [""] * len(prompts))[:len(prompts)]
        return results

    results = []
    for prompt in prompts:
        try:
            results.append(llm_generate_fn(prompt, rng, **kwargs))
        except Exception as e:
            print(f"[WARN] LLM call failed: {e}")
            results.append("")
    return results
