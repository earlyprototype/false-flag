"""Independent advisor pushback regressions for issue #87."""

from random import Random

from agents.conversation import generate_advisor_pushback
from engine.initial_conditions import load_initial_conditions
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
            "   ",
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

