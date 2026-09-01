"""Mock LLM driver for deterministic testing.

Provides template-based responses for the conversational system. Mock mode is
the first-run experience (no API key configured), so the canned cabinet must
behave like a cabinet: each advisor speaks with their own voice, reactions
reference the quality of the decision, and foreign capitals respond in
character rather than with a single generic acknowledgement.

The same standard applies to the story itself: stochastic turns draw from
_INJECT_POOL rather than replaying one hardcoded event, so an offline
campaign develops instead of looping.
"""

import json
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
# Detection keys on a builder-owned marker emitted after editable and
# interpolated text, rather than on arbitrary persona-like lines in the prompt.
# The surrounding context mentions every advisor, and player text can itself
# contain identity instructions; trusting either previously collapsed voices.
# ---------------------------------------------------------------------------

# advisor key -> aliases used in persona lines (role titles and display names)
_ADVISOR_ALIASES = {
    "cds": ("military commander", "chief of the defence staff"),
    "nsa": ("national security adviser", "national security advisor",
            "intelligence coordinator"),
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

# Country alternation is derived from _DIPLOMACY_VOICES (defined below) so a
# new capital only needs a dictionary entry.
_LEADER_LINE_RE = None


def _leader_line_re():
    global _LEADER_LINE_RE
    if _LEADER_LINE_RE is None:
        countries = "|".join(re.escape(country) for country
                             in sorted(_DIPLOMACY_VOICES, key=len, reverse=True))
        _LEADER_LINE_RE = re.compile(
            r"you are roleplaying as the (.+?) of "
            r"(" + countries + r") in a crisis simulation"
        )
    return _LEADER_LINE_RE

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
# to_llm_context) reaches ONLY the roleplay prompts - diplomacy conversations
# and state-actor simulation. Player-facing prompts (advisors, injects,
# quality assessment) are segregated from the secret, so their mock output
# carries no tells; deduction runs on faction behaviour. Detection keys on
# the "Crisis Protagonist: <ISO>" line; tells are short clauses appended
# deterministically so the deduction loop is playable offline.
# ---------------------------------------------------------------------------

_NARRATIVE_PROTAGONISTS = {
    "rus": "russia", "russia": "russia",
    "chn": "china", "china": "china",
}


def _detect_narrative(prompt_lower: str):
    """Return 'russia'/'china' if a hidden narrative context block is present.

    Accepts ISO codes and full names; anything else is an explicit None so an
    unrecognised protagonist never half-matches a tell.
    """
    match = re.search(r"crisis protagonist:\s*([a-z]+)", prompt_lower)
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

# Inject description tells (appended as a final paragraph of the description).
# Deliberately domain-neutral so any pool entry below can carry one: the
# offline deduction loop depends on the tell appearing whatever the event is.
_INJECT_TELLS = {
    "china": ("**Attribution note:** Analysts flag one anomaly running through "
              "the technical picture. Elements of the financing and the cyber "
              "infrastructure behind recent attacks route through commercial "
              "fronts in Hong Kong rather than through any known Russian "
              "channel."),
    "russia": ("**Attribution note:** Analysts find standard Russian service "
               "planning signatures throughout - the tasking, the tradecraft "
               "and the timing all sit inside patterns we have seen from "
               "Moscow before. Attribution is uncontested."),
}

# ---------------------------------------------------------------------------
# Offline inject pool
#
# Mock mode is the entire experience for anyone playing without an API key,
# and it used to answer every "generate the next inject" prompt with one
# hardcoded event: the same submarine surfaced off Orkney every stochastic
# turn until the campaign ended (see dev-scripts/play-verify/transcript.ansi).
#
# The pool spans naval, infrastructure, cyber, information-operations,
# diplomatic, domestic-political and alliance-strain territory, in the voice
# of the scripted episodes (data/scenarios/war_game_2025/episodes). Selection
# is deterministic - see _select_inject.
#
# Fields:
#   id               internal key (the caller stamps the real per-turn id)
#   title            headline; kept under the ledger's 60-char truncation
#   channel          drives the on-screen tag and panel colour
#   description      YAML block-scalar body, written unindented here
#   effects          (metric, delta) pairs; deltas are "min..max" ranges
#   min_escalation   escalation risk this event needs before it can be drawn,
#                    so a calm campaign is not handed an ultimatum
# ---------------------------------------------------------------------------

_INJECT_POOL = (
    {
        "id": "cable_cut",
        "title": "Undersea Cables Severed in the Western Approaches",
        "channel": "emergency",
        "min_escalation": 0,
        "effects": (("escalation_risk", "5..8"),
                    ("domestic_stability", "-4..-6"),
                    ("alliance_cohesion", "-2..-3")),
        "description": """=== EMERGENCY BRIEFING ===

Prime Minister, at 04:12 this morning two transatlantic fibre-optic cables
failed within eleven minutes of each other in the Western Approaches, roughly
sixty miles south-west of Bude. The Irish interconnector went down forty
minutes later.

**GCHQ Bude Assessment:**
The breaks are clean, closely spaced, and at depths that rule out trawler
damage. The Russian survey vessel Yantar loitered over that corridor for
eleven hours on Thursday with her transponder off. We assess with moderate to
high confidence that this was deliberate, and that it was rehearsed.

**CDS:**
We have one survey ship and a chartered cable layer available. Repair is
weeks, not days. Protecting them means detaching an escort from the group
currently shadowing the Northern Fleet, and I cannot do both at once.

**Home Secretary:**
Financial traffic is rerouting through the remaining links, but two clearing
banks are already on contingency capacity and mobile networks across the South
West are congested. The story will be public by lunchtime, and the public will
ask what else is lying on the seabed unguarded.""",
    },
    {
        "id": "st_fergus",
        "title": "Explosion at St Fergus Gas Terminal",
        "channel": "emergency",
        "min_escalation": 55,
        "effects": (("escalation_risk", "8..12"),
                    ("domestic_stability", "-8..-12"),
                    ("casualties_civ", "3..5")),
        "description": """=== EMERGENCY BRIEFING ===

At 05:40 an explosion tore through the reception facility at the St Fergus gas
terminal in Aberdeenshire. St Fergus lands roughly a third of the United
Kingdom's gas. Two of its three processing trains are offline and the site is
isolated.

**Police Scotland, via the Home Secretary:**
Four terminal workers confirmed dead, nine injured, two of them critically.
The fire is contained. Forensic teams cannot enter for some hours yet, but the
seat of the blast is a subsea pipeline riser, not the plant.

**DESNZ and National Grid:**
Storage is thin for early October. Grid can hold the system tonight by calling
in interruptible industrial contracts. If the cold snap forecast for Thursday
arrives with the terminal still down, we are looking at three-hour rolling
disconnections and hard choices between hospitals, water treatment and homes.

**NSA:**
A Russian deep-sea unit has been mapping that riser field for three years. We
have no forensics yet and I will not pretend otherwise, but the pattern is
familiar and Moscow has left itself deniability by design.""",
    },
    {
        "id": "faroes_gap",
        "title": "Russian Bombers Probe the Faroes-Shetland Gap",
        "channel": "intelligence",
        "min_escalation": 0,
        "effects": (("escalation_risk", "4..7"),
                    ("domestic_stability", "-2..-4"),
                    ("alliance_cohesion", "2..3")),
        "description": """=== INTELLIGENCE UPDATE ===

Two Tu-95 Bear-H bombers with a supporting Il-78 tanker entered the
Faroes-Shetland gap at 02:20 and turned south, transponders dark, flying the
edge of our air defence identification zone for ninety minutes before
withdrawing north-east.

**CDS:**
Quick Reaction Alert Typhoons launched from Lossiemouth and held them
throughout. One bomber cycled a weapons bay door open and closed as our
aircraft closed - a gesture, and a message. Norwegian F-35s took the handover
at the northern limit; the Danes flew the Faroes leg.

Prime Minister, my concern is arithmetic. That is the fourth QRA launch in
thirty-six hours. Tanker availability, not airframes, is what limits us, and
we are burning through crew duty hours we cannot replace.

**NSA:**
This is data collection dressed as intimidation. They are timing our reaction,
mapping which radars illuminate them and which stay quiet, and building a
picture of exactly how long the United Kingdom can hold this posture.

**Foreign Secretary:**
Oslo and Copenhagen both flew without being asked. That is worth something,
and it is worth saying so publicly.""",
    },
    {
        "id": "nhs_ransomware",
        "title": "Ransomware Locks NHS Trusts in the North West",
        "channel": "emergency",
        "min_escalation": 0,
        "effects": (("escalation_risk", "3..5"),
                    ("domestic_stability", "-6..-9"),
                    ("casualties_civ", "1..2")),
        "description": """=== EMERGENCY BRIEFING ===

Six acute trusts across the North West lost their patient administration
systems overnight. Ambulances are diverting, three emergency departments are
running on paper, and elective surgery is cancelled across the region for at
least seventy-two hours.

**NCSC Assessment:**
The tooling belongs to a criminal ransomware crew that has operated from
Russian territory for years without ever troubling the authorities there. What
is unusual is that no ransom demand has been issued. Encrypted data is being
destroyed rather than held. This is a wiper wearing a criminal's coat.

**Home Secretary:**
Two deaths are already being linked to diverted ambulances, and the coroner
will say so in public before we are ready. Trust boards want to know whether
they are dealing with crime or with an act of war, and so does every hospital
in the country.

**Attorney General:**
Prime Minister, I must flag the distinction. Attribution to a criminal group
is not attribution to a state, however convenient the group's address. If you
intend to treat this as an armed attack, the evidential chain has to carry
that weight, and at present it does not.""",
    },
    {
        "id": "deepfake_broadcast",
        "title": "Forged Broadcast of the Prime Minister",
        "channel": "media",
        "min_escalation": 0,
        "effects": (("escalation_risk", "2..4"),
                    ("domestic_stability", "-7..-10"),
                    ("alliance_cohesion", "-2..-4")),
        "description": """=== MEDIA MONITORING - URGENT ===

A three-minute video carrying your face and your voice is spreading across
messaging apps. In it you announce the evacuation of the east coast between
the Humber and the Thames, and instruct the public to leave their homes
tonight. It is a fabrication, and it is very good.

**Home Secretary:**
Police in Grimsby, Hull and Great Yarmouth are taking calls faster than they
can answer them. The A180 is filling in both directions. The BBC and Sky have
both broadcast denials, but the correction is travelling at a fraction of the
speed of the lie, and every hour of confusion is an hour of it.

**NSA:**
Voice cloning from your published speeches, seeded on four channels within
eleven minutes of each other, then amplified by accounts we have catalogued
before. This is a rehearsed information operation, not a prank.

**Foreign Secretary:**
Three allied capitals have telephoned to ask whether the evacuation is real.
That they had to ask is itself the point of the exercise. I would rather you
were on camera within the hour than that we issue another written denial.""",
    },
    {
        "id": "moscow_ultimatum",
        "title": "Moscow Issues an Ultimatum",
        "channel": "flash_alert",
        "min_escalation": 65,
        "effects": (("escalation_risk", "12..18"),
                    ("domestic_stability", "-8..-12"),
                    ("alliance_cohesion", "3..5")),
        "description": """=== FLASH ALERT ===

The Russian Ambassador delivered a note to the Foreign Office nineteen minutes
ago and left without waiting for a reply. The text was broadcast on Russian
state television simultaneously, which tells you who it was written for.

The demands: that the United Kingdom cease what Moscow calls its support for
terrorism against the Russian Federation; that Royal Navy units withdraw
beyond the sixty-second parallel; and that Russian inspectors be admitted to
North Sea energy installations. Six hours. Failing which, the note says, the
United Kingdom "will bear the consequences in full".

**NSA:**
The deadline is the message. Six hours is not time to negotiate, it is time to
panic. They want you visibly refusing something unreasonable, or visibly
complying, and either serves them.

**CDS:**
I have moved to dispersal for the deterrent and the QRA force regardless of
your decision, and I will want that on the record. If you intend to reject
this publicly, I need thirty minutes' notice to get people off soft targets.

**Attorney General:**
Compliance under duress carries its own costs, Prime Minister. Admitting
foreign inspectors to our own critical infrastructure would be a concession no
successor government could reverse quietly.""",
    },
    {
        "id": "washington_hesitates",
        "title": "Washington Floats a Ceasefire",
        "channel": "diplomatic",
        "min_escalation": 0,
        "effects": (("escalation_risk", "2..4"),
                    ("domestic_stability", "-3..-5"),
                    ("alliance_cohesion", "-8..-12")),
        "description": """=== DIPLOMATIC TELEGRAM - WASHINGTON ===

The White House has briefed selected correspondents that the President's
national security team has opened a channel to Moscow and is exploring what
one official called an off-ramp. The United Kingdom was not consulted, and the
briefing contains no Article 5 language of any kind.

**Foreign Secretary:**
Prime Minister, we learned this from a journalist. Our Ambassador was told
forty minutes later that the President intends to speak to you "in due
course". The phrase American officials are using in private is that Europe
must own this crisis, and that the Pacific is where the President's attention
is required.

**NSA:**
Intelligence sharing on the Northern Fleet is unchanged so far, and I would
not read malice into this yet. But the moment Washington positions itself as
broker rather than ally, our leverage over Moscow becomes whatever we can
generate ourselves.

**CDS:**
Without American tankers and American satellite coverage, our sustainable
posture is roughly half of what you saw in the force tables this morning. I
would rather you knew that before you spoke to the President than after.""",
    },
    {
        "id": "commons_revolt",
        "title": "Parliament Recalled as Backbenches Turn",
        "channel": "domestic",
        "min_escalation": 0,
        "effects": (("domestic_stability", "-8..-12"),
                    ("alliance_cohesion", "-1..-3")),
        "description": """=== DOMESTIC POLITICAL BRIEF ===

The Speaker has agreed to recall the House for Thursday. Forty-seven letters
have gone to the chairman of the 1922 Committee since yesterday evening, and
two junior ministers resigned within an hour of each other this morning, one
citing insufficient resolve and the other insufficient restraint.

**Home Secretary:**
The Opposition will demand publication of the intelligence assessment in full
and a vote on any deployment. Our own benches are split three ways: those who
want the fleet sailing tonight, those who want a negotiated settlement, and
those who simply want to be somewhere else when the vote is called.

**Attorney General:**
If you intend to rely on emergency powers under the Civil Contingencies Act,
Parliament must be sitting within seven days in any event. Better to recall
them on your terms with a statement in your hand than to be dragged back on
theirs.

**Foreign Secretary:**
Allied capitals read a divided Commons the same way Moscow does. Whatever you
say at the despatch box on Thursday will be quoted in Warsaw and Berlin within
the hour, and it will be quoted selectively.""",
    },
    {
        "id": "fuel_panic",
        "title": "Fuel Queues and Empty Shelves",
        "channel": "domestic",
        "min_escalation": 0,
        "effects": (("escalation_risk", "1..3"),
                    ("domestic_stability", "-6..-9")),
        "description": """=== DOMESTIC SITUATION REPORT ===

Two in five forecourts across the South East ran dry before noon. The
supermarkets have imposed rationing on bottled water, tinned goods and
batteries without waiting to be asked. Cash withdrawals are running at four
times normal and two building societies have quietly extended their branch
hours.

**Home Secretary:**
There was a fight at a filling station outside Reading this morning and the
footage is everywhere. Chief constables want a decision on the reserve tanker
fleet and on whether we prioritise fuel for emergency services openly or
discreetly. Schools in three counties are closing tomorrow because staff
cannot get in.

**NSA:**
Queue footage is being amplified by accounts we have seen before, with
captions in English that were not written by English speakers. The shortage is
real; the panic is being farmed.

**Home Secretary:**
Prime Minister, the public has been extraordinarily steady so far. That is a
resource, and like every other resource in this crisis it is finite. They will
hold if they are told the truth early. They will not hold if they learn it
from a queue.""",
    },
    {
        "id": "gru_network",
        "title": "Counter Terrorism Command Rolls Up a Network",
        "channel": "intelligence",
        "min_escalation": 0,
        "effects": (("escalation_risk", "4..6"),
                    ("domestic_stability", "3..5"),
                    ("alliance_cohesion", "2..4")),
        "description": """=== INTELLIGENCE UPDATE ===

Overnight raids in Portsmouth, Grays and Motherwell produced eleven arrests
and, for the first time in this crisis, evidence that will survive a
courtroom.

**Security Service, via the NSA:**
Recovered from two addresses: surveillance packages on Devonport and Faslane
covering shift changes and boat movements over four months, forty pre-paid
handsets, and a lock-up containing diving equipment and two cases of
commercial detonators. Tasking ran through a freight brokerage registered in
Dubai and paid in three hops from a bank we know well.

**Home Secretary:**
Charges under the National Security Act 2023 will be laid this afternoon.
Prime Minister, this is the first unambiguously good news the public has had
since Saturday, and I would like your permission to let the Metropolitan
Police say so plainly.

**Foreign Secretary:**
Our allies have spent three days asking for evidence rather than assertion.
Here it is. I would share the package through NATO channels before we brief
the press, so that Washington hears it from us rather than from the six
o'clock news.

**NSA:**
One caution. Rolling up a network this size tends to be followed by whatever
the network was preparing for, brought forward.""",
    },
    {
        "id": "typhoon_down",
        "title": "RAF Typhoon Down over the North Sea",
        "channel": "flash_alert",
        "min_escalation": 70,
        "effects": (("escalation_risk", "15..20"),
                    ("casualties_mil", "1..2"),
                    ("domestic_stability", "-6..-10"),
                    ("alliance_cohesion", "4..6")),
        "description": """=== FLASH ALERT ===

A Typhoon on Quick Reaction Alert out of Lossiemouth is down in the North Sea,
approximately ninety miles east of Aberdeen. The last transmission from the
pilot was the single word "engaged".

**CDS, on the secure line from Northwood:**
A Russian Su-35 was inside two miles at the time. We hold radar and we hold
the audio. The pilot's personal locator beacon is transmitting; a Sea King out
of Lossiemouth and a Norwegian rescue aircraft are both en route, and the sea
state is worsening.

Prime Minister, I need a decision on rules of engagement within the hour. As
things stand our aircraft may fire only if fired upon and observed to be
fired upon. If that stands, I am sending crews to be shot at first.

**Attorney General:**
If the aircraft was engaged in international airspace, that is an armed attack
on British forces and Article 51 is available to you. If it was a collision
during an intercept, it is a catastrophe and not a casus belli. The recordings
will decide which, and I would not go before the cameras until they have.

**Foreign Secretary:**
Moscow is already denying any contact. NATO's Secretary General has asked to
speak to you. For once, Prime Minister, the alliance will be ahead of us on
this - a dead British pilot concentrates minds in a way our evidence packs
have not.""",
    },
    {
        "id": "berlin_sanctions",
        "title": "Berlin Breaks Ranks on Sanctions",
        "channel": "diplomatic",
        "min_escalation": 0,
        "effects": (("escalation_risk", "1..3"),
                    ("domestic_stability", "-2..-4"),
                    ("alliance_cohesion", "-6..-9")),
        "description": """=== DIPLOMATIC TELEGRAM - BERLIN ===

The German Chancellery informed the Foreign Office an hour ago that the
coalition will not support the energy annex of the sanctions package. Hungary
and Slovakia have said the same within the last twenty minutes, which suggests
the choreography was arranged before we were told.

**Foreign Secretary:**
Without the energy annex the package is a travel ban and a list of names.
German storage is at sixty-one per cent with the heating season starting, and
the Chancellor's partners have made it plain they will not survive a winter of
rationing for a British quarrel. Paris will hold, but Paris will also make
certain we understand what it is costing them.

**NSA:**
Moscow will read the gap between the communiqué and the measures within a day.
Every week the alliance spends arguing about annexes is a week their planners
count as a win, and they will time the next incident to arrive while we are
still counting votes in Brussels.

**Home Secretary:**
There is a domestic edge to this too. If Europe waters down the response, our
own price cap review lands in January with nothing to show for the pain.""",
    },
)

# render_event_ledger truncates a title past 60 characters to 57 chars + "...",
# so long titles are matched on the surviving prefix rather than in full.
_LEDGER_TITLE_PROBE = 57

_ESCALATION_WORDS = {"low": 15, "moderate": 45, "high": 70, "critical": 90}


def _inject_turn(prompt_lower: str) -> int:
    """Turn number the inject is being generated for (0 if unstated)."""
    for pattern in (r"generate the next inject/event for turn (\d+)",
                    r"dynamic inject generation - turn (\d+)"):
        match = re.search(pattern, prompt_lower)
        if match:
            return int(match.group(1))
    return 0


def _escalation_level(prompt_lower: str) -> int:
    """Escalation risk carried by the prompt's world state block.

    Reads the numeric line the inject context builder emits, falling back to
    the narrative wording used when there is no transcript yet. Unknown state
    returns a mid value, which admits the ordinary events and holds back the
    sharpest ones.
    """
    match = re.search(r"escalation risk:\s*(\d+)", prompt_lower)
    if match:
        return int(match.group(1))
    match = re.search(r"threat assessment:\s*(low|moderate|high|critical)", prompt_lower)
    if match:
        return _ESCALATION_WORDS[match.group(1)]
    return 50


def _mentions_title(title: str, text_lower: str) -> bool:
    """Whether a pool title appears in a stretch of prompt text."""
    probe = title.lower()
    if probe in text_lower:
        return True
    return len(probe) > _LEDGER_TITLE_PROBE and probe[:_LEDGER_TITLE_PROBE] in text_lower


def _section(prompt_lower: str, header: str) -> str:
    """The context block introduced by ``header``, up to the next blank line.

    Context sections are joined with a trailing empty string, so a blank line
    is a reliable terminator. Returns "" when the block is absent.
    """
    start = prompt_lower.find(header)
    if start == -1:
        return ""
    end = prompt_lower.find("\n\n", start)
    return prompt_lower[start:] if end == -1 else prompt_lower[start:end]


def _select_inject(prompt: str, prompt_lower: str, rng: Random) -> dict:
    """Pick a pool entry for this turn - deterministically, and not the last one.

    Three constraints, in descending order of importance:

    1. The event ledger (context_builder.render_event_ledger) is honoured:
       anything listed under EVENTS ALREADY PLAYED is not restaged. A blocked
       pick is replaced, never returned empty - an empty inject costs the
       player a whole turn, which is worse than a repeat.
    2. Nothing already visible in the prompt is drawn again, which covers the
       previous turn's inject (the LAST TURN continuity window) and the story
       digest, so a campaign works through the pool instead of looping.
    3. Sharper events need a hot campaign behind them (``min_escalation``),
       so a calm turn is not handed an ultimatum out of nowhere.

    Each constraint is relaxed in turn if it leaves nothing to choose from,
    least important first. The final choice draws from the ``rng`` the driver
    is handed, so the same seed replays the same campaign and a different seed
    tells a different story.
    """
    ledger = _section(prompt_lower, "events already played")
    last_turn = (prompt_lower.rsplit("for continuity", 1)[-1]
                 if "for continuity" in prompt_lower else "")

    def matching(text):
        return {e["id"] for e in _INJECT_POOL
                if text and _mentions_title(e["title"], text)}

    played = matching(ledger)          # hard block: already staged this campaign
    previous = matching(last_turn)     # last turn's event, ledger or no ledger
    seen = matching(prompt_lower)      # anything the prompt already mentions

    escalation = _escalation_level(prompt_lower)
    in_range = [e for e in _INJECT_POOL if e["min_escalation"] <= escalation]

    # "seen" already contains everything in "played" (the ledger is part of the
    # prompt), so the first two passes cover the ledger as well.
    candidates = (
        [e for e in in_range if e["id"] not in seen]
        or [e for e in _INJECT_POOL if e["id"] not in seen]
        or [e for e in _INJECT_POOL if e["id"] not in played and e["id"] not in previous]
        or [e for e in _INJECT_POOL if e["id"] not in previous]
        or list(_INJECT_POOL)
    )

    try:
        index = rng.randrange(len(candidates))
    except AttributeError:
        # A caller without a real Random still gets a stable, varying pick.
        index = _stable_index(prompt, len(candidates))
    return candidates[index]


def _render_inject(entry: dict, turn: int, tell: str = "") -> str:
    """Render a pool entry as the fenced YAML the inject parser expects.

    The title goes through ``json.dumps``: a JSON string literal is also a
    valid YAML double-quoted scalar, so a title containing a quote or a
    backslash escapes itself instead of breaking the document. Every title in
    the pool today is plain prose, so this is hardening against the next one
    rather than a fix for a live defect.
    """
    description = entry["description"].strip("\n")
    if tell:
        description = f"{description}\n\n{tell}"
    body = "\n".join(f"  {line}" if line.strip() else ""
                     for line in description.split("\n"))
    effects = "\n".join(f"  - metric: {metric}\n    delta: {delta}"
                        for metric, delta in entry["effects"])
    return ("```yaml\n"
            f"id: turn_{turn:03d}_inject\n"
            f"title: {json.dumps(entry['title'])}\n"
            "description: |\n"
            f"{body}\n"
            f"channel: {entry['channel']}\n"
            "effects:\n"
            f"{effects}\n"
            "```")


def _detect_advisor(prompt_lower: str):
    """Return the advisor named by trusted builder or reaction framing."""
    selected = None
    selected_at = -1
    for key, aliases in _ADVISOR_ALIASES.items():
        for alias in aliases:
            role = re.escape(alias)
            patterns = (
                r"(?m)^\s*\[advisor role:\s*(?:the )?(?:uk )?(?:us )?"
                + role + r"\s*\]\s*$",
                r"(?m)^\s*you are (?:the )?(?:uk )?(?:us )?" + role
                + r"\.\s*\n\s*your relationship with the pm:",
            )
            for pattern in patterns:
                for match in re.finditer(pattern, prompt_lower):
                    if match.start() > selected_at:
                        selected = key
                        selected_at = match.start()
    return selected


def _extract_question(prompt: str) -> str:
    """Pull the player's question out of an advisor Q&A prompt, if present."""
    match = re.search(r'the prime minister asks:\s*"(.*?)"', prompt, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else prompt


def _extract_quoted_prompt_value(
    prompt: str,
    heading: str,
    *following_headings: str,
):
    """Extract a quoted prompt field, including embedded quotes/newlines."""
    boundaries = "|".join(
        re.escape(following) for following in following_headings)
    match = re.search(
        re.escape(heading) + r'\s*"(.*?)"\s*'
        r'(?=(?:' + boundaries + r')|\Z)',
        prompt,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else None


def _extract_tasked_forces(action: str) -> str:
    """Return assets explicitly tasked by the submitted decision."""
    # ponytail: this deliberately recognises only directive clauses containing
    # a finite vocabulary of obvious military assets. Unknown euphemisms fail
    # closed; use the unit registry if that ceiling ever needs lifting.
    action = re.sub(
        r"((?:\band|\bor)|,)[^\S\r\n]*\r?\n[^\S\r\n]*",
        r"\1 ",
        action,
        flags=re.IGNORECASE,
    )
    action = re.sub(r"[^\S\r\n]*\r?\n[^\S\r\n]*", "; ", action)
    action = " ".join(action.split())
    tasking_verb = (
        r"(?:activate|assign|authorise|authorize|commit|deploy|detach|dispatch|"
        r"divert|escort|keep|launch|mobilise|mobilize|move|order|position|put|"
        r"ready|redeploy|reinforce|reroute|retask|sail|scramble|send|station|"
        r"surge|task(?!\s+force\b)|use(?!\s+of force\b))"
    )
    negation = (
        r"(?:do not|don['’]t|will not|won['’]t|cannot|can['’]t|not(?:\s+to)?|"
        r"never|no|refuse to|without|avoid)"
    )
    action = re.sub(
        rf"\b(?P<negated>{negation}),\s*under any circumstances,\s*"
        rf"(?P<verb>{tasking_verb})\b",
        r"\g<negated> \g<verb>",
        action,
        flags=re.IGNORECASE,
    )
    asset = (
        r"(?:\b(?:HMS|RAF|RNAS|SSBNs?|SSNs?|CAP|carriers?|destroyers?|"
        r"frigates?|submarines?|squadrons?|aircraft|jets?|fighters?|"
        r"helicopters?|drones?|warships?|ships?|fleet|forces|troops?|"
        r"marines?|patrols?|Poseidons?|Typhoons?|Wedgetails?)\b|"
        r"\b(?:Type\s*-?\s*\d+|[PFE]\s*-?\s*\d+[A-Z]?)\b)"
    )
    clauses = re.split(
        rf"(?:[;.!?]+|"
        rf",\s*(?:and|but)\s+(?:(?:instead|then)\s+)?"
        rf"(?=(?:{negation}\s+)?{tasking_verb}\b)|"
        rf",\s*(?=(?:{negation}\s+)?{tasking_verb}\b)|"
        rf"\s+(?:and|but)\s+(?:(?:instead|then)\s+)?"
        rf"(?=(?:{negation}\s+)?{tasking_verb}\b))",
        action,
        flags=re.IGNORECASE,
    )
    forces = []
    for clause in clauses:
        directive = re.match(
            rf"^(?P<negated>{negation}\s+)?{tasking_verb}\s+(?P<object>.+)$",
            clause.strip(),
            re.IGNORECASE,
        )
        if not directive or directive.group("negated"):
            continue
        tasked_object = directive.group("object")
        force_match = re.match(
            r"(.+?)(?=\s+(?:at|for|in|into|near|off|on|over|to|toward|"
            r"towards|under)\b|$)",
            tasked_object,
            re.IGNORECASE,
        )
        for force in force_match.group(1).split(","):
            force = " ".join(force.split()).strip(" \"'")
            force = re.split(
                rf"\s+(?:(?:but|and)\s+(?:{negation}|except|other\s+than)|"
                r"without|except|other\s+than)\b",
                force,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip()
            if re.match(
                    r"(?:not|(?:but|and)\s+not|other than|except)\b",
                    force,
                    re.IGNORECASE):
                continue
            if re.search(rf"\b{negation}\b", force, re.IGNORECASE):
                continue
            if re.search(asset, force, re.IGNORECASE):
                forces.append(force)
    return ", ".join(force for force in forces if force) or "None specified"


class MockDeterministicDriver:
    """Deterministic mock LLM driver for testing.

    Generates template-based responses that are deterministic given the same
    prompt (variant choice hashes the question/prompt, not process state).
    """

    def generate_text(self, prompt: str, rng: Random, **kwargs) -> str:
        """Generate mock response based on prompt structure and keywords.

        Args:
            prompt: Input prompt
            rng: Random number generator (for future use)
            **kwargs: Generation options (system_instruction, temperature,
                max_tokens) accepted and ignored, so the router forwards
                uniformly to every driver

        Returns:
            Mock response text
        """
        _ = kwargs
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
            decided = _extract_quoted_prompt_value(
                prompt, "the prime minister has decided:", "IMPORTANT:")
            normalised_decision = " ".join((decided or "").split())
            summary = normalised_decision if decided is not None else \
                "Deploy naval and air assets to defensive posture"
            forces = _extract_tasked_forces(decided or "")
            return (f"INTERPRETATION: {summary}\n"
                    f"FORCES INVOLVED: {forces}\n"
                    "RESOURCES CONSUMED: Minimal (patrol operations)\n"
                    "TIMELINE: Immediate (within 1 turn)\n"
                    "FEASIBILITY: Feasible within current constraints")

        # Pushback generation. Trigger keywords are matched against the PM's
        # actual decision text, not the whole prompt - the surrounding context
        # (force listings, transcript) mentions "deploy"/"carrier" on every
        # turn and would otherwise fire pushback for every decision.
        if "pushback triggers" in prompt_lower:
            decided = _extract_quoted_prompt_value(
                prompt, "the pm has decided:",
                "Interpretation of this action:",
                "Advisors and their pushback triggers:")
            # Fail closed: if the decision can't be extracted, don't scan the
            # whole prompt - its context mentions deploy/carrier every turn
            # and would fire spurious pushback.
            if decided is None:
                return "[ERROR: Advisor response unavailable]"
            action_text = decided.lower()
            advisor = _detect_advisor(prompt_lower)

            if "nuclear" in action_text:
                if advisor == "legal":
                    return ("Prime Minister, nuclear first-use without imminent "
                            "existential threat violates our legal framework and "
                            "would fracture NATO immediately.")
                if advisor == "foreign":
                    return "This would end US support and isolate us internationally."
                if advisor is None:  # Legacy direct mock probe.
                    return ("Attorney General: Prime Minister, nuclear first-use "
                            "without imminent existential threat violates our legal "
                            "framework and would fracture NATO immediately.\n"
                            "Foreign Secretary: This would end US support and "
                            "isolate us internationally.")
                return "NO PUSHBACK"

            if "deploy" in action_text and ("carrier" in action_text or "prince of wales" in action_text):
                if advisor == "cds":
                    return ("Prime Minister, HMS Prince of Wales is not at highest "
                            "readiness. We can surge her immediately at reduced "
                            "capability, or wait 3 turns for full readiness.")
                if advisor is None:  # Legacy direct mock probe.
                    return ("Chief of the Defence Staff: Prime Minister, HMS Prince "
                            "of Wales is not at highest readiness. We can surge her "
                            "immediately at reduced capability, or wait 3 turns for "
                            "full readiness.")
                return "NO PUSHBACK"

            return "NO PUSHBACK"

        # Critical omissions check: the mock cabinet raises no blocking concerns
        if "critical omissions check" in prompt_lower:
            return "NO_CONCERN"

        # Inject generation. One event is drawn from _INJECT_POOL per turn:
        # deterministic, never the previous turn's, never one the event
        # ledger says has already played. Under a Mystery narrative the
        # description carries a subtle attribution tell.
        if "generate the next inject" in prompt_lower:
            entry = _select_inject(prompt, prompt_lower, rng)
            narrative = _detect_narrative(prompt_lower)
            return _render_inject(entry, _inject_turn(prompt_lower),
                                  _INJECT_TELLS.get(narrative, ""))

        # Diplomatic call: the counterpart persona line names the leader and
        # country, the same way advisor prompts name the addressed advisor.
        # Must run before advisor detection - the call context mentions cabinet
        # titles (e.g. the US National Security Advisor) that would otherwise
        # shadow the foreign counterpart.
        if "you are roleplaying as the" in prompt_lower:
            leader_match = _leader_line_re().search(prompt_lower)
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
                public = f"{public.rstrip()} {_ACTOR_TELLS[narrative].lstrip()}"
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

    def batch_generate_text(self, prompts: list[str], rng: Random, **kwargs) -> list[str]:
        """Generate multiple mock responses in parallel (simulated).

        Args:
            prompts: List of prompt texts
            rng: Random number generator
            **kwargs: Generation options (max_tokens) accepted and ignored

        Returns:
            List of mock responses in same order as prompts
        """
        _ = kwargs
        # For mock driver, just call generate_text sequentially
        # (No actual parallelism needed for testing)
        return [self.generate_text(prompt, rng) for prompt in prompts]
