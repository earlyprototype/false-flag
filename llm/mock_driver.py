"""Mock LLM driver for deterministic testing.

Provides template-based responses for the conversational system. Mock mode is
the first-run experience (no API key configured), so the canned cabinet must
behave like a cabinet: each advisor speaks with their own voice, reactions
reference the quality of the decision, and foreign capitals respond in
character rather than with a single generic acknowledgement.
"""

import re
import zlib
from random import Random


def _stable_index(key: str, size: int) -> int:
    """Deterministic variant selection (Python's hash() is salted per process)."""
    if size <= 0:
        return 0
    return zlib.crc32(key.encode("utf-8", errors="ignore")) % size


# ---------------------------------------------------------------------------
# Advisor personas
#
# Prompt builders address a single advisor with an explicit persona line:
#   - Q&A:              "You are the {role} in a UK government COBRA meeting"
#   - Reactions:        "You are {character.name}."
#   - Omissions check:  "You are the UK {role} advising the Prime Minister"
# Detection keys on that line rather than on keywords anywhere in the prompt,
# because the surrounding context (transcript, character lists) mentions every
# advisor by title and previously collapsed all voices into one.
# ---------------------------------------------------------------------------

# advisor key -> aliases used in persona lines (role titles and display names)
_ADVISOR_ALIASES = {
    "cds": ("military commander", "chief of the defence staff"),
    "nsa": ("intelligence coordinator", "national security advisor", "national security adviser"),
    "foreign": ("diplomatic lead", "foreign secretary"),
    "home": ("domestic security", "home secretary"),
    "legal": ("legal advisor", "attorney general"),
}

# In-character discussion answers, 3 variants per advisor.
_ADVISOR_QA = {
    "cds": [
        ("Prime Minister, from a military perspective our options are constrained. "
         "Our Type-45 destroyers provide ballistic missile defence, but we can only "
         "sustain two simultaneous combat air patrols across the entire UK. Any "
         "deployment must be one we can actually sustain."),
        ("Prime Minister, the Fleet is at sea and QRA jets are at readiness. What I "
         "cannot give you is depth: our missile stockpiles will not survive a "
         "prolonged exchange, so every deployment must serve a clear objective."),
        ("Prime Minister, militarily we can shadow their fleet and harden our air "
         "defences, but I must be blunt: we cannot match their numbers ship-for-ship. "
         "Anything we do should be defensive, deliberate, and coordinated with NATO."),
    ],
    "nsa": [
        ("Prime Minister, the intelligence picture points to a coordinated campaign "
         "of coercion. GCHQ and SIS both assess Russia is testing NATO resolve. I "
         "recommend we coordinate closely with allies and avoid any step that could "
         "be read as escalatory without defensive justification."),
        ("Prime Minister, our assessment is that Moscow is probing for gaps between "
         "us and our allies - each incident calibrated to stay below the Article 5 "
         "threshold. Our best play is patience, hard evidence, and a united front."),
        ("Prime Minister, the agencies are working the problem now. Attribution is "
         "firming but not yet courtroom-solid. Until it is, I would counsel against "
         "public accusations we cannot prove."),
    ],
    "foreign": [
        ("Prime Minister, diplomatically we must secure US and NATO commitment "
         "immediately. Unilateral action risks isolating us. I propose we activate "
         "Article 4 consultations and engage directly with Washington."),
        ("Prime Minister, the allies are watching how we respond. Paris and Berlin "
         "are hesitant; Warsaw is pressing for a firm line. A coordinated NATO "
         "statement would be worth more than any single deployment."),
        ("Prime Minister, my counterparts want evidence before commitment. If we "
         "share our intelligence through NATO channels and keep the Americans on "
         "side, we retain the diplomatic initiative."),
    ],
    "home": [
        ("Prime Minister, my concern is public safety and critical infrastructure "
         "protection. We've already seen attacks on power and transport. We need to "
         "reassure the public while quietly preparing civil defence measures."),
        ("Prime Minister, the public mood is fragile - panic buying has started in "
         "some areas and misinformation is spreading faster than our corrections. I "
         "recommend a calm, factual public statement within the day."),
        ("Prime Minister, police forces are stretched and infrastructure operators "
         "are asking for guidance. I want COBRA authority to raise protective "
         "security levels at key sites tonight."),
    ],
    "legal": [
        ("Prime Minister, from a legal perspective any use of force must be "
         "necessary and proportionate under international law. Self-defence is "
         "available to us, but we must document the threat meticulously."),
        ("Prime Minister, we are on firm legal ground for defensive measures in our "
         "own waters and airspace. Anything beyond that requires a clear Article 51 "
         "justification, and I would want it in writing before any order is given."),
        ("Prime Minister, I must caution that attribution matters legally as well as "
         "politically. Retaliating against the wrong actor would put us in breach "
         "and hand Moscow a propaganda victory."),
    ],
}

