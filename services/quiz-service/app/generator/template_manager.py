"""
Quiz Template Manager and Validators
Builds enhanced prompts and validates generated quizzes.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List

from app.generator.difficulty_controller import DifficultyController
from app.generator.content_filter import ContentFilter


class QuizTemplateManager:
    def __init__(self) -> None:
        self.difficulty_controller = DifficultyController()
        self.content_filter = ContentFilter()

    def build_enhanced_prompt(
        self,
        subject: str,
        total_count: int,
        difficulty_mix: Dict[str, Any],
        context_blocks: List[Dict[str, Any]],
    ) -> str:
        filtered_contexts = self.content_filter.filter_context_blocks(context_blocks or [])
        difficulty_instructions = self.difficulty_controller.enhance_difficulty_prompt(difficulty_mix or {})
        content_rules = self.content_filter.generate_content_filtering_prompt()

        enhanced_prompt = f"""
ENHANCED QUIZ GENERATION SYSTEM

Subject: {subject}
Total Questions: {total_count}

{difficulty_instructions}

{content_rules}

QUALITY VALIDATION:
- Before finalizing each question, verify it meets difficulty criteria
- Ensure question tests substantial academic content, not document metadata
- Include difficulty_validation object in response with actual vs target counts

CONTEXT BLOCKS (pre-filtered for quality):
{json.dumps(filtered_contexts, ensure_ascii=False, indent=2)}
"""
        return enhanced_prompt

    def validate_generated_quiz(self, quiz_response: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            "difficulty_accuracy": {},
            "content_quality_score": 0,
            "citation_completeness": 0,
            "overall_score": 0,
        }
        questions = list(quiz_response.get("questions", []) or [])
        total_sources = 0
        present_sources = 0
        for q in questions:
            target_diff = (q.get("metadata", {}).get("difficulty") or "").lower()
            assessed = self.difficulty_controller._assess_difficulty(q.get("stem", ""))
            if target_diff:
                bucket = results["difficulty_accuracy"].setdefault(target_diff, {"correct": 0, "total": 0})
                bucket["total"] += 1
                if assessed == target_diff:
                    bucket["correct"] += 1
            sources = list((q.get("metadata", {}).get("sources") or []))
            total_sources += 1
            if sources:
                present_sources += 1
        results["citation_completeness"] = (present_sources / total_sources) if total_sources else 0.0
        # simple proxy for quality: presence of difficulty_validation entries
        has_validation = sum(1 for q in questions if (q.get("metadata", {}).get("difficulty_validation") is not None))
        results["content_quality_score"] = (has_validation / max(len(questions), 1))
        results["overall_score"] = 0.5 * results["citation_completeness"] + 0.5 * results["content_quality_score"]
        return results


class QuizGenerationValidator:
    @staticmethod
    def handle_insufficient_content(context_blocks: List[Dict[str, Any]], required_count: int) -> Dict[str, Any]:
        if len(context_blocks or []) < required_count:
            available = len(context_blocks or [])
            return {
                "status": "insufficient_content",
                "available_contexts": available,
                "requested_count": required_count,
                "recommendation": f"Reduce question count to {available} or provide more content",
            }
        return {"status": "sufficient"}

    @staticmethod
    def detect_language_consistency(context_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Placeholder: assume upstream detection is used in orchestrator
        # Here we just report unknown; integrate with app.lang if needed.
        return {"status": "unknown"}


