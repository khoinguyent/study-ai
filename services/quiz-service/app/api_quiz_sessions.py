from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .services.session_service import create_session_from_quiz
from .services.grading_service import upsert_answers, grade_session
from .models.quiz_session import QuizSession, QuizSessionQuestion

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
            data["options"] = q.options or []   # [{id,text}]
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


# Submit and grade
@router.post("/sessions/{session_id}/submit")
def submit_session(session_id: str, db: Session = Depends(get_db)):
    """Submit a quiz session for grading"""
    result = grade_session(db, session_id)
    return result


