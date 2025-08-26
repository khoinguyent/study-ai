import re
from typing import List, Optional


def split_into_sentences(text: str, locale_hint: Optional[str] = None) -> List[str]:
    """Multilingual sentence splitter using regex heuristics.

    Note: Python doesn't have Intl.Segmenter; we use robust regex instead.
    """
    if not text:
        return []

    # Normalize whitespace
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    # Regex-based sentence boundary detection covering ., !, ?, Vietnamese and quotes
    pattern = re.compile(
        r"(.+?(?:[\.!?…]+|\u2026|\?|\!|\n{2,}|$))(\s+|$)",
        re.UNICODE,
    )

    sentences: List[str] = []
    start = 0
    for match in pattern.finditer(normalized):
        segment = match.group(1).strip()
        if segment:
            sentences.append(segment)
        start = match.end()

    # Fallback if nothing matched
    if not sentences:
        return [normalized]

    # Merge extremely short fragments with next sentence
    merged: List[str] = []
    buffer = ""
    for s in sentences:
        if len(s) < 20:
            buffer = (buffer + " " + s).strip()
            continue
        if buffer:
            merged.append((buffer + " " + s).strip())
            buffer = ""
        else:
            merged.append(s)
    if buffer:
        merged.append(buffer)

    return merged


