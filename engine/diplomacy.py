"""Diplomatic encounter system for international leader/diplomat interactions.

Handles:
- Mandatory diplomatic encounters (inject-driven)
- Optional player-initiated diplomatic calls
- Access level determination (leader vs diplomat)
- Conversation management with LLM-driven counterparts
- Outcome assessment and metric updates
"""

import sys
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
from random import Random
import yaml

from models.world import WorldState
from llm.model_config import LLMContext
from llm.parse_health import record_miss
from llm.parsing import extract_label, find_signed_int, match_enum


# Parsed diplomatic_profiles.yaml, keyed by (path, mtime_ns, size).
#
# This file is 16 KB of YAML and takes ~15 ms to parse on CPython — and every
# push_state() lists the open channels, so a browser turn pays it two or three
# times. That is more than a whole mock-mode turn costs (~30 ms), and mock mode
# is what a player with no API key gets, so it is the dominant cost in the one
# configuration that must feel instant. Under Pyodide it is worse.
#
# Keying on the file's mtime and size rather than the path alone means there is
# no invalidation to get wrong: edit the YAML and the next call reparses it,
# because the key no longer matches. The stat() that costs is microseconds.
_PROFILE_CACHE: Dict[Any, Dict[str, Any]] = {}


def load_diplomatic_profiles(root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load diplomatic profiles from YAML.

    The parsed result is cached per file version (see ``_PROFILE_CACHE``).
    Callers treat it as read-only; nothing in the engine mutates it.

    Args:
        root_path: Optional root path override

    Returns:
        Dict containing country profiles and conversation rules
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parents[1]

    profiles_path = root_path / "data" / "diplomatic_profiles.yaml"

    try:
        st = profiles_path.stat()
        key = (str(profiles_path), st.st_mtime_ns, st.st_size)
        cached = _PROFILE_CACHE.get(key)
        if cached is not None:
            return cached
    except OSError:
        key = None

    try:
        with open(profiles_path, "r", encoding="utf-8") as f:
            profiles = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"[ERROR] Diplomatic profiles not found: {profiles_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"[ERROR] Failed to parse diplomatic profiles: {e}")
        return {}

    if key is not None:
        _PROFILE_CACHE[key] = profiles
    return profiles


def _relationship_reading(title: str, delta: int) -> str:
    """Describe where a call left the relationship, without the number.

    Metric-hiding modes still want the signal a call carries — whether the
    line just opened or just closed — so the delta becomes a reading of the
    room rather than a scoreboard entry.
    """
    if delta >= 8:
        return f"{title} rings off warmer than they came on; something was won here."
    if delta >= 3:
        return f"{title} sounds readier to work with you than before the call."
    if delta > 0:
        return f"{title} gives little away, but the line stays open."
    if delta == 0:
        return f"{title} ends where they began; nothing gained, nothing lost."
    if delta > -5:
        return f"{title} is cooler at the end of the call than at the start."
    return f"{title} rings off hard; that conversation cost you something."


def get_available_countries() -> List[str]:
    """Get list of countries available for diplomatic contact.
    
    Returns:
        List of country codes (US, France, Germany, Poland, Russia, Ukraine,
        Ireland, China)
    """
    return ["US", "France", "Germany", "Poland", "Russia", "Ukraine",
            "Ireland", "China"]


# The switchboard keys off the names in data/diplomatic_profiles.yaml, but
# callers reasonably reach for ISO codes or plain country names. The scenario's
# own diplomatic_contacts list uses ISO-3 ("USA", "DEU"), so a front end that
# offers those as buttons must be able to dial them.
COUNTRY_ALIASES = {
    "US": "US", "USA": "US", "AMERICA": "US", "UNITED STATES": "US",
    "FRA": "France", "FRANCE": "France", "FRENCH": "France",
    "DEU": "Germany", "GER": "Germany", "GERMANY": "Germany", "GERMAN": "Germany",
    "POL": "Poland", "POLAND": "Poland", "POLISH": "Poland",
    "RUS": "Russia", "RUSSIA": "Russia", "RUSSIAN": "Russia", "MOSCOW": "Russia",
    "UKR": "Ukraine", "UKRAINE": "Ukraine", "UKRAINIAN": "Ukraine",
    "IRL": "Ireland", "IRE": "Ireland", "IRELAND": "Ireland", "IRISH": "Ireland",
    "CHN": "China", "CHINA": "China", "CHINESE": "China", "PRC": "China",
    "BEIJING": "China",
}


def normalize_country(name: Optional[str]) -> str:
    """Resolve a country code or name onto a diplomatic-profile key.

    Unknown values are returned title-cased and unchanged in substance, so
    the caller still gets the in-fiction "no such head of state on the
    exchange" refusal rather than a crash.
    """
    if not name:
        return ""
    key = str(name).strip()
    return COUNTRY_ALIASES.get(key.upper(), key.capitalize() if key.islower() else key)


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
    full_transcript: Optional[List[str]] = None,
    encounter_context: Optional[str] = None
) -> str:
    """Build LLM prompt for diplomatic conversation.

    Args:
        world: Current world state
        country: Country code
        counterpart_profile: Dict with personality, concerns, etc.
        conversation_history: List of (speaker, message) tuples for this call,
            NOT including the player's current message (it is rendered
            separately below)
        player_message: Player's current message
        full_transcript: Optional full game transcript for context
        encounter_context: The authored premise of a scripted encounter — why
            the counterpart placed this call (ER-041). None for
            player-initiated calls.

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

    # The scripted premise of the call, when there is one (ER-041)
    premise = ""
    if encounter_context:
        premise = f"\n=== WHY YOU ARE CALLING ===\n{str(encounter_context).strip()}\n"

    # Exchange count. The history gains two entries per exchange (the
    # counterpart's line and the player's), so dividing by two counts
    # exchanges rather than lines (ER-040): the first player message is
    # exchange 1, not exchange 3.
    exchange_count = len(conversation_history) // 2 + 1

    prompt = f"""You are roleplaying as the {title} of {country} in a crisis simulation.

