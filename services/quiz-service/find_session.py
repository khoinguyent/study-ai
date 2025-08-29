#!/usr/bin/env python3
"""
Simple script to find session ID for quiz ID: 5a38de62-67e4-4a28-ac47-d5147cfc73c6
Run this from the quiz-service directory
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import get_db
from models import Quiz, QuizSession, QuizAttempt

def find_quiz_session():
    """Find session ID for the specific quiz ID"""
    quiz_id = "5a38de62-67e4-4a28-ac47-d5147cfc73c6"
    
    print(f"🔍 Looking for quiz ID: {quiz_id}")
    print("=" * 60)
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Check if quiz exists
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        if not quiz:
            print(f"❌ Quiz with ID '{quiz_id}' not found in database")
            return
        
        print(f"✅ Found quiz:")
        print(f"   ID: {quiz.id}")
        print(f"   Title: {quiz.title}")
        print(f"   Status: {quiz.status}")
        print(f"   User ID: {quiz.user_id}")
        print(f"   Created: {quiz.created_at}")
        print()
        
        # Find quiz sessions
        sessions = db.query(QuizSession).filter(QuizSession.quiz_id == quiz_id).all()
        
        if sessions:
            print(f"✅ Found {len(sessions)} quiz session(s):")
            for i, session in enumerate(sessions, 1):
                print(f"   Session {i}:")
                print(f"     Session ID: {session.id}")
                print(f"     Quiz ID: {session.quiz_id}")
                print(f"     User ID: {session.user_id}")
                print(f"     Status: {session.status}")
                print(f"     Created: {session.created_at}")
                print(f"     Seed: {session.seed}")
                print()
        else:
            print("⚠️  No quiz sessions found for this quiz")
        
        # Find quiz attempts
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()
        
        if attempts:
            print(f"✅ Found {len(attempts)} quiz attempt(s):")
            for i, attempt in enumerate(attempts, 1):
                print(f"   Attempt {i}:")
                print(f"     Attempt ID: {attempt.attempt_id}")
                print(f"     Quiz ID: {attempt.quiz_id}")
                print(f"     User ID: {attempt.user_id}")
                print(f"     Status: {attempt.status}")
                print(f"     Started: {attempt.started_at}")
                print(f"     Submitted: {attempt.submitted_at}")
                print(f"     Score: {attempt.total_score}/{attempt.max_score}")
                print()
        else:
            print("⚠️  No quiz attempts found for this quiz")
        
        # Summary
        print("📊 Summary:")
        print(f"   Quiz sessions: {len(sessions)}")
        print(f"   Quiz attempts: {len(attempts)}")
        
        if sessions:
            print("\n🎯 Frontend Access URLs:")
            print("=" * 60)
            
            for session in sessions:
                session_id = session.id
                print(f"Session ID: {session_id}")
                print(f"   Main Quiz Route: /quiz/session/{session_id}")
                print(f"   Study Session Route: /study-session/session-{session_id}")
                print(f"   Alternative Route: /study-session/session-{session_id}?quizId={quiz_id}")
                print()
            
            print("💡 Recommendation:")
            print("   Use the main quiz route: /quiz/session/{session_id}")
            print("   This will load the QuizSession component with full functionality")
        else:
            print("\n❌ No sessions found for this quiz ID")
            print("   This might mean:")
            print("   - The quiz hasn't been started yet")
            print("   - The quiz exists but no session was created")
            print("   - You need to start a new study session first")
    
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    find_quiz_session()
