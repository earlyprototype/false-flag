"""
Narrative-Driven Adjudication System
=====================================

Uses hidden metrics to guide LLM character responses whilst
presenting narrative consequences to player.
"""

from typing import Dict, List, Tuple, Any
from random import Random

from models.narrative_state import NarrativeState
from engine.utils import clamp

# Actor Simulation Imports
from models.state_actors import StateActorSystem, ActorResponse
from engine.actor_simulation import (
    simulate_actor_response,
    calculate_effects_from_responses,
    identify_relevant_actors
)


# === QUALITY ASSESSMENT ===

def assess_action_quality(
    action: str,
    narrative_state: NarrativeState,
    interpretation: str,
    llm_generate_fn = None,
    world_narrative = None
) -> Dict[str, Any]:
    """
    Use LLM to assess quality and appropriateness of player action.
    
    Args:
        action: Player's raw action text
        narrative_state: Current narrative state with hidden metrics
        interpretation: LLM's interpretation of the action
        llm_generate_fn: LLM generation function (optional, falls back to heuristic)
        world_narrative: Optional NarrativeConfig for secret truth context
    
    Returns:
        Assessment dict with:
        - quality: "exceptional" | "good" | "adequate" | "poor" | "catastrophic"
        - reasoning: Why this assessment
        - suggested_effects: Dict of metric impacts
    """
    
    if llm_generate_fn is None:
        # Fallback to heuristic assessment
        return _heuristic_quality_assessment(action, narrative_state)
    
    # Build LLM prompt for quality assessment
    context = narrative_state.to_llm_context()
    
    # Add secret narrative truth if available
    narrative_context = ""
    if world_narrative:
        narrative_context = "\n" + world_narrative.to_llm_context() + "\n"
    
    prompt = f"""
{context}
{narrative_context}
PLAYER ACTION: {action}

INTERPRETATION: {interpretation}

ASSESS THIS ACTION:

Consider:
1. Is this the right action at the right time given the situation?
2. Does it address the most critical issues?
3. Is it proportionate to the threat level?
4. Will it strengthen or weaken the UK's position?
5. Are there obvious negative consequences being overlooked?
6. If a secret narrative is present, does the action play into or against the hidden truth?

Respond in this exact format:

QUALITY: [exceptional/good/adequate/poor/catastrophic]

REASONING: [One paragraph explaining the assessment]

EFFECTS:
escalation_risk: [delta -20 to +20]
alliance_cohesion: [delta -20 to +20]
domestic_stability: [delta -20 to +20]

QUALITY MULTIPLIER: [0.5 to 2.5]
"""
    
    try:
        response = llm_generate_fn(prompt, max_tokens=400)
        return _parse_quality_response(response)
    except Exception:
        # Fallback to heuristic on error
        return _heuristic_quality_assessment(action, narrative_state)


def _heuristic_quality_assessment(action: str, narrative_state: NarrativeState) -> Dict[str, Any]:
    """Fallback heuristic quality assessment"""
    action_lower = action.lower()
    
    # Default: adequate quality
    quality = "adequate"
    multiplier = 1.0
    reasoning = "Standard response to the crisis."
    effects = {}
    
    # Diplomatic actions
    if any(word in action_lower for word in ["diplomatic", "nato", "alliance", "allies", "consult"]):
        effects["alliance_cohesion"] = 5
        quality = "good"
        multiplier = 1.5
        reasoning = "Diplomatic engagement strengthening alliance ties."
    
    # De-escalation
    if any(word in action_lower for word in ["de-escalate", "restraint", "defensive", "caution", "investigate", "evidence"]):
        effects["escalation_risk"] = -5
        quality = "good"
        multiplier = 1.5
        reasoning = "Measured approach showing restraint and good judgment."
    
    # Public messaging
    if any(word in action_lower for word in ["public", "statement", "reassure", "address nation"]):
        effects["domestic_stability"] = 3
    
    # Military deployment
    if any(word in action_lower for word in ["deploy", "surge", "mobilize", "forces"]):
        effects["escalation_risk"] = 5
        if narrative_state.hidden_metrics.escalation_risk > 70:
            quality = "poor"
            multiplier = 0.5
            reasoning = "Escalatory military moves when tensions are already critical."
    
    # Passive response
    if any(word in action_lower for word in ["ignore", "wait", "nothing", "delay"]):
        effects["domestic_stability"] = -5
        effects["alliance_cohesion"] = -3
        quality = "poor"
        multiplier = 0.5
        reasoning = "Passive response when decisive action is needed."
    
    # Catastrophic actions
    if any(word in action_lower for word in ["nuclear", "pre-emptive strike", "attack", "bomb"]):
        effects["escalation_risk"] = 20
        effects["alliance_cohesion"] = -30
        effects["domestic_stability"] = -10
        if narrative_state.hidden_metrics.escalation_risk > 60:
            quality = "catastrophic"
            multiplier = -0.5
            reasoning = "Aggressive escalation at the worst possible time - risks nuclear war."
    
    # Default baseline if no specific action detected
    if not effects:
        effects = {
            "escalation_risk": 2,
            "domestic_stability": -1
        }
    
    return {
        "quality": quality,
        "multiplier": multiplier,
        "reasoning": reasoning,
        "suggested_effects": effects
    }


