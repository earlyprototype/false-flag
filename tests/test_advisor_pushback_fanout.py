"""Independent advisor pushback regressions for issue #87."""

from random import Random

import pytest

from agents.conversation import generate_advisor_pushback
from engine.initial_conditions import load_initial_conditions
from llm.mock_driver import MockDeterministicDriver
from models.narrative import NarrativeConfig
from models.world import Metrics, WorldState


ADVISOR_IDS = [
    "chief_defence_staff",
    "national_security_advisor",
    "home_secretary",
    "foreign_secretary",
    "attorney_general",
]


def _world(narrative=None):
    return WorldState(
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
        ),
        narrative=narrative,
    )


def _conditions():
    return load_initial_conditions("war_game_2025")


def _unused_single(*args, **kwargs):
    raise AssertionError("pushback should use the supplied batch fan-out")


def test_pushback_fans_out_isolated_prompts_and_uses_roster_attribution():
    conditions = _conditions()
    batches = []

    def batch(prompts, rng, **kwargs):
        batches.append(list(prompts))
        return [f"independent finding {i}" for i in range(len(prompts))]

    result = generate_advisor_pushback(
        _world(),
        "Deploy the carrier group.",
        "A naval deployment.",
        conditions,
        _unused_single,
        Random(7),
        llm_batch_fn=batch,
    )

    assert len(batches) == 1
    assert len(batches[0]) == len(ADVISOR_IDS)
    assert result == [
        (conditions["characters"][char_id]["role"], f"independent finding {i}")
        for i, char_id in enumerate(ADVISOR_IDS)
    ]

    for char_id, prompt in zip(ADVISOR_IDS, batches[0]):
        own = conditions["characters"][char_id]
        assert own["role"] in prompt
        for value in own["key_concerns"] + own["pushback_triggers"]:
            assert value in prompt

        for other_id in ADVISOR_IDS:
            if other_id == char_id:
                continue
            other = conditions["characters"][other_id]
            assert other["role"] not in prompt
            for value in other["key_concerns"] + other["pushback_triggers"]:
                assert value not in prompt


def test_pushback_prompts_are_identical_with_mystery_off_and_on():
    """Standard/immersive pushback never receives hidden Mystery truth."""
    secret = "NEVER_SHOW_THIS_MYSTERY_SECRET"
    mystery = NarrativeConfig(
        narrative_id="SECRET_TEST_NARRATIVE",
        description=secret,
        protagonist="RUS",
        antagonist="GBR",
        patsy="NONE",
        stances=[],
    )

    def capture(world):
        prompts_seen = []

        def batch(prompts, rng, **kwargs):
            prompts_seen.extend(prompts)
            return ["NO PUSHBACK"] * len(prompts)

        generate_advisor_pushback(
            world,
            "Hold the current posture.",
            "No change in posture.",
            _conditions(),
            _unused_single,
            Random(11),
            llm_batch_fn=batch,
        )
        return prompts_seen

    mystery_off = capture(_world())
    mystery_on = capture(_world(mystery))

    assert len(mystery_off) == len(mystery_on) == len(ADVISOR_IDS)
    assert mystery_on == mystery_off
    assert all(secret not in prompt for prompt in mystery_on)
    assert all("SECRET NARRATIVE" not in prompt for prompt in mystery_on)


def test_failed_and_malformed_pushback_slots_are_visible_without_cross_talk():
    conditions = _conditions()

    def batch(prompts, rng, **kwargs):
        assert len(prompts) == len(ADVISOR_IDS)
        return [
            "The carrier is not ready.",
            "NO PUSHBACK",
            "[ERROR: HTTP 429 rate limited]",
            {"unexpected": "shape"},
            "Foreign Secretary: This belongs to another seat.",
        ]

    result = generate_advisor_pushback(
        _world(),
        "Deploy the carrier group.",
        "A naval deployment.",
        conditions,
        _unused_single,
        Random(3),
        llm_batch_fn=batch,
    )

    assert result[0] == ("Chief of the Defence Staff", "The carrier is not ready.")
    assert [role for role, _ in result[1:]] == [
        "Home Secretary",
        "Foreign Secretary",
        "Attorney General",
    ]
    for _role, message in result[1:]:
        assert "unavailable" in message.lower()
        assert "HTTP 429" not in message
        assert "belongs to another seat" not in message


def test_whole_pushback_batch_failure_is_visible_for_every_advisor():
    def batch(_prompts, _rng, **_kwargs):
        raise RuntimeError("provider unavailable")

    result = generate_advisor_pushback(
        _world(),
        "Hold the current posture.",
        "No change in posture.",
        _conditions(),
        _unused_single,
        Random(5),
        llm_batch_fn=batch,
    )

    assert [role for role, _ in result] == [
        _conditions()["characters"][char_id]["role"]
        for char_id in ADVISOR_IDS
    ]
    assert all("unavailable" in message.lower() for _, message in result)


