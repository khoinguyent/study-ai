import asyncio
import time
from typing import List, Dict, Any
import httpx
import logging
from ..config import settings
from ..models import Document
from ..database import get_db
from sqlalchemy.orm import Session
from .text_extractor import TextExtractor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Asynchronous document processor"""
    
    def __init__(self):
        self.notification_url = settings.NOTIFICATION_SERVICE_URL
        self.indexing_url = settings.INDEXING_SERVICE_URL
        self.text_extractor = TextExtractor()
    
    async def process_document(self, document_id: str, user_id: str, db: Session = None):
        """Process document asynchronously"""
        start_time = time.time()
        
        # Create a new database session if none provided
        if db is None:
            db = next(get_db())
        
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Update document status to processing
            document.status = "processing"
            db.commit()
            
            # Process document with actual text extraction
            extraction_result = await self._extract_text(document_id, user_id, db)
            if not extraction_result['success']:
                raise Exception(f"Text extraction failed: {extraction_result.get('error', 'Unknown error')}")
            
            # Chunk the extracted text
            chunks = await self._chunk_document(extraction_result['text'], document_id, user_id)
            
            # Trigger indexing with the extracted text and chunks
            await self._trigger_indexing(document_id, user_id, extraction_result, chunks)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update document status to completed
            document.status = "completed"
            db.commit()
            
            logger.info(f"Document {document_id} processing completed successfully in {processing_time:.2f}s")
            logger.info(f"Extracted {extraction_result['word_count']} words, created {len(chunks)} chunks")
            
        except Exception as e:
            # Update document status to failed
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                db.commit()
            logger.error(f"Document {document_id} processing failed: {str(e)}")
            raise
        finally:
            # Close the database session
            if db:
                db.close()
    
    async def _extract_text(self, document_id: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Extract text from document using the text extractor service"""
        try:
            # Get document from database to access file path
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise Exception(f"Document {document_id} not found")
            
            # Get file content from storage service
            from .storage_service import StorageService
            storage_service = StorageService()
            
            # Extract file key from file_path (remove minio:// prefix if present)
            file_key = document.file_path
            if file_key.startswith('minio://'):
                file_key = file_key.replace('minio://', '')
            
            # Download file content
            file_content = await storage_service.download_file(file_key)
            
            # Extract text using the text extractor
            if document.content_type == "application/pdf":
                # Use enhanced PDF extraction with fallback strategies
                extraction_result = await self.text_extractor.extract_pdf_with_fallback(
                    file_content=file_content,
                    filename=document.filename
                )
            else:
                # Use standard text extraction for other formats
                extraction_result = await self.text_extractor.extract_text(
                    file_content=file_content,
                    content_type=document.content_type,
                    filename=document.filename
                )
            
            if not extraction_result['success']:
                raise Exception(f"Text extraction failed: {extraction_result.get('error', 'Unknown error')}")
            
            logger.info(f"Successfully extracted text from {document.filename}: {extraction_result['word_count']} words")
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Failed to extract text from document {document_id}: {str(e)}")
            raise Exception(f"Text extraction failed: {str(e)}")
    
    async def _chunk_document(self, text: str, document_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Chunk document into smaller pieces for better processing"""
        try:
            # Simple chunking strategy: split by paragraphs and limit chunk size
            paragraphs = text.split('\n\n')
            chunks = []
            current_chunk = []
            current_size = 0
            max_chunk_size = 1000  # characters per chunk
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # If adding this paragraph would exceed chunk size, save current chunk
                if current_size + len(paragraph) > max_chunk_size and current_chunk:
                    chunks.append({
                        'content': '\n\n'.join(current_chunk),
                        'size': current_size,
                        'type': 'paragraph'
                    })
                    current_chunk = [paragraph]
                    current_size = len(paragraph)
                else:
                    current_chunk.append(paragraph)
                    current_size += len(paragraph)
            
            # Add the last chunk if it has content
            if current_chunk:
                chunks.append({
                    'content': '\n\n'.join(current_chunk),
                    'size': current_size,
                    'type': 'paragraph'
                })
            
            logger.info(f"Created {len(chunks)} chunks from document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {str(e)}")
            # Return single chunk with full text if chunking fails
            return [{
                'content': text,
                'size': len(text),
                'type': 'full_text'
            }]
    
    async def _trigger_indexing(self, document_id: str, user_id: str, extraction_result: Dict[str, Any], chunks: List[Dict[str, Any]]):
        """Trigger indexing service with extracted text and chunks"""
        try:
            # Prepare indexing data
            indexing_data = {
                'document_id': document_id,
                'user_id': user_id,
                'text': extraction_result['text'],
                'chunks': chunks,
                'metadata': extraction_result['metadata'],
                'word_count': extraction_result['word_count'],
                'extraction_method': extraction_result['extraction_method']
            }
            
            # Trigger indexing service
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.indexing_url}/index?document_id={document_id}&user_id={user_id}",
                        json=indexing_data,
                        timeout=30.0
                    )
                    if response.status_code != 200:
                        raise Exception(f"Indexing service error: {response.text}")
                    
                    logger.info(f"Successfully triggered indexing for document {document_id}")
                    
                except httpx.TimeoutException:
                    raise Exception("Indexing service request timed out")
                except Exception as e:
                    raise Exception(f"Failed to trigger indexing: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to trigger indexing for document {document_id}: {str(e)}")
            raise Exception(f"Indexing failed: {str(e)}")
    
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
                logger.error(f"Failed to create task status: {e}")
    
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
                logger.error(f"Failed to update task status: {e}")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported document formats"""
        return self.text_extractor.get_supported_formats()
    
    def is_format_supported(self, content_type: str) -> bool:
        """Check if a document format is supported"""
        return self.text_extractor.is_format_supported(content_type) 