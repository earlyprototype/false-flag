from typing import List, Dict
from random import Random
import re

from models.state_actors import StateActor, ActorResponse, StateActorSystem
from llm.model_config import LLMContext
from llm.parse_health import record_miss
from llm.parsing import extract_label, find_signed_int, match_enum

# ISO country codes -> short display names for player-facing summaries.
# (StateActor.full_name holds the formal name, e.g. "Republic of Poland";
# these are the compact forms used in dense panels.)
COUNTRY_DISPLAY_NAMES = {
    "USA": "United States",
    "FRA": "France",
    "DEU": "Germany",
    "POL": "Poland",
    "RUS": "Russia",
}


def display_country_name(country_code: str) -> str:
    """Return a player-friendly name for an actor country code."""
    return COUNTRY_DISPLAY_NAMES.get(country_code, country_code)


def build_actor_prompt(actor: StateActor, player_action: str,
                      world_context: str, world_narrative=None) -> str:
    """Build one actor's roleplay prompt (no call - see simulate_actor_responses).

    The prompt carries the actor's HIDDEN STATE - motivations, agendas,
    dependencies - which is what makes the response something other than a
    press release.

    ``world_narrative`` is the Mystery-mode NarrativeConfig, if any. It is
    rendered per actor so each capital gets its OWN authored stance (secret
    motive, public posture, leverage) rather than a shared global block
    (ER-012). Actor country codes are already ISO-3.
    """
    narrative_block = ""
    if world_narrative is not None:
        narrative_block = "\n" + world_narrative.to_llm_context(
            actor.country_code, audience="roleplay") + "\n"
    return f"""
You are simulating {actor.full_name}'s response to a UK government action.

=== ACTOR IDENTITY ===
Country: {actor.full_name} ({actor.country_code})
Official Position: {actor.official_position}
Relationship with UK: {actor.relationship_uk}/100

=== HIDDEN STATE (guides your response, UK does not know this) ===
True Motivations: {', '.join(actor.true_motivations)}
Hidden Agendas: {', '.join(actor.hidden_agendas) if actor.hidden_agendas else 'None'}
Threat Perception: {actor.threat_perception}/100
Domestic Pressure: {actor.domestic_pressure}/100
Dependencies: {actor.dependencies}
Redlines: {', '.join(actor.redlines) if actor.redlines else 'None'}

Strategic Capabilities:
- Military: {actor.military_capability}/100
- Economic: {actor.economic_leverage}/100
- Diplomatic: {actor.diplomatic_influence}/100
- Intelligence Sharing: {actor.intelligence_sharing}

=== WORLD CONTEXT ===
{world_context}
{narrative_block}
=== UK ACTION ===
{player_action}

=== TASK ===
Respond as {actor.full_name} would REALISTICALLY respond given:
1. Your true motivations (not just public position)
2. Your hidden agendas
3. Your actual threat perception
4. Your domestic/economic constraints
5. Your dependencies and vulnerabilities

Respond in this EXACT format:

PUBLIC_RESPONSE: [What you say publicly/diplomatically to UK]

PRIVATE_ASSESSMENT: [What you actually think internally]

TRUST_CHANGE: [number from -20 to +20, how this action affects your view of UK]

WILL_SUPPORT: [yes/no/conditional]

CONDITIONS: [If conditional, what specific conditions must UK meet? Leave empty if yes/no]

INTEL_SHARED: [Any intelligence you choose to share, or "none"]

Be realistic. If you have hidden agendas, let them guide your response.
If you have dependencies (e.g., Russian gas), they constrain your actions.
If you have redlines, enforce them.
"""


def simulate_actor_response(
    actor: StateActor,
    player_action: str,
    world_context: str,
    llm_generate_fn,
    rng: Random
) -> ActorResponse:
    """Simulate one actor's response. Kept for callers that ask for a single
    country; the turn loop goes through simulate_actor_responses instead."""
    prompt = build_actor_prompt(actor, player_action, world_context)
    try:
        response_text = llm_generate_fn(prompt, rng)
        return _parse_actor_response(actor.country_code, response_text)
    except Exception:
        # Fallback to heuristic response
        return _heuristic_actor_response(actor, player_action)


