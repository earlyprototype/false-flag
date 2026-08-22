"""Dependency-ordered decision pipeline (ER-023).

Committing a decision used to issue seven dispatch rounds one after another:
interpretation, pushback, the omissions scan, the actor simulation, the
quality assessment, the character reactions and the situation summary. Four
of the six waits were not required by any data dependency, and against a
live provider the serial shape was measured at 8.5 seconds of a 12.2-second
turn. The dependencies permit three rounds, and this module runs them.

Two shapes are offered, because the two kinds of front end need different
commitment points:

1. **The full pipeline** — ``run_decision_pipeline`` — for callers that
   commit a decision in one step (``GameManager.resolve_decision``: the
   headless, browser and HTTP paths). Three rounds:

   - Round 1: decision interpretation ∥ actor simulation (the actor
     simulation reads only the action and the narrative state).
   - Round 2: pushback ∥ critical-omissions scan ∥ quality assessment
     (all three consume the interpretation — the omissions dependency is
     real since ER-002's fix threaded the reading into that prompt).
   - Round 3: character reactions ∥ situation-summary fold (both need the
     applied outcome; the summary text is assigned only after the round
     joins, so the reaction prompts never race the fold's mutation).

2. **The preview round** — ``run_preview_round`` — for the terminal CLIs,
   which keep their interpret → preview → confirm gate (a cancelled
   decision must not burn actor calls). After the interpretation they run
   pushback ∥ omissions as one round, and round 3's reactions ∥ summary
   pair runs inside the adjudication functions themselves
   (engine/narrative_adjudication.py imports ``run_round`` lazily).

A front end that previews and then commits the SAME text hands the
preview's results back to ``run_decision_pipeline`` via its ``preview``
parameter, so the advisory families are paid once per decision instead of
twice (ER-074); an amended commit passes no preview and pays in full.

**Determinism.** Before each round, one child seed per task is pre-drawn
from the master rng in the FIXED order the round lists its tasks; each task
then runs on its own ``Random(child_seed)``. Results are therefore
independent of thread scheduling — the same structure the batch drivers use
(llm/openai_compat_driver.py::batch_generate_text) — and the structure is
identical on every provider, mock included.

**Failure isolation.** A task that raises degrades to that family's
existing fallback (heuristic assessment, empty pushback, templated
reactions, ...) and records ``parse_health.record_fallback("decision_phase",
...)``; it never kills the round.
"""

import contextvars
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from agents.conversation import (
    check_critical_omissions,
    generate_advisor_pushback,
    interpret_player_action,
)
from engine.actor_simulation import (
    calculate_effects_from_responses,
    identify_relevant_actors,
    simulate_actor_responses,
    _heuristic_actor_response,
)
from engine.initial_conditions import load_initial_conditions
from engine.narrative_adjudication import (
    _generate_actor_summary,
    _generate_templated_responses,
    _heuristic_quality_assessment,
    _check_and_trigger_crises,
    _update_character_attitudes,
    apply_quality_scaling,
    assess_action_quality,
    compute_situation_summary,
    determine_base_effects,
    fallback_situation_summary,
    generate_character_responses,
    record_event_disposition,
)
from engine.utils import clamp
from llm.parse_health import record_fallback

# One task per family, three families in the widest round.
MAX_ROUND_WORKERS = 3

# Fixed metric order for the actor/quality merge, so the effects dict (and
# therefore every transcript and save that renders it) never depends on set
# iteration order.
_METRIC_ORDER = ("escalation_risk", "alliance_cohesion", "domestic_stability")


# A round task: (name, run(task_rng) -> result, fallback() -> result).
RoundTask = Tuple[str, Callable[[Random], Any], Callable[[], Any]]


