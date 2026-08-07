"""The call log: one JSONL record per LLM call, only when asked for.

The log is the instrument behind the verification matrix
(audits/VERIFICATION-MATRIX.md): input-side evidence (what context reached
a call), output-side evidence (raw reply vs parsed), routing evidence
(which model a family resolved to) and truncation evidence all read from
these records.
"""

import json
from random import Random

import pytest

from llm import call_log, parse_health
from llm.model_config import LLMContext


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    call_log.reset()
    parse_health.reset()
    monkeypatch.delenv("WARGAME_CALL_LOG", raising=False)
    yield
    call_log.reset()
    parse_health.reset()


def read_records(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class TestCallLogModule:
    def test_the_log_is_inert_when_the_env_var_is_unset(self, tmp_path):
        target = tmp_path / "calls.jsonl"
        call_log.record(family="advisor_qa", tier="pro", provider="mock",
                        model=None, prompt="p", reply="r")
        assert not call_log.enabled()
        assert not target.exists()

    def test_one_record_per_call_with_sequence_numbers(self, tmp_path, monkeypatch):
        target = tmp_path / "calls.jsonl"
        monkeypatch.setenv("WARGAME_CALL_LOG", str(target))
        call_log.record(family="advisor_qa", tier="pro", provider="mock",
                        model="m", prompt="first", reply="a")
        call_log.record(family="narrator", tier="flash", provider="mock",
                        model="m", prompt="second", reply="b")
        records = read_records(target)
        assert [r["seq"] for r in records] == [1, 2]
        assert records[0]["prompt"] == "first"
        assert records[1]["family"] == "narrator"

    def test_set_field_annotates_until_changed(self, tmp_path, monkeypatch):
        target = tmp_path / "calls.jsonl"
        monkeypatch.setenv("WARGAME_CALL_LOG", str(target))
        call_log.set_field("turn", 3)
        call_log.record(family="narrator", tier="flash", provider="mock",
                        model=None, prompt="p", reply="r")
        call_log.set_field("turn", 4)
        call_log.record(family="narrator", tier="flash", provider="mock",
                        model=None, prompt="p", reply="r")
        call_log.set_field("turn", None)
        call_log.record(family="narrator", tier="flash", provider="mock",
                        model=None, prompt="p", reply="r")
        turns = [r.get("turn") for r in read_records(target)]
        assert turns == [3, 4, None]


class TestRouterIntegration:
    def test_generate_text_logs_family_tier_and_reply(self, tmp_path, monkeypatch):
        target = tmp_path / "calls.jsonl"
        monkeypatch.setenv("WARGAME_CALL_LOG", str(target))
        monkeypatch.setenv("WARGAME_LLM", "mock")
        from llm import router
        reply = router.generate_text(
            "What is the situation?", Random(42), show_spinner=False,
            context=LLMContext.QUALITY_ASSESSMENT)
        records = read_records(target)
        assert len(records) == 1
        rec = records[0]
        assert rec["family"] == "quality_assessment"
        assert rec["tier"] == "pro"
        assert rec["provider"] == "mock"
        assert rec["prompt"] == "What is the situation?"
        assert rec["reply"] == reply
        assert rec["fallback"] is False

    def test_batch_generate_text_logs_every_prompt(self, tmp_path, monkeypatch):
        target = tmp_path / "calls.jsonl"
        monkeypatch.setenv("WARGAME_CALL_LOG", str(target))
        monkeypatch.setenv("WARGAME_LLM", "mock")
        from llm import router
        replies = router.batch_generate_text(
            ["a", "b", "c"], Random(42), show_spinner=False,
            context=LLMContext.ACTOR_SIMULATION)
        records = read_records(target)
        assert len(records) == 3
        assert [r["batch_index"] for r in records] == [0, 1, 2]
        assert all(r["batch_size"] == 3 for r in records)
        assert [r["reply"] for r in records] == replies

    def test_the_router_stays_silent_without_the_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WARGAME_LLM", "mock")
        from llm import router
        router.generate_text("q", Random(1), show_spinner=False,
                             context=LLMContext.NARRATOR)
        assert list(tmp_path.iterdir()) == []


class TestParseHealthExtensions:
    def test_truncations_and_residues_are_counted_and_reset(self):
        parse_health.record_truncation("situation_summary", "length")
        parse_health.record_residue("actor_simulation", 3, "stray line")
        snap = parse_health.snapshot()
        assert snap["truncations"] == {"situation_summary": 1}
        assert snap["residues"] == {"actor_simulation": 1}
        assert parse_health.total() == 2
        parse_health.reset()
        assert parse_health.total() == 0
        assert parse_health.snapshot()["truncations"] == {}
