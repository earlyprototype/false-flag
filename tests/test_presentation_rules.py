"""Presentation rules: plain text at the source, one voice per prompt.

The live session showed raw markdown throughout play. The cause was
systemic: no prompt forbade markdown, three demanded it, the scripted
episodes embedded it, and two front ends render none. These tests pin the
class fix - plain-text instructions on every player-facing family, clean
authored content, and the scene-setting/stance fixes from the same audit.
"""

import glob
import re
from pathlib import Path

import pytest

from engine.game_manager import GameManager

REPO = Path(__file__).resolve().parents[1]

# "in Turn 2", "TURN 11" - game time by numeral. Kept on its own because a
# transcript header ("=== TURN 1 ===") legitimately carries this form; only
# instruction text is held to it.
_NUMBERED_TURN_RE = re.compile(r"\bturn \d+\b", re.IGNORECASE)

# The forms the numeral pattern misses, and the two the rule text itself
# used to quote (issue #97): a turn number spelled out ("in turn two") and
# turn-relative game time ("last turn"). Neither has any business appearing
# anywhere in an advisor-voiced prompt, headers included.
_WORDED_TURN_RE = re.compile(
    r"\bturn (?:one|two|three|four|five|six|seven|eight|nine|ten|eleven"
    r"|twelve)\b|\b(?:last|next|this|previous) turn\b",
    re.IGNORECASE)

# Everything the advisor voice forbids, for the instruction text that must
# demonstrate none of it.
_GAME_TURN_RE = re.compile(
    _NUMBERED_TURN_RE.pattern + "|" + _WORDED_TURN_RE.pattern, re.IGNORECASE)

# The standing rule that no metric may be spoken of as a number.
_NO_VALUES_RULE = "Do NOT reference 'metrics', 'game mechanics', 'scores', or 'values'."


class TestPromptsForbidMarkdown:
    def test_no_prompt_demands_bold(self):
        source = (REPO / "llm" / "prompts.py").read_text(encoding="utf-8")
        assert "Use **bold**" not in source

    def test_advisor_voice_carries_the_plain_text_rule(self):
        from llm.prompts import ADVISOR_VOICE_INSTRUCTIONS, PLAIN_TEXT_RULE
        assert PLAIN_TEXT_RULE in ADVISOR_VOICE_INSTRUCTIONS
        assert "British English" in ADVISOR_VOICE_INSTRUCTIONS

    def test_player_facing_family_prompts_carry_a_no_markdown_line(self):
        gm = GameManager(seed=5)

        from engine.actor_simulation import build_actor_prompt
        from engine.narrative_adjudication import (
            build_character_response_prompt)
        actor = gm.world.actor_system.actors["USA"]
        assert "no markdown" in build_actor_prompt(
            actor, "Blockade announced", gm.world).lower()

        char = gm.narrative_state.characters["uk_cds"]
        reaction = build_character_response_prompt(
            char, "Blockade announced", "good", gm.narrative_state)
        assert "no markdown" in reaction.lower()
        assert "British English" in reaction

    def test_the_narrator_is_not_also_an_advisor(self):
        from llm.prompts import build_narrator_intro_prompt
        gm = GameManager(seed=5)
        prompt = build_narrator_intro_prompt(
            gm.world, ["Line one", "Line two"], "NEXT EVENT")
        assert "You are the Narrator" in prompt
        assert "real advisor in COBRA" not in prompt


class TestPromptsDoNotContradictThemselves:
    """No prompt may demonstrate, or supply, what its own rules forbid.

    Each of these pinned a live contradiction (issue #91): a worked example
    written in game time under a rule banning game time; a printed
    scoreboard under a rule banning numbers; and one advisor template
    serving both the routed and the whole-room call shapes.
    """

    def _prompts(self):
        from tests.prompt_parity_fixtures import build_all_prompts
        return build_all_prompts()

    def test_no_instruction_text_demonstrates_game_time(self):
        """The rule and its examples are the text an advisor imitates."""
        from llm import prompt_templates as pt
        from llm.prompts import ADVISOR_VOICE_INSTRUCTIONS

        for family, text in pt.DEFAULTS.items():
            found = _GAME_TURN_RE.search(text)
            assert found is None, (
                f"{family} template shows game time {found.group(0)!r} while "
                "the advisor voice forbids it")
        found = _GAME_TURN_RE.search(ADVISOR_VOICE_INSTRUCTIONS)
        assert found is None, (
            f"the voice rule demonstrates {found.group(0)!r}, the very form "
            "it bans")

    def test_no_advisor_voiced_prompt_speaks_in_game_time(self):
        """The whole assembled prompt, not just the rule that ends it.

        The numeral form is exempted here alone: the transcript block heads
        each turn "=== TURN 1 ===", which is the history's own structure and
        not something the advisor is invited to say. The spelled-out and
        relative forms have no such excuse - and they were exactly what the
        rule text smuggled in (issue #97).
        """
        from llm.prompts import ADVISOR_VOICE_INSTRUCTIONS

        voiced = {family: prompt for family, prompt in self._prompts().items()
                  if ADVISOR_VOICE_INSTRUCTIONS in prompt}
        assert voiced, "no prompt carries the advisor voice - fixture broken"
        for family, prompt in voiced.items():
            found = _WORDED_TURN_RE.search(prompt)
            assert found is None, (
                f"{family} speaks game time {found.group(0)!r} in a prompt "
                "whose own rule forbids it")

    def test_a_prompt_that_bans_values_is_shown_none(self):
        """The four advisor-voiced calls get the situation in words."""
        for family, prompt in self._prompts().items():
            if _NO_VALUES_RULE not in prompt:
                continue
            assert "/100" not in prompt, (
                f"{family} prints a metric value under a rule forbidding "
                "any reference to values")
            assert "THREAT ASSESSMENT:" in prompt, (
                f"{family} bans the numbers without giving the situation "
                "in words")

    def test_the_whole_room_prompt_does_not_deflect_to_the_room(self):
        """Fanout asks every advisor at once, so 'ask someone else' is an
        instruction that call shape cannot honour."""
        prompts = self._prompts()
        deflection = "suggest who might better answer it"
        assert deflection in prompts["advisor_qa"]
        assert deflection not in prompts["advisor_qa_fanout"]
        assert "Every member of the COBRA cell is answering this question" \
            in prompts["advisor_qa_fanout"]


