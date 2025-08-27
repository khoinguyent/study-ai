from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Numeric
from sqlalchemy.dialects.postgresql import ARRAY, SMALLINT, JSONB
from .enums import ATTEMPT_STATUS
from ..db import Base

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    attempt_id: Mapped[str] = mapped_column(String, primary_key=True)
    quiz_id: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(ATTEMPT_STATUS, nullable=False, default="in_progress")
    seed: Mapped[int] = mapped_column(Integer, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    time_limit_sec: Mapped[Optional[int]] = mapped_column(Integer)
    grader_version: Mapped[str] = mapped_column(String, nullable=False, default="v1")
    rubric_hash: Mapped[Optional[str]] = mapped_column(String)

    total_score: Mapped[Optional[float]] = mapped_column(Numeric(5,2))
    max_score: Mapped[Optional[float]] = mapped_column(Numeric(5,2))

class AttemptItem(Base):
    __tablename__ = "attempt_items"

    attempt_id: Mapped[str] = mapped_column(String, primary_key=True)
    item_no: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[str] = mapped_column(String, nullable=False)

    option_perm: Mapped[Optional[list[int]]] = mapped_column(ARRAY(SMALLINT), nullable=True)
    revealed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    attempt_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    item_no: Mapped[int] = mapped_column(nullable=False)

    response: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(4,2), nullable=False, default=0)
    correct: Mapped[Optional[bool]] = mapped_column()
    auto_graded: Mapped[bool] = mapped_column(nullable=False, default=True)
    grading_meta: Mapped[Optional[dict]] = mapped_column(JSONB)

    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)