def _parse_quality_response(response: str) -> Dict[str, Any]:
    """Parse LLM quality assessment response"""
    lines = response.strip().split("\n")
    
    quality = "adequate"
    reasoning = ""
    effects = {}
    multiplier = 1.0
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("QUALITY:"):
            quality_str = line.split(":", 1)[1].strip().lower()
            if quality_str in ["exceptional", "good", "adequate", "poor", "catastrophic"]:
                quality = quality_str
        
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        
        elif ":" in line and any(metric in line.lower() for metric in ["escalation", "alliance", "stability"]):
            parts = line.split(":")
            metric = parts[0].strip().lower().replace(" ", "_").replace("-", "_")
            try:
                value = int(parts[1].strip())
                effects[metric] = value
            except:
                pass
        
        elif line.startswith("QUALITY MULTIPLIER:"):
            try:
                multiplier = float(line.split(":", 1)[1].strip())
                multiplier = max(0.5, min(2.5, multiplier))
            except:
                pass
    
    # Map quality to multiplier if not explicitly provided
    if multiplier == 1.0:
        quality_multipliers = {
            "exceptional": 2.5,
            "good": 1.5,
            "adequate": 1.0,
            "poor": 0.5,
            "catastrophic": -0.5
        }
        multiplier = quality_multipliers.get(quality, 1.0)
    
    return {
        "quality": quality,
        "multiplier": multiplier,
        "reasoning": reasoning or "Action assessed.",
        "suggested_effects": effects
    }


# === EFFECT DETERMINATION ===

def determine_base_effects(action: str, narrative_state: NarrativeState) -> Dict[str, int]:
    """
    Determine base metric effects using heuristics.
    Similar to current system but returns dict instead of applying directly.
    """
    effects = {}
    action_lower = action.lower()
    
    # Diplomatic actions
    if any(word in action_lower for word in ["diplomatic", "nato", "alliance", "allies", "consult"]):
        effects["alliance_cohesion"] = 5
    
    # Public messaging
    if any(word in action_lower for word in ["public", "statement", "reassure", "address nation"]):
        effects["domestic_stability"] = 3
    
    # Military deployment
    if any(word in action_lower for word in ["deploy", "surge", "mobilize", "forces"]):
        effects["escalation_risk"] = 5
    
    # De-escalation
    if any(word in action_lower for word in ["de-escalate", "restraint", "defensive", "caution"]):
        effects["escalation_risk"] = -5
    
    # Investigation/evidence gathering
    if any(word in action_lower for word in ["investigate", "evidence", "verify", "intelligence"]):
        effects["escalation_risk"] = -3
        effects["alliance_cohesion"] = 3  # Shows responsible approach
    
    # Aggressive actions
    if any(word in action_lower for word in ["nuclear", "strike", "attack", "offensive"]):
        effects["escalation_risk"] = 20
        effects["alliance_cohesion"] = -30
        effects["domestic_stability"] = -10
    
    return effects


