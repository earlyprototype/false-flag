"""Conversational advisor system using LLM to generate in-character responses.

Replaces the old hardcoded AdvisorProposal system with free-form Q&A.
"""

import re
import unicodedata
from random import Random
from typing import Any, Dict, List, Optional, Set, Tuple

from models.world import WorldState
from llm.prompts import (
    build_advisor_context,
    build_decision_interpretation_prompt,
    build_pushback_prompt,
    build_critical_omissions_prompt
)
from llm.model_config import LLMContext
from llm.fanout import generate_group
from llm.parse_health import record_fallback, record_miss, record_residue
from llm.parsing import (
    extract_label,
    is_error_response,
    is_sentinel_line,
    strip_decoration,
)
from engine.initial_conditions import (
    PLAYER_CHARACTER_ID,
    get_all_uk_advisors,
    get_character_info,
)


# Common title variants advisors are referred to by in LLM output,
# keyed by character id. Used to recognise "Role: message" pushback lines.
_ADVISOR_ROLE_ALIASES: Dict[str, List[str]] = {
    "prime_minister": ["prime minister", "pm", "government leader"],
    "chief_defence_staff": [
        "chief of the defence staff", "chief defence staff", "cds",
        "military commander",
    ],
    "national_security_advisor": [
        "national security advisor", "national security adviser", "nsa",
        "intelligence coordinator",
    ],
    "home_secretary": ["home secretary", "domestic security"],
    "foreign_secretary": ["foreign secretary", "diplomatic lead"],
    "attorney_general": ["attorney general", "legal advisor"],
}


# Words that mark a leading "Title, ..." prefix as an address to a specific
# official (as opposed to ordinary sentence openers like "Ok," or "Overall,").
# Used to catch questions aimed at advisors who are not in the room.
_TITLE_WORDS = {
    "chancellor", "secretary", "minister", "advisor", "adviser", "general",
    "chief", "commander", "admiral", "marshal", "director", "ambassador",
    "governor", "president", "chairman", "whip", "staff",
}

# Leading address: optional "the", then a short title, optional speech verb,
# and punctuation — e.g. "Chancellor, ..." or "Foreign Secretary says: ...".
_ADDRESS_RE = re.compile(
    r"^\s*(?:the\s+)?([A-Za-z][A-Za-z '\-]{1,40}?)"
    r"\s*(?:[*_`]+\s*)?"
    r"(?:\s+(says?|said|speaks?|speaking|respond(?:s|ed|ing)?|"
    r"repl(?:y|ies|ied|ying))\s*(?:[*_`]+\s*)?)?"
    r"([,;:–—-])"
)

_PUSHBACK_SEPARATORS = ",;:\u2013\u2014-"
_NO_PUSHBACK_PATTERN = (
    r"(?<![A-Za-z0-9])NO(?:\s+|_)PUSHBACK(?![A-Za-z0-9])")
_PUSHBACK_SENTINEL_WRAPPERS = {
    "(": ")", "[": "]", "\"": "\"", "'": "'", "`": "`",
    "\u201c": "\u201d", "\u2018": "\u2019",
    "*": "*", "**": "**", "***": "***",
    "_": "_", "__": "__", "___": "___",
}
_PUSHBACK_SENTINEL_OPENERS = {
    char for wrapper in _PUSHBACK_SENTINEL_WRAPPERS for char in wrapper
}
_PUSHBACK_SENTINEL_DECORATION = _PUSHBACK_SENTINEL_OPENERS | {
    char
    for wrapper in _PUSHBACK_SENTINEL_WRAPPERS.values()
    for char in wrapper
}
# Invisible non-Cf ranges rejected at this plain-text protocol boundary.
_INVISIBLE_UNICODE_RANGES = (
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180D),
    (0x180F, 0x180F),
    (0x2065, 0x2065),
    (0x2800, 0x2800),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0xE0000, 0xE0FFF),
)
_PUSHBACK_ATTRIBUTION_TRIM = " \t*_`\"'\u2018\u2019\u201c\u201d"
_PUSHBACK_SPEECH_LABELS = {
    "advise", "advised", "advises", "advising",
    "argue", "argued", "argues", "arguing",
    "assert", "asserted", "asserting", "asserts",
    "caution", "cautioned", "cautioning", "cautions",
    "contend", "contended", "contending", "contends",
    "declare", "declared", "declares", "declaring",
    "insist", "insisted", "insisting", "insists",
    "maintain", "maintained", "maintaining", "maintains",
    "note", "noted", "notes", "noting",
    "object", "objected", "objecting", "objects",
    "observe", "observed", "observes", "observing",
    "push-back", "pushed-back", "pushes-back", "pushing-back",
    "recommend", "recommended", "recommending", "recommends",
    "replied", "replies", "reply", "replying",
    "respond", "responded", "responding", "responds",
    "said", "say", "saying", "says",
    "speak", "speaking", "speaks", "spoke",
    "state", "stated", "states", "stating",
    "urge", "urged", "urges", "urging",
    "warn", "warned", "warning", "warns",
}
_PUSHBACK_FINITE_SPEECH_LABELS = {
    label for label in _PUSHBACK_SPEECH_LABELS
    if label.endswith(("ed", "s"))
    or label in {"pushed-back", "pushes-back", "said", "spoke"}
}
_PUSHBACK_NARRATIVE_SPEECH_LABELS = (
    _PUSHBACK_FINITE_SPEECH_LABELS | {"told"}
)
_PUSHBACK_ATTRIBUTION_MODIFIERS = {
    "again", "also", "now", "quite", "still", "then", "very",
}
_PUSHBACK_AUXILIARIES = {
    "am", "are", "can", "cannot", "could", "did", "do", "does", "had",
    "has", "have", "is", "may", "might", "must", "shall", "should", "was",
    "were", "will", "would",
}
_PUSHBACK_PREDICATE_HEADS = _PUSHBACK_AUXILIARIES | {
    "appeared", "appears", "became", "becomes", "felt", "feels", "looked",
    "looks", "remained", "remains", "seemed", "seems",
}
# Deliberately conservative: ambiguous wrapped-role text fails visibly unless
# it clearly continues an ordinary sentence with one of these predicates.
_PUSHBACK_ORDINARY_PREDICATES = {
    "accepted", "accepts", "agreed", "agrees", "believed", "believes",
    "considered", "considers", "continued", "continues", "doubted", "doubts",
    "endorsed", "endorses", "expected", "expects", "faced", "faces",
    "favored", "favors", "favoured", "favours", "finds", "found", "held",
    "holds", "knew", "knows", "made", "makes", "meant", "means", "needed",
    "needs", "opposed", "opposes", "preferred", "prefers", "questioned",
    "questions", "rejected", "rejects", "reported", "reports", "shared",
    "shares", "stood", "supports", "supported", "thinks", "thought", "told",
    "understands", "understood", "wanted", "wants",
}
_PUSHBACK_CLAUSE_STARTERS = {
    "a", "an", "he", "her", "his", "how", "i", "it", "no", "our", "she",
    "that", "the", "their", "these", "they", "this", "those", "we", "what",
    "when", "where", "which", "who", "why", "yes", "you", "your",
}

