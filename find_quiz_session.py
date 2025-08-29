#!/usr/bin/env python3
"""
Script to find the session ID associated with a specific quiz ID.
This script queries the quiz service database to find related sessions.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Quiz ID we're looking for
TARGET_QUIZ_ID = "5a38de62-67e4-4a28-ac47-d5147cfc73c6"

def get_database_connection():
    """Get database connection from environment or use default"""
    # Try to get from environment first
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Default to local development database
        database_url = "postgresql://postgres:password@localhost:5432/quiz_db"
        print(f"⚠️  No DATABASE_URL found in environment, using default: {database_url}")
    
    try:
        engine = create_engine(database_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Connected to database successfully")
        return engine
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def find_quiz_sessions(engine, quiz_id):
    """Find all sessions related to a specific quiz ID"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query 1: Check if quiz exists
        quiz_query = text("""
            SELECT id, title, status, user_id, created_at 
            FROM quizzes 
            WHERE id = :quiz_id
        """)
        
        quiz_result = session.execute(quiz_query, {"quiz_id": quiz_id})
        quiz_data = quiz_result.fetchone()
        
        if not quiz_data:
            print(f"❌ Quiz with ID '{quiz_id}' not found in database")
            return None
        
        print(f"✅ Found quiz:")
        print(f"   ID: {quiz_data.id}")
        print(f"   Title: {quiz_data.title}")
        print(f"   Status: {quiz_data.status}")
        print(f"   User ID: {quiz_data.user_id}")
        print(f"   Created: {quiz_data.created_at}")
        print()
        
        # Query 2: Find quiz sessions
        sessions_query = text("""
            SELECT id, quiz_id, user_id, status, created_at, seed
            FROM quiz_sessions 
            WHERE quiz_id = :quiz_id
            ORDER BY created_at DESC
        """)
        
        sessions_result = session.execute(sessions_query, {"quiz_id": quiz_id})
        sessions = sessions_result.fetchall()
        
        if sessions:
            print(f"✅ Found {len(sessions)} quiz session(s):")
            for i, session_data in enumerate(sessions, 1):
                print(f"   Session {i}:")
                print(f"     Session ID: {session_data.id}")
                print(f"     Quiz ID: {session_data.quiz_id}")
                print(f"     User ID: {session_data.user_id}")
                print(f"     Status: {session_data.status}")
                print(f"     Created: {session_data.created_at}")
                print(f"     Seed: {session_data.seed}")
                print()
        else:
            print("⚠️  No quiz sessions found for this quiz")
        
        # Query 3: Find quiz attempts
        attempts_query = text("""
            SELECT attempt_id, quiz_id, user_id, status, started_at, submitted_at, total_score, max_score
            FROM quiz_attempts 
            WHERE quiz_id = :quiz_id
            ORDER BY started_at DESC
        """)
        
        attempts_result = session.execute(attempts_query, {"quiz_id": quiz_id})
        attempts = attempts_result.fetchall()
        
        if attempts:
            print(f"✅ Found {len(attempts)} quiz attempt(s):")
            for i, attempt_data in enumerate(attempts, 1):
                print(f"   Attempt {i}:")
                print(f"     Attempt ID: {attempt_data.attempt_id}")
                print(f"     Quiz ID: {attempt_data.quiz_id}")
                print(f"     User ID: {attempt_data.user_id}")
                print(f"     Status: {attempt_data.status}")
                print(f"     Started: {attempt_data.started_at}")
                print(f"     Submitted: {attempt_data.submitted_at}")
                print(f"     Score: {attempt_data.total_score}/{attempt_data.max_score}")
                print()
        else:
            print("⚠️  No quiz attempts found for this quiz")
        
        # Query 4: Check for any other related data
        related_query = text("""
            SELECT 
                'quiz_sessions' as table_name,
                COUNT(*) as count
            FROM quiz_sessions 
            WHERE quiz_id = :quiz_id
            UNION ALL
            SELECT 
                'quiz_attempts' as table_name,
                COUNT(*) as count
            FROM quiz_attempts 
            WHERE quiz_id = :quiz_id
            UNION ALL
            SELECT 
                'quiz_session_questions' as table_name,
                COUNT(*) as count
            FROM quiz_session_questions qsq
            JOIN quiz_sessions qs ON qsq.session_id = qs.id
            WHERE qs.quiz_id = :quiz_id
        """)
        
        related_result = session.execute(related_query, {"quiz_id": quiz_id})
        related_data = related_result.fetchall()
        
        print("📊 Summary of related data:")
        for row in related_data:
            print(f"   {row.table_name}: {row.count} records")
        
        return sessions
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None
    finally:
        session.close()

def main():
    """Main function"""
    print(f"🔍 Looking for quiz ID: {TARGET_QUIZ_ID}")
    print("=" * 60)
    
    # Get database connection
    engine = get_database_connection()
    if not engine:
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Find quiz sessions
    sessions = find_quiz_sessions(engine, TARGET_QUIZ_ID)
    
    if sessions:
        print("\n🎯 Frontend Access URLs:")
        print("=" * 60)
        
        for session_data in sessions:
            session_id = session_data.id
            print(f"Session ID: {session_id}")
            print(f"   Main Quiz Route: /quiz/session/{session_id}")
            print(f"   Study Session Route: /study-session/session-{session_id}")
            print(f"   Alternative Route: /study-session/session-{session_id}?quizId={TARGET_QUIZ_ID}")
            print()
        
        print("💡 Recommendation:")
        print("   Use the main quiz route: /quiz/session/{session_id}")
        print("   This will load the QuizSession component with full functionality")
        
    else:
        print("\n❌ No sessions found for this quiz ID")
        print("   This might mean:")
        print("   - The quiz hasn't been started yet")
        print("   - The quiz ID is incorrect")
        print("   - The quiz exists but no session was created")
        print("   - You need to start a new study session first")

if __name__ == "__main__":
    main()
