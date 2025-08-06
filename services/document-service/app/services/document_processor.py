import asyncio
import uuid
from typing import Dict, Any
import httpx
from ..config import settings

class DocumentProcessor:
    def __init__(self):
        self.notification_url = settings.NOTIFICATION_SERVICE_URL
        self.indexing_url = settings.INDEXING_SERVICE_URL
    
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
    
    async def process_document(self, document_id: str, user_id: str, filename: str, content_type: str):
        """Process a document asynchronously"""
        task_id = f"doc_process_{document_id}"
        
        try:
            # Create initial task status
            await self.create_task_status(
                task_id=task_id,
                user_id=user_id,
                task_type="document_processing",
                status="processing",
                progress=10,
                message="Starting document processing..."
            )
            
            # Simulate document processing steps
            await asyncio.sleep(1)  # Simulate processing time
            
            await self.update_task_status(
                task_id=task_id,
                status="processing",
                progress=30,
                message="Extracting text from document..."
            )
            
            await asyncio.sleep(1)  # Simulate processing time
            
            await self.update_task_status(
                task_id=task_id,
                status="processing",
                progress=60,
                message="Preparing document for indexing..."
            )
            
            # Trigger indexing service
            await self.trigger_indexing(document_id, user_id)
            
            await self.update_task_status(
                task_id=task_id,
                status="completed",
                progress=100,
                message="Document processed successfully!"
            )
            
        except Exception as e:
            await self.update_task_status(
                task_id=task_id,
                status="failed",
                progress=0,
                message=f"Document processing failed: {str(e)}"
            )
            raise
    
    async def trigger_indexing(self, document_id: str, user_id: str):
        """Trigger the indexing service to process the document"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.indexing_url}/index",
                    params={"document_id": document_id}
                )
                if response.status_code != 200:
                    raise Exception(f"Indexing service failed: {response.text}")
                return response.json()
            except Exception as e:
                print(f"Failed to trigger indexing: {e}")
                raise 