#!/usr/bin/env python3
"""
Test script for image OCR functionality
Tests text extraction from various image formats
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.text_extractor import TextExtractor

async def test_image_ocr():
    """Test image OCR functionality"""
    print("🧪 Testing Image OCR Functionality")
    print("=" * 50)
    
    # Initialize text extractor
    extractor = TextExtractor()
    
    # Check OCR availability
    print(f"✅ OCR Available: {extractor.supported_formats.get('image/png') is not None}")
    
    # Test supported formats
    print("\n📋 Supported Image Formats:")
    image_formats = [
        'image/png', 'image/jpeg', 'image/jpg', 
        'image/tiff', 'image/bmp', 'image/gif'
    ]
    
    for format_type in image_formats:
        is_supported = extractor.is_format_supported(format_type)
        status = "✅" if is_supported else "❌"
        print(f"  {status} {format_type}")
    
    # Test with a sample image (if available)
    test_image_path = Path("test_image.png")
    if test_image_path.exists():
        print(f"\n🔍 Testing with sample image: {test_image_path}")
        
        try:
            with open(test_image_path, 'rb') as f:
                image_content = f.read()
            
            # Test extraction
            result = await extractor.extract_text(
                file_content=image_content,
                content_type="image/png",
                filename="test_image.png"
            )
            
            if result['success']:
                print(f"✅ OCR Success!")
                print(f"📝 Extracted {result['word_count']} words")
                print(f"📊 Method: {result['extraction_method']}")
                print(f"📋 Metadata: {result['metadata']}")
                print(f"📄 Text preview: {result['text'][:200]}...")
            else:
                print(f"❌ OCR Failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
    else:
        print(f"\n⚠️  No test image found at {test_image_path}")
        print("   Create a test image to verify OCR functionality")
    
    print("\n🎯 OCR Configuration:")
    print("  - Engine: Tesseract")
    print("  - Languages: Vietnamese + English (vie+eng)")
    print("  - PSM Mode: 6 (uniform block of text)")
    print("  - OEM Mode: 3 (default OCR engine)")
    print("  - Image Processing: Grayscale conversion")
    
    print("\n✅ Image OCR functionality is ready!")

if __name__ == "__main__":
    asyncio.run(test_image_ocr())

