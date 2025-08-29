#!/usr/bin/env python3
"""
Test script to verify the complete quiz generation flow works through the API gateway
"""

import requests
import json

def test_quiz_generation_flow():
    """Test the complete quiz generation flow through API gateway"""
    
    print("🚀 Testing complete quiz generation flow...")
    
    # Test payload
    payload = {
        "docIds": ["test-doc-1", "test-doc-2"],
        "numQuestions": 5,
        "questionTypes": ["MCQ"],
        "difficulty": "medium",
        "language": "auto"
    }
    
    print(f"📤 Sending quiz generation request with payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Call the API gateway endpoint
        response = requests.post(
            "http://localhost:8000/api/quizzes/generate",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token"
            }
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quiz generation successful!")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check if session was created
            if data.get("session_id"):
                print(f"🎯 Session created automatically: {data['session_id']}")
                print(f"   Quiz ID: {data.get('quiz_id')}")
                print(f"   Job ID: {data.get('job_id')}")
                
                # Test accessing the session
                session_id = data['session_id']
                print(f"🔍 Testing session access: {session_id}")
                
                session_response = requests.get(
                    f"http://localhost:8004/study-sessions/{session_id}/quiz",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    print(f"✅ Session accessible!")
                    print(f"   Questions: {len(session_data.get('questions', []))}")
                else:
                    print(f"❌ Session not accessible: {session_response.status_code}")
                    print(f"   Response: {session_response.text}")
            else:
                print("⚠️ No session created automatically")
                
        else:
            print(f"❌ Quiz generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Error testing quiz generation flow: {str(e)}")

if __name__ == "__main__":
    test_quiz_generation_flow()
