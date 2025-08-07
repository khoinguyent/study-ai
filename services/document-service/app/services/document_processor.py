import asyncio
import time
from typing import List
import httpx
from ..config import settings
from ..models import Document
from sqlalchemy.orm import Session

class DocumentProcessor:
    """Asynchronous document processor"""
    
    def __init__(self):
        self.notification_url = settings.NOTIFICATION_SERVICE_URL
        self.indexing_url = settings.INDEXING_SERVICE_URL
    
    async def process_document(self, document_id: str, user_id: str, db: Session):
        """Process document asynchronously"""
        start_time = time.time()
        
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Update document status
            document.status = "processing"
            db.commit()
            
            # Simulate document processing steps
            await self._extract_text(document_id, user_id)
            await self._chunk_document(document_id, user_id)
            await self._trigger_indexing(document_id, user_id)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update document status
            document.status = "completed"
            db.commit()
            
        except Exception as e:
            # Update document status
            document.status = "failed"
            db.commit()
            raise
    
    async def _extract_text(self, document_id: str, user_id: str):
        """Extract text from document"""
        # Simulate text extraction
        await asyncio.sleep(2)
    
    async def _chunk_document(self, document_id: str, user_id: str):
        """Chunk document into smaller pieces"""
        # Simulate document chunking
        await asyncio.sleep(3)
    
    async def _trigger_indexing(self, document_id: str, user_id: str):
        """Trigger indexing service"""
        # Simulate triggering indexing
        await asyncio.sleep(1)
        
        # Trigger indexing service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.indexing_url}/index?document_id={document_id}"
                )
                if response.status_code != 200:
                    raise Exception(f"Indexing service error: {response.text}")
            except Exception as e:
                raise Exception(f"Failed to trigger indexing: {str(e)}")
    
    async def create_task_status(self, task_id: str, user_id: str, task_type: str, status: str = "pending", progress: int = 0, message: str = None):
        """Create a task status in the notification service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.notification_url}/task-status",
                    json={
                        "task_id": task_id,
                        "user_id": user_id,
                        "task_type": task_type,
                        "status": status,
                        "progress": progress,
                        "message": message
                    }
                )
                return response.json()
            except Exception as e:
                print(f"Failed to create task status: {e}")
    
    async def update_task_status(self, task_id: str, status: str, progress: int = None, message: str = None):
        """Update task status in the notification service"""
        async with httpx.AsyncClient() as client:
            try:
                update_data = {"status": status}
                if progress is not None:
                    update_data["progress"] = progress
                if message is not None:
                    update_data["message"] = message
                
                response = await client.put(
                    f"{self.notification_url}/task-status/{task_id}",
                    json=update_data
                )
                return response.json()
            except Exception as e:
                print(f"Failed to update task status: {e}") 