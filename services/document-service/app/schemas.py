from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    subject_id: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    filename: str
    content_type: str
    file_size: int
    subject_id: Optional[str] = None
    category_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    file_path: str
    status: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    subject: Optional[SubjectResponse] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True

class DocumentGroupResponse(BaseModel):
    subject: SubjectResponse
    categories: List[CategoryResponse]
    documents: List[DocumentResponse]
    total_documents: int
    total_size: int

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str 