# Lowercase connectives that appear inside natural titles ("Chancellor of the
# Exchequer", "Minister for the Armed Forces") and must not defeat the
# title-case test in _detect_unknown_addressee.
_TITLE_CONNECTIVES = {"of", "the", "for", "and", "to"}
_ROLE_PREFIX_OPEN = r"(?:(?:[*_`]{1,3}|[\"'\u201c\u2018]|\(|\[)){0,2}"
_ROLE_PREFIX_CLOSE = r"(?:(?:[*_`]{1,3}|[\"'\u201d\u2019]|\)|\])){0,2}"
_TITLE_PREFIX_RE = re.compile(
    rf"^(?:(?i:the)\s+)?{_ROLE_PREFIX_OPEN}"
    r"([A-Z][A-Za-z'\-]*"
    r"(?:\s+(?:of|the|for|and|to|[A-Z][A-Za-z'\-]*)){0,5})"
    rf"{_ROLE_PREFIX_CLOSE}"
)
_EXPLICIT_ATTRIBUTION_TITLE_PREFIX_RE = re.compile(
    _TITLE_PREFIX_RE.pattern,
    re.IGNORECASE,
)

# The FLASH-tier pushback model sometimes leaks game time into the fiction
# ("we tried this in Turn 2"). The prompt now forbids it
# (llm.prompts.ADVISOR_VOICE_INSTRUCTIONS), and this display-side belt
# rewrites any survivor deterministically: "turn N" -> "day N", the
# in-fiction clock the voice instructions teach ("two days ago").
_TURN_REFERENCE_RE = re.compile(r"\bturn (\d+)\b", re.IGNORECASE)


def _scrub_turn_references(text: str) -> str:
    """Replace 'turn N' with 'day N' in advisor-voiced display text."""
    return _TURN_REFERENCE_RE.sub(r"day \1", text)


# The cabinet titles the fiction seats around the COBRA table (matches /menu)
_COBRA_ROSTER = (
    "the National Security Advisor, the Chief of the Defence Staff, the "
    "Foreign Secretary, the Home Secretary and the Attorney General"
)


def _detect_unknown_addressee(question: str, known_roles: Set[str]) -> Optional[str]:
    """Return the addressed title if the player named an advisor who isn't present.

    A question like "Chancellor, what do you think?" addresses an official the
    roster doesn't contain; silently rerouting it to another advisor reads as
    a bug. Only title-shaped prefixes trigger (see _TITLE_WORDS), so ordinary
    openers ("Right, ...") never match.
    """
    match = _ADDRESS_RE.match(question)
    if not match:
        return None
    candidate = match.group(1).strip()
    words = candidate.split()
    # A real address is title-cased ("Defence Secretary, ..."); this keeps
    # sentence openers like "General question, ..." from matching. Lowercase
    # connectives are ignored so "Chancellor of the Exchequer, ..." matches.
    significant = [w for w in words if w.lower() not in _TITLE_CONNECTIVES]
    if not significant or not all(w[0].isupper() for w in significant):
        return None
    normalized = candidate.lower()
    if normalized in known_roles:
        return None
    if set(normalized.split()) & _TITLE_WORDS:
        return candidate
    return None


def _question_matches_keyword(question_lower: str, keyword: str) -> bool:
    """Match a routing keyword against the question using word boundaries.

    Prevents short keywords like "us" from matching inside words such as
    "Russia" or "status", while multi-word phrases still match as phrases.
    """
    return re.search(r"\b" + re.escape(keyword) + r"\b", question_lower) is not None


def _known_pushback_roles(initial_conditions: Dict[str, Any]) -> Set[str]:
    """Build every role prefix recognised in per-advisor pushback."""
    roles: Set[str] = set()
    for aliases in _ADVISOR_ROLE_ALIASES.values():
        roles.update(aliases)

    player = get_character_info(initial_conditions, PLAYER_CHARACTER_ID) or {}
    player_role = player.get("role", "") if isinstance(player, dict) else ""
    if player_role:
        roles.add(player_role.strip().lower())

    uk_advisors = get_all_uk_advisors(initial_conditions)
    for char_id, char_info in uk_advisors.items():
        roles.add(char_id.replace("_", " ").lower())
        role = char_info.get("role", "")
        if role:
            roles.add(role.strip().lower())

    return roles


def _detect_unknown_pushback_role(
    line: str,
    known_roles: Set[str],
    *,
    explicit_attribution: bool = False,
) -> Optional[str]:
    """Return an unseated, title-shaped role at the start of a reply."""
    title_prefix_re = (
        _EXPLICIT_ATTRIBUTION_TITLE_PREFIX_RE
        if explicit_attribution else _TITLE_PREFIX_RE
    )
    match = title_prefix_re.match(line)
    if match is None:
        return None
    candidate = match.group(1).strip()
    normalized = candidate.lower()
    if normalized in known_roles:
        return None
    significant = [
        word for word in normalized.split()
        if word not in _TITLE_CONNECTIVES
    ]
    if not set(significant) & _TITLE_WORDS:
        return None
    if explicit_attribution and candidate[0].islower():
        words = normalized.split()
        simple_title = (
            len(significant) <= 2 and significant[-1] in _TITLE_WORDS
        )
        connector_title = (
            words[0] in _TITLE_WORDS
            and 3 <= len(words) <= 5
            and words[1] in {"of", "for", "to"}
        )
        if not simple_title and not connector_title:
            return None
    if explicit_attribution:
        return candidate
    tail = line[match.end():]
    if _split_pushback_prefix_tail(tail, known_roles) is not None:
        return candidate
    if _is_structural_pushback_tail(
            tail,
            sentence_subject=match.group(0).lower().startswith("the ")):
        return candidate
    return None


