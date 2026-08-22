"""Shared fixed inputs for the prompt hot-edit byte-parity gate.

The golden file (tests/data/prompt_parity_golden.json) was captured by
running build_all_prompts() against the PRE-refactor builders (the inline
f-string templates). After the refactor to data/prompts/*.txt templates,
tests/test_prompt_templates.py rebuilds the same prompts and asserts they
are byte-identical - proving the extraction changed nothing.

Inputs are deliberately fixed and self-contained: no scenario files, no
RNG, no LLM. Both capture and test must go through these exact functions.
"""

from typing import Any, Dict, List

from models.world import Metrics, WorldState


def build_world() -> WorldState:
    return WorldState(
        turn=3,
        scene=3,
        difficulty="standard",
        phase="discussion",
        metrics=Metrics(
            escalation_risk=62,
            domestic_stability=48,
            alliance_cohesion=41,
            casualties_mil=4,
            casualties_civ=1,
        ),
        flags={"nato_article4_invoked": True, "cyber_attacks_ongoing": False},
        posture={},
    )


def build_initial_conditions() -> Dict[str, Any]:
    return {
        "characters": {
            "chief_defence_staff": {
                "role": "Chief of the Defence Staff",
                "knowledge_domains": ["military_operations", "force_readiness"],
                "key_concerns": ["escalation control", "force protection"],
                "pushback_triggers": ["unsupported deployments", "rules of engagement gaps"],
            },
            "attorney_general": {
                "role": "Attorney General",
                "knowledge_domains": ["legal_framework"],
                "key_concerns": ["legality of use of force"],
                "pushback_triggers": ["actions without legal basis"],
            },
        },
        "constraints": {
            "political": ["No first use of force without attribution."],
            "legal": ["All action must satisfy Article 51 self-defence."],
        },
        "uk_forces": {
            "royal_navy": [{"id": "CSG-25", "type": "carrier strike group"}],
        },
        "stockpiles": {
            "missiles": {"aster_30": {"count": 120}},
        },
    }


def build_transcript() -> List[str]:
    return [
        "=== TURN 1 ===",
        "Prime Minister: What is the current threat assessment?",
        "Chief of the Defence Staff: Russian naval activity in the North Sea "
        "is at its highest level since the incident began.",
    ]


def build_all_prompts() -> Dict[str, str]:
    """Assemble one representative prompt per hot-editable family."""
    from llm.prompts import (
        build_advisor_context,
        build_decision_interpretation_prompt,
        build_pushback_prompt,
    )

    world = build_world()
    conditions = build_initial_conditions()
    transcript = build_transcript()
    action = "Deploy the carrier strike group to shadow the vessel."

    return {
        "advisor_qa": build_advisor_context(
            world, conditions, "chief_defence_staff",
            "What are our options at sea?", transcript, event_ledger=None,
        ),
        "decision_interpretation": build_decision_interpretation_prompt(
            world, action, conditions, transcript, event_ledger=None,
        ),
        "advisor_pushback": build_pushback_prompt(
            world, action, "The PM intends a naval shadowing operation.",
            conditions, transcript, event_ledger=None,
        ),
    }
