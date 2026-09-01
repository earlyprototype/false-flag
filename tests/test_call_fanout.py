"""Independent LLM calls are asked together, not one after another (issue #32).

A turn issues ~15 LLM calls and most of them are not waiting on each other:
the five advisors scanning for critical omissions never read one another's
answers, nor do the international actors, nor the advisors reacting to an
adjudicated decision. They ran sequentially all the same - ``batch_generate_text``
and its thread pool existed in both live drivers and no game code anywhere
called it.

Played end to end against a recording endpoint at 2s per call, a ten-turn
campaign went from 297.7s to 191.2s of wall clock, with peak concurrency
rising from 1 to 5.

These tests pin the wiring rather than the timing: that each group reaches
the batch path when one is supplied, that it still works when one is not
(the mock driver and every injected test double take the single-call shape),
and that the rate limiter is not bypassed by going wide.
"""

import sys
from pathlib import Path
from random import Random

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import llm.router as router
from agents.conversation import check_critical_omissions
from engine.actor_simulation import simulate_actor_responses
from llm.fanout import generate_group
from models.world import Metrics, WorldState


CONCERN = "CONCERN: No allied consultation.\nRECOMMENDATION: Call the NAC."


def _world():
    return WorldState(
        turn=4, scene=4, phase="decision",
        metrics=Metrics(escalation_risk=70, domestic_stability=40,
                        alliance_cohesion=50),
        flags={}, posture={}, narrative=None,
    )


def _conditions():
    return {
        "characters": {
            "foreign_secretary": {"role": "Foreign Secretary"},
            "chief_defence_staff": {"role": "Chief of the Defence Staff"},
            "attorney_general": {"role": "Attorney General"},
            "home_secretary": {"role": "Home Secretary"},
            "national_security_advisor": {"role": "National Security Advisor"},
        }
    }


# --- the group helper -------------------------------------------------------

def test_a_group_goes_to_the_batch_function_in_one_call():
    seen = {}

    def batch(prompts, rng, **kwargs):
        seen["n_calls"] = seen.get("n_calls", 0) + 1
        seen["n_prompts"] = len(prompts)
        return ["ok"] * len(prompts)

    result = generate_group(["a", "b", "c"], None, Random(1), batch)
    assert result == ["ok", "ok", "ok"]
    assert seen == {"n_calls": 1, "n_prompts": 3}


def test_without_a_batch_function_the_group_still_runs_sequentially():
    """Every existing caller injects a single-call function; none may break."""
    calls = []

    def single(prompt, rng, **kwargs):
        calls.append(prompt)
        return f"answer to {prompt}"

    assert generate_group(["a", "b"], single, Random(1)) == [
        "answer to a", "answer to b"]
    assert calls == ["a", "b"]


def test_one_failed_call_does_not_cost_the_rest_of_the_group():
    def single(prompt, rng, **kwargs):
        if prompt == "b":
            raise RuntimeError("refused")
        return "fine"

    assert generate_group(["a", "b", "c"], single, Random(1)) == [
        "fine", "", "fine"]


def test_malformed_batch_container_fails_every_slot_visibly_to_callers():
    for malformed in (
        "NO PUSHBACK",
        b"NO PUSHBACK",
        {"reply": "ok"},
        {"first", "second"},
        frozenset({"first", "second"}),
    ):
        def batch(prompts, rng, **kwargs):
            return malformed

        assert generate_group(
            ["a", "b"], None, Random(1), batch
        ) == ["", ""]


def test_an_empty_group_asks_nothing():
    def explode(*args, **kwargs):
        raise AssertionError("should not have been called")

    assert generate_group([], explode, Random(1), explode) == []


# --- critical omissions -----------------------------------------------------