# Post-decision reactions, keyed by broad quality bucket. The reaction prompt
# includes "ACTION QUALITY: <quality>", which we use to pick the tone.
_ADVISOR_REACTIONS = {
    "cds": {
        "positive": ("A sound order, Prime Minister. The Chiefs can execute this "
                     "within current readiness, and it keeps our posture defensible."),
        "neutral": ("Understood, Prime Minister. I'll issue the orders and keep "
                    "force protection under continuous review."),
        "negative": ("Prime Minister, I will carry out the order, but I must "
                     "register concern: this stretches our forces beyond what I can "
                     "sustain if Moscow escalates."),
    },
    "nsa": {
        "positive": ("Prime Minister, that is the right call at this moment - it "
                     "addresses the threat without handing Moscow a pretext."),
        "neutral": ("Understood, Prime Minister. We will watch Moscow's response "
                    "closely and keep the assessment updated."),
        "negative": ("Prime Minister, I must be candid: I believe this plays into "
                     "Moscow's hands, and I would urge us to revisit it as the "
                     "picture develops."),
    },
    "foreign": {
        "positive": ("This will land well in allied capitals, Prime Minister. I'll "
                     "brief NATO counterparts within the hour."),
        "neutral": ("I'll relay this to our allies, Prime Minister, and manage any "
                    "concerns from the more hesitant capitals."),
        "negative": ("Prime Minister, I must warn you the allies will not like "
                     "this. I will try to hold the coalition together, but expect "
                     "difficult calls."),
    },
    "home": {
        "positive": ("This should steady the public mood, Prime Minister. I'll "
                     "align our domestic messaging with it today."),
        "neutral": ("Noted, Prime Minister. I'll keep policing and infrastructure "
                    "protection in step with this decision."),
        "negative": ("Prime Minister, I'm concerned about the message this sends at "
                     "home. We should prepare for a rough news cycle and the risk "
                     "of unrest."),
    },
    "legal": {
        "positive": ("Legally sound, Prime Minister. This sits comfortably within "
                     "our international obligations."),
        "neutral": ("I see no legal impediment, Prime Minister, though I will keep "
                    "the framework under review as events develop."),
        "negative": ("Prime Minister, I must place my legal reservations on record. "
                     "The justification for this course is thin as it stands."),
    },
}

_QUALITY_BUCKETS = {
    "exceptional": "positive",
    "good": "positive",
    "adequate": "neutral",
    "poor": "negative",
    "catastrophic": "negative",
}

# ---------------------------------------------------------------------------
# International actors (multi-agent simulation)
#
# The actor-simulation prompt asks for an EXACT structured format
# (PUBLIC_RESPONSE / TRUST_CHANGE / ...). Each country gets in-character
# variants; unknown codes fall back to a generic conditional response.
# Tuples: (public, private, trust_change, will_support, conditions, intel)
# ---------------------------------------------------------------------------

_ACTOR_RESPONSES = {
    "USA": [
        ("The United States stands with the United Kingdom. We are accelerating "
         "the carrier group's transit and expect full intelligence sharing in return.",
         "London is holding steady; we can work with this.",
         6, "yes", "", "Satellite coverage of the Northern Fleet's disposition"),
        ("Washington supports the UK's measured response, but Congress will want "
         "hard evidence before any wider commitment.",
         "Supportive in public, cautious in private until attribution is solid.",
         3, "conditional", "Provide verifiable attribution of the Severomorsk attack", "none"),
    ],
    "POL": [
        ("Poland fully endorses the UK's stance and offers immediate basing and "
         "logistical support on NATO's eastern flank.",
         "The stronger London acts, the safer Warsaw is.",
         8, "yes", "", "GRU logistics activity observed near Kaliningrad"),
        ("Warsaw urges the strongest possible allied response and will press for "
         "NATO consultations without delay.",
         "If NATO hesitates now, we are next.",
         5, "yes", "", "none"),
    ],
    "DEU": [
        ("Germany urges continued restraint and supports allied consultations, "
         "though we must weigh the energy implications for Europe carefully.",
         "Escalation would be catastrophic for German industry.",
         1, "conditional", "Exhaust diplomatic channels before any military measures", "none"),
        ("Berlin supports the UK diplomatically and will coordinate within the EU, "
         "but cannot commit to military measures at this stage.",
         "The coalition would fracture over anything harder than sanctions.",
         2, "conditional", "Keep responses below the threshold of armed conflict", "none"),
    ],
    "FRA": [
        ("France supports a firm and united European response and proposes joint "
         "naval patrols under a European framework.",
         "An opportunity to demonstrate European strategic autonomy.",
         4, "conditional", "Coordinate the response through European structures as well as NATO", "none"),
        ("Paris stands by the United Kingdom and will consult on further measures, "
         "favouring a calibrated response over escalation.",
         "Support London, but do not let Washington set the tempo alone.",
         3, "yes", "", "none"),
    ],
    "RUS": [
        ("The Russian Federation categorically rejects these provocations and warns "
         "that any aggressive act against Russian forces will be met with a "
         "decisive response.",
         "The pressure campaign is working; London is reacting as predicted.",
         -8, "no", "", "none"),
        ("Moscow denounces the UK's actions as reckless escalation orchestrated by "
         "NATO and reserves the right to respond by all necessary means.",
         "Maintain deniability; let their alliance argue itself apart.",
         -5, "no", "", "none"),
    ],
}

