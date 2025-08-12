import asyncio
import time
import traceback
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
import httpx

from .database import get_db, create_tables
from .models import Quiz, CustomDocumentSet
from .schemas import (
    QuizCreate, QuizResponse, QuizGenerationRequest, 
    SubjectQuizGenerationRequest, CategoryQuizGenerationRequest,
    DocumentSelectionRequest, CustomDocumentSetRequest, 
    CustomDocumentSetResponse, QuizGenerationResponse
)
from .config import settings
from .services.quiz_generator import QuizGenerator

# Initialize FastAPI app
app = FastAPI(title="Quiz Service", version="1.0.0")

# Initialize quiz generator
quiz_generator = QuizGenerator()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()
    logger.info("Quiz service started and database tables created")

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

# Background task for quiz generation
async def generate_quiz_background(quiz_id: str, topic: str, difficulty: str, num_questions: int, context_chunks: List[dict], source_type: str, source_id: str, user_id: str):
    """Background task to generate quiz content"""
    db = next(get_db())
    try:
        logger.info(f"Starting background quiz generation for quiz ID: {quiz_id}")
        
        # Update quiz status to processing
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            quiz.status = "processing"
            quiz.questions = {"message": "Quiz generation in progress..."}
            db.commit()
        
        # Generate quiz using AI
        quiz_content = await quiz_generator.generate_quiz_from_context(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            context_chunks=context_chunks,
            source_type=source_type,
            source_id=source_id
        )
        
        # Update quiz with generated content
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            quiz.status = "completed"
            quiz.title = quiz_content.get("title", "Generated Quiz")
            quiz.description = quiz_content.get("description", "")
            quiz.questions = quiz_content.get("questions", [])
            db.commit()
            logger.info(f"Quiz generation completed successfully for quiz ID: {quiz_id}")
        else:
            logger.error(f"Quiz not found for ID: {quiz_id}")
            
    except Exception as e:
        logger.error(f"Quiz generation failed for quiz ID {quiz_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update quiz with error message
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
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

@app.post("/generate/selected-documents", response_model=QuizGenerationResponse)
async def generate_quiz_from_selected_documents(
    request: DocumentSelectionRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a quiz from specific selected documents - async version"""
    start_time = time.time()
    
    try:
        # Skip document validation for now - we'll trust the user_id from the token
        # TODO: Implement proper document ownership validation
        
        # Get context from all selected documents
        all_context_chunks = []
        for doc_id in request.document_ids:
            async with httpx.AsyncClient() as client:
                context_response = await client.get(
                    f"{settings.INDEXING_SERVICE_URL}/chunks/{doc_id}"
                )
                
                if context_response.status_code == 200:
                    chunks = context_response.json()
                    all_context_chunks.extend(chunks)
        
        if not all_context_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content found in selected documents"
            )
        
        # Create initial quiz record with "pending" status
        quiz = Quiz(
            user_id=user_id,
            title=f"Quiz about {request.topic}",
            description=f"Generating quiz about {request.topic}...",
            questions={"message": "Quiz generation pending..."},
            status="pending"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Start background task for quiz generation
        asyncio.create_task(
            generate_quiz_background(
                quiz_id=quiz.id,
                topic=request.topic,
                difficulty=request.difficulty,
                num_questions=request.num_questions,
                context_chunks=all_context_chunks,
                source_type="selected_documents",
                source_id=",".join(request.document_ids),
                user_id=user_id
            )
        )
        
        generation_time = time.time() - start_time
        
        return QuizGenerationResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            questions_count=0,  # Will be updated when generation completes
            generation_time=generation_time,
            source_type="selected_documents",
            source_id=",".join(request.document_ids),
            documents_used=request.document_ids,
            status="pending"
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Quiz generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Re-raise the original exception to see the full error
        raise

@app.post("/generate/document-set/{set_id}", response_model=QuizGenerationResponse)
async def generate_quiz_from_custom_document_set(
    set_id: str,
    request: QuizGenerationRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a quiz from a custom document set"""
    start_time = time.time()
    
    try:
        # Get the custom document set
        doc_set = db.query(CustomDocumentSet).filter(
            CustomDocumentSet.id == set_id,
            CustomDocumentSet.user_id == user_id
        ).first()
        
        if not doc_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document set not found"
            )
        
        # Get context from all documents in the set
        all_context_chunks = []
        for doc_id in doc_set.document_ids:
            async with httpx.AsyncClient() as client:
                context_response = await client.get(
                    f"{settings.INDEXING_SERVICE_URL}/chunks/{doc_id}"
                )
                
                if context_response.status_code == 200:
                    chunks = context_response.json()
                    all_context_chunks.extend(chunks)
        
        if not all_context_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content found in document set"
            )
        
        # Use document set name as topic if not provided
        topic = request.topic or doc_set.name
        
        # Generate quiz using AI with document set context
        quiz_content = await quiz_generator.generate_quiz_from_context(
            topic=topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=all_context_chunks,
            source_type="custom_document_set",
            source_id=str(set_id)
        )
        
        # Save quiz to database
        quiz = Quiz(
            user_id=user_id,
            title=quiz_content["title"],
            description=quiz_content.get("description"),
            questions=quiz_content["questions"],
            status="draft"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        generation_time = time.time() - start_time
        
        return QuizGenerationResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            questions_count=len(quiz.questions),
            generation_time=generation_time,
            source_type="custom_document_set",
            source_id=str(set_id),
            documents_used=doc_set.document_ids
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )

@app.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a new quiz based on user request and document context"""
    start_time = time.time()
    
    try:
        # Determine search endpoint based on request
        if request.subject_id and request.use_only_subject_content:
            # Search within subject
            search_response = await httpx.AsyncClient().post(
                f"{settings.INDEXING_SERVICE_URL}/search/subject",
                json={
                    "query": request.topic,
                    "subject_id": request.subject_id,
                    "limit": 10
                }
            )
        elif request.category_id and request.use_only_subject_content:
            # Search within category
            search_response = await httpx.AsyncClient().post(
                f"{settings.INDEXING_SERVICE_URL}/search/category",
                json={
                    "query": request.topic,
                    "category_id": request.category_id,
                    "limit": 10
                }
            )
        else:
            # General search
            search_response = await httpx.AsyncClient().post(
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
        
        # Create initial quiz record with "pending" status
        from datetime import datetime
        current_time = datetime.utcnow()
        
        quiz = Quiz(
            user_id=user_id,
            title=f"Quiz about {request.topic}",
            description=f"Generating quiz about {request.topic}...",
            questions={"message": "Quiz generation pending..."},
            document_id=request.document_id,
            subject_id=request.subject_id,
            category_id=request.category_id,
            status="pending"
        )
        
        # Set timestamps manually since SQLAlchemy onupdate doesn't work for new records
        quiz.created_at = current_time
        quiz.updated_at = current_time
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Start background task for quiz generation using Celery
        from .tasks import generate_quiz_background_task
        
        # Enqueue the task
        task = generate_quiz_background_task.delay(
            quiz_id=quiz.id,
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=search_results,
            source_type="general_search",
            source_id=request.subject_id or request.category_id or "general",
            user_id=user_id
        )
        
        generation_time = time.time() - start_time
        
        # Return quiz generation response instead of the quiz itself
        from .schemas import QuizGenerationResponse
        return QuizGenerationResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            questions_count=0,  # Will be updated when generation completes
            generation_time=generation_time,
            source_type="general_search",
            source_id=request.subject_id or request.category_id or "general",
            documents_used=[request.document_id] if request.document_id else None,
            status="pending",
            task_id=task.id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )

@app.post("/generate/subject", response_model=QuizGenerationResponse)
async def generate_subject_quiz(
    request: SubjectQuizGenerationRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a quiz based on a specific subject's content"""
    start_time = time.time()
    
    try:
        # Get subject information
        async with httpx.AsyncClient() as client:
            subject_response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/subjects/{request.subject_id}"
            )
            
            if subject_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found"
                )
            
            subject = subject_response.json()
        
        # Use subject name as topic if not provided
        topic = request.topic or subject["name"]
        
        # Get context from indexing service
        async with httpx.AsyncClient() as client:
            context_response = await client.get(
                f"{settings.INDEXING_SERVICE_URL}/chunks/subject/{request.subject_id}"
            )
            
            if context_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get subject context"
                )
            
            context_chunks = context_response.json()
        
        # Generate quiz using AI with subject context
        quiz_content = await quiz_generator.generate_quiz_from_context(
            topic=topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=context_chunks,
            source_type="subject",
            source_id=str(request.subject_id)
        )
        
        # Save quiz to database
        quiz = Quiz(
            user_id=user_id,
            title=quiz_content["title"],
            description=quiz_content.get("description"),
            questions=quiz_content["questions"],
            subject_id=request.subject_id,
            status="draft"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        generation_time = time.time() - start_time
        
        return QuizGenerationResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            questions_count=len(quiz.questions),
            generation_time=generation_time,
            source_type="subject",
            source_id=str(request.subject_id)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subject quiz generation failed: {str(e)}"
        )

