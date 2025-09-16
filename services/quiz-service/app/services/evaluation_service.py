"""
Quiz Evaluation Service
Handles point calculation, grading, and evaluation logic for quiz submissions
"""
import re
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.quiz_session import QuizSession, QuizSessionQuestion, QuizSessionAnswer
from app.services.eval_utils import matches_any, normalize


class QuizEvaluator:
    """Handles quiz evaluation and point calculation"""
    
    def __init__(self):
        self.grade_thresholds = {
            'A': 90,  # 90-100%
            'B': 80,  # 80-89%
            'C': 70,  # 70-79%
            'D': 60,  # 60-69%
            'F': 0    # 0-59%
        }
    
    def _ensure_payload_dict(self, payload: Any) -> Dict[str, Any]:
        """Coerce DB stored private_payload into a dictionary.
        Some rows may store JSON as a string; parse it defensively.
        """
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    def _safe_float(self, value: Any, default: float) -> float:
        """Coerce value to float with a default for None/invalid."""
        try:
            if value is None:
                return float(default)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str) and value.strip() != "":
                return float(value)
            return float(default)
        except Exception:
            return float(default)

    def calculate_points(self, question: QuizSessionQuestion, user_answer: Dict[str, Any]) -> Tuple[float, bool, str]:
        """
        Calculate points for a single question
        
        Returns:
            Tuple of (score, is_correct, explanation)
        """
        question_type = question.q_type
        private_payload = self._ensure_payload_dict(question.private_payload or {})
        max_points = self._safe_float(private_payload.get('points', 1.0), 1.0)
        
        # Defensive normalization: accept primitives/lists and coerce to expected dict shape
        if not isinstance(user_answer, dict):
            if question_type == "mcq":
                if isinstance(user_answer, list):
                    user_answer = {"selected_option_ids": user_answer}
                else:
                    user_answer = {"selected_option_id": str(user_answer)}
            elif question_type == "true_false":
                if isinstance(user_answer, str):
                    v = user_answer.strip().lower()
                    user_answer = {"answer_bool": v in ("true", "t", "1", "yes")}
                else:
                    user_answer = {"answer_bool": bool(user_answer)}
            elif question_type == "fill_in_blank":
                if not isinstance(user_answer, list):
                    user_answer = [str(user_answer)]
                user_answer = {"blanks": user_answer}
            elif question_type in ("short_answer", "text"):
                user_answer = {"text": str(user_answer)}
            else:
                user_answer = {}
        
        if question_type == "mcq":
            return self._evaluate_multiple_choice(question, user_answer, max_points)
        elif question_type == "true_false":
            return self._evaluate_true_false(question, user_answer, max_points)
        elif question_type == "fill_in_blank":
            return self._evaluate_fill_blank(question, user_answer, max_points)
        elif question_type == "short_answer":
            return self._evaluate_short_answer(question, user_answer, max_points)
        else:
            return 0.0, False, "Unknown question type"
    
    def _evaluate_multiple_choice(self, question: QuizSessionQuestion, user_answer: Dict[str, Any], max_points: float) -> Tuple[float, bool, str]:
        """Evaluate multiple choice questions"""
        private_payload = self._ensure_payload_dict(question.private_payload or {})
        selected_option_id = user_answer.get("selected_option_id")
        
        # Check if using new format (opt_X keys)
        correct_answer = private_payload.get("correct_answer")
        if correct_answer and isinstance(correct_answer, str) and correct_answer.startswith("opt_"):
            # New format: correct_answer is opt_X
            correct_option_ids = {correct_answer}
        else:
            # Legacy format: handle UUIDs and indices
            raw_correct = private_payload.get("correct_option_ids")
            if isinstance(raw_correct, list):
                correct_option_ids = set(str(x.get('id') if isinstance(x, dict) else x) for x in raw_correct)
            elif isinstance(raw_correct, str):
                # accept comma-separated or single id
                parts = [p.strip() for p in raw_correct.split(',')] if ',' in raw_correct else [raw_correct]
                correct_option_ids = set(parts)
            else:
                correct_option_ids = set()

            # If still empty, attempt to derive from correct_option_index or meta_data.original_question.correct_option
            if not correct_option_ids:
                # First try correct_option_index from private_payload
                correct_index = private_payload.get('correct_option_index')
                if isinstance(correct_index, int):
                    correct_option_ids = {f"opt_{correct_index}"}
                else:
                    # Synthesize ids as opt_{index} to match frontend choiceIds
                    try:
                        meta = getattr(question, 'meta_data', None) or {}
                        if isinstance(meta, str):
                            meta = json.loads(meta)
                        original = (meta or {}).get('original_question') or {}
                        correct_index = original.get('correct_option')
                        if isinstance(correct_index, int):
                            correct_option_ids = {f"opt_{correct_index}"}
                    except Exception:
                        pass
            
            # Handle case where correct_option_ids is still empty (fallback to first option)
            if not correct_option_ids:
                correct_option_ids = {"opt_0"}  # Default to first option
        
        if not selected_option_id:
            return 0.0, False, "No answer provided"
        
        is_correct = selected_option_id in correct_option_ids
        score = max_points if is_correct else 0.0
        
        explanation = private_payload.get("explanation", "")
        if is_correct:
            feedback = f"Correct! {explanation}" if explanation else "Correct answer!"
        else:
            # Get the user's selected option text for better feedback
            user_option_text = self._get_option_text_by_id(question, selected_option_id)
            
            # Get correct answer text - handle both new and legacy formats
            if isinstance(question.options, dict):
                # New format: options is dict with opt_X keys
                correct_text = question.options.get(correct_answer, "")
            else:
                # Legacy format: normalize options which could be list of dicts or list of strings
                norm_options = []
                for opt in (question.options or []):
                    if isinstance(opt, dict):
                        norm_options.append({
                            'id': str(opt.get('id')) if opt.get('id') is not None else None,
                            'text': str(opt.get('text', ''))
                        })
                    else:
                        norm_options.append({'id': None, 'text': str(opt)})
                correct_options = [opt for opt in norm_options if opt.get('id') in correct_option_ids]
                correct_text = ", ".join([opt.get('text', '') for opt in correct_options])
            
            # Provide better feedback with user's selection
            user_selection = f"You selected: {user_option_text}" if user_option_text else "You selected: No answer"
            feedback = f"Incorrect. {user_selection}. The correct answer was: {correct_text}. {explanation}" if explanation else f"Incorrect. {user_selection}. The correct answer was: {correct_text}"
        
        return score, is_correct, feedback
    
    def _evaluate_true_false(self, question: QuizSessionQuestion, user_answer: Dict[str, Any], max_points: float) -> Tuple[float, bool, str]:
        """Evaluate true/false questions"""
        private_payload = self._ensure_payload_dict(question.private_payload or {})
        user_answer_bool = user_answer.get("answer_bool")
        correct_answer_bool = private_payload.get("answer_bool")
        
        if user_answer_bool is None:
            return 0.0, False, "No answer provided"
        
        is_correct = user_answer_bool == correct_answer_bool
        score = max_points if is_correct else 0.0
        
        explanation = private_payload.get("explanation", "")
        if is_correct:
            feedback = f"Correct! {explanation}" if explanation else "Correct answer!"
        else:
            user_text = "True" if user_answer_bool else "False"
            correct_text = "True" if correct_answer_bool else "False"
            feedback = f"Incorrect. You selected: {user_text}. The correct answer was: {correct_text}. {explanation}" if explanation else f"Incorrect. You selected: {user_text}. The correct answer was: {correct_text}"
        
        return score, is_correct, feedback
    
    def _evaluate_fill_blank(self, question: QuizSessionQuestion, user_answer: Dict[str, Any], max_points: float) -> Tuple[float, bool, str]:
        """Evaluate fill-in-the-blank questions"""
        private_payload = self._ensure_payload_dict(question.private_payload or {})
        user_blanks = list(user_answer.get("blanks") or [])
        accepted_answers = list(private_payload.get("accepted") or [])
        
        if not user_blanks or not accepted_answers:
            return 0.0, False, "No answer provided"
        
        # Calculate partial credit
        total_blanks = max(len(accepted_answers), len(user_blanks), 1)
        correct_blanks = 0
        
        for i in range(min(len(user_blanks), len(accepted_answers))):
            # Fix: Ensure accepted_answers[i] is a list for matches_any function
            accepted_list = accepted_answers[i] if isinstance(accepted_answers[i], list) else [accepted_answers[i]]
            if matches_any(user_blanks[i], accepted_list):
                correct_blanks += 1
        
        # Calculate percentage score
        percentage = correct_blanks / total_blanks
        score = max_points * percentage
        is_correct = (percentage == 1.0)
        
        explanation = private_payload.get("explanation", "")
        if is_correct:
            feedback = f"Perfect! All blanks correct. {explanation}" if explanation else "Perfect! All blanks correct."
        elif percentage > 0:
            feedback = f"Partially correct ({correct_blanks}/{total_blanks} blanks). {explanation}" if explanation else f"Partially correct ({correct_blanks}/{total_blanks} blanks)."
        else:
            feedback = f"Incorrect. {explanation}" if explanation else "Incorrect."
        
        return score, is_correct, feedback
    
    def _evaluate_short_answer(self, question: QuizSessionQuestion, user_answer: Dict[str, Any], max_points: float) -> Tuple[float, bool, str]:
        """Evaluate short answer questions"""
        private_payload = self._ensure_payload_dict(question.private_payload or {})
        user_text = user_answer.get("text", "")
        
        if not user_text.strip():
            return 0.0, False, "No answer provided"
        
        # Get evaluation criteria
        key_points = private_payload.get("key_points") or []
        threshold = self._safe_float(private_payload.get("threshold", 0.6), 0.6)
        min_words = int(self._safe_float(private_payload.get("min_words", 0), 0))
        
        # Check minimum word requirement
        word_count = len(user_text.split())
        if min_words > 0 and word_count < min_words:
            return 0.0, False, f"Answer too short. Minimum {min_words} words required, got {word_count}."
        
        # Calculate score based on key points
        normalized_text = normalize(user_text)
        total_weight = 0.0
        earned_weight = 0.0
        
        for point in key_points:
            # Handle both string and dict formats for key_points
            if isinstance(point, str):
                # Simple string format - treat as keyword with default weight
                weight = 0.2
                keywords = [point]
            elif isinstance(point, dict):
                # Dict format with weight and aliases
                weight = self._safe_float(point.get("weight", 0.2), 0.2)
                keywords = [point.get("text", "")] + list(point.get("aliases") or [])
            else:
                continue
                
            total_weight += weight
            
            # Check for keyword matches
            for keyword in keywords:
                if not keyword:
                    continue
                if keyword.startswith("re:") and re.search(keyword[3:], normalized_text):
                    earned_weight += weight
                    break
                elif normalize(keyword) in normalized_text:
                    earned_weight += weight
                    break
        
        # Calculate percentage score
        if total_weight == 0:
            return 0.0, False, "No evaluation criteria available"
        
        percentage = min(earned_weight / total_weight, 1.0)
        score = max_points * percentage
        is_correct = (percentage >= threshold)
        
        explanation = private_payload.get("explanation", "")
        if is_correct:
            feedback = f"Good answer! Score: {percentage:.1%}. {explanation}" if explanation else f"Good answer! Score: {percentage:.1%}."
        else:
            feedback = f"Answer needs improvement. Score: {percentage:.1%}. {explanation}" if explanation else f"Answer needs improvement. Score: {percentage:.1%}."
        
        return score, is_correct, feedback
    
    def _sanitize_user_answer(self, question: QuizSessionQuestion, user_answer: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sanitized version of user answer for display (no correct answers leaked)"""
        question_type = question.q_type
        sanitized = {}
        
        if question_type == "mcq":
            selected_option_id = user_answer.get("selected_option_id")
            if selected_option_id:
                # Find the actual option text for display
                option_text = self._get_option_text_by_id(question, selected_option_id)
                sanitized["selected_option"] = option_text or f"Option {selected_option_id}"
            else:
                sanitized["selected_option"] = "No answer"
                
        elif question_type == "true_false":
            answer_bool = user_answer.get("answer_bool")
            if answer_bool is not None:
                sanitized["answer"] = "True" if answer_bool else "False"
            else:
                sanitized["answer"] = "No answer"
                
        elif question_type == "fill_in_blank":
            blanks = user_answer.get("blanks", [])
            sanitized["answers"] = blanks if blanks else ["No answer"]
            
        elif question_type == "short_answer":
            text = user_answer.get("text", "")
            sanitized["answer"] = text if text.strip() else "No answer"
            
        return sanitized
    
    def _get_option_text_by_id(self, question: QuizSessionQuestion, option_id: str) -> str:
        """Get the actual text of an option by its ID"""
        if not question.options:
            return ""
        
        # Handle new format: options as dict with opt_X keys
        if isinstance(question.options, dict):
            return str(question.options.get(option_id, ""))
        
        # Handle legacy formats
        if option_id.startswith("opt_"):
            # Extract index from opt_X format (opt_1 = index 0, opt_2 = index 1, etc.)
            try:
                index = int(option_id.split("_")[1]) - 1  # Convert opt_1 to index 0, opt_2 to index 1
                if isinstance(question.options, list):
                    if 0 <= index < len(question.options):
                        option = question.options[index]
                        if isinstance(option, dict):
                            return str(option.get('text', ''))
                        else:
                            return str(option)
            except (ValueError, IndexError):
                pass
        
        # Handle UUID format
        for option in question.options:
            if isinstance(option, dict):
                if str(option.get('id')) == str(option_id):
                    return str(option.get('text', ''))
            else:
                # Handle case where options might be stored differently
                if str(option) == str(option_id):
                    return str(option)
        return ""
    
    def calculate_percentage_score(self, total_score: float, max_score: float) -> float:
        """Calculate percentage score"""
        if max_score == 0:
            return 0.0
        return (total_score / max_score) * 100
    
    def assign_grade(self, percentage: float) -> str:
        """Assign letter grade based on percentage"""
        for grade, threshold in self.grade_thresholds.items():
            if percentage >= threshold:
                return grade
        return 'F'
    
    def get_grade_with_percentage(self, percentage: float) -> dict:
        """Get both letter grade and exact percentage"""
        grade = self.assign_grade(percentage)
        return {
            "letter": grade,
            "percentage": round(percentage, 1),
            "display": f"{grade} ({percentage:.1f}%)"
        }
    
    def evaluate_quiz_session(self, db: Session, session_id: str, user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a complete quiz session
        
        Args:
            db: Database session
            session_id: Quiz session ID
            user_answers: User's answers in AnswerMap format
        
        Returns:
            Complete evaluation result
        """
        # Get session and questions
        session = db.query(QuizSession).filter_by(id=session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        questions = db.query(QuizSessionQuestion).filter_by(session_id=session_id).order_by(QuizSessionQuestion.display_index).all()
        
        # Evaluate each question
        question_evaluations = []
        total_score = 0.0
        max_score = 0.0
        correct_count = 0
        
        for question in questions:
            # Get user answer for this question
            user_answer = user_answers.get(question.id, {})
            
            # Calculate points
            score, is_correct, feedback = self.calculate_points(question, user_answer)
            question_max_points = self._safe_float(self._ensure_payload_dict(question.private_payload or {}).get('points', 1.0), 1.0)
            
            # Update totals
            total_score += score
            max_score += question_max_points
            if is_correct:
                correct_count += 1
            
            # Create sanitized user answer for display
            sanitized_user_answer = self._sanitize_user_answer(question, user_answer)
            
            # Store evaluation (remove correct answers for security)
            question_evaluations.append({
                "questionId": str(question.id),
                "type": question.q_type,
                "userAnswer": sanitized_user_answer,
                "isCorrect": is_correct,
                "score": score,
                "maxScore": question_max_points,
                "percentage": (score / question_max_points * 100) if question_max_points > 0 else 0,
                "explanation": feedback
            })
            
            # Update database
            answer = db.query(QuizSessionAnswer).filter_by(
                session_id=session_id, 
                session_question_id=question.id
            ).first()
            
            if answer:
                answer.payload = user_answer
                answer.is_correct = is_correct
                answer.score = score
                db.add(answer)
            else:
                new_answer = QuizSessionAnswer(
                    session_id=session_id,
                    session_question_id=question.id,
                    payload=user_answer,
                    is_correct=is_correct,
                    score=score
                )
                db.add(new_answer)
        
        # Calculate overall results
        percentage_score = self.calculate_percentage_score(total_score, max_score)
        grade_info = self.get_grade_with_percentage(percentage_score)
        
        # Update session status
        session.status = "submitted"
        db.add(session)
        db.commit()
        
        # Create breakdown by question type
        breakdown_by_type = {}
        for eval_result in question_evaluations:
            q_type = eval_result["type"]
            if q_type not in breakdown_by_type:
                breakdown_by_type[q_type] = {"correct": 0, "total": 0, "percentage": 0}
            
            breakdown_by_type[q_type]["total"] += 1
            if eval_result["isCorrect"]:
                breakdown_by_type[q_type]["correct"] += 1
        
        # Calculate percentages for each type
        for q_type in breakdown_by_type:
            total = breakdown_by_type[q_type]["total"]
            correct = breakdown_by_type[q_type]["correct"]
            breakdown_by_type[q_type]["percentage"] = (correct / total * 100) if total > 0 else 0
        
        return {
            "sessionId": str(session.id),
            "quizId": str(session.quiz_id),
            "userId": session.user_id,
            "totalScore": round(total_score, 2),
            "maxScore": round(max_score, 2),
            "scorePercentage": round(percentage_score, 2),
            "correctCount": correct_count,
            "totalQuestions": len(questions),
            "questionEvaluations": question_evaluations,
            "breakdown": {
                "byType": breakdown_by_type,
                "byQuestion": question_evaluations
            },
            "grade": grade_info,
            "submittedAt": datetime.utcnow().isoformat()
        }


# Global evaluator instance
evaluator = QuizEvaluator()
