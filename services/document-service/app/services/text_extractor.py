import asyncio
import io
import os
from typing import Optional, Dict, Any
from pathlib import Path
import logging

# Import text extraction libraries
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available. DOCX files cannot be processed.")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyPDF2 not available. PDF files cannot be processed.")

try:
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("pandas not available. Excel files cannot be processed.")

logger = logging.getLogger(__name__)

class TextExtractor:
    """Service for extracting text from various document formats"""
    
    def __init__(self):
        self.supported_formats = {
            'application/pdf': self._extract_pdf_text if PDF_AVAILABLE else None,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_docx_text if DOCX_AVAILABLE else None,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': self._extract_excel_text if EXCEL_AVAILABLE else None,
            'text/plain': self._extract_plain_text,
            'application/msword': self._extract_doc_text,  # Legacy .doc files
        }
    
    async def extract_text(self, file_content: bytes, content_type: str, filename: str = None) -> Dict[str, Any]:
        """
        Extract text from document content
        
        Args:
            file_content: Raw file bytes
            content_type: MIME type of the file
            filename: Optional filename for better error messages
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Get the appropriate extraction method
            extractor = self.supported_formats.get(content_type)
            
            if not extractor:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Run extraction in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                extractor, 
                file_content, 
                filename
            )
            
            return {
                'success': True,
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'word_count': result.get('word_count', 0),
                'extraction_method': result.get('method', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from {filename or 'unknown file'}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {},
                'word_count': 0
            }
    
    def _extract_docx_text(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """Extract text from DOCX files"""
        try:
            # Create a BytesIO object from the file content
            doc_stream = io.BytesIO(file_content)
            
            # Load the document
            doc = DocxDocument(doc_stream)
            
            # Extract text from paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            
            # Extract text from tables
            tables_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        tables_text.append(' | '.join(row_text))
            
            # Combine all text
            full_text = '\n\n'.join(paragraphs + tables_text)
            
            # Extract metadata
            metadata = {
                'paragraph_count': len(paragraphs),
                'table_count': len(doc.tables),
                'has_headers': any(paragraph.style.name.startswith('Heading') for paragraph in doc.paragraphs),
                'has_footers': len(doc.sections) > 0 and any(section.footer for section in doc.sections),
            }
            
            return {
                'text': full_text,
                'metadata': metadata,
                'word_count': len(full_text.split()),
                'method': 'python-docx'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX file {filename}: {str(e)}")
            raise Exception(f"DOCX text extraction failed: {str(e)}")
    
    def _extract_doc_text(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Extract text from legacy .doc files
        Note: This is a basic implementation. For better support, consider using antiword or similar tools.
        """
        try:
            # For now, we'll return a placeholder since .doc files require additional tools
            # In production, you might want to use antiword, catdoc, or similar tools
            
            # Basic text extraction attempt (this is limited)
            text_content = file_content.decode('utf-8', errors='ignore')
            
            # Try to extract readable text (this is very basic)
            readable_chars = ''.join(char for char in text_content if char.isprintable() or char.isspace())
            
            # Clean up the text
            cleaned_text = ' '.join(readable_chars.split())
            
            return {
                'text': cleaned_text,
                'metadata': {
                    'note': 'Basic .doc extraction - consider using antiword for better results',
                    'file_size': len(file_content)
                },
                'word_count': len(cleaned_text.split()),
                'method': 'basic-doc'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from DOC file {filename}: {str(e)}")
            raise Exception(f"DOC text extraction failed: {str(e)}")
    
    def _extract_pdf_text(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """Extract text from PDF files with enhanced text processing"""
        try:
            # Create a BytesIO object from the file content
            pdf_stream = io.BytesIO(file_content)
            
            # Create PDF reader
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                logger.warning(f"PDF {filename} is encrypted - text extraction may be limited")
            
            # Extract text from all pages with enhanced processing
            text_content = []
            page_metadata = []
            total_words = 0
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # Extract raw text from page
                    raw_text = page.extract_text()
                    
                    if raw_text and raw_text.strip():
                        # Clean and process the text
                        cleaned_text = self._clean_pdf_text(raw_text)
                        
                        if cleaned_text.strip():
                            # Add page separator with metadata
                            page_info = f"--- Page {page_num + 1} ---"
                            text_content.append(page_info)
                            text_content.append(cleaned_text.strip())
                            
                            # Calculate page statistics
                            page_words = len(cleaned_text.split())
                            total_words += page_words
                            
                            page_metadata.append({
                                'page_number': page_num + 1,
                                'word_count': page_words,
                                'character_count': len(cleaned_text),
                                'has_content': True
                            })
                        else:
                            page_metadata.append({
                                'page_number': page_num + 1,
                                'word_count': 0,
                                'character_count': 0,
                                'has_content': False,
                                'note': 'Page contains no extractable text'
                            })
                    else:
                        # Page has no text content
                        page_metadata.append({
                            'page_number': page_num + 1,
                            'word_count': 0,
                            'character_count': 0,
                            'has_content': False,
                            'note': 'Page is empty or contains no text'
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    page_metadata.append({
                        'page_number': page_num + 1,
                        'word_count': 0,
                        'character_count': 0,
                        'has_content': False,
                        'error': str(e)
                    })
                    continue
            
            # Combine all text with proper spacing
            full_text = '\n\n'.join(text_content)
            
            # Enhanced metadata extraction
            metadata = {
                'page_count': len(pdf_reader.pages),
                'pages_with_content': len([p for p in page_metadata if p.get('has_content', False)]),
                'has_encryption': pdf_reader.is_encrypted,
                'file_size': len(file_content),
                'page_metadata': page_metadata,
                'text_quality': self._assess_pdf_text_quality(full_text, page_metadata),
                'extraction_method': 'PyPDF2_enhanced'
            }
            
            # Try to extract additional PDF metadata if available
            try:
                if hasattr(pdf_reader, 'metadata') and pdf_reader.metadata:
                    metadata['pdf_metadata'] = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': pdf_reader.metadata.get('/CreationDate', ''),
                        'modification_date': pdf_reader.metadata.get('/ModDate', '')
                    }
            except Exception as e:
                logger.debug(f"Could not extract PDF metadata: {str(e)}")
            
            return {
                'text': full_text,
                'metadata': metadata,
                'word_count': total_words,
                'method': 'PyPDF2_enhanced'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF file {filename}: {str(e)}")
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    def _clean_pdf_text(self, raw_text: str) -> str:
        """Clean and improve PDF extracted text quality"""
        if not raw_text:
            return ""
        
        # Remove excessive whitespace while preserving structure
        lines = raw_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean individual line
            cleaned_line = self._clean_pdf_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # Join lines with proper spacing
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Final cleanup
        cleaned_text = self._final_pdf_text_cleanup(cleaned_text)
        
        return cleaned_text
    
    def _clean_pdf_line(self, line: str) -> str:
        """Clean individual line from PDF text"""
        if not line:
            return ""
        
        # Remove excessive whitespace
        line = ' '.join(line.split())
        
        # Remove common PDF artifacts
        line = line.replace('\x00', '')  # Null characters
        line = line.replace('\x0c', '')  # Form feed
        
        # Clean up common PDF text issues
        line = line.replace('ﬁ', 'fi')  # Ligatures
        line = line.replace('ﬂ', 'fl')
        line = line.replace('ﬀ', 'ff')
        line = line.replace('ﬃ', 'ffi')
        line = line.replace('ﬄ', 'ffl')
        
        # Remove lines that are just punctuation or symbols
        if len(line.strip()) <= 2 and not line.strip().isalnum():
            return ""
        
        return line.strip()
    
    def _final_pdf_text_cleanup(self, text: str) -> str:
        """Final cleanup of PDF text"""
        if not text:
            return ""
        
        # Remove excessive blank lines
        lines = text.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append(line)
                prev_empty = True
        
        # Join and clean up spacing
        result = '\n'.join(cleaned_lines)
        
        # Remove leading/trailing whitespace
        result = result.strip()
        
        # Normalize paragraph breaks
        result = result.replace('\n\n\n', '\n\n')
        
        return result
    
    def _assess_pdf_text_quality(self, text: str, page_metadata: list) -> dict:
        """Assess the quality of extracted PDF text"""
        if not text:
            return {'score': 0, 'issues': ['No text extracted'], 'quality': 'poor'}
        
        issues = []
        score = 100
        
        # Check text length
        if len(text) < 100:
            issues.append('Very short text - may be image-based PDF')
            score -= 30
        
        # Check for common PDF issues
        if '\x00' in text:
            issues.append('Contains null characters')
            score -= 10
        
        if text.count('\n') > len(text) * 0.1:  # Too many line breaks
            issues.append('Excessive line breaks - poor text structure')
            score -= 15
        
        # Check word density
        words = text.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length < 2:
                issues.append('Very short words - possible OCR artifacts')
                score -= 20
        
        # Check page coverage
        pages_with_content = len([p for p in page_metadata if p.get('has_content', False)])
        total_pages = len(page_metadata)
        if total_pages > 0:
            coverage = pages_with_content / total_pages
            if coverage < 0.5:
                issues.append(f'Low text coverage: {coverage:.1%} of pages have content')
                score -= 25
        
        # Determine quality level
        if score >= 80:
            quality = 'excellent'
        elif score >= 60:
            quality = 'good'
        elif score >= 40:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'score': max(0, score),
            'issues': issues,
            'quality': quality,
            'text_length': len(text),
            'word_count': len(words),
            'page_coverage': pages_with_content / total_pages if total_pages > 0 else 0
        }
    
    def _get_pdf_processing_recommendations(self, quality_assessment: dict) -> list:
        """Get recommendations for improving PDF text extraction"""
        recommendations = []
        
        if quality_assessment['quality'] == 'poor':
            recommendations.append({
                'priority': 'high',
                'action': 'OCR Processing',
                'description': 'Consider using OCR (Optical Character Recognition) for image-based PDFs',
                'tools': ['Tesseract', 'Adobe Acrobat Pro', 'Online OCR services']
            })
            
            if quality_assessment.get('page_coverage', 0) < 0.5:
                recommendations.append({
                    'priority': 'high',
                    'action': 'Page Analysis',
                    'description': 'Many pages contain no text - may be scanned documents or images',
                    'tools': ['PDF page inspection tools', 'Image analysis software']
                })
        
        if quality_assessment.get('issues'):
            for issue in quality_assessment['issues']:
                if 'null characters' in issue:
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'Text Cleaning',
                        'description': 'Remove null characters and other artifacts',
                        'tools': ['Text preprocessing scripts', 'PDF repair tools']
                    })
                
                if 'excessive line breaks' in issue:
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'Text Structure Analysis',
                        'description': 'Analyze and fix text structure issues',
                        'tools': ['Text analysis tools', 'PDF layout analysis']
                    })
        
        if quality_assessment['score'] < 60:
            recommendations.append({
                'priority': 'medium',
                'action': 'Alternative Extraction',
                'description': 'Try different PDF text extraction libraries',
                'tools': ['pdfplumber', 'pdfminer', 'PyMuPDF (fitz)']
            })
        
        return recommendations
    
    def extract_pdf_with_fallback(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Extract text from PDF with fallback strategies for poor quality text
        
        This method attempts to extract text and provides recommendations
        for improving extraction quality when needed.
        """
        try:
            # First attempt: Standard text extraction
            extraction_result = self._extract_pdf_text(file_content, filename)
            
            # Assess text quality
            quality_assessment = extraction_result['metadata']['text_quality']
            
            # Add recommendations if quality is poor
            if quality_assessment['quality'] in ['poor', 'fair']:
                recommendations = self._get_pdf_processing_recommendations(quality_assessment)
                extraction_result['metadata']['recommendations'] = recommendations
                extraction_result['metadata']['needs_improvement'] = True
                
                # Add alternative extraction suggestions
                extraction_result['metadata']['alternative_methods'] = [
                    {
                        'method': 'OCR Processing',
                        'description': 'Use OCR for image-based PDFs',
                        'estimated_accuracy': '85-95%',
                        'requirements': 'OCR software or service'
                    },
                    {
                        'method': 'Layout Analysis',
                        'description': 'Analyze PDF layout for better text extraction',
                        'estimated_accuracy': '70-85%',
                        'requirements': 'Advanced PDF processing tools'
                    },
                    {
                        'method': 'Manual Review',
                        'description': 'Review and manually correct extracted text',
                        'estimated_accuracy': '95-100%',
                        'requirements': 'Human review time'
                    }
                ]
            else:
                extraction_result['metadata']['needs_improvement'] = False
                extraction_result['metadata']['recommendations'] = []
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"PDF extraction with fallback failed for {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {
                    'extraction_method': 'failed',
                    'quality': 'failed',
                    'recommendations': [
                        {
                            'priority': 'high',
                            'action': 'Error Resolution',
                            'description': f'Fix extraction error: {str(e)}',
                            'tools': ['Error analysis', 'PDF validation']
                        }
                    ]
                },
                'word_count': 0
            }
    
    def _extract_excel_text(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """Extract text from Excel files"""
        try:
            # Create a BytesIO object from the file content
            excel_stream = io.BytesIO(file_content)
            
            # Read Excel file
            excel_data = pd.read_excel(excel_stream, sheet_name=None)
            
            # Extract text from all sheets
            text_content = []
            for sheet_name, sheet_data in excel_data.items():
                if not sheet_data.empty:
                    text_content.append(f"--- Sheet: {sheet_name} ---")
                    
                    # Convert DataFrame to text
                    for index, row in sheet_data.iterrows():
                        row_text = ' | '.join(str(cell) for cell in row if pd.notna(cell))
                        if row_text.strip():
                            text_content.append(row_text)
                    
                    text_content.append("")  # Empty line between sheets
            
            full_text = '\n'.join(text_content)
            
            # Extract metadata
            metadata = {
                'sheet_count': len(excel_data),
                'sheet_names': list(excel_data.keys()),
                'total_rows': sum(len(sheet) for sheet in excel_data.values()),
                'file_size': len(file_content)
            }
            
            return {
                'text': full_text,
                'metadata': metadata,
                'word_count': len(full_text.split()),
                'method': 'pandas'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from Excel file {filename}: {str(e)}")
            raise Exception(f"Excel text extraction failed: {str(e)}")
    
    def _extract_plain_text(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """Extract text from plain text files"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    text_content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all encodings fail, use utf-8 with error handling
                text_content = file_content.decode('utf-8', errors='ignore')
            
            # Clean up the text
            cleaned_text = text_content.strip()
            
            # Extract metadata
            metadata = {
                'encoding': encoding if 'encoding' in locals() else 'unknown',
                'line_count': len(cleaned_text.splitlines()),
                'file_size': len(file_content)
            }
            
            return {
                'text': cleaned_text,
                'metadata': metadata,
                'word_count': len(cleaned_text.split()),
                'method': 'plain-text'
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from plain text file {filename}: {str(e)}")
            raise Exception(f"Plain text extraction failed: {str(e)}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported content types"""
        return [content_type for content_type, extractor in self.supported_formats.items() if extractor is not None]
    
    def is_format_supported(self, content_type: str) -> bool:
        """Check if a content type is supported"""
        return content_type in self.supported_formats and self.supported_formats[content_type] is not None
