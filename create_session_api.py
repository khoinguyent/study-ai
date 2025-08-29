#!/usr/bin/env python3
"""
Simple script to create a quiz session via API call.
This will create a new session for the existing quiz ID.
"""

import requests
import json

# Configuration
QUIZ_SERVICE_URL = "http://localhost:8004"
QUIZ_ID = "5a38de62-67e4-4a28-ac47-d5147cfc73c6"

def create_session_via_api():
    """Create a quiz session by calling the API endpoint"""
    
    print(f"🚀 Creating quiz session via API")
    print("=" * 60)
    print(f"Quiz Service URL: {QUIZ_SERVICE_URL}")
    print(f"Quiz ID: {QUIZ_ID}")
    print()
    
    # Note: This endpoint requires authentication
    # You'll need to provide a valid JWT token
    print("⚠️  Note: This endpoint requires authentication")
    print("   You'll need to provide a valid JWT token in the Authorization header")
    print()
    
    # Example API call (you'll need to add your auth token)
    api_url = f"{QUIZ_SERVICE_URL}/quizzes/{QUIZ_ID}/create-session"
    
    print("📡 API Endpoint:")
    print(f"   POST {api_url}")
    print()
    
    print("🔑 Required Headers:")
    print("   Content-Type: application/json")
    print("   Authorization: Bearer <your-jwt-token>")
    print()
    
    print("📝 Example cURL command:")
    print(f"   curl -X POST '{api_url}' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -H 'Authorization: Bearer <your-jwt-token>'")
    print()
    
    print("🌐 Frontend Access:")
    print("   After creating the session, you can access the quiz at:")
    print("   /quiz/session/{sessionId}")
    print()
    
    print("💡 Alternative: Use the Python script")
    print("   If you have database access, run:")
    print("   cd services/quiz-service && python3 create_session.py")
    
    return api_url

def test_api_health():
    """Test if the quiz service is running"""
    try:
        response = requests.get(f"{QUIZ_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ Quiz service is running")
            return True
        else:
            print(f"⚠️  Quiz service responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to quiz service")
        print("   Make sure the service is running on port 8004")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Quiz Session Creator - API Method")
    print("=" * 60)
    
    # Test if service is running
    if not test_api_health():
        print("\n❌ Quiz service is not accessible")
        print("   Please ensure the service is running before proceeding")
        return
    
    print()
    
    # Show API creation method
    api_url = create_session_via_api()
    
    print("📋 Next Steps:")
    print("   1. Get a valid JWT token from your auth service")
    print("   2. Call the API endpoint with the token")
    print("   3. Use the returned sessionId to access the quiz in frontend")
    print()
    
    print("🔗 Quick Links:")
    print(f"   API Endpoint: {api_url}")
    print("   Frontend Base: http://localhost:3000")

if __name__ == "__main__":
    main()
