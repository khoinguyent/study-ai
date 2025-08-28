#!/usr/bin/env python3
"""
Test script to verify the quiz service API endpoints work correctly.
This script tests the various endpoints to ensure they respond properly.
"""

import asyncio
import aiohttp
import json
import sys

# Quiz service base URL
BASE_URL = "http://localhost:8004"

async def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def test_openai_config():
    """Test the OpenAI configuration endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/test-openai") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ OpenAI config test: {data}")
                    return True
                else:
                    print(f"❌ OpenAI config test failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ OpenAI config test error: {e}")
        return False

async def test_ollama_config():
    """Test the Ollama configuration endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/test-ollama") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Ollama config test: {data}")
                    return True
                else:
                    print(f"❌ Ollama config test failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ollama config test error: {e}")
        return False

async def test_quiz_generation():
    """Test the quiz generation endpoint"""
    try:
        payload = {
            "docIds": ["test-doc-1"],
            "numQuestions": 3,
            "difficulty": "easy",
            "questionTypes": ["MCQ"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/quizzes/generate-simple",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Quiz generation test: {data}")
                    return True
                else:
                    print(f"❌ Quiz generation test failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Quiz generation test error: {e}")
        return False

async def test_real_quiz_generation():
    """Test the real quiz generation endpoint"""
    try:
        payload = {
            "docIds": ["test-doc-1"],
            "numQuestions": 2,
            "difficulty": "easy",
            "questionTypes": ["MCQ"],
            "topic": "Test Topic"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/test-quiz-generation",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Real quiz generation test: {data}")
                    return True
                else:
                    print(f"❌ Real quiz generation test failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Real quiz generation test error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Quiz Service API Endpoint Tests\n")
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("OpenAI Config", test_openai_config),
        ("Ollama Config", test_ollama_config),
        ("Mock Quiz Generation", test_quiz_generation),
        ("Real Quiz Generation", test_real_quiz_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results:")
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   - {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All API endpoint tests passed!")
    else:
        print("\n⚠️  Some API endpoint tests failed.")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
