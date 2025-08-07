from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx

from .database import get_db, create_tables
from .models import Base, DocumentChunk
from .schemas import SearchRequest, SearchResponse, ChunkResponse, SubjectSearchRequest
from .config import settings
from .services.vector_service import VectorService

app = FastAPI(
    title="Indexing Service",
    description="Document indexing and vector search service with subject-based grouping",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Initialize services
vector_service = VectorService()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "indexing-service"}

@app.post("/index", response_model=dict)
async def index_document(document_id: str, db: Session = Depends(get_db)):
    """Index a document by processing it into chunks and generating embeddings"""
    try:
        # For now, create mock document data since we can't access document service
        # In production, this would fetch from document service with proper authentication
        mock_document = {
            "id": document_id,
            "filename": f"document_{document_id}.txt",
            "content": f"Sample content for document {document_id}. This is a placeholder for the actual document content.",
            "subject_id": "9e329560-b3db-48b9-9867-630bc7d8dc42",  # History
            "category_id": "f967c95a-db9d-4442-9957-f553e5dd5aa3"  # Tay Son Rebellion
        }
        
        # Process document and create chunks
        chunks = await vector_service.process_document(document_id, mock_document)
        
        # Store chunks in database with subject/category information
        for chunk in chunks:
            db_chunk = DocumentChunk(
                document_id=document_id,
                subject_id=mock_document["subject_id"],
                category_id=mock_document["category_id"],
                content=chunk["content"],
                embedding=chunk["embedding"],
                chunk_index=chunk["index"]
            )
            db.add(db_chunk)
        
        db.commit()
        
        return {
            "message": "Document indexed successfully",
            "chunks_created": len(chunks),
            "document_id": document_id,
            "subject_id": mock_document["subject_id"],
            "category_id": mock_document["category_id"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )

@app.post("/search", response_model=List[SearchResponse])
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search for relevant document chunks using vector similarity"""
    try:
        # Generate embedding for search query
        query_embedding = await vector_service.generate_embedding(request.query)
        
        # Search for similar chunks
        results = await vector_service.search_similar_chunks(
            query_embedding, 
            request.limit or 10,
            db
        )
        
        return [
            SearchResponse(
                chunk_id=str(result.chunk_id),
                document_id=result.document_id,
                content=result.content,
                similarity_score=1 - result.distance  # Convert distance to similarity score
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@app.post("/search/subject", response_model=List[SearchResponse])
async def search_within_subject(
    request: SubjectSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for relevant document chunks within a specific subject"""
    try:
        # Generate embedding for search query
        query_embedding = await vector_service.generate_embedding(request.query)
        
        # Search for similar chunks within the subject
        results = await vector_service.search_similar_chunks_within_subject(
            query_embedding, 
            request.subject_id,
            request.limit or 10,
            db
        )
        
        return [
            SearchResponse(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                content=result.content,
                similarity_score=result.similarity_score
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subject search failed: {str(e)}"
        )

@app.post("/search/category", response_model=List[SearchResponse])
async def search_within_category(
    request: SubjectSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for relevant document chunks within a specific category"""
    try:
        # Generate embedding for search query
        query_embedding = await vector_service.generate_embedding(request.query)
        
        # Search for similar chunks within the category
        results = await vector_service.search_similar_chunks_within_category(
            query_embedding, 
            request.category_id,
            request.limit or 10,
            db
        )
        
        return [
            SearchResponse(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                content=result.content,
                similarity_score=result.similarity_score
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Category search failed: {str(e)}"
        )

@app.get("/chunks/{document_id}", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get all chunks for a specific document"""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()
    
    return [
        ChunkResponse(
            id=str(chunk.id),
            document_id=chunk.document_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at
        )
        for chunk in chunks
    ]

@app.get("/chunks/subject/{subject_id}", response_model=List[ChunkResponse])
async def get_subject_chunks(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """Get all chunks for a specific subject"""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.subject_id == subject_id
    ).order_by(DocumentChunk.chunk_index).all()
    
    return [
        ChunkResponse(
            id=str(chunk.id),
            document_id=chunk.document_id,
            subject_id=chunk.subject_id,
            category_id=chunk.category_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at
        )
        for chunk in chunks
    ]

@app.get("/chunks/category/{category_id}", response_model=List[ChunkResponse])
async def get_category_chunks(
    category_id: str,
    db: Session = Depends(get_db)
):
    """Get all chunks for a specific category"""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.category_id == category_id
    ).order_by(DocumentChunk.chunk_index).all()
    
    return [
        ChunkResponse(
            id=str(chunk.id),
            document_id=chunk.document_id,
            subject_id=chunk.subject_id,
            category_id=chunk.category_id,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            created_at=chunk.created_at
        )
        for chunk in chunks
    ]

@app.delete("/chunks/{document_id}")
async def delete_document_chunks(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete all chunks for a specific document"""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete()
    
    db.commit()
    
    return {
        "message": "Document chunks deleted successfully",
        "chunks_deleted": chunks
    }

@app.delete("/chunks/subject/{subject_id}")
async def delete_subject_chunks(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """Delete all chunks for a specific subject"""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.subject_id == subject_id
    ).all()
    
    for chunk in chunks:
        db.delete(chunk)
    
    db.commit()
    
    return {"message": f"Deleted {len(chunks)} chunks for subject {subject_id}"}

@app.get("/stats/subject/{subject_id}")
async def get_subject_stats(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific subject"""
    total_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.subject_id == subject_id
    ).count()
    
    unique_documents = db.query(DocumentChunk.document_id).filter(
        DocumentChunk.subject_id == subject_id
    ).distinct().count()
    
    return {
        "subject_id": subject_id,
        "total_chunks": total_chunks,
        "unique_documents": unique_documents
    }

@app.get("/stats/category/{category_id}")
async def get_category_stats(
    category_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific category"""
    total_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.category_id == category_id
    ).count()
    
    unique_documents = db.query(DocumentChunk.document_id).filter(
        DocumentChunk.category_id == category_id
    ).distinct().count()
    
    return {
        "category_id": category_id,
        "total_chunks": total_chunks,
        "unique_documents": unique_documents
    }

@app.get("/test-index")
async def test_indexing(db: Session = Depends(get_db)):
    """Test indexing with mock data"""
    try:
        # Create mock document data
        mock_document = {
            "id": "test-document-123",
            "filename": "test.txt",
            "content": "This is a test document for indexing.",
            "subject_id": "9e329560-b3db-48b9-9867-630bc7d8dc42",
            "category_id": "f967c95a-db9d-4442-9957-f553e5dd5aa3"
        }
        
        # Process document and create chunks
        chunks = await vector_service.process_document("test-document-123", mock_document)
        
        # Store chunks in database
        for chunk in chunks:
            db_chunk = DocumentChunk(
                document_id="test-document-123",
                subject_id=mock_document["subject_id"],
                category_id=mock_document["category_id"],
                content=chunk["content"],
                embedding=chunk["embedding"],
                chunk_index=chunk["index"]
            )
            db.add(db_chunk)
        
        db.commit()
        
        return {
            "message": "Test indexing successful",
            "chunks_created": len(chunks),
            "document_id": "test-document-123"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test indexing failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 