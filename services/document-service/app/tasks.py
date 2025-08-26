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
from app.config import settings
import sys
import os

# Add the shared directory to the Python path
shared_path = os.path.join(os.path.dirname(__file__), '..', 'shared')
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

from .celery_app import celery_app
from shared.celery_app import EventDrivenTask
from shared.event_publisher import EventPublisher
from shared.events import EventType, create_event
import logging

logger = logging.getLogger(__name__)

# Initialize services
storage_service = StorageService()
document_processor = DocumentProcessor()
event_publisher = EventPublisher()

@celery_app.task(bind=True, queue='document_queue')
def upload_document_to_s3(self, document_id: str, user_id: str, file_content: bytes, filename: str, content_type: str):
    """
    Upload document to S3 storage
    """
    task_id = self.request.id
    
    try:
        # Publish upload started event (with error handling)
        try:
            event_publisher.publish_document_uploaded(
                user_id=user_id,
                document_id=document_id,
                filename=filename,
                file_size=len(file_content),
                content_type=content_type
            )
        except Exception as event_error:
            logger.error(f"Failed to publish upload started event: {event_error}")
        
        # Update task status
        self.update_state(
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
                
                # Publish upload completed event (with error handling)
                try:
                    event_publisher.publish_task_status_update(
                        user_id=user_id,
                        task_id=task_id,
                        task_type="document_upload",
                        status="completed",
                        progress=100,
                        message=f"Document {filename} uploaded successfully"
                    )
                except Exception as event_error:
                    logger.error(f"Failed to publish upload completed event: {event_error}")
                
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
        
        # Publish failure event (with error handling)
        try:
            event_publisher.publish_document_failed(
                user_id=user_id,
                document_id=document_id,
                error_message=str(e)
            )
        except Exception as event_error:
            logger.error(f"Failed to publish document failed event: {event_error}")
        
        # Publish task failure event (with error handling)
        try:
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_upload",
                status="failed",
                progress=0,
                message=f"Upload failed: {str(e)}"
            )
        except Exception as event_error:
            logger.error(f"Failed to publish task status update event: {event_error}")
        
        raise

@celery_app.task(bind=True, queue='document_queue')
def process_document(self, document_id: str, user_id: str):
    """
    Process document content (extract text, chunk, etc.)
    """
    task_id = self.request.id
    
    try:
        # Publish processing started event (with error handling)
        try:
            event_publisher.publish_document_processing(
                user_id=user_id,
                document_id=document_id,
                progress=0
            )
        except Exception as event_error:
            logger.error(f"Failed to publish processing started event: {event_error}")
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Starting document processing...'}
        )
        
        # Get document from database with retry logic
        db = None
        try:
            db = next(get_db())
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Update document status to processing
            document.status = "processing"
            db.commit()
            logger.info(f"Document {document_id} status updated to processing")
            
            # Process document
            start_time = time.time()
            
            # Use the main process_document method instead of calling individual methods
            result = asyncio.run(document_processor.process_document(document_id, user_id, db))
            
            processing_time = time.time() - start_time
            
            # Update document status to completed
            if db and document:
                document.status = "completed"
                db.commit()
                logger.info(f"Document {document_id} status updated to completed")
            
            logger.info(f"Document {document_id} processed successfully in {processing_time:.2f}s")
            
            # Publish processing completed event (with error handling)
            try:
                event_publisher.publish_document_processed(
                    user_id=user_id,
                    document_id=document_id,
                    chunks_count=10,  # Simulated chunks count
                    processing_time=processing_time
                )
            except Exception as event_error:
                logger.error(f"Failed to publish document processed event: {event_error}")
            
            # Publish task completed event (with error handling)
            try:
                event_publisher.publish_task_status_update(
                    user_id=user_id,
                    task_id=task_id,
                    task_type="document_processing",
                    status="completed",
                    progress=100,
                    message=f"Document {document.filename} processed successfully"
                )
            except Exception as event_error:
                logger.error(f"Failed to publish task status update event: {event_error}")
            
            # Trigger indexing via HTTP call to indexing service
            try:
                import httpx
                async def trigger_indexing():
                    indexing_url = f"{os.environ.get('INDEXING_SERVICE_URL', 'http://indexing-service:8003')}/index"
                    params = {
                        "document_id": document_id,
                        "user_id": user_id
                    }
                    logger.info(f"Calling indexing service: {indexing_url} with params: {params}")
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            indexing_url,
                            params=params
                        )
                        logger.info(f"Indexing service response: {response.status_code} - {response.text}")
                        
                        if response.status_code == 200:
                            logger.info(f"Indexing triggered successfully for document {document_id}")
                        else:
                            logger.error(f"Failed to trigger indexing for document {document_id}: {response.status_code}")
                            logger.error(f"Response: {response.text}")
                
                # Run the async function
                asyncio.run(trigger_indexing())
            except Exception as e:
                logger.error(f"Failed to trigger indexing for document {document_id}: {str(e)}")
                # Don't fail the entire task if indexing trigger fails
                # Just log the error and continue
                logger.warning(f"Document processing will continue without indexing for {document_id}")
            
            return {
                'status': 'success',
                'document_id': document_id,
                'processing_time': processing_time,
                'chunks_count': 10
            }
            
        finally:
            if db:
                db.close()
                logger.debug(f"Database session closed for document {document_id}")
            
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        
        # Update document status to failed using existing session if available
        if db and document:
            try:
                document.status = "failed"
                db.commit()
                logger.info(f"Document {document_id} status updated to failed")
            except Exception as db_error:
                logger.error(f"Failed to update document status to failed: {db_error}")
        else:
            # Create a new session only if needed
            try:
                temp_db = next(get_db())
                temp_document = temp_db.query(Document).filter(Document.id == document_id).first()
                if temp_document:
                    temp_document.status = "failed"
                    temp_db.commit()
                    logger.info(f"Document {document_id} status updated to failed using new session")
                temp_db.close()
            except Exception as temp_db_error:
                logger.error(f"Failed to update document status using new session: {temp_db_error}")
        
        # Publish failure events (with error handling)
        try:
            event_publisher.publish_document_failed(
                user_id=user_id,
                document_id=document_id,
                error_message=str(e)
            )
        except Exception as event_error:
            logger.error(f"Failed to publish document failed event: {event_error}")
        
        try:
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_processing",
                status="failed",
                progress=0,
                message=f"Processing failed: {str(e)}"
            )
        except Exception as event_error:
            logger.error(f"Failed to publish task status update event: {event_error}")
        
        raise

