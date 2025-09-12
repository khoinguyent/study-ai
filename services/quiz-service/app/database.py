from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create SQLAlchemy engine
engine = create_engine(os.getenv('DATABASE_URL', 'postgresql://postgres:password@quiz-db:5432/quiz_db'))

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Import all models here to ensure they are registered with Base
from .models import *  # noqa: E402,F401

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    # Ensure all metadata is created without dropping existing data
    # In production/dev we should never drop tables on service restart.
    Base.metadata.create_all(bind=engine)