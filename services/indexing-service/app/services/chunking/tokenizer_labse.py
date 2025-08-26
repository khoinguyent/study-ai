import hashlib
from functools import lru_cache
from typing import Dict

from transformers import AutoTokenizer


_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/LaBSE")
    return _tokenizer


_cache: Dict[str, int] = {}


def count_labse_tokens(text: str) -> int:
    """Count WordPiece tokens using LaBSE tokenizer.

    Cached by text hash to avoid memory bloat with large strings.
    """
    if not text:
        return 0
    # Build a stable hash for caching
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if text_hash in _cache:
        return _cache[text_hash]
    tokenizer = _get_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)
    count = len(tokens)
    # simple LRU-like behavior: cap size
    if len(_cache) > 8000:
        _cache.clear()
    _cache[text_hash] = count
    return count