def apply_quality_scaling(
    base_effects: Dict[str, int],
    quality_assessment: Dict[str, Any],
    narrative_state: NarrativeState
) -> Dict[str, int]:
    """
    Scale base effects by quality multiplier and add contextual modifiers.
    
    Args:
        base_effects: Base heuristic effects
        quality_assessment: LLM quality assessment with multiplier
        narrative_state: Current state for context
    
    Returns:
        Final scaled effects
    """
    multiplier = quality_assessment["multiplier"]
    suggested = quality_assessment.get("suggested_effects", {})
    
    final_effects = {}
    
    # Scale base effects by quality
    for metric, delta in base_effects.items():
        scaled = int(delta * multiplier)
        # Clamp to reasonable bounds
        scaled = max(-20, min(20, scaled))
        final_effects[metric] = scaled
    
    # Add LLM-suggested effects (if any)
    for metric, delta in suggested.items():
        if metric in final_effects:
            # Average with base effect
            final_effects[metric] = (final_effects[metric] + delta) // 2
        else:
            final_effects[metric] = delta
    
    # Context modifiers based on current state
    m = narrative_state.hidden_metrics
    
    # Diplomatic actions less effective if alliance already strong
    if "alliance_cohesion" in final_effects and final_effects["alliance_cohesion"] > 0:
        if m.alliance_cohesion > 70:
            final_effects["alliance_cohesion"] = final_effects["alliance_cohesion"] // 2
    
    # Public reassurance less effective if crisis severe
    if "domestic_stability" in final_effects and final_effects["domestic_stability"] > 0:
        if m.escalation_risk > 80:
            final_effects["domestic_stability"] = final_effects["domestic_stability"] // 2
    
    return final_effects


# === CHARACTER RESPONSE GENERATION ===

def generate_character_responses(
    action: str,
    quality_assessment: Dict[str, Any],
    final_effects: Dict[str, int],
    narrative_state: NarrativeState,
    llm_generate_fn = None
) -> List[Tuple[str, str]]:
    """
    Generate character responses guided by metrics and quality.
    
    Args:
        action: Player action
        quality_assessment: Quality assessment dict
        final_effects: Final metric effects about to be applied
        narrative_state: Current narrative state
        llm_generate_fn: Optional LLM function
    
    Returns:
        List of (character_name, response_text) tuples
    """
    responses = []
    
    if llm_generate_fn is None:
        # Fallback to templated responses
        return _generate_templated_responses(action, quality_assessment, narrative_state)
    
    # Select key characters to respond
    key_characters = _select_responding_characters(narrative_state, final_effects)
    
    for char_id in key_characters:
        if char_id not in narrative_state.characters:
            continue
        
        char = narrative_state.characters[char_id]
        
        response_text = _generate_character_response_llm(
            character=char,
            action=action,
            quality=quality_assessment["quality"],
            effects=final_effects,
            narrative_state=narrative_state,
            llm_generate_fn=llm_generate_fn
        )
        
        responses.append((char.name, response_text))
    
    return responses


def _select_responding_characters(
    narrative_state: NarrativeState,
    effects: Dict[str, int]
) -> List[str]:
    """Select which characters should respond based on action effects"""
    responders = []
    
    # Always: NSA provides assessment
    responders.append("uk_nsa")
    
    # If alliance affected: Foreign Secretary
    if "alliance_cohesion" in effects and abs(effects["alliance_cohesion"]) > 5:
        responders.append("uk_foreign_sec")
    
    # If domestic affected: Home Secretary
    if "domestic_stability" in effects and abs(effects["domestic_stability"]) > 5:
        responders.append("uk_home_sec")
    
    # If military action: CDS
    if "escalation_risk" in effects and effects["escalation_risk"] > 5:
        responders.append("uk_cds")
    
    # Limit to 3-4 characters for readability
    return responders[:4]


def _generate_character_response_llm(
    character,
    action: str,
    quality: str,
    effects: Dict[str, int],
    narrative_state: NarrativeState,
    llm_generate_fn
) -> str:
    """Generate single character response using LLM"""
    
    context = narrative_state.to_llm_context()
    
    # Build tone guidance based on quality
    tone_guidance = {
        "exceptional": "impressed and supportive",
        "good": "approving but professional",
        "adequate": "neutral, professional acknowledgment",
        "poor": "concerned and skeptical",
        "catastrophic": "alarmed and strongly opposed"
    }
    tone = tone_guidance.get(quality, "neutral")
    
    prompt = f"""
{context}

PLAYER ACTION: {action}
ACTION QUALITY: {quality}

You are {character.name}.
Your relationship with the PM: {character.relationship.upper()} (trust: {character.trust}/100)
Your current stance: {character.stance_summary}

Respond to the PM's action with a tone that is {tone}.

Keep your response to 2-3 sentences, in character, as if speaking directly to the Prime Minister in a COBRA briefing.

Response:"""
    
    try:
        response = llm_generate_fn(prompt, max_tokens=150)
        # Clean up response
        response = response.strip().strip('"')
        return response
    except Exception:
        return f"[{character.name}] Understood, Prime Minister."