def quiet_generate(fn: Optional[Callable]) -> Optional[Callable]:
    """Wrap a generate function to suppress its own spinner.

    Inside a concurrent round each family's calls would otherwise race
    their sonar sweeps over the same terminal line; the round shows one
    status line instead. Only callables that accept ``show_spinner`` (by
    name or via **kwargs) are wrapped — injected test doubles that declare
    neither pass through untouched.
    """
    if fn is None:
        return None
    import inspect
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return fn
    accepts = ("show_spinner" in sig.parameters
               or any(p.kind is inspect.Parameter.VAR_KEYWORD
                      for p in sig.parameters.values()))
    if not accepts:
        return fn

    def wrapped(payload, rng, **kwargs):
        kwargs.setdefault("show_spinner", False)
        return fn(payload, rng, **kwargs)

    return wrapped


def _round_status(label: str):
    """One status line for the whole round, in place of the inner spinners.

    Mirrors the router's guard: nothing on mock/offline providers, nothing
    when cli/ is not importable (headless, browser), nothing on non-TTY
    stdout (the Spinner's own rule).
    """
    from contextlib import nullcontext

    try:
        from llm.router import _get_provider
        if _get_provider() in ("mock", "offline"):
            return nullcontext()
        from cli.spinner import Spinner
    except ImportError:
        return nullcontext()
    return Spinner(label)


def run_round(tasks: List[RoundTask], rng: Random,
              status: Optional[str] = None) -> List[Any]:
    """Run one round of independent tasks concurrently, deterministically.

    Child seeds are pre-drawn from ``rng`` in task-list order — the
    documented fixed order — so the draw sequence, and with it every
    result, is independent of which thread finishes first. A task that
    raises yields its fallback and records a decision_phase fallback; the
    round always returns one result per task, in task-list order.
    """
    if not tasks:
        return []

    # Pre-drawn in list order: the ONLY draws the round takes from the
    # master generator, whatever the scheduling.
    seeds = [rng.randint(0, 2**31 - 1) for _ in tasks]

    def run_one(index: int) -> Any:
        name, run, fallback = tasks[index]
        try:
            return run(Random(seeds[index]))
        except Exception as e:
            logger.warning("Decision-phase task %s failed (%s); using its fallback",
                           name, type(e).__name__)
            record_fallback("decision_phase", f"{name} {type(e).__name__}")
            return fallback()

    results: List[Any] = [None] * len(tasks)
    with _round_status(status or f"SIGNALS INBOUND ── {len(tasks)} CHANNELS"):
        with ThreadPoolExecutor(max_workers=MAX_ROUND_WORKERS) as executor:
            # copy_context() at submit: raw executor threads start with an
            # EMPTY contextvars context, so anything bound on the calling
            # thread (the API's llm_relay session binding, which attributes
            # call-log records to a session's event stream) would be lost
            # inside the round. Running each task in a copy of the caller's
            # context propagates those bindings; the task itself runs
            # byte-identically.
            future_to_index = {
                executor.submit(contextvars.copy_context().run, run_one, i): i
                for i in range(len(tasks))
            }
            for future in as_completed(future_to_index):
                results[future_to_index[future]] = future.result()
    return results


def format_decision_transcript(
    action: str,
    interpretation: str,
    pushback: List[Tuple[str, str]],
    critical_concerns: List[Tuple[str, str, str]],
) -> List[str]:
    """The decision block's transcript lines, shared by both shapes.

    One formatter for run_turn_decision and the full pipeline, so the
    save-file record of a decision cannot drift between front ends.
    """
    lines = [f"Prime Minister's Decision: {action}", ""]
    # The interpretation is the UK's internal reading of the decision. It
    # rides in ONE entry behind a speaker-style prefix so the diplomatic
    # fail-closed filter (llm/context_builder.get_diplomatic_context, ER-018)
    # excludes it; appended bare, its usually prefix-less first line passed
    # the no-prefix test and reached every foreign leader's context.
    lines.append(f"Interpretation: {interpretation}")
    lines.append("")

    if pushback:
        lines.append("Advisor Concerns:")
        for role, concern in pushback:
            lines.append(f"\n{role}: {concern}")
        lines.append("")
    else:
        lines.append("No advisor concerns raised.")
        lines.append("")

    if critical_concerns:
        lines.append("CRITICAL ADVISORY:")
        for role, concern, recommendation in critical_concerns:
            lines.append(f"\n{role}: {concern}")
            lines.append(f"RECOMMENDATION: {recommendation}")
        lines.append("")

    return lines