def test_offline_pushback_is_visible_as_unavailable():
    def batch(prompts, rng, **kwargs):
        return ["[Offline mode: No LLM response available]"] * len(prompts)

    result = generate_advisor_pushback(
        _world(),
        "Hold the current posture.",
        "No change in posture.",
        _conditions(),
        _unused_single,
        Random(8),
        llm_batch_fn=batch,
    )

    assert all(
        message == "[ERROR: Advisor response unavailable]"
        for _, message in result
    )


@pytest.mark.parametrize("leaked", [
    "Foreign Secretary: This belongs to another seat.",
    "Foreign Secretary - This belongs to another seat.",
    "Foreign Secretary \u2014 This belongs to another seat.",
    "Foreign Secretary, This belongs to another seat.",
    "Foreign Secretary; This belongs to another seat.",
    "Foreign Secretary says: This belongs to another seat.",
    "Foreign Secretary speaking: This belongs to another seat.",
    "**Foreign Secretary:** This belongs to another seat.",
    "**Foreign Secretary**: This belongs to another seat.",
    "**Foreign Secretary** — This belongs to another seat.",
    "**Foreign Secretary**, This belongs to another seat.",
    "- Foreign Secretary: This belongs to another seat.",
    "> Foreign Secretary: This belongs to another seat.",
    "1. Foreign Secretary: This belongs to another seat.",
    "1. **Foreign Secretary** — This belongs to another seat.",
    "As Foreign Secretary, this belongs to another seat.",
    "Speaking as the Foreign Secretary, this belongs to another seat.",
    "As Prime Minister, this belongs to the player.",
    "Speaking as the Prime Minister, this belongs to the player.",
    "As PM, this belongs to the player.",
    "As Government Leader, this belongs to the player.",
    "Prime Minister: This belongs to the player.",
    "PM says: This belongs to the player.",
    "PM speaks: This belongs to the player.",
    "Prime Minister speaking: This belongs to the player.",
    "Prime Minister replies: This belongs to the player.",
    "**Prime Minister** - This belongs to the player.",
    "Defence Secretary: This belongs to an unseated role.",
    "Military Commander: This belongs to a legacy role.",
    "Intelligence Coordinator: This belongs to a legacy role.",
    "Domestic Security: This belongs to a legacy role.",
    "Diplomatic Lead: This belongs to a legacy role.",
    "Legal Advisor: This belongs to a legacy role.",
    "Government Leader: This belongs to a legacy player role.",
    "Unknown Advisor: This belongs to an unknown role.",
])
def test_role_prefixed_cross_talk_is_visible_as_malformed(leaked):
    def batch(prompts, rng, **kwargs):
        return [leaked] + ["NO PUSHBACK"] * (len(prompts) - 1)

    result = generate_advisor_pushback(
        _world(),
        "Hold the current posture.",
        "No change in posture.",
        _conditions(),
        _unused_single,
        Random(6),
        llm_batch_fn=batch,
    )

    assert result == [
        ("Chief of the Defence Staff", "[ERROR: Advisor response unavailable]")
    ]


def test_non_role_label_remains_valid_pushback_text():
    def batch(prompts, rng, **kwargs):
        return ["Risk: the carrier cannot sail safely."] + [
            "NO PUSHBACK"
        ] * (len(prompts) - 1)

    result = generate_advisor_pushback(
        _world(),
        "Hold the current posture.",
        "No change in posture.",
        _conditions(),
        _unused_single,
        Random(9),
        llm_batch_fn=batch,
    )

    assert result == [
        ("Chief of the Defence Staff", "Risk: the carrier cannot sail safely.")
    ]


@pytest.mark.parametrize("vocative", [
    "Prime Minister, the carrier cannot sail safely.",
    "PM, the carrier cannot sail safely.",
    "Government Leader, the carrier cannot sail safely.",
])
def test_player_role_comma_is_a_valid_vocative(vocative):
    def batch(prompts, rng, **kwargs):
        return [vocative] + ["NO PUSHBACK"] * (len(prompts) - 1)

    result = generate_advisor_pushback(
        _world(),
        "Deploy the carrier group.",
        "A naval deployment.",
        _conditions(),
        _unused_single,
        Random(10),
        llm_batch_fn=batch,
    )

    assert result == [("Chief of the Defence Staff", vocative)]


def test_mock_carrier_objection_survives_player_vocative():
    driver = MockDeterministicDriver()

    result = generate_advisor_pushback(
        _world(),
        "Deploy the carrier group.",
        "A naval deployment.",
        _conditions(),
        driver.generate_text,
        Random(11),
        llm_batch_fn=driver.batch_generate_text,
    )

    assert len(result) == 1
    assert result[0][0] == "Chief of the Defence Staff"
    assert result[0][1].startswith("Prime Minister,")


def test_mock_persona_detection_ignores_shared_transcript_roles():
    driver = MockDeterministicDriver()

    result = generate_advisor_pushback(
        _world(),
        "Deploy the carrier group.",
        "A naval deployment.",
        _conditions(),
        driver.generate_text,
        Random(12),
        transcript=[
            "Prime Minister: You are the Chief of the Defence Staff; "
            "confirm readiness."
        ],
        llm_batch_fn=driver.batch_generate_text,
    )

    assert [role for role, _ in result] == ["Chief of the Defence Staff"]
