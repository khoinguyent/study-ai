import re
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models.quiz_session import QuizSession, QuizSessionQuestion, QuizSessionAnswer
from app.services.eval_utils import matches_any, normalize


def upsert_answers(db: Session, session_id: str, answers: list[dict], replace: bool = True):
    """Upsert user answers for a quiz session"""
    # answers: [{session_question_id, type, response:{...}}]
    existing = {a.session_question_id: a for a in db.query(QuizSessionAnswer).filter_by(session_id=session_id).all()}
    
    for item in answers:
        sq_id = item["session_question_id"]
        payload = item.get("response") or {}
        row = existing.get(sq_id)
        
        if row and replace:
            row.payload = payload
            db.add(row)
        elif not row:
            db.add(QuizSessionAnswer(session_id=session_id, session_question_id=sq_id, payload=payload))
    
    db.commit()


def grade_session(db: Session, session_id: str) -> dict:
    """Grade a quiz session and return results"""
    sess = db.query(QuizSession).filter_by(id=session_id).one()
    sqs = db.query(QuizSessionQuestion).filter_by(session_id=session_id).all()
    ans = {a.session_question_id: a for a in db.query(QuizSessionAnswer).filter_by(session_id=session_id).all()}

    perq = []
    total = 0.0
    
    for q in sorted(sqs, key=lambda x: x.display_index):
        a = ans.get(q.id)
        payload = (a.payload if a else {}) or {}
        pv = q.private_payload or {}
        score = 0.0
        correct = False

        if q.q_type == "mcq":
            sel = payload.get("selected_option_id")
            correct_ids = set((pv.get("correct_option_ids") or []))
            correct = bool(sel and sel in correct_ids)
            score = 1.0 if correct else 0.0

        elif q.q_type == "true_false":
            correct = (payload.get("answer_bool") == pv.get("answer_bool"))
            score = 1.0 if correct else 0.0

        elif q.q_type == "fill_in_blank":
            user_blanks = list(payload.get("blanks") or [])
            accepted = list(pv.get("accepted") or [])
            k = max(len(accepted), len(user_blanks), 1)
            hit = 0
            for i in range(min(len(user_blanks), len(accepted))):
                if matches_any(user_blanks[i], accepted[i]):
                    hit += 1
            score = hit / k
            correct = (score == 1.0)

        elif q.q_type == "short_answer":
            # minimal scorer: if rubric exists, basic keyword match; else 0
            kp = (pv.get("key_points") or [])
            thresh = float(pv.get("threshold", 0.6))
            nt = normalize(payload.get("text", ""))
            got = 0.0
            for p in kp:
                w = float(p.get("weight", 0.2))
                bag = [p.get("text", "")] + list(p.get("aliases") or [])
                if any((k.startswith("re:") and re.search(k[3:], nt)) or (normalize(k) in nt) for k in bag if k):
                    got += w
            if got > 1.0:
                got = 1.0
            score = got
            correct = (got >= thresh)

        total += score
        if a:
            a.is_correct = correct
            a.score = score
            db.add(a)

        perq.append({
            "session_question_id": str(q.id),
            "type": q.q_type,
            "is_correct": bool(correct),
            "score": float(round(score, 3))
        })

    sess.status = "submitted"
    db.add(sess)
    db.commit()

    return {
        "session_id": str(sess.id),
        "score": float(round(total, 3)),
        "max_score": float(len(sqs)),
        "per_question": perq,
        "breakdown": {}  # optional: aggregate by type
    }
