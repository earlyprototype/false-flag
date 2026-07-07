from typing import List, Dict
from random import Random
import re

from models.state_actors import StateActor, ActorResponse, StateActorSystem

def simulate_actor_response(
    actor: StateActor,
    player_action: str,
    world_context: str,
    llm_generate_fn,
    rng: Random
) -> ActorResponse:
    """
    Use LLM to simulate how this specific actor responds.
    
    The LLM is given the actor's HIDDEN STATE (motivations, agendas, dependencies)
    and asked to roleplay their response realistically.
    """
    
    # Build prompt with actor's secret knowledge
    prompt = f"""
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
    
    try:
        response_text = llm_generate_fn(prompt, rng)
        return _parse_actor_response(actor.country_code, response_text)
    
    except Exception:
        # Fallback to heuristic response
        return _heuristic_actor_response(actor, player_action)


def _parse_actor_response(actor_id: str, response_text: str) -> ActorResponse:
    """Parse LLM response into structured ActorResponse (Robust Version)."""
    lines = response_text.strip().split('\n')
    
    public_response = ""
    private_assessment = ""
    trust_change = 0
    will_support = "conditional"
    conditions = []
    intel_shared = None
    
    # Regex patterns for robust extraction
    trust_pattern = re.compile(r"TRUST_CHANGE:\s*([+-]?\d+)")
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("PUBLIC_RESPONSE:"):
            public_response = line.split(":", 1)[1].strip()
        
        elif line.startswith("PRIVATE_ASSESSMENT:"):
            private_assessment = line.split(":", 1)[1].strip()
        
        elif line.startswith("TRUST_CHANGE:"):
            match = trust_pattern.search(line)
            if match:
                try:
                    val = int(match.group(1))
                    trust_change = max(-20, min(20, val))
                except ValueError:
                    trust_change = 0
        
        elif line.startswith("WILL_SUPPORT:"):
            content = line.split(":", 1)[1].strip().lower()
            if "yes" in content:
                will_support = "yes"
            elif "no" in content and "not" not in content: # Avoid "not conditional" false positives if phrasing implies it
                will_support = "no"
            elif "conditional" in content:
                will_support = "conditional"
            # Default to conditional if ambiguous
        
        elif line.startswith("CONDITIONS:"):
            try:
                cond_text = line.split(":", 1)[1].strip()
                if cond_text and cond_text.lower() != "none":
                    # Split by semicolons or commas if they look like list items
                    conditions = [c.strip() for c in re.split(r'[;,]', cond_text) if c.strip()]
            except:
                pass
        
        elif line.startswith("INTEL_SHARED:"):
            try:
                intel_text = line.split(":", 1)[1].strip()
                if intel_text and intel_text.lower() != "none":
                    intel_shared = intel_text
            except:
                pass
    
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
    
    # Deduplicate
    relevant = list(set(relevant))
    
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
