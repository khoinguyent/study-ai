#!/usr/bin/env python3
"""
Test script for DOCX parsing and chunking functionality
This script demonstrates the complete pipeline for processing the DOCX file:
1. Text extraction from DOCX
2. Document chunking
3. Chunk analysis and display
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the document service app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'document-service', 'app'))

from services.text_extractor import TextExtractor
from services.document_processor import DocumentProcessor

async def test_docx_parsing_and_chunking():
    """Test the complete DOCX parsing and chunking pipeline"""
    print("Testing DOCX Parsing and Chunking Pipeline")
    print("=" * 60)
    
    # Initialize services
    text_extractor = TextExtractor()
    document_processor = DocumentProcessor()
    
    # Path to the DOCX file
    docx_path = Path("data/Đồng Bằng Sông Cửu Long.docx")
    
    if not docx_path.exists():
        print(f"❌ DOCX file not found: {docx_path}")
        return
    
    print(f"📄 Processing DOCX file: {docx_path}")
    print(f"📊 File size: {docx_path.stat().st_size / 1024:.1f} KB")
    print()
    
    try:
        # Step 1: Extract text from DOCX
        print("🔍 Step 1: Text Extraction")
        print("-" * 30)
        
        with open(docx_path, 'rb') as f:
            file_content = f.read()
        
        # Extract text using the TextExtractor service
        extraction_result = await text_extractor.extract_text(
            file_content, 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            docx_path.name
        )
        
        if not extraction_result['success']:
            print(f"❌ Text extraction failed: {extraction_result.get('error', 'Unknown error')}")
            return
        
        print(f"✅ Text extraction successful!")
        print(f"📝 Word count: {extraction_result['word_count']}")
        print(f"🔧 Extraction method: {extraction_result['extraction_method']}")
        
        # Display metadata
        metadata = extraction_result.get('metadata', {})
        if metadata:
            print(f"📊 Metadata:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
        
        print()
        
        # Step 2: Display extracted text preview
        print("📖 Step 2: Extracted Text Preview")
        print("-" * 30)
        
        extracted_text = extraction_result['text']
        print(f"Full text length: {len(extracted_text)} characters")
        print()
        
        # Show first 500 characters
        preview = extracted_text[:500]
        if len(extracted_text) > 500:
            preview += "..."
        print("Text preview:")
        print("-" * 20)
        print(preview)
        print("-" * 20)
        print()
        
        # Step 3: Document chunking
        print("✂️  Step 3: Document Chunking")
        print("-" * 30)
        
        # Use the document processor's chunking method
        chunks = await document_processor._chunk_document(
            extracted_text, 
            "test-docx-001", 
            "test-user-001"
        )
        
        print(f"✅ Created {len(chunks)} chunks")
        print()
        
        # Step 4: Analyze chunks
        print("📊 Step 4: Chunk Analysis")
        print("-" * 30)
        
        total_chars = 0
        chunk_sizes = []
        
        for i, chunk in enumerate(chunks):
            chunk_size = len(chunk['content'])
            chunk_sizes.append(chunk_size)
            total_chars += chunk_size
            
            print(f"Chunk {i+1}:")
            print(f"  Size: {chunk_size} characters")
            print(f"  Type: {chunk.get('type', 'unknown')}")
            print(f"  Preview: {chunk['content'][:100]}...")
            print()
        
        # Statistics
        print("📈 Chunking Statistics:")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Total characters: {total_chars}")
        print(f"  Average chunk size: {total_chars / len(chunks):.1f} characters")
        print(f"  Largest chunk: {max(chunk_sizes)} characters")
        print(f"  Smallest chunk: {min(chunk_sizes)} characters")
        print()
        
        # Step 5: Verify chunking quality
        print("🔍 Step 5: Chunking Quality Check")
        print("-" * 30)
        
        # Check if all text was preserved
        reconstructed_text = ""
        for chunk in chunks:
            reconstructed_text += chunk['content']
        
        text_preserved = len(reconstructed_text.strip()) == len(extracted_text.strip())
        print(f"Text preservation: {'✅ Complete' if text_preserved else '❌ Incomplete'}")
        
        if not text_preserved:
            print(f"Original length: {len(extracted_text)}")
            print(f"Reconstructed length: {len(reconstructed_text)}")
            print(f"Difference: {abs(len(extracted_text) - len(reconstructed_text))} characters")
        
        # Check chunk size distribution
        oversized_chunks = [c for c in chunk_sizes if c > 1000]
        if oversized_chunks:
            print(f"⚠️  {len(oversized_chunks)} chunks exceed 1000 character limit")
        else:
            print("✅ All chunks within size limits")
        
        print()
        
        # Step 6: Display sample chunks for review
        print("📋 Step 6: Sample Chunks for Review")
        print("-" * 30)
        
        # Show first 3 chunks in detail
        for i in range(min(3, len(chunks))):
            chunk = chunks[i]
            print(f"Chunk {i+1} (Full Content):")
            print("-" * 40)
            print(chunk['content'])
            print("-" * 40)
            print()
        
        if len(chunks) > 3:
            print(f"... and {len(chunks) - 3} more chunks")
        
        print("🎉 DOCX parsing and chunking test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking Dependencies")
    print("-" * 20)
    
    try:
        from docx import Document
        print("✅ python-docx: Available")
    except ImportError:
        print("❌ python-docx: Not available")
        print("   Install with: pip install python-docx")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy: Available")
    except ImportError:
        print("❌ SQLAlchemy: Not available")
        print("   Install with: pip install sqlalchemy")
        return False
    
    print()
    return True

if __name__ == "__main__":
    print("🚀 Starting DOCX Parsing and Chunking Test")
    print("=" * 60)
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Missing required dependencies. Please install them first.")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_docx_parsing_and_chunking())
