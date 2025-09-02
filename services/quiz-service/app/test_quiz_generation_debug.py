#!/usr/bin/env python3
"""
Debug script to trace quiz generation flow with specific document IDs
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
INDEXING_SERVICE_URL = os.getenv('INDEXING_SERVICE_URL', 'http://indexing-service:8003')
QUIZ_SERVICE_URL = os.getenv('QUIZ_SERVICE_URL', 'http://localhost:8004')

async def fetch_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    """Fetch chunks for a specific document"""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            url = f"{INDEXING_SERVICE_URL}/chunks/{document_id}"
            print(f"🔍 Fetching chunks from: {url}")
            
            resp = await client.get(url)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json() or []
                print(f"✅ Found {len(data)} chunks for document {document_id}")
                
                # Show chunk previews
                for i, chunk in enumerate(data[:3]):  # Show first 3 chunks
                    content = chunk.get("content", "")
                    print(f"   Chunk {i+1}: {content[:100]}...")
                
                return data
            else:
                print(f"❌ Failed to fetch chunks for {document_id}: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return []
                
    except Exception as e:
        print(f"❌ Error fetching chunks for {document_id}: {str(e)}")
        return []

async def test_quiz_generation():
    """Test the complete quiz generation flow"""
    print("🚀 Starting quiz generation debug test")
    print("=" * 60)
    
    # Step 1: Fetch chunks for all documents
    print("\n📚 STEP 1: Fetching document chunks")
    print("-" * 40)
    
    all_chunks = []
    for doc_id in DOCUMENT_IDS:
        print(f"\n📄 Document: {doc_id}")
        chunks = await fetch_document_chunks(doc_id)
        all_chunks.extend(chunks)
    
    print(f"\n📊 Total chunks found: {len(all_chunks)}")
    
    if not all_chunks:
        print("❌ No chunks found! This explains why the quiz is not related to documents.")
        return
    
    # Step 2: Prepare context chunks (same as quiz service)
    print("\n🔧 STEP 2: Preparing context chunks")
    print("-" * 40)
    
    context_chunks = []
    for ch in all_chunks:
        context_chunks.append({
            "content": ch.get("content", ""),
            "metadata": {
                "document_id": ch.get("document_id", "unknown"),
                "chunk_index": ch.get("chunk_index")
            }
        })
    
    print(f"📝 Prepared {len(context_chunks)} context chunks")
    
    # Step 3: Show context content
    print("\n📖 STEP 3: Context content preview")
    print("-" * 40)
    
    total_chars = sum(len(chunk["content"]) for chunk in context_chunks)
    print(f"📏 Total characters: {total_chars}")
    
    # Show first few chunks
    for i, chunk in enumerate(context_chunks[:3]):
        content = chunk["content"]
        print(f"\n📄 Context Chunk {i+1}:")
        print(f"   Length: {len(content)} characters")
        print(f"   Content: {content[:200]}...")
        print(f"   Metadata: {chunk['metadata']}")
    
    # Step 4: Test quiz generation API with authentication
    print("\n🎯 STEP 4: Testing quiz generation API")
    print("-" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            # Prepare request payload
            payload = {
                "topic": "Document-based Quiz",
                "difficulty": "medium",
                "num_questions": 4,
                "document_ids": DOCUMENT_IDS
            }
            
            # Add authentication header (mock token for testing)
            headers = {
                "Authorization": "Bearer test_token_for_debug",
                "Content-Type": "application/json"
            }
            
            print(f"🌐 Making request to: {url}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            print(f"🔐 Headers: {json.dumps(headers, indent=2)}")
            
            resp = await client.post(url, json=payload, headers=headers)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                quiz_data = resp.json()
                print("✅ Quiz generation successful!")
                print(f"📋 Quiz data: {json.dumps(quiz_data, indent=2)}")
                
                # Analyze questions
                questions = quiz_data.get('questions', [])
                print(f"\n❓ Generated {len(questions)} questions:")
                
                for i, q in enumerate(questions):
                    stem = q.get('stem', '')
                    options = q.get('options', [])
                    correct = q.get('correct_option', -1)
                    
                    print(f"\n   Question {i+1}: {stem}")
                    for j, opt in enumerate(options):
                        marker = "✓" if j == correct else " "
                        print(f"     {marker} {j}. {opt}")
                        
            else:
                print(f"❌ Quiz generation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing quiz generation: {str(e)}")

async def test_direct_chunk_analysis():
    """Analyze chunks directly to understand content"""
    print("\n🔍 DIRECT CHUNK ANALYSIS")
    print("=" * 60)
    
    for doc_id in DOCUMENT_IDS:
        print(f"\n📄 Analyzing document: {doc_id}")
        chunks = await fetch_document_chunks(doc_id)
        
        if chunks:
            print(f"   Found {len(chunks)} chunks")
            
            # Analyze content
            total_content = ""
            for chunk in chunks:
                content = chunk.get("content", "")
                total_content += content + " "
            
            print(f"   Total content length: {len(total_content)} characters")
            print(f"   Content preview: {total_content[:300]}...")
            
            # Check for specific keywords
            keywords = ["vietnam", "history", "war", "dynasty", "nguyen", "tay son"]
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in total_content.lower():
                    found_keywords.append(keyword)
            
            print(f"   Found keywords: {found_keywords}")
        else:
            print("   ❌ No chunks found")

async def test_quiz_generator_directly():
    """Test the quiz generator directly with the chunks"""
    print("\n🤖 DIRECT QUIZ GENERATOR TEST")
    print("=" * 60)
    
    # Fetch chunks
    all_chunks = []
    for doc_id in DOCUMENT_IDS:
        chunks = await fetch_document_chunks(doc_id)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("❌ No chunks found for direct testing")
        return
    
    # Prepare context chunks
    context_chunks = []
    for ch in all_chunks:
        context_chunks.append({
            "content": ch.get("content", ""),
            "metadata": {
                "document_id": ch.get("document_id", "unknown"),
                "chunk_index": ch.get("chunk_index")
            }
        })
    
    print(f"📝 Using {len(context_chunks)} context chunks for direct testing")
    
    # Show the actual content being used
    print("\n📖 ACTUAL CONTENT BEING USED FOR QUIZ GENERATION:")
    print("-" * 60)
    
    # Filter out placeholder content and show real content
    real_chunks = []
    for chunk in context_chunks:
        content = chunk["content"]
        if "placeholder" not in content.lower() and len(content.strip()) > 10:
            real_chunks.append(chunk)
    
    print(f"📊 Found {len(real_chunks)} chunks with real content (excluding placeholders)")
    
    if real_chunks:
        print("\n📄 REAL CONTENT CHUNKS:")
        for i, chunk in enumerate(real_chunks[:5]):  # Show first 5 real chunks
            content = chunk["content"]
            print(f"\n   Chunk {i+1}:")
            print(f"   Length: {len(content)} characters")
            print(f"   Content: {content[:300]}...")
            print(f"   Metadata: {chunk['metadata']}")
    else:
        print("❌ No real content found! All chunks are placeholders.")
        print("   This explains why the quiz questions are not related to the documents.")

if __name__ == "__main__":
    print("🔍 Quiz Generation Debug Tool")
    print("=" * 60)
    
    asyncio.run(test_quiz_generation())
    asyncio.run(test_direct_chunk_analysis())
    asyncio.run(test_quiz_generator_directly())
