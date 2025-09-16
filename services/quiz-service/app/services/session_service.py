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
        raw_options = raw.get("options") or {}
        correct_answer = raw.get("answer", "opt_1")
        
        # Handle new format: options as object with opt_X keys
        if isinstance(raw_options, dict):
            # New format: {"opt_1": "Option A", "opt_2": "Option B", ...}
            options_dict = raw_options
            priv = {"correct_answer": correct_answer, "options": options_dict}
            base["options"] = options_dict  # Keep as dict for new format
        else:
            # Legacy format: ["Option A", "Option B", ...]
            raw_options_list = list(raw_options)
            options = []
            for opt in raw_options_list:
                if isinstance(opt, dict):
                    options.append(opt.get('text', ''))
                else:
                    options.append(str(opt))
            
            correct_option = raw.get("correct_option")
            if isinstance(correct_option, int):
                priv = {"correct_option_index": correct_option, "options": options}
            else:
                priv = {"correct_option_index": 0, "options": options}  # default to first option
            base["options"] = options[:]  # will be replaced with [{id,text}] after shuffle
        
    elif qt == "true_false":
        correct_option = raw.get("correct_option")
        if isinstance(correct_option, int):
            # correct_option: 0 = True, 1 = False
            priv = {"answer_bool": correct_option == 0}
        else:
            priv = {"answer_bool": True}  # default to True
        
    elif qt == "fill_in_blank":
        blanks_raw = raw.get("blanks")
        if isinstance(blanks_raw, list):
            blanks = blanks_raw
            base["blanks"] = max(1, len(blanks) or 1)
            priv = {"accepted": [[b] for b in blanks]}  # wrap each as list-of-accepted
        elif isinstance(blanks_raw, int):
            base["blanks"] = max(1, blanks_raw)
            # For single blank, use correct_answer if available
            correct_answer = raw.get("correct_answer")
            if correct_answer:
                priv = {"accepted": [[correct_answer]]}
            else:
                priv = {"accepted": [[""]]}  # empty accepted answer
        else:
            base["blanks"] = 1
            priv = {"accepted": [[""]]}  # empty accepted answer

        # Normalize stem placeholders to a single style (____)
        # Some sources may contain mixed patterns like {{1}} and __________
        try:
            import re
            normalized_stem = stem
            # Remove any double-curly placeholders entirely
            normalized_stem = re.sub(r"\{\{\d+\}\}", "____", normalized_stem)
            # Normalize any underscore runs (3+ underscores) to a single token
            normalized_stem = re.sub(r"_{3,}", "____", normalized_stem)
            # If no explicit blank present but accepted answers exist, append a trailing blank for safety
            if base.get("blanks", 1) >= 1 and "____" not in normalized_stem:
                normalized_stem = normalized_stem.strip()
            base["stem"] = normalized_stem
        except Exception:
            # If anything goes wrong, keep original stem
            base["stem"] = stem
        
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
            # Check if using new format (dict with opt_X keys)
            if isinstance(priv.get("options"), dict):
                # New format: options are already in opt_X format, just shuffle the order
                options_dict = priv.get("options", {})
                correct_answer = priv.get("correct_answer", "opt_1")
                
                # Create list of opt_X keys and shuffle them
                opt_keys = list(options_dict.keys())
                if shuffle:
                    rng.shuffle(opt_keys)
                
                # Create shuffled options maintaining opt_X keys
                shuffled_options = {}
                for key in opt_keys:
                    shuffled_options[key] = options_dict[key]
                
                options_out = shuffled_options
                priv = {"correct_answer": correct_answer, "options": shuffled_options}
            else:
                # Legacy format: handle as before
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
                    if p == priv.get("correct_option_index"):
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


