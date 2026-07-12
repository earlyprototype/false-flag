"""Diplomatic encounter system for international leader/diplomat interactions.

Handles:
- Mandatory diplomatic encounters (inject-driven)
- Optional player-initiated diplomatic calls
- Access level determination (leader vs diplomat)
- Conversation management with LLM-driven counterparts
- Outcome assessment and metric updates
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
from random import Random
import yaml

from models.world import WorldState
from llm.model_config import LLMContext


def load_diplomatic_profiles(root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load diplomatic profiles from YAML.
    
    Args:
        root_path: Optional root path override
    
    Returns:
        Dict containing country profiles and conversation rules
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]
    
    profiles_path = root_path / "data" / "diplomatic_profiles.yaml"
    
    try:
        with open(profiles_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"[ERROR] Diplomatic profiles not found: {profiles_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"[ERROR] Failed to parse diplomatic profiles: {e}")
        return {}


def get_available_countries() -> List[str]:
    """Get list of countries available for diplomatic contact.
    
    Returns:
        List of country codes (US, France, Germany, Poland, Russia, Ukraine, Ireland)
    """
    return ["US", "France", "Germany", "Poland", "Russia", "Ukraine", "Ireland"]


def check_diplomatic_access(
    world: WorldState,
    country: str,
    profiles: Dict[str, Any]
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Check what level of diplomatic access player has to a country.
    
    Args:
        world: Current world state
        country: Country code (e.g., "US", "France")
        profiles: Diplomatic profiles dict
    
    Returns:
        Tuple of (access_level, counterpart_profile) where:
        - access_level: "leader", "diplomat", or None
        - counterpart_profile: Dict with personality, concerns, etc.
    """
    countries = profiles.get("countries", {})
    country_data = countries.get(country)
    
    if not country_data:
        return None, None
    
    # Get alliance cohesion as primary access metric
    cohesion = world.metrics.alliance_cohesion
    
    # Check leader access
    leader_data = country_data.get("leader", {})
    leader_threshold = leader_data.get("access_threshold", 999)
    
    if cohesion >= leader_threshold:
        return "leader", leader_data
    
    # Check diplomat access
    diplomat_data = country_data.get("diplomat", {})
    diplomat_threshold = diplomat_data.get("access_threshold", 999)
    
    if cohesion >= diplomat_threshold:
        return "diplomat", diplomat_data
    
    # No access
    return None, None


def build_diplomatic_conversation_prompt(
    world: WorldState,
    country: str,
    counterpart_profile: Dict[str, Any],
    conversation_history: List[Tuple[str, str]],
    player_message: str,
    full_transcript: Optional[List[str]] = None
) -> str:
    """Build LLM prompt for diplomatic conversation.
    
    Args:
        world: Current world state
        country: Country code
        counterpart_profile: Dict with personality, concerns, etc.
        conversation_history: List of (speaker, message) tuples for this call
        player_message: Player's current message
        full_transcript: Optional full game transcript for context
    
    Returns:
        Formatted prompt for LLM
    """
    from llm.context_builder import get_diplomatic_context
    
    title = counterpart_profile.get("title", "Diplomat")
    personality = counterpart_profile.get("personality", "Professional and diplomatic")
    tone = counterpart_profile.get("tone", "professional")
    key_concerns = counterpart_profile.get("key_concerns", [])
    
    # Use the new context builder for secure, narrative-aware context
    secure_context = ""
    if full_transcript:
        secure_context = get_diplomatic_context(full_transcript, world, country)
    else:
        # Fallback if no transcript available
        secure_context = f"Turn: {world.turn}\nEscalation: {world.metrics.escalation_risk}/100"
    
    # Conversation history for this call
    call_history = ""
    if conversation_history:
        call_history = "\n\n=== CONVERSATION SO FAR ===\n"
        for speaker, message in conversation_history:
            call_history += f"{speaker}: {message}\n"
    
    # Key concerns formatted
    concerns_text = "\n".join(f"- {concern}" for concern in key_concerns)
    
    # Exchange count
    exchange_count = len(conversation_history) + 1
    
    prompt = f"""You are roleplaying as the {title} of {country} in a crisis simulation.

=== YOUR CHARACTER ===
Title: {title}
Personality: {personality}
Tone: {tone}

Key Concerns:
{concerns_text}

{secure_context}

=== THIS DIPLOMATIC CALL ===
{call_history}

UK Prime Minister: {player_message}

=== YOUR TASK ===
Respond in character as the {title}. Stay true to your personality, tone, and concerns.
Act according to your SECRET MOTIVE (if provided above) at all times, but never reveal it directly.

IMPORTANT: This is exchange {exchange_count} of a maximum 11. Try to bring the conversation 
to a natural conclusion within 5-7 exchanges by:
- Summarizing your position and asking for UK commitment
- Offering specific support or making specific requests
- Suggesting follow-up through official channels
- Expressing need to brief your own government/cabinet

Be realistic: you are busy during this crisis and won't engage in endless back-and-forth.

Your response (as {title}):"""
    
    return prompt


