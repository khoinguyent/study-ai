#!/usr/bin/env python3
"""
Script to test the actual quiz generation prompt with real content
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

async def test_quiz_prompt():
    """Test the actual quiz generation prompt with real content"""
    print("🔍 TESTING QUIZ GENERATION PROMPT")
    print("=" * 60)
    
    # Get all chunks from indexing service
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
                    print(f"📄 Document {doc_id}: {len(real_chunks)} real chunks")
                else:
                    print(f"❌ Failed to get chunks for {doc_id}: {resp.status_code}")
                    
        except Exception as e:
            print(f"❌ Error getting chunks for {doc_id}: {str(e)}")
    
    print(f"\n📊 Total real chunks available: {len(all_chunks)}")
    
    if all_chunks:
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
        
        # Simulate the quiz generation prompt (same as quiz service)
        print("\n🎯 SIMULATING QUIZ GENERATION PROMPT")
        print("-" * 60)
        
        # This is the EXACT logic from the quiz service
        context_text = "\n\n".join([f"Context {i+1}: {chunk.get('content', '')}" for i, chunk in enumerate(context_chunks[:3])])  # Limit to first 3 chunks
        
        print(f"📏 Context chunks used: {len(context_chunks[:3])} out of {len(context_chunks)} available")
        print(f"📏 Context text length: {len(context_text)} characters")
        print(f"📏 Total available content: {sum(len(chunk['content']) for chunk in context_chunks)} characters")
        print(f"📊 Content utilization: {len(context_text)} / {sum(len(chunk['content']) for chunk in context_chunks)} = {len(context_text) / sum(len(chunk['content']) for chunk in context_chunks) * 100:.1f}%")
        
        print(f"\n📖 ACTUAL CONTEXT BEING SENT TO AI MODEL:")
        print("=" * 60)
        print(context_text)
        
        print(f"\n🎯 USER PROMPT THAT WOULD BE SENT:")
        print("=" * 60)
        user_prompt = f"""Generate 4 medium difficulty questions based on this context:

{context_text}

Create questions that test understanding of the key concepts in the context. Ensure the questions are clear, relevant, and have one correct answer."""
        print(user_prompt)
        
        # Show what content is being missed
        print(f"\n❌ MISSED CONTENT (chunks 4-{len(context_chunks)}):")
        print("-" * 60)
        missed_chunks = context_chunks[3:8]  # Show chunks 4-8 as examples
        for i, chunk in enumerate(missed_chunks):
            content = chunk["content"]
            print(f"\n   Chunk {i+4}:")
            print(f"   Length: {len(content)} characters")
            print(f"   Content: {content[:200]}...")
        
        print(f"\n🔍 ANALYSIS:")
        print("-" * 60)
        print(f"✅ Available content: {len(context_chunks)} chunks with {sum(len(chunk['content']) for chunk in context_chunks)} characters")
        print(f"❌ Used content: {len(context_chunks[:3])} chunks with {len(context_text)} characters")
        print(f"❌ Missed content: {len(context_chunks[3:])} chunks with {sum(len(chunk['content']) for chunk in context_chunks[3:])} characters")
        print(f"❌ Content utilization: {len(context_text) / sum(len(chunk['content']) for chunk in context_chunks) * 100:.1f}%")
        print(f"\n💡 SOLUTION: The quiz generator should use more chunks or all available chunks instead of limiting to 3.")
        
    else:
        print("❌ No real chunks found!")

async def test_improved_prompt():
    """Test an improved prompt that uses more content"""
    print("\n🔧 TESTING IMPROVED PROMPT")
    print("=" * 60)
    
    # Get all chunks from indexing service
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
                    
        except Exception as e:
            print(f"❌ Error getting chunks for {doc_id}: {str(e)}")
    
    if all_chunks:
        # Prepare context chunks
        context_chunks = []
        for chunk in all_chunks:
            context_chunks.append({
                "content": chunk.get("content", ""),
                "metadata": {
                    "document_id": chunk.get("document_id", "unknown"),
                    "chunk_index": chunk.get("chunk_index")
                }
            })
        
        # Improved approach: use more chunks or all chunks
        print(f"📊 Total real chunks available: {len(context_chunks)}")
        
        # Option 1: Use first 10 chunks instead of 3
        context_text_10 = "\n\n".join([f"Context {i+1}: {chunk.get('content', '')}" for i, chunk in enumerate(context_chunks[:10])])
        
        # Option 2: Use all chunks (but limit total length to avoid token limits)
        total_chars = sum(len(chunk["content"]) for chunk in context_chunks)
        max_chars = 50000  # Conservative limit
        
        if total_chars <= max_chars:
            context_text_all = "\n\n".join([f"Context {i+1}: {chunk.get('content', '')}" for i, chunk in enumerate(context_chunks)])
        else:
            # Use as many chunks as possible within the limit
            used_chunks = []
            current_chars = 0
            for i, chunk in enumerate(context_chunks):
                if current_chars + len(chunk["content"]) <= max_chars:
                    used_chunks.append(chunk)
                    current_chars += len(chunk["content"])
                else:
                    break
            context_text_all = "\n\n".join([f"Context {i+1}: {chunk.get('content', '')}" for i, chunk in enumerate(used_chunks)])
        
        print(f"\n📊 COMPARISON OF APPROACHES:")
        print("-" * 60)
        print(f"Current approach (3 chunks): {len(context_chunks[:3])} chunks, {sum(len(chunk['content']) for chunk in context_chunks[:3])} characters")
        print(f"Improved approach (10 chunks): {len(context_chunks[:10])} chunks, {sum(len(chunk['content']) for chunk in context_chunks[:10])} characters")
        print(f"Best approach (all chunks): {len(context_chunks)} chunks, {sum(len(chunk['content']) for chunk in context_chunks)} characters")
        
        print(f"\n💡 RECOMMENDED FIX:")
        print("-" * 60)
        print("1. Change the quiz generator to use more chunks (at least 10-15)")
        print("2. Or use all chunks with a reasonable character limit (50,000 chars)")
        print("3. This will provide much more context for generating relevant questions")

if __name__ == "__main__":
    print("🔍 Quiz Prompt Debug Tool")
    print("=" * 60)
    
    asyncio.run(test_quiz_prompt())
    asyncio.run(test_improved_prompt())