def test_the_five_omission_checks_are_asked_together():
    batches = []

    def batch(prompts, rng, **kwargs):
        batches.append(len(prompts))
        return [CONCERN] * len(prompts)

    concerns = check_critical_omissions(
        _world(), "Deploy the destroyer.", "INTERPRETATION: deploy",
        _conditions(), None, Random(1), ["Submarine detected"],
        llm_batch_fn=batch)

    assert batches == [5], "the advisors are still being asked one at a time"
    assert len(concerns) == 5


def test_omission_checks_still_work_with_only_a_single_call_function():
    calls = []

    def single(prompt, rng, **kwargs):
        calls.append(prompt)
        return "NO_CONCERN"

    concerns = check_critical_omissions(
        _world(), "Deploy.", "interp", _conditions(), single, Random(1), [])
    assert len(calls) == 5
    assert concerns == []


def test_an_empty_answer_is_not_read_as_a_concern():
    """A refused call returns "" from the group; it must not become an advisory."""
    def batch(prompts, rng, **kwargs):
        return [""] * len(prompts)

    assert check_critical_omissions(
        _world(), "Deploy.", "interp", _conditions(), None, Random(1), [],
        llm_batch_fn=batch) == []


# --- actor simulation -------------------------------------------------------

class _Actor:
    def __init__(self, code):
        self.country_code = code
        self.full_name = f"Republic of {code}"
        self.official_position = "neutral"
        self.relationship_uk = 50
        self.true_motivations = ["survival"]
        self.hidden_agendas = []
        self.threat_perception = 40
        self.domestic_pressure = 30
        self.dependencies = {}
        self.redlines = []
        self.military_capability = 50
        self.economic_leverage = 50
        self.diplomatic_influence = 50
        self.intelligence_sharing = "partial"


ACTOR_REPLY = """PUBLIC_RESPONSE: We are considering our position.
PRIVATE_ASSESSMENT: London is isolated.
TRUST_CHANGE: -3
WILL_SUPPORT: no
CONDITIONS:
INTEL_SHARED: none"""


def test_capitals_are_asked_at_the_same_time():
    batches = []

    def batch(prompts, rng, **kwargs):
        batches.append(len(prompts))
        return [ACTOR_REPLY] * len(prompts)

    responses = simulate_actor_responses(
        [_Actor("FR"), _Actor("DE"), _Actor("PL")], "Deploy.", "context",
        None, Random(1), llm_batch_fn=batch)

    assert batches == [3]
    assert [r.actor_id for r in responses] == ["FR", "DE", "PL"]


def test_a_driver_error_string_falls_back_to_the_heuristic_response():
    """batch_generate_text reports per-prompt failures as "[ERROR: ...]" text.

    Handing that to the response parser would produce a diplomatic reply
    built out of an error message.
    """
    def batch(prompts, rng, **kwargs):
        return ["[ERROR: HTTP 429]"] * len(prompts)

    responses = simulate_actor_responses(
        [_Actor("FR")], "Deploy.", "context", None, Random(1), llm_batch_fn=batch)
    assert len(responses) == 1
    assert "ERROR" not in responses[0].public_response


def test_no_actors_means_no_call():
    def explode(*args, **kwargs):
        raise AssertionError("should not have been called")

    assert simulate_actor_responses([], "Deploy.", "ctx", explode,
                                    Random(1), llm_batch_fn=explode) == []


# --- the router's batch path ------------------------------------------------

class _CountingDriver:
    """Stands in for a live driver: records what the router hands it."""

    def __init__(self):
        self.batches = []

    def generate_text(self, prompt, rng, **kwargs):
        return "single"

    def batch_generate_text(self, prompts, rng, max_tokens=None):
        self.batches.append((len(prompts), max_tokens))
        return ["batched"] * len(prompts)


class _NoMaxTokensDriver:
    """A driver whose batch method predates the max_tokens argument."""

    def __init__(self):
        self.calls = 0

    def generate_text(self, prompt, rng, **kwargs):
        return "single"

    def batch_generate_text(self, prompts, rng):
        self.calls += 1
        return ["batched"] * len(prompts)


