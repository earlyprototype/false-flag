"""Hot-editable instruction templates for the highest-traffic prompt families.

The static instruction blocks of the advisor Q&A, decision-interpretation
and pushback prompts live in data/prompts/<family>.txt so an operator can
edit them live (dashboard editor, PUT /prompts/{family}) without restarting
the server. Assembly logic - shared context prefix, value formatting - stays
in llm/prompts.py; only the template TEXT moved.

Templates are ``str.format`` strings; each family's placeholder names are
fixed (PLACEHOLDERS below). Loading is mtime-based: an edited file is
re-read on the next call, an unchanged file costs one stat().

DEFAULTS holds the canonical text, byte-identical to the pre-extraction
inline literals (tests/test_prompt_templates.py pins this against a golden
capture - note two lines in decision_interpretation end with a significant
trailing space). The default is served when a file is missing and restored
by reset_template; a template file that no longer formats cleanly falls
back to it rather than crashing a turn.
"""

import os
import threading
from pathlib import Path
from string import Formatter
from typing import Dict, Iterable, Tuple

_DEFAULT_PROMPT_DIR = Path(__file__).resolve().parents[1] / "data" / "prompts"


def _prompt_dir() -> Path:
    """The template directory: WARGAME_PROMPT_DIR overrides the repo default.

    The override exists so the test suite can point every write
    (set_template, reset_template, fixture teardowns) at a throwaway
    directory. Without it, tests rewrote the REAL committed
    data/prompts/*.txt files - and any earlier test's teardown silently
    healed a drifted committed file before the parity test could read it.
    """
    override = os.environ.get("WARGAME_PROMPT_DIR")
    return Path(override) if override else _DEFAULT_PROMPT_DIR


_lock = threading.Lock()
# family -> ((path, mtime_ns, size), text). The path is part of the key so
# a directory switch (tests) can never serve a stale entry whose mtime and
# size happen to coincide.
_cache: Dict[str, Tuple[Tuple[str, int, int], str]] = {}


DEFAULTS: Dict[str, str] = {
    "advisor_qa": '''You are the {role} in a UK government COBRA meeting during a crisis.

Your knowledge domains: {knowledge_domains}
Your key concerns: {key_concerns}

Relevant context specific to your role:
{context_str}

The Prime Minister asks: "{question}"

Respond in character as the {role}. Be concise, professional, and focus on your areas of expertise.
Reference past decisions, warnings, or outcomes from the conversation history when relevant.
If the question is outside your knowledge domain, acknowledge this and suggest who might better answer it.

Keep paragraphs short for readability.

Your response:''',

    # NOTE: two lines below end with a trailing space ("...advisors. " and
    # "...the PM ") - they are part of the pre-extraction bytes and are
    # pinned by the parity test. Do not "clean" them.
    "decision_interpretation": '''You are interpreting a decision made by the UK Prime Minister during a crisis.

Available forces:
{uk_forces}

Ammunition stockpiles:
{stockpiles}

Constraints:
{constraints}

The Prime Minister has decided: "{action}"

IMPORTANT: Interpret this as the PM's DECISION/DIRECTIVE to their cabinet, not as a question to advisors. 
Even if phrased as questions or dialogue (e.g., "Where can we...?", "Speak to..."), treat this as the PM 
ORDERING those actions to be taken by the appropriate departments.

Interpret this action and provide:
1. A clear, structured summary of what the PM intends to do
2. Which UK forces/assets are being deployed or used
3. What resources (ammunition, etc.) will be consumed
4. Expected timeline (immediate, 1-3 turns, longer)
5. Any obvious impossibilities or violations of constraints

Consider the conversation history - if this decision builds on or contradicts previous actions, note that.

Format your response as:
INTERPRETATION: [one-sentence summary]
FORCES INVOLVED: [list]
RESOURCES CONSUMED: [list or "None"]
TIMELINE: [immediate/short/medium/long]
FEASIBILITY: [feasible/requires clarification/impossible because...]

Your interpretation:''',

    "advisor_pushback": '''You are simulating UK government advisors responding to a Prime Minister's decision.

The PM has decided: "{action}"

Interpretation of this action:
{interpretation}

Advisors and their pushback triggers:
{advisors_str}

For each advisor whose pushback triggers are activated by this decision, generate a brief (2-3 sentences) in-character warning or concern. Reference past warnings or decisions from the conversation history if relevant (e.g., "As I warned in Turn 2..."). If no triggers are activated, respond with "NO PUSHBACK".

Format:
[ADVISOR ROLE]: [their concern]

OR

NO PUSHBACK

Your response:''',
}


