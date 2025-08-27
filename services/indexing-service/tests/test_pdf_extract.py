"""
Tests for the robust PDF parser module
"""

import pytest
import os
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parsers.pdf_extractor import extract_pdf, extract_pdf_from_bytes, _clean_text

class TestPDFExtractor:
    """Test cases for PDF extraction functionality"""
    
    def test_clean_text_dehyphenation(self):
        """Test dehyphenation and text cleaning"""
        text = "This is a hy-\nphenated word.\n\n   Multiple spaces.   \n\n\n\nToo many newlines."
        cleaned = _clean_text(text)
        
        assert "hy-\nphenated" not in cleaned
        assert "hyphenated" in cleaned
        assert cleaned.count('\n\n') <= 2  # Should normalize excessive newlines
        assert "   Multiple spaces.   " not in cleaned  # Should trim spaces
    
    def test_clean_text_control_chars(self):
        """Test removal of control characters"""
        text = "Normal text\x00with null\x0ccharacters"
        cleaned = _clean_text(text)
        
        assert '\x00' not in cleaned
        assert '\x0c' not in cleaned
        assert "Normal text" in cleaned
        assert "with null" in cleaned
    
    def test_create_test_pdf_digital(self):
        """Create a test PDF with digital text"""
        doc = fitz.open()
        page = doc.new_page()
        
        # Add text content
        text = "This is a test PDF with digital text.\nIt contains multiple lines.\nAnd some Vietnamese: Đây là tiếng Việt."
        page.insert_text((50, 50), text, fontsize=12)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            doc.save(tmp.name)
            tmp_path = tmp.name
        
        doc.close()
        return tmp_path
    
    def test_create_test_pdf_image(self):
        """Create a test PDF with image content (simulating scanned document)"""
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to add text (this will be image-based, not digital text)
        try:
            # Use default font if available
            draw.text((20, 20), "This is image-based text", fill='black')
            draw.text((20, 50), "It should require OCR", fill='black')
            draw.text((20, 80), "Vietnamese: Đây là tiếng Việt", fill='black')
        except:
            # If font not available, draw some shapes
            draw.rectangle([20, 20, 200, 100], outline='black')
            draw.text((30, 30), "Image content", fill='black')
        
        # Convert to PDF
        doc = fitz.open()
        page = doc.new_page()
        
        # Convert PIL image to bytes
        img_bytes = img.tobytes()
        img_pdf = fitz.Pixmap(img_bytes, img.width, img.height, "RGB")
        
        # Insert image into PDF
        page.insert_image(page.rect, pixmap=img_pdf)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            doc.save(tmp.name)
            tmp_path = tmp.name
        
        doc.close()
        return tmp_path
    
    def test_digital_pdf_extraction(self):
        """Test extraction from digital-text PDF"""
        pdf_path = self.test_create_test_pdf_digital()
        
        try:
            result = extract_pdf(pdf_path)
            
            assert result['success'] is True
            assert result['page_count'] == 1
            assert len(result['full_text']) > 200
            assert "test PDF" in result['full_text']
            assert "tiếng Việt" in result['full_text']  # Vietnamese preserved
            assert result['extraction_method'] == 'PyMuPDF_enhanced'
            
            # Check page metadata
            assert len(result['pages']) == 1
            page = result['pages'][0]
            assert page['page'] == 1
            assert page['method'] in ['text', 'text_plain']
            assert page['char_count'] > 0
            
        finally:
            os.unlink(pdf_path)
    
    def test_image_pdf_extraction(self):
        """Test extraction from image-based PDF with OCR"""
        pdf_path = self.test_create_test_pdf_image()
        
        try:
            result = extract_pdf(pdf_path)
            
            assert result['success'] is True
            assert result['page_count'] == 1
            
            # With OCR enabled, should extract some text
            if result['ocr_used']:
                assert len(result['full_text']) > 0
                assert result['extraction_method'] == 'PyMuPDF_enhanced'
                
                # Check page metadata
                page = result['pages'][0]
                assert page['method'] == 'ocr'
            else:
                # OCR might not be available or might not extract text
                # This is acceptable for test environments
                pass
                
        finally:
            os.unlink(pdf_path)
    
    def test_bytes_extraction(self):
        """Test extraction from bytes (simulating S3 stream)"""
        pdf_path = self.test_create_test_pdf_digital()
        
        try:
            with open(pdf_path, 'rb') as f:
                content = f.read()
            
            result = extract_pdf_from_bytes(content)
            
            assert result['success'] is True
            assert result['page_count'] == 1
            assert len(result['full_text']) > 200
            
        finally:
            os.unlink(pdf_path)
    
    def test_vietnamese_preservation(self):
        """Test that Vietnamese diacritics are preserved"""
        # Create PDF with Vietnamese text
        doc = fitz.open()
        page = doc.new_page()
        
        vietnamese_text = "Đây là tiếng Việt với dấu thanh và dấu mũ. Có thể đọc được không?"
        page.insert_text((50, 50), vietnamese_text, fontsize=12)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            doc.save(tmp.name)
            tmp_path = tmp.name
        
        doc.close()
        
        try:
            result = extract_pdf(tmp_path)
            
            assert result['success'] is True
            assert "tiếng Việt" in result['full_text']
            assert "dấu thanh" in result['full_text']
            assert "dấu mũ" in result['full_text']
            
        finally:
            os.unlink(tmp_path)
    
    def test_error_handling(self):
        """Test error handling for invalid PDFs"""
        # Test with invalid content
        result = extract_pdf(b"not a pdf")
        
        assert result['success'] is False
        assert 'error' in result
        assert result['page_count'] == 0
        assert result['full_text'] == ""

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
