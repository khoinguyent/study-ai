from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[Dict[str, Any]]

class QuizResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    questions: List[Dict[str, Any]]
    user_id: str
    document_id: Optional[str] = None
    subject_id: Optional[int] = None
    category_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizGenerationRequest(BaseModel):
    topic: str
    difficulty: str = "medium"  # easy, medium, hard
    num_questions: int = 5
    document_id: Optional[str] = None
    subject_id: Optional[int] = None
    category_id: Optional[int] = None
    use_only_subject_content: bool = True  # Only use content from the subject/category

class SubjectQuizGenerationRequest(BaseModel):
    subject_id: int
    topic: Optional[str] = None  # If not provided, use subject name
    difficulty: str = "medium"
    num_questions: int = 5
    use_only_subject_content: bool = True

class CategoryQuizGenerationRequest(BaseModel):
    category_id: int
    topic: Optional[str] = None  # If not provided, use category name
    difficulty: str = "medium"
    num_questions: int = 5
    use_only_category_content: bool = True

class QuizGenerationResponse(BaseModel):
    quiz_id: int
    title: str
    questions_count: int
    generation_time: float
    source_type: str  # "document", "subject", "category"
    source_id: Optional[str] = None 