@celery_app.task(bind=True, queue='document_queue')
def cleanup_failed_document(self, document_id: str, user_id: str):
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
                
                logger.info(f"Failed document {document_id} cleaned up successfully")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to cleanup document {document_id}: {str(e)}")
        raise

@celery_app.task(bind=True, queue='document_queue')
def delete_document_async(self, document_id: str, user_id: str):
    """
    Asynchronously delete document and all related data
    """
    task_id = self.request.id
    logger.info(f"Starting async deletion of document {document_id}")
    
    try:
        db = next(get_db())
        
        try:
            # Get document details
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                logger.warning(f"Document {document_id} not found for user {user_id}")
                return {'status': 'not_found', 'document_id': document_id}
            
            filename = document.filename
            file_path = document.file_path
            
            # Publish initial status
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_deletion",
                status="processing",
                progress=10,
                message=f"Starting deletion of {filename}"
            )
            
            # Step 1: Delete from storage (MinIO/S3)
            if file_path:
                try:
                    # Extract the key from the file_path
                    if file_path.startswith("minio://"):
                        key = file_path.split("/", 3)[-1]
                    else:
                        key = file_path
                    
                    await_result = asyncio.run(storage_service.delete_file(key))
                    logger.info(f"Deleted file {key} from storage")
                    
                    event_publisher.publish_task_status_update(
                        user_id=user_id,
                        task_id=task_id,
                        task_type="document_deletion",
                        status="processing",
                        progress=30,
                        message="File deleted from storage"
                    )
                except Exception as e:
                    logger.error(f"Failed to delete file from storage: {str(e)}")
                    # Continue with other deletions even if storage deletion fails
            
            # Step 2: Trigger deletion of document chunks from indexing service
            try:
                import httpx
                indexing_url = settings.INDEXING_SERVICE_URL or "http://indexing-service:8003"
                
                async def delete_chunks():
                    async with httpx.AsyncClient() as client:
                        response = await client.delete(f"{indexing_url}/chunks/{document_id}")
                        return response
                
                chunk_response = asyncio.run(delete_chunks())
                
                if chunk_response.status_code == 200:
                    chunks_data = chunk_response.json()
                    chunks_deleted = chunks_data.get('chunks_deleted', 0)
                    logger.info(f"Deleted {chunks_deleted} chunks for document {document_id}")
                else:
                    logger.warning(f"Failed to delete chunks: {chunk_response.status_code}")
                
                event_publisher.publish_task_status_update(
                    user_id=user_id,
                    task_id=task_id,
                    task_type="document_deletion",
                    status="processing",
                    progress=60,
                    message="Document chunks deleted from index"
                )
                
            except Exception as e:
                logger.error(f"Failed to delete chunks from indexing service: {str(e)}")
                # Continue with document deletion even if chunk deletion fails
            
            # Step 3: Delete document from database
            db.delete(document)
            db.commit()
            
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_deletion",
                status="processing",
                progress=90,
                message="Document removed from database"
            )
            
            # Final success status
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="document_deletion",
                status="completed",
                progress=100,
                message=f"Document '{filename}' deleted successfully"
            )
            
            logger.info(f"Successfully deleted document {document_id}")
            
            return {
                'status': 'success',
                'document_id': document_id,
                'filename': filename
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        
        # Publish failure event
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="document_deletion",
            status="failed",
            progress=0,
            message=f"Deletion failed: {str(e)}"
        )
        
        raise

