"""
Leaf Quiz Service - FastAPI Application
Question generation using T5 transformers based on Leaf approach
"""
import asyncio
import time
import logging
import traceback
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
import httpx

from .database import get_db, create_tables
from .models import LeafQuiz, QuestionGenerationJob
from .schemas import (
    LeafQuizCreate, LeafQuizResponse, QuestionGenerationRequest,
    QuestionGenerationResponse, JobStatusResponse
)
from .config import settings
from .services.leaf_question_generator import LeafQuestionGenerator

# Initialize FastAPI app
app = FastAPI(
    title="Leaf Quiz Service",
    description="AI-powered quiz generation using T5 transformers (Leaf approach)",
    version="1.0.0"
)

# Initialize question generator
leaf_generator = LeafQuestionGenerator()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables and models on startup"""
    create_tables()
    await leaf_generator.initialize()
    logger.info("Leaf Quiz service started and initialized")


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
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
        return user_id
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "leaf-quiz-service",
        "model_initialized": leaf_generator.initialized
    }


@app.get("/test-models")
async def test_models():
    """Test if T5 models are working"""
    try:
        if not leaf_generator.initialized:
            await leaf_generator.initialize()
        
        # Test with a simple text
        test_text = "The capital of France is Paris. Paris is known for the Eiffel Tower."
        questions = await leaf_generator.generate_questions_from_text(test_text, 1)
        
        return {
            "status": "success",
            "message": "T5 models are working",
            "test_questions_generated": len(questions),
            "model_initialized": leaf_generator.initialized
        }
    except Exception as e:
        logger.error(f"Model test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Model test failed: {str(e)}",
            "model_initialized": leaf_generator.initialized
        }


# Background task for question generation
async def generate_questions_background(
    quiz_id: str, 
    source_text: str, 
    num_questions: int, 
    difficulty: str,
    user_id: str,
    topic: Optional[str] = None,
    subject_id: Optional[str] = None,
    category_id: Optional[str] = None,
    document_id: Optional[str] = None
):
    """Background task to generate questions using T5 models"""
    db = next(get_db())
    try:
        logger.info(f"Starting background question generation for quiz ID: {quiz_id}")
        
        # Update quiz status to processing
        quiz = db.query(LeafQuiz).filter(LeafQuiz.id == quiz_id).first()
        if quiz:
            quiz.status = "processing"
            quiz.questions = {"message": "Question generation in progress..."}
            db.commit()
        
        # Generate questions using T5 models
        start_time = time.time()
        questions = await leaf_generator.generate_questions_from_text(
            source_text=source_text,
            num_questions=num_questions,
            difficulty=difficulty
        )
        generation_time = int(time.time() - start_time)
        
        # Update quiz with generated content
        quiz = db.query(LeafQuiz).filter(LeafQuiz.id == quiz_id).first()
        if quiz:
            quiz.status = "completed"
            quiz.title = topic or f"Generated Quiz ({num_questions} questions)"
            quiz.description = f"Quiz generated from text using T5 transformers"
            quiz.questions = questions
            quiz.source_text = source_text
            quiz.generation_model = settings.question_generation_model
            quiz.generation_time = generation_time
            db.commit()
            logger.info(f"Question generation completed successfully for quiz ID: {quiz_id}")
        else:
            logger.error(f"Quiz not found for ID: {quiz_id}")
            
    except Exception as e:
        logger.error(f"Question generation failed for quiz ID {quiz_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update quiz with error message
        quiz = db.query(LeafQuiz).filter(LeafQuiz.id == quiz_id).first()
        if quiz:
            quiz.status = "failed"
            quiz.questions = {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            db.commit()
        else:
            logger.error(f"Quiz not found for ID: {quiz_id} when updating error")
    finally:
        db.close()


@app.post("/generate", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate questions from text using T5 transformers - async version"""
    start_time = time.time()
    
    try:
        # Create initial quiz record with "pending" status
        quiz = LeafQuiz(
            user_id=user_id,
            title=request.topic or f"Generated Quiz ({request.num_questions} questions)",
            description=f"Generating questions from text...",
            questions={"message": "Question generation pending..."},
            status="pending",
            source_text=request.source_text,
            subject_id=request.subject_id,
            category_id=request.category_id,
            document_id=request.document_id
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Start background task for question generation
        asyncio.create_task(
            generate_questions_background(
                quiz_id=quiz.id,
                source_text=request.source_text,
                num_questions=request.num_questions,
                difficulty=request.difficulty,
                user_id=user_id,
                topic=request.topic,
                subject_id=request.subject_id,
                category_id=request.category_id,
                document_id=request.document_id
            )
        )
        
        generation_time = time.time() - start_time
        
        return QuestionGenerationResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            questions_count=0,  # Will be updated when generation completes
            generation_time=generation_time,
            source_type="text",
            source_id=None,
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Question generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@app.get("/quizzes", response_model=List[LeafQuizResponse])
async def list_quizzes(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all quizzes for the user"""
    quizzes = db.query(LeafQuiz).filter(LeafQuiz.user_id == user_id).order_by(LeafQuiz.created_at.desc()).all()
    return quizzes


@app.get("/quizzes/{quiz_id}", response_model=LeafQuizResponse)
async def get_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID"""
    quiz = db.query(LeafQuiz).filter(
        and_(LeafQuiz.id == quiz_id, LeafQuiz.user_id == user_id)
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz


@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a quiz"""
    quiz = db.query(LeafQuiz).filter(
        and_(LeafQuiz.id == quiz_id, LeafQuiz.user_id == user_id)
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    db.delete(quiz)
    db.commit()
    
    return {"message": "Quiz deleted successfully"} 