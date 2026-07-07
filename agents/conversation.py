"""Conversational advisor system using LLM to generate in-character responses.

Replaces the old hardcoded AdvisorProposal system with free-form Q&A.
"""

from typing import Any, Dict, List, Tuple
from random import Random

from models.world import WorldState
from llm.prompts import (
    build_advisor_context,
    build_decision_interpretation_prompt,
    build_pushback_prompt,
    build_critical_omissions_prompt
)
from llm.model_config import LLMContext
from engine.initial_conditions import get_all_uk_advisors


def handle_player_question(
    world: WorldState,
    question: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> List[Tuple[str, str]]:
    """Handle player's question during discussion phase.
    
    Determines which advisor(s) should respond based on question content
    and their knowledge domains, then generates in-character responses.
    
    Args:
        world: Current world state
        question: Player's question
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM (signature: prompt, rng -> str)
        rng: Random number generator for determinism
        transcript: Optional full game transcript for conversation history
    
    Returns:
        List of (advisor_role, response) tuples
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)
    
    # If no advisors loaded, return error message
    if not uk_advisors:
        return [("System", "Error: No advisors available. Initial conditions may not have loaded correctly.")]
    
    # Simple keyword matching to determine which advisor(s) should respond
    # In a full implementation, this could use LLM to route questions
    question_lower = question.lower()
    
    responding_advisors = []
    
    # Check for specific advisor mentions
    advisor_keywords = {
        "chief_defence_staff": ["cds", "military", "defence", "forces", "deploy"],
        "national_security_advisor": ["nsa", "security", "intelligence", "threat", "assess"],
        "foreign_secretary": ["foreign", "diplomatic", "alliance", "nato", "us"],
        "home_secretary": ["home", "domestic", "public", "civilian", "infrastructure"],
        "attorney_general": ["legal", "law", "attorney", "international law"],
        "prime_minister": ["pm", "prime minister", "overall", "strategy"]
    }
    
    for char_id, keywords in advisor_keywords.items():
        if char_id in uk_advisors and any(kw in question_lower for kw in keywords):
            responding_advisors.append(char_id)
    
    # If no specific advisor mentioned, default to NSA (coordinates responses)
    if not responding_advisors and "national_security_advisor" in uk_advisors:
        responding_advisors = ["national_security_advisor"]
    
    # If still no advisors, return all available
    if not responding_advisors:
        responding_advisors = list(uk_advisors.keys())[:1]  # Just return first one
    
    # Generate responses
    responses = []
    for char_id in responding_advisors:
        try:
            prompt = build_advisor_context(world, initial_conditions, char_id, question, transcript)
            response = llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_QA)
            
            char_info = uk_advisors[char_id]
            role = char_info.get("role", "Advisor")
            responses.append((role, response))
        except Exception as e:
            responses.append(("System", f"Error generating response: {e}"))
    
    return responses


def interpret_player_action(
    world: WorldState,
    action: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> str:
    """Interpret player's free-form action into structured summary.
    
    Args:
        world: Current world state
        action: Player's action description
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
    
    Returns:
        Structured interpretation of the action
    """
    prompt = build_decision_interpretation_prompt(world, action, initial_conditions, transcript)
    interpretation = llm_generate_fn(prompt, rng, context=LLMContext.DECISION_INTERPRETATION)
    return interpretation


def generate_advisor_pushback(
    world: WorldState,
    action: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> List[Tuple[str, str]]:
    """Generate advisor warnings/pushback for player's action.
    
    Args:
        world: Current world state
        action: Player's action description
        interpretation: LLM's interpretation of the action
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
    
    Returns:
        List of (advisor_role, pushback_message) tuples, or empty list if no pushback
    """
    prompt = build_pushback_prompt(world, action, interpretation, initial_conditions, transcript)
    pushback_text = llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_PUSHBACK)
    
    # Parse pushback response
    if "NO PUSHBACK" in pushback_text:
        return []
    
    # Simple parsing: each line starting with role name
    pushback_list = []
    for line in pushback_text.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            role, message = line.split(":", 1)
            pushback_list.append((role.strip(), message.strip()))
    
    return pushback_list


def check_critical_omissions(
    world: WorldState,
    player_decision: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None
) -> List[Tuple[str, str, str]]:
    """Check if player has failed to take critical actions.
    
    After decision interpretation, key advisors scan for catastrophic omissions:
    - Military action without NATO coordination
    - Offensive action without legal authority
    - Crisis without public communication
    - Escalation without ally consultation
    
    High threshold - only truly critical gaps are flagged.
    
    Args:
        world: Current world state
        player_decision: The decision the PM made
        interpretation: LLM's interpretation of the decision
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
    
    Returns:
        List of (advisor_role, concern, recommendation) tuples
        Empty list if no critical omissions detected
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)
    
    if not uk_advisors:
        return []
    
    # Build recent events context from world state
    recent_events = []
    if hasattr(world, 'recent_injects') and world.recent_injects:
        recent_events = world.recent_injects[-3:]  # Last 3 injects
    elif hasattr(world, 'flags') and world.flags:
        # Fallback: use flags as context
        recent_events = [f"Active situation: {flag}" for flag in list(world.flags.keys())[:3]]
    
    # Check with specific advisors based on their domain
    advisors_to_check = [
        "foreign_secretary",      # Alliance/diplomatic omissions
        "chief_defence_staff",    # Military readiness gaps
        "attorney_general",       # Legal authority gaps
        "home_secretary",         # Domestic security/messaging
        "national_security_advisor"  # Overall strategic coordination
    ]
    
    critical_concerns = []
    
    for char_id in advisors_to_check:
        if char_id not in uk_advisors:
            continue
        
        try:
            prompt = build_critical_omissions_prompt(
                world,
                initial_conditions,
                char_id,
                player_decision,
                recent_events,
                transcript
            )
            response = llm_generate_fn(prompt, rng, context=LLMContext.CRITICAL_OMISSIONS)
            
            # Parse response
            if "NO_CONCERN" in response or "NO CONCERN" in response:
                continue
            
            # Extract concern and recommendation
            concern = ""
            recommendation = ""
            
            lines = response.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("CONCERN:"):
                    concern = line.replace("CONCERN:", "").strip()
                elif line.startswith("RECOMMENDATION:"):
                    recommendation = line.replace("RECOMMENDATION:", "").strip()
                elif concern and not recommendation:
                    # Multi-line concern
                    concern += " " + line
            
            if concern and recommendation:
                char_info = uk_advisors[char_id]
                role = char_info.get("role", "Advisor")
                critical_concerns.append((role, concern, recommendation))
        
        except Exception:
            # Silently continue if one advisor check fails
            continue
    
    return critical_concerns

