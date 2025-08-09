"""
Document Service Tasks for Study AI Platform
Handles document processing tasks using Celery and event-driven architecture
"""

import asyncio
import time
from celery import current_task
from app.models import Document
from app.database import get_db
from app.services.storage_service import StorageService
from app.services.document_processor import DocumentProcessor
from shared.celery_app import celery_app, EventDrivenTask, document_task
from shared.event_publisher import EventPublisher
from shared.events import EventType, create_event
import logging

logger = logging.getLogger(__name__)

# Initialize services
storage_service = StorageService()
document_processor = DocumentProcessor()
event_publisher = EventPublisher()

@document_task
def upload_document_to_s3(document_id: str, user_id: str, file_content: bytes, filename: str, content_type: str):
    """
    Upload document to S3 storage
    """
    task_id = current_task.request.id
    
    try:
        # Publish upload started event
        event_publisher.publish_document_uploaded(
            user_id=user_id,
            document_id=document_id,
            filename=filename,
            file_size=len(file_content),
            content_type=content_type
        )
        
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 25, 'message': f'Uploading {filename} to S3...'}
        )
        
        # Upload to S3
        s3_key = f"documents/{user_id}/{document_id}/{filename}"
        asyncio.run(storage_service.upload_file(s3_key, file_content, content_type))
        
        # Update document in database
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.file_path = s3_key
                document.file_size = len(file_content)
                document.status = "uploaded"
                db.commit()
                
                logger.info(f"Document {document_id} uploaded to S3 successfully")
                
                # Publish upload completed event
                event_publisher.publish_task_status_update(
                    user_id=user_id,
                    task_id=task_id,
                    task_type="document_upload",
                    status="completed",
                    progress=100,
                    message=f"Document {filename} uploaded successfully"
                )
                
                # Trigger document processing
                process_document.delay(document_id, user_id)
                
                return {
                    'status': 'success',
                    'document_id': document_id,
                    's3_key': s3_key,
                    'file_size': len(file_content)
                }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to upload document {document_id}: {str(e)}")
        
        # Update document status to failed
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                db.commit()
        finally:
            db.close()
        
        # Publish failure event
        event_publisher.publish_document_failed(
            user_id=user_id,
            document_id=document_id,
            error_message=str(e)
        )
        
        # Publish task failure event
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="document_upload",
            status="failed",
            progress=0,
            message=f"Upload failed: {str(e)}"
        )
        
        raise

@document_task
def process_document(document_id: str, user_id: str):
    """
    Process document content (extract text, chunk, etc.)
    """
    task_id = current_task.request.id
    
    try:
        # Publish processing started event
        event_publisher.publish_document_processing(
            user_id=user_id,
            document_id=document_id,
            progress=0
        )
        
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Starting document processing...'}
        )
        
        # Get document from database
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Update document status to processing
            document.status = "processing"
            db.commit()
            
            # Process document
            start_time = time.time()
            
            # Simulate processing steps
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 25, 'message': 'Extracting text...'}
            )
            asyncio.run(document_processor._extract_text(document_id, user_id))
            
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 50, 'message': 'Chunking document...'}
            )
            asyncio.run(document_processor._chunk_document(document_id, user_id))
            
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 75, 'message': 'Preparing for indexing...'}
            )
            asyncio.run(document_processor._trigger_indexing(document_id, user_id))
            
            processing_time = time.time() - start_time
            
            # Update document status to completed
            document.status = "completed"
            db.commit()
            
            logger.info(f"Document {document_id} processed successfully in {processing_time:.2f}s")
            
            # Publish processing completed event
            event_publisher.publish_document_processed(
                user_id=user_id,
                document_id=document_id,
                chunks_count=10,  # Simulated chunks count
                processing_time=processing_time
            )
            
            # Publish task completed event
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_processing",
                status="completed",
                progress=100,
                message=f"Document {document.filename} processed successfully"
            )
            
            # Trigger indexing
            from services.indexing_service.app.tasks import index_document
            index_document.delay(document_id, user_id)
            
            return {
                'status': 'success',
                'document_id': document_id,
                'processing_time': processing_time,
                'chunks_count': 10
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        
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
        event_publisher.publish_document_failed(
            user_id=user_id,
            document_id=document_id,
            error_message=str(e)
        )
        
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="document_processing",
            status="failed",
            progress=0,
            message=f"Processing failed: {str(e)}"
        )
        
        raise

@document_task
def cleanup_failed_document(document_id: str, user_id: str):
    """
    Clean up failed document (remove from S3, update database)
    """
    try:
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document and document.file_path:
                # Remove from S3
                asyncio.run(storage_service.delete_file(document.file_path))
                
                # Update document status
                document.status = "failed"
                db.commit()
                
                logger.info(f"Cleaned up failed document {document_id}")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to cleanup document {document_id}: {str(e)}")
        raise