def simulate_actor_responses(
    actors: list,
    player_action: str,
    world_context: str,
    llm_generate_fn,
    rng: Random,
    llm_batch_fn=None,
    world_narrative=None,
) -> list:
    """Simulate several actors' responses to the same UK action.

    Capitals do not consult each other before replying, and the game does not
    show them each other's answers, so there is nothing sequential about this
    group beyond the fact that it used to be written as a loop.

    An actor whose call comes back empty or as a driver error string falls
    back to the same heuristic response the single-call path used, rather
    than reaching the parser as a blank.
    """
    from llm.fanout import generate_group

    if not actors:
        return []

    prompts = [build_actor_prompt(actor, player_action, world_context,
                                  world_narrative=world_narrative)
               for actor in actors]
    raw = generate_group(prompts, llm_generate_fn, rng, llm_batch_fn,
                         context=LLMContext.ACTOR_SIMULATION)

    responses = []
    for actor, text in zip(actors, raw):
        if not text or text.startswith("[ERROR:"):
            responses.append(_heuristic_actor_response(actor, player_action))
            continue
        try:
            responses.append(_parse_actor_response(actor.country_code, text))
        except Exception:
            responses.append(_heuristic_actor_response(actor, player_action))
    return responses


def _parse_actor_response(actor_id: str, response_text: str) -> ActorResponse:
    """Parse LLM response into structured ActorResponse (Robust Version)."""
    lines = response_text.strip().split('\n')

    public_response = ""
    private_assessment = ""
    trust_change = 0
    will_support = None
    conditions = []
    intel_shared = None
    any_label = False
    will_support_seen = False

    for line in lines:
        line = line.strip()

        value = extract_label(line, "PUBLIC_RESPONSE")
        if value is not None:
            public_response = value
            any_label = True
            continue

        value = extract_label(line, "PRIVATE_ASSESSMENT")
        if value is not None:
            private_assessment = value
            any_label = True
            continue

        value = extract_label(line, "TRUST_CHANGE")
        if value is not None:
            any_label = True
            parsed = find_signed_int(value)
            if parsed is not None:
                trust_change = max(-20, min(20, parsed))
            else:
                record_miss("actor_simulation", "trust_change", actor_id)
            continue

        value = extract_label(line, "WILL_SUPPORT")
        if value is not None:
            any_label = True
            will_support_seen = True
            # Exact enum first; then a worded refusal ("absolutely not",
            # "no, we will not assist") with no unnegated yes reads as no;
            # then unnegated yes; then the conditional token.
            verdict = match_enum(value, ("yes", "no", "conditional"),
                                 refusal_value="no")
            if verdict is not None:
                will_support = verdict
            else:
                record_miss("actor_simulation", "will_support", actor_id)
            continue

        value = extract_label(line, "CONDITIONS")
        if value is not None:
            any_label = True
            if value and value.lower() != "none":
                # Split by semicolons or commas if they look like list items
                conditions = [c.strip() for c in re.split(r'[;,]', value) if c.strip()]
            continue

        value = extract_label(line, "INTEL_SHARED")
        if value is not None:
            any_label = True
            if value and value.lower() != "none":
                intel_shared = value
            continue

    if not any_label:
        record_miss("actor_simulation", "all_fields", actor_id)
    elif not will_support_seen and will_support is None:
        record_miss("actor_simulation", "will_support", actor_id)
    if will_support is None:
        will_support = "conditional"

    return ActorResponse(
        actor_id=actor_id,
        public_response=public_response or f"{actor_id} acknowledges the action.",
        private_assessment=private_assessment or "Assessing situation.",
        trust_change=trust_change,
        will_support=will_support,
        conditions=conditions,
        intel_shared=intel_shared
    )

def _heuristic_actor_response(actor: StateActor, player_action: str) -> ActorResponse:
    """Fallback heuristic response if LLM fails."""
    return ActorResponse(
        actor_id=actor.country_code,
        public_response="We are reviewing this development.",
        private_assessment="Uncertainty prevents clear commitment.",
        trust_change=0,
        will_support="conditional",
        conditions=["Need more information"],
        intel_shared=None
    )

