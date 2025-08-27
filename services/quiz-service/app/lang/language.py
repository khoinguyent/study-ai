from __future__ import annotations
from typing import Iterable, Tuple
import re

try:
    from lingua import LanguageDetectorBuilder, Language  # type: ignore
    _DET = LanguageDetectorBuilder.from_all_languages().build()

    def _detect_one(text: str) -> Tuple[str, float]:
        res = _DET.detect_language_of(text or "")
        conf = _DET.compute_language_confidence(text or "", res) if res else 0.0
        return (res.iso_code_639_1.name.lower() if res else "unknown", float(conf))
except Exception:
    # fallback
    try:
        from langdetect import detect, DetectorFactory  # type: ignore
        DetectorFactory.seed = 42

        def _detect_one(text: str) -> Tuple[str, float]:
            try:
                return (detect(text or ""), 0.6)  # langdetect has no score; assume middling
            except Exception:
                return ("unknown", 0.0)
    except Exception:
        # ultimate fallback: unknown
        def _detect_one(text: str) -> Tuple[str, float]:
            return ("unknown", 0.0)


VI_CODES = {"vi"}
EN_CODES = {"en"}


def sample_text(snippets: Iterable[str], max_chars: int = 4000) -> str:
    buf, n = [], 0
    for t in snippets:
        t = re.sub(r"\s+", " ", t or "").strip()
        if not t:
            continue
        if n + len(t) > max_chars:
            t = t[: max_chars - n]
        buf.append(t)
        n += len(t)
        if n >= max_chars:
            break
    return " ".join(buf)


def detect_language(snippets: Iterable[str]) -> Tuple[str, float]:
    text = sample_text(snippets)
    if not text:
        return ("unknown", 0.0)
    lang, conf = _detect_one(text)
    # normalize common cases
    if lang not in VI_CODES | EN_CODES:
        # bias to vi if many Vietnamese diacritics present
        if re.search(r"[ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", text, re.I):
            return ("vi", max(conf, 0.8))
    return (lang, conf)


