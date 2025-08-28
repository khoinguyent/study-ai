from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class CustomDocumentSet(Base):
    __tablename__ = "custom_document_sets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    document_ids: Mapped[dict] = mapped_column(JSONB, nullable=False)  # List of document IDs
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String, nullable=True)  # Optional subject context
    category_id: Mapped[str] = mapped_column(String, nullable=True)  # Optional category context
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
