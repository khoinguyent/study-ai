from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/study_ai')

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv('DEBUG', 'False').lower() == 'true'
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
db_session = scoped_session(SessionLocal)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create tables"""
    from models import Base
    
    # Import all models to ensure they are registered
    from models import User, Document, DocumentChunk, Quiz, ProcessingTask
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Enable pgvector extension if not already enabled
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
        conn.commit()

def check_db_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def get_vector_similarity_scores(embedding, document_ids=None, limit=10):
    """
    Get similar document chunks using vector similarity search
    
    Args:
        embedding: The query embedding vector
        document_ids: Optional list of document IDs to filter by
        limit: Maximum number of results to return
    
    Returns:
        List of (chunk_id, similarity_score, content) tuples
    """
    from models import DocumentChunk
    
    # Build the query
    query = db_session.query(
        DocumentChunk.id,
        DocumentChunk.content,
        DocumentChunk.embedding.cosine_distance(embedding).label('distance')
    ).filter(DocumentChunk.embedding.isnot(None))
    
    # Filter by document IDs if provided
    if document_ids:
        query = query.join(DocumentChunk.document).filter(
            DocumentChunk.document_id.in_(document_ids)
        )
    
    # Order by similarity and limit results
    results = query.order_by(text('distance')).limit(limit).all()
    
    return [(result.id, 1 - result.distance, result.content) for result in results] 