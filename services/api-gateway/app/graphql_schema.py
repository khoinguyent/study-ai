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
        print(f"WARNING: Failed to parse datetime '{date_string}': {e}")
        return datetime.now()

def safe_average(scores: List[float]) -> float:
    """Safely calculate average with fallback for empty list"""
    return sum(scores) / len(scores) if scores else 0.0

@strawberry.type
class Document:
    id: str
    name: str
    filename: str
    content_type: str = strawberry.field(name="content_type")
    file_size: int = strawberry.field(name="file_size") 
    status: str
    s3_url: str = strawberry.field(name="s3_url")
    created_at: datetime = strawberry.field(name="created_at")
    updated_at: Optional[datetime] = strawberry.field(name="updated_at", default=None)

@strawberry.type
class Category:
    id: str
    name: str
    description: str
    total_documents: int = strawberry.field(name="total_documents")
    documents: List[Document]
    avg_score: float = strawberry.field(name="avg_score")
    created_at: datetime = strawberry.field(name="created_at")
    updated_at: Optional[datetime] = strawberry.field(name="updated_at", default=None)

@strawberry.type
class Subject:
    id: str
    name: str
    description: str
    icon: Optional[str] = None
    color_theme: Optional[str] = strawberry.field(name="color_theme", default=None)
    total_documents: int = strawberry.field(name="total_documents")
    categories: List[Category]
    avg_score: float = strawberry.field(name="avg_score")
    created_at: datetime = strawberry.field(name="created_at")
    updated_at: Optional[datetime] = strawberry.field(name="updated_at", default=None)

@strawberry.type
class DashboardStats:
    total_subjects: int = strawberry.field(name="total_subjects")
    total_categories: int = strawberry.field(name="total_categories")
    total_documents: int = strawberry.field(name="total_documents")
    avg_score: float = strawberry.field(name="avg_score")

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
        headers = {"user_id": user_id}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        print(f"DEBUG: Fetching subjects for user {user_id}")
        print(f"DEBUG: Document service URL: {self.document_service_url}")
        print(f"DEBUG: Headers: {headers}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # Add timeout
                response = await client.get(
                    f"{self.document_service_url}/subjects?user_id={user_id}",
                    headers=headers
                )
                print(f"DEBUG: Response status: {response.status_code}")
                print(f"DEBUG: Response text: {response.text}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"DEBUG: Parsed subjects data: {data}")
                    return data if isinstance(data, list) else []  # Validate response type
                else:
                    print(f"ERROR: Failed to fetch subjects, status: {response.status_code}")
                    return []
        except Exception as e:
            print(f"ERROR: Exception in get_user_subjects: {str(e)}")
            return []
    
    async def get_categories_by_subject(self, subject_id: str, user_id: str, token: str = None) -> List[dict]:
        """Fetch categories for a subject"""
        headers = {"user_id": user_id}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.document_service_url}/categories?subject_id={subject_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else []
                else:
                    print(f"ERROR: Failed to fetch categories for subject {subject_id}, status: {response.status_code}")
                    return []
        except Exception as e:
            print(f"ERROR: Exception in get_categories_by_subject: {str(e)}")
            return []
    
    async def get_documents_by_category(self, category_id: str, user_id: str, token: str = None) -> List[dict]:
        """Fetch documents for a category"""
        headers = {"user_id": user_id}
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
                    print(f"ERROR: Failed to fetch documents for category {category_id}, status: {response.status_code}")
                    return []
        except Exception as e:
            print(f"ERROR: Exception in get_documents_by_category: {str(e)}")
            return []
    
    async def get_document_s3_url(self, document_id: str, user_id: str, token: str = None) -> str:
        """Get S3 URL for a document"""
        headers = {"user_id": user_id}
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
                    print(f"WARNING: Failed to get S3 URL for document {document_id}, using fallback")
                    return f"s3://study-ai-documents/{document_id}"
        except Exception as e:
            print(f"WARNING: Exception getting S3 URL for document {document_id}: {str(e)}")
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
                
                # Build documents list with S3 URLs
                documents = []
                category_scores = []
                
                for doc_data in documents_data:
                    s3_url = await self.get_document_s3_url(doc_data['id'], user_id, token)
                    
                    document = Document(
                        id=doc_data['id'],
                        name=doc_data.get('filename', 'Unknown'),
                        filename=doc_data.get('filename', 'Unknown'),
                        content_type=doc_data.get('content_type', ''),
                        file_size=doc_data.get('file_size', 0),
                        status=doc_data.get('status', 'unknown'),
                        s3_url=s3_url,
                        created_at=safe_parse_datetime(doc_data.get('created_at', '')),
                        updated_at=safe_parse_datetime(doc_data.get('updated_at', '')) if doc_data.get('updated_at') else None
                    )
                    documents.append(document)
                    
                    # Collect scores (placeholder for now)
                    if doc_data.get('avg_score'):
                        category_scores.append(doc_data['avg_score'])
                
                # Build category
                category = Category(
                    id=category_data['id'],
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
    async def dashboard(self, user_id: str, info: Info) -> DashboardData:
        """Get complete dashboard data for a user"""
        print(f"DEBUG: Dashboard resolver called with user_id: {user_id}")
        
        # Extract auth token from request headers
        request: Request = info.context["request"]
        auth_header = request.headers.get("authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        print(f"DEBUG: Extracted token: {token[:20] if token else 'None'}...")
        print(f"DEBUG: Calling build_dashboard_data")
        
        result = await graphql_service.build_dashboard_data(user_id, token)
        print(f"DEBUG: Dashboard result subjects count: {len(result.subjects) if result.subjects else 0}")
        return result
    
    @strawberry.field
    async def test_subjects(self, user_id: str, info: Info) -> List[str]:
        """Test endpoint to fetch subjects directly"""
        print(f"DEBUG: Test subjects called with user_id: {user_id}")
        
        # Extract auth token from request headers  
        request: Request = info.context["request"]
        auth_header = request.headers.get("authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            
        print(f"DEBUG: Token for test: {token[:20] if token else 'None'}...")
        
        try:
            subjects_data = await graphql_service.get_user_subjects(user_id, token)
            print(f"DEBUG: Raw subjects data: {subjects_data}")
            return [subject.get('name', 'Unknown') for subject in subjects_data] if subjects_data else []
        except Exception as e:
            print(f"DEBUG: Error in test_subjects: {str(e)}")
            return []
    
    @strawberry.field
    async def subjects(self, user_id: str) -> List[Subject]:
        """Get subjects with categories and documents for a user"""
        dashboard_data = await graphql_service.build_dashboard_data(user_id)
        return dashboard_data.subjects
    
    @strawberry.field
    async def stats(self, user_id: str) -> DashboardStats:
        """Get dashboard statistics for a user"""
        dashboard_data = await graphql_service.build_dashboard_data(user_id)
        return dashboard_data.stats

schema = strawberry.Schema(query=Query)