def test_the_batch_path_claims_a_rate_limit_slot_for_every_prompt(monkeypatch):
    """Going wide must not go around the limiter.

    The driver fans the group out across a thread pool and never sees the
    limiter, so unless the router claims the slots before dispatching, a
    configured RPM is simply ignored - which nothing noticed while this
    function had no callers.
    """
    driver = _CountingDriver()
    waits = []

    class _Limiter:
        requests_per_minute = 20

        def wait_if_needed(self, verbose=True):
            waits.append(1)

    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)
    monkeypatch.setattr(router, "_get_provider", lambda: "openai_compat")
    monkeypatch.setattr(router, "get_rate_limiter", lambda model_name=None: _Limiter())

    router.batch_generate_text(["a", "b", "c"], Random(1), show_spinner=False)
    assert len(waits) == 3


def test_max_tokens_reaches_a_driver_that_accepts_it(monkeypatch):
    driver = _CountingDriver()
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)
    monkeypatch.setattr(router, "_get_provider", lambda: "openai_compat")
    monkeypatch.setattr(router, "get_rate_limiter", lambda model_name=None: None)

    router.batch_generate_text(["a", "b"], Random(1), show_spinner=False,
                               max_tokens=150)
    assert driver.batches == [(2, 150)]


def test_max_tokens_is_not_forced_on_a_driver_that_cannot_take_it(monkeypatch):
    """The mock and offline drivers take (prompts, rng) alone.

    Passing an argument they do not declare would turn the graceful fallback
    into a TypeError at the worst possible moment.
    """
    driver = _NoMaxTokensDriver()
    monkeypatch.setattr(router, "_get_text_driver", lambda model_name=None: driver)
    monkeypatch.setattr(router, "_get_provider", lambda: "openai_compat")
    monkeypatch.setattr(router, "get_rate_limiter", lambda model_name=None: None)

    assert router.batch_generate_text(["a"], Random(1), show_spinner=False,
                                      max_tokens=150) == ["batched"]
    assert driver.calls == 1


def test_a_batch_error_never_becomes_an_advisor_line():
    """The batch path reports a failed prompt as "[ERROR: ...]" text rather
    than raising. It is truthy, so without an explicit guard it survives as
    the advisor's spoken line and the player reads an HTTP status attributed
    to a cabinet minister. The single-call path could not produce this."""
    import engine.narrative_adjudication as na

    from models.narrative_state import NarrativeState

    def batch(prompts, rng, **kw):
        return ["[ERROR: 429 Too Many Requests]"] * len(prompts)

    from models.narrative_state import CharacterAttitude
    ns = NarrativeState(hidden_metrics=Metrics(escalation_risk=60,
                                               domestic_stability=40,
                                               alliance_cohesion=50), turn=2)
    # _select_responding_characters always seats the NSA, and the loop skips
    # any id absent from characters - without one the test proves nothing.
    ns.characters["uk_nsa"] = CharacterAttitude(
        character_id="uk_nsa", name="National Security Adviser", trust=50)
    out = na.generate_character_responses(
        "hold the line", {"quality": "good", "reasoning": "fine"}, {}, ns,
        lambda *a, **k: "unused", Random(1), llm_batch_fn=batch)

    for name, line in out:
        assert "[ERROR:" not in line, f"{name} spoke a driver error: {line!r}"
        assert line.endswith("Understood, Prime Minister."), line


def test_a_short_batch_result_does_not_drop_advisors():
    """Callers zip the result against their input, so a short list silently
    loses the trailing advisors instead of failing."""
    from llm.fanout import generate_group

    out = generate_group(["a", "b", "c"], lambda *a, **k: "x", Random(1),
                         llm_batch_fn=lambda p, r, **kw: ["only one"])
    assert len(out) == 3, out
    assert out[0] == "only one"
    assert out[1] == "" and out[2] == ""
