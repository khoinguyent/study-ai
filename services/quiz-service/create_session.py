#!/usr/bin/env python3
"""
Script to create a new quiz session for an existing quiz ID.
This will allow immediate access to the quiz in the frontend.
"""

import sys
import os
import uuid
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import get_db
from models import Quiz, QuizSession, QuizSessionQuestion

def create_quiz_session():
    """Create a new session for the existing quiz ID"""
    quiz_id = "5a38de62-67e4-4a28-ac47-d5147cfc73c6"
    
    print(f"🎯 Creating new session for quiz ID: {quiz_id}")
    print("=" * 60)
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 1. Check if the quiz exists
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        if not quiz:
            print(f"❌ Quiz with ID '{quiz_id}' not found in database")
            print("   Please ensure the quiz exists before creating a session")
            return None
        
        print(f"✅ Found quiz:")
        print(f"   ID: {quiz.id}")
        print(f"   Title: {quiz.title}")
        print(f"   Status: {quiz.status}")
        print(f"   User ID: {quiz.user_id}")
        print(f"   Created: {quiz.created_at}")
        print()
        
        # 2. Create a new quiz session
        new_session = QuizSession(
            id=str(uuid.uuid4()),
            quiz_id=quiz_id,
            user_id=quiz.user_id,  # Use the same user ID as the quiz
            seed=str(uuid.uuid4()),  # Generate a unique seed
            status="active",
            created_at=datetime.utcnow()
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        print(f"✅ Created new quiz session:")
        print(f"   Session ID: {new_session.id}")
        print(f"   Quiz ID: {new_session.quiz_id}")
        print(f"   User ID: {new_session.user_id}")
        print(f"   Status: {new_session.status}")
        print(f"   Created: {new_session.created_at}")
        print(f"   Seed: {new_session.seed}")
        print()
        
        # 3. Create session questions from the quiz
        if quiz.questions and isinstance(quiz.questions, dict):
            questions_data = quiz.questions.get('questions', [])
            
            if questions_data:
                print(f"📝 Creating session questions from quiz...")
                
                for i, question_data in enumerate(questions_data):
                    # Extract question information
                    q_type = question_data.get('type', 'mcq').lower()
                    stem = question_data.get('question', question_data.get('prompt', f'Question {i+1}'))
                    
                    # Handle different question types
                    options = None
                    blanks = None
                    
                    if q_type in ['mcq', 'single_choice', 'multiple_choice']:
                        options = question_data.get('options', [])
                    elif q_type in ['fill_blank', 'fill_in_blank']:
                        blanks = question_data.get('blanks', 1)
                    
                    # Create session question
                    session_question = QuizSessionQuestion(
                        id=str(uuid.uuid4()),
                        session_id=new_session.id,
                        display_index=i + 1,
                        q_type=q_type,
                        stem=stem,
                        options=options,
                        blanks=blanks,
                        private_payload={
                            'correct_answer': question_data.get('correct_answer'),
                            'explanation': question_data.get('explanation'),
                            'points': question_data.get('points', 1)
                        },
                        meta_data={
                            'source_question_id': question_data.get('id', f'q{i+1}'),
                            'question_type': q_type
                        },
                        source_index=i
                    )
                    
                    db.add(session_question)
                
                db.commit()
                print(f"✅ Created {len(questions_data)} session questions")
            else:
                print("⚠️  No questions found in quiz data")
        else:
            print("⚠️  Quiz questions data is not in expected format")
        
        # 4. Display frontend access information
        print("\n🎯 Frontend Access URLs:")
        print("=" * 60)
        
        session_id = new_session.id
        print(f"Session ID: {session_id}")
        print(f"Quiz ID: {quiz_id}")
        print()
        
        print("🌐 Available Routes:")
        print(f"   1. Main Quiz Route: /quiz/session/{session_id}")
        print(f"   2. Study Session Route: /study-session/session-{session_id}")
        print(f"   3. With Quiz Context: /study-session/session-{session_id}?quizId={quiz_id}")
        print()
        
        print("💡 Recommendation:")
        print(f"   Use: /quiz/session/{session_id}")
        print("   This will load the QuizSession component with full functionality")
        print()
        
        print("📱 Quick Access:")
        print(f"   Copy this URL to your browser:")
        print(f"   http://localhost:3000/quiz/session/{session_id}")
        
        return new_session
        
    except Exception as e:
        print(f"❌ Error creating quiz session: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

def main():
    """Main function"""
    print("🚀 Quiz Session Creator")
    print("=" * 60)
    
    session = create_quiz_session()
    
    if session:
        print("\n✅ Session created successfully!")
        print("   You can now access the quiz in the frontend")
    else:
        print("\n❌ Failed to create session")
        print("   Check the error messages above")

if __name__ == "__main__":
    main()
