"""
Pydantic schemas for Leaf Quiz Service
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class QuestionOption(BaseModel):
    """Individual question option"""
    text: str
    is_correct: bool = False


class GeneratedQuestion(BaseModel):
    """Generated question structure"""
    id: str
    question: str
    options: List[QuestionOption]
    correct_answer: int  # Index of correct option
    explanation: Optional[str] = None


class LeafQuizCreate(BaseModel):
    """Create a new leaf quiz"""
    title: str
    description: Optional[str] = None
    questions: Union[List[GeneratedQuestion], Dict[str, Any]]
    status: str = "draft"


class LeafQuizResponse(BaseModel):
    """Leaf quiz response"""
    id: str
    title: str
    description: Optional[str] = None
    questions: Union[List[GeneratedQuestion], Dict[str, Any]]
    status: str
    user_id: str
    subject_id: Optional[str] = None
    category_id: Optional[str] = None
    document_id: Optional[str] = None
    source_text: Optional[str] = None
    generation_model: Optional[str] = None
    generation_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionGenerationRequest(BaseModel):
    """Request to generate questions from text"""
    source_text: str
    num_questions: int = 5
    difficulty: str = "medium"  # easy, medium, hard
    topic: Optional[str] = None
    subject_id: Optional[str] = None
    category_id: Optional[str] = None
    document_id: Optional[str] = None
    
    @field_validator('num_questions')
    def validate_num_questions(cls, v):
        if v < 1 or v > 20:
            raise ValueError('Number of questions must be between 1 and 20')
        return v


class QuestionGenerationResponse(BaseModel):
    """Response for question generation request"""
    quiz_id: str
    title: str
    questions_count: int
    generation_time: float
    status: str
    source_type: str
    source_id: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    quiz_id: str
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 