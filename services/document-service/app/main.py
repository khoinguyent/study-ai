from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Header, Query, Request, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import httpx
from typing import List, Optional
import json
import asyncio
from pydantic import BaseModel

from .database import get_db, create_tables
from .models import Subject, Category, Document
from .schemas import (
    SubjectCreate, SubjectUpdate, SubjectResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    DocumentResponse, DocumentUploadResponse, DocumentGroupResponse, DocumentStatus, PaginatedDocumentResponse
)
from .config import settings
from .services.document_processor import DocumentProcessor
from .services.storage_service import StorageService

# Notification service helper
class NotificationService:
    def __init__(self):
        self.notification_service_url = settings.NOTIFICATION_SERVICE_URL or "http://notification-service:8005"
    
    async def create_task_status(self, task_id: str, user_id: str, task_type: str, status: str = "pending", message: str = None):
        """Create a new task status in the notification service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.notification_service_url}/task-status",
                    json={
                        "task_id": task_id,
                        "user_id": user_id,
                        "task_type": task_type,
                        "status": status,
                        "progress": 0,
                        "message": message,
                        "metadata": {}
                    }
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Failed to create task status: {e}")
                return False
    
    async def update_task_status(self, task_id: str, status: str = None, progress: int = None, message: str = None, metadata: dict = None):
        """Update task status in the notification service"""
        async with httpx.AsyncClient() as client:
            try:
                update_data = {}
                if status:
                    update_data["status"] = status
                if progress is not None:
                    update_data["progress"] = progress
                if message:
                    update_data["message"] = message
                if metadata:
                    update_data["metadata"] = metadata
                
                response = await client.put(
                    f"{self.notification_service_url}/task-status/{task_id}",
                    json=update_data
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Failed to update task status: {e}")
                return False
    
    async def send_notification(self, user_id: str, title: str, message: str, notification_type: str = "task_status", metadata: dict = None):
        """Send a notification to the user"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.notification_service_url}/notifications",
                    json={
                        "user_id": user_id,
                        "title": title,
                        "message": message,
                        "notification_type": notification_type,
                        "metadata": metadata or {}
                    }
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Failed to send notification: {e}")
                return False

app = FastAPI(
    title="Document Service",
    description="Document upload and processing service with subject/category management",
    version="1.0.0"
)

# CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Simple Pydantic model for subject creation
class SubjectCreateModel(BaseModel):
    name: str
    description: Optional[str] = None

# Initialize services
document_processor = DocumentProcessor()
storage_service = StorageService()
notification_service = NotificationService()

async def process_document_with_notifications(document_id: str, user_id: str, task_id: str, db: Session):
    """Process document with notification updates"""
    try:
        # Update status to processing
        await notification_service.update_task_status(
            task_id=task_id,
            status="processing",
            progress=80,
            message="Processing document content..."
        )
        
        # Call the original document processor
        result = await document_processor.process_document(document_id, user_id, db)
        
        # Update status to completed
        await notification_service.update_task_status(
            task_id=task_id,
            status="completed",
            progress=100,
            message="Document processing completed successfully"
        )
        
        # Send success notification
        await notification_service.send_notification(
            user_id=user_id,
            title="Document Processed",
            message=f"Document {document_id} has been processed and is ready for indexing",
            notification_type="processing_status",
            metadata={"document_id": document_id, "processing_result": result}
        )
        
        return result
        
    except Exception as e:
        # Update status to failed
        await notification_service.update_task_status(
            task_id=task_id,
            status="failed",
            progress=100,
            message=f"Document processing failed: {str(e)}"
        )
        
        # Send failure notification
        await notification_service.send_notification(
            user_id=user_id,
            title="Processing Failed",
            message=f"Failed to process document {document_id}: {str(e)}",
            notification_type="processing_status",
            metadata={"document_id": document_id, "error": str(e)}
        )
        
        # Update document status in database
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.FAILED
            db.commit()
        
        return None

async def verify_auth_token(authorization: str = Header(alias="Authorization")):
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

@app.post("/test-pydantic")
async def test_pydantic(subject: SubjectCreateModel):
    """Test Pydantic model without any dependencies"""
    return {
        "message": "Pydantic test successful",
        "data": {
            "name": subject.name,
            "description": subject.description
        }
    }

