from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from .enums import QUESTION_TYPE, DIFFICULTY
from ..database import Base

class QuestionBank(Base):
    __tablename__ = "question_bank"

    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    subject_id: Mapped[str] = mapped_column(String, nullable=False)

    type: Mapped[str] = mapped_column(QUESTION_TYPE, nullable=False)
    difficulty: Mapped[str] = mapped_column(DIFFICULTY, nullable=False, default="medium")

    stem: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    question_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False)

    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)

    # LLM trace fields
    llm_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_prompt_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_raw_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    llm_run_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


