import asyncio
import time
from typing import List
import httpx
from ..config import settings
from ..models import Document
from sqlalchemy.orm import Session
import sys
import os

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from shared import EventPublisher, EventType

class DocumentProcessor:
    """Asynchronous document processor with event-driven architecture"""
    
    def __init__(self):
        self.event_publisher = EventPublisher(settings.REDIS_URL)
        self.notification_url = settings.NOTIFICATION_SERVICE_URL
        self.indexing_url = settings.INDEXING_SERVICE_URL
    
    async def process_document(self, document_id: str, user_id: str, db: Session):
        """Process document asynchronously with event publishing"""
        start_time = time.time()
        
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Publish processing started event
            self.event_publisher.publish_document_processing(
                user_id=user_id,
                document_id=document_id,
                progress=0
            )
            
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
            
            # Publish processing completed event
            self.event_publisher.publish_document_processed(
                user_id=user_id,
                document_id=document_id,
                chunks_count=10,  # Simulated chunk count
                processing_time=processing_time
            )
            
            # Send notification to user
            self.event_publisher.publish_user_notification(
                user_id=user_id,
                notification_type="document_processed",
                title="Document Processing Complete",
                message=f"Your document '{document.filename}' has been processed successfully.",
                priority="normal"
            )
            
        except Exception as e:
            # Update document status
            document.status = "failed"
            db.commit()
            
            # Publish failure event
            self.event_publisher.publish_document_failed(
                user_id=user_id,
                document_id=document_id,
                error_message=str(e)
            )
            
            # Send notification to user
            self.event_publisher.publish_user_notification(
                user_id=user_id,
                notification_type="document_failed",
                title="Document Processing Failed",
                message=f"Failed to process document '{document.filename}': {str(e)}",
                priority="high"
            )
            
            raise
    
    async def _extract_text(self, document_id: str, user_id: str):
        """Extract text from document"""
        # Simulate text extraction
        await asyncio.sleep(2)
        
        # Publish progress update
        self.event_publisher.publish_document_processing(
            user_id=user_id,
            document_id=document_id,
            progress=30
        )
    
    async def _chunk_document(self, document_id: str, user_id: str):
        """Chunk document into smaller pieces"""
        # Simulate document chunking
        await asyncio.sleep(3)
        
        # Publish progress update
        self.event_publisher.publish_document_processing(
            user_id=user_id,
            document_id=document_id,
            progress=70
        )
    
    async def _trigger_indexing(self, document_id: str, user_id: str):
        """Trigger indexing service"""
        # Simulate triggering indexing
        await asyncio.sleep(1)
        
        # Publish progress update
        self.event_publisher.publish_document_processing(
            user_id=user_id,
            document_id=document_id,
            progress=90
        )
        
        # Trigger indexing service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.indexing_url}/index",
                    json={
                        "document_id": document_id,
                        "user_id": user_id
                    }
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