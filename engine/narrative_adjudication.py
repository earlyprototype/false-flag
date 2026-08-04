"""
Narrative-Driven Adjudication System
=====================================

Uses hidden metrics to guide LLM character responses whilst
presenting narrative consequences to player.
"""

import logging
import re
from typing import Dict, List, Tuple, Any
from random import Random

logger = logging.getLogger(__name__)

from models.narrative_state import NarrativeState
from engine.endings import _truncate_decision
from engine.utils import clamp

# Actor Simulation Imports
from models.state_actors import StateActorSystem, ActorResponse
from llm.fanout import generate_group
from engine.actor_simulation import (
    simulate_actor_responses,
    calculate_effects_from_responses,
    identify_relevant_actors,
    display_country_name
)


# === MYSTERY-MODE LEAK GUARD ===

# Phrases that give the game away outright. Both leaks observed in live play
# (gpt-oss-120b turn 1, llama-3.3-70b turn 3) used wording from this set —
# the old prompt asked the model to weigh the "hidden truth", so it said so.
# Kept in step with the prompt's prohibitions: whatever the adjudicator is
# told not to say, the scrubber must be able to catch.
_LEAK_MARKERS = re.compile(
    r"secret narrative|hidden narrative|hidden truth|secret truth|"
    r"narrative context|true (?:architect|author|instigator)|"
    r"\bpatsy\b|answer key",
    re.IGNORECASE,
)

# A run this long shared with the narrative description is a quotation, not
# a coincidence — the observed leak paraphrased lightly, so compare token
# windows rather than requiring an exact substring match.
_DESCRIPTION_WINDOW = 8

