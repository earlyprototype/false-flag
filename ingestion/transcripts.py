from __future__ import annotations

from pathlib import Path


def read_transcript_text(path: str | Path) -> str:
    """Read transcript text from a local file. Returns empty string if missing/unreadable.

    This scaffold avoids raising exceptions to keep ingestion optional in early stages.
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def normalise_transcript(text: str) -> str:
    """Normalise whitespace: trim lines and collapse multiple blank lines."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines()]
    out_lines: list[str] = []
    last_blank = False
    for ln in lines:
        is_blank = len(ln) == 0
        if is_blank and last_blank:
            continue
        out_lines.append(ln)
        last_blank = is_blank
    return "\n".join(out_lines).strip()


def load_and_normalise(path: str | Path) -> str:
    """Convenience wrapper: read then normalise text."""
    raw = read_transcript_text(path)
    if not raw:
        return ""
    return normalise_transcript(raw)