=== YOUR CHARACTER ===
Title: {title}
Personality: {personality}
Tone: {tone}

Key Concerns:
{concerns_text}

{secure_context}
{premise}
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
    outcome = None
    delta = None
    summary = ""
    last_field = None

    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue

        value = extract_label(line, "OUTCOME")
        if value is not None:
            verdict = match_enum(value, ("SUCCESS", "NEUTRAL", "FAILURE"))
            if verdict is not None:
                outcome = verdict
            else:
                record_miss("diplomacy_outcome", "outcome", value)
                outcome = "NEUTRAL"
            last_field = None
            continue

        value = extract_label(line, "ALLIANCE_COHESION_DELTA")
        if value is not None:
            parsed = find_signed_int(value)
            if parsed is not None:
                delta = max(-15, min(15, parsed))  # Clamp to range
            else:
                record_miss("diplomacy_outcome", "delta", value)
                delta = 0
            last_field = None
            continue

        value = extract_label(line, "SUMMARY")
        if value is not None:
            summary = value
            last_field = "summary"
            continue

        # Wrapped continuation of the SUMMARY paragraph
        if last_field == "summary":
            summary = f"{summary} {line}".strip()

    if outcome is None:
        outcome = "NEUTRAL"
        record_miss("diplomacy_outcome", "outcome", "no OUTCOME label found")
    if delta is None:
        delta = 0
        record_miss("diplomacy_outcome", "delta", "no delta label found")
    if not summary:
        summary = "The conversation concluded."
        record_miss("diplomacy_outcome", "summary", "no SUMMARY label found")

    # Build assessment text
    assessment = f"Diplomatic Outcome: {outcome}\n{summary}"
    
    return assessment, delta


# --- STATEFUL ENCOUNTER CLASS FOR API ---

