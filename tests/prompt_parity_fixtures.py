"""Shared fixed inputs for the prompt byte-parity and contradiction gates.

The golden file (tests/data/prompt_parity_golden.json) holds the intended
text of the three hot-editable families. It was first captured against the
PRE-refactor builders (the inline f-string templates) to prove the move to
data/prompts/*.txt changed nothing; it was re-captured once, for issue #91,
when two lines were deliberately rewritten (the pushback prompt's worked
example and the advisor-voice rule about the metric figures). Any other
change to those bytes is drift, and tests/test_prompt_templates.py fails on
it.

build_all_prompts also assembles the builders the golden does not pin, so
tests/test_presentation_rules.py can check every prompt against the rules
that prompt itself issues.

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
    """Assemble one representative prompt per advisor-facing builder.

    The three hot-editable families come first (those are the ones the
    golden pins byte-for-byte). The rest - whole-room fanout, the
    critical-omissions scan, inject generation and the narrator bridge -
    are here so the self-contradiction checks in
    tests/test_presentation_rules.py can read every assembled prompt this
    module can build from one place. No LLM is called: the
    inject builder is given a short transcript, so it takes the fixed
    "campaign has just begun" summary rather than generate_summary.
    """
    from llm.prompts import (
        build_advisor_context,
        build_critical_omissions_prompt,
        build_decision_interpretation_prompt,
        build_inject_generation_prompt,
        build_narrator_intro_prompt,
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
        "advisor_qa_fanout": build_advisor_context(
            world, conditions, "chief_defence_staff",
            "What are our options at sea?", transcript, event_ledger=None,
            fanout=True,
        ),
        "critical_omissions": build_critical_omissions_prompt(
            world, conditions, "chief_defence_staff", action,
            ["A Russian submarine was tracked off the Shetland cable route."],
            transcript, interpretation="A naval shadowing operation.",
            event_ledger=None,
        ),
        "inject_generation": build_inject_generation_prompt(
            world, 4, conditions, scenario_library=None,
            transcript=transcript, event_ledger=None,
        ),
        "narrator_intro": build_narrator_intro_prompt(
            world, transcript, "THE CABLE GOES DARK",
        ),
    }


#: The families the golden pins byte-for-byte (the hot-editable three).
GOLDEN_FAMILIES = ("advisor_qa", "decision_interpretation", "advisor_pushback")
