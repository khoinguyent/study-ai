"""
Content Filter
Filters low-quality context blocks and generates prompt rules to avoid metadata.
"""

from __future__ import annotations

from typing import List, Dict, Any


class ContentFilter:
    def __init__(self) -> None:
        self.metadata_indicators = {
            "vietnamese": ["đề cương", "bài tập", "môn học", "chương", "trang"],
            "english": ["outline", "assignment", "course", "chapter", "page"],
            "structural": ["title", "header", "section", "part", "table of contents"],
        }

    def filter_context_blocks(self, context_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered: List[Dict[str, Any]] = []
        for block in context_blocks or []:
            if self._is_substantial_content(block):
                filtered.append(block)
        return filtered

    def _is_substantial_content(self, context_block: Dict[str, Any]) -> bool:
        text = str((context_block or {}).get("text", "")).lower()

        # Minimum substantive length
        if len(text.split()) < 15:
            return False

        # Skip structural/metadata heavy blocks
        metadata_ratio = self._calculate_metadata_ratio(text)
        if metadata_ratio > 0.4:
            return False

        # Avoid pure structural lines
        if self._is_structural_only(text):
            return False

        return True

    def _calculate_metadata_ratio(self, text: str) -> float:
        words = text.split()
        if not words:
            return 0.0
        metadata_count = 0
        indicators = sum(self.metadata_indicators.values(), [])
        for word in words:
            if any(ind in word for ind in indicators):
                metadata_count += 1
        return metadata_count / len(words)

    def _is_structural_only(self, text: str) -> bool:
        # crude signal for enumerations and headings without concepts
        if text.strip().endswith(":") and len(text.split()) <= 8:
            return True
        if text.strip().lower().startswith(("chapter", "section", "part")) and len(text.split()) <= 8:
            return True
        return False

    def generate_content_filtering_prompt(self) -> str:
        return (
            "CONTENT FILTERING RULES:\n"
            "- EXCLUDE questions about document structure, titles, headers, course codes.\n"
            "- EXCLUDE meta-questions about document type or administrative info.\n"
            "- FOCUS ON substantive academic concepts and knowledge within content.\n"
            "- Ensure minimum 15 words of substantial content before creating questions.\n"
            "- Verify questions test actual subject matter understanding."
        )


def preprocess_contexts(context_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filter_obj = ContentFilter()
    quality_blocks = filter_obj.filter_context_blocks(context_blocks or [])
    # Optionally attach quality flags (lightweight placeholder score)
    for block in quality_blocks:
        text = str(block.get("text", ""))
        quality = min(max(len(text.split()) / 50.0, 0.0), 1.0)
        block["content_quality_score"] = quality
        block["is_substantial"] = quality > 0.6
    return quality_blocks