def run_preview_round(
    world,
    action: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    rng: Random,
    full_transcript: Optional[List[str]] = None,
    event_ledger=None,
    llm_generate_fn=None,
    llm_batch_fn=None,
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str, str]]]:
    """Pushback ∥ critical omissions, for the interpret → preview → confirm
    front ends (shape 2 in the module docstring).

    Both consume the interpretation and neither reads the other, so after
    the interpretation call they go out together. Child-seed order:
    pushback first, omissions second.

    Returns (pushback, critical_concerns) in the same shapes the serial
    calls returned.
    """
    gen = quiet_generate(llm_generate_fn)
    batch = quiet_generate(llm_batch_fn)

    tasks: List[RoundTask] = [
        ("pushback",
         lambda task_rng: generate_advisor_pushback(
             world, action, interpretation, initial_conditions,
             gen, task_rng, full_transcript, event_ledger=event_ledger),
         list),
        ("critical_omissions",
         lambda task_rng: check_critical_omissions(
             world, action, interpretation, initial_conditions,
             gen, task_rng, full_transcript, llm_batch_fn=batch,
             event_ledger=event_ledger),
         list),
    ]
    pushback, critical_concerns = run_round(
        tasks, rng, status="CABINET REVIEW ── 2 CHANNELS")
    return pushback, critical_concerns


@dataclass
class DecisionResult:
    """Everything a committed decision produced, in one place."""

    interpretation: str = ""
    pushback: List[Tuple[str, str]] = field(default_factory=list)
    critical_concerns: List[Tuple[str, str, str]] = field(default_factory=list)
    actor_responses: List[Any] = field(default_factory=list)
    character_responses: List[Tuple[str, str]] = field(default_factory=list)
    final_effects: Dict[str, int] = field(default_factory=dict)
    reasoning: str = ""
    quality_assessment: Dict[str, Any] = field(default_factory=dict)
    transcript: List[str] = field(default_factory=list)


