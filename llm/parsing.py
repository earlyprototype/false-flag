"""Shared tolerant parsing utilities for structured LLM output.

Every parser in the engine asks the model for a labelled plain-text format
("QUALITY: poor", "TRUST_CHANGE: -8") and models routinely hand it back
decorated - markdown emphasis on the labels, bulleted delta lines, an
annotation after the number. Two call sites already handled this correctly
(the decoration-tolerant label reader in agents/conversation.py and the
signed-int search in engine/actor_simulation.py); this module generalises
those two techniques so every parser reads the same dialect.
"""

import re
from typing import Optional, Sequence

# Decoration characters found around labels and values: markdown emphasis,
# backticks, quotes, brackets, blockquote/heading markers, and list bullets.
_DECORATION_CHARS = "*_`\"'[]()>#•–—- \t"

# Leading decoration before a label: any mix of the characters above,
# optionally with a numbered bullet ("1." / "2)") in the middle.
_LEAD_RE = r"^[\s*_`>#•\-]*(?:\d+[.)][\s*_`>#•\-]*)?"

# Worded refusals ("absolutely not", "no, we will not assist"). Kept
# deliberately broad: a refusal misread as consent inverts an outcome,
# while consent misread as refusal only understates one.
_REFUSAL_RE = re.compile(
    r"\b(no|not|never|refuse[sd]?|decline[sd]?|cannot|won't|will not)\b",
    re.IGNORECASE,
)

# Words that negate the token immediately after them ("not yes").
_NEGATORS = {"no", "not", "never", "cannot", "won't", "wouldn't", "don't"}

_SIGNED_INT_RE = re.compile(r"[+-]?\d+")
_FLOAT_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")


def strip_decoration(text: str) -> str:
    """Strip leading/trailing markdown, bullets and brackets from a token.

    Unlike the old role-prefix normaliser this also removes leading hyphens
    and bullet glyphs, so "- Military Commander" reads as the role it names.
    """
    return text.strip().strip(_DECORATION_CHARS).strip()


def extract_label(line: str, label: str) -> Optional[str]:
    """Return the text after a "LABEL:" prefix, tolerating decoration.

    Accepts "LABEL:", "**LABEL:**", "**LABEL**:", "- label:", "> LABEL:",
    "2. LABEL:" and similar (case-insensitive). Returns None when the line
    does not start with the label.
    """
    pattern = (_LEAD_RE + re.escape(label) + r"[\s*_`]*:[\s*_`]*(.*)$")
    match = re.match(pattern, line.strip(), re.IGNORECASE)
    if match is None:
        return None
    value = match.group(1).strip()
    # Trailing emphasis belongs to the decoration, not the value
    value = value.strip("*_`").strip()
    # A value the model chose to quote ('INTEL_SHARED: "none"') means the
    # value itself; only a symmetric surrounding pair is treated as
    # decoration, so a quote inside the text survives.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


def find_signed_int(text: str) -> Optional[int]:
    """Return the first signed integer in the text, or None.

    Searches rather than converts, so an annotated value like
    "+8 (sharp rise)" recovers the 8 instead of raising.
    """
    match = _SIGNED_INT_RE.search(text)
    return int(match.group(0)) if match else None


def find_float(text: str) -> Optional[float]:
    """Return the first (optionally signed) number in the text, or None."""
    match = _FLOAT_RE.search(text)
    return float(match.group(0)) if match else None


# How many words before a token are checked for a negator. One word missed
# "Not a failure" (the article hid the negation); a short window catches the
# common phrasings without letting a negator half a sentence away flip an
# unrelated verdict.
_NEGATION_LOOKBACK = 3


def _has_unnegated_token(text: str, token: str) -> bool:
    """True when `token` appears on a word boundary not preceded by a negator.

    The lookback spans the last few words ("not a failure", "not quite a
    success"), not just the immediately preceding one.
    """
    for match in re.finditer(r"\b" + re.escape(token) + r"\b", text, re.IGNORECASE):
        preceding = text[:match.start()].rstrip().split()
        window = preceding[-_NEGATION_LOOKBACK:]
        if any(word.strip(",;:.\"'()").lower() in _NEGATORS for word in window):
            continue
        return True
    return False


def match_enum(
    text: str,
    allowed: Sequence[str],
    refusal_value: Optional[str] = None,
) -> Optional[str]:
    """Match free text against an enumeration, tolerating wording.

    Priority:
    1. The cleaned text equals one token exactly ("no", "**FAILURE**").
    2. With `refusal_value` set: a worded refusal ("absolutely not",
       "no, we will not assist") with no unnegated "yes" maps to it.
    3. The first token from `allowed` present on an unnegated word boundary.

    Returns the matching token from `allowed` (original casing), or None.
    """
    cleaned = strip_decoration(text).strip(".").strip().lower()
    by_lower = {token.lower(): token for token in allowed}
    if cleaned in by_lower:
        return by_lower[cleaned]
    if (refusal_value is not None and _REFUSAL_RE.search(text)
            and not _has_unnegated_token(text, "yes")):
        return refusal_value
    for token in allowed:
        if _has_unnegated_token(text, token):
            return token
    return None


def is_sentinel_line(text: str, sentinel: str) -> bool:
    """True only when the line IS the sentinel (modulo decoration).

    Underscores and spaces are interchangeable, so "NO_CONCERN" and
    "NO CONCERN" both match a sentinel written either way. A sentinel
    mentioned mid-sentence does not match.
    """
    normalized = text.strip().strip("*_`\"'[]().:;!-• \t").upper().replace("_", " ")
    return normalized == sentinel.strip().upper().replace("_", " ")
