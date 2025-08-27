#!/usr/bin/env python3
"""
Test script to verify Docker build dependencies
Tests that all imports work correctly
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports for Docker build...")
    
    try:
        # Test basic imports
        print("✅ Testing basic imports...")
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        import pydantic
        import jinja2
        import requests
        import httpx
        import redis
        import celery
        import openai
        import numpy
        import pandas
        
        print("✅ Basic imports successful")
        
        # Test app imports
        print("✅ Testing app imports...")
        from app.config import settings
        from app.database import get_db
        from app.models import Quiz, CustomDocumentSet
        from app.schemas import QuizCreate
        
        print("✅ App imports successful")
        
        # Test new generator imports
        print("✅ Testing generator imports...")
        from app.generator.orchestrator import generate_from_documents
        from app.generator.context_builder import fetch_chunks_for_docs
        from app.generator.validators import validate_batch
        
        print("✅ Generator imports successful")
        
        # Test LLM provider imports
        print("✅ Testing LLM provider imports...")
        from app.llm.providers.base import LLMProvider
        from app.llm.providers.ollama_adapter import OllamaProvider
        from app.llm.providers.openai_adapter import OpenAIProvider
        from app.llm.providers.hf_adapter import HFProvider
        
        print("✅ LLM provider imports successful")
        
        # Test language detection
        print("✅ Testing language detection...")
        from app.lang.detect import detect_language_distribution
        
        print("✅ Language detection import successful")
        
        print("\n🎉 All imports successful! Docker build should work.")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_language_detection():
    """Test language detection functionality"""
    print("\n🧪 Testing language detection...")
    
    try:
        from app.lang.detect import detect_language_distribution
        
        # Test with sample text
        sample_texts = [
            "This is English text for testing.",
            "Ceci est du texte français pour les tests.",
            "Dies ist deutscher Text zum Testen."
        ]
        
        lang_code, confidence, distribution = detect_language_distribution(sample_texts)
        print(f"✅ Language detection working: {lang_code} (confidence: {confidence:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ Language detection failed: {e}")
        return False

def test_provider_creation():
    """Test LLM provider creation"""
    print("\n🧪 Testing LLM provider creation...")
    
    try:
        from app.llm.providers.ollama_adapter import OllamaProvider
        from app.llm.providers.openai_adapter import OpenAIProvider
        from app.llm.providers.hf_adapter import HFProvider
        
        # Test Ollama provider
        ollama_provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")
        print(f"✅ Ollama provider created: {ollama_provider.name}")
        
        # Test OpenAI provider (if API key available)
        if os.getenv("OPENAI_API_KEY"):
            openai_provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
            print(f"✅ OpenAI provider created: {openai_provider.name}")
        else:
            print("⚠️  OpenAI API key not found, skipping OpenAI test")
        
        # Test HF provider (if API key available)
        if os.getenv("HF_API_KEY"):
            hf_provider = HFProvider(model_id="microsoft/DialoGPT-medium")
            print(f"✅ HuggingFace provider created: {hf_provider.name}")
        else:
            print("⚠️  HuggingFace API key not found, skipping HF test")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider creation failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Docker Build Dependency Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test language detection
        lang_ok = test_language_detection()
        
        # Test provider creation
        provider_ok = test_provider_creation()
        
        print("\n" + "=" * 50)
        if imports_ok and lang_ok and provider_ok:
            print("🎉 All tests passed! Ready for Docker build.")
            return 0
        else:
            print("❌ Some tests failed. Check dependencies.")
            return 1
    else:
        print("❌ Import tests failed. Cannot proceed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
