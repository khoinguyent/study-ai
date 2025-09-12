from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .services.session_service import create_session_from_quiz
from .services.grading_service import upsert_answers, grade_session
from .services.evaluation_service import evaluator
from .models.quiz_session import QuizSession, QuizSessionQuestion, QuizSessionAnswer

router = APIRouter(prefix="/quizzes", tags=["quiz-sessions"])


@router.post("/{quiz_id}/sessions")
def start_quiz_session(
    quiz_id: str,
    user_id: Optional[str] = None,
    shuffle: bool = True,
    db: Session = Depends(get_db),
):
    """Create a new quiz session from a quiz"""
    try:
        sess, created = create_session_from_quiz(db, quiz_id=quiz_id, user_id=user_id, shuffle=shuffle)
        return {"session_id": str(sess.id), "count": len(created)}
    except ValueError:
        raise HTTPException(status_code=404, detail="Quiz not found")


# Display-safe view (no answers/explanations)
@router.get("/sessions/{session_id}/view")
def view_session(session_id: str, db: Session = Depends(get_db)):
    """Get a safe view of a quiz session without answers or explanations"""
    sess = db.query(QuizSession).filter_by(id=session_id).one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    
    qs = (db.query(QuizSessionQuestion)
            .filter_by(session_id=session_id)
            .order_by(QuizSessionQuestion.display_index.asc())
            .all())
    
    def public(q: QuizSessionQuestion):
        data = {
            "session_question_id": str(q.id),
            "index": q.display_index,
            "type": q.q_type,
            "stem": q.stem,
            "citations": (q.metadata or {}).get("sources") or []
        }
        if q.q_type == "mcq":
            # Ensure options in shape {id,text}[]
            raw_opts = list(q.options or [])
            if raw_opts and isinstance(raw_opts[0], dict) and 'id' in raw_opts[0] and 'text' in raw_opts[0]:
                data["options"] = [{"id": str(o.get('id')), "text": str(o.get('text', ''))} for o in raw_opts]
            else:
                data["options"] = [
                    {"id": f"opt_{i}", "text": str(opt) if not isinstance(opt, dict) else str(opt.get("text", ""))}
                    for i, opt in enumerate(raw_opts)
                ]
        elif q.q_type == "true_false":
            data["options"] = [{"id": "true", "text": "True"}, {"id": "false", "text": "False"}]
        elif q.q_type == "fill_in_blank":
            data["blanks"] = q.blanks or 1
        return data
    
    return {
        "session_id": str(sess.id),
        "quiz_id": str(sess.quiz_id),
        "questions": [public(x) for x in qs]
    }


# Save (partial) answers
@router.post("/sessions/{session_id}/answers")
def save_answers(session_id: str, body: dict, db: Session = Depends(get_db)):
    """Save user answers for a quiz session"""
    answers = body.get("answers") or []
    replace = bool(body.get("replace", True))
    upsert_answers(db, session_id, answers, replace=replace)
    return {"ok": True, "count": len(answers)}


# Submit and grade (legacy endpoint)
@router.post("/sessions/{session_id}/submit")
def submit_session(session_id: str, db: Session = Depends(get_db)):
    """Submit a quiz session for grading (legacy endpoint)"""
    result = grade_session(db, session_id)
    return result


