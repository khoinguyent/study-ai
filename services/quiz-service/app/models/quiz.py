from __future__ import annotations
from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    questions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    document_id: Mapped[str] = mapped_column(String, nullable=True)
    subject_id: Mapped[str] = mapped_column(String, nullable=True)
    category_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    quiz_id: Mapped[str] = mapped_column(String, primary_key=True)
    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    position: Mapped[int] = mapped_column(nullable=False)


