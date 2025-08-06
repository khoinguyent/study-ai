from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class SubjectSearchRequest(BaseModel):
    query: str
    subject_id: Optional[int] = None
    category_id: Optional[int] = None
    limit: Optional[int] = 10

class SearchResponse(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    similarity_score: float

class ChunkResponse(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    created_at: datetime 