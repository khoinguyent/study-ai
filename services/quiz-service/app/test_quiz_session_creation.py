#!/usr/bin/env python3
"""
Test script to verify quiz session creation is working
"""

import asyncio
import httpx
import json
import os
from typing import Dict, Any

# Document IDs for testing
DOCUMENT_IDS = [
    "c84fdfad-da6d-4cc6-80f6-9ad18c5ff993",
    "c43478f7-f08a-4de1-a5e1-d2a71c42ec51", 
    "7313ca17-9cdd-4510-8dd7-6ef93e079a89",
    "9aced301-214d-4060-806c-235580034bef"
]

# Service URLs
QUIZ_SERVICE_URL = os.getenv('QUIZ_SERVICE_URL', 'http://localhost:8004')

async def test_quiz_session_creation():
    """Test that quiz session is created automatically after quiz generation"""
    print("🎯 TESTING QUIZ SESSION CREATION")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{QUIZ_SERVICE_URL}/quizzes/generate"
            
            payload = {
                "topic": "Test Quiz Session Creation",
                "difficulty": "medium",
                "numQuestions": 3,
                "docIds": DOCUMENT_IDS
            }
            
            headers = {
                "Authorization": "Bearer test_token_for_debug",
                "Content-Type": "application/json"
            }
            
            print(f"📤 Sending quiz generation request...")
            resp = await client.post(url, json=payload, headers=headers)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                quiz_data = resp.json()
                
                print(f"✅ Quiz generation successful!")
                print(f"   Quiz ID: {quiz_data.get('quiz_id')}")
                print(f"   Session ID: {quiz_data.get('session_id')}")
                print(f"   Job ID: {quiz_data.get('job_id')}")
                print(f"   Status: {quiz_data.get('status')}")
                
                # Check if session_id is present
                session_id = quiz_data.get('session_id')
                if session_id:
                    print(f"🎯 SUCCESS: Session created automatically!")
                    print(f"   Session ID: {session_id}")
                    
                    # Verify session exists in database
                    print(f"\n🔍 Verifying session in database...")
                    verify_url = f"{QUIZ_SERVICE_URL}/quizzes/sessions/{session_id}/view"
                    verify_resp = await client.get(verify_url, headers=headers)
                    
                    if verify_resp.status_code == 200:
                        session_data = verify_resp.json()
                        print(f"✅ Session verification successful!")
                        print(f"   Session ID: {session_data.get('session_id')}")
                        print(f"   Quiz ID: {session_data.get('quiz_id')}")
                        print(f"   Questions count: {len(session_data.get('questions', []))}")
                        
                        # Show first question details
                        if session_data.get('questions'):
                            first_q = session_data['questions'][0]
                            print(f"   First question type: {first_q.get('type')}")
                            print(f"   First question stem: {first_q.get('stem', '')[:50]}...")
                    else:
                        print(f"❌ Session verification failed: {verify_resp.status_code}")
                        print(f"   Response: {verify_resp.text}")
                        
                else:
                    print(f"❌ FAILED: No session ID in response!")
                    print(f"   Response data: {json.dumps(quiz_data, indent=2)}")
                    
            else:
                print(f"❌ Quiz generation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing quiz session creation: {str(e)}")

async def test_existing_quiz_session():
    """Test session creation for existing quiz"""
    print("\n🔄 TESTING SESSION CREATION FOR EXISTING QUIZ")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use the existing quiz ID
            quiz_id = "3fcbec8d-44c6-46ce-90fc-41539110246f"
            
            url = f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/sessions"
            
            headers = {
                "Authorization": "Bearer test_token_for_debug",
                "Content-Type": "application/json"
            }
            
            print(f"📤 Creating session for existing quiz {quiz_id}...")
            resp = await client.post(url, headers=headers)
            print(f"📊 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                session_data = resp.json()
                print(f"✅ Session creation successful!")
                print(f"   Session ID: {session_data.get('session_id')}")
                print(f"   Questions count: {session_data.get('count')}")
                
                # Verify the session
                session_id = session_data.get('session_id')
                if session_id:
                    verify_url = f"{QUIZ_SERVICE_URL}/quizzes/sessions/{session_id}/view"
                    verify_resp = await client.get(verify_url, headers=headers)
                    
                    if verify_resp.status_code == 200:
                        session_view = verify_resp.json()
                        print(f"✅ Session verification successful!")
                        print(f"   Session ID: {session_view.get('session_id')}")
                        print(f"   Quiz ID: {session_view.get('quiz_id')}")
                        print(f"   Questions count: {len(session_view.get('questions', []))}")
                    else:
                        print(f"❌ Session verification failed: {verify_resp.status_code}")
                        
            else:
                print(f"❌ Session creation failed: {resp.status_code}")
                print(f"   Response: {resp.text}")
                
    except Exception as e:
        print(f"❌ Error testing existing quiz session: {str(e)}")

if __name__ == "__main__":
    print("🔧 Quiz Session Creation Test")
    print("=" * 60)
    
    asyncio.run(test_quiz_session_creation())
    asyncio.run(test_existing_quiz_session())
