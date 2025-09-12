# requirements: pymupdf (fitz) - OCR removed for smaller image size
# open from bytes and from file path; keep page numbers and per-page text

import io
import os
import fitz
import re
from typing import List, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

def _clean_text(t: str) -> str:
    """Clean and normalize extracted text"""
    if not t:
        return ""
    
    # dehyphenation and paragraph join
    t = re.sub(r"-\s*\n", "", t)           # join hyphenated line-breaks
    t = re.sub(r"[ \t]+\n", "\n", t)       # trim trailing spaces
    t = re.sub(r"\n{3,}", "\n\n", t)       # collapse huge gaps
    t = re.sub(r"\s+", " ", t)             # normalize whitespace
    t = re.sub(r"[^\w\s\-\.,;:!?()\[\]{}'\"]", "", t)  # remove control chars
    
    return t.strip()

def extract_pdf(content: Union[bytes, str]) -> Dict:
    """
    Extract text from PDF with robust fallback strategies
    
    Args:
        content: bytes (S3 download) or file path
        
    Returns:
        Dict with structure:
        {
            "pages": [{"page": i, "text": "...", "method": "..."}],
            "full_text": "...",
            "page_count": N,
            "extraction_method": "PyMuPDF_enhanced",
            "ocr_used": bool,
            "success": bool
        }
    """
    try:
        if isinstance(content, (bytes, bytearray)):
            doc = fitz.open(stream=content, filetype="pdf")
        else:
            doc = fitz.open(content)  # file path

        pages = []
        total_txt = []
        extraction_method = "PyMuPDF_text_only"

        for i in range(len(doc)):
            page = doc[i]
            page_text = ""
            method_used = "text"
            
            # Try digital text first - structured blocks for better layout preservation
            try:
                blocks = page.get_text("blocks")
                if blocks:
                    # Extract text from blocks, preserving some layout
                    text_parts = []
                    for block in blocks:
                        if len(block) >= 5:  # block[4] contains text
                            text_parts.append(block[4])
                    page_text = "\n".join(text_parts).strip()
                    
                    # If blocks give too little text, try plain mode
                    if len(page_text) < 25:
                        page_text = page.get_text("text").strip()
                        method_used = "text_plain"
                else:
                    page_text = page.get_text("text").strip()
                    method_used = "text_plain"
            except Exception as e:
                logger.warning(f"Text extraction failed for page {i+1}: {e}")
                page_text = page.get_text("text").strip()
                method_used = "text_plain"

            # OCR functionality removed for smaller image size
            # Text extraction relies on PyMuPDF text extraction only

            # Clean the extracted text
            cleaned_text = _clean_text(page_text)
            
            pages.append({
                "page": i + 1, 
                "text": cleaned_text,
                "method": method_used,
                "char_count": len(cleaned_text),
                "word_count": len(cleaned_text.split()) if cleaned_text else 0
            })
            
            if cleaned_text:
                total_txt.append(cleaned_text)

        # Combine all text
        full_text = "\n\n".join(total_txt).strip()
        
        # Calculate overall statistics
        total_chars = sum(p["char_count"] for p in pages)
        total_words = sum(p["word_count"] for p in pages)
        pages_with_content = len([p for p in pages if p["text"]])
        
        result = {
            "pages": pages,
            "full_text": full_text,
            "page_count": len(doc),
            "extraction_method": extraction_method,
            "success": True,
            "statistics": {
                "total_characters": total_chars,
                "total_words": total_words,
                "pages_with_content": pages_with_content,
                "average_chars_per_page": total_chars / len(doc) if doc else 0,
                "average_words_per_page": total_words / len(doc) if doc else 0
            }
        }
        
        doc.close()
        return result
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "pages": [],
            "full_text": "",
            "page_count": 0,
            "extraction_method": "failed"
        }

def extract_pdf_from_bytes(content: bytes) -> Dict:
    """Convenience function for extracting from bytes (S3 streams)"""
    return extract_pdf(content)

def extract_pdf_from_path(file_path: str) -> Dict:
    """Convenience function for extracting from file path"""
    return extract_pdf(file_path)

def get_pdf_info(content: Union[bytes, str]) -> Dict:
    """Get basic PDF information without full text extraction"""
    try:
        if isinstance(content, (bytes, bytearray)):
            doc = fitz.open(stream=content, filetype="pdf")
        else:
            doc = fitz.open(file_path)
            
        info = {
            "page_count": len(doc),
            "file_size": len(content) if isinstance(content, bytes) else os.path.getsize(content),
            "metadata": doc.metadata,
            "success": True
        }
        
        doc.close()
        return info
        
    except Exception as e:
        logger.error(f"PDF info extraction failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