def _generate_templated_responses(
    action: str,
    quality_assessment: Dict[str, Any],
    narrative_state: NarrativeState
) -> List[Tuple[str, str]]:
    """Fallback templated responses"""
    responses = []
    quality = quality_assessment["quality"]
    
    # NSA always responds
    nsa_responses = {
        "exceptional": "Prime Minister, that's an excellent decision. Exactly the right approach.",
        "good": "A sound decision, Prime Minister. This should strengthen our position.",
        "adequate": "Understood, Prime Minister. We'll proceed accordingly.",
        "poor": "Prime Minister, I have concerns about this approach. We may want to reconsider.",
        "catastrophic": "Prime Minister, I must strongly advise against this course of action."
    }
    responses.append(("National Security Advisor", nsa_responses.get(quality, nsa_responses["adequate"])))
    
    return responses


# === MAIN ADJUDICATION FUNCTIONS ===

def adjudicate_with_narrative(
    narrative_state: NarrativeState,
    action: str,
    interpretation: str,
    rng: Random,
    llm_generate_fn = None,
    world_narrative = None
) -> Tuple[Dict[str, int], List[Tuple[str, str]], str]:
    """
    Complete narrative-driven adjudication pipeline.
    
    Args:
        narrative_state: Current narrative state (modified in place)
        action: Player action text
        interpretation: LLM interpretation
        rng: Random number generator
        llm_generate_fn: Optional LLM function
        world_narrative: Optional NarrativeConfig for secret truth context
    
    Returns:
        (final_effects, character_responses, quality_reasoning)
    """
    
    # 1. Assess action quality and get LLM-suggested effects
    quality_assessment = assess_action_quality(
        action, narrative_state, interpretation, llm_generate_fn, world_narrative
    )
    
    # 2. Use LLM's suggested effects directly (with quality scaling already applied)
    final_effects = apply_quality_scaling(
        quality_assessment["suggested_effects"], quality_assessment, narrative_state
    )
    
    # 3. Apply effects to hidden metrics
    for metric, delta in final_effects.items():
        if hasattr(narrative_state.hidden_metrics, metric):
            current = getattr(narrative_state.hidden_metrics, metric)
            updated = clamp(current + delta)
            setattr(narrative_state.hidden_metrics, metric, updated)
    
    # 4. Generate character responses
    character_responses = generate_character_responses(
        action, quality_assessment, final_effects, narrative_state, llm_generate_fn
    )
    
    # 5. Update character attitudes based on action quality
    _update_character_attitudes(narrative_state, quality_assessment["quality"])
    
    # 6. Check for crisis triggers
    _check_and_trigger_crises(narrative_state)
    
    return final_effects, character_responses, quality_assessment["reasoning"]