@app.post("/generate/category", response_model=QuizGenerationResponse)
async def generate_category_quiz(
    request: CategoryQuizGenerationRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a quiz based on a specific category's content"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting category quiz generation for category_id: {request.category_id}")
        
        # Get category information
        logger.info("Getting category information...")
        async with httpx.AsyncClient() as client:
            category_response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/categories/{request.category_id}",
                headers={"Authorization": f"Bearer {user_id}"}
            )
            
            if category_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            category = category_response.json()
            logger.info(f"Category found: {category['name']}")
        
        # Use category name as topic if not provided
        topic = request.topic or category["name"]
        logger.info(f"Using topic: {topic}")
        
        # Get context from indexing service
        logger.info("Getting context from indexing service...")
        async with httpx.AsyncClient() as client:
            context_response = await client.get(
                f"{settings.INDEXING_SERVICE_URL}/chunks/category/{request.category_id}"
            )
            
            if context_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get category context"
                )
            
            context_chunks = context_response.json()
            logger.info(f"Retrieved {len(context_chunks)} context chunks")
        
        # Generate quiz using AI with category context
        logger.info("Generating quiz using AI...")
        quiz_content = await quiz_generator.generate_quiz_from_context(
            topic=topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=context_chunks,
            source_type="category",
            source_id=str(request.category_id)
        )
        logger.info("Quiz content generated successfully")
        
        # Save quiz to database
        logger.info("Saving quiz to database...")
        quiz = Quiz(
            user_id=user_id,
            title=quiz_content["title"],
            description=quiz_content.get("description"),
            questions=quiz_content["questions"],
            category_id=request.category_id,
            status="draft"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        logger.info(f"Quiz saved with ID: {quiz.id}")
        
        generation_time = time.time() - start_time
        
        return QuizGenerationResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            questions_count=len(quiz.questions),
            generation_time=generation_time,
            source_type="category",
            source_id=str(request.category_id)
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Category quiz generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Category quiz generation failed: {str(e)}"
        )

@app.get("/quizzes", response_model=List[QuizResponse])
async def list_quizzes(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all quizzes for the user"""
    quizzes = db.query(Quiz).filter(Quiz.user_id == user_id).order_by(Quiz.created_at.desc()).all()
    return quizzes

@app.get("/quizzes/subject/{subject_id}", response_model=List[QuizResponse])
async def list_subject_quizzes(
    subject_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all quizzes for a specific subject"""
    quizzes = db.query(Quiz).filter(
        Quiz.user_id == user_id,
        Quiz.subject_id == subject_id
    ).all()
    return quizzes

@app.get("/quizzes/category/{category_id}", response_model=List[QuizResponse])
async def list_category_quizzes(
    category_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all quizzes for a specific category"""
    quizzes = db.query(Quiz).filter(
        Quiz.user_id == user_id,
        Quiz.category_id == category_id
    ).all()
    return quizzes

@app.get("/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID"""
    quiz = db.query(Quiz).filter(
        and_(Quiz.id == quiz_id, Quiz.user_id == user_id)
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz

@app.put("/quizzes/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: str,
    quiz_update: QuizCreate,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Update a quiz"""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    for field, value in quiz_update.dict(exclude_unset=True).items():
        setattr(quiz, field, value)
    
    db.commit()
    db.refresh(quiz)
    return quiz

@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a quiz"""
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