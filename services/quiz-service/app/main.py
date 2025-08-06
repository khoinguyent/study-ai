from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import httpx

from .database import get_db
from .models import Base, Quiz
from .schemas import QuizCreate, QuizResponse, QuizGenerationRequest
from .config import settings
from .services.quiz_generator import QuizGenerator

app = FastAPI(
    title="Quiz Service",
    description="AI-powered quiz generation service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
quiz_generator = QuizGenerator()

async def verify_auth_token(authorization: str = Depends(Header)):
    """Verify JWT token with auth service"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/verify",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()["user_id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "quiz-service"}

@app.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a new quiz based on user request and document context"""
    try:
        # Search for relevant document chunks
        async with httpx.AsyncClient() as client:
            search_response = await client.post(
                f"{settings.INDEXING_SERVICE_URL}/search",
                json={
                    "query": request.topic,
                    "limit": 10
                }
            )
            
            if search_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to search for relevant content"
                )
            
            search_results = search_response.json()
        
        # Generate quiz using AI
        quiz_content = await quiz_generator.generate_quiz(
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=search_results
        )
        
        # Save quiz to database
        quiz = Quiz(
            user_id=user_id,
            title=quiz_content["title"],
            topic=request.topic,
            difficulty=request.difficulty,
            questions=quiz_content["questions"],
            answers=quiz_content["answers"],
            explanations=quiz_content["explanations"]
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        return QuizResponse(
            id=quiz.id,
            title=quiz.title,
            topic=quiz.topic,
            difficulty=quiz.difficulty,
            num_questions=len(quiz.questions),
            created_at=quiz.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )

@app.get("/quizzes", response_model=List[QuizResponse])
async def list_quizzes(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get all quizzes for the authenticated user"""
    quizzes = db.query(Quiz).filter(Quiz.user_id == user_id).order_by(Quiz.created_at.desc()).all()
    
    return [
        QuizResponse(
            id=quiz.id,
            title=quiz.title,
            topic=quiz.topic,
            difficulty=quiz.difficulty,
            num_questions=len(quiz.questions),
            created_at=quiz.created_at
        )
        for quiz in quizzes
    ]

@app.get("/quizzes/{quiz_id}", response_model=dict)
async def get_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific quiz with all questions and answers"""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "topic": quiz.topic,
        "difficulty": quiz.difficulty,
        "questions": quiz.questions,
        "answers": quiz.answers,
        "explanations": quiz.explanations,
        "created_at": quiz.created_at
    }

@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a specific quiz"""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    db.delete(quiz)
    db.commit()
    
    return {"message": "Quiz deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 