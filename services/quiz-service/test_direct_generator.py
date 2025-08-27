#!/usr/bin/env python3
"""
Test script for the Direct Chunks Generator
Tests the new quiz generation system without OpenAI File Search
"""

import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.generator.orchestrator import generate_from_documents
from app.llm.providers.ollama_adapter import OllamaProvider
from app.llm.providers.openai_adapter import OpenAIProvider
from app.llm.providers.hf_adapter import HFProvider


async def test_ollama_generation():
    """Test quiz generation using Ollama"""
    print("Testing Ollama generation...")
    
    # Mock session and provider
    class MockSession:
        def query(self, model):
            return MockQuery()
    
    class MockQuery:
        def filter(self, condition):
            return self
        
        def order_by(self, field):
            return self
        
        def all(self):
            # Return mock chunks
            return [
                MockChunk(1, 1, "test_doc.pdf", 1, "Introduction", 0, 100, "This is a test document about Vietnamese history."),
                MockChunk(2, 1, "test_doc.pdf", 2, "Chapter 1", 100, 200, "The Nguyen dynasty was established in 1802."),
                MockChunk(3, 1, "test_doc.pdf", 3, "Chapter 2", 200, 300, "Emperor Gia Long unified Vietnam under his rule.")
            ]
    
    class MockChunk:
        def __init__(self, id, doc_id, file_name, chunk_id, section_path, start_char, end_char, content):
            self.id = id
            self.document_id = doc_id
            self.file_name = file_name
            self.chunk_id = chunk_id
            self.section_path = section_path
            self.start_char = start_char
            self.end_char = end_char
            self.content = content
            self.text = content
    
    # Create provider
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")
    
    try:
        # Test generation
        batch, blocks, lang_code = generate_from_documents(
            session=MockSession(),
            provider=provider,
            subject_name="Vietnamese History",
            doc_ids=[1],
            total_count=3,
            allowed_types=["MCQ"],
            counts_by_type={"MCQ": 3},
            difficulty_mix={"easy": 0.4, "medium": 0.4, "hard": 0.2},
            schema_json=json.dumps({
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "stem": {"type": "string"},
                                "options": {"type": "array"},
                                "metadata": {"type": "object"}
                            }
                        }
                    }
                }
            })
        )
        
        print(f"✅ Successfully generated {len(batch.get('questions', []))} questions")
        print(f"Language detected: {lang_code}")
        print(f"Context blocks used: {len(blocks)}")
        print(f"Generation metadata: {batch.get('generation_metadata', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama generation failed: {e}")
        return False


async def test_provider_adapters():
    """Test the provider adapters"""
    print("\nTesting provider adapters...")
    
    # Test OpenAI adapter
    try:
        if os.getenv("OPENAI_API_KEY"):
            provider = OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini"
            )
            print("✅ OpenAI adapter created successfully")
        else:
            print("⚠️  OpenAI API key not found, skipping OpenAI test")
    except Exception as e:
        print(f"❌ OpenAI adapter failed: {e}")
    
    # Test Ollama adapter
    try:
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")
        print("✅ Ollama adapter created successfully")
    except Exception as e:
        print(f"❌ Ollama adapter failed: {e}")
    
    # Test HF adapter
    try:
        if os.getenv("HF_API_KEY"):
            provider = HFProvider(model_id="microsoft/DialoGPT-medium")
            print("✅ HuggingFace adapter created successfully")
        else:
            print("⚠️  HuggingFace API key not found, skipping HF test")
    except Exception as e:
        print(f"❌ HuggingFace adapter failed: {e}")


async def main():
    """Main test function"""
    print("🧪 Testing Direct Chunks Generator Implementation")
    print("=" * 50)
    
    # Test provider adapters
    await test_provider_adapters()
    
    # Test Ollama generation (if available)
    print("\n" + "=" * 50)
    await test_ollama_generation()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())
