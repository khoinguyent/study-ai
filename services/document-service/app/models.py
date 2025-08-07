from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    categories = relationship("Category", back_populates="subject", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="subject")

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subject = relationship("Subject", back_populates="categories")
    documents = relationship("Document", back_populates="category")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")
    user_id = Column(String, nullable=False, index=True)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subject = relationship("Subject", back_populates="documents")
    category = relationship("Category", back_populates="documents") 