def identify_relevant_actors(action: str, actor_system: StateActorSystem, max_actors: int = 3) -> List[str]:
    """
    Determine which actors should respond to this action.
    
    Relevance based on:
    - Action keywords (NATO → all NATO members relevant)
    - Actor threat perception (high threat → more reactive)
    - Recent interaction (contacted recently → more likely to respond)
    """
    relevant = []
    action_lower = action.lower()
    
    # Always relevant: Core allies
    always_relevant = ["USA", "FRA", "DEU", "POL"]
    
    # NATO actions → all NATO members
    if any(word in action_lower for word in ["nato", "article 5", "alliance"]):
        relevant.extend(always_relevant)
    
    # Diplomatic actions → mentioned countries + close allies
    elif any(word in action_lower for word in ["diplomatic", "call", "contact"]):
        # Add explicitly mentioned countries
        for code, actor in actor_system.actors.items():
            if code.lower() in action_lower or actor.full_name.lower() in action_lower:
                relevant.append(code)
        
        # Add close allies if none mentioned
        if not relevant:
            relevant = ["USA", "POL"]  # Default to closest allies
    
    # Military actions → threatened actors respond
    elif any(word in action_lower for word in ["deploy", "military", "forces"]):
        for code, actor in actor_system.actors.items():
            if actor.threat_perception > 70:
                relevant.append(code)
    
    # Default: Top 2-3 most relevant actors
    if not relevant:
        relevant = ["USA", "FRA", "POL"]  # Default key actors
    
    # Deduplicate, preserving order. list(set(...)) varies with PYTHONHASHSEED,
    # so the international responses came back in a different order on every
    # process - including replays of the same seed, and including the tie-break
    # in the relationship sort below.
    relevant = list(dict.fromkeys(relevant))
    
    # Limit to max_actors, prioritize by relationship_uk
    if len(relevant) > max_actors:
        relevant = sorted(relevant, key=lambda c: actor_system.actors[c].relationship_uk, reverse=True)[:max_actors]
    
    return relevant


def calculate_effects_from_responses(
    responses: List[ActorResponse],
    actor_system: StateActorSystem
) -> Dict[str, int]:
    """
    Derive actual metric effects from actor responses.
    
    Instead of abstract "alliance_cohesion +5", calculate based on:
    - How many actors support (yes)
    - How many undermine (no, or low trust_change)
    - How many are conditional
    """
    effects = {
        "alliance_cohesion": 0,
        "escalation_risk": 0,
        "domestic_stability": 0
    }
    
    strong_support = 0.0
    undermining = 0.0
    conditional = 0.0
    
    for response in responses:
        actor = actor_system.actors.get(response.actor_id)
        if not actor:
            continue
        
        # Weight by actor's diplomatic influence
        weight = actor.diplomatic_influence / 50.0  # Normalize to 0-2 range
        
        if response.will_support == "yes":
            strong_support += weight
            effects["alliance_cohesion"] += int(5 * weight)
        
        elif response.will_support == "no":
            undermining += weight
            effects["alliance_cohesion"] -= int(8 * weight)
            effects["escalation_risk"] += int(3 * weight)  # Opposition signals weakness
        
        elif response.will_support == "conditional":
            conditional += weight
            effects["alliance_cohesion"] += int(2 * weight)  # Slight positive, but hesitant
        
        # Trust changes affect domestic stability (shows leadership quality)
        if response.trust_change > 5:
            effects["domestic_stability"] += 2
        elif response.trust_change < -5:
            effects["domestic_stability"] -= 3
    
    # Bonus/penalty based on overall consensus
    if strong_support >= 2 and undermining == 0:
        # Strong unified support
        effects["alliance_cohesion"] += 5
        effects["escalation_risk"] -= 5
    
    elif undermining >= 1 and strong_support < 2:
        # Divided alliance
        effects["alliance_cohesion"] -= 5
        effects["escalation_risk"] += 5
    
    return effects
