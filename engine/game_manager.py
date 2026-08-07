"""Game Manager for API/Headless execution.

Manages the state and lifecycle of a single game session without CLI dependencies.
"""

from pathlib import Path
from random import Random
from typing import Optional, List, Dict, Any
import os

from models.world import WorldState, Metrics
from models.narrative_state import NarrativeState, create_initial_narrative_state
from engine.endings import (
    EPILOGUE_TURNS, Ending, build_debrief_lines, check_ending, get_ending,
)
from engine.flags import update_world_flags
from engine.initial_conditions import load_initial_conditions
from engine.scenario_loader import (
    get_scenario_config,
    get_turn_filename,
    load_narrative_configs,
)
from engine.sim_loop import run_turn_briefing, run_turn_decision, run_turn_discussion  # noqa: F401 (run_turn_decision: preview path)

# Environment flag to disable Rich output in engine modules
os.environ["WARGAME_RICH_UI"] = "false"


class GameManager:
    def __init__(
        self,
        scenario_id: str = "war_game_2025",
        variant: str = "standard",
        difficulty: str = "standard",
        play_mode: str = "immersive",
        seed: int = 42,
        mystery_mode: bool = False,
        endings: Optional[bool] = None
    ):
        """Create a headless game session.

        Args:
            scenario_id: Scenario identifier (e.g. "war_game_2025")
            variant: Scenario variant ("standard", "fast_start", ...)
            difficulty: Difficulty key applied to inject effects
            play_mode: "classic" | "immersive" | "emergent"
            seed: RNG seed (determinism)
            mystery_mode: If True, draw a hidden narrative truth from the
                scenario's narratives.yaml, the way the CLI's Mystery Mode
                does. The drawn narrative is never surfaced to the player.
            endings: Whether terminal win/lose checks apply. ``None`` keeps
                the CLI's rule (classic mode only); pass True to grade any
                mode, which is what a session with no "quit" affordance
                (browser, API) needs so a campaign can actually finish.
        """
        self.scenario_id = scenario_id
        self.variant = variant
        self.difficulty = difficulty
        self.play_mode = play_mode
        self.seed = seed
        self.mystery_mode = mystery_mode
        self.rng = Random(seed)

        # Terminal conditions. The CLI only grades classic campaigns; other
        # front ends (browser, API) need to opt in explicitly.
        self.endings_enabled = (play_mode == "classic") if endings is None else bool(endings)
        self.ending: Optional[Ending] = None

        from engine.persistence import _default_root
        self.root_path = _default_root()
        self.transcript: List[str] = []
        self.active_encounter = None

        # The last previewed decision and the advisors who pushed back on it,
        # set by interpret_decision. Committing the identical text unamended
        # costs a point of trust with each objecting advisor (ER-013).
        self._pending_pushback: Optional[tuple] = None

        # True when the next briefing is a replay of one that already ran
        # before a save/load (ER-004): show it for context, but do not
        # re-apply its effects, re-record its ledger entry, regenerate its
        # event, or re-open its mandatory diplomatic call. Set by from_dict
        # when the restored world is mid-turn.
        self._resume_replay: bool = False

        # Initialize World
        self._init_world()

        # Campaign-start metrics, so the debrief can report deltas from the
        # beginning of the campaign rather than from wherever it ended.
        self.initial_metrics_snapshot = {
            "escalation_risk": self.world.metrics.escalation_risk,
            "domestic_stability": self.world.metrics.domestic_stability,
            "alliance_cohesion": self.world.metrics.alliance_cohesion,
        }

    def _init_world(self):
        """Initialize world state, actor system, and narrative state."""
        self.initial_conditions = load_initial_conditions(self.scenario_id, self.root_path)
        initial_metrics = self.initial_conditions.get("initial_metrics", {})

        # Mystery Mode: draw a hidden narrative truth that colours actor
        # behaviour. Original Story Mode leaves this None.
        selected_narrative = None
        if self.mystery_mode:
            try:
                narratives = load_narrative_configs(self.scenario_id, self.root_path)
                if narratives:
                    selected_narrative = self.rng.choice(narratives)
            except Exception as e:  # pragma: no cover - malformed scenario data
                print(f"Warning: Could not load narratives for mystery mode: {e}")

        self.world = WorldState(
            turn=1,
            scene=1,
            difficulty=self.difficulty,
            narrative=selected_narrative,  # The secret truth (Mystery Mode only)
            metrics=Metrics(
                escalation_risk=initial_metrics.get("escalation_risk", 60),
                domestic_stability=initial_metrics.get("domestic_stability", 50),
                alliance_cohesion=initial_metrics.get("alliance_cohesion", 40),
                casualties_mil=initial_metrics.get("casualties_mil", 2),
                casualties_civ=initial_metrics.get("casualties_civ", 0),
            ),
            flags={},
            posture={},
            phase="briefing"
        )
        
        # Initialize State Actors
        try:
            from models.state_actors import load_actors_from_yaml
            actor_yaml_path = self.root_path / "data" / "state_actors.yaml"
            self.world.actor_system = load_actors_from_yaml(str(actor_yaml_path))
        except Exception as e:
            print(f"Warning: Could not load actor system: {e}")
            self.world.actor_system = None
            
        # Initialize Narrative State
        self.narrative_state = create_initial_narrative_state(
            metrics=self.world.metrics.copy(),
            play_mode=self.play_mode,
            game_time=self.initial_conditions.get("metadata", {}).get("start_time", "Sunday 5th October 2025, 17:00")
        )
        
        # Load Scenario Config
        self.scenario_config = get_scenario_config(self.scenario_id, self.variant, self.root_path)

    def get_turn_briefing(self) -> Dict[str, Any]:
        """Run the briefing phase and return the inject."""
        stochastic_from = self.scenario_config.get("stochastic_from", 7)
        use_stochastic = self.world.turn >= stochastic_from
        turn_filename = get_turn_filename(self.world.turn, self.scenario_config)

        # Only the first briefing after a mid-turn load is a replay (ER-004).
        replay = self._resume_replay
        self._resume_replay = False

        inject, lines = run_turn_briefing(
            self.world,
            self.scenario_id,
            use_stochastic,
            self.rng,
            self.root_path,
            self.transcript,
            turn_filename=turn_filename,
            suppress_display=True,
            silent_effects=True,
            replay=replay,  # Loaded mid-turn save: show briefing, don't re-apply it
            narrative_state=self.narrative_state  # Feeds the event ledger (issue #25)
        )

        self.transcript.extend(lines)

        # A scripted mandatory encounter: the briefing hands back the spec
        # rather than playing the call for the player (ER-033). Open the
        # line here so the existing process_diplomacy plumbing can drive it.
        pending = (inject or {}).pop("_pending_encounter", None)
        if pending:
            from engine.diplomacy import DiplomaticEncounter, normalize_country

            self.active_encounter = DiplomaticEncounter(
                self.world,
                normalize_country(pending.get("country")),
                pending.get("context"),
                self.root_path,
                full_transcript=self.transcript,
                show_metrics=self.play_mode == "classic",
                required=True,
                narrative_state=self.narrative_state  # Memory for the outcome call (ER-017)
            )
            opening = self.active_encounter.start(self.rng)
            self.transcript.extend(opening)
            inject["pending_encounter"] = {
                "country": pending.get("country"),
                "context": pending.get("context"),
                "title": self.active_encounter.title,
            }

        # Sync inject effects into the narrative state. Adjudication mutates
        # narrative_state.hidden_metrics and the result is copied back over
        # world.metrics at end of turn, so any briefing effect left only on
        # world.metrics would be silently reverted. This also snapshots
        # previous_metrics, giving the immersive-mode vibes a real trend
        # baseline. Not on replay (ER-004): nothing was applied, so there is
        # nothing to sync — the same guard the CLI loop carries.
        if not replay:
            self.narrative_state.update_hidden_metrics({
                "escalation_risk": self.world.metrics.escalation_risk,
                "domestic_stability": self.world.metrics.domestic_stability,
                "alliance_cohesion": self.world.metrics.alliance_cohesion,
                "casualties_mil": self.world.metrics.casualties_mil,
                "casualties_civ": self.world.metrics.casualties_civ,
            })

        # The briefing has now been played, so any save taken from here on
        # must resume as a replay. from_dict derives that from the phase,
        # and "briefing" means NOT-a-replay - so a save between this return
        # and the first question would re-apply the inject's effects and
        # re-open the mandatory call on load. The terminal CLIs force the
        # phase forward for exactly this reason (cli/main.py); the headless
        # front ends (browser, API) go through here.
        self.world.phase = "discussion"

        return inject or {}

    def process_question(self, question_text: str) -> List[str]:
        """Process a player question during Discussion phase.

        No pre-append of the question here: run_turn_discussion writes the
        "Prime Minister: ..." line into the lines extended below, and doing
        both put every question in the transcript twice (ER-024).
        """
        discussion_lines = run_turn_discussion(
            self.world,
            self.scenario_id,
            [question_text],
            self.rng,
            self.root_path,
            self.transcript,
            narrative_state=self.narrative_state  # Feeds the event ledger (ER-003)
        )
        
        self.transcript.extend(discussion_lines)
        return discussion_lines

    # PHASE 1: DECISION LOOP -------------------------------------------

    def interpret_decision(self, action_text: str) -> Dict[str, Any]:
        """Interpret decision and gather advisor feedback without committing.

        Pushback and critical omissions are returned as separate lists - a
        consumer must be able to tell a cabinet objection from an omissions
        warning (ER-013). The commit path (resolve_decision) keeps them
        separate too.
        """
        interpretation, pushback, critical_concerns, decision_lines = run_turn_decision(
            self.world,
            self.scenario_id,
            action_text,
            self.rng,
            self.root_path,
            self.transcript,
            dry_run=True,  # Don't advance phase or commit to transcript yet
            narrative_state=self.narrative_state
        )

        # Format critical concerns for API
        concerns_list = []
        if critical_concerns:
            for role, concern, recommendation in critical_concerns:
                concerns_list.append({
                    "role": role,
                    "concern": concern,
                    "recommendation": recommendation
                })

        # Remember who objected to exactly this text: overriding them
        # unamended at commit time has a trust cost (ER-013).
        self._pending_pushback = (
            (action_text, [role for role, _ in pushback]) if pushback else None
        )

        # Create placeholder data for missing fields
        return {
            "interpretation": interpretation,
            "critical_concerns": concerns_list,
            "pushback": [{"role": r, "concern": c} for r, c in (pushback or [])],
            "raw_transcript": decision_lines,
            "forces_involved": [],  # Placeholder
            "timeline": "Immediate" # Placeholder
        }

    def _apply_pushback_trust_cost(self, objecting_roles: List[str]) -> None:
        """Overriding a raised objection verbatim costs one point of trust.

        Deterministic and deliberately small: the roles the pushback parser
        returns ("Foreign Secretary") are matched by name against the
        narrative state's characters, and each match takes a -1 through the
        existing attitude machinery. Roles with no seeded character (e.g. the
        Attorney General) are simply skipped (ER-013).
        """
        by_name = {}
        for char_id, char in self.narrative_state.characters.items():
            name = char.get("name", "") if isinstance(char, dict) else getattr(char, "name", "")
            by_name.setdefault(str(name).strip().lower(), char_id)
        for role in objecting_roles:
            char_id = by_name.get(str(role).strip().lower())
            if char_id:
                self.narrative_state.update_character_attitude(char_id, trust_delta=-1)

    # CAMPAIGN TERMINATION ----------------------------------------------

    @property
    def campaign_final_turn(self) -> int:
        """Turn on which the campaign is graded if no threshold ending fires.

        Mirrors cli/main.py: the scripted turns plus a short stochastic
        epilogue.
        """
        stochastic_from = self.scenario_config.get("stochastic_from", 7)
        epilogue = self.scenario_config.get("epilogue_turns", EPILOGUE_TURNS)
        return (stochastic_from - 1) + epilogue

    def check_campaign_ending(self) -> Optional[Ending]:
        """Return the terminal Ending if the campaign is over, else None.

        Must be called while ``world.turn`` still names the turn that has
        just been adjudicated (i.e. before the turn counter advances), which
        is how the CLI loop orders it.
        """
        if not self.endings_enabled:
            return None
        return check_ending(self.world, final_turn=self.campaign_final_turn)

    def get_debrief_lines(self) -> List[str]:
        """Plain-text after-action debrief for the ending that fired."""
        if not self.ending:
            return []
        return build_debrief_lines(
            self.world, self.ending, self.initial_metrics_snapshot, self.transcript
        )

    def is_over(self) -> bool:
        """True once a terminal ending has fired."""
        return self.ending is not None

    def resolve_decision(self, action_text: str) -> Dict[str, Any]:
        """Commit and resolve a decision (Adjudication phase).

        This is the one-step commit path (headless, browser, HTTP), so it
        runs the full three-round decision pipeline (ER-023) rather than
        the terminal CLIs' interpret → preview → confirm shape.
        """
        # The preview raised pushback and the player committed the identical
        # text unamended: the overridden advisors lose a point of trust
        # (ER-013). Amending the text, or committing without a preview,
        # costs nothing. Applied before the pipeline runs, so the prompts
        # that render trust (quality assessment, reactions) see the cost -
        # the same ordering the serial path had.
        pending = self._pending_pushback
        self._pending_pushback = None
        if pending and pending[0] == action_text and pending[1]:
            self._apply_pushback_trust_cost(pending[1])

        interpretation = ""
        pushback = []
        critical_concerns = []
        final_effects = {}
        character_responses = []
        actor_responses = []
        reasoning = ""
        error = None

        try:
            from engine.decision_phase import run_decision_pipeline
            from llm.router import generate_text, batch_generate_text

            result = run_decision_pipeline(
                self.world,
                self.scenario_id,
                action_text,
                self.rng,
                root_path=self.root_path,
                full_transcript=self.transcript,
                narrative_state=self.narrative_state,
                llm_generate_fn=generate_text,
                llm_batch_fn=batch_generate_text,
            )
            interpretation = result.interpretation
            pushback = result.pushback
            critical_concerns = result.critical_concerns
            final_effects = result.final_effects
            character_responses = result.character_responses
            actor_responses = result.actor_responses
            reasoning = result.reasoning
            self.transcript.extend(result.transcript)

            # Sync world metrics with narrative state (keep both in sync)
            self.world.metrics.escalation_risk = self.narrative_state.hidden_metrics.escalation_risk
            self.world.metrics.domestic_stability = self.narrative_state.hidden_metrics.domestic_stability
            self.world.metrics.alliance_cohesion = self.narrative_state.hidden_metrics.alliance_cohesion
            self.world.metrics.casualties_mil = self.narrative_state.hidden_metrics.casualties_mil
            self.world.metrics.casualties_civ = self.narrative_state.hidden_metrics.casualties_civ
            update_world_flags(self.world)
        except Exception as e:
            # Keep the print for server logs, but surface the failure to callers
            print(f"Adjudication error: {e}")
            error = str(e)

        # Keep narrative state clock in sync before the turn advances
        self.narrative_state.turn = self.world.turn

        # Terminal conditions are checked against the turn that just played,
        # before the counter advances — same ordering as the CLI loop. Without
        # this a headless session (browser, API) could never finish a campaign.
        if self.ending is None:
            self.ending = self.check_campaign_ending()

        # Update Phase & Turn
        self.world.turn += 1
        self.world.phase = "briefing"
        self.world.scene = self.world.turn
        self.world.discussion_transcript = []

        return {
            "interpretation": interpretation,
            "reasoning": reasoning,
            "effects": final_effects,
            "advisor_reactions": character_responses,
            "international_reactions": [r.dict() for r in actor_responses] if actor_responses else [],
            "pushback": [{"role": r, "concern": c} for r, c in (pushback or [])],
            "critical_concerns": [
                {"role": r, "concern": c, "recommendation": rec}
                for r, c, rec in (critical_concerns or [])
            ],
            "ending": {
                "ending_id": self.ending.ending_id,
                "title": self.ending.title,
                "verdict": self.ending.verdict,
                "narrative": self.ending.narrative,
                "debrief": self.get_debrief_lines(),
            } if self.ending else None,
            "error": error
        }

    def commit_decision(self, action_text: str) -> Dict[str, Any]:
        """Legacy/Wrapper method: Process player decision and return results."""
        return self.resolve_decision(action_text)

    # PHASE 2: DEEP STATE METHODS --------------------------------------

    def get_situation_vibes(self) -> Dict[str, Any]:
        """Get current narrative atmosphere."""
        vibes_objects = self.narrative_state.get_situation_vibes()
        # Convert Pydantic objects to strings for API
        vibes_list = [f"{v.name}: {v.descriptor}" for v in vibes_objects]
        
        intensity = min(10, max(1, self.world.metrics.escalation_risk // 10))
        dominant = "NEUTRAL"
        if vibes_objects:
            dominant = vibes_objects[0].descriptor 
        
        return {"vibes": vibes_list, "dominant": dominant, "intensity": intensity}

    def get_advisors_state(self) -> List[Dict[str, Any]]:
        """Get advisor trust and relationship status."""
        advisors = []
        for role, char in self.narrative_state.characters.items():
            # Helper to handle both Pydantic models and dicts
            if isinstance(char, dict):
                name = char.get("name", role)
                trust = char.get("trust", 50)
                relationship = char.get("relationship", "professional")
                notes = char.get("description") or char.get("stance_summary")
            else:
                # Assume Pydantic model
                name = getattr(char, "name", role)
                trust = getattr(char, "trust", 50)
                relationship = getattr(char, "relationship", "professional")
                notes = getattr(char, "stance_summary", "")

            advisors.append({
                "role": role,
                "name": name,
                "trust": trust,
                "relationship": relationship,
                "status": "active",
                "notes": notes
            })
        return advisors

    def get_world_flags(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get active and inactive crisis flags."""
        active = []
        inactive = []
        for key, val in self.world.flags.items():
            item = {
                "key": key, 
                "label": key.replace("_", " ").title(),
                "severity": "monitoring"
            }
            if val:
                if isinstance(val, int) and val > 0:
                     item["turn_activated"] = val
                active.append(item)
            else:
                inactive.append(item)
        return {"active_flags": active, "inactive_flags": inactive}

    def get_intel_actors(self) -> List[Dict[str, Any]]:
        """List actors available for intelligence assessment."""
        actors = []
        if self.world.actor_system:
             for code, actor in self.world.actor_system.actors.items():
                 actors.append({
                     "code": code,
                     "name": actor.full_name,
                     "category": "adversary" if code == "RUS" else "ally" if code == "USA" else "neutral"
                 })
        else:
            actors = [
                {"code": "RUS", "name": "Russia", "category": "adversary"},
                {"code": "USA", "name": "United States", "category": "ally"},
                {"code": "CHN", "name": "China", "category": "neutral"}
            ]
        return actors

    def get_intel_detail(self, actor_code: str) -> Dict[str, Any]:
        """Generate detailed intelligence assessment."""
        from engine.intelligence import generate_actor_detailed_assessment
        
        name_map = {"RUS": "Russia", "USA": "United States", "CHN": "China"}
        if self.world.actor_system and actor_code in self.world.actor_system.actors:
            actor_name = self.world.actor_system.actors[actor_code].full_name
        else:
            actor_name = name_map.get(actor_code, actor_code)
        
        assessment = generate_actor_detailed_assessment(
            actor_code=actor_code,
            world=self.world,
            turn=self.world.turn
        )
        
        return {
            "actor": actor_name,
            "code": actor_code,
            "assessment": {"raw": assessment},
            "confidence": "medium",
            "last_updated": self.world.turn
        }

    # PHASE 3: DIPLOMACY METHODS ---------------------------------------

    def list_diplomatic_channels(self) -> List[Dict[str, Any]]:
        """Contacts the current alliance standing actually opens a line to."""
        from engine.diplomacy import list_available_diplomatic_contacts

        return [
            {"country": country, "access": access, "title": title}
            for country, access, title in
            list_available_diplomatic_contacts(self.world, self.root_path)
        ]

    def start_diplomacy(self, country_code: str) -> Dict[str, Any]:
        """Start a diplomatic encounter.

        ``country_code`` may be an ISO code ("USA", "DEU"), a country name,
        or a switchboard key; they are all resolved to the same channel.
        """
        from engine.diplomacy import DiplomaticEncounter, normalize_country

        country_code = normalize_country(country_code)

        # The full transcript feeds get_diplomatic_context (public events plus
        # the secret narrative truth); without it Mystery Mode never colours
        # foreign leaders' responses. Raw metric numbers must stay out of the
        # call in metric-hiding modes.
        # No encounter_context: that block is the authored premise of a
        # scripted call, and a meta string here would leak into the
        # counterpart's prompt as a stage direction.
        self.active_encounter = DiplomaticEncounter(
            self.world,
            country_code,
            None,
            self.root_path,
            full_transcript=self.transcript,
            show_metrics=self.play_mode == "classic",
            narrative_state=self.narrative_state  # Memory for the outcome call (ER-017)
        )
        transcript = self.active_encounter.start(self.rng)
        return {
            "transcript": transcript, 
            "active": self.active_encounter.active,
            "title": self.active_encounter.title
        }

    def process_diplomacy(self, message: str) -> Dict[str, Any]:
        """Process a turn in the active diplomatic encounter."""
        if not self.active_encounter or not self.active_encounter.active:
            return {"error": "No active diplomatic call", "active": False}
            
        from llm.router import generate_text

        mark = len(self.active_encounter.transcript)
        transcript = self.active_encounter.process_turn(message, generate_text, self.rng)
        outcome = self.active_encounter.outcome

        if self.active_encounter.required:
            # A scripted call is part of the campaign record: mirror its new
            # lines into the session transcript, the way the CLI extends the
            # game transcript after a call. (Its opening lines were mirrored
            # by get_turn_briefing.)
            self.transcript.extend(transcript[mark:])

        if outcome is not None:
            # The call has ended and its cohesion delta landed on
            # world.metrics. Mirror it into the narrative state, the way the
            # CLI does after a call: resolve_decision copies hidden_metrics
            # back over world.metrics, so a delta left only on world.metrics
            # would be silently reverted at the next decision.
            self.narrative_state.hidden_metrics.alliance_cohesion = \
                self.world.metrics.alliance_cohesion

        return {
            "transcript": transcript,
            "active": self.active_encounter.active,
            "outcome": outcome
        }

    # SAVE / LOAD SYSTEM -----------------------------------------------

    def to_dict(self, save_name: str = "session") -> Dict[str, Any]:
        """Serialise the whole session to a plain dict.

        Split out of save_game so front ends without a filesystem (the
        browser build stores saves in localStorage) can round-trip a session
        through exactly the same representation as a save file.
        """
        from datetime import datetime

        from engine.persistence import encode_rng_state

        return {
            "metadata": {
                "save_name": save_name,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "config": {
                "scenario_id": self.scenario_id,
                "variant": self.variant,
                "difficulty": self.difficulty,
                "play_mode": self.play_mode,
                "seed": self.seed,
                "mystery_mode": self.mystery_mode,
                "endings": self.endings_enabled
            },
            "state": {
                "world": self.world.dict(),
                "narrative_state": self.narrative_state.dict(),
                "transcript": self.transcript,
                "initial_metrics": self.initial_metrics_snapshot,
                "ending_id": self.ending.ending_id if self.ending else None,
                # A live diplomatic call survives the round-trip (ER-047).
                # An ended call is not stored: its outcome already landed.
                "active_encounter": self._encounter_state(),
                # Who objected to which exact decision text: the ER-013
                # trust cost must survive an interpret -> save -> load ->
                # commit sequence, or overriding the cabinet becomes free.
                "pending_pushback": (
                    [self._pending_pushback[0], list(self._pending_pushback[1])]
                    if self._pending_pushback else None
                ),
                # Generator position, so a resumed session continues the
                # draw sequence instead of replaying spent randomness (ER-037)
                "rng_state": encode_rng_state(self.rng)
            }
        }

    def _encounter_state(self) -> Optional[Dict[str, Any]]:
        """Serialisable state of a live diplomatic call, else None."""
        enc = self.active_encounter
        if enc is None or not enc.active:
            return None
        return {
            "country": enc.country,
            "context": enc.context,
            "show_metrics": enc.show_metrics,
            "required": enc.required,
            "transcript": list(enc.transcript),
            "history": [list(pair) for pair in enc.history],
            "player_exchanges": enc._player_exchanges,
        }

    def save_game(self, save_name: str) -> str:
        """Save current game state to file."""
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Sanitize filename
        safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        filename = f"{safe_name}_{timestamp}.json"

        save_dir = self.root_path / "saves"
        save_dir.mkdir(exist_ok=True)
        save_path = save_dir / filename

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(save_name), f, indent=2, default=str)

        return str(save_path)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameManager':
        """Rebuild a session from the dict produced by to_dict."""
        config = data["config"]
        state = data["state"]

        # Create instance. mystery_mode is replayed so the reconstructed
        # session knows it is a Mystery campaign; the drawn narrative itself
        # is restored verbatim from the saved world below, not re-rolled.
        manager = cls(
            scenario_id=config["scenario_id"],
            variant=config.get("variant", "standard"),
            difficulty=config.get("difficulty", "standard"),
            play_mode=config.get("play_mode", "immersive"),
            seed=config["seed"],
            mystery_mode=config.get("mystery_mode", False),
            endings=config.get("endings")
        )

        # Restore state
        from models.world import WorldState

        # Note: WorldState.parse_obj will handle nested ActorSystem if model structure matches
        manager.world = WorldState.parse_obj(state["world"])
        manager.narrative_state = NarrativeState.parse_obj(state["narrative_state"])
        manager.transcript = state["transcript"]
        if state.get("initial_metrics"):
            manager.initial_metrics_snapshot = state["initial_metrics"]

        # A campaign that ended must load as ended. Without this the restored
        # session reports is_over() == False, and a front end that resumes on
        # that answer (the browser build does) drops the player back into a
        # graded, finished game instead of showing them the ending.
        manager.ending = get_ending(state.get("ending_id"))

        # Restore the generator position AFTER construction — the constructor
        # burns draws (the Mystery Mode narrative draw), and restoring first
        # would let them corrupt the saved position (ER-037). Old payloads
        # without the field keep the fresh-seeded generator, as before.
        from engine.persistence import decode_rng_state
        rng_state = decode_rng_state(state.get("rng_state"))
        if rng_state is not None:
            manager.rng.setstate(rng_state)

        # A save taken mid-turn already ran this turn's briefing: the next
        # get_turn_briefing must replay it for context without re-applying
        # its effects or re-running its diplomatic encounter (ER-004).
        manager._resume_replay = manager.world.phase in (
            "discussion", "decision", "adjudication")

        # A call that was live at save time comes back live (ER-047). The
        # encounter is rebuilt against the restored world and narrative
        # state, then its conversation so far is restored verbatim.
        enc_data = state.get("active_encounter")
        if enc_data:
            from engine.diplomacy import DiplomaticEncounter
            enc = DiplomaticEncounter(
                manager.world,
                enc_data["country"],
                enc_data.get("context"),
                manager.root_path,
                full_transcript=manager.transcript,
                show_metrics=enc_data.get("show_metrics", True),
                required=enc_data.get("required", False),
                narrative_state=manager.narrative_state,
            )
            enc.transcript = list(enc_data.get("transcript", []))
            enc.history = [tuple(pair) for pair in enc_data.get("history", [])]
            enc._player_exchanges = int(enc_data.get("player_exchanges", 0))
            manager.active_encounter = enc

        pending = state.get("pending_pushback")
        if pending:
            manager._pending_pushback = (pending[0], list(pending[1]))

        return manager

    @classmethod
    def load_game(cls, save_path: str) -> 'GameManager':
        """Load game from file."""
        import json

        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    def list_saves(self) -> List[Dict[str, Any]]:
        """List available save files."""
        import json
        save_dir = self.root_path / "saves"
        if not save_dir.exists():
            return []
            
        saves = []
        for f in save_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    meta = data.get("metadata", {})
                    saves.append({
                        "path": str(f),
                        "name": meta.get("save_name", f.stem),
                        "timestamp": meta.get("timestamp"),
                        "turn": data.get("state", {}).get("world", {}).get("turn", 0),
                        "scenario": data.get("config", {}).get("scenario_id")
                    })
            except Exception:
                continue
                
        return sorted(saves, key=lambda x: x["timestamp"] or "", reverse=True)

    # RESOURCES & CONTACTS ---------------------------------------------

    def get_resources(self) -> Dict[str, Any]:
        """Return flattened, well-typed forces and stockpiles."""
        forces = self._flatten_forces(self.initial_conditions.get("uk_forces", {}))
        stockpiles = self._flatten_stockpiles(self.initial_conditions.get("stockpiles", {}))
        return {"forces": forces, "stockpiles": stockpiles}

    def get_diplomatic_contacts(self) -> List[Dict[str, Any]]:
        """Return diplomatic contacts derived from initial conditions."""
        contacts = self.initial_conditions.get("diplomatic_contacts", [])
        flat_contacts: List[Dict[str, Any]] = []
        access_map = {
            3: "leader",
            2: "foreign_minister",
            1: "ambassador",
            0: "restricted"
        }

        for contact in contacts:
            country_code = contact.get("country_code")
            if not country_code:
                continue

            notes = contact.get("notes", [])
            if isinstance(notes, list):
                note_text = " ".join(str(n) for n in notes)
            else:
                note_text = str(notes)

            flat_contacts.append({
                "country_code": country_code,
                "title": contact.get("leader_title") or contact.get("leader_name"),
                "access_level": access_map.get(contact.get("access_level", 0), "restricted"),
                "disposition": contact.get("disposition"),
                "notes": note_text or None
            })

        return flat_contacts

    # HELPERS ----------------------------------------------------------

    def _flatten_forces(self, forces_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert nested UK forces into a list of unit summaries."""
        flattened: List[Dict[str, Any]] = []
        for branch, units in forces_data.items():
            if not isinstance(units, list):
                continue

            for unit in units:
                summary = self._build_force_summary(branch, unit)
                if summary:
                    flattened.append(summary)
        return flattened

    def _build_force_summary(self, branch: str, unit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a consistent summary for a single unit."""
        unit_id = unit.get("id")
        if not unit_id:
            return None

        notes = self._build_unit_notes(unit)

        return {
            "id": unit_id,
            "branch": branch,
            "unit_type": unit.get("type"),
            "location": unit.get("location"),
            "status": unit.get("status"),
            "role": unit.get("role"),
            "readiness_turns": unit.get("turns_to_full_readiness"),
            "notes": notes or unit.get("note")
        }

    def _build_unit_notes(self, unit: Dict[str, Any]) -> Optional[str]:
        """Combine ancillary unit data into a single note string."""
        note_segments: List[str] = []
        mapping = [
            ("embarked", "Embarked"),
            ("armament", "Armament"),
            ("current_assignments", "Assignments"),
            ("aircraft_count", "Aircraft"),
            ("operational_aircraft", "Operational Aircraft"),
            ("max_simultaneous_patrols", "Max Patrols")
        ]

        for field, label in mapping:
            value = unit.get(field)
            segment = self._format_note_segment(label, value)
            if segment:
                note_segments.append(segment)

        additional_note = unit.get("note")
        if additional_note:
            note_segments.append(str(additional_note))

        return " | ".join(note_segments) if note_segments else None

    def _format_note_segment(self, label: Optional[str], value: Any) -> Optional[str]:
        """Render complex values as tidy strings."""
        if value is None:
            return None

        if isinstance(value, list):
                value_str = ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
                value_str = ", ".join(f"{k}: {v}" for k, v in value.items())
        else:
                value_str = str(value)

        if not value_str:
            return None

        return f"{label}: {value_str}" if label else value_str

    def _flatten_stockpiles(self, stockpile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert nested stockpile data into item summaries."""
        items: List[Dict[str, Any]] = []

        for category, entries in stockpile_data.items():
            if not isinstance(entries, dict):
                continue

            for name, values in entries.items():
                count = 0
                note = None

                if isinstance(values, dict):
                    count = values.get("count", 0)
                    note = values.get("note")
                elif isinstance(values, (int, float)):
                    count = values
                else:
                    note = str(values)

                items.append({
                    "category": category,
                    "name": name,
                    "count": count,
                    "note": note
                })

        return items
