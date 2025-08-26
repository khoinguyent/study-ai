import math
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from ...config import Settings
from .sectionizer import Section
from .sentence_split import split_into_sentences
from .tokenizer_labse import count_labse_tokens


@dataclass
class Chunk:
    id: str
    text: str
    tokens: int
    meta: Dict[str, Any]


def _density_score(text: str, w_symbols: float, w_avgword: float, w_numbers: float) -> float:
    if not text:
        return 0.0
    total_chars = len(text)
    if total_chars == 0:
        return 0.0
    num_symbols = sum(1 for c in text if not c.isalnum() and not c.isspace())
    symbols_ratio = num_symbols / total_chars

    words = [w for w in text.split() if any(ch.isalpha() for ch in w)]
    avg_word_len = sum(len(w) for w in words) / max(1, len(words))
    avg_word_len_norm = min(1.0, max(0.0, (avg_word_len - 3) / 7))

    num_numbers = sum(1 for c in text if c.isdigit())
    number_ratio = num_numbers / total_chars

    score = (
        w_symbols * symbols_ratio + w_avgword * avg_word_len_norm + w_numbers * number_ratio
    )
    return max(0.0, min(1.0, score))


def _target_tokens(base: int, min_tokens: int, max_tokens: int, density: float) -> int:
    # target = clamp(base * (1 - 0.35 * density), MIN, MAX)
    raw = base * (1 - 0.35 * density)
    return int(max(min_tokens, min(max_tokens, raw)))


async def chunk_section_dynamic(sec: Section, cfg: Settings) -> List[Chunk]:
    sentences = split_into_sentences(sec.text)
    if not sentences:
        return []

    density = _density_score(
        sec.text,
        cfg.DENSITY_WEIGHT_SYMBOLS,
        cfg.DENSITY_WEIGHT_AVGWORD,
        cfg.DENSITY_WEIGHT_NUMBERS,
    )
    target = _target_tokens(
        cfg.CHUNK_BASE_TOKENS, cfg.CHUNK_MIN_TOKENS, cfg.CHUNK_MAX_TOKENS, density
    )
    max_tokens = cfg.LABSE_MAX_TOKENS - 32

    # Sentence-level overlap count
    overlap_ratio = cfg.CHUNK_SENT_OVERLAP_RATIO
    if sec.type in ("list", "table", "code"):
        overlap_ratio = max(overlap_ratio, 0.2)
    overlap_sentences = max(1, int(round(len(sentences) * overlap_ratio)))

    chunks: List[Chunk] = []
    i = 0
    while i < len(sentences):
        current_sentences: List[str] = []
        current_tokens = 0
        start_i = i

        while i < len(sentences):
            s = sentences[i]
            s_tokens = count_labse_tokens(s)
            # Safety: handle extremely long single sentence
            if s_tokens > max_tokens:
                # naive split inside sentence by punctuation/space
                midpoint = max(1, len(s) // 2)
                left = s[:midpoint]
                right = s[midpoint:]
                sentences[i:i+1] = [left, right]
                continue

            if current_tokens + s_tokens <= min(target, max_tokens):
                current_sentences.append(s)
                current_tokens += s_tokens
                i += 1
            else:
                break

        if not current_sentences:
            # Force include one sentence to make progress
            s = sentences[i]
            s_tokens = count_labse_tokens(s)
            current_sentences = [s]
            current_tokens = min(s_tokens, max_tokens)
            i += 1

        chunk_text = " ".join(current_sentences).strip()
        chunk = Chunk(
            id=str(uuid.uuid4()),
            text=chunk_text,
            tokens=count_labse_tokens(chunk_text),
            meta={
                "section_title": sec.headingPath[-1] if sec.headingPath else None,
                "heading_path": sec.headingPath,
                "page_start": sec.pageStart,
                "page_end": sec.pageEnd,
                "char_start": sec.charStart,
                "char_end": sec.charEnd,
                "type": sec.type,
                "target_tokens": target,
                "mode": "DYNAMIC",
            },
        )
        chunks.append(chunk)

        # advance with overlap
        i = start_i + max(1, len(current_sentences) - overlap_sentences)

    return chunks