def _is_structural_pushback_tail(
    tail: str,
    *,
    sentence_subject: bool = False,
) -> bool:
    """Recognise speaker framing without classifying ordinary prose."""
    cleaned = tail.strip().lstrip(")]}'\"*_`").lstrip()
    if cleaned.startswith("."):
        return bool(cleaned[1:].strip())
    if cleaned.startswith(("(", "[")):
        closing = ")" if cleaned[0] == "(" else "]"
        end = cleaned.find(closing, 1)
        if 0 < end <= 81:
            cleaned = cleaned[end + 1:].lstrip("*_` \t")
            continuation = re.match(
                r"^([A-Za-z]+)(?:\s+([A-Za-z]+))?", cleaned)
            if not sentence_subject or not cleaned or cleaned[0].isupper():
                return True
            if continuation is None:
                return True
            first = continuation.group(1).lower()
            second = continuation.group(2)
            if ("?" in cleaned
                    or first in _PUSHBACK_CLAUSE_STARTERS
                    or (first in _PUSHBACK_AUXILIARIES and second is not None
                        and (second[0].isupper()
                             or second.lower()
                             in _PUSHBACK_CLAUSE_STARTERS))
                    or (second is not None
                        and first not in _PUSHBACK_PREDICATE_HEADS
                        and second.lower() in _PUSHBACK_PREDICATE_HEADS)
                    or (first not in _PUSHBACK_PREDICATE_HEADS
                        and first not in _PUSHBACK_ORDINARY_PREDICATES)):
                return True
        else:
            return True

    label = re.match(r"^([A-Za-z]+(?:-[A-Za-z]+)*)\b", cleaned)
    if (label is not None
            and label.group(1).lower() in _PUSHBACK_SPEECH_LABELS):
        return True

    leading_words: List[str] = []
    end = 0
    for word_match in re.finditer(r"[A-Za-z]+(?:-[A-Za-z]+)*", cleaned):
        if re.search(r"[^\s*_`]", cleaned[end:word_match.start()]):
            break
        word = word_match.group(0)
        normalized = word.lower()
        if (normalized not in _PUSHBACK_SPEECH_LABELS
                and normalized not in _PUSHBACK_ATTRIBUTION_MODIFIERS
                and not normalized.endswith("ly")):
            break
        leading_words.append(word)
        end = word_match.end()
    if _is_pushback_attribution(leading_words):
        return True

    separator = re.search(
        r"[:;](?=\s|$)|[\u2013\u2014]|\s-(?=\s|$)", cleaned)
    if (separator is None
            or re.search(r"[,.!?]", cleaned[:separator.start()])):
        return False

    words = re.findall(
        r"[A-Za-z]+(?:-[A-Za-z]+)*", cleaned[:separator.start()])
    return _is_pushback_attribution(words)


def _is_pushback_attribution(words: List[str]) -> bool:
    """Return whether words form one speech verb plus modifiers."""
    speech_words = [
        word for word in words if word.lower() in _PUSHBACK_SPEECH_LABELS
    ]
    return len(speech_words) == 1 and all(
        word.lower() in _PUSHBACK_SPEECH_LABELS
        or word.lower() in _PUSHBACK_ATTRIBUTION_MODIFIERS
        or word.lower().endswith("ly")
        for word in words
    )


def _find_pushback_failure_marker(text: str) -> Optional[str]:
    """Return an embedded provider error or pushback sentinel."""
    for bracket in re.finditer(r"\[", text):
        marker = text[bracket.start():]
        if is_error_response(marker):
            return marker
    sentinel = re.search(_NO_PUSHBACK_PATTERN, text)
    if sentinel is not None:
        suffix = text[sentinel.end():].lstrip()
        while suffix and suffix[0] in _PUSHBACK_SENTINEL_DECORATION:
            suffix = suffix[1:].lstrip()
        if not suffix or not suffix[0].isalnum():
            return "NO PUSHBACK"
    return None


def _has_invisible_unicode(text: str) -> bool:
    """Return whether invisible Unicode formatting can alter visible text."""
    for char in text:
        if unicodedata.category(char) == "Cf":
            return True
        codepoint = ord(char)
        if any(start <= codepoint <= end
               for start, end in _INVISIBLE_UNICODE_RANGES):
            return True
    return False


def _split_leading_pushback_sentinel(text: str) -> Optional[str]:
    """Return text after a leading no-pushback sentinel, if present."""
    cleaned = re.sub(
        r"^(?:(?:[-\u2013\u2014>#\u2022]|\d+[.)])\s+)",
        "", text.strip(), count=1)
    match = re.search(_NO_PUSHBACK_PATTERN, cleaned, re.IGNORECASE)
    if match is None:
        return None
    prefix = cleaned[:match.start()].strip()
    tail = cleaned[match.end():].strip()
    if prefix:
        close = _PUSHBACK_SENTINEL_WRAPPERS.get(prefix)
        if close is None:
            return None
        if tail.startswith(close):
            tail = tail[len(close):]
        elif tail.endswith(close):
            tail = tail[:-len(close)]
        else:
            return None
    return tail.strip()