class DiplomaticEncounter:
    """Stateful manager for a diplomatic conversation (API friendly)."""
    
    def __init__(self, world: WorldState, country: str, context: Optional[str], root_path: Optional[Path] = None,
                 full_transcript: Optional[List[str]] = None,
                 show_metrics: bool = True,
                 required: bool = False):
        self.world = world
        self.country = country
        self.context = context
        self.root_path = root_path
        self.show_metrics = show_metrics
        # A mandatory (inject-scripted) encounter: front ends must not let
        # the player walk away from it, and the exchange cap below is what
        # guarantees a headless required call still terminates (ER-033).
        self.required = required
        # Full game transcript feeds get_diplomatic_context (public events plus
        # the secret narrative truth); without it the conversation prompt falls
        # back to a bare turn/escalation stub and Mystery mode never colours
        # foreign leaders' responses.
        self.full_transcript = full_transcript
        
        self.profiles = load_diplomatic_profiles(root_path)
        self.access_level, self.profile = check_diplomatic_access(world, country, self.profiles)
        
        self.title = self.profile.get("title", "Diplomat") if self.profile else "Unknown"
        self.transcript: List[str] = []
        self.history: List[Tuple[str, str]] = []
        self.active = True
        self.outcome: Optional[Dict[str, Any]] = None
        # Same lookup the legacy runner uses; enforced here so every caller
        # gets a call that terminates, not just the blocking CLI loop.
        self.max_exchanges = (self.profile.get("conversation_rules", {})
                              .get("max_exchanges", 11)) if self.profile else 11
        self._player_exchanges = 0
        
        if not self.profile:
            self.active = False
            known_countries = (self.profiles or {}).get("countries", {})
            if country not in known_countries:
                # In-fiction failure: the country simply isn't on the exchange
                self.transcript.append(
                    f"SIGNAL: no secure channel to '{country}' — the Downing Street "
                    "switchboard holds no such head of state on the exchange."
                )
            else:
                self.transcript.append(
                    f"SIGNAL: {country} is not accepting the call — alliance standing "
                    "is too low for a secure channel at this time."
                )

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
        self._player_exchanges += 1

        # Check for end conditions: only an explicit, standalone closer ends
        # the call. A substring test hung up on lines like "Thank you for the
        # intel, but I need firm Article 5 commitments."
        msg_lower = player_message.strip().lower()
        normalized = "".join(c for c in msg_lower if c.isalpha() or c.isspace()).strip()
        closers = {"end", "goodbye", "thank you", "thank you goodbye", "that will be all", "end call"}
        if msg_lower == "/end" or normalized in closers:
            self.history.append(("Prime Minister", player_message))
            return self.end(llm_generate, rng)

        # Generate response. The prompt is built BEFORE the player's line
        # joins the history: it renders that line itself, and the exchange
        # counter divides the history length, so appending first both doubled
        # the line and inflated the count (ER-040).
        prompt = build_diplomatic_conversation_prompt(
            self.world, self.country, self.profile, self.history, player_message,
            full_transcript=self.full_transcript,
            encounter_context=self.context
        )
        self.history.append(("Prime Minister", player_message))
        response = llm_generate(prompt, rng, context=LLMContext.DIPLOMACY_CONVERSATION)
        response = response.strip()

        self.transcript.append(f"{self.title}: {response}")
        self.history.append((self.title, response))

        # Exchange cap: the counterpart is busy running a country. Without
        # this only the legacy CLI runner enforced the limit, so a headless
        # required call could run forever (ER-033).
        if self._player_exchanges >= self.max_exchanges:
            return self.end(llm_generate, rng)

        return self.transcript

    def end(self, llm_generate: Callable, rng: Random,
            show_metrics: Optional[bool] = None) -> List[str]:
        """End the encounter and assess outcome.

        Args:
            show_metrics: Whether the raw alliance-cohesion delta appears in
                the call's closing lines. Immersive and emergent modes hide
                metrics everywhere else, so "Alliance Cohesion: +10" leaked
                the scoreboard those modes exist to remove; they get an
                in-fiction reading of where the call left the relationship
                instead. Defaults to the value the encounter was built with.
                The delta is always recorded in ``outcome`` and always
                applied to world state.
        """
        self.active = False

        # Assess outcome
        assessment, delta = assess_diplomatic_outcome(
            self.world, self.country, self.history, llm_generate, rng
        )

        self.outcome = {
            "assessment": assessment,
            "cohesion_delta": delta
        }

        if show_metrics is None:
            show_metrics = self.show_metrics
        closing = f"\n=== CALL ENDED ===\n{assessment}"
        if show_metrics:
            closing += f"\nAlliance Cohesion: {delta:+d}"
        else:
            closing += f"\n{_relationship_reading(self.title, delta)}"
        self.transcript.append(closing)
        
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
    print_fn: Optional[Callable[[str], None]] = None,
    echo_player: Optional[bool] = None,
    show_metrics: bool = True
) -> Tuple[List[str], int]:
    """Legacy blocking runner for CLI.

    Args:
        echo_player: Whether the player's own lines are printed as part of
            the call. At a live keyboard the terminal has already echoed
            them, so repeating them reads as a glitch; but with piped input
            — recorded sessions, spectator consoles, streamed play — nothing
            echoes them and the transcript shows only one side of the
            conversation. Defaults to echoing exactly when stdin is not a
            TTY.
    """
    if echo_player is None:
        echo_player = not sys.stdin.isatty()
    encounter = DiplomaticEncounter(world, country, context, root_path,
                                    full_transcript=full_transcript,
                                    show_metrics=show_metrics,
                                    required=required)

    if not encounter.active:
        # Surface the in-fiction failure (unknown country / no access) —
        # returning silently left the player staring at a dead prompt.
        if print_fn:
            for line in encounter.transcript:
                print_fn(line)
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
            # Bare label: CLI prompt wrappers add their own ": " suffix
            # (passing "Response: " rendered a doubled "Response: : ")
            msg = get_player_input("Response")
        else:
            msg = "Thank you."

        encounter.process_turn(msg, llm_generate, rng)
        # Print exactly the lines this exchange appended (the previous
        # last-line-twice approach printed every reply twice and never the PM).
        if print_fn:
            for line in encounter.transcript[printed_upto:]:
                if line.startswith("Prime Minister:") and not echo_player:
                    continue
                print_fn(line)
        printed_upto = len(encounter.transcript)

    if encounter.active:
        encounter.end(llm_generate, rng, show_metrics=show_metrics)

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
