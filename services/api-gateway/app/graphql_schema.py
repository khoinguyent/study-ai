import strawberry
from strawberry.types import Info
from typing import List, Optional
from datetime import datetime
import httpx
import asyncio
from fastapi import Request
from .config import settings
import os

def safe_parse_datetime(date_string: str) -> datetime:
    """Safely parse datetime string with fallback"""
    if not date_string:
        return datetime.now()
    try:
        # Handle both Z and +00:00 timezone formats
        if date_string.endswith('Z'):
            date_string = date_string.replace('Z', '+00:00')
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError) as e:
        return datetime.now()

def safe_average(scores: List[float]) -> float:
    """Safely calculate average with fallback for empty list"""
    return sum(scores) / len(scores) if scores else 0.0

@strawberry.type
class Document:
    id: str
    name: str
    filename: str
    content_type: str = strawberry.field(name="contentType")
    file_size: int = strawberry.field(name="fileSize") 
    status: str
    s3_url: str = strawberry.field(name="s3Url")
    created_at: datetime = strawberry.field(name="createdAt")
    updated_at: Optional[datetime] = strawberry.field(name="updatedAt", default=None)

@strawberry.type
class Category:
    id: str
    name: str
    description: str
    total_documents: int = strawberry.field(name="totalDocuments")
    documents: List[Document]
    avg_score: float = strawberry.field(name="avgScore")
    created_at: datetime = strawberry.field(name="createdAt")
    updated_at: Optional[datetime] = strawberry.field(name="updatedAt", default=None)

@strawberry.type
class Subject:
    id: str
    name: str
    description: str
    icon: Optional[str] = None
    color_theme: Optional[str] = strawberry.field(name="colorTheme", default=None)
    total_documents: int = strawberry.field(name="totalDocuments")
    categories: List[Category]
    avg_score: float = strawberry.field(name="avgScore")
    created_at: datetime = strawberry.field(name="createdAt")
    updated_at: Optional[datetime] = strawberry.field(name="updatedAt", default=None)

@strawberry.type
class DashboardStats:
    total_subjects: int = strawberry.field(name="totalSubjects")
    total_categories: int = strawberry.field(name="totalCategories")
    total_documents: int = strawberry.field(name="totalDocuments")
    avg_score: float = strawberry.field(name="avgScore")

@strawberry.type
class DashboardData:
    stats: DashboardStats
    subjects: List[Subject]