def _is_no_pushback_rationale_clause(clause: str) -> bool:
    """Recognise a bounded statement that no pushback condition applies."""
    if re.fullmatch(r"[A-Za-z\s]+", clause) is None:
        return False
    words = re.findall(r"[a-z]+", clause.lower())
    if not words or set(words) & {
        "and", "but", "however", "yet", "although", "though", "because",
        "while", "despite", "nevertheless", "still", "except", "greater",
        "more", "stronger", "graver", "than", "if", "unless", "apart",
        "even",
    }:
        return False

    protocol_terms = {
        "pushback", "trigger", "triggers", "concern", "concerns",
        "objection", "objections", "reservation", "reservations",
        "warning", "warnings",
    }
    modifiers = {
        "the", "my", "our", "your", "any", "listed", "stated",
        "relevant", "applicable", "current", "active", "remaining",
        "known", "identified", "pushback",
    }
    def has_only_context(rest: List[str]) -> bool:
        if not rest:
            return True
        return re.fullmatch(
            r"(?:here|"
            r"(?:about|for|in|by|to|on) (?:this|the) "
            r"(?:decision|action|proposal|course|case|situation|order)|"
            r"(?:under|within) (?:my|our|this|the) "
            r"(?:remit|criteria|rules|scope))",
            " ".join(rest),
        ) is not None

    def find_protocol_subject(start: int, stop: int) -> Optional[int]:
        for index in range(start, min(stop, len(words))):
            if words[index] not in protocol_terms:
                continue
            if (words[index] == "pushback"
                    and words[index + 1:index + 2]
                    in (["trigger"], ["triggers"])):
                continue
            return index
        return None

    if re.fullmatch(
            r"(?:this|the) "
            r"(?:decision|action|proposal|course|case|situation|order) "
            r"(?:does|did) not (?:activate|trigger) "
            r"(?:any of )?(?:my|our|the) "
            r"(?:pushback )?(?:trigger|triggers)",
            " ".join(words)):
        return True

    if words[0] in {"no", "none"}:
        subject = find_protocol_subject(1, 7)
        if subject is None:
            return False
        prefix = words[1:subject]
        if words[0] == "no":
            if any(word not in modifiers for word in prefix):
                return False
        elif (not prefix or prefix[0] != "of"
              or any(word not in modifiers for word in prefix[1:])):
            return False
        predicate = words[subject + 1:]
        if not predicate:
            return False
        if predicate[0] in {
                "apply", "applies", "arise", "arises", "exist", "exists",
                "remain", "remains"}:
            return has_only_context(predicate[1:])
        if predicate[0] in {"activated", "triggered"}:
            return has_only_context(predicate[1:])
        if (len(predicate) >= 2
                and predicate[0] in {"is", "are", "was", "were"}
                and predicate[1] in {
                    "activated", "triggered", "applicable", "present",
                }):
            return has_only_context(predicate[2:])
        if (len(predicate) >= 3
                and predicate[0] in {"has", "have"}
                and predicate[1] == "been"
                and predicate[2] in {"activated", "triggered"}):
            return has_only_context(predicate[3:])
        return False

    if words[0] == "i" and words[1:3] in (["have", "no"], ["see", "no"]):
        subject = find_protocol_subject(3, 9)
        return (
            subject is not None
            and all(word in modifiers for word in words[3:subject])
            and has_only_context(words[subject + 1:])
        )

    if words[0] == "nothing":
        actions = {
            "raise", "raises", "trigger", "triggers", "warrant",
            "warrants", "create", "creates", "constitute", "constitutes",
        }
        cursor = 1
        if words[cursor:cursor + 1] == ["here"]:
            cursor += 1
        if cursor >= len(words) or words[cursor] not in actions:
            return False
        cursor += 1
        if words[cursor:cursor + 1] in (["a"], ["an"], ["any"]):
            cursor += 1
        return (
            cursor < len(words)
            and words[cursor] in protocol_terms
            and has_only_context(words[cursor + 1:])
        )
    return False


def _is_no_pushback_rationale(text: str) -> bool:
    """Accept only explicit absence/non-applicability rationale."""
    text = re.sub(r"^[,.\-\u2013\u2014]+\s*", "", text.strip())
    wrapped = re.fullmatch(r"\((.*)\)[,.]?", text, re.DOTALL)
    if wrapped is not None:
        text = wrapped.group(1).strip()
    if re.fullmatch(r"[A-Za-z\s,.]*", text) is None:
        return False
    clauses = [
        clause.strip()
        for clause in re.split(r"[,.\r\n]+", text)
        if clause.strip()
    ]
    return not clauses or all(
        _is_no_pushback_rationale_clause(clause) for clause in clauses)


def _split_pushback_narrative_tail(
    cleaned: str,
    known_roles: Set[str],
) -> Optional[Tuple[str, bool, bool]]:
    """Split an ``As the ROLE has warned, ...`` reference clause."""
    comma = cleaned.find(",")
    if comma <= 0:
        return None
    clause = cleaned[:comma]

    word_matches = list(re.finditer(
        r"[A-Za-z]+(?:-[A-Za-z]+)*", clause))
    words = [match.group(0) for match in word_matches]
    speech_index = next((
        index for index, word in enumerate(words)
        if word.lower() in _PUSHBACK_NARRATIVE_SPEECH_LABELS
    ), None)
    if speech_index is None or not all(
        word.lower() in _PUSHBACK_AUXILIARIES
        or word.lower() in _PUSHBACK_ATTRIBUTION_MODIFIERS
        or word.lower().endswith("ly")
        for word in words[:speech_index]
    ):
        return None
    post_speech = clause[word_matches[speech_index].end():]
    if re.search(r"[:;.!?\u2013\u2014]|\s-(?=\s|$)", clause):
        return None
    for as_match in re.finditer(r"\bas\b", post_speech, re.IGNORECASE):
        candidate, _has_article = _normalize_pushback_attribution_target(
            post_speech[as_match.end():], known_roles)
        if (_extract_pushback_prefix(candidate, known_roles) is not None
                or _detect_unknown_pushback_role(
                    candidate, known_roles, explicit_attribution=True)):
            return None
    return cleaned[comma + 1:].lstrip("*_` \t"), False, True


