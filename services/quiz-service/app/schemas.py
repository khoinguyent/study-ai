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