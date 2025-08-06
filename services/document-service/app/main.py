from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import httpx

from .database import get_db
from .models import Base, Document
from .schemas import DocumentCreate, DocumentResponse, DocumentStatus
from .config import settings
from .services.document_processor import DocumentProcessor
from .services.storage_service import StorageService

app = FastAPI(
    title="Document Service",
    description="Document upload and processing service",
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

# Initialize services
document_processor = DocumentProcessor()
storage_service = StorageService()

async def verify_auth_token(authorization: str = Depends(Header)):
    """Verify JWT token with auth service"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/verify",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()["user_id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "document-service"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type"
        )
    
    # Create document record
    document_id = str(uuid.uuid4())
    document = Document(
        id=document_id,
        user_id=user_id,
        filename=file.filename,
        content_type=file.content_type,
        status=DocumentStatus.UPLOADED,
        file_size=0  # Will be updated after upload
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    try:
        # Upload to S3
        file_content = await file.read()
        s3_key = f"documents/{user_id}/{document_id}/{file.filename}"
        await storage_service.upload_file(s3_key, file_content, file.content_type)
        
        # Update document with file size
        document.file_size = len(file_content)
        document.s3_key = s3_key
        document.status = DocumentStatus.PROCESSING
        db.commit()
        
        # Trigger processing task asynchronously
        asyncio.create_task(document_processor.process_document(document_id, user_id, db))
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            status=document.status,
            file_size=document.file_size,
            created_at=document.created_at
        )
        
    except Exception as e:
        # Cleanup on error
        document.status = DocumentStatus.ERROR
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            content_type=doc.content_type,
            status=doc.status,
            file_size=doc.file_size,
            created_at=doc.created_at
        )
        for doc in documents
    ]

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        status=document.status,
        file_size=document.file_size,
        created_at=document.created_at
    )

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from S3
    if document.s3_key:
        await storage_service.delete_file(document.s3_key)
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 