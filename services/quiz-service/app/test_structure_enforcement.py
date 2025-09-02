#!/usr/bin/env python3
"""
Test script to verify structure enforcement works across all LLM providers
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
QUIZ_SERVICE_URL = os.getenv('QUIZ_SERVICE_URL', 'http://localhost:8004')

async def test_structure_enforcement():
    """Test that all LLM providers return questions in the correct structure"""
    print("🔧 TESTING STRUCTURE ENFORCEMENT")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            # Test with different topics to ensure consistency
            test_cases = [
                {
                    "topic": "Vietnam History - Tay Son Rebellion",
                    "difficulty": "medium",
                    "numQuestions": 3,
                    "docIds": DOCUMENT_IDS
                },
                {
                    "topic": "Nguyen Dynasty Establishment",
                    "difficulty": "easy",
                    "numQuestions": 2,
                    "docIds": DOCUMENT_IDS
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                print(f"\n📚 Test Case {i+1}: {test_case['topic']}")
                print("-" * 50)
                
                headers = {
                    "Authorization": "Bearer test_token_for_debug",
                    "Content-Type": "application/json"
                }
                
                resp = await client.post(url, json=test_case, headers=headers)
                print(f"📊 Response status: {resp.status_code}")
                
                if resp.status_code == 200:
                    quiz_data = resp.json()
                    quiz = quiz_data.get('quiz', {})
                    questions = quiz.get('questions', [])
                    
                    print(f"✅ Generated {len(questions)} questions")
                    
                    # Validate structure for each question
                    valid_structure = True
                    for j, question in enumerate(questions):
                        print(f"\n   📝 Question {j+1}:")
                        print(f"      Stem: {question.get('stem', 'N/A')[:80]}...")
                        
                        # Check required fields
                        required_fields = ["stem", "options", "correct_option", "metadata"]
                        missing_fields = [field for field in required_fields if field not in question]
                        
                        if missing_fields:
                            print(f"      ❌ Missing fields: {missing_fields}")
                            valid_structure = False
                        else:
                            print(f"      ✅ All required fields present")
                        
                        # Check options
                        options = question.get('options', [])
                        if len(options) != 4:
                            print(f"      ❌ Wrong number of options: {len(options)} (expected 4)")
                            valid_structure = False
                        else:
                            print(f"      ✅ Correct number of options: 4")
                        
                        # Check correct_option
                        correct_option = question.get('correct_option')
                        if not isinstance(correct_option, int) or correct_option not in [0, 1, 2, 3]:
                            print(f"      ❌ Invalid correct_option: {correct_option} (expected 0-3)")
                            valid_structure = False
                        else:
                            print(f"      ✅ Valid correct_option: {correct_option}")
                        
                        # Check metadata
                        metadata = question.get('metadata', {})
                        if 'language' not in metadata:
                            print(f"      ❌ Missing language in metadata")
                            valid_structure = False
                        else:
                            print(f"      ✅ Language present: {metadata['language']}")
                        
                        # Check sources if present
                        if 'sources' in metadata:
                            sources = metadata['sources']
                            if isinstance(sources, list) and len(sources) > 0:
                                print(f"      ✅ Sources present: {len(sources)} source(s)")
                            else:
                                print(f"      ⚠️  Sources field present but empty")
                        else:
                            print(f"      ⚠️  No sources field in metadata")
                    
                    print(f"\n📊 STRUCTURE VALIDATION:")
                    print(f"   Total questions: {len(questions)}")
                    print(f"   Valid structure: {'✅ YES' if valid_structure else '❌ NO'}")
                    
                    if valid_structure:
                        print("   🎯 SUCCESS: All questions follow the required structure!")
                    else:
                        print("   ⚠️  WARNING: Some questions have structural issues")
                        
                else:
                    print(f"❌ Quiz generation failed: {resp.status_code}")
                    print(f"   Response: {resp.text}")
                    
    except Exception as e:
        print(f"❌ Error testing structure enforcement: {str(e)}")

async def test_fallback_behavior():
    """Test that the system gracefully handles malformed responses"""
    print("\n🔄 TESTING FALLBACK BEHAVIOR")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            # Test with minimal parameters to trigger fallback if needed
            test_case = {
                "topic": "Test Topic",
                "difficulty": "easy",
                "numQuestions": 1,
                "docIds": DOCUMENT_IDS
            }
            
            headers = {
                "Authorization": "Bearer test_token_for_debug",
                "Content-Type": "application/json"
            }
            
            resp = await client.post(url, json=test_case, headers=headers)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                quiz_data = resp.json()
                quiz = quiz_data.get('quiz', {})
                questions = quiz.get('questions', [])
                
                print(f"✅ Generated {len(questions)} questions")
                
                # Check if fallback structure was used
                if len(questions) == 1 and "What should be done if no chunks are found" in questions[0].get('stem', ''):
                    print("🔄 Fallback structure was used (expected for test case)")
                else:
                    print("✅ Normal generation was successful")
                    
                # Validate structure anyway
                for i, question in enumerate(questions):
                    print(f"\n   📝 Question {i+1}:")
                    print(f"      Stem: {question.get('stem', 'N/A')}")
                    print(f"      Options: {len(question.get('options', []))} options")
                    print(f"      Correct: {question.get('correct_option', 'N/A')}")
                    print(f"      Metadata: {question.get('metadata', {})}")
                    
            else:
                print(f"❌ Quiz generation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing fallback behavior: {str(e)}")

if __name__ == "__main__":
    print("🔧 Structure Enforcement Test")
    print("=" * 60)
    
    asyncio.run(test_structure_enforcement())
    asyncio.run(test_fallback_behavior())
