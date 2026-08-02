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

# ---------------------------------------------------------------------------
# Diplomatic calls (/call)
#
# The diplomacy prompt builder emits an explicit persona line:
#   "You are roleplaying as the {title} of {country} in a crisis simulation."
# Detection keys on that line (same technique as the advisor personas) and the
# player's current line arrives as "UK Prime Minister: {message}". Each
# callable capital gets its own voice; a light keyword layer shifts the
# response when the PM makes a recognisable ask (troops/ports vs statement vs
# support). Variant selection hashes the player's line.
# ---------------------------------------------------------------------------

_LEADER_LINE_RE = re.compile(
    r"you are roleplaying as the (.+?) of "
    r"(us|france|germany|poland|russia|ukraine|ireland) in a crisis simulation"
)

# country -> tone -> variants. Missing tones fall back to "general".
_DIPLOMACY_VOICES = {
    "ireland": {
        "military": [
            ("Prime Minister, I'll be straight with you, as a friend: Irish "
             "neutrality isn't something I can set aside, even now. Ports and "
             "bases for military use are off the table. What I can offer is "
             "Shannon for humanitarian flights, and every diplomatic channel "
             "Dublin has."),
            ("Ah, now - you know I can't send soldiers or open our ports to "
             "warships. The Dáil would have my head, and rightly so. But "
             "Ireland will help with the human side of this: refugees, medical "
             "support, quiet diplomacy wherever it's useful."),
        ],
        "statement": [
            ("We can certainly say something, Prime Minister, though you'll "
             "understand it will be worded carefully - concern, de-escalation, "
             "support for international law. Neutral language from a neutral "
             "country, but the warmth between our islands will be plain enough."),
        ],
        "general": [
            ("Prime Minister, it's good to hear your voice, truly - though I "
             "wish the circumstances were kinder. Ireland is watching this with "
             "real concern. We're neutral, you know that, but neutral doesn't "
             "mean indifferent. Tell me what you're thinking, and I'll tell you "
             "honestly what Dublin can and cannot do."),
            ("I won't pretend we aren't worried over here - your crisis washes "
             "up on our shores too, one way or another. We can't join any "
             "military effort, but if you need a back channel or an honest "
             "broker, Ireland's door is open."),
            ("Between the two of us, Prime Minister, half my cabinet is asking "
             "how close this comes to Irish airspace. We'll support you every "
             "way a neutral country can - just don't ask me for what I can't "
             "give."),
        ],
    },
    "us": {
        "support": [
            ("Prime Minister, we're with you - but let's be clear about what "
             "that means. Article 5 is for an armed attack, and my lawyers tell "
             "me we're not there yet. Give me hard attribution I can take to "
             "Congress and we'll talk about the next step. Meanwhile, what are "
             "you putting on the table?"),
            ("Look, America stands by its allies, you know that. But I need "
             "something to work with here - burden-sharing, intelligence, a "
             "concrete plan. If Europe steps up, we step up. That's the deal."),
        ],
        "military": [
            ("You want assets, I want clarity. The carrier group can move, but "
             "I'm not committing American forces to a shooting war on ambiguous "
             "intelligence. Show me the evidence chain and we'll surge what you "
             "need."),
        ],
        "general": [
            ("Alright, Prime Minister, give it to me straight - what's your "
             "play, and what do you need from us? I've got Congress asking why "
             "Europe can't handle its own backyard, and my planners want to be "
             "looking at the Pacific. Convince me."),
            ("We're tracking everything you're tracking, probably more. The "
             "question isn't whether America supports Britain - it's what this "
             "costs and who pays. Let's keep this practical."),
            ("I'll be honest with you: half this town wants to stay out of it, "
             "and half wants to sail the Sixth Fleet up the Channel. Keep your "
             "response tight and defensible and I can hold the middle together."),
        ],
    },
    "france": {
        "support": [
            ("France stands with Britain, naturally. But permit me an "
             "observation: if the answer to every European crisis is to "
             "telephone Washington, then Europe has learned nothing. Let us "
             "build a response that is ours - European capability, European "
             "resolve - and the Americans may join it."),
        ],
        "general": [
            ("Ah, Prime Minister. The situation is grave, but graver still "
             "would be a Europe that cannot answer for its own security. I "
             "propose we coordinate directly - joint patrols, shared "
             "intelligence, a European framework with NATO alongside it, not in "
             "front of it."),
            ("You will forgive me if I think aloud: Moscow tests not Britain, "
             "but Europe entire. The response must be measured, sophisticated - "
             "escalation is a game the crude play. France offers you "
             "partnership, on the understanding that Europe leads."),
            ("France is with you, of course. But let us be precise about the "
             "architecture of this response. Strategic autonomy is not a "
             "slogan, Prime Minister - it is the difference between a Europe "
             "that acts and one that waits."),
        ],
    },
    "germany": {
        "military": [
            ("Prime Minister, I must be honest: military measures are extremely "
             "difficult for us. My coalition would not survive a deployment "
             "vote taken in haste, and our constitutional constraints are real. "
             "Let us exhaust Article 4 consultations first - properly, "
             "collectively."),
        ],
        "support": [
            ("Germany supports you, but you must understand my position. Half "
             "of German industry is watching the gas price, and half my "
             "coalition is watching the other half. I can deliver consensus, "
             "sanctions, patience - I cannot deliver boldness overnight."),
        ],
        "general": [
            ("Prime Minister, thank you for consulting us before acting - it "
             "matters. We must proceed by the book: NATO consultations, EU "
             "coordination, consensus at each step. Germany's support is solid, "
             "but it must be built properly or it will not hold."),
            ("I will speak plainly, between us: our energy exposure is severe, "
             "and my coalition partners are nervous. Germany will not block a "
             "firm collective response, but I need process, evidence, and time "
             "to bring my government with me."),
            ("This is a grave situation, and gravity demands care. We support "
             "de-escalation where possible and defence where necessary - in "
             "that order. Please, no surprises; every unilateral step makes my "
             "task in Berlin harder."),
        ],
    },
    "poland": {
        "military": [
            ("Whatever you need, Prime Minister - airfields, ports, logistics "
             "corridors, they are yours. Poland has been preparing for this day "
             "for twenty years. Base your aircraft with us, stage through "
             "Gdansk, and let Moscow see that NATO's flank holds."),
        ],
        "support": [
            ("Poland is with you completely - and I ask only that Britain not "
             "lose its nerve. Push for Article 4 today and put Article 5 on the "
             "table. Every day of hesitation, Moscow reads as weakness. We know "
             "them; we have always known them."),
        ],
        "general": [
            ("Prime Minister, we warned the West for years, and now it is "
             "here. Poland stands with Britain without conditions. Tell me what "
             "you need - basing, logistics, our voice at NATO - and it is done."),
            ("Good that you called. While Berlin drafts communiqués, Poland "
             "acts. Our eastern radars are yours, our airspace is open to "
             "allied movements, and my government will back the strongest "
             "response NATO will bear."),
            ("Do not let them do to you what they did to others by inches, "
             "Prime Minister. Strength now is the cheapest option on the table. "
             "Poland offers full support - and asks that Britain lead from the "
             "front."),
        ],
    },
    "russia": {
        "general": [
            ("Prime Minister, I will convey your words to Moscow, though I "
             "doubt they will improve the mood there. The Russian Federation "
             "has attacked no one. It is British provocation, and NATO's, that "
             "brings us to this point - and provocations have consequences."),
            ("You repeat accusations without evidence. Russia conducts lawful "
             "exercises in international waters; your response has been "
             "hysteria and escalation. I would advise the United Kingdom, most "
             "sincerely, to step back before events acquire their own logic."),
            ("These are serious charges, Prime Minister, delivered with "
             "remarkably little proof. Moscow denies them entirely. But I note "
             "them carefully - as I note every British deployment. Nothing you "
             "do goes unobserved."),
        ],
    },
    "ukraine": {
        "general": [
            ("Prime Minister, we have seen this film before - the denials, the "
             "'exercises', the outrage at being accused. It is the same "
             "playbook they used on us. Do not wait for perfect proof; by then "
             "the next phase has already begun. Ukraine will share everything "
             "we have."),
            ("Listen to me as a friend who has paid for this knowledge: they "
             "escalate when you hesitate and pause when you are firm. Whatever "
             "you decide, decide it quickly and together with your allies. Our "
             "intelligence services are at your disposal."),
            ("We stand with Britain absolutely. And I must say what others "
             "will not: some of your allies will counsel patience because the "
             "missiles are not falling on them. We know how that story ends. "
             "Move fast, stay united, and do not negotiate from fear."),
        ],
    },
}

