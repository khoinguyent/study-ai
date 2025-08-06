from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.sql import func
import uuid
from .database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String, nullable=False, index=True)
    subject_id = Column(Integer, nullable=True, index=True)  # For subject-based search
    category_id = Column(Integer, nullable=True, index=True)  # For category-based search
    content = Column(Text, nullable=False)
    embedding = Column(VECTOR(384), nullable=False)  # 384-dimensional vector
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 