def run_decision_pipeline(
    world,
    scenario_id: str,
    action: str,
    rng: Random,
    root_path: Optional[Path] = None,
    full_transcript: Optional[List[str]] = None,
    narrative_state=None,
    llm_generate_fn=None,
    llm_batch_fn=None,
    preview: Optional[Dict[str, Any]] = None,
) -> DecisionResult:
    """The full three-round decision pipeline (shape 1 in the module
    docstring), for callers that commit a decision in one step.

    Mutates ``narrative_state`` (hidden metrics, ledger disposition,
    attitudes, crises, situation summary) and the actor relationships on
    ``world.actor_system``, exactly as the serial
    run_turn_decision + adjudicate_with_* pair did. ``world.metrics`` is
    NOT synced here — that remains the caller's job, as before.

    ``preview`` (ER-074): a caller that already previewed EXACTLY this
    action (GameManager.interpret_decision → resolve_decision) passes the
    preview's results as ``{"interpretation": str,
    "pushback": [(role, concern), ...],
    "critical_concerns": [(role, concern, recommendation), ...]}``.
    The pipeline then reuses them instead of re-asking the model — the
    verification run measured the advisory families answering twice per
    decision (70 omissions calls over 7 turns, double the cost) — and runs
    only what depends on post-commit state: the actor simulation, the
    quality assessment, the reactions and the summary fold. Matching the
    preview to the committed text is the CALLER's job; an amended decision
    must arrive with ``preview=None`` and pays the full pipeline.

    Child-seed order per round (fixed, documented):
      round 1: interpretation, actor_simulation
      round 2: pushback, critical_omissions, quality_assessment
      round 3: character_responses, situation_summary
    A round always draws every one of its seeds, even when a task is
    skipped (no actor system) or answered from the preview (ER-074) — the
    reused task stays IN the task list as a no-LLM lambda, so its seed is
    still drawn and the seeds handed to the tasks that do run (actor
    simulation, quality assessment, round 3) never shift. Campaigns with
    and without a preview therefore replay identically for every call
    that executes.
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    if narrative_state is None:
        raise ValueError("run_decision_pipeline requires a narrative_state")

    world.phase = "decision"

    gen = quiet_generate(llm_generate_fn)
    batch = quiet_generate(llm_batch_fn)

    initial_conditions = load_initial_conditions(scenario_id, root_path)
    event_ledger = narrative_state.recent_played_events()

    actor_system = getattr(world, "actor_system", None)
    world_narrative = getattr(world, "narrative", None)

    # --- Round 1: interpretation ∥ actor simulation ------------------------
    # The actor roster and its world context are chosen before the round -
    # both are deterministic and call no model.
    actors: List[Any] = []
    if actor_system:
        relevant_ids = identify_relevant_actors(action, actor_system,
                                                max_actors=3)
        actors = [a for a in (actor_system.get_actor(i) for i in relevant_ids)
                  if a]
        actor_context = narrative_state.to_actor_context()

    # Preview reuse (ER-074): all-or-nothing — a preview without an
    # interpretation (the field every round-2 family consumed) is not a
    # usable preview, so the whole pipeline runs. The reused tasks return
    # the preview's answers without a model call, but keep their slots so
    # the seed draws hold (see the docstring's determinism note).
    use_preview = bool(preview and preview.get("interpretation"))

    if use_preview:
        previewed_interpretation = preview["interpretation"]
        round1: List[RoundTask] = [
            ("interpretation",
             lambda task_rng: previewed_interpretation,
             lambda: action),
        ]
    else:
        round1 = [
            ("interpretation",
             lambda task_rng: interpret_player_action(
                 world, action, initial_conditions, gen, task_rng,
                 full_transcript, event_ledger=event_ledger),
             lambda: action),
        ]
    if actors:
        round1.append(
            ("actor_simulation",
             lambda task_rng: simulate_actor_responses(
                 actors, action, actor_context, gen, task_rng,
                 llm_batch_fn=batch, world_narrative=world_narrative),
             lambda: [_heuristic_actor_response(a, action) for a in actors]))
    else:
        # Keep the round's draw count fixed whether or not the actor file
        # loaded, so the two configurations replay independently.
        round1.append(("actor_simulation",
                       lambda task_rng: [], list))

    interpretation, actor_responses = run_round(
        round1, rng, status="READING THE ORDER ── 2 CHANNELS")

    # --- Round 2: pushback ∥ omissions ∥ quality ---------------------------
    # With a preview, the advisory pair is answered from it (their prompts
    # depend on nothing the commit changed); the quality assessment always
    # runs — it reads post-commit state and its verdict scales the effects.
    if use_preview:
        previewed_pushback = [tuple(p) for p in (preview.get("pushback") or [])]
        previewed_concerns = [
            tuple(c) for c in (preview.get("critical_concerns") or [])]
        round2: List[RoundTask] = [
            ("pushback", lambda task_rng: previewed_pushback, list),
            ("critical_omissions", lambda task_rng: previewed_concerns, list),
        ]
    else:
        round2 = [
            ("pushback",
             lambda task_rng: generate_advisor_pushback(
                 world, action, interpretation, initial_conditions,
                 gen, task_rng, full_transcript, event_ledger=event_ledger),
             list),
            ("critical_omissions",
             lambda task_rng: check_critical_omissions(
                 world, action, interpretation, initial_conditions,
                 gen, task_rng, full_transcript, llm_batch_fn=batch,
                 event_ledger=event_ledger),
             list),
        ]
    round2.append(
        ("quality_assessment",
         lambda task_rng: assess_action_quality(
             action, narrative_state, interpretation, gen, task_rng),
         lambda: _heuristic_quality_assessment(action, narrative_state)))
    pushback, critical_concerns, quality_assessment = run_round(
        round2, rng, status="CABINET REVIEW ── 3 CHANNELS")

    # --- Apply the outcome (no model calls) --------------------------------
    if actor_system:
        # Mirrors adjudicate_with_actor_simulation: relationships move on
        # the actors' answers, then the 60/40 actor/quality blend lands on
        # the hidden metrics.
        for actor, response in zip(actors, actor_responses):
            actor_system.update_actor_relationship(
                actor.country_code, response.trust_change)

        actor_effects = calculate_effects_from_responses(
            actor_responses, actor_system)
        base_effects = determine_base_effects(action, narrative_state)
        quality_effects = apply_quality_scaling(
            base_effects, quality_assessment, narrative_state)

        # Fixed metric order (never set iteration): the merged dict's key
        # order is part of the deterministic record.
        merged = [m for m in _METRIC_ORDER
                  if m in actor_effects or m in quality_effects]
        merged += sorted(k for k in (set(actor_effects) | set(quality_effects))
                         if k not in _METRIC_ORDER)
        final_effects = {
            metric: int(actor_effects.get(metric, 0) * 0.6
                        + quality_effects.get(metric, 0) * 0.4)
            for metric in merged
        }
        reasoning = _generate_actor_summary(actor_responses, quality_assessment)
    else:
        # Mirrors adjudicate_with_narrative: the LLM's suggested effects are
        # the base, scaled by its own multiplier - the suggestion dict is
        # emptied so the merge cannot average the scaling away.
        assessment_for_scaling = dict(quality_assessment)
        assessment_for_scaling["suggested_effects"] = {}
        final_effects = apply_quality_scaling(
            quality_assessment["suggested_effects"], assessment_for_scaling,
            narrative_state)
        reasoning = quality_assessment["reasoning"]

    for metric, delta in final_effects.items():
        if hasattr(narrative_state.hidden_metrics, metric):
            current = getattr(narrative_state.hidden_metrics, metric)
            setattr(narrative_state.hidden_metrics, metric,
                    clamp(current + delta))

    record_event_disposition(narrative_state, action,
                             quality_assessment=quality_assessment,
                             final_effects=final_effects,
                             pushback=pushback)

    # --- Round 3: character reactions ∥ situation-summary fold -------------
    # Both read the applied outcome. The fold's text is assigned only after
    # the round joins (and after the crisis check), so the reaction prompts
    # read a stable narrative_state and the deterministic fallback sees the
    # same post-check crisis list it always did.
    round3: List[RoundTask] = [
        ("character_responses",
         lambda task_rng: generate_character_responses(
             action, quality_assessment, final_effects, narrative_state,
             gen, task_rng, llm_batch_fn=batch),
         lambda: _generate_templated_responses(
             action, quality_assessment, narrative_state)),
        ("situation_summary",
         lambda task_rng: compute_situation_summary(
             narrative_state, action, gen, task_rng,
             quality_assessment=quality_assessment,
             final_effects=final_effects),
         lambda: None),
    ]
    character_responses, summary_text = run_round(
        round3, rng, status="THE ROOM REACTS ── 2 CHANNELS")

    _update_character_attitudes(narrative_state, quality_assessment["quality"])
    _check_and_trigger_crises(narrative_state)
    narrative_state.situation_summary = (
        summary_text if summary_text
        else fallback_situation_summary(narrative_state))

    return DecisionResult(
        interpretation=interpretation,
        pushback=pushback,
        critical_concerns=critical_concerns,
        actor_responses=actor_responses,
        character_responses=character_responses,
        final_effects=final_effects,
        reasoning=reasoning,
        quality_assessment=quality_assessment,
        transcript=format_decision_transcript(
            action, interpretation, pushback, critical_concerns),
    )
