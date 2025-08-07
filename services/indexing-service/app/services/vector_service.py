"""
Vector Service for Study AI Platform
Handles document processing, embedding generation, and vector search
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np
# from sentence_transformers import SentenceTransformer  # Temporarily disabled
from ..models import DocumentChunk
import logging

logger = logging.getLogger(__name__)

class VectorService:
    """Service for handling vector operations and document processing"""
    
    def __init__(self):
        # Initialize with mock model for now
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Temporarily disabled
        logger.info("Vector service initialized with mock model")
    
    async def process_document(self, document_id: str, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a document and create chunks with embeddings"""
        try:
            # Simulate document text extraction (in real implementation, this would extract text from the file)
            # For now, we'll create sample chunks
            sample_text = f"Sample content for document {document_id}. This is a placeholder for the actual document content."
            
            # Create chunks (in real implementation, this would split the actual document text)
            chunks = []
            chunk_size = 500  # characters per chunk
            overlap = 100     # overlap between chunks
            
            for i in range(0, len(sample_text), chunk_size - overlap):
                chunk_text = sample_text[i:i + chunk_size]
                if chunk_text.strip():
                    # Generate mock embedding for the chunk
                    embedding = await self.generate_embedding(chunk_text)
                    
                    chunks.append({
                        "content": chunk_text,
                        "embedding": embedding,
                        "index": len(chunks)
                    })
            
            logger.info(f"Processed document {document_id} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for a text string"""
        try:
            # Generate a mock 384-dimensional embedding
            import random
            embedding = [random.uniform(-1, 1) for _ in range(384)]
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        limit: int, 
        db: Session
    ) -> List[Any]:
        """Search for similar chunks using vector similarity"""
        try:
            # Convert embedding to list for pgvector
            if hasattr(query_embedding, 'tolist'):
                embedding_list = query_embedding.tolist()
            else:
                embedding_list = query_embedding
            
            # Convert list to string format for pgvector
            embedding_str = '[' + ','.join(map(str, embedding_list)) + ']'
            
            # Perform vector similarity search using pgvector
            query = text(f"""
                SELECT 
                    id as chunk_id,
                    document_id,
                    content,
                    embedding <=> '{embedding_str}'::vector as distance
                FROM document_chunks 
                ORDER BY embedding <=> '{embedding_str}'::vector 
                LIMIT {limit}
            """)
            
            result = db.execute(query)
            
            return result.fetchall()
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            raise
    
    async def search_similar_chunks_within_subject(
        self, 
        query_embedding: List[float], 
        subject_id: int,
        limit: int, 
        db: Session
    ) -> List[Any]:
        """Search for similar chunks within a specific subject"""
        try:
            # Convert embedding to numpy array for pgvector
            embedding_array = np.array(query_embedding)
            
            # Perform vector similarity search within subject
            query = text("""
                SELECT 
                    id as chunk_id,
                    document_id,
                    content,
                    1 - (embedding <=> :embedding) as similarity_score
                FROM document_chunks 
                WHERE subject_id = :subject_id
                ORDER BY embedding <=> :embedding 
                LIMIT :limit
            """)
            
            result = db.execute(query, {
                "embedding": embedding_array,
                "subject_id": subject_id,
                "limit": limit
            })
            
            return result.fetchall()
            
        except Exception as e:
            logger.error(f"Error in subject-based vector search: {str(e)}")
            raise
    
    async def search_similar_chunks_within_category(
        self, 
        query_embedding: List[float], 
        category_id: int,
        limit: int, 
        db: Session
    ) -> List[Any]:
        """Search for similar chunks within a specific category"""
        try:
            # Convert embedding to numpy array for pgvector
            embedding_array = np.array(query_embedding)
            
            # Perform vector similarity search within category
            query = text("""
                SELECT 
                    id as chunk_id,
                    document_id,
                    content,
                    1 - (embedding <=> :embedding) as similarity_score
                FROM document_chunks 
                WHERE category_id = :category_id
                ORDER BY embedding <=> :embedding 
                LIMIT :limit
            """)
            
            result = db.execute(query, {
                "embedding": embedding_array,
                "category_id": category_id,
                "limit": limit
            })
            
            return result.fetchall()
            
        except Exception as e:
            logger.error(f"Error in category-based vector search: {str(e)}")
            raise
    
    async def get_subject_context(self, subject_id: int, db: Session) -> str:
        """Get context from all chunks in a subject for quiz generation"""
        try:
            # Get all chunks for the subject
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.subject_id == subject_id
            ).order_by(DocumentChunk.document_id, DocumentChunk.chunk_index).all()
            
            # Combine all chunk content
            context = "\n\n".join([chunk.content for chunk in chunks])
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting subject context: {str(e)}")
            raise
    
    async def get_category_context(self, category_id: int, db: Session) -> str:
        """Get context from all chunks in a category for quiz generation"""
        try:
            # Get all chunks for the category
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.category_id == category_id
            ).order_by(DocumentChunk.document_id, DocumentChunk.chunk_index).all()
            
            # Combine all chunk content
            context = "\n\n".join([chunk.content for chunk in chunks])
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting category context: {str(e)}")
            raise 