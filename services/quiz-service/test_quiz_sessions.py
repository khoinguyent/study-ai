#!/usr/bin/env python3
"""
Test script to verify the quiz session functionality works correctly.
This script tests the new quiz session endpoints and functionality.
"""

import asyncio
import aiohttp
import json
import sys

# Quiz service base URL
BASE_URL = "http://localhost:8004"

async def test_create_quiz_session():
    """Test creating a quiz session"""
    try:
        # First, we need a quiz ID - let's create one or use an existing one
        # For now, we'll assume there's a quiz with ID "test-quiz-1"
        quiz_id = "test-quiz-1"
        
        payload = {
            "user_id": "test-user-1",
            "shuffle": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/quizzes/{quiz_id}/sessions",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Quiz session creation: {data}")
                    return data.get("session_id")
                else:
                    print(f"❌ Quiz session creation failed: {response.status}")
                    print(f"Response: {await response.text()}")
                    return None
    except Exception as e:
        print(f"❌ Quiz session creation error: {e}")
        return None

async def test_view_session(session_id):
    """Test viewing a quiz session"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/quizzes/sessions/{session_id}/view") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Session view: {data}")
                    return data
                else:
                    print(f"❌ Session view failed: {response.status}")
                    print(f"Response: {await response.text()}")
                    return None
    except Exception as e:
        print(f"❌ Session view error: {e}")
        return None

async def test_save_answers(session_id, session_data):
    """Test saving answers for a quiz session"""
    try:
        if not session_data or not session_data.get("questions"):
            print("❌ No questions found in session data")
            return False
            
        # Create sample answers based on question types
        answers = []
        for question in session_data["questions"]:
            q_type = question["type"]
            q_id = question["session_question_id"]
            
            if q_type == "mcq":
                # Select first option for MCQ
                if question.get("options"):
                    answers.append({
                        "session_question_id": q_id,
                        "type": q_type,
                        "response": {"selected_option_id": question["options"][0]["id"]}
                    })
            elif q_type == "true_false":
                # Answer true for true/false
                answers.append({
                    "session_question_id": q_id,
                    "type": q_type,
                    "response": {"answer_bool": True}
                })
            elif q_type == "fill_in_blank":
                # Fill in blanks with sample text
                blanks_count = question.get("blanks", 1)
                answers.append({
                    "session_question_id": q_id,
                    "type": q_type,
                    "response": {"blanks": ["Sample answer"] * blanks_count}
                })
            elif q_type == "short_answer":
                # Provide sample short answer
                answers.append({
                    "session_question_id": q_id,
                    "type": q_type,
                    "response": {"text": "This is a sample answer"}
                })
        
        payload = {
            "answers": answers,
            "replace": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/quizzes/sessions/{session_id}/answers",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Save answers: {data}")
                    return True
                else:
                    print(f"❌ Save answers failed: {response.status}")
                    print(f"Response: {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Save answers error: {e}")
        return False

async def test_submit_session(session_id):
    """Test submitting a quiz session for grading"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/quizzes/sessions/{session_id}/submit") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Session submission: {data}")
                    return data
                else:
                    print(f"❌ Session submission failed: {response.status}")
                    print(f"Response: {await response.text()}")
                    return None
    except Exception as e:
        print(f"❌ Session submission error: {e}")
        return None

async def main():
    """Run all tests"""
    print("🧪 Testing Quiz Session Functionality")
    print("=" * 50)
    
    # Test 1: Create quiz session
    print("\n1. Testing quiz session creation...")
    session_id = await test_create_quiz_session()
    if not session_id:
        print("❌ Cannot proceed without a session ID")
        return
    
    # Test 2: View session
    print("\n2. Testing session view...")
    session_data = await test_view_session(session_id)
    if not session_data:
        print("❌ Cannot proceed without session data")
        return
    
    # Test 3: Save answers
    print("\n3. Testing answer saving...")
    answers_saved = await test_save_answers(session_id, session_data)
    if not answers_saved:
        print("❌ Cannot proceed without saved answers")
        return
    
    # Test 4: Submit session
    print("\n4. Testing session submission...")
    submission_result = await test_submit_session(session_id)
    if submission_result:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Session submission failed")

if __name__ == "__main__":
    asyncio.run(main())