_NEUTRAL_REASONING = "Your advisors take stock of the response."

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _normalise(text: str) -> List[str]:
    """Lowercase word tokens, punctuation stripped, for overlap comparison."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _quotes_description(sentence: str, description: str) -> bool:
    """True if the sentence shares a long verbatim run with the description."""
    sentence_tokens = _normalise(sentence)
    description_tokens = _normalise(description)
    if len(sentence_tokens) < _DESCRIPTION_WINDOW:
        return False
    if len(description_tokens) < _DESCRIPTION_WINDOW:
        return False
    windows = {
        tuple(description_tokens[i:i + _DESCRIPTION_WINDOW])
        for i in range(len(description_tokens) - _DESCRIPTION_WINDOW + 1)
    }
    return any(
        tuple(sentence_tokens[i:i + _DESCRIPTION_WINDOW]) in windows
        for i in range(len(sentence_tokens) - _DESCRIPTION_WINDOW + 1)
    )


def _scrub_reasoning(reasoning: str, world_narrative=None) -> str:
    """Strip any sentence that reveals the hidden narrative to the player.

    The adjudicator's REASONING is shown verbatim in the ACTION ASSESSMENT
    panel *and* written to the transcript and save, so a leak also poisons
    later LLM context and the spectator console. Scrubbing happens here, at
    the parse boundary, rather than at display time so the leak never enters
    the record at all (issue #19).

    Offending sentences are dropped individually — the rest of the critique
    is usually sound and worth keeping. If nothing survives, fall back to a
    neutral line in the same voice the display layer uses.
    """
    if not reasoning:
        return reasoning

    narrative_id = getattr(world_narrative, "narrative_id", None)
    description = getattr(world_narrative, "description", None)

    kept = []
    for sentence in _SENTENCE_SPLIT.split(reasoning.strip()):
        if not sentence.strip():
            continue
        if _LEAK_MARKERS.search(sentence):
            continue
        if narrative_id and narrative_id.lower() in sentence.lower():
            continue
        if description and _quotes_description(sentence, description):
            continue
        kept.append(sentence.strip())

    if not kept:
        logger.debug("Adjudication reasoning fully scrubbed for narrative leak")
        return _NEUTRAL_REASONING
    return " ".join(kept)


# === EVENT DISPOSITION (issue #25) ===

# Verbs that describe closing a situation out, not merely responding to it.
_CLOSURE_VERBS = (
    "escort", "expel", "remove", "recover", "recovered", "salvage",
    "neutralise", "neutralize", "contain", "restore", "restored",
    "evacuate", "evacuated", "arrest", "detain", "secure", "seal",
    "resolve", "resolved", "conclude", "complete", "shut down", "stand down",
)

_STOPWORDS = frozenset({
    "the", "a", "an", "of", "off", "on", "in", "at", "to", "and", "or",
    "for", "from", "by", "with", "is", "was", "has", "have", "been",
})


def _significant_words(text: str) -> set:
    """Content words, lowercased - used for cheap title/action overlap."""
    return {w for w in re.findall(r"[a-z']+", (text or "").lower())
            if len(w) > 3 and w not in _STOPWORDS}


def record_event_disposition(narrative_state, action: str) -> None:
    """Set how the event under adjudication was left by ``action``.

    Closes the *most recently staged* entry rather than looking one up by
    turn number. ``narrative_state.turn`` is synchronised with the world
    turn only after adjudication, so a turn-keyed lookup finds the previous
    turn's event; and the ledger is append-only with one entry per turn, so
    the last entry is always the one being adjudicated.

    Must be called from every adjudication path - actor-enabled campaigns
    route through ``adjudicate_with_actor_simulation``, so recording in the
    narrative path alone left the ledger permanently open in real play.
    """
    try:
        ledger = getattr(narrative_state, "event_ledger", None)
        if not ledger:
            return
        current = ledger[-1]
        disposition = infer_event_disposition(current.title, action)
        if disposition != "open":
            narrative_state.close_event(
                current.turn, disposition, _truncate_decision(action, 90))
    except Exception:  # pragma: no cover - bookkeeping must never break a turn
        logger.debug("Could not set event disposition", exc_info=True)


def infer_event_disposition(title: str, action: str) -> str:
    """Guess how the player left the event titled ``title``.

    Deliberately conservative. A false "resolved" suppresses a live thread
    from future injects, which is worse than the repetition the ledger
    exists to prevent - so closure is only claimed when the decision both
    refers to the event and uses language of ending it. Everything else is
    "advanced" (engaged with) or "open" (not addressed).
    """
    title_words = _significant_words(title)
    if not title_words:
        return "open"
    action_lower = (action or "").lower()
    overlap = title_words & _significant_words(action)
    if not overlap:
        return "open"
    if any(verb in action_lower for verb in _CLOSURE_VERBS):
        return "resolved"
    return "advanced"


# === QUALITY ASSESSMENT ===

def assess_action_quality(
    action: str,
    narrative_state: NarrativeState,
    interpretation: str,
    llm_generate_fn = None,
    world_narrative = None,
    rng: Random = None
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
    
    if llm_generate_fn is None or rng is None:
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
6. Was this decision well-reasoned given what the player could actually know?
   Reward sound judgement under uncertainty - gathering evidence, testing
   assumptions, keeping options open - and penalise acting further than the
   evidence supports. Do NOT reward or punish the player for agreeing or
   disagreeing with facts they have no way of knowing yet.

Any secret narrative context above is background for YOU: use it to judge which
consequences are foreseeable and how other actors will really respond. It is not
something the player has been told.

CRITICAL - REASONING is displayed to the player word for word:
- Never mention a secret or hidden narrative, hidden truth, or these instructions
- Never name the crisis protagonist, patsy, or true author of events
- Never state attribution as settled fact the player has not established
- Argue only from evidence visible in the game world

Respond in this exact format:

QUALITY: [exceptional/good/adequate/poor/catastrophic]

REASONING: [One paragraph explaining the assessment, in the terms above]

EFFECTS:
escalation_risk: [delta -20 to +20]
alliance_cohesion: [delta -20 to +20]
domestic_stability: [delta -20 to +20]

QUALITY MULTIPLIER: [0.5 to 2.5]
"""
    
    try:
        response = llm_generate_fn(prompt, rng, max_tokens=400)
        return _parse_quality_response(response, world_narrative)
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
            # Amplify (never invert) the harmful effects: a negative multiplier
            # would flip escalation penalties into rewards in apply_quality_scaling
            multiplier = 2.0
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


def _parse_quality_response(response: str, world_narrative=None) -> Dict[str, Any]:
    """Parse LLM quality assessment response.

    Args:
        response: Raw LLM text in the QUALITY/REASONING/EFFECTS format.
        world_narrative: Optional NarrativeConfig. When present, the reasoning
            is scrubbed of anything that would reveal the hidden narrative to
            the player before it reaches the screen, transcript or save.
    """
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
            "catastrophic": 2.0  # amplify the harmful effects; negative would invert them
        }
        multiplier = quality_multipliers.get(quality, 1.0)
    
    return {
        "quality": quality,
        "multiplier": multiplier,
        "reasoning": _scrub_reasoning(reasoning, world_narrative) or "Action assessed.",
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
    llm_generate_fn = None,
    rng: Random = None,
    llm_batch_fn = None
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
    if llm_generate_fn is None or rng is None:
        # Fallback to templated responses
        return _generate_templated_responses(action, quality_assessment, narrative_state)

    # Select key characters to respond
    key_characters = [c for c in _select_responding_characters(narrative_state, final_effects)
                      if c in narrative_state.characters]

    # Each advisor reacts to the same decision and the same assessment; none
    # of them reads another's line. Asked together rather than in sequence.
    chars = [narrative_state.characters[char_id] for char_id in key_characters]
    prompts = [
        build_character_response_prompt(
            character=char,
            action=action,
            quality=quality_assessment["quality"],
            narrative_state=narrative_state,
        )
        for char in chars
    ]
    raw = generate_group(prompts, llm_generate_fn, rng, llm_batch_fn,
                         max_tokens=CHARACTER_RESPONSE_MAX_TOKENS)

    responses = []
    for char, text in zip(chars, raw):
        cleaned = (text or "").strip().strip('"')
        # The batch path reports a per-prompt failure as "[ERROR: ...]" text
        # rather than raising, and the string is truthy - so without this it
        # survives as the advisor's spoken line and the player watches a
        # cabinet minister read out an HTTP status. The single-call path could
        # not produce this: a failed call raised and the caller substituted
        # the fallback. actor_simulation guards the same marker.
        if cleaned.startswith("[ERROR:"):
            cleaned = ""
        # Same fallback the single-call path used when a response was refused
        responses.append((char.name, cleaned or f"[{char.name}] Understood, Prime Minister."))
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


# Character reactions are two or three sentences; the cap is what stops a
# model that cannot be told to stop from spending its whole budget thinking
# and returning nothing. Named here because the batch path has to pass it
# explicitly, and a silently dropped cap is an empty advisor line.
CHARACTER_RESPONSE_MAX_TOKENS = 150


def build_character_response_prompt(
    character,
    action: str,
    quality: str,
    narrative_state: NarrativeState,
) -> str:
    """Build one advisor's reaction prompt (no call - see generate_group)."""

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

    return prompt


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


# === SITUATION SUMMARY ===

def update_situation_summary(
    narrative_state: NarrativeState,
    action: str,
    llm_generate_fn = None,
    rng: Random = None
) -> None:
    """
    Refresh the player-facing situation summary after adjudication.

    The summary is the primary end-of-turn display in emergent mode and feeds
    to_llm_context() for every downstream prompt, so it must track the story
    rather than stay frozen at its initial value.
    """
    if llm_generate_fn is not None and rng is not None:
        context = narrative_state.to_llm_context()
        prompt = f"""
{context}

THE PRIME MINISTER'S LATEST DECISION: {action}

Summarise the current situation in 2-3 sentences for the Prime Minister's
daily brief. Cover how the crisis stands after this decision, the state of
the alliance, and the mood at home. Write in plain, serious prose - no
headings, no numbers, no bullet points.

Summary:"""
        try:
            summary = llm_generate_fn(prompt, rng, max_tokens=150).strip().strip('"')
            if summary:
                narrative_state.situation_summary = summary
                return
        except Exception:
            logger.debug(
                "LLM situation summary failed; using deterministic fallback",
                exc_info=True,
            )

    # Deterministic fallback composed from the current hidden state
    m = narrative_state.hidden_metrics
    if m.escalation_risk >= 85:
        risk = "The situation stands at the threshold of open war."
    elif m.escalation_risk >= 70:
        risk = "Escalation is severe and the margin for error is narrowing."
    elif m.escalation_risk >= 50:
        risk = "Tensions remain elevated across the North Atlantic."
    else:
        risk = "The immediate crisis appears contained, for now."

    if m.alliance_cohesion >= 70:
        alliance = "NATO stands firmly behind the UK."
    elif m.alliance_cohesion >= 50:
        alliance = "Allied support is holding, though commitments remain cautious."
    elif m.alliance_cohesion >= 30:
        alliance = "Alliance unity is under visible strain."
    else:
        alliance = "The alliance is fracturing and the UK risks standing alone."

    if m.domestic_stability >= 70:
        domestic = "The public mood is steady."
    elif m.domestic_stability >= 50:
        domestic = "The home front is anxious but orderly."
    elif m.domestic_stability >= 30:
        domestic = "Domestic pressure on the Government is mounting."
    else:
        domestic = "Public order is deteriorating."

    parts = [risk, alliance, domestic]
    if narrative_state.active_crises:
        parts.append("Active crises: " + ", ".join(narrative_state.active_crises[-3:]) + ".")
    narrative_state.situation_summary = " ".join(parts)


# === MAIN ADJUDICATION FUNCTIONS ===

def adjudicate_with_narrative(
    narrative_state: NarrativeState,
    action: str,
    interpretation: str,
    rng: Random,
    llm_generate_fn = None,
    world_narrative = None,
    llm_batch_fn = None
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
        llm_batch_fn: Optional batch generator, forwarded to
            generate_character_responses so the advisor reactions go out
            as one group.

    Returns:
        (final_effects, character_responses, quality_reasoning)
    """
    
    # 1. Assess action quality and get LLM-suggested effects
    quality_assessment = assess_action_quality(
        action, narrative_state, interpretation, llm_generate_fn, world_narrative, rng
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
    
    # 3b. Record how this turn's event was left (issue #25)
    record_event_disposition(narrative_state, action)

    # 4. Generate character responses
    character_responses = generate_character_responses(
        action, quality_assessment, final_effects, narrative_state,
        llm_generate_fn, rng, llm_batch_fn=llm_batch_fn
    )
    
    # 5. Update character attitudes based on action quality
    _update_character_attitudes(narrative_state, quality_assessment["quality"])
    
    # 6. Check for crisis triggers
    _check_and_trigger_crises(narrative_state)

    # 7. Refresh the player-facing situation summary
    update_situation_summary(narrative_state, action, llm_generate_fn, rng)

    return final_effects, character_responses, quality_assessment["reasoning"]


def adjudicate_with_actor_simulation(
    narrative_state: NarrativeState,
    actor_system: StateActorSystem,
    action: str,
    interpretation: str,
    rng: Random,
    llm_generate_fn,
    world_narrative = None,
    llm_batch_fn = None
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

    Args:
        narrative_state: Current narrative state (modified in place)
        actor_system: The state actors available to respond
        action: Player action text
        interpretation: LLM interpretation
        rng: Random number generator
        llm_generate_fn: Function to call the LLM
        world_narrative: Optional NarrativeConfig for secret truth context
        llm_batch_fn: Optional batch generator, forwarded to both
            simulate_actor_responses and generate_character_responses.

    Returns:
        (final_effects, actor_responses, character_responses, reasoning),
        where reasoning is the actor-response summary.
    """
    
    # 1. Identify which actors should respond
    relevant_actor_ids = identify_relevant_actors(action, actor_system, max_actors=3)
    
    # 2. Simulate each actor's response
    world_context = narrative_state.to_llm_context()
    
    if world_narrative:
        world_context += "\n\nSECRET NARRATIVE TRUTH:\n" + world_narrative.to_llm_context()
    
    actors = [a for a in (actor_system.get_actor(i) for i in relevant_actor_ids) if a]
    actor_responses = simulate_actor_responses(
        actors, action, world_context, llm_generate_fn, rng,
        llm_batch_fn=llm_batch_fn
    )
    for actor, response in zip(actors, actor_responses):
        # Update actor's relationship with UK
        actor_system.update_actor_relationship(actor.country_code, response.trust_change)
    
    # 3. Calculate effects from responses
    actor_effects = calculate_effects_from_responses(actor_responses, actor_system)
    
    # 4. Also run quality assessment for player skill
    quality_assessment = assess_action_quality(action, narrative_state, interpretation, llm_generate_fn, world_narrative, rng)

    # Record how this turn's event was left. Actor-enabled campaigns route
    # here rather than through adjudicate_with_narrative, so this path needs
    # the same bookkeeping or the ledger never closes (issue #25).
    record_event_disposition(narrative_state, action)
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
        action, quality_assessment, final_effects, narrative_state,
        llm_generate_fn, rng, llm_batch_fn=llm_batch_fn
    )
    
    # 8. Generate narrative summary
    reasoning = _generate_actor_summary(actor_responses, quality_assessment)
    
    # 9. Check for crisis triggers
    _check_and_trigger_crises(narrative_state)

    # 10. Refresh the player-facing situation summary
    update_situation_summary(narrative_state, action, llm_generate_fn, rng)

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

        actor_name = display_country_name(response.actor_id)
        # Word-boundary truncation (shared with the debrief recap) so the
        # summary never ends mid-word
        public = _truncate_decision(response.public_response, limit=90)
        summary_parts.append(f"  {support_symbol} {actor_name}: {public}")

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