class GraphQLService:
    def __init__(self):
        self.document_service_url = settings.DOCUMENT_SERVICE_URL or "http://document-service:8002"
        self.quiz_service_url = settings.QUIZ_SERVICE_URL or "http://quiz-service:8004"
    
    async def get_user_subjects(self, user_id: str, token: str = None) -> List[dict]:
        """Fetch subjects for a user"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.document_service_url}/subjects",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else []
                else:
                    return []
        except Exception as e:
            return []
    
    async def get_categories_by_subject(self, subject_id: str, user_id: str, token: str = None) -> List[dict]:
        """Fetch categories for a subject"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.document_service_url}/categories",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    # Filter categories by subject_id
                    filtered_categories = [cat for cat in data if cat.get('subject_id') == subject_id]
                    return filtered_categories
                else:
                    return []
        except Exception as e:
            return []
    
    async def get_documents_by_category(self, category_id: str, user_id: str, token: str = None) -> List[dict]:
        """Fetch documents for a category"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.document_service_url}/categories/{category_id}/documents?page_size=100",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    # The endpoint returns paginated response with 'documents' array
                    documents = data.get('documents', []) if isinstance(data, dict) else []
                    return documents if isinstance(documents, list) else []
                else:
                    return []
        except Exception as e:
            return []
    
    async def get_document_s3_url(self, document_id: str, user_id: str, token: str = None) -> str:
        """Get S3 URL for a document"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.document_service_url}/documents/{document_id}/download-url?user_id={user_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get('download_url', f"s3://study-ai-documents/{document_id}")
                else:
                    return f"s3://study-ai-documents/{document_id}"
        except Exception as e:
            return f"s3://study-ai-documents/{document_id}"
    
    async def build_dashboard_data(self, user_id: str, token: str = None) -> DashboardData:
        """Build complete dashboard data with all subjects, categories, and documents"""
        
        # Get all subjects
        subjects_data = await self.get_user_subjects(user_id, token)
        
        # Build subjects with categories and documents
        subjects = []
        total_documents = 0
        total_categories = 0
        all_scores = []
        
        for subject_data in subjects_data:
            # Get categories for this subject
            categories_data = await self.get_categories_by_subject(subject_data['id'], user_id, token)
            
            categories = []
            subject_total_documents = 0
            subject_scores = []
            
            for category_data in categories_data:
                # Get documents for this category
                documents_data = await self.get_documents_by_category(category_data['id'], user_id, token)
                
                # Process documents
                documents = []
                category_scores = []
                for doc_data in documents_data:
                    # Get S3 URL for document
                    s3_url = await self.get_document_s3_url(doc_data['id'], user_id, token)
                    
                    document = Document(
                        id=doc_data.get('id', ''),
                        name=doc_data.get('filename', doc_data.get('name', 'Unknown')),
                        filename=doc_data.get('filename', doc_data.get('name', 'Unknown')),
                        content_type=doc_data.get('content_type', 'application/pdf'),
                        file_size=doc_data.get('file_size', 0),
                        status=doc_data.get('status', 'pending'),
                        s3_url=s3_url,
                        created_at=safe_parse_datetime(doc_data.get('created_at', '')),
                        updated_at=safe_parse_datetime(doc_data.get('updated_at', '')) if doc_data.get('updated_at') else None
                    )
                    documents.append(document)
                    
                    # Add to scores (using file_size as placeholder for now)
                    if doc_data.get('file_size'):
                        category_scores.append(float(doc_data.get('file_size')))
                
                # Build category
                category = Category(
                    id=category_data.get('id', ''),
                    name=category_data.get('name', 'Unknown'),
                    description=category_data.get('description', ''),
                    total_documents=len(documents),
                    documents=documents,
                    avg_score=safe_average(category_scores),
                    created_at=safe_parse_datetime(category_data.get('created_at', '')),
                    updated_at=safe_parse_datetime(category_data.get('updated_at', '')) if category_data.get('updated_at') else None
                )
                categories.append(category)
                
                # Update counters
                subject_total_documents += len(documents)
                subject_scores.extend(category_scores)
            
            # Build subject
            subject = Subject(
                id=subject_data['id'],
                name=subject_data.get('name', 'Unknown'),
                description=subject_data.get('description', ''),
                icon=subject_data.get('icon'),
                color_theme=subject_data.get('color_theme'),
                total_documents=subject_total_documents,
                categories=categories,
                avg_score=safe_average(subject_scores),
                created_at=safe_parse_datetime(subject_data.get('created_at', '')),
                updated_at=safe_parse_datetime(subject_data.get('updated_at', '')) if subject_data.get('updated_at') else None
            )
            subjects.append(subject)
            
            # Update global counters
            total_documents += subject_total_documents
            total_categories += len(categories)
            all_scores.extend(subject_scores)
        
        # Build stats
        stats = DashboardStats(
            total_subjects=len(subjects),
            total_categories=total_categories,
            total_documents=total_documents,
            avg_score=safe_average(all_scores)
        )
        
        return DashboardData(
            stats=stats,
            subjects=subjects
        )

# Initialize the service
graphql_service = GraphQLService()

@strawberry.type
class Query:
    @strawberry.field
    async def dashboard(self, userId: str, info: Info) -> DashboardData:
        """Get complete dashboard data for a user"""
        # Extract auth token from request headers
        request: Request = info.context["request"]
        auth_header = request.headers.get("authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        result = await graphql_service.build_dashboard_data(userId, token)
        return result
    
    @strawberry.field
    async def subjects(self, userId: str, info: Info) -> List[Subject]:
        """Get subjects with categories and documents for a user"""
        # Extract auth token from request headers
        request: Request = info.context["request"]
        auth_header = request.headers.get("authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        dashboard_data = await graphql_service.build_dashboard_data(userId, token)
        return dashboard_data.subjects
    
    @strawberry.field
    async def stats(self, userId: str, info: Info) -> DashboardStats:
        """Get dashboard statistics for a user"""
        # Extract auth token from request headers
        request: Request = info.context["request"]
        auth_header = request.headers.get("authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        dashboard_data = await graphql_service.build_dashboard_data(userId, token)
        return dashboard_data.stats

schema = strawberry.Schema(query=Query)
