#!/usr/bin/env python3
"""
Test script for text extraction functionality
Run this to test DOC, DOCX, and enhanced PDF text extraction
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.text_extractor import TextExtractor

async def test_text_extraction():
    """Test the text extraction service"""
    print("Testing Text Extraction Service...")
    print("=" * 50)
    
    # Initialize the text extractor
    extractor = TextExtractor()
    
    # Show supported formats
    print(f"Supported formats: {extractor.get_supported_formats()}")
    print()
    
    # Test with sample text content
    sample_text = b"This is a sample text document for testing purposes.\n\nIt contains multiple paragraphs.\n\nThis should be extracted correctly."
    
    # Test plain text extraction
    print("Testing plain text extraction...")
    result = await extractor.extract_text(sample_text, "text/plain", "test.txt")
    print(f"Success: {result['success']}")
    print(f"Word count: {result['word_count']}")
    print(f"Method: {result['extraction_method']}")
    print(f"Text preview: {result['text'][:100]}...")
    print()
    
    # Test format support checking
    test_formats = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "application/msword",
        "text/markdown"
    ]
    
    print("Testing format support...")
    for format_type in test_formats:
        supported = extractor.is_format_supported(format_type)
        status = "✅ Supported" if supported else "❌ Not supported"
        print(f"{format_type}: {status}")
    
    print()
    
    # Test PDF text extraction with sample PDF-like content
    print("Testing enhanced PDF text extraction...")
    print("-" * 40)
    
    # Create a sample PDF-like text with common PDF issues
    sample_pdf_text = b"""This is a sample PDF document.

Page 1 content with some text.

--- Page 2 ---
More content on page 2.

--- Page 3 ---
Final page with additional text.

This document has multiple pages and should demonstrate the enhanced extraction capabilities."""
    
    # Test the enhanced PDF extraction
    pdf_result = await extractor.extract_pdf_with_fallback(sample_pdf_text, "sample.pdf")
    
    if pdf_result['success']:
        print(f"✅ PDF extraction successful")
        print(f"📄 Word count: {pdf_result['word_count']}")
        print(f"🔧 Method: {pdf_result['method']}")
        print(f"📊 Quality: {pdf_result['metadata']['text_quality']['quality']}")
        print(f"📈 Quality score: {pdf_result['metadata']['text_quality']['score']}")
        
        if pdf_result['metadata']['text_quality'].get('issues'):
            print(f"⚠️  Issues found:")
            for issue in pdf_result['metadata']['text_quality']['issues']:
                print(f"   - {issue}")
        
        if pdf_result['metadata'].get('recommendations'):
            print(f"💡 Recommendations:")
            for rec in pdf_result['metadata']['recommendations']:
                print(f"   - {rec['action']}: {rec['description']}")
        
        print(f"📝 Text preview: {pdf_result['text'][:150]}...")
    else:
        print(f"❌ PDF extraction failed: {pdf_result.get('error', 'Unknown error')}")
    
    print()
    
    # Test PDF quality assessment
    print("Testing PDF quality assessment...")
    print("-" * 40)
    
    # Test with poor quality text
    poor_quality_text = b"""T h i s   i s   p o o r   q u a l i t y   t e x t.

It has excessive spaces and line breaks.

This should trigger quality warnings and recommendations."""
    
    pdf_poor_result = await extractor.extract_pdf_with_fallback(poor_quality_text, "poor_quality.pdf")
    
    if pdf_poor_result['success']:
        quality = pdf_poor_result['metadata']['text_quality']
        print(f"📊 Poor quality PDF assessment:")
        print(f"   Quality: {quality['quality']}")
        print(f"   Score: {quality['score']}")
        print(f"   Issues: {len(quality.get('issues', []))}")
        
        if quality.get('issues'):
            print(f"   Issues found:")
            for issue in quality['issues']:
                print(f"     - {issue}")
        
        if pdf_poor_result['metadata'].get('recommendations'):
            print(f"   Recommendations:")
            for rec in pdf_poor_result['metadata']['recommendations']:
                print(f"     - {rec['priority'].upper()}: {rec['action']}")
                print(f"       {rec['description']}")
    else:
        print(f"❌ Poor quality PDF test failed: {pdf_poor_result.get('error', 'Unknown error')}")
    
    print()
    print("Text extraction service test completed!")

if __name__ == "__main__":
    asyncio.run(test_text_extraction())
