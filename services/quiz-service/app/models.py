from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Note: Quiz class is now defined in models/quiz.py to avoid duplication

class CustomDocumentSet(Base):
    __tablename__ = "custom_document_sets"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_ids = Column(JSON, nullable=False)  # List of document IDs
    user_id = Column(String, nullable=False, index=True)
    subject_id = Column(String, nullable=True)  # Optional subject context
    category_id = Column(String, nullable=True)  # Optional category context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 