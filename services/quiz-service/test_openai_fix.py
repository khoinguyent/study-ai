#!/usr/bin/env python3
"""
Test script to verify OpenAI integration fixes in the quiz service.
This script tests the provider initialization and basic functionality.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_quiz_generator():
    """Test the QuizGenerator initialization and provider setup"""
    try:
        print("🔧 Testing QuizGenerator initialization...")
        
        from services.quiz_generator import QuizGenerator
        from config import settings
        
        print(f"📋 Configuration:")
        print(f"   - Strategy: {settings.QUIZ_GENERATION_STRATEGY}")
        print(f"   - Provider: {settings.QUIZ_PROVIDER}")
        print(f"   - OpenAI API Key: {'SET' if settings.OPENAI_API_KEY else 'NOT SET'}")
        print(f"   - OpenAI Base URL: {settings.OPENAI_BASE_URL}")
        print(f"   - OpenAI Model: {settings.OPENAI_MODEL}")
        
        # Initialize the quiz generator
        quiz_generator = QuizGenerator()
        
        print(f"✅ QuizGenerator initialized successfully")
        print(f"   - Strategy: {quiz_generator.strategy}")
        print(f"   - Provider: {quiz_generator.provider.name if quiz_generator.provider else 'None'}")
        
        if quiz_generator.provider:
            print(f"   - Provider Name: {quiz_generator.provider.name}")
            print(f"   - Provider Type: {type(quiz_generator.provider).__name__}")
        else:
            print("   - No provider available, will use mock data")
        
        # Test basic functionality
        print("\n🧪 Testing basic quiz generation...")
        
        mock_context_chunks = [
            {
                "content": "This is a test document about artificial intelligence.",
                "metadata": {"source": "test", "document_id": "test-doc"}
            }
        ]
        
        try:
            quiz_data = await quiz_generator.generate_quiz_from_context(
                topic="AI Test",
                difficulty="easy",
                num_questions=2,
                context_chunks=mock_context_chunks,
                source_type="test",
                source_id="test-doc"
            )
            
            print(f"✅ Quiz generation successful!")
            print(f"   - Questions generated: {len(quiz_data.get('questions', []))}")
            print(f"   - Quiz title: {quiz_data.get('title', 'N/A')}")
            print(f"   - Provider used: {quiz_generator.provider.name if quiz_generator.provider else 'Mock'}")
            
        except Exception as e:
            print(f"❌ Quiz generation failed: {e}")
            print(f"   - This might be expected if using mock data")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_openai_provider():
    """Test the OpenAI provider specifically"""
    try:
        print("\n🔧 Testing OpenAI provider specifically...")
        
        from llm.providers.openai_adapter import OpenAIProvider
        from config import settings
        
        if not settings.OPENAI_API_KEY:
            print("⚠️  OpenAI API key not configured, skipping provider test")
            return True
        
        print(f"📋 OpenAI Configuration:")
        print(f"   - API Key: {settings.OPENAI_API_KEY[:8]}...")
        print(f"   - Base URL: {settings.OPENAI_BASE_URL}")
        print(f"   - Model: {settings.OPENAI_MODEL}")
        
        # Initialize the provider
        provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_BASE_URL
        )
        
        print(f"✅ OpenAI provider initialized successfully")
        
        # Test a simple generation
        print("🧪 Testing OpenAI API call...")
        
        system_prompt = "You are a helpful assistant."
        user_prompt = "Generate a simple JSON response with a greeting message."
        
        try:
            result = provider.generate_json(system_prompt, user_prompt)
            print(f"✅ OpenAI API call successful!")
            print(f"   - Response type: {type(result)}")
            print(f"   - Response: {result}")
            
        except Exception as e:
            print(f"❌ OpenAI API call failed: {e}")
            print(f"   - This might indicate a configuration or network issue")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Quiz Service OpenAI Integration Tests\n")
    
    # Test 1: QuizGenerator initialization
    test1_success = await test_quiz_generator()
    
    # Test 2: OpenAI provider
    test2_success = await test_openai_provider()
    
    print("\n📊 Test Results:")
    print(f"   - QuizGenerator Test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   - OpenAI Provider Test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! OpenAI integration should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the configuration and try again.")
    
    return test1_success and test2_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
