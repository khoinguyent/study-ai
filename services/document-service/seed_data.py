#!/usr/bin/env python3
"""
Data seeding script for Document Service
Creates sample subjects and categories for development/testing
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Subject, Category
from app.config import settings

def create_sample_data():
    """Create sample subjects and categories for development and testing"""
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Test user ID (this should match the user created in auth service)
        test_user_id = "c3eb1d08-ced5-449f-ad7d-f7a9f0c5cb80"  # test@test.com
        
        # Check if subjects already exist
        existing_subjects = db.query(Subject).filter(Subject.user_id == test_user_id).count()
        if existing_subjects > 0:
            print("✅ Sample subjects already exist for test user")
            return
        
        print("🌱 Creating sample subjects and categories...")
        
        # Create sample subjects
        subjects_data = [
            {
                "name": "Computer Science",
                "description": "Computer science and programming topics",
                "icon": "laptop",
                "color_theme": "blue"
            },
            {
                "name": "Mathematics",
                "description": "Mathematics and problem-solving",
                "icon": "calculator",
                "color_theme": "green"
            },
            {
                "name": "History",
                "description": "Historical events and analysis",
                "icon": "book-open",
                "color_theme": "amber"
            },
            {
                "name": "Science",
                "description": "Scientific concepts and experiments",
                "icon": "flask",
                "color_theme": "purple"
            },
            {
                "name": "Literature",
                "description": "Books, poetry, and literary analysis",
                "icon": "book",
                "color_theme": "red"
            }
        ]
        
        created_subjects = []
        for subject_data in subjects_data:
            subject = Subject(
                name=subject_data["name"],
                description=subject_data["description"],
                icon=subject_data["icon"],
                color_theme=subject_data["color_theme"],
                user_id=test_user_id
            )
            db.add(subject)
            db.flush()  # Flush to get the ID
            created_subjects.append(subject)
            print(f"✅ Created subject: {subject.name}")
        
        # Create sample categories for each subject
        categories_data = {
            "Computer Science": [
                {"name": "Python Programming", "description": "Python language and frameworks"},
                {"name": "Web Development", "description": "HTML, CSS, JavaScript, and web frameworks"},
                {"name": "Data Structures", "description": "Algorithms and data structures"},
                {"name": "Machine Learning", "description": "AI and machine learning concepts"}
            ],
            "Mathematics": [
                {"name": "Calculus", "description": "Differential and integral calculus"},
                {"name": "Linear Algebra", "description": "Vectors, matrices, and linear transformations"},
                {"name": "Statistics", "description": "Probability and statistical analysis"},
                {"name": "Number Theory", "description": "Properties of numbers and integers"}
            ],
            "History": [
                {"name": "Ancient History", "description": "Early civilizations and ancient empires"},
                {"name": "Medieval History", "description": "Middle Ages and medieval period"},
                {"name": "Modern History", "description": "Recent historical events and developments"},
                {"name": "Vietnam History", "description": "Vietnamese history and culture"}
            ],
            "Science": [
                {"name": "Physics", "description": "Physical laws and phenomena"},
                {"name": "Chemistry", "description": "Chemical reactions and molecular structures"},
                {"name": "Biology", "description": "Living organisms and life processes"},
                {"name": "Astronomy", "description": "Space, stars, and celestial bodies"}
            ],
            "Literature": [
                {"name": "Classic Literature", "description": "Timeless literary works"},
                {"name": "Modern Fiction", "description": "Contemporary novels and stories"},
                {"name": "Poetry", "description": "Poetic forms and analysis"},
                {"name": "Drama", "description": "Theatrical works and plays"}
            ]
        }
        
        for subject in created_subjects:
            if subject.name in categories_data:
                for cat_data in categories_data[subject.name]:
                    category = Category(
                        name=cat_data["name"],
                        description=cat_data["description"],
                        subject_id=subject.id,
                        user_id=test_user_id
                    )
                    db.add(category)
                    print(f"  ✅ Created category: {category.name} (in {subject.name})")
        
        db.commit()
        print("\n🎉 Sample data created successfully!")
        print(f"📚 Created {len(created_subjects)} subjects with categories")
        print("\n📋 Sample Data Summary:")
        print("=" * 50)
        for subject in created_subjects:
            print(f"📖 {subject.name} ({subject.color_theme} theme)")
            subject_categories = [cat for cat in subject.categories]
            for category in subject_categories:
                print(f"  📁 {category.name}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating sample data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main function to run the seeding script"""
    print("🌱 Starting data seeding for Document Service...")
    print("=" * 60)
    
    try:
        # Create sample data
        create_sample_data()
        
        print("\n🎉 Data seeding completed successfully!")
        print("\n💡 You can now test the application:")
        print("   - Web Frontend: http://localhost:3001")
        print("   - Document Service API: http://localhost:8002/docs")
        print("   - Login with: test@test.com / test123")
        
    except Exception as e:
        print(f"❌ Data seeding failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