_DIPLOMACY_DEFAULT = {
    "general": [
        ("Prime Minister, thank you for the call. My government is following "
         "events closely and consulting with partners. We would welcome any "
         "evidence you can share through official channels, and we will "
         "coordinate our response accordingly."),
        ("We appreciate the United Kingdom keeping us informed. Our position "
         "for now is one of concern and careful watching - please keep this "
         "channel open as the situation develops."),
    ],
}


def _diplomacy_tone(message_lower: str) -> str:
    """Classify the PM's ask so capitals can react to it plausibly."""
    if any(w in message_lower for w in (
            "troop", "soldier", "ship", "port", "base", "basing", "deploy",
            "military", "forces", "navy", "aircraft")):
        return "military"
    if any(w in message_lower for w in (
            "statement", "public", "announce", "declar", "condemn", "press")):
        return "statement"
    if any(w in message_lower for w in (
            "support", "help", "assist", "commit", "article 5", "stand with",
            "back us")):
        return "support"
    return "general"


def _extract_player_line(prompt: str) -> str:
    """Pull the PM's current line out of a diplomacy prompt, if present."""
    matches = re.findall(r"uk prime minister:\s*(.+)", prompt, re.IGNORECASE)
    return matches[-1].strip() if matches else prompt

# ---------------------------------------------------------------------------
# Mystery mode narratives
#
# When a hidden narrative is active, its context block (models/narrative.py
# to_llm_context) reaches prompts via the context builders and includes a
# "Crisis Protagonist: <ISO>" line. Detection keys on that line; tells are
# short clauses appended deterministically to roughly half of the outputs so
# the deduction loop is playable offline without turning into a headline.
# ---------------------------------------------------------------------------