_ACTOR_DEFAULT = [
    ("We note the United Kingdom's action and are consulting with partners before "
     "determining our response.",
     "Wait for the major powers to move first.",
     0, "conditional", "Clear evidence and allied consensus", "none"),
]


def _detect_advisor(prompt_lower: str):
    """Return the advisor key explicitly addressed by a persona line, if any."""
    for key, aliases in _ADVISOR_ALIASES.items():
        for alias in aliases:
            if re.search(r"you are (?:the )?(?:uk )?(?:us )?" + re.escape(alias), prompt_lower):
                return key
    return None


def _extract_question(prompt: str) -> str:
    """Pull the player's question out of an advisor Q&A prompt, if present."""
    match = re.search(r'the prime minister asks:\s*"(.*?)"', prompt, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else prompt


class MockDeterministicDriver:
    """Deterministic mock LLM driver for testing.

    Generates template-based responses that are deterministic given the same
    prompt (variant choice hashes the question/prompt, not process state).
    """

    def generate_text(self, prompt: str, rng: Random) -> str:
        """Generate mock response based on prompt structure and keywords.

        Args:
            prompt: Input prompt
            rng: Random number generator (for future use)

        Returns:
            Mock response text
        """
        prompt_lower = prompt.lower()

        # Task-shaped prompts are checked BEFORE advisor personas: these prompts
        # embed the narrative context, which mentions advisors by title, so a
        # persona keyword would otherwise shadow the actual task.

        # Action quality assessment (narrative adjudication)
        if "assess this action" in prompt_lower:
            return ("QUALITY: adequate\n"
                    "\n"
                    "REASONING: A measured response that addresses the immediate situation without "
                    "overcommitting forces or foreclosing diplomatic options.\n"
                    "\n"
                    "EFFECTS:\n"
                    "escalation_risk: -2\n"
                    "alliance_cohesion: 3\n"
                    "domestic_stability: 1\n"
                    "\n"
                    "QUALITY MULTIPLIER: 1.0")

        # Situation summary refresh (end of turn)
        if "summarise the current situation" in prompt_lower:
            return ("The crisis continues to develop as Russian forces maintain their posture in the "
                    "North Atlantic. Allied consultations are ongoing and the public mood remains tense. "
                    "The Government's latest decision is being watched closely at home and abroad.")

        # Narrator bridge between turns
        if "atmospheric bridge" in prompt_lower:
            return ("The hours drag past in the bunker beneath Whitehall, each update thinning the "
                    "silence a little further. Then an aide appears at the door, folder in hand.")

        # Decision interpretation: echo the actual decision back as the summary
        # so the OPERATIONAL ORDER panel reflects what the player typed.
        if "interpret this action" in prompt_lower:
            decided = re.search(r'the prime minister has decided:\s*"(.*?)"', prompt,
                                re.IGNORECASE | re.DOTALL)
            summary = " ".join(decided.group(1).split()) if decided else \
                "Deploy naval and air assets to defensive posture"
            return (f"INTERPRETATION: {summary}\n"
                    "FORCES INVOLVED: Type-45 destroyers, combat air patrols, P-8 reconnaissance\n"
                    "RESOURCES CONSUMED: Minimal (patrol operations)\n"
                    "TIMELINE: Immediate (within 1 turn)\n"
                    "FEASIBILITY: Feasible within current constraints")

        # Pushback generation. Trigger keywords are matched against the PM's
        # actual decision text, not the whole prompt - the surrounding context
        # (force listings, transcript) mentions "deploy"/"carrier" on every
        # turn and would otherwise fire pushback for every decision.
        if "pushback triggers" in prompt_lower:
            decided = re.search(r'the pm has decided:\s*"(.*?)"', prompt,
                                re.IGNORECASE | re.DOTALL)
            action_text = (decided.group(1) if decided else prompt).lower()

            if "nuclear" in action_text:
                return ("Attorney General: Prime Minister, nuclear first-use without imminent existential threat "
                        "violates our legal framework and would fracture NATO immediately.\n"
                        "Foreign Secretary: This would end US support and isolate us internationally.")

            if "deploy" in action_text and ("carrier" in action_text or "prince of wales" in action_text):
                return ("Chief of the Defence Staff: Prime Minister, HMS Prince of Wales is not at highest readiness. "
                        "We can surge her immediately at reduced capability, or wait 3 turns for full readiness.")

            return "NO PUSHBACK"

        # Critical omissions check: the mock cabinet raises no blocking concerns
        if "critical omissions check" in prompt_lower:
            return "NO_CONCERN"

        # Inject generation
        if "generate the next inject" in prompt_lower:
            return """```yaml
id: turn_002_inject
title: "Russian Submarine Surfaces Near UK Waters"
description: |
  A Russian Kilo-class submarine has surfaced approximately 12 nautical miles off the Orkney Islands,
  within sight of a commercial ferry. The submarine remained on the surface for approximately 15 minutes
  before submerging. This provocative act was witnessed by civilians and is already spreading on social media.

  Intelligence assessment: This is a deliberate show of force designed to intimidate and test UK response.
  The submarine is part of the larger Northern Fleet deployment.
channel: intelligence
effects:
  - metric: escalation_risk
    delta: 5..10
  - metric: domestic_stability
    delta: -3..-5
```"""

        # International actor simulation (multi-agent adjudication). Requires the
        # structured-format marker so it can't shadow the advisor pushback prompt
        # (which also opens with "You are simulating...").
        if "you are simulating" in prompt_lower and "public_response" in prompt_lower:
            code_match = re.search(r"country:\s*[^\n(]*\(([a-z]{2,3})\)", prompt_lower)
            code = code_match.group(1).upper() if code_match else ""
            variants = _ACTOR_RESPONSES.get(code, _ACTOR_DEFAULT)
            public, private, trust, support, conditions, intel = \
                variants[_stable_index(prompt, len(variants))]
            return (f"PUBLIC_RESPONSE: {public}\n"
                    "\n"
                    f"PRIVATE_ASSESSMENT: {private}\n"
                    "\n"
                    f"TRUST_CHANGE: {trust:+d}\n"
                    "\n"
                    f"WILL_SUPPORT: {support}\n"
                    "\n"
                    f"CONDITIONS: {conditions or 'none'}\n"
                    "\n"
                    f"INTEL_SHARED: {intel}")

        # Advisor personas: key off the explicit "You are the <role>" persona
        # line so the addressed advisor answers, not whichever title happens to
        # appear first in the surrounding context/transcript.
        advisor = _detect_advisor(prompt_lower)
        if advisor:
            quality_match = re.search(r"action quality:\s*(\w+)", prompt_lower)
            if quality_match:
                # Post-decision reaction: tone follows the assessed quality
                bucket = _QUALITY_BUCKETS.get(quality_match.group(1), "neutral")
                return _ADVISOR_REACTIONS[advisor][bucket]
            variants = _ADVISOR_QA[advisor]
            return variants[_stable_index(_extract_question(prompt), len(variants))]

        # Legacy keyword fallback for prompts without a persona line
        for key, aliases in _ADVISOR_ALIASES.items():
            if any(alias in prompt_lower for alias in aliases):
                variants = _ADVISOR_QA[key]
                return variants[_stable_index(_extract_question(prompt), len(variants))]

        # Default response
        return "Understood, Prime Minister. I'll provide my assessment based on the current situation."

    def batch_generate_text(self, prompts: list[str], rng: Random) -> list[str]:
        """Generate multiple mock responses in parallel (simulated).

        Args:
            prompts: List of prompt texts
            rng: Random number generator

        Returns:
            List of mock responses in same order as prompts
        """
        # For mock driver, just call generate_text sequentially
        # (No actual parallelism needed for testing)
        return [self.generate_text(prompt, rng) for prompt in prompts]