#: The exact placeholder set each family's template may use. PUT validation
#: and the runtime fallback both key off this.
PLACEHOLDERS: Dict[str, Tuple[str, ...]] = {
    "advisor_qa": ("role", "knowledge_domains", "key_concerns",
                   "context_str", "question"),
    "decision_interpretation": ("uk_forces", "stockpiles", "constraints",
                                "action"),
    "advisor_pushback": ("action", "interpretation", "advisors_str"),
}

FAMILIES: Tuple[str, ...] = tuple(DEFAULTS)


def template_path(family: str) -> Path:
    _require_family(family)
    return _prompt_dir() / f"{family}.txt"


def _require_family(family: str) -> None:
    if family not in DEFAULTS:
        raise KeyError(f"Unknown prompt family '{family}'; "
                       f"expected one of {sorted(DEFAULTS)}")


def _normalise(text: str) -> str:
    """CRLF-proof and trailing-newline-proof the file bytes.

    A CRLF checkout or an editor-appended final newline must not change the
    assembled prompt; interior trailing spaces are significant and kept.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def validate_template(family: str, text: str) -> None:
    """Raise ValueError when ``text`` cannot format with the family's fields.

    Rejects unknown field names, positional ``{}`` fields and malformed
    format specs - the failures a live edit could otherwise smuggle into
    the middle of a campaign.
    """
    _require_family(family)
    allowed = set(PLACEHOLDERS[family])
    try:
        fields = [f for _, f, _, _ in Formatter().parse(text) if f is not None]
    except ValueError as e:
        raise ValueError(f"Malformed format string: {e}")
    for field in fields:
        if field == "":
            raise ValueError("Positional '{}' fields are not allowed; "
                             f"use named fields: {sorted(allowed)}")
        name = field.split(".")[0].split("[")[0]
        if name not in allowed:
            raise ValueError(f"Unknown placeholder '{{{field}}}'; "
                             f"this family accepts: {sorted(allowed)}")
    # Prove it assembles.
    text.format(**{name: "" for name in allowed})


def get_template(family: str) -> str:
    """The family's current template text: edited file if present and
    readable, else the canonical default. mtime-cached."""
    path = template_path(family)
    try:
        stat = path.stat()
        key = (str(path), stat.st_mtime_ns, stat.st_size)
    except OSError:
        return DEFAULTS[family]

    with _lock:
        cached = _cache.get(family)
        if cached is not None and cached[0] == key:
            return cached[1]

    try:
        text = _normalise(path.read_text(encoding="utf-8"))
    except OSError:
        return DEFAULTS[family]

    with _lock:
        _cache[family] = (key, text)
    return text


def render(family: str, **values) -> str:
    """Format the family's current template; fall back to the canonical
    default if a live edit broke it (and warn, once per bad text)."""
    template = get_template(family)
    try:
        return template.format(**values)
    except (KeyError, IndexError, ValueError) as e:
        print(f"[WARNING] Prompt template '{family}' failed to format "
              f"({type(e).__name__}: {e}); using the default template")
        return DEFAULTS[family].format(**values)


def set_template(family: str, text: str) -> None:
    """Validate and persist an edited template (PUT /prompts/{family})."""
    text = _normalise(text)
    validate_template(family, text)
    path = template_path(family)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    with _lock:
        _cache.pop(family, None)


def reset_template(family: str) -> None:
    """Restore the canonical default text for a family."""
    _require_family(family)
    path = template_path(family)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULTS[family], encoding="utf-8", newline="\n")
    with _lock:
        _cache.pop(family, None)


def is_edited(family: str) -> bool:
    """True when the family's current text differs from the default."""
    return get_template(family) != DEFAULTS[family]


def families_summary() -> Iterable[Dict[str, object]]:
    """One row per family for GET /prompts."""
    return [
        {
            "family": family,
            "placeholders": list(PLACEHOLDERS[family]),
            "edited": is_edited(family),
        }
        for family in FAMILIES
    ]
