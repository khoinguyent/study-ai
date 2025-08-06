from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"

class DocumentBase(BaseModel):
    filename: str
    content_type: str

class DocumentCreate(DocumentBase):
    user_id: str

class DocumentResponse(DocumentBase):
    id: UUID
    status: DocumentStatus
    file_size: int
    created_at: datetime
    
    class Config:
        from_attributes = True 