def assess_diplomatic_outcome(
    world: WorldState,
    country: str,
    conversation_history: List[Tuple[str, str]],
    llm_generate: Callable[[str, Random], str],
    rng: Random
) -> Tuple[str, int]:
    """Assess the outcome of a diplomatic conversation and determine metric impact.
    
    Args:
        world: Current world state
        country: Country code
        conversation_history: Full conversation history
        llm_generate: LLM text generation function
        rng: Random number generator
    
    Returns:
        Tuple of (assessment_text, alliance_cohesion_delta)
    """
    from llm.prompts import build_world_state_summary
    
    # Build conversation transcript
    conversation_text = "\n".join(
        f"{speaker}: {message}" for speaker, message in conversation_history
    )
    
    world_summary = build_world_state_summary(world)
    
    prompt = f"""You are assessing the outcome of a diplomatic conversation in a crisis simulation.

=== SITUATION ===
{world_summary}

=== DIPLOMATIC CONVERSATION WITH {country} ===
{conversation_text}

=== YOUR TASK ===
Assess the outcome of this conversation based on:
1. Did the UK PM reassure the counterpart about UK intentions?
2. Did the UK PM secure concrete support or commitments?
3. Did the UK PM avoid antagonizing the counterpart?
4. Did the conversation strengthen or weaken the relationship?

Provide your assessment in this format:

OUTCOME: [SUCCESS/NEUTRAL/FAILURE]
ALLIANCE_COHESION_DELTA: [number between -15 and +15]
SUMMARY: [2-3 sentence summary of outcome]

Your assessment:"""
    
    response = llm_generate(prompt, rng, context=LLMContext.DIPLOMACY_OUTCOME)
    
    # Parse response
    outcome = "NEUTRAL"
    delta = 0
    summary = "The conversation concluded."
    
    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("OUTCOME:"):
            outcome = line.replace("OUTCOME:", "").strip()
        elif line.startswith("ALLIANCE_COHESION_DELTA:"):
            try:
                delta_str = line.replace("ALLIANCE_COHESION_DELTA:", "").strip()
                # Extract number (handle +/- prefix)
                delta_str = delta_str.replace("+", "").replace(" ", "")
                delta = int(delta_str)
                delta = max(-15, min(15, delta))  # Clamp to range
            except ValueError:
                delta = 0
        elif line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
    
    # Build assessment text
    assessment = f"Diplomatic Outcome: {outcome}\n{summary}"
    
    return assessment, delta


# --- STATEFUL ENCOUNTER CLASS FOR API ---