@celery_app.task(bind=True, queue='document_queue')
def bulk_delete_documents_async(self, document_ids: list, user_id: str):
    """
    Asynchronously delete multiple documents and all related data
    """
    task_id = self.request.id
    total_docs = len(document_ids)
    logger.info(f"Starting bulk deletion of {total_docs} documents")
    
    try:
        db = next(get_db())
        
        try:
            # Get document details
            documents = db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.user_id == user_id
            ).all()
            
            if not documents:
                logger.warning(f"No documents found for user {user_id}")
                return {'status': 'not_found', 'document_ids': document_ids}
            
            # Publish initial status
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="bulk_document_deletion",
                status="processing",
                progress=5,
                message=f"Starting bulk deletion of {len(documents)} documents"
            )
            
            deleted_count = 0
            failed_count = 0
            
            # Process each document
            for i, document in enumerate(documents):
                try:
                    filename = document.filename
                    file_path = document.file_path
                    
                    # Update progress
                    progress = 10 + (i * 70 / total_docs)
                    event_publisher.publish_task_status_update(
                        user_id=user_id,
                        task_id=task_id,
                        task_type="bulk_document_deletion",
                        status="processing",
                        progress=int(progress),
                        message=f"Deleting {filename} ({i+1}/{len(documents)})"
                    )
                    
                    # Delete from storage
                    if file_path:
                        try:
                            if file_path.startswith("minio://"):
                                key = file_path.split("/", 3)[-1]
                            else:
                                key = file_path
                            
                            asyncio.run(storage_service.delete_file(key))
                            logger.info(f"Deleted file {key} from storage")
                        except Exception as e:
                            logger.error(f"Failed to delete file from storage: {str(e)}")
                    
                    # Delete chunks from indexing service
                    try:
                        import httpx
                        indexing_url = settings.INDEXING_SERVICE_URL or "http://indexing-service:8003"
                        
                        async def delete_chunks():
                            async with httpx.AsyncClient() as client:
                                response = await client.delete(f"{indexing_url}/chunks/{document.id}")
                                return response
                        
                        chunk_response = asyncio.run(delete_chunks())
                        
                        if chunk_response.status_code == 200:
                            chunks_data = chunk_response.json()
                            chunks_deleted = chunks_data.get('chunks_deleted', 0)
                            logger.info(f"Deleted {chunks_deleted} chunks for document {document.id}")
                        else:
                            logger.warning(f"Failed to delete chunks: {chunk_response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"Failed to delete chunks from indexing service: {str(e)}")
                    
                    # Delete from database
                    db.delete(document)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to delete document {document.id}: {str(e)}")
                    failed_count += 1
            
            # Commit all database changes
            db.commit()
            
            # Final progress update
            event_publisher.publish_task_status_update(
                user_id=user_id,
                task_id=task_id,
                task_type="bulk_document_deletion",
                status="processing",
                progress=90,
                message="Finalizing bulk deletion..."
            )
            
            # Final success status
            if failed_count == 0:
                event_publisher.publish_task_status_update(
                    user_id=user_id,
                    task_id=task_id,
                    task_type="bulk_document_deletion",
                    status="completed",
                    progress=100,
                    message=f"Successfully deleted {deleted_count} documents"
                )
            else:
                event_publisher.publish_task_status_update(
                    user_id=user_id,
                    task_id=task_id,
                    task_type="bulk_document_deletion",
                    status="completed",
                    progress=100,
                    message=f"Deleted {deleted_count} documents ({failed_count} failed)"
                )
            
            logger.info(f"Bulk deletion completed: {deleted_count} deleted, {failed_count} failed")
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'failed_count': failed_count,
                'document_ids': document_ids
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to bulk delete documents: {str(e)}")
        
        # Publish failure event
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="bulk_document_deletion",
            status="failed",
            progress=0,
            message=f"Bulk deletion failed: {str(e)}"
        )
        
        raise
