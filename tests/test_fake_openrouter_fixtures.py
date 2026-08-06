"""The measurement endpoint: classification keeps up with the prompts, and
the fixtures mode substitutes adversarial replies deterministically.

dev-scripts/fake_openrouter.py is what every campaign measurement runs
against, so its two soft spots get pinned here: the tail markers that name
each call family (which drifted when the diplomacy prompts were reworked),
and the --fixtures mode used to feed one call family a hostile reply while
the rest of the campaign runs clean.
"""

import importlib.util
import json
from pathlib import Path
from random import Random

import pytest

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "fake_openrouter", ROOT / "dev-scripts" / "fake_openrouter.py")
fake_openrouter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fake_openrouter)


class TestClassify:
    def test_the_outcome_assessment_is_named_from_its_closing_line(self):
        prompt = "x" * 5000 + "\nOUTCOME: [SUCCESS/NEUTRAL/FAILURE]\n\nYour assessment:"
        assert fake_openrouter.classify(prompt) == "diplomacy_outcome"

    def test_the_counterpart_turn_is_named_from_its_closing_line(self):
        prompt = ("x" * 25000
                  + "\nYour response (as US National Security Advisor):")
        assert fake_openrouter.classify(prompt) == "diplomacy"

    def test_the_counterpart_marker_does_not_depend_on_transcript_text(self):
        # The old heuristic looked for "diplomat" anywhere in the tail, which
        # only held while transcript text happened to sit inside the window.
        prompt = ("no marker words here " * 2000
                  + "\nYour response (as Chancellor of Germany):")
        assert fake_openrouter.classify(prompt) == "diplomacy"


class TestOutcomeCannedReply:
    def test_the_canned_outcome_reply_parses_without_a_miss(self):
        """The endpoint's reply must clear the real parser, or a measurement
        run degrades to fallbacks and mismeasures what it claims to watch."""
        from engine.diplomacy import assess_diplomatic_outcome
        from llm import parse_health
        from models.world import Metrics, WorldState

        parse_health.reset()
        canned = fake_openrouter._RESPONSES["diplomacy_outcome"]

        def stub(prompt, rng, **kw):
            return canned

        world = WorldState(metrics=Metrics(
            escalation_risk=60, domestic_stability=50, alliance_cohesion=50))
        assessment, delta = assess_diplomatic_outcome(
            world, "US", [("US National Security Advisor", "Hello.")],
            stub, Random(0))
        assert delta == 2
        assert "channel stays open" in assessment
        health = parse_health.snapshot()
        assert not any(k.startswith("diplomacy_outcome") for k in health["misses"])


class TestFixtures:
    def test_fixtures_load_and_match_in_file_order(self, tmp_path):
        path = tmp_path / "fixtures.json"
        path.write_text(json.dumps({
            "QUALITY MULTIPLIER:": "first",
            "MULTIPLIER:": "second",
        }), encoding="utf-8")
        fixtures = fake_openrouter.load_fixtures(str(path))
        assert fixtures == [("QUALITY MULTIPLIER:", "first"),
                            ("MULTIPLIER:", "second")]
        # First match in file order wins, even when a later pattern also hits.
        assert fake_openrouter.match_fixture(
            fixtures, "... QUALITY MULTIPLIER: 1.0 ...") == (
                "QUALITY MULTIPLIER:", "first")
        assert fake_openrouter.match_fixture(fixtures, "no match") is None

    def test_a_non_string_table_is_refused(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"key": 3}), encoding="utf-8")
        with pytest.raises(ValueError):
            fake_openrouter.load_fixtures(str(path))
        path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        with pytest.raises(ValueError):
            fake_openrouter.load_fixtures(str(path))
