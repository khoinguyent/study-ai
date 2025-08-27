#!/usr/bin/env python3
"""
Test script for real PDF file processing
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.text_extractor import TextExtractor

def test_real_pdf():
    """Test the text extraction service with the actual PDF file"""
    print("Testing Real PDF File Processing...")
    print("=" * 50)
    
    # Initialize the text extractor
    extractor = TextExtractor()
    
    # Path to the actual PDF file
    pdf_path = "../../data/de-cuong-on-tap-hoc-ki-1-mon-lich-su-lop-8.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"PDF file size: {len(pdf_content)} bytes")
        print(f"PDF file path: {pdf_path}")
        
        # Test PDF text extraction
        print("\nTesting PDF text extraction...")
        result = extractor.extract_pdf_with_fallback(pdf_content, "de-cuong-on-tap-hoc-ki-1-mon-lich-su-lop-8.pdf")
        
        if result['success']:
            print("✅ PDF processing successful!")
            print(f"Text length: {len(result['text'])} characters")
            print(f"Word count: {result['word_count']}")
            print(f"Method: {result['method']}")
            print(f"Pages: {result['metadata']['page_count']}")
            print(f"Pages with content: {result['metadata']['pages_with_content']}")
            
            # Show text preview
            text_preview = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
            print(f"\nText preview:\n{text_preview}")
            
            # Show quality assessment
            if 'text_quality' in result['metadata']:
                quality = result['metadata']['text_quality']
                print(f"\nText quality: {quality['quality']}")
                print(f"Score: {quality['score']}/100")
                
                if 'issues' in quality and quality['issues']:
                    print("\nIssues found:")
                    for issue in quality['issues']:
                        print(f"- {issue}")
            
            # Show recommendations if any
            if result['metadata'].get('recommendations'):
                print("\nRecommendations:")
                for rec in result['metadata']['recommendations']:
                    print(f"- {rec['action']}: {rec['description']}")
                    
        else:
            print("❌ PDF processing failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            if 'metadata' in result and 'recommendations' in result['metadata']:
                print("\nRecommendations:")
                for rec in result['metadata']['recommendations']:
                    print(f"- {rec['action']}: {rec['description']}")
    
    except Exception as e:
        print(f"❌ Error during PDF processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_pdf()