def adjudicate_with_actor_simulation(
    narrative_state: NarrativeState,
    actor_system: StateActorSystem,
    action: str,
    interpretation: str,
    rng: Random,
    llm_generate_fn,
    world_narrative = None
) -> Tuple[Dict[str, int], List[ActorResponse], List[Tuple[str, str]], str]:
    """
    Enhanced adjudication with multi-agent actor simulation.
    
    Pipeline:
    1. Identify relevant actors
    2. Simulate each actor's response
    3. Calculate effects from responses
    4. Apply to metrics
    5. Update actor relationships
    6. Generate character (advisor) responses
    7. Generate narrative summary
    """
    
    # 1. Identify which actors should respond
    relevant_actor_ids = identify_relevant_actors(action, actor_system, max_actors=3)
    
    # 2. Simulate each actor's response
    actor_responses = []
    world_context = narrative_state.to_llm_context()
    
    if world_narrative:
        world_context += "\n\nSECRET NARRATIVE TRUTH:\n" + world_narrative.to_llm_context()
    
    for actor_id in relevant_actor_ids:
        actor = actor_system.get_actor(actor_id)
        if not actor:
            continue
        
        response = simulate_actor_response(
            actor, action, world_context, llm_generate_fn, rng
        )
        actor_responses.append(response)
        
        # Update actor's relationship with UK
        actor_system.update_actor_relationship(actor_id, response.trust_change)
    
    # 3. Calculate effects from responses
    actor_effects = calculate_effects_from_responses(actor_responses, actor_system)
    
    # 4. Also run quality assessment for player skill
    quality_assessment = assess_action_quality(action, narrative_state, interpretation, llm_generate_fn, world_narrative)
    base_effects = determine_base_effects(action, narrative_state)
    quality_effects = apply_quality_scaling(base_effects, quality_assessment, narrative_state)
    
    # 5. Merge actor effects with quality effects (average)
    final_effects = {}
    all_metrics = set(actor_effects.keys()) | set(quality_effects.keys())
    
    for metric in all_metrics:
        actor_val = actor_effects.get(metric, 0)
        quality_val = quality_effects.get(metric, 0)
        # Weight: 60% actor responses, 40% quality assessment
        final_effects[metric] = int(actor_val * 0.6 + quality_val * 0.4)
    
    # 6. Apply to narrative state
    for metric, delta in final_effects.items():
        if hasattr(narrative_state.hidden_metrics, metric):
            current = getattr(narrative_state.hidden_metrics, metric)
            updated = clamp(current + delta)
            setattr(narrative_state.hidden_metrics, metric, updated)
    
    # 7. Generate character responses (Advisors)
    character_responses = generate_character_responses(
        action, quality_assessment, final_effects, narrative_state, llm_generate_fn
    )
    
    # 8. Generate narrative summary
    reasoning = _generate_actor_summary(actor_responses, quality_assessment)
    
    # 9. Check for crisis triggers
    _check_and_trigger_crises(narrative_state)
    
    return final_effects, actor_responses, character_responses, reasoning


def _generate_actor_summary(responses: List[ActorResponse], quality: Dict) -> str:
    """Generate human-readable summary of actor responses."""
    summary_parts = []
    
    summary_parts.append(f"Action Quality: {quality['quality'].upper()}")
    summary_parts.append(f"Reasoning: {quality['reasoning']}")
    summary_parts.append("")
    summary_parts.append("International Response:")
    
    for response in responses:
        support_symbol = {
            "yes": "✓",
            "no": "✗",
            "conditional": "○"
        }.get(response.will_support, "?")
        
        summary_parts.append(f"  {support_symbol} {response.actor_id}: {response.public_response[:60]}...")
    
    return "\n".join(summary_parts)


def _update_character_attitudes(narrative_state: NarrativeState, quality: str):
    """Update character trust based on action quality"""
    trust_deltas = {
        "exceptional": +5,
        "good": +2,
        "adequate": 0,
        "poor": -3,
        "catastrophic": -8
    }
    
    delta = trust_deltas.get(quality, 0)
    
    # Update UK advisors
    for char_id in ["uk_nsa", "uk_foreign_sec", "uk_home_sec", "uk_cds"]:
        if char_id in narrative_state.characters:
            narrative_state.update_character_attitude(char_id, trust_delta=delta)


def _check_and_trigger_crises(narrative_state: NarrativeState):
    """Check metrics and trigger narrative crises"""
    m = narrative_state.hidden_metrics
    
    # High escalation risk
    if m.escalation_risk >= 85 and "War Threshold Reached" not in narrative_state.active_crises:
        narrative_state.add_crisis("War Threshold Reached")
        narrative_state.add_event("Crisis: Situation at war threshold")
    
    # Low stability
    if m.domestic_stability < 30 and "Domestic Crisis" not in narrative_state.active_crises:
        narrative_state.add_crisis("Domestic Crisis")
        narrative_state.add_event("Crisis: Public order deteriorating")
    
    # Low cohesion
    if m.alliance_cohesion < 25 and "Alliance Fracturing" not in narrative_state.active_crises:
        narrative_state.add_crisis("Alliance Fracturing")
        narrative_state.add_event("Crisis: NATO unity collapsing")
