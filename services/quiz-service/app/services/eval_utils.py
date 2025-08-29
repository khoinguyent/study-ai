import re
import unicodedata
from typing import List


def normalize(s: str) -> str:
    """Normalize text for comparison by removing accents, converting to lowercase, and normalizing whitespace"""
    if s is None:
        return ""
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def matches_any(ans: str, accepted: List[str]) -> bool:
    """Check if answer matches any of the accepted patterns, including regex patterns"""
    n = normalize(ans)
    for a in accepted:
        if isinstance(a, str) and a.startswith("re:"):
            if re.fullmatch(a[3:], n, flags=re.IGNORECASE):
                return True
        else:
            if n == normalize(a):
                return True
    return False
