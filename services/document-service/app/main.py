from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import httpx
from typing import List, Optional

from .database import get_db
from .models import Base, Document, Subject, Category
from .schemas import (
    DocumentCreate, DocumentResponse, DocumentStatus, DocumentUploadResponse,
    SubjectCreate, SubjectResponse, SubjectUpdate,
    CategoryCreate, CategoryResponse, CategoryUpdate,
    DocumentGroupResponse
)
from .config import settings
from .services.document_processor import DocumentProcessor
from .services.storage_service import StorageService

app = FastAPI(
    title="Document Service",
    description="Document upload and processing service with subject/category management",
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

# Subject Management Endpoints
@app.post("/subjects", response_model=SubjectResponse)
async def create_subject(
    subject: SubjectCreate,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Create a new subject"""
    # Check if subject name already exists for this user
    existing_subject = db.query(Subject).filter(
        Subject.name == subject.name,
        Subject.user_id == user_id
    ).first()
    
    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject with this name already exists"
        )
    
    db_subject = Subject(
        name=subject.name,
        description=subject.description,
        user_id=user_id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    
    return db_subject

@app.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all subjects for a user"""
    subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
    return subjects

@app.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific subject"""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject

@app.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Update a subject"""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    for field, value in subject_update.dict(exclude_unset=True).items():
        setattr(subject, field, value)
    
    db.commit()
    db.refresh(subject)
    return subject

@app.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a subject and all its categories"""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Delete all categories in this subject
    db.query(Category).filter(Category.subject_id == subject_id).delete()
    
    # Update documents to remove subject reference
    db.query(Document).filter(Document.subject_id == subject_id).update({
        Document.subject_id: None,
        Document.category_id: None
    })
    
    db.delete(subject)
    db.commit()
    
    return {"message": "Subject deleted successfully"}

# Category Management Endpoints
@app.post("/categories", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    # Verify subject exists and belongs to user
    subject = db.query(Subject).filter(
        Subject.id == category.subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if category name already exists in this subject
    existing_category = db.query(Category).filter(
        Category.name == category.name,
        Category.subject_id == category.subject_id
    ).first()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists in this subject"
        )
    
    db_category = Category(
        name=category.name,
        description=category.description,
        subject_id=category.subject_id,
        user_id=user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

@app.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    subject_id: Optional[int] = Query(None),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List categories, optionally filtered by subject"""
    query = db.query(Category).join(Subject).filter(Subject.user_id == user_id)
    
    if subject_id:
        query = query.filter(Category.subject_id == subject_id)
    
    categories = query.all()
    return categories

@app.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific category"""
    category = db.query(Category).join(Subject).filter(
        Category.id == category_id,
        Subject.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category

@app.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Update a category"""
    category = db.query(Category).join(Subject).filter(
        Category.id == category_id,
        Subject.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    for field, value in category_update.dict(exclude_unset=True).items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category

@app.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a category"""
    category = db.query(Category).join(Subject).filter(
        Category.id == category_id,
        Subject.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update documents to remove category reference
    db.query(Document).filter(Document.category_id == category_id).update({
        Document.category_id: None
    })
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}

# Document Group Management
@app.get("/groups", response_model=List[DocumentGroupResponse])
async def list_document_groups(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all document groups (subjects with their categories and documents)"""
    subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
    
    groups = []
    for subject in subjects:
        categories = db.query(Category).filter(Category.subject_id == subject.id).all()
        documents = db.query(Document).filter(Document.subject_id == subject.id).all()
        
        total_size = sum(doc.file_size for doc in documents)
        
        group = DocumentGroupResponse(
            subject=subject,
            categories=categories,
            documents=documents,
            total_documents=len(documents),
            total_size=total_size
        )
        groups.append(group)
    
    return groups

@app.get("/groups/{subject_id}", response_model=DocumentGroupResponse)
async def get_document_group(
    subject_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific document group"""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    categories = db.query(Category).filter(Category.subject_id == subject_id).all()
    documents = db.query(Document).filter(Document.subject_id == subject_id).all()
    
    total_size = sum(doc.file_size for doc in documents)
    
    return DocumentGroupResponse(
        subject=subject,
        categories=categories,
        documents=documents,
        total_documents=len(documents),
        total_size=total_size
    )

# Updated Document Upload with Subject/Category Support
@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    subject_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Upload a document with optional subject and category assignment"""
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
    
    # Validate subject and category if provided
    if subject_id:
        subject = db.query(Subject).filter(
            Subject.id == subject_id,
            Subject.user_id == user_id
        ).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
    
    if category_id:
        category = db.query(Category).join(Subject).filter(
            Category.id == category_id,
            Subject.user_id == user_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        # Ensure category belongs to the specified subject
        if subject_id and category.subject_id != subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category does not belong to the specified subject"
            )
    
    # Create document record
    document = Document(
        user_id=user_id,
        filename=file.filename,
        content_type=file.content_type,
        file_size=0,  # Will be updated after upload
        file_path="",  # Will be updated after upload
        status=DocumentStatus.UPLOADED,
        subject_id=subject_id,
        category_id=category_id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    try:
        # Upload to MinIO
        file_content = await file.read()
        s3_key = f"documents/{user_id}/{document.id}/{file.filename}"
        await storage_service.upload_file(s3_key, file_content, file.content_type)
        
        # Update document with file size and path
        document.file_size = len(file_content)
        document.file_path = s3_key
        document.status = DocumentStatus.PROCESSING
        db.commit()
        
        # Trigger processing task asynchronously
        asyncio.create_task(document_processor.process_document(document.id, user_id, db))
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            message="Document uploaded successfully and processing started"
        )
        
    except Exception as e:
        document.status = DocumentStatus.FAILED
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
    if document.file_path:
        await storage_service.delete_file(document.file_path)
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 