"""
Difficulty Controller
Provides difficulty taxonomy guidance and lightweight difficulty assessment
"""

from __future__ import annotations

from typing import Dict, Any, List
import re


class DifficultyController:
    """Maps desired difficulty to cues and generates prompt instructions.

    Also provides a lightweight heuristic to assess question stems.
    """

    def __init__(self) -> None:
        self.difficulty_patterns: Dict[str, Dict[str, Any]] = {
            "easy": {
                "keywords": [
                    "define", "list", "identify", "what is", "when", "where"
                ],
                "cognitive_level": ["remember", "understand"],
            },
            "medium": {
                "keywords": [
                    "compare", "explain", "analyze", "relate", "predict"
                ],
                "cognitive_level": ["apply", "analyze"],
            },
            "hard": {
                "keywords": [
                    "evaluate", "critique", "design", "justify", "synthesize"
                ],
                "cognitive_level": ["evaluate", "create"],
            },
        }

    def enhance_difficulty_prompt(self, difficulty_mix: Dict[str, Any]) -> str:
        """Generate difficulty-specific instructions for the prompt."""
        lines: List[str] = []
        for level, count in (difficulty_mix or {}).items():
            crit = self.difficulty_patterns.get(level, {})
            keywords = ", ".join(crit.get("keywords", []))
            cog = ", ".join(crit.get("cognitive_level", []))
            lines.append(
                f"For {count} {level.upper()} questions:\n"
                f"- Use indicative verbs/phrases: {keywords}\n"
                f"- Target Bloom levels: {cog}\n"
                f"- Verify that the stem matches {level} complexity before finalizing."
            )
        return "\n".join(lines)

    def validate_question_difficulty(self, question_text: str, target_difficulty: str) -> bool:
        actual = self._assess_difficulty(question_text)
        return actual == target_difficulty

    def _assess_difficulty(self, question_text: str) -> str:
        """Heuristic assessment based on verbs, structure, and length.

        This is intentionally simple and fast; it is used for post-checks
        and telemetry, not to hard-fail generations.
        """
        text = (question_text or "").lower().strip()
        if not text:
            return "easy"

        num_words = len(text.split())
        has_multi_clause = bool(re.search(r",|;| because | therefore | however ", text))
        has_compare = any(k in text for k in ["compare", "contrast", "versus"]) or " vs " in text
        has_reasoning = any(k in text for k in ["explain", "analyze", "why", "how", "predict"]) or has_multi_clause
        has_synthesis = any(k in text for k in ["evaluate", "justify", "design", "critique", "synthesize"]) or has_compare

        if has_synthesis and num_words >= 10:
            return "hard"
        if has_reasoning and num_words >= 8:
            return "medium"

        # default to easy
        return "easy"


