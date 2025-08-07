from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: Union[List[Dict[str, Any]], Dict[str, Any]]
    status: str = "draft"

class QuizResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    questions: Union[List[Dict[str, Any]], Dict[str, Any]]
    status: str
    user_id: str
    subject_id: Optional[str] = None
    category_id: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuizGenerationRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    subject_id: Optional[str] = None
    category_id: Optional[str] = None
    document_id: Optional[str] = None

class SubjectQuizGenerationRequest(BaseModel):
    subject_id: str
    topic: Optional[str] = None
    difficulty: str = "medium"
    num_questions: int = 5

class CategoryQuizGenerationRequest(BaseModel):
    category_id: str
    topic: Optional[str] = None
    difficulty: str = "medium"
    num_questions: int = 5

class DocumentSelectionRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    document_ids: List[str]
    subject_id: Optional[str] = None
    category_id: Optional[str] = None

class CustomDocumentSetRequest(BaseModel):
    name: str
    description: Optional[str] = None
    document_ids: List[str]
    subject_id: Optional[str] = None
    category_id: Optional[str] = None

class CustomDocumentSetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    document_ids: List[str]
    user_id: str
    subject_id: Optional[str] = None
    category_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuizGenerationResponse(BaseModel):
    quiz_id: str
    title: str
    questions_count: int
    generation_time: float
    source_type: str
    source_id: str
    documents_used: Optional[List[str]] = None
    status: str  # Added status field 