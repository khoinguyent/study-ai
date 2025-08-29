import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from .database import get_db
from .models.quiz_session import QuizSession, QuizSessionQuestion


router = APIRouter(prefix="/quiz-sessions", tags=["quiz-sessions"])


def _public_view(q: QuizSessionQuestion) -> dict:
    base = {
        "session_question_id": str(q.id),
        "index": q.display_index,
        "type": q.q_type,
        "stem": q.stem,
        "citations": (q.metadata or {}).get("sources") or [],
    }
    if q.q_type == "mcq":
        options_list = q.options or []
        base["options"] = [
            {"label": chr(65 + i), "text": t} for i, t in enumerate(options_list)
        ]
    elif q.q_type == "true_false":
        base["options"] = [{"label": "A", "text": "True"}, {"label": "B", "text": "False"}]
    elif q.q_type == "fill_in_blank":
        base["blanks"] = q.blanks or 1
    return base


@router.get("/{session_id}/stream")
async def stream_session(session_id: str, db: Session = Depends(get_db)):
    sess = db.query(QuizSession).filter(QuizSession.id == session_id).one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    qs = (
        db.query(QuizSessionQuestion)
        .filter(QuizSessionQuestion.session_id == sess.id)
        .order_by(QuizSessionQuestion.display_index.asc())
        .all()
    )

    async def sse_gen():
        start = {"event": "start", "data": {"session_id": str(sess.id), "count": len(qs)}}
        yield f"event: {start['event']}\n"
        yield "data: " + json.dumps(start["data"], ensure_ascii=False) + "\n\n"
        for q in qs:
            ev = {"event": "question", "data": _public_view(q)}
            yield f"event: {ev['event']}\n"
            yield "data: " + json.dumps(ev["data"], ensure_ascii=False) + "\n\n"
        done = {"event": "done", "data": {"count": len(qs)}}
        yield f"event: {done['event']}\n"
        yield "data: " + json.dumps(done["data"], ensure_ascii=False) + "\n\n"

    return EventSourceResponse(sse_gen(), headers={"Cache-Control": "no-cache"})