@app.post("/simple-subject")
async def create_simple_subject(subject: SubjectCreateModel, user_id: str = Depends(verify_auth_token), db: Session = Depends(get_db)):
    """Create a subject with proper Pydantic validation"""
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
    
    return {
        "id": db_subject.id,
        "name": db_subject.name,
        "description": db_subject.description,
        "user_id": db_subject.user_id,
        "created_at": db_subject.created_at.isoformat() if db_subject.created_at else None
    }

# Subject Management Endpoints
@app.post("/subjects")
async def create_subject(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Create a new subject"""
    # Extract data from request
    name = request.get("name")
    description = request.get("description")
    icon = request.get("icon", "microscope")
    color_theme = request.get("color_theme", "green")
    
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required"
        )
    
    # Check if subject name already exists for this user
    existing_subject = db.query(Subject).filter(
        Subject.name == name,
        Subject.user_id == user_id
    ).first()
    
    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject with this name already exists"
        )
    
    db_subject = Subject(
        name=name,
        description=description,
        icon=icon,
        color_theme=color_theme,
        user_id=user_id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    
    return {
        "id": db_subject.id,
        "name": db_subject.name,
        "description": db_subject.description,
        "icon": db_subject.icon,
        "color_theme": db_subject.color_theme,
        "user_id": db_subject.user_id,
        "created_at": db_subject.created_at.isoformat() if db_subject.created_at else None
    }

@app.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all subjects for a user"""
    from sqlalchemy import func
    
    # Add document count subquery
    doc_count_subquery = db.query(
        Document.subject_id,
        func.count(Document.id).label('doc_count'),
        func.avg(Document.file_size).label('avg_score')  # Using file_size as placeholder for avg_score
    ).group_by(Document.subject_id).subquery()
    
    subjects = db.query(Subject).filter(Subject.user_id == user_id).outerjoin(
        doc_count_subquery, Subject.id == doc_count_subquery.c.subject_id
    ).all()
    
    # Convert to response models with document counts
    result = []
    for subject in subjects:
        doc_count = getattr(subject, 'doc_count', 0) or 0
        avg_score = getattr(subject, 'avg_score', 0.0) or 0.0
        
        subject_response = SubjectResponse(
            id=subject.id,
            name=subject.name,
            description=subject.description,
            icon=subject.icon,
            color_theme=subject.color_theme,
            user_id=subject.user_id,
            document_count=doc_count,
            avg_score=float(avg_score),
            created_at=subject.created_at,
            updated_at=subject.updated_at
        )
        result.append(subject_response)
    
    return result

@app.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: str,
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
    subject_id: str,
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
    subject_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a subject"""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
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
    subject_id: Optional[str] = Query(None),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all categories for a user, optionally filtered by subject"""
    from sqlalchemy import func
    
    query = db.query(Category).join(Subject).filter(Subject.user_id == user_id)
    if subject_id:
        query = query.filter(Category.subject_id == subject_id)
    
    # Add document count subquery
    doc_count_subquery = db.query(
        Document.category_id,
        func.count(Document.id).label('doc_count'),
        func.avg(Document.file_size).label('avg_score')  # Using file_size as placeholder for avg_score
    ).group_by(Document.category_id).subquery()
    
    categories = query.outerjoin(doc_count_subquery, Category.id == doc_count_subquery.c.category_id).all()
    
    # Convert to response models with document counts
    result = []
    for category in categories:
        doc_count = getattr(category, 'doc_count', 0) or 0
        avg_score = getattr(category, 'avg_score', 0.0) or 0.0
        
        category_response = CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            subject_id=category.subject_id,
            user_id=category.user_id,
            document_count=doc_count,
            avg_score=float(avg_score),
            created_at=category.created_at,
            updated_at=category.updated_at
        )
        result.append(category_response)
    
    return result

@app.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
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
    category_id: str,
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
    category_id: str,
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
    subject_id: str,
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
    subject_id: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
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
        asyncio.create_task(document_processor.process_document(str(document.id), user_id, db))
        
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

