import json
import hashlib
import random
import uuid
from typing import Dict, Any, List, Tuple

from sqlalchemy.orm import Session

from app.models.quiz_session import QuizSession, QuizSessionQuestion
from app.models.quiz import Quiz


def _rng(seed_str: str) -> random.Random:
    """Create deterministic random number generator from seed string"""
    return random.Random(int(hashlib.sha1(seed_str.encode()).hexdigest(), 16) % (10**8))


def _canon_type(t: str) -> str:
    """Canonicalize question type strings"""
    t = (t or "").strip().lower().replace(" ", "_").replace("-", "_")
    if t in ("mcq", "multiple_choice"):
        return "mcq"
    if t in ("true_false", "truefalse"):
        return "true_false"
    if t in ("fill_blank", "fill_in_blank", "fill_in_the_blank"):
        return "fill_in_blank"
    if t in ("short", "short_answer"):
        return "short_answer"
    return t


def _norm_item(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Normalize a raw question item from LLM JSON"""
    qt = _canon_type(raw.get("type", ""))
    stem = (raw.get("question") or "").strip()
    meta = (raw.get("metadata") or {})
    sources = (meta.get("sources") or [])
    
    base = {
        "q_type": qt,
        "stem": stem,
        "metadata": {"sources": sources},
        "source_index": idx,
    }
    
    priv = {}
    
    if qt == "mcq":
        options = list(raw.get("options") or [])
        answer_index = int(raw.get("answer", -1))
        priv = {"options": options, "answer_index": answer_index}
        base["options"] = options[:]  # will be replaced with [{id,text}] after shuffle
        
    elif qt == "true_false":
        priv = {"answer_bool": bool(raw.get("answer"))}
        
    elif qt == "fill_in_blank":
        blanks = list(raw.get("blanks") or [])
        base["blanks"] = max(1, len(blanks) or 1)
        priv = {"accepted": [[b] for b in blanks]}  # wrap each as list-of-accepted
        
    elif qt == "short_answer":
        priv = raw.get("rubric") or {}
        
    base["private_payload"] = priv
    return base


def create_session_from_quiz(db: Session, quiz_id: str, user_id: str | None = None, shuffle: bool = True) -> Tuple[QuizSession, List[QuizSessionQuestion]]:
    """Create a quiz session from quiz questions data"""
    quiz: Quiz = db.query(Quiz).filter(Quiz.id == quiz_id).one()
    
    # Use questions field directly
    raw = quiz.questions if isinstance(quiz.questions, str) else json.dumps(quiz.questions)
    
    data = json.loads(raw or "{}")
    raw_items = list(data.get("questions") or [])
    items = [_norm_item(q, i) for i, q in enumerate(raw_items)]

    sess = QuizSession(quiz_id=quiz.id, user_id=user_id, seed="")
    db.add(sess)
    db.flush()
    sess.seed = str(sess.id)

    rng = _rng(sess.seed)
    order = list(range(len(items)))
    if shuffle:
        rng.shuffle(order)

    created: List[QuizSessionQuestion] = []
    for disp_idx, src_i in enumerate(order):
        it = items[src_i]
        qtype = it["q_type"]
        priv = it["private_payload"]

        options_out = None
        if qtype == "mcq":
            raw_opts = list(priv.get("options") or [])
            perm = list(range(len(raw_opts)))
            if shuffle:
                rng.shuffle(perm)
            # assign stable option IDs for this session question
            mapped = []
            correct_ids = []
            for j, p in enumerate(perm):
                oid = str(uuid.uuid4())
                mapped.append({"id": oid, "text": raw_opts[p]})
                if p == priv.get("answer_index"):
                    correct_ids.append(oid)
            options_out = mapped
            priv = {"correct_option_ids": correct_ids}

        qq = QuizSessionQuestion(
            session_id=sess.id,
            display_index=disp_idx,
            q_type=qtype,
            stem=it["stem"],
            options=options_out,
            blanks=it.get("blanks"),
            metadata=it.get("metadata"),
            private_payload=priv,
            source_index=it.get("source_index"),
        )
        db.add(qq)
        created.append(qq)

    db.commit()
    db.refresh(sess)
    for x in created:
        db.refresh(x)
    return sess, created