def _split_pushback_prefix_tail(
    tail: str,
    known_roles: Set[str],
) -> Optional[Tuple[str, bool, bool]]:
    """Split one unambiguous speaker prefix without consuming prose."""
    cleaned = tail.strip().lstrip(")]}'\"*_`").lstrip()
    if not cleaned or cleaned == ".":
        return "", True, False
    if cleaned[0] in _PUSHBACK_SEPARATORS:
        return cleaned[1:].lstrip("*_` \t"), True, False

    # A stage direction alone, e.g. ``[quietly]:``.
    if cleaned[0] in "([":
        closing = ")" if cleaned[0] == "(" else "]"
        end = cleaned.find(closing, 1)
        if 0 < end <= 81:
            rest = cleaned[end + 1:].lstrip("*_` \t")
            if rest and rest[0] in _PUSHBACK_SEPARATORS:
                return rest[1:].lstrip("*_` \t"), False, False
        return None

    narrative = _split_pushback_narrative_tail(cleaned, known_roles)
    if narrative is not None:
        return narrative

    # One speech-attribution token, optionally hyphenated and followed by a
    # short stage direction: ``warns:``, ``pushes-back:``, ``says (quietly):``.
    index = 0
    while index < len(cleaned) and cleaned[index].isalpha():
        index += 1
    while (index + 1 < len(cleaned)
           and cleaned[index] == "-"
           and cleaned[index + 1].isalpha()):
        index += 1
        while index < len(cleaned) and cleaned[index].isalpha():
            index += 1
    if index == 0:
        return None

    label = cleaned[:index].lower()
    if label not in _PUSHBACK_SPEECH_LABELS:
        return None

    rest = cleaned[index:].lstrip()
    if rest.startswith(("(", "[")):
        closing = ")" if rest[0] == "(" else "]"
        end = rest.find(closing, 1)
        if not 0 < end <= 81:
            return None
        rest = rest[end + 1:].lstrip("*_` \t")
    if rest and rest[0] in _PUSHBACK_SEPARATORS:
        is_narrative_attribution = (
            label in _PUSHBACK_FINITE_SPEECH_LABELS and rest[0] == ",")
        return (
            rest[1:].lstrip("*_` \t"), False,
            is_narrative_attribution,
        )
    return None


def _extract_pushback_prefix(
    line: str,
    known_roles: Set[str],
) -> Optional[Tuple[str, Optional[str], bool, bool, bool]]:
    """Return a role prefix, remainder, and attribution flags."""
    for known_role in sorted(known_roles, key=len, reverse=True):
        match = re.match(
            rf"^(?:the\s+)?{_ROLE_PREFIX_OPEN}{re.escape(known_role)}"
            rf"{_ROLE_PREFIX_CLOSE}"
            r"(?=$|[\s*_`\"',.;:()\[\]{}\u2013\u2014-])",
            line,
            re.IGNORECASE,
        )
        if match is None:
            continue

        tail = line[match.end():]
        split = _split_pushback_prefix_tail(tail, known_roles)
        if split is not None:
            remainder, is_direct, is_narrative_attribution = split
            return (
                known_role, remainder, is_direct, True,
                is_narrative_attribution,
            )
        return (
            known_role, None, False,
            _is_structural_pushback_tail(
                tail,
                sentence_subject=match.group(0).lower().startswith("the "),
            ),
            False,
        )
    return None


def _normalize_pushback_attribution_target(
    candidate: str,
    known_roles: Set[str],
) -> Tuple[str, bool]:
    """Expose a roster role after ``as`` without consuming role wrappers."""
    candidate = candidate.lstrip(_PUSHBACK_ATTRIBUTION_TRIM)
    stage = re.match(
        r"^(\([^\)\r\n]{1,80}\)|\[[^\]\r\n]{1,80}\])",
        candidate,
    )
    if stage is not None:
        stage_text = re.sub(
            r"^(?:the|our|your)\s+", "",
            strip_decoration(stage.group(1)[1:-1]),
            count=1, flags=re.IGNORECASE)
        if (_extract_pushback_prefix(stage_text, known_roles) is None
                and not _detect_unknown_pushback_role(
                    stage_text, known_roles, explicit_attribution=True)):
            candidate = candidate[stage.end():].lstrip(
                _PUSHBACK_ATTRIBUTION_TRIM)

    article = re.match(
        rf"^(?P<open>{_ROLE_PREFIX_OPEN})(?P<article>the|our|your)\s+",
        candidate,
        re.IGNORECASE,
    )
    if article is None:
        return candidate, False
    return article.group("open") + candidate[article.end():], True


def _classify_pushback_speaking_span(span: str) -> Tuple[bool, bool]:
    """Return whether a ``Speaking ... as`` span is valid or malformed."""
    stage_pattern = r"\([^\)\r\n]{1,80}\)|\[[^\]\r\n]{1,80}\]"
    stage = re.search(stage_pattern, span)
    if stage is not None:
        span = span[:stage.start()] + span[stage.end():]
    if re.search(r"[()\[\]]", span):
        return False, True

    span = re.sub(r"[*_`\"'\u2018\u2019\u201c\u201d]", "", span).strip()
    if not span:
        return True, False
    words = span.split()
    conjunctions = [
        index for index, word in enumerate(words)
        if word.lower() in {"and", "but"}
    ]
    if (len(conjunctions) > 1
            or conjunctions and conjunctions[0] in {0, len(words) - 1}):
        return False, False
    return all(
        word.lower() in {"and", "but"}
        or (re.fullmatch(r"[A-Za-z]+(?:-[A-Za-z]+)*", word)
            and (word.lower() in _PUSHBACK_ATTRIBUTION_MODIFIERS
                 or word.lower().endswith("ly")))
        for word in words
    ), False


def _normalize_pushback_attribution_intro(
    line: str,
    known_roles: Set[str],
) -> Tuple[str, bool, bool, bool]:
    """Return normalized role text plus self/narrative attribution flags."""
    bare_as = re.match(r"^as\b", line, re.IGNORECASE)
    if bare_as is not None:
        candidate, has_article = _normalize_pushback_attribution_target(
            line[bare_as.end():], known_roles)
        return candidate, True, has_article, False

    speaking = re.match(r"^speaking\b", line, re.IGNORECASE)
    if speaking is None:
        return line, False, False, False

    window = line[speaking.end():speaking.end() + 81]
    for as_match in re.finditer(r"\bas\b", window, re.IGNORECASE):
        is_attribution, is_malformed = _classify_pushback_speaking_span(
            window[:as_match.start()])
        if not is_attribution and not is_malformed:
            continue
        candidate, _has_article = _normalize_pushback_attribution_target(
            line[speaking.end() + as_match.end():], known_roles)
        if (_extract_pushback_prefix(candidate, known_roles) is not None
                or _detect_unknown_pushback_role(
                    candidate, known_roles, explicit_attribution=True)):
            return candidate, True, False, is_malformed
    return line, False, False, False


