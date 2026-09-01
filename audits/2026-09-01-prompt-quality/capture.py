#!/usr/bin/env python3
"""Capture zero-cost runtime prompt evidence for issue #83."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.conversation import (
    check_critical_omissions,
    handle_player_question,
    handle_player_question_all,
    interpret_player_action,
)
from engine.actor_simulation import (
    calculate_effects_from_responses,
    identify_relevant_actors,
    simulate_actor_responses,
)
from engine.events import load_inject_for_turn
from engine.game_manager import GameManager
from engine.narrative_adjudication import (
    apply_quality_scaling,
    assess_action_quality,
    compute_situation_summary,
    determine_base_effects,
    generate_character_responses,
    record_event_disposition,
)
from engine.narrator import generate_narrator_bridge
from engine.utils import clamp
from llm import call_log, router
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
CHARACTER_SELECTION_EFFECTS = {
    "escalation_risk": 7,
    "alliance_cohesion": -7,
    "domestic_stability": -7,
}


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _jsonable(value.value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _jsonable(value.dict())
    return str(value)


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


def _new_game(mystery_mode: bool) -> tuple[GameManager, dict[str, Any]]:
    game = GameManager(**BASE_CONFIG, mystery_mode=mystery_mode)
    return game, game.get_turn_briefing()


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
        record["context"] = record["family"]
        record["raw_reply"] = record["reply"]
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
    briefing: dict[str, Any],
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
        lambda: handle_player_question(
            game.world, QUESTION, game.initial_conditions,
            router.generate_text, game.rng, game.transcript,
            event_ledger=ledger,
        ),
        per_record=True,
    )
    _capture(
        records, outputs, "advisor_qa_fanout", game.world.turn,
        lambda: handle_player_question_all(
            game.world, ROOM_QUESTION, game.initial_conditions,
            router.generate_text, game.rng, game.transcript,
            llm_batch_fn=router.batch_generate_text,
            event_ledger=ledger,
        ),
        per_record=True,
    )
    interpretation = _capture(
        records, outputs, "decision_interpretation", game.world.turn,
        lambda: interpret_player_action(
            game.world, ACTION, game.initial_conditions,
            router.generate_text, game.rng, game.transcript,
            event_ledger=ledger,
        ),
    )
    _capture(
        records, outputs, "critical_omissions", game.world.turn,
        lambda: check_critical_omissions(
            game.world, ACTION, interpretation, game.initial_conditions,
            router.generate_text, game.rng, game.transcript,
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
            router.generate_text, game.rng,
            llm_batch_fn=router.batch_generate_text,
            world_narrative=game.world.narrative,
        ),
        per_record=True,
    )
    quality = _capture(
        records, outputs, "quality_assessment", game.world.turn,
        lambda: assess_action_quality(
            ACTION, game.narrative_state, interpretation,
            router.generate_text, game.rng,
        ),
    )
    effects = _final_effects(game, actor_responses, quality)
    _apply_outcome(game, quality, effects)

    _capture(
        records, outputs, "character_response", game.world.turn,
        lambda: generate_character_responses(
            ACTION, quality, CHARACTER_SELECTION_EFFECTS, game.narrative_state,
            router.generate_text, game.rng,
            llm_batch_fn=router.batch_generate_text,
        ),
        per_record=True,
    )
    summary = _capture(
        records, outputs, "situation_summary", game.world.turn,
        lambda: compute_situation_summary(
            game.narrative_state, ACTION, router.generate_text, game.rng,
            quality_assessment=quality, final_effects=effects,
        ),
    )
    if summary:
        game.narrative_state.situation_summary = summary

    game.world.turn = 2
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

    game.world.turn = 7
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
        "briefing_title": briefing.get("title"),
        "actor_ids": actor_ids,
        "final_effects": effects,
        "character_selection_effects": CHARACTER_SELECTION_EFFECTS,
        "outputs": outputs,
    }


def _run_pushback_case(
    case: str,
    mystery_mode: bool,
    game: GameManager,
    briefing: dict[str, Any],
    records: list[dict[str, Any]],
    git_head: str,
) -> dict[str, Any]:
    from agents.conversation import generate_advisor_pushback

    selected_narrative = _narrative_id(game)
    _require(bool(selected_narrative) is mystery_mode, "Mystery setup is invalid")
    call_log.set_field("case", case)
    call_log.set_field("mystery_mode", mystery_mode)
    call_log.set_field("narrative_id", selected_narrative or "none")
    call_log.set_field("git_head", git_head)
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
        "briefing_title": briefing.get("title"),
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
        _require({record["path"] for record in case_records} == set(MAIN_PATH_FAMILIES),
                 f"{case} path coverage is incomplete")
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


def _run_phase(phase: str) -> dict[str, Any]:
    _assert_mock_only()
    git_head = _git_head()
    old_file_sink = os.environ.pop("WARGAME_CALL_LOG", None)
    try:
        prepared = [
            (case, mystery_mode, *_new_game(mystery_mode))
            for case, mystery_mode in CASES
        ]
        records: list[dict[str, Any]] = []
        listener = records.append
        call_log.reset()
        call_log.add_listener(listener)
        try:
            if phase == "main":
                cases = [
                    _run_main_case(case, mystery, game, briefing, records)
                    for case, mystery, game, briefing in prepared
                ]
                _assert_main_complete(records, cases)
                required_paths = list(MAIN_PATH_FAMILIES)
                required_families = sorted(set(MAIN_PATH_FAMILIES.values()))
            else:
                cases = [
                    _run_pushback_case(
                        case, mystery, game, briefing, records, git_head
                    )
                    for case, mystery, game, briefing in prepared
                ]
                _assert_pushback_complete(records, cases)
                required_paths = ["advisor_pushback"]
                required_families = ["advisor_pushback"]
        finally:
            call_log.remove_listener(listener)
            for field in (
                "case", "mystery_mode", "narrative_id", "git_head", "path", "turn"
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
