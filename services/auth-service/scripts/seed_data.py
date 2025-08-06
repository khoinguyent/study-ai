#!/usr/bin/env python3
"""
Data seeding script for Auth Service
Creates test users and sample data for development/testing
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, User
from app.schemas import UserCreate
from app.config import settings
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_test_users():
    """Create test users for development and testing"""
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.email == "test@test.com").first()
        if existing_user:
            print("✅ Test user already exists: test@test.com")
            return
        
        # Create test user
        test_user = User(
            email="test@test.com",
            username="testuser",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(test_user)
        
        # Create additional test users
        test_users = [
            {
                "email": "admin@study-ai.com",
                "username": "admin",
                "password": "admin123",
                "is_active": True
            },
            {
                "email": "student@study-ai.com", 
                "username": "student",
                "password": "student123",
                "is_active": True
            },
            {
                "email": "teacher@study-ai.com",
                "username": "teacher", 
                "password": "teacher123",
                "is_active": True
            },
            {
                "email": "demo@study-ai.com",
                "username": "demo",
                "password": "demo123",
                "is_active": True
            }
        ]
        
        for user_data in test_users:
            # Check if user already exists
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    is_active=user_data["is_active"],
                    created_at=datetime.utcnow()
                )
                db.add(user)
                print(f"✅ Created user: {user_data['email']} (password: {user_data['password']})")
        
        db.commit()
        print("✅ Test users created successfully!")
        print("\n📋 Test User Credentials:")
        print("=" * 50)
        print("Primary Test User:")
        print("  Email: test@test.com")
        print("  Password: test123")
        print("  Username: testuser")
        print("\nAdditional Test Users:")
        print("  Email: admin@study-ai.com | Password: admin123")
        print("  Email: student@study-ai.com | Password: student123") 
        print("  Email: teacher@study-ai.com | Password: teacher123")
        print("  Email: demo@study-ai.com | Password: demo123")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating test users: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def create_sample_data():
    """Create additional sample data if needed"""
    print("📊 Creating sample data...")
    # Add more sample data creation here if needed
    print("✅ Sample data created!")

def main():
    """Main function to run the seeding script"""
    print("🌱 Starting data seeding for Auth Service...")
    print("=" * 60)
    
    try:
        # Create test users
        create_test_users()
        
        # Create additional sample data
        create_sample_data()
        
        print("\n🎉 Data seeding completed successfully!")
        print("\n💡 You can now use these credentials to test the application:")
        print("   - Login at: http://localhost:8001/docs")
        print("   - API Gateway: http://localhost")
        
    except Exception as e:
        print(f"❌ Data seeding failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 