_NARRATIVE_PROTAGONISTS = {"rus": "russia", "chn": "china"}


def _detect_narrative(prompt_lower: str):
    """Return 'russia'/'china' if a hidden narrative context block is present."""
    match = re.search(r"crisis protagonist:\s*([a-z]{2,3})", prompt_lower)
    if not match:
        return None
    return _NARRATIVE_PROTAGONISTS.get(match.group(1))


# Advisor Q&A tells, keyed by advisor then narrative.
_ADVISOR_TELLS = {
    "nsa": {
        "china": (" One loose thread troubles me: several of the financial and "
                  "cyber fingerprints do not route through Moscow at all - they "
                  "trace east, through Hong Kong infrastructure we associate "
                  "with Chinese state actors."),
        "russia": (" If anything, attribution is almost too clean - textbook "
                   "GRU tradecraft, every fingerprint exactly where we would "
                   "expect it."),
    },
    "foreign": {
        "china": (" And a small oddity from the diplomatic track: Beijing has "
                  "gone unusually quiet - not even their standard call for "
                  "restraint from all sides."),
        "russia": (" The diplomatic picture matches the intelligence, for once: "
                   "this is Moscow's operation, prosecuted more or less in the "
                   "open."),
    },
}

# Foreign-leader tells for /call responses (the Russian ambassador excepted).
_DIPLOMACY_TELLS = {
    "china": ("One more thing, between us - has anyone in London remarked on "
              "how quiet Beijing has been through all of this? Not even the "
              "usual lecture about restraint."),
    "russia": ("For what it is worth, our own services see Moscow's hand in "
               "this, and Moscow's alone."),
}

# International-actor tells (appended to public responses; RUS excepted).
_ACTOR_TELLS = {
    "china": (" We are also watching indicators well beyond Moscow - Beijing's "
              "public silence has been noted."),
}

