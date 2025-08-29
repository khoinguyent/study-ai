#!/usr/bin/env python3
"""
Script to create a test quiz with raw_json data for testing quiz sessions.
This creates a quiz with sample LLM-generated questions in the required format.
"""

import asyncio
import aiohttp
import json
import uuid

# Quiz service base URL
BASE_URL = "http://localhost:8004"

async def create_test_quiz():
    """Create a test quiz with raw_json data"""
    try:
        # Create a quiz with raw_json data in the LLM format
        quiz_data = {
            "title": "Test Quiz - Vietnam History",
            "description": "A test quiz with various question types",
            "questions": {
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question": "Who was the founder of the Nguyen Dynasty?",
                        "options": [
                            "Nguyen Hue",
                            "Nguyen Anh (Gia Long)",
                            "Tay Son brothers",
                            "Le Loi"
                        ],
                        "answer": 1,
                        "explanation": "Nguyen Anh, later known as Gia Long, founded the Nguyen Dynasty in 1802."
                    },
                    {
                        "type": "true_false",
                        "question": "The Tay Son Rebellion occurred in the 18th century.",
                        "answer": True,
                        "explanation": "The Tay Son Rebellion took place from 1771 to 1802."
                    },
                    {
                        "type": "fill_blank",
                        "question": "The capital of Vietnam during the Nguyen Dynasty was _____.",
                        "blanks": ["Hue"],
                        "explanation": "Hue served as the imperial capital of the Nguyen Dynasty."
                    },
                    {
                        "type": "short_answer",
                        "question": "What were the main causes of the Tay Son Rebellion?",
                        "rubric": {
                            "key_points": [
                                {"text": "corruption", "weight": 0.3, "aliases": ["greed", "dishonesty"]},
                                {"text": "peasant discontent", "weight": 0.4, "aliases": ["farmer anger", "rural unrest"]},
                                {"text": "foreign influence", "weight": 0.3, "aliases": ["external interference"]}
                            ],
                            "threshold": 0.6
                        }
                    }
                ]
            },
            "raw_json": {
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question": "Who was the founder of the Nguyen Dynasty?",
                        "options": [
                            "Nguyen Hue",
                            "Nguyen Anh (Gia Long)",
                            "Tay Son brothers",
                            "Le Loi"
                        ],
                        "answer": 1,
                        "explanation": "Nguyen Anh, later known as Gia Long, founded the Nguyen Dynasty in 1802.",
                        "metadata": {
                            "sources": ["vietnam_history_doc_1", "dynasty_records"]
                        }
                    },
                    {
                        "type": "true_false",
                        "question": "The Tay Son Rebellion occurred in the 18th century.",
                        "answer": True,
                        "explanation": "The Tay Son Rebellion took place from 1771 to 1802.",
                        "metadata": {
                            "sources": ["rebellion_timeline", "historical_records"]
                        }
                    },
                    {
                        "type": "fill_blank",
                        "question": "The capital of Vietnam during the Nguyen Dynasty was _____.",
                        "blanks": ["Hue"],
                        "explanation": "Hue served as the imperial capital of the Nguyen Dynasty.",
                        "metadata": {
                            "sources": ["capital_records", "geography_docs"]
                        }
                    },
                    {
                        "type": "short_answer",
                        "question": "What were the main causes of the Tay Son Rebellion?",
                        "rubric": {
                            "key_points": [
                                {"text": "corruption", "weight": 0.3, "aliases": ["greed", "dishonesty"]},
                                {"text": "peasant discontent", "weight": 0.4, "aliases": ["farmer anger", "rural unrest"]},
                                {"text": "foreign influence", "weight": 0.3, "aliases": ["external interference"]}
                            ],
                            "threshold": 0.6
                        },
                        "metadata": {
                            "sources": ["rebellion_analysis", "social_studies"]
                        }
                    }
                ]
            },
            "user_id": "test-user-1",
            "status": "published"
        }
        
        async with aiohttp.ClientSession() as session:
            # Create the quiz
            async with session.post(
                f"{BASE_URL}/quizzes",
                json=quiz_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Test quiz created: {data}")
                    return data.get("id")
                else:
                    print(f"❌ Quiz creation failed: {response.status}")
                    print(f"Response: {await response.text()}")
                    return None
    except Exception as e:
        print(f"❌ Quiz creation error: {e}")
        return None

async def main():
    """Main function"""
    print("🏗️ Creating Test Quiz for Session Testing")
    print("=" * 50)
    
    quiz_id = await create_test_quiz()
    if quiz_id:
        print(f"✅ Test quiz created with ID: {quiz_id}")
        print(f"📝 You can now use this quiz ID to test sessions:")
        print(f"   - Create session: POST /quizzes/{quiz_id}/sessions")
        print(f"   - View session: GET /quizzes/sessions/{{session_id}}/view")
        print(f"   - Save answers: POST /quizzes/sessions/{{session_id}}/answers")
        print(f"   - Submit session: POST /quizzes/sessions/{{session_id}}/submit")
    else:
        print("❌ Failed to create test quiz")

if __name__ == "__main__":
    asyncio.run(main())
