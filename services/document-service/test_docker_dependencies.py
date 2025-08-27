#!/usr/bin/env python3
"""
Test script to verify all dependencies are available
This simulates what should work in the Docker container
"""

import sys
import os

def test_dependencies():
    """Test all required dependencies"""
    print("Testing Document Service Dependencies...")
    print("=" * 50)
    
    # Test core web framework
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn: {e}")
    
    # Test database dependencies
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy: {e}")
    
    try:
        import psycopg2
        print("✅ psycopg2: Available")
    except ImportError as e:
        print(f"❌ psycopg2: {e}")
    
    # Test document processing - PDF
    try:
        import PyPDF2
        print(f"✅ PyPDF2: {PyPDF2.__version__}")
    except ImportError as e:
        print(f"❌ PyPDF2: {e}")
    
    try:
        import pdf2image
        print("✅ pdf2image: Available")
    except ImportError as e:
        print(f"❌ pdf2image: {e}")
    
    try:
        import PIL
        print(f"✅ Pillow: {PIL.__version__}")
    except ImportError as e:
        print(f"❌ Pillow: {e}")
    
    try:
        import pytesseract
        print("✅ pytesseract: Available")
    except ImportError as e:
        print(f"❌ pytesseract: {e}")
    
    # Test document processing - Office
    try:
        import docx
        print("✅ python-docx: Available")
    except ImportError as e:
        print(f"❌ python-docx: {e}")
    
    try:
        import openpyxl
        print(f"✅ openpyxl: {openpyxl.__version__}")
    except ImportError as e:
        print(f"❌ openpyxl: {e}")
    
    # Test data processing
    try:
        import pandas
        print(f"✅ pandas: {pandas.__version__}")
    except ImportError as e:
        print(f"❌ pandas: {e}")
    
    try:
        import numpy
        print(f"✅ numpy: {numpy.__version__}")
    except ImportError as e:
        print(f"❌ numpy: {e}")
    
    # Test storage and utilities
    try:
        import minio
        print(f"✅ minio: {minio.__version__}")
    except ImportError as e:
        print(f"❌ minio: {e}")
    
    try:
        import magic
        print("✅ python-magic: Available")
    except ImportError as e:
        print(f"❌ python-magic: {e}")
    
    try:
        import chardet
        print(f"✅ chardet: {chardet.__version__}")
    except ImportError as e:
        print(f"❌ chardet: {e}")
    
    # Test background tasks
    try:
        import celery
        print(f"✅ celery: {celery.__version__}")
    except ImportError as e:
        print(f"❌ celery: {e}")
    
    try:
        import redis
        print(f"✅ redis: {redis.__version__}")
    except ImportError as e:
        print(f"❌ redis: {e}")
    
    # Test OCR capabilities
    print("\nTesting OCR Capabilities:")
    print("-" * 30)
    
    try:
        import pytesseract
        # Check if tesseract is available in system
        import subprocess
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Tesseract OCR: Available in system")
            print(f"   Version: {result.stdout.split()[1] if result.stdout else 'Unknown'}")
        else:
            print("⚠️ Tesseract OCR: Installed but not working in system")
    except Exception as e:
        print(f"❌ Tesseract OCR: {e}")
    
    # Test PDF processing capabilities
    print("\nTesting PDF Processing:")
    print("-" * 30)
    
    try:
        import PyPDF2
        # Test basic PDF functionality
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000111 00000 n \n0000000206 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        
        import io
        pdf_stream = io.BytesIO(test_pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        print(f"✅ PyPDF2: Can read PDF files ({len(pdf_reader.pages)} pages)")
        
        # Test text extraction
        if len(pdf_reader.pages) > 0:
            text = pdf_reader.pages[0].extract_text()
            print(f"✅ PyPDF2: Can extract text ('{text.strip()}')")
        else:
            print("⚠️ PyPDF2: PDF has no pages")
            
    except Exception as e:
        print(f"❌ PyPDF2: {e}")
    
    print("\n" + "=" * 50)
    print("Dependency test completed!")

if __name__ == "__main__":
    test_dependencies()