def handle_player_question(
    world: WorldState,
    question: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    event_ledger=None
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
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        List of (advisor_role, response) tuples
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)
    
    # If no advisors loaded, return error message
    if not uk_advisors:
        return [("System", "Error: No advisors available. Initial conditions may not have loaded correctly.")]
    
    # A named-but-absent advisor gets an in-fiction correction instead of a
    # silent reroute to whoever matched a keyword (and burns no LLM call).
    unknown_title = _detect_unknown_addressee(question, _known_pushback_roles(initial_conditions))
    if unknown_title:
        return [(
            "Cabinet Secretary",
            f"(leaning in) There is no {unknown_title} in this room, Prime "
            f"Minister. Around this table: {_COBRA_ROSTER}."
        )]

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
    }
    
    for char_id, keywords in advisor_keywords.items():
        if char_id in uk_advisors and any(
            _question_matches_keyword(question_lower, kw) for kw in keywords
        ):
            responding_advisors.append(char_id)
    
    # If no specific advisor mentioned, default to NSA (coordinates responses)
    if not responding_advisors and "national_security_advisor" in uk_advisors:
        responding_advisors = ["national_security_advisor"]
    
    # If still no advisors, return all available
    if not responding_advisors:
        responding_advisors = list(uk_advisors.keys())[:1]  # Just return first one
    
    # Generate responses. A failed, empty or error-slot reply is recorded
    # and answered with an in-fiction line - never an out-of-fiction
    # "System: Error ..." message.
    _DEFERRAL_LINE = ("Prime Minister, I want to verify that before I answer "
                      "- give me a moment.")
    responses = []
    for char_id in responding_advisors:
        role = uk_advisors[char_id].get("role", "Advisor")
        try:
            prompt = build_advisor_context(world, initial_conditions, char_id,
                                           question, transcript, event_ledger)
            response = llm_generate_fn(prompt, rng, context=LLMContext.ADVISOR_QA)
            cleaned = (response or "").strip()
            if cleaned.startswith("[ERROR:"):
                record_fallback("advisor_qa", f"{char_id} error slot")
                cleaned = ""
            elif not cleaned:
                record_fallback("advisor_qa", f"{char_id} empty reply")
            responses.append((role, cleaned or _DEFERRAL_LINE))
        except Exception as e:
            record_fallback("advisor_qa", f"{char_id} {type(e).__name__}")
            responses.append((role, _DEFERRAL_LINE))

    return responses


