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

class DocumentSelectionRequest(BaseModel):
    """Request for quiz generation with specific document selection"""
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    document_ids: List[str]  # List of specific document IDs to use
    subject_id: Optional[int] = None  # For context/validation
    category_id: Optional[int] = None  # For context/validation

class CustomDocumentSetRequest(BaseModel):
    """Request for creating a custom document set for quiz generation"""
    name: str
    description: Optional[str] = None
    document_ids: List[str]
    subject_id: Optional[int] = None
    category_id: Optional[int] = None

class CustomDocumentSetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    document_ids: List[str]
    subject_id: Optional[int] = None
    category_id: Optional[int] = None
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class QuizGenerationResponse(BaseModel):
    quiz_id: int
    title: str
    questions_count: int
    generation_time: float
    source_type: str  # "document", "subject", "category", "custom_set"
    source_id: Optional[str] = None
    documents_used: List[str] = []  # List of document IDs used 