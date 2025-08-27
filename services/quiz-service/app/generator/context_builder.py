"""
Context Builder for Quiz Generation
Fetches and curates document chunks for direct quiz generation
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def fetch_chunks_for_docs(session: Session, doc_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Fetch document chunks from the database for the given document IDs.
    
    Args:
        session: Database session
        doc_ids: List of document IDs to fetch chunks for
        
    Returns:
        List of chunk dictionaries with fields: id, doc_id, file_name, chunk_id, 
        section_path, char_range, text
    """
    try:
        # Import here to avoid circular imports
        from app.models import DocumentChunk
        
        query = session.query(DocumentChunk).filter(
            DocumentChunk.document_id.in_(doc_ids)
        ).order_by(DocumentChunk.document_id, DocumentChunk.chunk_id)
        
        chunks = query.all()
        
        # Convert to dictionary format
        chunk_dicts = []
        for chunk in chunks:
            chunk_dict = {
                "id": f"c{chunk.id:04d}",  # Deterministic ID format
                "doc_id": chunk.document_id,
                "file_name": getattr(chunk.document, 'file_name', 'Unknown') if hasattr(chunk, 'document') else 'Unknown',
                "chunk_id": chunk.chunk_id,
                "section_path": getattr(chunk, 'section_path', ''),
                "char_range": f"{getattr(chunk, 'start_char', 0)}-{getattr(chunk, 'end_char', 0)}",
                "text": chunk.content or chunk.text or ""
            }
            chunk_dicts.append(chunk_dict)
            
        logger.info(f"Fetched {len(chunk_dicts)} chunks for {len(doc_ids)} documents")
        return chunk_dicts
        
    except Exception as e:
        logger.error(f"Error fetching chunks: {e}")
        return []


def curate_blocks(
    chunks: List[Dict[str, Any]], 
    max_chars: int = 60000, 
    per_doc_cap: int = 25, 
    clip: int = 700
) -> List[Dict[str, Any]]:
    """
    Curate and prepare context blocks for quiz generation.
    
    Args:
        chunks: List of chunk dictionaries from fetch_chunks_for_docs
        max_chars: Maximum total characters to include
        per_doc_cap: Maximum chunks per document
        clip: Maximum characters per chunk (will truncate if longer)
        
    Returns:
        List of curated blocks ready for prompt injection
    """
    if not chunks:
        return []
    
    # Group chunks by document
    doc_chunks = {}
    for chunk in chunks:
        doc_id = chunk["doc_id"]
        if doc_id not in doc_chunks:
            doc_chunks[doc_id] = []
        doc_chunks[doc_id].append(chunk)
    
    # Apply per-document cap and sort by chunk_id
    curated_chunks = []
    total_chars = 0
    
    for doc_id, doc_chunk_list in doc_chunks.items():
        # Sort by chunk_id and take up to per_doc_cap
        sorted_chunks = sorted(doc_chunk_list, key=lambda x: x["chunk_id"])
        selected_chunks = sorted_chunks[:per_doc_cap]
        
        for chunk in selected_chunks:
            # Clip text if too long
            text = chunk["text"]
            if len(text) > clip:
                text = text[:clip] + "..."
                chunk["text"] = text
            
            # Check if adding this chunk would exceed max_chars
            if total_chars + len(text) > max_chars:
                break
                
            curated_chunks.append(chunk)
            total_chars += len(text)
            
            if total_chars >= max_chars:
                break
        
        if total_chars >= max_chars:
            break
    
    logger.info(f"Curated {len(curated_chunks)} blocks with {total_chars} total characters")
    return curated_chunks


def create_context_summary(blocks: List[Dict[str, Any]]) -> str:
    """
    Create a summary of the context blocks for logging/debugging.
    
    Args:
        blocks: List of curated blocks
        
    Returns:
        Summary string
    """
    if not blocks:
        return "No context blocks"
    
    doc_count = len(set(b["doc_id"] for b in blocks))
    total_chars = sum(len(b["text"]) for b in blocks)
    
    return f"{len(blocks)} blocks from {doc_count} documents ({total_chars} chars)"