@app.post("/upload-multiple", response_model=List[DocumentUploadResponse])
async def upload_multiple_documents(
    files: List[UploadFile] = File(..., max_length=100 * 1024 * 1024),  # 100MB max per file
    subject_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Upload multiple documents with optional subject and category assignment"""
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )
    
    # Validate file types
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain"
    ]
    
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.filename}"
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
    
    uploaded_documents = []
    
    for file in files:
        # Generate task ID for tracking
        task_id = f"upload_{user_id}_{uuid.uuid4()}"
        
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
        
        # Create task status notification
        await notification_service.create_task_status(
            task_id=task_id,
            user_id=user_id,
            task_type="document_upload",
            status="uploading",
            message=f"Uploading {file.filename}..."
        )
        
        try:
            # Update progress: Starting upload
            await notification_service.update_task_status(
                task_id=task_id,
                status="uploading",
                progress=25,
                message=f"Reading file {file.filename}..."
            )
            
            # Upload to MinIO
            file_content = await file.read()
            
            # Update progress: File read, starting storage
            await notification_service.update_task_status(
                task_id=task_id,
                progress=50,
                message=f"Storing {file.filename}..."
            )
            
            s3_key = f"documents/{user_id}/{document.id}/{file.filename}"
            await storage_service.upload_file(s3_key, file_content, file.content_type)
            
            # Update document with file size and path
            document.file_size = len(file_content)
            document.file_path = s3_key
            document.status = DocumentStatus.PROCESSING
            db.commit()
            
            # Update progress: Upload complete, starting processing
            await notification_service.update_task_status(
                task_id=task_id,
                status="processing",
                progress=75,
                message=f"Processing {file.filename}...",
                metadata={"document_id": str(document.id), "file_size": document.file_size}
            )
            
            # Trigger processing task asynchronously with task tracking
            asyncio.create_task(
                document_processor.process_document(str(document.id), user_id, db)
            )
            
            uploaded_documents.append(DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                status=document.status,
                message="Document uploaded successfully and processing started"
            ))
            
        except Exception as e:
            document.status = DocumentStatus.FAILED
            db.commit()
            
            # Update task status to failed
            await notification_service.update_task_status(
                task_id=task_id,
                status="failed",
                progress=100,
                message=f"Upload failed: {str(e)}"
            )
            
            # Send failure notification
            await notification_service.send_notification(
                user_id=user_id,
                title="Upload Failed",
                message=f"Failed to upload {file.filename}: {str(e)}",
                notification_type="upload_status",
                metadata={"document_id": str(document.id), "error": str(e)}
            )
            
            # Continue with other files but mark this one as failed
            uploaded_documents.append(DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                status=DocumentStatus.FAILED,
                message=f"Upload failed: {str(e)}"
            ))
    
    return uploaded_documents

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
            file_size=doc.file_size,
            file_path=doc.file_path,
            status=doc.status,
            user_id=doc.user_id,
            subject_id=doc.subject_id,
            category_id=doc.category_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at
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
        file_size=document.file_size,
        file_path=document.file_path,
        status=document.status,
        user_id=document.user_id,
        subject_id=document.subject_id,
        category_id=document.category_id,
        created_at=document.created_at,
        updated_at=document.updated_at
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

@app.get("/categories/{category_id}/documents", response_model=PaginatedDocumentResponse)
async def list_category_documents(
    category_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List documents in a specific category with pagination"""
    # Verify category exists and belongs to user
    category = db.query(Category).join(Subject).filter(
        Category.id == category_id,
        Subject.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total_count = db.query(Document).filter(
        Document.category_id == category_id,
        Document.user_id == user_id
    ).count()
    
    # Get paginated documents
    documents = db.query(Document).filter(
        Document.category_id == category_id,
        Document.user_id == user_id
    ).order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to response models
    document_responses = [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            file_path=doc.file_path,
            status=doc.status,
            user_id=doc.user_id,
            subject_id=doc.subject_id,
            category_id=doc.category_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]
    
    return PaginatedDocumentResponse(
        documents=document_responses,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total_count
    )

@app.get("/subjects/{subject_id}/documents", response_model=List[DocumentResponse])
async def list_subject_documents(
    subject_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all documents in a specific subject"""
    # Verify subject exists and belongs to user
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get all documents in this subject
    documents = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.user_id == user_id
    ).all()
    
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            file_path=doc.file_path,
            status=doc.status,
            user_id=doc.user_id,
            subject_id=doc.subject_id,
            category_id=doc.category_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 