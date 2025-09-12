#!/usr/bin/env python3
"""
Test script for image OCR API endpoint
Tests the /extract-image-text endpoint
"""

import asyncio
import httpx
import sys
import os
from pathlib import Path

async def test_image_api():
    """Test image OCR API endpoint"""
    print("🧪 Testing Image OCR API Endpoint")
    print("=" * 50)
    
    # API configuration
    base_url = "http://localhost:8002"
    endpoint = "/extract-image-text"
    
    # Test image path
    test_image_path = Path("test_image.png")
    
    if not test_image_path.exists():
        print(f"❌ Test image not found at {test_image_path}")
        print("   Please create a test image to verify the API")
        return
    
    print(f"🔍 Testing with image: {test_image_path}")
    
    try:
        # Prepare the file upload
        with open(test_image_path, 'rb') as f:
            files = {'file': (test_image_path.name, f, 'image/png')}
            
            # Make the API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}{endpoint}",
                    files=files,
                    headers={'Authorization': 'Bearer test-token'}  # Mock token for testing
                )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Success!")
            print(f"📝 Filename: {result.get('filename')}")
            print(f"📋 Content Type: {result.get('content_type')}")
            
            extraction = result.get('extraction_result', {})
            print(f"📊 Success: {extraction.get('success')}")
            print(f"📝 Word Count: {extraction.get('word_count', 0)}")
            print(f"🔧 Method: {extraction.get('extraction_method', 'unknown')}")
            
            # Show metadata
            metadata = extraction.get('metadata', {})
            print(f"📋 Image Format: {metadata.get('image_format')}")
            print(f"📏 Image Size: {metadata.get('image_size')}")
            print(f"🎯 OCR Engine: {metadata.get('ocr_engine')}")
            print(f"🌐 Languages: {metadata.get('ocr_languages')}")
            
            # Show text preview
            text = extraction.get('text', '')
            if text:
                print(f"📄 Text Preview: {text[:200]}...")
            else:
                print("📄 No text extracted")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    
    print("\n🎯 API Endpoints Available:")
    print(f"  - POST {base_url}/extract-image-text")
    print(f"  - GET {base_url}/supported-formats")
    print(f"  - GET {base_url}/health")

if __name__ == "__main__":
    asyncio.run(test_image_api())

