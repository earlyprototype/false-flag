#!/usr/bin/env python3
"""Capture zero-cost runtime prompt evidence for issue #83."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from random import Random
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import engine.narrator as narrator_module
import engine.sim_loop as sim_loop_module
import llm.inject_generator as inject_generator_module
from agents.conversation import (
    check_critical_omissions,
    interpret_player_action,
)
from engine.actor_simulation import (
    calculate_effects_from_responses,
    identify_relevant_actors,
    simulate_actor_responses,
)
from engine.decision_phase import format_decision_transcript
from engine.events import load_inject_for_turn
from engine.flags import update_world_flags
from engine.game_manager import GameManager
from engine.narrative_adjudication import (
    _check_and_trigger_crises,
    _update_character_attitudes,
    apply_quality_scaling,
    assess_action_quality,
    compute_situation_summary,
    determine_base_effects,
    generate_character_responses,
    record_event_disposition,
)
from engine.narrator import generate_narrator_bridge
from engine.utils import clamp
from llm import call_log, parse_health, router
from llm.inject_generator import generate_inject
from llm.mock_driver import MockDeterministicDriver
from llm.model_config import LLMContext

BASE_CONFIG = {
    "scenario_id": "war_game_2025",
    "variant": "standard",
    "difficulty": "standard",
    "play_mode": "immersive",
    "seed": 0,
}
CASES = (("mystery_off", False), ("mystery_on", True))

MAIN_PATH_FAMILIES = {
    "advisor_qa_single": "advisor_qa",
    "advisor_qa_fanout": "advisor_qa",
    "decision_interpretation": "decision_interpretation",
    "critical_omissions": "critical_omissions",
    "actor_simulation": "actor_simulation",
    "quality_assessment": "quality_assessment",
    "character_response": "character_response",
    "situation_summary": "situation_summary",
    "narrator": "narrator",
    "diplomacy_conversation": "diplomacy_conversation",
    "diplomacy_outcome": "diplomacy_outcome",
    "inject_yaml": "inject_generation",
}
PATH_FAMILIES = {**MAIN_PATH_FAMILIES, "advisor_pushback": "advisor_pushback"}
BATCH_PATHS = {
    "advisor_qa_fanout",
    "critical_omissions",
    "actor_simulation",
    "character_response",
}
EXPECTED_MAIN_PATH_COUNTS = {
    "advisor_qa_single": 1,
    "advisor_qa_fanout": 5,
    "decision_interpretation": 1,
    "critical_omissions": 5,
    "actor_simulation": 3,
    "quality_assessment": 1,
    "character_response": 2,
    "situation_summary": 1,
    "narrator": 1,
    "diplomacy_conversation": 1,
    "diplomacy_outcome": 1,
    "inject_yaml": 1,
}
EXPECTED_PUSHBACK_PATH_COUNTS = {"advisor_pushback": 5}
REQUEST_FIELDS = (
    "system_instruction",
    "temperature",
    "max_tokens",
    "model_override",
)

QUESTION = (
    "National Security Adviser, what does the evidence support, and what "
    "must we verify before acting?"
)
ROOM_QUESTION = (
    "What is the single most important risk the Cabinet must control in the "
    "next six hours?"
)
ACTION = (
    "Consult NATO allies, deploy P-8 patrols and Type 23 frigates to track "
    "Russian submarines, strengthen cyber defences, reassure the public, and "
    "require verified intelligence and Attorney General approval before any "
    "use of force."
)
DIPLOMACY_MESSAGE = (
    "We will keep our deployments defensive and evidence-led. Will Ireland "
    "share maritime observations and keep a quiet channel open?"
)
PUSHBACK_ACTION = (
    "Deploy HMS Prince of Wales immediately at reduced readiness and prepare "
    "a nuclear first-use option."
)
PUSHBACK_INTERPRETATION = (
    "The Prime Minister orders the carrier surged before full readiness and "
    "directs officials to prepare a nuclear first-use option immediately."
)
METRICS = ("escalation_risk", "alliance_cohesion", "domestic_stability")

_ROUTER_GENERATE_TEXT = router.generate_text
_ROUTER_BATCH_GENERATE_TEXT = router.batch_generate_text


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _jsonable(value.value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, set):
        converted = [_jsonable(item) for item in value]
        return sorted(converted, key=lambda item: json.dumps(item, sort_keys=True))
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _jsonable(value.dict())
    raise TypeError(f"Cannot serialise {type(value).__name__}")


@contextmanager
def _request_metadata(**values: Any):
    for field in REQUEST_FIELDS:
        call_log.set_field(field, values.get(field))
    try:
        yield
    finally:
        for field in REQUEST_FIELDS:
            call_log.set_field(field, None)


def _audited_generate_text(
    prompt: str,
    rng: Any,
    show_spinner: bool = True,
    context: LLMContext | None = None,
    model_override: str | None = None,
    system_instruction: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    with _request_metadata(
        system_instruction=system_instruction,
        temperature=temperature,
        max_tokens=max_tokens,
        model_override=model_override,
    ):
        return _ROUTER_GENERATE_TEXT(
            prompt,
            rng,
            show_spinner=show_spinner,
            context=context,
            model_override=model_override,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def _audited_batch_generate_text(
    prompts: list[str],
    rng: Any,
    show_spinner: bool = True,
    context: LLMContext | None = None,
    model_override: str | None = None,
    max_tokens: int | None = None,
) -> list[str]:
    with _request_metadata(
        max_tokens=max_tokens,
        model_override=model_override,
    ):
        return _ROUTER_BATCH_GENERATE_TEXT(
            prompts,
            rng,
            show_spinner=show_spinner,
            context=context,
            model_override=model_override,
            max_tokens=max_tokens,
        )


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _assert_mock_only() -> None:
    providers = {"default": router._resolve_call_provider(None)}
    providers.update({
        context.value: router._resolve_call_provider(context)
        for context in LLMContext
    })
    unsafe = {name: provider for name, provider in providers.items()
              if provider != "mock"}
    if unsafe:
        routes = ", ".join(f"{name}={provider}" for name, provider in unsafe.items())
        raise SystemExit(f"Refusing to run: effective provider must be mock ({routes})")
    for context in LLMContext:
        model = router._resolve_call_model("mock", context, None)
        if not isinstance(
            router._driver_for_call("mock", model), MockDeterministicDriver
        ):
            raise SystemExit(
                f"Refusing to run: {context.value} does not route to "
                "MockDeterministicDriver"
            )


def _new_game(mystery_mode: bool) -> GameManager:
    game = GameManager(**BASE_CONFIG, mystery_mode=mystery_mode)
    game.get_turn_briefing()
    return game


def _narrative_id(game: GameManager) -> str | None:
    narrative = game.world.narrative
    return getattr(narrative, "narrative_id", None) if narrative else None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _capture(
    records: list[dict[str, Any]],
    outputs: dict[str, Any],
    path: str,
    turn: int,
    operation: Callable[[], Any],
    *,
    per_record: bool = False,
) -> Any:
    call_log.set_field("path", path)
    call_log.set_field("turn", turn)
    start = len(records)
    result = operation()
    captured = records[start:]
    _require(bool(captured), f"{path} made no logged LLM call")
    _require(
        all(record["family"] == PATH_FAMILIES[path] for record in captured),
        f"{path} logged the wrong family",
    )

    converted = _jsonable(result)
    outputs[path] = converted
    item_outputs = converted if (
        per_record and isinstance(converted, list) and len(converted) == len(captured)
    ) else None
    for index, record in enumerate(captured):
        record["parsed_output"] = (
            item_outputs[index] if item_outputs is not None else converted
        )
    return result


def _final_effects(
    game: GameManager,
    actor_responses: list[Any],
    quality: dict[str, Any],
) -> dict[str, int]:
    actor_system = game.world.actor_system
    for response in actor_responses:
        actor_system.update_actor_relationship(response.actor_id, response.trust_change)
    actor_effects = calculate_effects_from_responses(actor_responses, actor_system)
    quality_effects = apply_quality_scaling(
        determine_base_effects(ACTION, game.narrative_state),
        quality,
        game.narrative_state,
    )
    keys = list(METRICS)
    keys.extend(sorted((set(actor_effects) | set(quality_effects)) - set(keys)))
    return {
        metric: int(actor_effects.get(metric, 0) * 0.6
                    + quality_effects.get(metric, 0) * 0.4)
        for metric in keys
        if metric in actor_effects or metric in quality_effects
    }


def _apply_outcome(game: GameManager, quality: dict[str, Any], effects: dict[str, int]) -> None:
    for metric, delta in effects.items():
        if hasattr(game.world.metrics, metric):
            value = clamp(getattr(game.world.metrics, metric) + delta)
            setattr(game.world.metrics, metric, value)
    game.narrative_state.update_hidden_metrics(game.world.metrics.model_dump())
    record_event_disposition(
        game.narrative_state,
        ACTION,
        quality_assessment=quality,
        final_effects=effects,
        pushback=[],
    )


def _run_main_case(
    case: str,
    mystery_mode: bool,
    game: GameManager,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_narrative = _narrative_id(game)
    _require(bool(selected_narrative) is mystery_mode, "Mystery setup is invalid")
    call_log.set_field("case", case)
    call_log.set_field("mystery_mode", mystery_mode)
    call_log.set_field("narrative_id", selected_narrative or "none")
    outputs: dict[str, Any] = {}
    ledger = game.narrative_state.recent_played_events()

    _capture(
        records, outputs, "advisor_qa_single", game.world.turn,
        lambda: game.process_question(QUESTION),
    )
    _capture(
        records, outputs, "advisor_qa_fanout", game.world.turn,
        lambda: game.process_question_all(ROOM_QUESTION)[1:],
        per_record=True,
    )
    game.world.phase = "decision"

    # Match run_decision_pipeline's three fixed rounds. Pushback keeps its
    # seed slot but is not invoked until the separate, final audit phase.
    decision_rngs = [
        Random(game.rng.randint(0, 2**31 - 1))
        for _ in range(7)
    ]
    (
        interpretation_rng,
        actor_rng,
        _pushback_rng,
        omissions_rng,
        quality_rng,
        character_rng,
        summary_rng,
    ) = decision_rngs
    interpretation = _capture(
        records, outputs, "decision_interpretation", game.world.turn,
        lambda: interpret_player_action(
            game.world, ACTION, game.initial_conditions,
            router.generate_text, interpretation_rng, game.transcript,
            event_ledger=ledger,
        ),
    )
    critical_concerns = _capture(
        records, outputs, "critical_omissions", game.world.turn,
        lambda: check_critical_omissions(
            game.world, ACTION, interpretation, game.initial_conditions,
            router.generate_text, omissions_rng, game.transcript,
            llm_batch_fn=router.batch_generate_text,
            event_ledger=ledger,
        ),
    )

    actor_system = game.world.actor_system
    _require(actor_system is not None, "scenario actor data did not load")
    actor_ids = identify_relevant_actors(ACTION, actor_system, max_actors=3)
    actors = [actor_system.get_actor(actor_id) for actor_id in actor_ids]
    actors = [actor for actor in actors if actor is not None]
    _require(bool(actors), "no relevant actors selected")
    actor_responses = _capture(
        records, outputs, "actor_simulation", game.world.turn,
        lambda: simulate_actor_responses(
            actors, ACTION, game.narrative_state.to_actor_context(),
            router.generate_text, actor_rng,
            llm_batch_fn=router.batch_generate_text,
            world_narrative=game.world.narrative,
        ),
        per_record=True,
    )
    quality = _capture(
        records, outputs, "quality_assessment", game.world.turn,
        lambda: assess_action_quality(
            ACTION, game.narrative_state, interpretation,
            router.generate_text, quality_rng,
        ),
    )
    effects = _final_effects(game, actor_responses, quality)
    _apply_outcome(game, quality, effects)

    _capture(
        records, outputs, "character_response", game.world.turn,
        lambda: generate_character_responses(
            ACTION, quality, effects, game.narrative_state,
            router.generate_text, character_rng,
            llm_batch_fn=router.batch_generate_text,
        ),
        per_record=True,
    )
    summary = _capture(
        records, outputs, "situation_summary", game.world.turn,
        lambda: compute_situation_summary(
            game.narrative_state, ACTION, router.generate_text, summary_rng,
            quality_assessment=quality, final_effects=effects,
        ),
    )
    _update_character_attitudes(game.narrative_state, quality["quality"])
    _check_and_trigger_crises(game.narrative_state)
    if summary:
        game.narrative_state.situation_summary = summary

    game.transcript.extend(format_decision_transcript(
        ACTION, interpretation, [], critical_concerns
    ))
    game.world.phase = "adjudication"
    update_world_flags(game.world)
    game.narrative_state.turn = game.world.turn
    game.world.turn += 1
    game.world.phase = "briefing"
    game.world.scene = game.world.turn
    game.world.discussion_transcript = []
    next_inject = load_inject_for_turn(
        BASE_CONFIG["scenario_id"], game.world.turn, game.root_path
    ) or {}
    _capture(
        records, outputs, "narrator", game.world.turn,
        lambda: generate_narrator_bridge(
            game.world, game.transcript,
            next_inject.get("title", "Next situation update"), game.rng,
        ),
    )

    opening = game.start_diplomacy("IRL")
    _require(bool(opening.get("active")), "Ireland diplomatic channel did not open")
    _capture(
        records, outputs, "diplomacy_conversation", game.world.turn,
        lambda: game.process_diplomacy(DIPLOMACY_MESSAGE),
    )
    _capture(
        records, outputs, "diplomacy_outcome", game.world.turn,
        lambda: game.process_diplomacy("Thank you, goodbye."),
    )

    game.world.turn = 6
    game.world.scene = 6
    _, turn_six_lines = sim_loop_module.run_turn_briefing(
        game.world,
        game.scenario_id,
        False,
        game.rng,
        game.root_path,
        full_transcript=[],
        suppress_display=True,
        narrative_state=game.narrative_state,
    )
    game.transcript.extend(turn_six_lines)
    game.narrative_state.update_hidden_metrics({
        "escalation_risk": game.world.metrics.escalation_risk,
        "domestic_stability": game.world.metrics.domestic_stability,
        "alliance_cohesion": game.world.metrics.alliance_cohesion,
        "casualties_mil": game.world.metrics.casualties_mil,
        "casualties_civ": game.world.metrics.casualties_civ,
    })
    game.narrative_state.turn = 6
    game.world.turn = 7
    game.world.scene = 7
    game.world.phase = "briefing"
    _capture(
        records, outputs, "inject_yaml", game.world.turn,
        lambda: generate_inject(
            game.world, game.world.turn, game.initial_conditions, game.rng,
            game.root_path, game.transcript,
            event_ledger=game.narrative_state.recent_played_events(),
            story_summary=game.narrative_state.situation_summary,
        ),
    )

    return {
        "case": case,
        "config": {**BASE_CONFIG, "mystery_mode": mystery_mode},
        "selected_narrative_id": selected_narrative,
        "actor_ids": actor_ids,
        "final_effects": effects,
        "outputs": outputs,
    }


def _run_pushback_case(
    case: str,
    mystery_mode: bool,
    game: GameManager,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    from agents.conversation import generate_advisor_pushback

    selected_narrative = _narrative_id(game)
    _require(bool(selected_narrative) is mystery_mode, "Mystery setup is invalid")
    call_log.set_field("case", case)
    call_log.set_field("mystery_mode", mystery_mode)
    call_log.set_field("narrative_id", selected_narrative or "none")
    outputs: dict[str, Any] = {}
    _capture(
        records, outputs, "advisor_pushback", game.world.turn,
        lambda: generate_advisor_pushback(
            game.world, PUSHBACK_ACTION, PUSHBACK_INTERPRETATION,
            game.initial_conditions, router.generate_text, game.rng,
            game.transcript,
            event_ledger=game.narrative_state.recent_played_events(),
        ),
    )
    return {
        "case": case,
        "config": {**BASE_CONFIG, "mystery_mode": mystery_mode},
        "selected_narrative_id": selected_narrative,
        "outputs": outputs,
    }


def _assert_main_complete(records: list[dict[str, Any]], cases: list[dict[str, Any]]) -> None:
    expected_families = {context.value for context in LLMContext
                         if context is not LLMContext.ADVISOR_PUSHBACK}
    expected_cases = {name for name, _ in CASES}
    _require(set(MAIN_PATH_FAMILIES.values()) == expected_families,
             "main family inventory is stale")
    _require({case["case"] for case in cases} == expected_cases,
             "main case metadata is incomplete")
    _require({record["case"] for record in records} == expected_cases,
             "main call records are missing a case")
    _require({record["family"] for record in records} == expected_families,
             "main family coverage is incomplete")
    _require(all(record["provider"] == "mock" for record in records),
             "main captured a non-mock provider")
    _require(all(record["fallback"] is False for record in records),
             "main captured a fallback call")
    _require(all(record["family"] != "advisor_pushback" for record in records),
             "main invoked advisor pushback")
    for case, _ in CASES:
        case_records = [record for record in records if record["case"] == case]
        path_counts = Counter(record["path"] for record in case_records)
        _require(path_counts == Counter(EXPECTED_MAIN_PATH_COUNTS),
                 f"{case} path counts differ: {dict(path_counts)}")
        for path in BATCH_PATHS:
            batch = [record for record in case_records if record["path"] == path]
            _require(bool(batch) and all(
                record["batch_size"] == len(batch) for record in batch
            ), f"{case}/{path} batch size metadata is invalid")
            _require(
                [record["batch_index"] for record in batch] == list(range(len(batch))),
                f"{case}/{path} batch index metadata is invalid",
            )


def _assert_pushback_complete(records: list[dict[str, Any]], cases: list[dict[str, Any]]) -> None:
    expected_cases = {name for name, _ in CASES}
    _require({case["case"] for case in cases} == expected_cases,
             "pushback case metadata is incomplete")
    _require({record["case"] for record in records} == expected_cases,
             "pushback call records are missing a case")
    _require(bool(records) and all(
        record["family"] == "advisor_pushback" for record in records
    ), "pushback captured another family")
    _require(all(record["path"] == "advisor_pushback" for record in records),
             "pushback captured another path")
    _require(all(record["provider"] == "mock" for record in records),
             "pushback captured a non-mock provider")
    _require(all(record["fallback"] is False for record in records),
             "pushback captured a fallback call")
    for case, _ in CASES:
        case_records = [record for record in records if record["case"] == case]
        path_counts = Counter(record["path"] for record in case_records)
        _require(path_counts == Counter(EXPECTED_PUSHBACK_PATH_COUNTS),
                 f"{case} pushback path counts differ: {dict(path_counts)}")


def _run_phase(phase: str) -> dict[str, Any]:
    _assert_mock_only()
    git_head = _git_head()
    old_file_sink = os.environ.pop("WARGAME_CALL_LOG", None)
    try:
        prepared = [
            (case, mystery_mode, _new_game(mystery_mode))
            for case, mystery_mode in CASES
        ]
        records: list[dict[str, Any]] = []
        def listener(record: dict[str, Any]) -> None:
            for field in REQUEST_FIELDS:
                record.setdefault(field, None)
            records.append(record)

        call_log.reset()
        parse_health.reset()
        call_log.add_listener(listener)
        try:
            with (
                patch.object(router, "generate_text", _audited_generate_text),
                patch.object(router, "batch_generate_text", _audited_batch_generate_text),
                patch.object(sim_loop_module, "generate_text", _audited_generate_text),
                patch.object(
                    sim_loop_module,
                    "batch_generate_text",
                    _audited_batch_generate_text,
                ),
                patch.object(narrator_module, "generate_text", _audited_generate_text),
                patch.object(
                    inject_generator_module,
                    "generate_text",
                    _audited_generate_text,
                ),
            ):
                if phase == "main":
                    cases = [
                        _run_main_case(case, mystery, game, records)
                        for case, mystery, game in prepared
                    ]
                    _assert_main_complete(records, cases)
                    required_paths = list(MAIN_PATH_FAMILIES)
                    required_families = sorted(set(MAIN_PATH_FAMILIES.values()))
                else:
                    cases = [
                        _run_pushback_case(case, mystery, game, records)
                        for case, mystery, game in prepared
                    ]
                    _assert_pushback_complete(records, cases)
                    required_paths = ["advisor_pushback"]
                    required_families = ["advisor_pushback"]
            health = parse_health.snapshot()
            _require(parse_health.total() == 0,
                     f"parser health is not clean: {health}")
        finally:
            call_log.remove_listener(listener)
            for field in (
                "case", "mystery_mode", "narrative_id", "path", "turn"
            ):
                call_log.set_field(field, None)
    finally:
        if old_file_sink is not None:
            os.environ["WARGAME_CALL_LOG"] = old_file_sink

    return {
        "schema_version": 1,
        "phase": phase,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head,
        "config": {**BASE_CONFIG, "mystery_mode_cases": [False, True]},
        "required_paths": required_paths,
        "required_families": required_families,
        "parse_health": health,
        "cases": cases,
        "records": records,
    }


def _write(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"{payload['phase']}: wrote {len(payload['records'])} mock call records "
        f"across {len(payload['cases'])} cases to {output}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="phase", required=True)
    for phase in ("main", "pushback"):
        command = subparsers.add_parser(phase)
        command.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    _write(_run_phase(args.phase), args.output)


if __name__ == "__main__":
    main()
