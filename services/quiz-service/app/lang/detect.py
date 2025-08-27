from __future__ import annotations
from typing import Iterable, Dict, Tuple, List
import re

_has_lingua = False
_has_pycld3 = False

try:
    from lingua import LanguageDetectorBuilder  # type: ignore
    _lingua = LanguageDetectorBuilder.from_all_languages().build()
    _has_lingua = True
except Exception:
    _lingua = None

try:
    import pycld3  # type: ignore
    _has_pycld3 = True
except Exception:
    pycld3 = None  # type: ignore


def _normalize_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s


def sample_text(snippets: Iterable[str], max_chars: int = 8000) -> str:
    buf: List[str] = []
    n = 0
    for t in snippets:
        t = _normalize_text(t)
        if not t:
            continue
        if n + len(t) > max_chars:
            t = t[: max_chars - n]
        buf.append(t)
        n += len(t)
        if n >= max_chars:
            break
    return " ".join(buf)


def detect_language_distribution(snippets: Iterable[str]) -> Tuple[str, float, Dict[str, float]]:
    """
    Returns (best_code, best_conf, distribution) where distribution is {iso_code: score}.
    Uses Lingua if available, then pycld3, then a tiny heuristic fallback.
    """
    text = sample_text(snippets)
    if not text:
        return ("und", 0.0, {"und": 1.0})

    scores: Dict[str, float] = {}

    if _has_lingua and _lingua is not None:
        try:
            lang = _lingua.detect_language_of(text)
            if lang:
                code = getattr(lang.iso_code_639_1, "name", None)
                code = (code or lang.name).lower()
                conf = _lingua.compute_language_confidence(text, lang) or 0.0
                scores[code] = float(conf)
        except Exception:
            pass

    if _has_pycld3 and pycld3 is not None:
        try:
            r = pycld3.get_frequent_languages(text, num_langs=3) or []
            for it in r:
                code = (getattr(it, "language", None) or "und").lower()
                conf = float(getattr(it, "probability", 0.0) or 0.0)
                scores[code] = max(scores.get(code, 0.0), conf)
        except Exception:
            pass

    if not scores:
        # Enhanced fallback heuristic based on common patterns
        text_lower = text.lower()
        
        # Check for Vietnamese characters
        if any(char in text_lower for char in ['ă', 'â', 'ê', 'ô', 'ơ', 'ư', 'đ']):
            scores["vi"] = 0.8
        # Check for common English words
        elif any(word in text_lower for word in ['the', 'and', 'of', 'to', 'in', 'is', 'it', 'that', 'with', 'for']):
            scores["en"] = 0.7
        # Check for common French words
        elif any(word in text_lower for word in ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'pour', 'avec']):
            scores["fr"] = 0.7
        # Check for common German words
        elif any(word in text_lower for word in ['der', 'die', 'das', 'und', 'in', 'den', 'von', 'zu', 'mit', 'auf']):
            scores["de"] = 0.7
        else:
            scores["und"] = 0.5

    best_code = max(scores.items(), key=lambda kv: kv[1])[0]
    best_conf = scores[best_code]
    return (best_code, best_conf, scores)


