from __future__ import annotations


def split_paragraphs(text: str, min_len: int = 20) -> list[str]:
    """Naive paragraph splitter on blank lines; filters very short segments.

    Returns an empty list if input is empty.
    """
    if not text:
        return []
    parts = [p.strip() for p in text.split("\n\n")]
    return [p for p in parts if len(p) >= min_len]



