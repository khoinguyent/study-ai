#!/usr/bin/env python3
"""
Script to check actual document content in the database
"""

import asyncio
import httpx
import json
import os
from typing import List, Dict, Any

# Document IDs provided by user
DOCUMENT_IDS = [
    "c84fdfad-da6d-4cc6-80f6-9ad18c5ff993",
    "c43478f7-f08a-4de1-a5e1-d2a71c42ec51", 
    "7313ca17-9cdd-4510-8dd7-6ef93e079a89",
    "9aced301-214d-4060-806c-235580034bef"
]

# Service URLs
DOCUMENT_SERVICE_URL = os.getenv('DOCUMENT_SERVICE_URL', 'http://document-service:8002')
INDEXING_SERVICE_URL = os.getenv('INDEXING_SERVICE_URL', 'http://indexing-service:8003')

async def check_document_details():
    """Check document details from document service"""
    print("🔍 CHECKING DOCUMENT DETAILS")
    print("=" * 60)
    
    for doc_id in DOCUMENT_IDS:
        print(f"\n📄 Document: {doc_id}")
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Check document details
                url = f"{DOCUMENT_SERVICE_URL}/documents/{doc_id}"
                print(f"🔍 Checking document details: {url}")
                
                resp = await client.get(url)
                print(f"📊 Response status: {resp.status_code}")
                
                if resp.status_code == 200:
                    doc_data = resp.json()
                    print(f"✅ Document found:")
                    print(f"   Filename: {doc_data.get('filename', 'N/A')}")
                    print(f"   Content Type: {doc_data.get('content_type', 'N/A')}")
                    print(f"   Status: {doc_data.get('status', 'N/A')}")
                    print(f"   File Size: {doc_data.get('file_size', 'N/A')}")
                    print(f"   File Path: {doc_data.get('file_path', 'N/A')}")
                    print(f"   Subject ID: {doc_data.get('subject_id', 'N/A')}")
                    print(f"   Category ID: {doc_data.get('category_id', 'N/A')}")
                    print(f"   Created At: {doc_data.get('created_at', 'N/A')}")
                    print(f"   Updated At: {doc_data.get('updated_at', 'N/A')}")
                else:
                    print(f"❌ Failed to get document details: {resp.status_code}")
                    print(f"   Response: {resp.text}")
                    
        except Exception as e:
            print(f"❌ Error checking document details: {str(e)}")

async def check_indexing_service_chunks():
    """Check chunks from indexing service"""
    print("\n🔍 CHECKING INDEXING SERVICE CHUNKS")
    print("=" * 60)
    
    for doc_id in DOCUMENT_IDS:
        print(f"\n📄 Document: {doc_id}")
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                url = f"{INDEXING_SERVICE_URL}/chunks/{doc_id}"
                print(f"🔍 Fetching chunks: {url}")
                
                resp = await client.get(url)
                print(f"📊 Response status: {resp.status_code}")
                
                if resp.status_code == 200:
                    chunks = resp.json() or []
                    print(f"✅ Found {len(chunks)} chunks")
                    
                    # Analyze chunk content
                    real_chunks = 0
                    placeholder_chunks = 0
                    total_content = ""
                    
                    for i, chunk in enumerate(chunks):
                        content = chunk.get("content", "")
                        total_content += content + " "
                        
                        if "placeholder" in content.lower():
                            placeholder_chunks += 1
                        else:
                            real_chunks += 1
                    
                    print(f"📊 Chunk Analysis:")
                    print(f"   Real content chunks: {real_chunks}")
                    print(f"   Placeholder chunks: {placeholder_chunks}")
                    print(f"   Total content length: {len(total_content)} characters")
                    
                    # Show sample of real content
                    if real_chunks > 0:
                        print(f"\n📖 Sample real content:")
                        for i, chunk in enumerate(chunks[:3]):
                            content = chunk.get("content", "")
                            if "placeholder" not in content.lower() and len(content.strip()) > 10:
                                print(f"   Chunk {i+1}: {content[:200]}...")
                                break
                    else:
                        print("❌ No real content found in chunks!")
                        
                else:
                    print(f"❌ Failed to fetch chunks: {resp.status_code}")
                    print(f"   Response: {resp.text}")
                    
        except Exception as e:
            print(f"❌ Error checking chunks: {str(e)}")

async def test_quiz_generation_with_real_content():
    """Test quiz generation with the actual content"""
    print("\n🎯 TESTING QUIZ GENERATION WITH REAL CONTENT")
    print("=" * 60)
    
    # Get chunks from indexing service
    all_chunks = []
    for doc_id in DOCUMENT_IDS:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                url = f"{INDEXING_SERVICE_URL}/chunks/{doc_id}"
                resp = await client.get(url)
                
                if resp.status_code == 200:
                    chunks = resp.json() or []
                    # Filter out placeholder chunks
                    real_chunks = []
                    for chunk in chunks:
                        content = chunk.get("content", "")
                        if "placeholder" not in content.lower() and len(content.strip()) > 10:
                            real_chunks.append(chunk)
                    
                    all_chunks.extend(real_chunks)
                    print(f"📄 Document {doc_id}: {len(real_chunks)} real chunks out of {len(chunks)} total")
                else:
                    print(f"❌ Failed to get chunks for {doc_id}: {resp.status_code}")
                    
        except Exception as e:
            print(f"❌ Error getting chunks for {doc_id}: {str(e)}")
    
    print(f"\n📊 Total real chunks found: {len(all_chunks)}")
    
    if all_chunks:
        print("\n📖 REAL CONTENT BEING USED FOR QUIZ GENERATION:")
        print("-" * 60)
        
        # Show the actual content that would be used
        for i, chunk in enumerate(all_chunks[:5]):  # Show first 5 chunks
            content = chunk.get("content", "")
            print(f"\n   Chunk {i+1}:")
            print(f"   Length: {len(content)} characters")
            print(f"   Content: {content[:300]}...")
            print(f"   Metadata: {chunk.get('metadata', {})}")
        
        # Test quiz generation with this content
        print(f"\n🎯 Testing quiz generation with {len(all_chunks)} real chunks...")
        
        # Prepare context chunks (same format as quiz service)
        context_chunks = []
        for chunk in all_chunks:
            context_chunks.append({
                "content": chunk.get("content", ""),
                "metadata": {
                    "document_id": chunk.get("document_id", "unknown"),
                    "chunk_index": chunk.get("chunk_index")
                }
            })
        
        # Show what would be sent to the quiz generator
        total_chars = sum(len(chunk["content"]) for chunk in context_chunks)
        print(f"📏 Total characters to be sent to quiz generator: {total_chars}")
        
        if total_chars > 0:
            print("✅ Real content is available for quiz generation!")
            print("   The issue might be in the quiz generation logic or AI model.")
        else:
            print("❌ No real content available for quiz generation!")
            print("   This explains why the quiz questions are not related to documents.")
    else:
        print("❌ No real chunks found! This explains the issue.")

if __name__ == "__main__":
    print("🔍 Document Content Analysis Tool")
    print("=" * 60)
    
    asyncio.run(check_document_details())
    asyncio.run(check_indexing_service_chunks())
    asyncio.run(test_quiz_generation_with_real_content())
