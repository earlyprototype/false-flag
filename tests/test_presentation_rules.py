"""Presentation rules: plain text at the source, one voice per prompt.

The live session showed raw markdown throughout play. The cause was
systemic: no prompt forbade markdown, three demanded it, the scripted
episodes embedded it, and two front ends render none. These tests pin the
class fix - plain-text instructions on every player-facing family, clean
authored content, and the scene-setting/stance fixes from the same audit.
"""

import glob
from pathlib import Path

import pytest

from engine.game_manager import GameManager

REPO = Path(__file__).resolve().parents[1]


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
