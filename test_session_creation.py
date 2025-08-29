#!/usr/bin/env python3
"""
Test script to verify the new session creation endpoint works
"""

import requests
import json

def test_session_creation():
    """Test the new /quiz-sessions/from-quiz/{quiz_id} endpoint"""
    
    # First, let's get a list of existing quizzes
    print("🔍 Getting existing quizzes...")
    try:
        response = requests.get("http://localhost:8004/quizzes")
        if response.status_code == 200:
            quizzes = response.json()
            print(f"✅ Found {quizzes.get('total', 0)} quizzes")
            
            if quizzes.get('quizzes'):
                quiz_id = quizzes['quizzes'][0]['id']
                print(f"🎯 Using quiz ID: {quiz_id}")
                
                # Test session creation
                print(f"🚀 Creating session for quiz {quiz_id}...")
                session_response = requests.post(
                    f"http://localhost:8004/quiz-sessions/from-quiz/{quiz_id}",
                    params={"user_id": "test-user", "shuffle": "true"},
                    headers={"Authorization": "Bearer test-token"}
                )
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    print(f"✅ Session created successfully!")
                    print(f"   Session ID: {session_data.get('session_id')}")
                    print(f"   Question Count: {session_data.get('count')}")
                    
                    # Test getting the session quiz data
                    session_id = session_data.get('session_id')
                    print(f"🔍 Testing session data retrieval for {session_id}...")
                    
                    quiz_response = requests.get(
                        f"http://localhost:8004/study-sessions/{session_id}/quiz",
                        headers={"Authorization": "Bearer test-token"}
                    )
                    
                    if quiz_response.status_code == 200:
                        quiz_data = quiz_response.json()
                        print(f"✅ Session quiz data retrieved successfully!")
                        print(f"   Session ID: {quiz_data.get('session_id')}")
                        print(f"   Quiz ID: {quiz_data.get('quiz_id')}")
                        print(f"   Questions: {len(quiz_data.get('questions', []))}")
                    else:
                        print(f"❌ Failed to get session quiz data: {quiz_response.status_code}")
                        print(f"   Response: {quiz_response.text}")
                        
                else:
                    print(f"❌ Failed to create session: {session_response.status_code}")
                    print(f"   Response: {session_response.text}")
            else:
                print("⚠️ No quizzes found in database")
                
        else:
            print(f"❌ Failed to get quizzes: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error testing session creation: {str(e)}")

if __name__ == "__main__":
    test_session_creation()
