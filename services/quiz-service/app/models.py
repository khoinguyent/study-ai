from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from .database import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(JSON, nullable=False)  # List of question objects
    user_id = Column(String, nullable=False)
    document_id = Column(String, nullable=True)  # Reference to source document
    subject_id = Column(Integer, nullable=True)  # Reference to source subject
    category_id = Column(Integer, nullable=True)  # Reference to source category
    status = Column(String, default="draft")  # draft, published, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CustomDocumentSet(Base):
    __tablename__ = "custom_document_sets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_ids = Column(JSON, nullable=False)  # List of document IDs
    user_id = Column(String, nullable=False, index=True)
    subject_id = Column(Integer, nullable=True)  # Optional subject context
    category_id = Column(Integer, nullable=True)  # Optional category context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 