def handle_player_question_all(
    world: WorldState,
    question: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None,
    event_ledger=None
) -> List[Tuple[str, str]]:
    """Put one question to the whole room: every advisor answers in role.

    Unlike handle_player_question, which routes to whichever advisor's
    keywords match, this asks every character in initial_conditions the same
    question through the same per-advisor context builder, so each answer
    comes from that advisor's own dossier and voice.

    DELIBERATE COST: this is one LLM call per seated advisor — five with the
    full COBRA roster — where a routed question costs one. That is the point
    of the feature (the player asked the room, the room answers), but a
    front end should treat it as the expensive affordance it is rather than
    the default. The prompts are independent, so when ``llm_batch_fn`` is
    supplied they go out as one batched group (see llm/fanout.py). Prompt and
    result order is stable; exact batch-vs-sequential RNG consumption is a
    provider detail and is not treated as equivalent.

    Args:
        world: Current world state
        question: Player's question, asked of everyone
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Single-call LLM function (prompt, rng -> str)
        rng: Random number generator for determinism
        transcript: Optional full game transcript for conversation history
        llm_batch_fn: Optional batch generator; when supplied the advisor
            prompts go out as one group rather than in sequence
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        List of (advisor_role, response) tuples, one per advisor, in the
        roster's order.
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)

    # get_all_uk_advisors excludes the player: the room answers, the chair asks.
    asked = list(uk_advisors)

    if not asked:
        return [("System", "Error: No advisors available. Initial conditions "
                           "may not have loaded correctly.")]

    # A failed, empty or error-slot reply is recorded and answered with an
    # in-fiction deferral - never an out-of-fiction "System: Error" line.
    _DEFERRAL_LINE = ("Prime Minister, I want to verify that before I answer "
                      "- give me a moment.")
    prompts = []
    prompt_ok = {}
    for char_id in asked:
        try:
            prompts.append(build_advisor_context(
                world, initial_conditions, char_id, question, transcript,
                event_ledger, fanout=True))
            prompt_ok[char_id] = True
        except Exception as e:
            record_fallback("advisor_qa", f"{char_id} {type(e).__name__}")
            prompts.append("")
            prompt_ok[char_id] = False

    responses = generate_group(
        [p for p in prompts if p],
        llm_generate_fn, rng, llm_batch_fn,
        context=LLMContext.ADVISOR_QA
    )
    answers = iter(responses)

    results = []
    for char_id, prompt in zip(asked, prompts):
        role = uk_advisors[char_id].get("role", "Advisor")
        if not prompt_ok[char_id]:
            results.append((role, _DEFERRAL_LINE))
            continue
        response = next(answers, "")
        cleaned = (response or "").strip()
        if cleaned.startswith("[ERROR:"):
            # A batch driver marks a per-prompt failure as "[ERROR: ...]" in
            # that slot rather than raising (see llm/fanout.py). That is a
            # failed call, not an advisor's line.
            record_fallback("advisor_qa", f"{char_id} error slot")
            cleaned = ""
        elif not cleaned:
            record_fallback("advisor_qa", f"{char_id} empty reply")
        results.append((role, cleaned or _DEFERRAL_LINE))

    return results


def interpret_player_action(
    world: WorldState,
    action: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    event_ledger=None
) -> str:
    """Interpret player's free-form action into structured summary.

    Args:
        world: Current world state
        action: Player's action description
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Structured interpretation of the action
    """
    prompt = build_decision_interpretation_prompt(world, action, initial_conditions,
                                                  transcript, event_ledger)
    interpretation = llm_generate_fn(prompt, rng, context=LLMContext.DECISION_INTERPRETATION)
    # An empty interpretation flows into every downstream prompt and the
    # decision display; the substitution there must show in parse health.
    if not interpretation or not interpretation.strip():
        record_fallback("decision_interpretation", "empty reply")
    return interpretation


def generate_advisor_pushback(
    world: WorldState,
    action: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None,
    event_ledger=None
) -> List[Tuple[str, str]]:
    """Ask each seated advisor independently for warnings or pushback.

    Args:
        world: Current world state
        action: Player's action description
        interpretation: LLM's interpretation of the action
        initial_conditions: Parsed initial conditions
        llm_generate_fn: Function to call LLM
        rng: Random number generator
        transcript: Optional full game transcript for conversation history
        llm_batch_fn: Optional batch generator for the independent prompts
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        Roster-attributed concerns. Failed/malformed slots carry a visible
        error concern; valid standalone NO PUSHBACK slots are omitted.
    """
    advisors = get_all_uk_advisors(initial_conditions)
    prompts = [
        build_pushback_prompt(
            world, action, interpretation, initial_conditions, char_id,
            transcript, event_ledger)
        for char_id in advisors
    ]
    responses = generate_group(
        prompts, llm_generate_fn, rng, llm_batch_fn,
        context=LLMContext.ADVISOR_PUSHBACK)
    
    unavailable = "[ERROR: Advisor response unavailable]"
    malformed_response = "[ERROR: Advisor response malformed]"
    known_roles = _known_pushback_roles(initial_conditions)
    player_roles = set(_ADVISOR_ROLE_ALIASES.get(PLAYER_CHARACTER_ID, []))
    player = get_character_info(initial_conditions, PLAYER_CHARACTER_ID) or {}
    if isinstance(player, dict) and player.get("role"):
        player_roles.add(player["role"].strip().lower())
    result = []
    for (char_id, char_info), response in zip(advisors.items(), responses):
        role = char_info.get("role", "Advisor")
        own_roles = set(_ADVISOR_ROLE_ALIASES.get(char_id, []))
        own_roles.add(char_id.replace("_", " ").lower())
        if role:
            own_roles.add(role.strip().lower())
        if not isinstance(response, str):
            record_fallback("advisor_pushback", f"{char_id} malformed reply")
            result.append((role, malformed_response))
            continue
        cleaned = response.strip()

        if _has_invisible_unicode(cleaned):
            record_fallback("advisor_pushback", f"{char_id} malformed reply")
            result.append((role, malformed_response))
            continue

        if not cleaned or is_error_response(cleaned):
            record_fallback("advisor_pushback", f"{char_id} failed reply")
            result.append((role, unavailable))
            continue

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        sentinel_tail = (
            _split_leading_pushback_sentinel(lines[0]) if lines else None)
        prefixed_response = None
        if sentinel_tail is None and lines:
            (candidate, self_attributed, _narrative_as,
             malformed_intro) = _normalize_pushback_attribution_intro(
                strip_decoration(lines[0]), known_roles)
            prefixed = None if malformed_intro else _extract_pushback_prefix(
                candidate, known_roles)
            if prefixed is not None:
                (prefix, stripped, is_direct, _is_speaker_prefix,
                 is_narrative_attribution) = prefixed
                is_player_vocative = (
                    prefix in player_roles and is_direct
                    and not self_attributed)
                if (stripped is not None
                        and (is_player_vocative
                             or (prefix in own_roles
                                 and not is_narrative_attribution))):
                    prefixed_response = stripped
                    sentinel = re.search(
                        _NO_PUSHBACK_PATTERN, stripped, re.IGNORECASE)
                    if (sentinel is not None
                            and all(
                                char.isspace()
                                or char in _PUSHBACK_SENTINEL_OPENERS
                                for char in stripped[:sentinel.start()])):
                        raw_sentinel = re.search(
                            _NO_PUSHBACK_PATTERN, lines[0], re.IGNORECASE)
                        if raw_sentinel is not None:
                            raw_start = raw_sentinel.start()
                            while (raw_start > 0
                                   and (lines[0][raw_start - 1].isspace()
                                        or lines[0][raw_start - 1]
                                        in _PUSHBACK_SENTINEL_OPENERS)):
                                raw_start -= 1
                            sentinel_tail = _split_leading_pushback_sentinel(
                                lines[0][raw_start:])
        if (prefixed_response is not None
                and is_error_response(prefixed_response)):
            record_fallback("advisor_pushback", f"{char_id} failed reply")
            result.append((role, unavailable))
            continue
        if sentinel_tail is not None:
            rationale = "\n".join([sentinel_tail, *lines[1:]]).strip()
            if _is_no_pushback_rationale(rationale):
                continue
            record_fallback("advisor_pushback", f"{char_id} malformed reply")
            result.append((role, malformed_response))
            continue

        # Attribution always comes from the roster. Tolerate and strip a
        # redundant self-prefix or player vocative; reject another seat only
        # when it is being used as structural speaker framing.
        parsed_lines = []
        malformed = False
        player_vocative_seen = False
        for line in lines:
            remainder = line
            narrative_line = None
            while remainder:
                undecorated = strip_decoration(remainder)
                connector_stripped = undecorated
                if narrative_line is not None:
                    connector_stripped = re.sub(
                        r"^(?:and|but|yet|so)\s+",
                        "",
                        undecorated,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                    for separator in re.finditer(
                            r"[,;:.!?]|\s[\u2013\u2014]\s",
                            connector_stripped):
                        continuation = strip_decoration(
                            connector_stripped[separator.end():])
                        (probe, probe_self_attributed, _probe_narrative,
                         probe_malformed) = (
                            _normalize_pushback_attribution_intro(
                                continuation, known_roles)
                        )
                        if (probe_malformed
                                or _extract_pushback_prefix(
                                    probe, known_roles) is not None
                                or _detect_unknown_pushback_role(
                                    probe,
                                    known_roles,
                                    explicit_attribution=(
                                        probe_self_attributed))):
                            connector_stripped = continuation
                            break
                    undecorated = strip_decoration(connector_stripped)
                if _find_pushback_failure_marker(remainder) is not None:
                    malformed = True
                    break
                (candidate_line, self_attributed, narrative_as,
                 malformed_intro) = _normalize_pushback_attribution_intro(
                    undecorated, known_roles)
                if malformed_intro:
                    malformed = True
                    break
                prefixed = _extract_pushback_prefix(
                    candidate_line, known_roles)
                if prefixed is None:
                    if _detect_unknown_pushback_role(
                            candidate_line, known_roles,
                            explicit_attribution=self_attributed):
                        malformed = True
                    else:
                        parsed_lines.append(narrative_line or remainder)
                    break

                (prefix, stripped, is_direct, is_speaker_prefix,
                 is_narrative_attribution) = prefixed
                is_own = prefix in own_roles
                is_player_vocative = (
                    prefix in player_roles
                    and is_direct
                    and not self_attributed
                    and not parsed_lines
                    and not player_vocative_seen
                )
                if is_player_vocative:
                    player_vocative_seen = True
                elif (is_own and is_narrative_attribution
                      and not narrative_as):
                    if narrative_line is None:
                        narrative_line = remainder
                elif not is_own:
                    if narrative_as and is_narrative_attribution:
                        if narrative_line is None:
                            narrative_line = remainder
                    else:
                        if self_attributed or is_speaker_prefix:
                            malformed = True
                        else:
                            parsed_lines.append(narrative_line or remainder)
                        break
                elif player_vocative_seen and parsed_lines:
                    malformed = True
                    break
                if stripped is None:
                    parsed_lines.append(narrative_line or remainder)
                    remainder = ""
                else:
                    remainder = stripped

            if malformed:
                break

        if malformed or not parsed_lines or any(
                is_error_response(line)
                or is_sentinel_line(line, "NO PUSHBACK")
                for line in parsed_lines):
            record_fallback("advisor_pushback", f"{char_id} malformed reply")
            result.append((role, malformed_response))
            continue

        result.append((role, _scrub_turn_references("\n".join(parsed_lines))))

    return result


def check_critical_omissions(
    world: WorldState,
    player_decision: str,
    interpretation: str,
    initial_conditions: Dict[str, Any],
    llm_generate_fn,
    rng: Random,
    transcript: List[str] = None,
    llm_batch_fn=None,
    event_ledger=None
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
        llm_batch_fn: Optional batch generator. When supplied the five
            advisor prompts go out as one group rather than in sequence.
        event_ledger: Optional played-event ledger for the dossier (ER-003)

    Returns:
        List of (advisor_role, concern, recommendation) tuples
        Empty list if no critical omissions detected
    """
    uk_advisors = get_all_uk_advisors(initial_conditions)
    
    if not uk_advisors:
        return []
    
    # Build recent events context from world state
    recent_events = []
    if world.recent_injects:
        recent_events = world.recent_injects[-5:]  # Last 5 injects
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

    # The five advisors scan independently - none of them reads another's
    # answer - so these are asked together rather than one after another.
    # They are also the largest identical-prefix group in a turn, and the
    # interpretation and pushback calls that run before them share that same
    # prefix, so the provider's cache is already warm by the time they fire.
    checking = [c for c in advisors_to_check if c in uk_advisors]
    prompts = [
        build_critical_omissions_prompt(
            world, initial_conditions, char_id, player_decision,
            recent_events, transcript,
            # The structured reading of the decision, produced one call
            # earlier for exactly this purpose - the scan is about what the
            # decision omits, so the advisors get the reading, not just the
            # raw typed sentence (ER-002).
            interpretation=interpretation,
            event_ledger=event_ledger
        )
        for char_id in checking
    ]
    responses = generate_group(
        prompts, llm_generate_fn, rng, llm_batch_fn,
        context=LLMContext.CRITICAL_OMISSIONS
    )

    for char_id, response in zip(checking, responses):
        try:
            # A batch driver marks a per-prompt failure as "[ERROR: ...]" in
            # that slot rather than raising (see llm/fanout.py). That is a
            # failed call, not an advisor finding nothing wrong.
            if response and response.startswith("[ERROR:"):
                record_fallback("critical_omissions", char_id)
                print(f"[WARN] Critical omissions check failed for {char_id}: "
                      f"{response[:80]}")
                continue

            # An EMPTY reply is a failed call, not an advisor finding
            # nothing wrong - it must not be conflated with the genuine
            # NO_CONCERN sentinel below.
            if not response or not response.strip():
                record_miss("critical_omissions", "empty_reply", char_id)
                continue

            # The all-clear sentinel only counts as a standalone line, so an
            # answer that merely mentions NO_CONCERN mid-sentence still parses
            if any(
                is_sentinel_line(line, "NO_CONCERN")
                for line in response.splitlines()
            ):
                continue

            # Extract concern and recommendation (tolerating markdown-bold
            # labels); continuation lines append to whichever was seen last
            concern = ""
            recommendation = ""
            last_field = None
            residue = []

            lines = response.strip().split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                concern_text = extract_label(line, "CONCERN")
                recommendation_text = extract_label(line, "RECOMMENDATION")
                if concern_text is not None:
                    concern = concern_text
                    last_field = "concern"
                elif recommendation_text is not None:
                    recommendation = recommendation_text
                    last_field = "recommendation"
                elif last_field == "concern":
                    # Multi-line concern
                    concern = f"{concern} {line}".strip()
                elif last_field == "recommendation":
                    # Multi-line recommendation
                    recommendation = f"{recommendation} {line}".strip()
                else:
                    # Before any label: neither consumed nor recognised
                    residue.append(line)

            if residue:
                record_residue("critical_omissions", len(residue),
                               residue[0][:60])

            if concern and not recommendation:
                # A concern with no recommendation is still a concern - it
                # must surface, not vanish over a missing second field
                record_miss("critical_omissions", "recommendation", char_id)
                recommendation = "(no specific recommendation given)"
            elif recommendation and not concern:
                record_miss("critical_omissions", "concern", char_id)
                continue

            if concern and recommendation:
                char_info = uk_advisors[char_id]
                role = char_info.get("role", "Advisor")
                critical_concerns.append((role, concern, recommendation))

        except Exception as e:
            # Keep checking the remaining advisors, but don't fail silently
            print(f"[WARN] Critical omissions check failed for {char_id}: {e}")
            continue

    return critical_concerns
