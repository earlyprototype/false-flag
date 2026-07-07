"""Game Manager for API/Headless execution.

Manages the state and lifecycle of a single game session without CLI dependencies.
"""

from pathlib import Path
from random import Random
from typing import Optional, List, Dict, Any
import os

from models.world import WorldState, Metrics
from models.narrative_state import NarrativeState, create_initial_narrative_state
from engine.initial_conditions import load_initial_conditions
from engine.scenario_loader import get_scenario_config, get_turn_filename
from engine.sim_loop import run_turn_briefing, run_turn_decision, run_turn_discussion

# Environment flag to disable Rich output in engine modules
os.environ["WARGAME_RICH_UI"] = "false"


class GameManager:
    def __init__(
        self,
        scenario_id: str = "war_game_2025",
        variant: str = "standard",
        difficulty: str = "standard",
        play_mode: str = "immersive",
        seed: int = 42
    ):
        self.scenario_id = scenario_id
        self.variant = variant
        self.difficulty = difficulty
        self.play_mode = play_mode
        self.seed = seed
        self.rng = Random(seed)
        
        self.root_path = Path(__file__).resolve().parents[1]
        self.transcript: List[str] = []
        self.active_encounter = None
        
        # Initialize World
        self._init_world()
        
    def _init_world(self):
        """Initialize world state, actor system, and narrative state."""
        self.initial_conditions = load_initial_conditions(self.scenario_id, self.root_path)
        initial_metrics = self.initial_conditions.get("initial_metrics", {})
        
        self.world = WorldState(
            turn=1,
            scene=1,
            difficulty=self.difficulty,
            narrative=None,  # Default to Original mode for now
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
        stochastic = False # Default for Turn 1
        turn_filename = get_turn_filename(self.world.turn, self.scenario_config)
        
        inject, lines = run_turn_briefing(
            self.world,
            self.scenario_id,
            stochastic,
            self.rng,
            self.root_path,
            self.transcript,
            suppress_display=True,
            silent_effects=True
        )
        
        self.transcript.extend(lines)
        return inject or {}

    def process_question(self, question_text: str) -> List[str]:
        """Process a player question during Discussion phase."""
        self.transcript.append(f"Prime Minister: {question_text}")
        
        discussion_lines = run_turn_discussion(
            self.world, 
            self.scenario_id, 
            [question_text], 
            self.rng, 
            self.root_path,
            self.transcript
        )
        
        self.transcript.extend(discussion_lines)
        return discussion_lines

    # PHASE 1: DECISION LOOP -------------------------------------------

    def interpret_decision(self, action_text: str) -> Dict[str, Any]:
        """Interpret decision and gather advisor feedback without committing."""
        interpretation, pushback, critical_concerns, decision_lines = run_turn_decision(
            self.world,
            self.scenario_id,
            action_text,
            self.rng,
            self.root_path,
            self.transcript,
            dry_run=True  # Don't advance phase or commit to transcript yet
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
        
        # Include pushback in concerns list as well (simpler UI model)
        if pushback:
            for role, concern in pushback:
                concerns_list.append({
                    "role": role,
                    "concern": concern,
                    "recommendation": "Consider revising your approach."
                })

        # Create placeholder data for missing fields
        return {
            "interpretation": interpretation,
            "critical_concerns": concerns_list,
            "raw_transcript": decision_lines,
            "forces_involved": [],  # Placeholder
            "timeline": "Immediate" # Placeholder
        }

    def resolve_decision(self, action_text: str) -> Dict[str, Any]:
        """Commit and resolve a decision (Adjudication phase)."""
        # 1. Final Interpretation (commit to transcript)
        interpretation, _, _, decision_lines = run_turn_decision(
            self.world,
            self.scenario_id,
            action_text,
            self.rng,
            self.root_path,
            self.transcript,
            dry_run=False # Commit phase change
        )
        self.transcript.extend(decision_lines)
        
        # 2. Adjudicate
        final_effects = {}
        character_responses = []
        actor_responses = []
        reasoning = ""
        
        try:
            if self.world.actor_system:
                from engine.narrative_adjudication import adjudicate_with_actor_simulation
                from llm.router import generate_text
                
                final_effects, actor_responses, character_responses, reasoning = adjudicate_with_actor_simulation(
                    self.narrative_state,
                    self.world.actor_system,
                    action_text,
                    interpretation,
                    self.rng,
                    llm_generate_fn=generate_text,
                    world_narrative=self.world.narrative
                )
            else:
                from engine.narrative_adjudication import adjudicate_with_narrative
                from llm.router import generate_text
                
                final_effects, character_responses, reasoning = adjudicate_with_narrative(
                    self.narrative_state,
                    action_text,
                    interpretation,
                    self.rng,
                    llm_generate_fn=generate_text,
                    world_narrative=self.world.narrative
                )
        except Exception as e:
            print(f"Adjudication error: {e}")
        
        # Update Phase & Turn
        self.world.turn += 1
        self.world.phase = "briefing"
        self.world.scene = self.world.turn
        
        return {
            "interpretation": interpretation,
            "reasoning": reasoning,
            "effects": final_effects,
            "advisor_reactions": character_responses,
            "international_reactions": [r.dict() for r in actor_responses] if actor_responses else []
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
                     "category": "adversary" if code == "RUS" else "ally" if code == "US" else "neutral"
                 })
        else:
            actors = [
                {"code": "RUS", "name": "Russia", "category": "adversary"},
                {"code": "US", "name": "United States", "category": "ally"},
                {"code": "CHN", "name": "China", "category": "neutral"}
            ]
        return actors

    def get_intel_detail(self, actor_code: str) -> Dict[str, Any]:
        """Generate detailed intelligence assessment."""
        from engine.intelligence import generate_actor_detailed_assessment
        
        name_map = {"RUS": "Russia", "US": "United States", "CHN": "China"}
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

    def start_diplomacy(self, country_code: str) -> Dict[str, Any]:
        """Start a diplomatic encounter."""
        from engine.diplomacy import DiplomaticEncounter
        
        self.active_encounter = DiplomaticEncounter(
            self.world, 
            country_code, 
            "Player initiated call", 
            self.root_path
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
        
        transcript = self.active_encounter.process_turn(message, generate_text, self.rng)
        outcome = self.active_encounter.outcome
        
        return {
            "transcript": transcript,
            "active": self.active_encounter.active,
            "outcome": outcome
        }

    # SAVE / LOAD SYSTEM -----------------------------------------------

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
        
        data = {
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
                "seed": self.seed
            },
            "state": {
                "world": self.world.dict(),
                "narrative_state": self.narrative_state.dict(),
                "transcript": self.transcript
            }
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            
        return str(save_path)

    @classmethod
    def load_game(cls, save_path: str) -> 'GameManager':
        """Load game from file."""
        import json
        
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        config = data["config"]
        state = data["state"]
        
        # Create instance
        manager = cls(
            scenario_id=config["scenario_id"],
            variant=config.get("variant", "standard"),
            difficulty=config.get("difficulty", "standard"),
            play_mode=config.get("play_mode", "immersive"),
            seed=config["seed"]
        )
        
        # Restore state
        from models.world import WorldState
        
        # Note: WorldState.parse_obj will handle nested ActorSystem if model structure matches
        manager.world = WorldState.parse_obj(state["world"])
        manager.narrative_state = NarrativeState.parse_obj(state["narrative_state"])
        manager.transcript = state["transcript"]
        
        return manager

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
