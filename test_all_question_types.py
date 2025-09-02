#!/usr/bin/env python3
"""
Comprehensive test script for all question types
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

async def test_individual_question_types():
    """Test each question type individually"""
    print("🔍 TESTING INDIVIDUAL QUESTION TYPES")
    print("=" * 60)
    
    question_types = [
        {
            "name": "MCQ Only",
            "topic": "MCQ Questions about Vietnam History",
            "expected_types": ["MCQ"],
            "numQuestions": 3
        },
        {
            "name": "True/False Only",
            "topic": "True/False Statements about Vietnam History",
            "expected_types": ["TRUE_FALSE"],
            "numQuestions": 2
        },
        {
            "name": "Fill-in-Blank Only",
            "topic": "Fill-in-Blank Questions about Vietnam History",
            "expected_types": ["FILL_BLANK"],
            "numQuestions": 2
        },
        {
            "name": "Short Answer Only",
            "topic": "Short Answer Questions about Vietnam History",
            "expected_types": ["SHORT_ANSWER"],
            "numQuestions": 2
        }
    ]
    
    for test_case in question_types:
        print(f"\n📚 Test: {test_case['name']}")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
                
                payload = {
                    "topic": test_case['topic'],
                    "difficulty": "medium",
                    "numQuestions": test_case['numQuestions'],
                    "docIds": DOCUMENT_IDS
                }
                
                headers = {
                    "Authorization": "Bearer test_token_for_debug",
                    "Content-Type": "application/json"
                }
                
                resp = await client.post(url, json=payload, headers=headers)
                print(f"📊 Response status: {resp.status_code}")
                
                if resp.status_code == 200:
                    quiz_data = resp.json()
                    quiz = quiz_data.get('quiz', {})
                    questions = quiz.get('questions', [])
                    
                    print(f"✅ Generated {len(questions)} questions")
                    
                    # Validate question types
                    actual_types = [q.get('type', 'UNKNOWN') for q in questions]
                    print(f"📋 Expected types: {test_case['expected_types']}")
                    print(f"📋 Actual types: {actual_types}")
                    
                    # Check if all questions are of expected type
                    all_correct_type = all(qtype in test_case['expected_types'] for qtype in actual_types)
                    print(f"🎯 All correct types: {'✅ YES' if all_correct_type else '❌ NO'}")
                    
                    # Validate structure for each question
                    valid_structure = True
                    for i, question in enumerate(questions):
                        print(f"\n   📝 Question {i+1} ({question.get('type', 'UNKNOWN')}):")
                        print(f"      Stem: {question.get('stem', 'N/A')[:80]}...")
                        
                        # Validate based on question type
                        if not validate_question_structure(question):
                            valid_structure = False
                            print(f"      ❌ Invalid structure")
                        else:
                            print(f"      ✅ Valid structure")
                    
                    print(f"\n📊 STRUCTURE VALIDATION:")
                    print(f"   Total questions: {len(questions)}")
                    print(f"   Valid structure: {'✅ YES' if valid_structure else '❌ NO'}")
                    print(f"   Correct types: {'✅ YES' if all_correct_type else '❌ NO'}")
                    
                else:
                    print(f"❌ Quiz generation failed: {resp.status_code}")
                    print(f"   Response: {resp.text}")
                    
        except Exception as e:
            print(f"❌ Error testing {test_case['name']}: {str(e)}")

async def test_mixed_question_types():
    """Test mixed question types in a single quiz"""
    print("\n🎯 TESTING MIXED QUESTION TYPES")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            payload = {
                "topic": "Mixed Question Types - Vietnam History",
                "difficulty": "medium",
                "numQuestions": 8,  # Request more questions to get variety
                "docIds": DOCUMENT_IDS
            }
            
            headers = {
                "Authorization": "Bearer test_token_for_debug",
                "Content-Type": "application/json"
            }
            
            resp = await client.post(url, json=payload, headers=headers)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                quiz_data = resp.json()
                quiz = quiz_data.get('quiz', {})
                questions = quiz.get('questions', [])
                
                print(f"✅ Generated {len(questions)} questions")
                
                # Analyze question type distribution
                type_counts = {}
                for question in questions:
                    qtype = question.get('type', 'UNKNOWN')
                    type_counts[qtype] = type_counts.get(qtype, 0) + 1
                
                print(f"\n📊 QUESTION TYPE DISTRIBUTION:")
                for qtype, count in type_counts.items():
                    print(f"   {qtype}: {count} questions")
                
                # Validate all questions
                valid_count = 0
                invalid_count = 0
                
                for i, question in enumerate(questions):
                    print(f"\n   📝 Question {i+1} ({question.get('type', 'UNKNOWN')}):")
                    print(f"      Stem: {question.get('stem', 'N/A')[:80]}...")
                    
                    if validate_question_structure(question):
                        valid_count += 1
                        print(f"      ✅ Valid structure")
                    else:
                        invalid_count += 1
                        print(f"      ❌ Invalid structure")
                
                print(f"\n📊 MIXED QUIZ VALIDATION:")
                print(f"   Total questions: {len(questions)}")
                print(f"   Valid questions: {valid_count}")
                print(f"   Invalid questions: {invalid_count}")
                print(f"   Success rate: {valid_count/len(questions)*100:.1f}%")
                
                if valid_count == len(questions):
                    print("   🎯 SUCCESS: All questions are valid!")
                else:
                    print("   ⚠️  WARNING: Some questions have issues")
                    
            else:
                print(f"❌ Quiz generation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing mixed question types: {str(e)}")

def validate_question_structure(question: Dict[str, Any]) -> bool:
    """Validate question structure based on its type"""
    try:
        if not isinstance(question, dict):
            return False
        
        question_type = question.get('type')
        if not question_type:
            return False
        
        if question_type == "MCQ":
            return validate_mcq_question(question)
        elif question_type == "TRUE_FALSE":
            return validate_true_false_question(question)
        elif question_type == "FILL_BLANK":
            return validate_fill_blank_question(question)
        elif question_type == "SHORT_ANSWER":
            return validate_short_answer_question(question)
        else:
            return False
            
    except Exception:
        return False

def validate_mcq_question(question: Dict[str, Any]) -> bool:
    """Validate MCQ question structure"""
    required_fields = ["stem", "options", "correct_option"]
    if not all(field in question for field in required_fields):
        return False
    
    options = question.get("options", [])
    if not isinstance(options, list) or len(options) != 4:
        return False
    
    correct_option = question.get("correct_option")
    if not isinstance(correct_option, int) or correct_option not in [0, 1, 2, 3]:
        return False
    
    return True

def validate_true_false_question(question: Dict[str, Any]) -> bool:
    """Validate True/False question structure"""
    required_fields = ["stem", "options", "correct_option"]
    if not all(field in question for field in required_fields):
        return False
    
    options = question.get("options", [])
    if not isinstance(options, list) or len(options) != 2:
        return False
    
    correct_option = question.get("correct_option")
    if not isinstance(correct_option, int) or correct_option not in [0, 1]:
        return False
    
    return True

def validate_fill_blank_question(question: Dict[str, Any]) -> bool:
    """Validate Fill-in-Blank question structure"""
    required_fields = ["stem", "blanks", "correct_answer"]
    if not all(field in question for field in required_fields):
        return False
    
    blanks = question.get("blanks")
    if not isinstance(blanks, int) or blanks < 1:
        return False
    
    correct_answer = question.get("correct_answer")
    if not isinstance(correct_answer, str) or len(correct_answer.strip()) == 0:
        return False
    
    return True

def validate_short_answer_question(question: Dict[str, Any]) -> bool:
    """Validate Short Answer question structure"""
    required_fields = ["stem", "correct_answer"]
    if not all(field in question for field in required_fields):
        return False
    
    correct_answer = question.get("correct_answer")
    if not isinstance(correct_answer, str) or len(correct_answer.strip()) == 0:
        return False
    
    return True

async def test_fallback_behavior():
    """Test fallback behavior with all question types"""
    print("\n🔄 TESTING FALLBACK BEHAVIOR")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            # Test with minimal parameters
            test_case = {
                "topic": "Test Fallback",
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
                fallback_indicators = [
                    "What should be done if no chunks are found",
                    "The system can handle multiple question types",
                    "The quiz system supports _____ question types",
                    "Explain why question type validation is important"
                ]
                
                fallback_used = any(
                    any(indicator in q.get('stem', '') for indicator in fallback_indicators)
                    for q in questions
                )
                
                if fallback_used:
                    print("🔄 Fallback structure was used")
                else:
                    print("✅ Normal generation was successful")
                
                # Validate structure anyway
                for i, question in enumerate(questions):
                    print(f"\n   📝 Question {i+1} ({question.get('type', 'UNKNOWN')}):")
                    print(f"      Stem: {question.get('stem', 'N/A')}")
                    
                    if question.get('type') == 'MCQ':
                        print(f"      Options: {len(question.get('options', []))} options")
                        print(f"      Correct: {question.get('correct_option', 'N/A')}")
                    elif question.get('type') == 'TRUE_FALSE':
                        print(f"      Options: {len(question.get('options', []))} options")
                        print(f"      Correct: {question.get('correct_option', 'N/A')}")
                    elif question.get('type') == 'FILL_BLANK':
                        print(f"      Blanks: {question.get('blanks', 'N/A')}")
                        print(f"      Answer: {question.get('correct_answer', 'N/A')}")
                    elif question.get('type') == 'SHORT_ANSWER':
                        print(f"      Answer: {question.get('correct_answer', 'N/A')}")
                    
                    print(f"      Metadata: {question.get('metadata', {})}")
                    
            else:
                print(f"❌ Quiz generation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing fallback behavior: {str(e)}")

if __name__ == "__main__":
    print("🔧 Comprehensive Question Type Test")
    print("=" * 60)
    
    asyncio.run(test_individual_question_types())
    asyncio.run(test_mixed_question_types())
    asyncio.run(test_fallback_behavior())