# Enhanced submit and evaluate endpoint
@router.post("/sessions/{session_id}/evaluate")
def evaluate_session(session_id: str, body: dict, db: Session = Depends(get_db)):
    """Submit and evaluate a quiz session with detailed results"""
    try:
        # Get user answers from request body (can be dict or array)
        user_answers_raw = body.get("answers", {})
        metadata = body.get("metadata", {})

        # Build lookup for question types to guide normalization
        questions = (
            db.query(QuizSessionQuestion)
            .filter_by(session_id=session_id)
            .all()
        )
        qtype_by_id = {str(q.id): q.q_type for q in questions}

        # Normalize legacy array format into a map keyed by questionId
        # Accept shapes like: [{ session_question_id, type, response }]
        if isinstance(user_answers_raw, list):
            answers_map = {}
            for item in user_answers_raw:
                if not isinstance(item, dict):
                    # skip unrecognized entries
                    continue
                qid = (
                    item.get("session_question_id")
                    or item.get("questionId")
                    or item.get("question_id")
                    or item.get("id")
                )
                if not qid:
                    continue
                answers_map[str(qid)] = {
                    "_raw": item.get("response")
                        if "response" in item
                        else item.get("value")
                        if "value" in item
                        else item.get("answer")
                        if "answer" in item
                        else item.get("choices")
                        if "choices" in item
                        else item.get("text"),
                    "_type": item.get("type"),
                }
        elif isinstance(user_answers_raw, dict):
            answers_map = user_answers_raw
        else:
            answers_map = {}

        def normalize_value(question_id: str, answer_value):
            """Normalize a primitive/list/dict answer to evaluator input."""
            qtype = qtype_by_id.get(str(question_id))

            # If already in expected evaluator shape, pass-through
            if isinstance(answer_value, dict):
                # If it looks like our already-converted payload, return as-is
                if any(k in answer_value for k in [
                    "selected_option_id", "selected_option_ids", "answer_bool", "blanks", "text"
                ]):
                    return answer_value
                # If it is the frontend "kind" shape, convert accordingly
                kind = answer_value.get("kind") if isinstance(answer_value, dict) else None
                if kind == "single":
                    return {"selected_option_id": answer_value.get("choiceId")}
                if kind == "multiple":
                    return {"selected_option_ids": answer_value.get("choiceIds", [])}
                if kind == "boolean":
                    return {"answer_bool": answer_value.get("value")}
                if kind == "blanks":
                    return {"blanks": answer_value.get("values", [])}
                if kind == "text":
                    return {"text": answer_value.get("value", "")}
                # If it contains a raw value under different keys
                if "_raw" in answer_value:
                    return normalize_value(question_id, answer_value.get("_raw"))

            # Primitive types
            if isinstance(answer_value, bool):
                return {"answer_bool": answer_value}
            if isinstance(answer_value, (int, float)):
                # Treat numeric as selected option id or text depending on type
                if qtype in ("short_answer", "text"):
                    return {"text": str(answer_value)}
                return {"selected_option_id": str(answer_value)}
            if isinstance(answer_value, str):
                if qtype == "true_false":
                    v = answer_value.strip().lower()
                    if v in ("true", "t", "1", "yes"):   # map common truthy
                        return {"answer_bool": True}
                    if v in ("false", "f", "0", "no"):
                        return {"answer_bool": False}
                if qtype in ("short_answer", "text"):
                    return {"text": answer_value}
                return {"selected_option_id": answer_value}
            if isinstance(answer_value, list):
                # Decide between multi-select vs blanks by question type
                if qtype == "fill_blank":
                    return {"blanks": answer_value}
                return {"selected_option_ids": answer_value}

            # Fallback to empty structure
            return {}

        # Convert all answers
        converted_answers = {}
        for question_id, answer in answers_map.items():
            try:
                converted_answers[str(question_id)] = normalize_value(str(question_id), answer)
            except Exception:
                # Never fail hard on a single malformed answer
                converted_answers[str(question_id)] = {}
        
        # Evaluate the session
        result = evaluator.evaluate_quiz_session(db, session_id, converted_answers)
        
        # Add metadata
        if metadata:
            result["metadata"] = metadata
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# Get evaluation results
@router.get("/sessions/{session_id}/results")
def get_session_results(session_id: str, db: Session = Depends(get_db)):
    """Get evaluation results for a submitted session"""
    session = db.query(QuizSession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "submitted":
        raise HTTPException(status_code=400, detail="Session not yet submitted")
    
    # Get answers with scores
    answers = db.query(QuizSessionAnswer).filter_by(session_id=session_id).all()
    questions = db.query(QuizSessionQuestion).filter_by(session_id=session_id).all()
    
    # Calculate totals
    total_score = sum(a.score or 0 for a in answers)
    max_score = sum((q.private_payload or {}).get('points', 1.0) for q in questions)
    correct_count = sum(1 for a in answers if a.is_correct)
    
    # Calculate percentage and grade
    percentage_score = (total_score / max_score * 100) if max_score > 0 else 0
    grade_info = evaluator.get_grade_with_percentage(percentage_score)
    
    # Create breakdown
    breakdown_by_type = {}
    for answer in answers:
        question = next((q for q in questions if q.id == answer.session_question_id), None)
        if question:
            q_type = question.q_type
            if q_type not in breakdown_by_type:
                breakdown_by_type[q_type] = {"correct": 0, "total": 0, "percentage": 0}
            
            breakdown_by_type[q_type]["total"] += 1
            if answer.is_correct:
                breakdown_by_type[q_type]["correct"] += 1
    
    # Calculate percentages
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
        "grade": grade_info,
        "breakdown": {
            "byType": breakdown_by_type
        },
        "submittedAt": session.created_at.isoformat()
    }


