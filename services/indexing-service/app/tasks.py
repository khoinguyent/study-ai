"""
Indexing Service Tasks for Study AI Platform
Handles document indexing tasks using Celery and event-driven architecture
"""

import asyncio
import time
from celery import current_task
from app.models import Document
from app.database import get_db
from app.services.vector_service import VectorService
from shared.celery_app import celery_app, EventDrivenTask, indexing_task
from shared.event_publisher import EventPublisher
from shared.events import EventType, create_event
import logging

logger = logging.getLogger(__name__)

# Initialize services
vector_service = VectorService()
event_publisher = EventPublisher()

@indexing_task
def index_document(document_id: str, user_id: str):
    """
    Index document content for vector search
    """
    task_id = current_task.request.id
    
    try:
        # Publish indexing started event
        event_publisher.publish_indexing_started(
            user_id=user_id,
            document_id=document_id,
            chunks_count=10  # Simulated chunks count
        )
        
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Starting document indexing...'}
        )
        
        # Get document from database
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Simulate indexing process
            start_time = time.time()
            total_chunks = 10
            processed_chunks = 0
            
            # Process chunks in batches
            for batch in range(0, total_chunks, 2):
                # Simulate chunk processing
                time.sleep(1)
                processed_chunks += 2
                progress = min((processed_chunks / total_chunks) * 100, 100)
                
                # Update task status
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(progress),
                        'message': f'Indexing chunks {processed_chunks}/{total_chunks}...'
                    }
                )
                
                # Publish indexing progress event
                event_publisher.publish_indexing_progress(
                    user_id=user_id,
                    document_id=document_id,
                    progress=int(progress),
                    processed_chunks=processed_chunks,
                    total_chunks=total_chunks
                )
            
            indexing_time = time.time() - start_time
            
            # Update document status to indexed
            document.status = "indexed"
            db.commit()
            
            logger.info(f"Document {document_id} indexed successfully in {indexing_time:.2f}s")
            
            # Publish indexing completed event
            event_publisher.publish_indexing_completed(
                user_id=user_id,
                document_id=document_id,
                vectors_count=total_chunks,
                indexing_time=indexing_time
            )
            
            # Publish task completed event
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_indexing",
                status="completed",
                progress=100,
                message=f"Document {document.filename} indexed successfully"
            )
            
            # Publish document ready event
            event_publisher.publish_user_notification(
                user_id=user_id,
                notification_type="document_ready",
                title="Document Ready",
                message=f"Document {document.filename} is now ready for quiz generation",
                priority="normal"
            )
            
            return {
                'status': 'success',
                'document_id': document_id,
                'indexing_time': indexing_time,
                'vectors_count': total_chunks
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to index document {document_id}: {str(e)}")
        
        # Update document status to failed
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                db.commit()
        finally:
            db.close()
        
        # Publish failure events
        event_publisher.publish_indexing_failed(
            user_id=user_id,
            document_id=document_id,
            error_message=str(e)
        )
        
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="document_indexing",
            status="failed",
            progress=0,
            message=f"Indexing failed: {str(e)}"
        )
        
        raise

@indexing_task
def reindex_document(document_id: str, user_id: str):
    """
    Reindex an existing document
    """
    return index_document.delay(document_id, user_id)

@indexing_task
def delete_document_index(document_id: str, user_id: str):
    """
    Delete document from vector index
    """
    task_id = current_task.request.id
    
    try:
        # Delete from vector service
        asyncio.run(vector_service.delete_document(document_id))
        
        logger.info(f"Document {document_id} deleted from index successfully")
        
        # Publish task completed event
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="document_index_deletion",
            status="completed",
            progress=100,
            message=f"Document {document_id} deleted from index"
        )
        
        return {
            'status': 'success',
            'document_id': document_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete document {document_id} from index: {str(e)}")
        
        # Publish failure event
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="document_index_deletion",
            status="failed",
            progress=0,
            message=f"Index deletion failed: {str(e)}"
        )
        
        raise