class DiplomaticEncounter:
    """Stateful manager for a diplomatic conversation (API friendly)."""
    
    def __init__(self, world: WorldState, country: str, context: Optional[str], root_path: Optional[Path] = None):
        self.world = world
        self.country = country
        self.context = context
        self.root_path = root_path
        
        self.profiles = load_diplomatic_profiles(root_path)
        self.access_level, self.profile = check_diplomatic_access(world, country, self.profiles)
        
        self.title = self.profile.get("title", "Diplomat") if self.profile else "Unknown"
        self.transcript: List[str] = []
        self.history: List[Tuple[str, str]] = []
        self.active = True
        self.outcome: Optional[Dict[str, Any]] = None
        
        if not self.profile:
            self.active = False
            self.transcript.append(f"Connection failed: No access to {country}.")

    def start(self, rng: Random) -> List[str]:
        """Initialize the call and generate opening line."""
        if not self.active:
            return self.transcript
            
        # Generate opening
        opening_lines = self.profile.get("opening_lines", [])
        opening = rng.choice(opening_lines) if opening_lines else "Greetings."
        
        header = f"=== DIPLOMATIC CALL: {self.title} ({self.country}) ==="
        self.transcript.append(header)
        
        msg = f"{self.title}: {opening}"
        self.transcript.append(msg)
        self.history.append((self.title, opening))
        
        return self.transcript

    def process_turn(self, player_message: str, llm_generate: Callable, rng: Random) -> List[str]:
        """Process player input and generate response."""
        if not self.active:
            return self.transcript

        # Player line
        pm_line = f"Prime Minister: {player_message}"
        self.transcript.append(pm_line)
        self.history.append(("Prime Minister", player_message))
        
        # Check for end conditions: only an explicit, standalone closer ends
        # the call. A substring test hung up on lines like "Thank you for the
        # intel, but I need firm Article 5 commitments."
        msg_lower = player_message.strip().lower()
        normalized = "".join(c for c in msg_lower if c.isalpha() or c.isspace()).strip()
        closers = {"end", "goodbye", "thank you", "thank you goodbye", "that will be all", "end call"}
        if msg_lower == "/end" or normalized in closers:
            return self.end(llm_generate, rng)

        # Generate response
        prompt = build_diplomatic_conversation_prompt(
            self.world, self.country, self.profile, self.history, player_message
        )
        response = llm_generate(prompt, rng, context=LLMContext.DIPLOMACY_CONVERSATION)
        response = response.strip()
        
        self.transcript.append(f"{self.title}: {response}")
        self.history.append((self.title, response))
        
        return self.transcript

    def end(self, llm_generate: Callable, rng: Random) -> List[str]:
        """End the encounter and assess outcome."""
        self.active = False
        
        # Assess outcome
        assessment, delta = assess_diplomatic_outcome(
            self.world, self.country, self.history, llm_generate, rng
        )
        
        self.outcome = {
            "assessment": assessment,
            "cohesion_delta": delta
        }
        
        self.transcript.append(f"\n=== CALL ENDED ===\n{assessment}\nAlliance Cohesion: {delta:+d}")
        
        # Update world metric
        self.world.metrics.alliance_cohesion = max(0, min(100, self.world.metrics.alliance_cohesion + delta))
        
        return self.transcript


def run_diplomatic_encounter(
    world: WorldState,
    country: str,
    required: bool,
    context: Optional[str],
    llm_generate: Callable[[str, Random], str],
    rng: Random,
    root_path: Optional[Path] = None,
    full_transcript: Optional[List[str]] = None,
    get_player_input: Optional[Callable[[str], str]] = None,
    print_fn: Optional[Callable[[str], None]] = None
) -> Tuple[List[str], int]:
    """Legacy blocking runner for CLI."""
    encounter = DiplomaticEncounter(world, country, context, root_path)
    
    if not encounter.active:
        return encounter.transcript, 0
    
    # Start
    lines = encounter.start(rng)
    if print_fn:
        for line in lines:
            print_fn(line)
    printed_upto = len(encounter.transcript)

    # Loop
    max_exchanges = encounter.profile.get("conversation_rules", {}).get("max_exchanges", 11)

    for _ in range(max_exchanges):
        if not encounter.active:
            break

        if get_player_input:
            msg = get_player_input("Response: ")
        else:
            msg = "Thank you."

        encounter.process_turn(msg, llm_generate, rng)
        # Print exactly the lines this exchange appended (the previous
        # last-line-twice approach printed every reply twice and never the PM)
        if print_fn:
            for line in encounter.transcript[printed_upto:]:
                print_fn(line)
        printed_upto = len(encounter.transcript)

    if encounter.active:
        encounter.end(llm_generate, rng)

    # Print anything appended after the loop (e.g. the end-of-call assessment
    # when the exchange limit was hit) exactly once
    if print_fn:
        for line in encounter.transcript[printed_upto:]:
            print_fn(line)

    return encounter.transcript, encounter.outcome.get("cohesion_delta", 0) if encounter.outcome else 0


def list_available_diplomatic_contacts(
    world: WorldState,
    root_path: Optional[Path] = None
) -> List[Tuple[str, str, str]]:
    """List available diplomatic contacts and their access levels.
    
    Args:
        world: Current world state
        root_path: Optional root path override
    
    Returns:
        List of (country_code, access_level, title) tuples
    """
    profiles = load_diplomatic_profiles(root_path)
    
    if not profiles:
        return []
    
    available = []
    
    for country in get_available_countries():
        access_level, counterpart_profile = check_diplomatic_access(world, country, profiles)
        
        if access_level and counterpart_profile:
            title = counterpart_profile.get("title", "Diplomat")
            available.append((country, access_level, title))
    
    return available
