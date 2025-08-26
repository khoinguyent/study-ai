from typing import List


def fixed_chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Simple fixed-size character chunking with overlap (backward compatible)."""
    if chunk_size <= 0:
        return [text]
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 5)

    chunks: List[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(text), step):
        chunk_text = text[i:i + chunk_size]
        if chunk_text.strip():
            chunks.append(chunk_text)
    return chunks


