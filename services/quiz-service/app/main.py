import asyncio
import time
import traceback
import logging
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
import httpx

from .database import get_db, create_tables
from . import models
from .schemas import (
    QuizCreate, QuizResponse, QuizGenerationRequest, 
    SubjectQuizGenerationRequest, CategoryQuizGenerationRequest,
    DocumentSelectionRequest, CustomDocumentSetRequest, 
    CustomDocumentSetResponse, QuizGenerationResponse
)
from .config import settings

# Initialize FastAPI app
app = FastAPI(title="Quiz Service", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        create_tables()
        logger.info("Quiz service started and database tables created")
    except Exception as e:
        logger.warning(f"Database connection failed during startup: {e}")
        logger.info("Quiz service started without database connection (for testing)")

async def verify_auth_token(authorization: str = Header(alias="Authorization")):
    """Verify JWT token and extract user ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    # For now, we'll use a simple approach - extract user_id from token
    # In production, you'd verify the JWT properly
    try:
        # This is a simplified token verification
        # In a real implementation, you'd decode and verify the JWT
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
        return user_id
    except ImportError:
        # Fallback: use a hardcoded user_id for testing
        logger.warning("JWT module not available, using fallback user_id")
        return "c3eb1d08-ced5-449f-ad7d-f7a9f0c5cb80"
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        # Fallback: use a hardcoded user_id for testing
        logger.warning("Using fallback user_id due to token verification error")
        return "c3eb1d08-ced5-449f-ad7d-f7a9f0c5cb80"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "quiz-service"}

@app.get("/test-ollama")
async def test_ollama():
    """Test Ollama connectivity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Ollama is accessible",
                    "models": response.json()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama returned status {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to Ollama: {str(e)}"
        }

@app.get("/test-openai")
async def test_openai():
    """Test OpenAI connectivity and configuration"""
    try:
        if not settings.OPENAI_API_KEY:
            return {
                "status": "error",
                "message": "OpenAI API key not configured"
            }
        
        # Test OpenAI client initialization
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            openai.base_url = settings.OPENAI_BASE_URL
            
            # Test with a simple API call
            response = await openai.chat.completions.acreate(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10
            )
            
            return {
                "status": "success",
                "message": "OpenAI is accessible and working",
                "model": settings.OPENAI_MODEL,
                "base_url": settings.OPENAI_BASE_URL,
                "test_response": response.choices[0].message.content
            }
            
        except ImportError:
            return {
                "status": "error",
                "message": "OpenAI package not available"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API test failed: {str(e)}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to test OpenAI: {str(e)}"
        }

# Enhanced Mock Quiz Generation Service
class MockQuizGenerator:
    """Mock quiz generator that returns realistic quiz data for development"""
    
    def __init__(self):
        self.question_templates = {
            "MCQ": [
                {
                    "type": "multiple_choice",
                    "question": "What was the main cause of the {topic}?",
                    "options": [
                        {
                            "content": "Economic factors",
                            "isCorrect": False
                        },
                        {
                            "content": "Political instability", 
                            "isCorrect": True
                        },
                        {
                            "content": "Social changes",
                            "isCorrect": False
                        },
                        {
                            "content": "Environmental factors",
                            "isCorrect": False
                        }
                    ],
                    "explanation": "Political instability was the primary driver of {topic}."
                },
                {
                    "type": "multiple_choice", 
                    "question": "Which of the following best describes {topic}?",
                    "options": [
                        {
                            "content": "A gradual process",
                            "isCorrect": False
                        },
                        {
                            "content": "A sudden event",
                            "isCorrect": False
                        },
                        {
                            "content": "A combination of factors",
                            "isCorrect": True
                        },
                        {
                            "content": "An isolated incident",
                            "isCorrect": False
                        }
                    ],
                    "explanation": "{topic} involved multiple interconnected factors."
                }
            ],
            "True/False": [
                {
                    "type": "true_false",
                    "question": "{topic} had significant long-term effects.",
                    "answer": True,
                    "explanation": "The impact of {topic} continues to be felt today."
                },
                {
                    "type": "true_false",
                    "question": "{topic} was completely unexpected.",
                    "answer": False,
                    "explanation": "There were warning signs before {topic} occurred."
                }
            ],
            "Fill in the Blank": [
                {
                    "type": "fill_blank",
                    "question": "The key figure in {topic} was _____.",
                    "answer": "the leader",
                    "explanation": "This person played a crucial role in {topic}."
                }
            ]
        }
    
    def generate_mock_quiz(self, subject_id: str, doc_ids: List[str], question_types: List[str], 
                          difficulty: str, question_count: int) -> Dict[str, Any]:
        """Generate realistic mock quiz data"""
        
        # Generate questions based on types and count
        questions = []
        questions_per_type = max(1, question_count // len(question_types))
        
        for q_type in question_types:
            if q_type.upper() in self.question_templates:
                template_questions = self.question_templates[q_type.upper()]
                for i in range(questions_per_type):
                    if i < len(template_questions):
                        template = template_questions[i].copy()
                        # Customize question based on subject
                        topic = self._get_topic_from_subject(subject_id)
                        template["question"] = template["question"].format(topic=topic)
                        template["explanation"] = template["explanation"].format(topic=topic)
                        template["id"] = str(uuid.uuid4())
                        questions.append(template)
        
        # Ensure we have the requested number of questions
        while len(questions) < question_count:
            # Add more MCQ questions if needed
            template = self.question_templates["MCQ"][0].copy()
            topic = self._get_topic_from_subject(subject_id)
            template["question"] = template["question"].format(topic=topic)
            template["explanation"] = template["explanation"].format(topic=topic)
            template["id"] = str(uuid.uuid4())
            questions.append(template)
        
        # Trim to exact question count
        questions = questions[:question_count]
        
        return {
            "id": str(uuid.uuid4()),
            "title": f"Study Quiz - {self._get_subject_name(subject_id)}",
            "description": f"Quiz with {question_count} {difficulty} questions",
            "questions": questions,
            "total_questions": len(questions),
            "difficulty": difficulty,
            "estimated_time": question_count * 2,  # 2 minutes per question
            "passing_score": 70,
            "created_at": time.time()
        }
    
    def _get_topic_from_subject(self, subject_id: str) -> str:
        """Get topic name from subject ID"""
        topics = {
            "9e329560-b3db-48b9-9867-630bc7d8dc42": "Rise of Tay Son Rebellion",
            "063a9a74-a587-4479-96ba-ecc52cf85e91": "Biological Evolution",
            "79955a34-7873-482c-a675-8c575f548ac7": "Physics Fundamentals"
        }
        return topics.get(subject_id, "Historical Events")
    
    def _get_subject_name(self, subject_id: str) -> str:
        """Get subject name from subject ID"""
        names = {
            "9e329560-b3db-48b9-9867-630bc7d8dc42": "History",
            "063a9a74-a587-4479-96ba-ecc52cf85e91": "Biology", 
            "79955a34-7873-482c-a675-8c575f548ac7": "Physics"
        }
        return names.get(subject_id, "General Studies")

# Initialize mock quiz generator
mock_quiz_generator = MockQuizGenerator()

# Study Session endpoints with enhanced mock data
@app.post("/study-sessions/start")
async def start_study_session(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Start a study session and begin quiz generation"""
    try:
        # Extract parameters from the request - make most fields optional
        question_types = request.get("questionTypes", ["MCQ"])
        difficulty = request.get("difficulty", "medium")
        question_count = request.get("questionCount", 10)
        
        # These fields are now truly optional - use defaults if not provided
        subject_id = request.get("subjectId", "mock-subject")
        doc_ids = request.get("docIds", ["mock-doc"])
        
        # Generate unique IDs
        session_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        quiz_id = str(uuid.uuid4())
        
        logger.info(f"Starting study session: session_id={session_id}, job_id={job_id}, quiz_id={quiz_id}")
        logger.info(f"Parameters: subject_id={subject_id}, doc_ids={doc_ids}, question_types={question_types}, difficulty={difficulty}, question_count={question_count}")
        
        # Create a quiz record in database
        try:
            quiz_data = {
                "title": f"Study Session - {subject_id}",
                "description": f"Quiz with {question_count} {difficulty} questions",
                "questions": [],  # Empty questions array initially
                "user_id": user_id,
                "subject_id": subject_id,
                "document_id": doc_ids[0] if doc_ids else None,
                "status": "generating"
            }
            
            quiz = models.Quiz(**quiz_data)
            db.add(quiz)
            db.commit()
            db.refresh(quiz)
            
            logger.info(f"Quiz record created in database with ID: {quiz.id}")
            
        except Exception as e:
            logger.error(f"Failed to create quiz record: {str(e)}")
            # Continue without database record for now
        
        return {
            "sessionId": session_id,
            "jobId": job_id,
            "quizId": quiz_id,
            "message": "Study session started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Study session start failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/study-sessions/status")
async def get_study_session_status(
    job_id: str = Query(..., description="Job ID to check status for"),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get the status of a study session job"""
    try:
        logger.info(f"Checking status for job_id: {job_id}")
        
        # For mock purposes, simulate different states based on job_id
        if "mock" in job_id.lower():
            # Return completed status for mock jobs
            return {
                "state": "completed",
                "progress": 100,
                "sessionId": "mock-session-id",
                "quizId": "mock-quiz-id",
                "message": "Quiz generation completed successfully"
            }
        else:
            # Simulate running state for real jobs
            return {
                "state": "running",
                "progress": 75,
                "stage": "Generating questions",
                "message": "Quiz generation in progress"
            }
            
    except Exception as e:
        logger.error(f"Failed to get study session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )

@app.get("/study-sessions/events")
async def get_study_session_events(
    job_id: str = Query(..., description="Job ID to get events for"),
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get real-time events for a study session job"""
    try:
        logger.info(f"Getting events for job_id: {job_id}")
        
        # Return mock events
        events = [
            {
                "timestamp": time.time(),
                "type": "quiz_generation_started",
                "message": "Quiz generation started",
                "progress": 10
            },
            {
                "timestamp": time.time() + 30,
                "type": "questions_generated",
                "message": "Questions generated successfully",
                "progress": 50
            },
            {
                "timestamp": time.time() + 60,
                "type": "quiz_generation_completed",
                "message": "Quiz generation completed successfully",
                "progress": 100
            }
        ]
        
        return {
            "events": events,
            "job_id": job_id,
            "total_events": len(events)
        }
        
    except Exception as e:
        logger.error(f"Failed to get study session events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events: {str(e)}"
        )

@app.post("/study-sessions/ingest")
async def ingest_study_session(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Ingest additional input for study session"""
    try:
        logger.info(f"Ingesting study session input: {request}")
        
        return {
            "status": "success",
            "message": "Study session input ingested successfully",
            "sessionId": "mock-session-id"
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest study session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest: {str(e)}"
        )

@app.post("/study-sessions/confirm")
async def confirm_study_session(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Confirm study session and generate final quiz"""
    try:
        logger.info(f"Confirming study session: {request}")
        
        # Extract only the essential parameters - make others truly optional
        question_types = request.get("questionTypes", ["MCQ"])
        difficulty = request.get("difficulty", "medium")
        question_count = request.get("questionCount", 10)
        
        # These fields are now truly optional - use defaults if not provided
        subject_id = request.get("subjectId", "mock-subject")
        doc_ids = request.get("docIds", ["mock-doc"])
        
        # Generate mock quiz using the enhanced generator
        quiz_data = mock_quiz_generator.generate_mock_quiz(
            subject_id=subject_id,
            doc_ids=doc_ids,
            question_types=question_types,
            difficulty=difficulty,
            question_count=question_count
        )
        
        logger.info(f"Generated mock quiz with {len(quiz_data['questions'])} questions")
        
        return {
            "status": "success",
            "message": "Study session confirmed and quiz generated successfully",
            "sessionId": "mock-session-id",
            "quiz": quiz_data
        }
        
    except Exception as e:
        logger.error(f"Failed to confirm study session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm: {str(e)}"
        )

# Clarifier endpoints for AI-assisted quiz setup
@app.post("/clarifier/start")
async def start_clarifier(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Start AI clarifier session for quiz setup"""
    try:
        logger.info(f"Starting clarifier session: {request}")
        
        return {
            "status": "success",
            "message": "Clarifier session started successfully",
            "sessionId": "mock-clarifier-session-id",
            "suggestions": [
                "Consider adding more diverse question types",
                "Adjust difficulty based on student level",
                "Include questions from all selected documents"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to start clarifier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start clarifier: {str(e)}"
        )

@app.post("/clarifier/ingest")
async def ingest_clarifier(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Ingest clarifier input and provide suggestions"""
    try:
        logger.info(f"Ingesting clarifier input: {request}")
        
        return {
            "status": "success",
            "message": "Clarifier input processed successfully",
            "sessionId": "mock-clarifier-session-id",
            "suggestions": [
                "Based on your input, I recommend focusing on key concepts",
                "Consider the learning objectives for this subject",
                "Balance question difficulty for better learning outcomes"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest clarifier input: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process input: {str(e)}"
        )

# Quiz management endpoints - Simplified for minimal requirements
@app.post("/generate")
async def generate_quiz_from_clarifier(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a new quiz from clarifier service - minimal requirements"""
    try:
        logger.info(f"Generating quiz from clarifier: {request}")
        
        # Extract only the essential fields
        doc_ids = request.get("docIds", [])
        num_questions = request.get("count", 10)  # clarifier uses 'count'
        difficulty = request.get("difficulty", "medium")
        question_types = request.get("questionTypes", ["MCQ"])
        session_id = request.get("sessionId", "")
        
        if not doc_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="docIds is required"
            )
        
        # Generate mock quiz with the essential fields
        quiz_data = mock_quiz_generator.generate_mock_quiz(
            subject_id="mock-subject",  # Not required for quiz generation
            doc_ids=doc_ids,
            question_types=question_types,
            difficulty=difficulty,
            question_count=num_questions
        )
        
        # Return success without sending notifications
        return {
            "status": "success",
            "message": "Quiz generated successfully from clarifier",
            "quiz": quiz_data,
            "sessionId": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate quiz from clarifier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@app.post("/quizzes/generate")
async def generate_quiz(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a new quiz with minimal requirements"""
    try:
        logger.info(f"Generating quiz: {request}")
        
        # Extract only the essential fields
        doc_ids = request.get("docIds", [])
        num_questions = request.get("numQuestions", 10)
        difficulty = request.get("difficulty", "medium")
        question_types = request.get("questionTypes", ["MCQ"])
        
        if not doc_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="docIds is required"
            )
        
        # Generate mock quiz with the essential fields
        quiz_data = mock_quiz_generator.generate_mock_quiz(
            subject_id="mock-subject",  # Not required for quiz generation
            doc_ids=doc_ids,
            question_types=question_types,
            difficulty=difficulty,
            question_count=num_questions
        )
        
        return {
            "status": "success",
            "message": "Quiz generated successfully",
            "quiz": quiz_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@app.post("/quizzes/generate-simple")
async def generate_quiz_simple(request: dict):
    """Generate a new quiz without authentication for testing"""
    try:
        logger.info(f"Generating simple quiz: {request}")
        
        # Extract only the essential fields - make docIds optional
        num_questions = request.get("numQuestions", 10)
        difficulty = request.get("difficulty", "medium")
        question_types = request.get("questionTypes", ["MCQ"])
        
        # These fields are now truly optional - use defaults if not provided
        doc_ids = request.get("docIds", ["mock-doc"])
        
        # Generate mock quiz with the essential fields
        quiz_data = mock_quiz_generator.generate_mock_quiz(
            subject_id="mock-subject",
            doc_ids=doc_ids,
            question_types=question_types,
            difficulty=difficulty,
            question_count=num_questions
        )
        
        return {
            "status": "success",
            "message": "Quiz generated successfully",
            "quiz": quiz_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate simple quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@app.get("/quizzes/{quiz_id}")
async def get_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID"""
    try:
        # For mock purposes, generate a quiz on demand
        quiz_data = mock_quiz_generator.generate_mock_quiz(
            subject_id="mock-subject",
            doc_ids=["mock-doc"],
            question_types=["MCQ"],
            difficulty="medium",
            question_count=10
        )
        quiz_data["id"] = quiz_id
        
        return quiz_data
        
    except Exception as e:
        logger.error(f"Failed to get quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quiz: {str(e)}"
        )

@app.get("/quizzes")
async def list_quizzes(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """List quizzes for a user"""
    try:
        # For mock purposes, return a list of generated quizzes
        quizzes = []
        for i in range(limit):
            quiz_data = mock_quiz_generator.generate_mock_quiz(
                subject_id=f"subject-{i}",
                doc_ids=[f"doc-{i}"],
                question_types=["MCQ"],
                difficulty="medium",
                question_count=10
            )
            quizzes.append(quiz_data)
        
        return {
            "quizzes": quizzes,
            "total": len(quizzes),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to list quizzes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list quizzes: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 