class TestAuthoredContentIsClean:
    def test_episode_yamls_contain_no_markdown_bold(self):
        for path in glob.glob(
                str(REPO / "data" / "scenarios" / "war_game_2025"
                    / "episodes" / "*.yaml")):
            content = Path(path).read_text(encoding="utf-8")
            assert "**" not in content, f"markdown bold in {path}"

    def test_no_real_leader_is_named(self):
        for path in glob.glob(
                str(REPO / "data" / "scenarios" / "war_game_2025"
                    / "episodes" / "*.yaml")):
            content = Path(path).read_text(encoding="utf-8")
            assert "Trump" not in content, f"named real person in {path}"

    def test_opening_scenes_are_stripped_of_rich_markup(self):
        gm = GameManager(seed=5)
        scenes = gm.get_opening_scenes()
        assert scenes, "no opening scenes - the cold open is gone"
        for scene in scenes:
            for line in scene.body:
                assert "[cyan" not in line and "[/" not in line, (
                    f"Rich markup reached a plain-text front end: {line!r}")


class TestAdvisorPanelIsTheUKCabinet:
    def test_only_uk_characters_and_the_attorney_general_present(self):
        gm = GameManager(seed=5)
        roles = {a["role"] for a in gm.get_advisors_state()}
        assert all(r.startswith("uk_") for r in roles)
        assert "uk_attorney_general" in roles
        assert "usa_nsa" not in roles


class TestRequiredCallConnectsAsPromised:
    def test_the_scripted_call_reaches_the_leader_even_at_low_cohesion(self):
        from engine.diplomacy import DiplomaticEncounter
        gm = GameManager(seed=5)
        gm.world.metrics.alliance_cohesion = 25   # below every threshold
        enc = DiplomaticEncounter(
            gm.world, "US", "Scripted premise", gm.root_path,
            full_transcript=[], required=True,
            narrative_state=gm.narrative_state)
        assert enc.active, "the caller refused their own call"
        assert enc.access_level == "leader"

    def test_optional_calls_still_gate_on_cohesion(self):
        from engine.diplomacy import DiplomaticEncounter
        gm = GameManager(seed=5)
        gm.world.metrics.alliance_cohesion = 25
        enc = DiplomaticEncounter(
            gm.world, "US", None, gm.root_path,
            full_transcript=[], required=False,
            narrative_state=gm.narrative_state)
        assert enc.access_level != "leader"


class TestNarrativeStances:
    def _narratives(self):
        from engine.scenario_loader import load_narrative_configs
        return load_narrative_configs("war_game_2025", REPO)

    def test_every_simulated_capital_has_a_stance_in_every_narrative(self):
        narratives = self._narratives()
        assert narratives
        for narrative in narratives:
            have = {s.country_code for s in narrative.stances}
            for code in ("USA", "FRA", "DEU", "POL", "RUS", "UKR"):
                assert code in have, (
                    f"{narrative.narrative_id} missing stance for {code}")

    def test_stanceless_roleplay_gets_no_secret_motive_order(self):
        narratives = self._narratives()
        context = narratives[0].to_llm_context(target_country_code="XYZ")
        assert "Act according to your secret motive" not in context
        assert "declared interests" in context

    def test_stanced_roleplay_still_gets_its_motive(self):
        narratives = self._narratives()
        context = narratives[0].to_llm_context(target_country_code="FRA")
        assert "SECRET MOTIVE" in context
        assert "Act according to your secret motive" in context
