"""
Database models for Leaf Quiz Service
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class LeafQuiz(Base):
    """Leaf Quiz model using T5 transformers"""
    
    __tablename__ = "leaf_quizzes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(JSON, nullable=False)  # Store generated questions as JSON
    status = Column(String, default="pending")  # pending, processing, completed, failed
    user_id = Column(String, nullable=False)
    subject_id = Column(String, nullable=True)
    category_id = Column(String, nullable=True)
    document_id = Column(String, nullable=True)
    
    # Generation metadata
    source_text = Column(Text, nullable=True)  # Original text used for generation
    generation_model = Column(String, nullable=True)  # Model used for generation
    generation_time = Column(Integer, nullable=True)  # Time taken in seconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<LeafQuiz(id={self.id}, title='{self.title}', status='{self.status}')>"


class QuestionGenerationJob(Base):
    """Track question generation jobs"""
    
    __tablename__ = "question_generation_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    source_text = Column(Text, nullable=False)
    num_questions = Column(Integer, nullable=False)
    difficulty = Column(String, nullable=True)
    
    # Job metadata
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<QuestionGenerationJob(id={self.id}, quiz_id={self.quiz_id}, status='{self.status}')>" 