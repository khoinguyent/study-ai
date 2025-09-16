#!/usr/bin/env python3
"""
Test script to verify the OpenAI model upgrade from gpt-3.5-turbo to gpt-4o
"""

import os
import sys
import asyncio
import httpx
from typing import Dict, Any

# Add the quiz service to the path
sys.path.append('services/quiz-service')

async def test_model_upgrade():
    """Test the upgraded model with a simple quiz generation request"""
    
    print("🧪 Testing OpenAI Model Upgrade: gpt-3.5-turbo → gpt-4o")
    print("=" * 60)
    
    # Test data
    test_request = {
        "topic": "Vietnam History - Tay Son Rebellion",
        "difficulty": "medium",
        "num_questions": 3,
        "context_chunks": [
            {
                "content": "The Tay Son Rebellion was a peasant uprising in Vietnam that began in 1771. Led by three brothers from the Tay Son village, the rebellion successfully overthrew the ruling Le dynasty and established a new government.",
                "source": "Vietnam History Document",
                "page": 1
            }
        ],
        "source_type": "document",
        "source_id": "test-doc-1"
    }
    
    try:
        # Test the quiz service endpoint
        async with httpx.AsyncClient() as client:
            print("📡 Testing quiz generation with upgraded model...")
            
            response = await client.post(
                "http://localhost:8004/quizzes/generate",
                json=test_request,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Quiz generation successful!")
                print(f"📊 Generated {len(result.get('questions', []))} questions")
                
                # Display first question as example
                if result.get('questions'):
                    first_q = result['questions'][0]
                    print(f"\n📝 Sample Question:")
                    print(f"   Type: {first_q.get('type', 'N/A')}")
                    print(f"   Question: {first_q.get('question', 'N/A')[:100]}...")
                    print(f"   Options: {len(first_q.get('options', []))} options")
                
                print(f"\n🎯 Model used: gpt-4o (upgraded from gpt-3.5-turbo)")
                return True
                
            else:
                print(f"❌ Quiz generation failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except httpx.ConnectError:
        print("❌ Could not connect to quiz service. Make sure it's running on port 8004")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

def check_environment_config():
    """Check if environment is properly configured for the new model"""
    
    print("\n🔧 Checking Environment Configuration:")
    print("-" * 40)
    
    # Check if we can import the quiz generator
    try:
        from services.quiz_service.app.services.quiz_generator import QuizGenerator
        generator = QuizGenerator()
        
        print(f"✅ Quiz Generator initialized")
        print(f"📋 Strategy: {generator.strategy}")
        print(f"🤖 OpenAI Model: {generator.openai_model}")
        print(f"🌡️ Temperature: {generator.openai_temperature}")
        print(f"📏 Max Tokens: {generator.openai_max_tokens}")
        
        if generator.openai_model == "gpt-4o":
            print("✅ Model successfully upgraded to gpt-4o!")
            return True
        else:
            print(f"⚠️ Model is still {generator.openai_model}, not gpt-4o")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import QuizGenerator: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OpenAI Model Upgrade Verification")
    print("=" * 50)
    
    # Check environment configuration
    config_ok = check_environment_config()
    
    if config_ok:
        # Test the actual API
        result = asyncio.run(test_model_upgrade())
        
        if result:
            print("\n🎉 Model upgrade verification completed successfully!")
            print("✅ gpt-4o is now active and working for quiz generation")
        else:
            print("\n⚠️ Model upgrade verification had issues")
            print("Check the quiz service logs for more details")
    else:
        print("\n❌ Environment configuration issues detected")
        print("Please check your environment variables and service configuration")
