from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON, Boolean

from ..database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    quiz_id: Mapped[str] = mapped_column(String, ForeignKey("quizzes.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    seed: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")  # active|submitted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    questions: Mapped[list["QuizSessionQuestion"]] = relationship(
        "QuizSessionQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="QuizSessionQuestion.display_index.asc()",
    )


class QuizSessionQuestion(Base):
    """Per-session materialized question snapshot.

    Note: We intentionally avoid the table name "quiz_questions" to not clash with
    the existing mapping model declared in app/models/quiz.py.
    """

    __tablename__ = "quiz_session_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_sessions.id"), nullable=False, index=True)
    display_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Minimal normalized render fields
    q_type: Mapped[str] = mapped_column(String, nullable=False)  # mcq | true_false | fill_in_blank | short_answer
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)  # [{id,text}] for MCQ
    blanks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Private payload (answers, explanations, rubrics, etc.)
    private_payload: Mapped[dict | None] = mapped_column(JSON, nullable=False)

    # Citations/meta (safe to stream)
    meta_data: Mapped[dict | None] = mapped_column("meta_data", JSON, nullable=True)
    
    # Server-only truth; never expose
    source_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # original index in raw JSON

    # Relationships
    session: Mapped[QuizSession] = relationship("QuizSession", back_populates="questions")


class QuizSessionAnswer(Base):
    """User answers for quiz session questions"""
    
    __tablename__ = "quiz_session_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_sessions.id"), nullable=False)
    session_question_id: Mapped[str] = mapped_column(String, ForeignKey("quiz_session_questions.id"), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # user response (display space)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[float | None] = mapped_column(Integer, nullable=True)  # or Numeric if you prefer fractional
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


