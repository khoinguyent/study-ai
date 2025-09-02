#!/usr/bin/env python3
"""
Test script to verify the fixed quiz generation
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

async def test_fixed_quiz_generation():
    """Test the fixed quiz generation"""
    print("🎯 TESTING FIXED QUIZ GENERATION")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            # Prepare request payload
            payload = {
                "topic": "Vietnam History - Tay Son Rebellion and Nguyen Dynasty",
                "difficulty": "medium",
                "numQuestions": 4,
                "docIds": DOCUMENT_IDS
            }
            
            # Add authentication header (mock token for testing)
            headers = {
                "Authorization": "Bearer test_token_for_debug",
                "Content-Type": "application/json"
            }
            
            print(f"🌐 Making request to: {url}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            resp = await client.post(url, json=payload, headers=headers)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                quiz_data = resp.json()
                print("✅ Quiz generation successful!")
                print(f"📋 Quiz data: {json.dumps(quiz_data, indent=2)}")
                
                # Analyze questions
                quiz = quiz_data.get('quiz', {})
                questions = quiz.get('questions', [])
                print(f"\n❓ Generated {len(questions)} questions:")
                
                # Check if questions are related to Vietnam history
                vietnam_keywords = ["vietnam", "nguyen", "tay son", "dynasty", "gia dinh", "siam", "hue", "anh", "rebellion", "war", "history"]
                related_questions = 0
                
                for i, q in enumerate(questions):
                    stem = q.get('stem', '')
                    options = q.get('options', [])
                    correct = q.get('correct_option', -1)
                    
                    # Check if question contains Vietnam-related keywords
                    question_text = stem.lower() + " " + " ".join(options).lower()
                    is_related = any(keyword in question_text for keyword in vietnam_keywords)
                    
                    if is_related:
                        related_questions += 1
                        marker = "✅"
                    else:
                        marker = "❌"
                    
                    print(f"\n   {marker} Question {i+1}: {stem}")
                    for j, opt in enumerate(options):
                        correct_marker = "✓" if j == correct else " "
                        print(f"     {correct_marker} {j}. {opt}")
                
                print(f"\n📊 ANALYSIS:")
                print(f"   Total questions: {len(questions)}")
                print(f"   Related to Vietnam history: {related_questions}")
                print(f"   Relevance rate: {related_questions / len(questions) * 100:.1f}%")
                
                if related_questions >= len(questions) * 0.75:  # At least 75% should be related
                    print("✅ SUCCESS: Most questions are now related to the documents!")
                else:
                    print("⚠️  WARNING: Some questions are still not related to the documents.")
                    
            else:
                print(f"❌ Quiz generation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing quiz generation: {str(e)}")

async def test_quiz_generation_with_different_topics():
    """Test quiz generation with different topics to see if it's more specific"""
    print("\n🎯 TESTING WITH DIFFERENT TOPICS")
    print("=" * 60)
    
    topics = [
        "Nguyen Anh's Exile and Return",
        "Tay Son Rebellion",
        "Vietnamese History",
        "Nguyen Dynasty Establishment"
    ]
    
    for topic in topics:
        print(f"\n📚 Testing topic: {topic}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
                
                payload = {
                    "topic": topic,
                    "difficulty": "medium",
                    "numQuestions": 2,
                    "docIds": DOCUMENT_IDS
                }
                
                headers = {
                    "Authorization": "Bearer test_token_for_debug",
                    "Content-Type": "application/json"
                }
                
                resp = await client.post(url, json=payload, headers=headers)
                
                if resp.status_code == 200:
                    quiz_data = resp.json()
                    quiz = quiz_data.get('quiz', {})
                    questions = quiz.get('questions', [])
                    
                    print(f"   ✅ Generated {len(questions)} questions")
                    
                    # Check relevance
                    vietnam_keywords = ["vietnam", "nguyen", "tay son", "dynasty", "gia dinh", "siam", "hue", "anh", "rebellion", "war", "history"]
                    related_count = 0
                    
                    for q in questions:
                        stem = q.get('stem', '')
                        options = q.get('options', [])
                        question_text = stem.lower() + " " + " ".join(options).lower()
                        if any(keyword in question_text for keyword in vietnam_keywords):
                            related_count += 1
                    
                    relevance_rate = related_count / len(questions) * 100 if questions else 0
                    print(f"   📊 Relevance: {relevance_rate:.1f}%")
                    
                    # Show first question
                    if questions:
                        first_q = questions[0]
                        print(f"   📝 Sample: {first_q.get('stem', '')[:100]}...")
                else:
                    print(f"   ❌ Failed: {resp.status_code}")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Fixed Quiz Generation Test")
    print("=" * 60)
    
    asyncio.run(test_fixed_quiz_generation())
    asyncio.run(test_quiz_generation_with_different_topics())
