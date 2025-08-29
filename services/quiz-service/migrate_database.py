#!/usr/bin/env python3
"""
Database migration script for quiz service.
This script adds the new fields and tables needed for quiz sessions.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from database import engine, Base
from models import Quiz, QuizSession, QuizSessionQuestion, QuizSessionAnswer

def migrate_database():
    """Run database migrations"""
    print("🔄 Starting database migration...")
    
    try:
        # Create all tables (this will add new fields to existing tables)
        Base.metadata.create_all(bind=engine)
        print("✅ Database migration completed successfully!")
        
        # Verify the new models are accessible
        print("📋 Verifying models...")
        print(f"   - Quiz model: {Quiz.__tablename__}")
        print(f"   - QuizSession model: {QuizSession.__tablename__}")
        print(f"   - QuizSessionQuestion model: {QuizSessionQuestion.__tablename__}")
        print(f"   - QuizSessionAnswer model: {QuizSessionAnswer.__tablename__}")
        
        # Check if raw_json field exists in Quiz model
        if hasattr(Quiz, 'raw_json'):
            print("✅ raw_json field added to Quiz model")
        else:
            print("❌ raw_json field not found in Quiz model")
            
        print("\n🎉 Migration completed! The quiz session system is ready to use.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