# Inject description tells (inserted inside the YAML description block).
_INJECT_TELLS = {
    "china": ("  Analysts flag one anomaly: elements of the financing and cyber "
              "infrastructure behind recent attacks route through commercial "
              "fronts in Hong Kong rather than known Russian channels."),
    "russia": ("  Analysts note the operation carries standard Northern Fleet "
               "planning signatures throughout; attribution is uncontested."),
}


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

        # Inject generation. Under a Mystery narrative the intelligence
        # assessment carries a subtle attribution tell.
        if "generate the next inject" in prompt_lower:
            narrative = _detect_narrative(prompt_lower)
            tell = ("\n" + _INJECT_TELLS[narrative]) if narrative in _INJECT_TELLS else ""
            return f"""```yaml
id: turn_002_inject
title: "Russian Submarine Surfaces Near UK Waters"
description: |
  A Russian Kilo-class submarine has surfaced approximately 12 nautical miles off the Orkney Islands,
  within sight of a commercial ferry. The submarine remained on the surface for approximately 15 minutes
  before submerging. This provocative act was witnessed by civilians and is already spreading on social media.

  Intelligence assessment: This is a deliberate show of force designed to intimidate and test UK response.
  The submarine is part of the larger Northern Fleet deployment.{tell}
channel: intelligence
effects:
  - metric: escalation_risk
    delta: 5..10
  - metric: domestic_stability
    delta: -3..-5
```"""

        # Diplomatic call: the counterpart persona line names the leader and
        # country, the same way advisor prompts name the addressed advisor.
        # Must run before advisor detection - the call context mentions cabinet
        # titles (e.g. the US National Security Advisor) that would otherwise
        # shadow the foreign counterpart.
        if "you are roleplaying as the" in prompt_lower:
            leader_match = _LEADER_LINE_RE.search(prompt_lower)
            country = leader_match.group(2) if leader_match else None
            player_line = _extract_player_line(prompt)
            voices = _DIPLOMACY_VOICES.get(country, _DIPLOMACY_DEFAULT)
            tone = _diplomacy_tone(player_line.lower())
            variants = voices.get(tone) or voices["general"]
            response = variants[_stable_index(player_line, len(variants))]

            # Mystery tell: appended to roughly half the exchanges. The
            # Russian ambassador never helps with attribution.
            narrative = _detect_narrative(prompt_lower)
            if (narrative in _DIPLOMACY_TELLS and country != "russia"
                    and _stable_index((country or "") + player_line, 2) == 0):
                response += " " + _DIPLOMACY_TELLS[narrative]
            return response

        # Diplomatic call outcome assessment (structured format expected)
        if "assessing the outcome of a diplomatic conversation" in prompt_lower:
            return ("OUTCOME: NEUTRAL\n"
                    "ALLIANCE_COHESION_DELTA: 0\n"
                    "SUMMARY: The call kept the channel open and clarified positions "
                    "on both sides, without securing commitments beyond continued "
                    "consultation.")

        # International actor simulation (multi-agent adjudication). Requires the
        # structured-format marker so it can't shadow the advisor pushback prompt
        # (which also opens with "You are simulating...").
        if "you are simulating" in prompt_lower and "public_response" in prompt_lower:
            code_match = re.search(r"country:\s*[^\n(]*\(([a-z]{2,3})\)", prompt_lower)
            code = code_match.group(1).upper() if code_match else ""
            variants = _ACTOR_RESPONSES.get(code, _ACTOR_DEFAULT)
            public, private, trust, support, conditions, intel = \
                variants[_stable_index(prompt, len(variants))]

            # Mystery tell: allied capitals occasionally hint that attribution
            # is wider than Moscow. Russia's responses stay on script.
            narrative = _detect_narrative(prompt_lower)
            if (narrative in _ACTOR_TELLS and code != "RUS"
                    and _stable_index(code + prompt, 2) == 0):
                public += _ACTOR_TELLS[narrative]
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
            question = _extract_question(prompt)
            variants = _ADVISOR_QA[advisor]
            response = variants[_stable_index(question, len(variants))]

            # Mystery tell: intelligence/diplomatic answers occasionally carry
            # an attribution clause consistent with the hidden narrative.
            narrative = _detect_narrative(prompt_lower)
            tells = _ADVISOR_TELLS.get(advisor, {})
            if narrative in tells and _stable_index(question, 2) == 0:
                response += tells[narrative]
            return response

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
