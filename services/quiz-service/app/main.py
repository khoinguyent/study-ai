import asyncio
import time
import traceback
import logging
import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Header, Query, Request
import uuid as _uuid
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_
import httpx
import random
from datetime import datetime

from .database import get_db, create_tables
from . import models
from .schemas import (
    QuizCreate, QuizResponse, QuizGenerationRequest, 
    SubjectQuizGenerationRequest, CategoryQuizGenerationRequest,
    DocumentSelectionRequest, CustomDocumentSetRequest, 
    CustomDocumentSetResponse, QuizGenerationResponse
)
import os
from .api_quiz_sessions import router as quiz_sessions_router
from .api_quiz_sessions_stream import router as quiz_sessions_stream_router

# Initialize FastAPI app
app = FastAPI(title="Quiz Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Register routers for quiz sessions creation and SSE streaming
app.include_router(quiz_sessions_router)
app.include_router(quiz_sessions_stream_router)

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
        # Try PyJWT first, fallback to simple token parsing
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
        except AttributeError:
            # Fallback for different JWT library
            import base64
            import json
            parts = token.split('.')
            if len(parts) == 3:
                payload_str = base64.b64decode(parts[1] + '==').decode('utf-8')
                payload = json.loads(payload_str)
            else:
                raise Exception("Invalid JWT token format")
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
            response = await client.get(f"{os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')}/api/tags")
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
        logger.info("Testing OpenAI configuration...")
        
        # Check if OpenAI is configured
        if not os.getenv('OPENAI_API_KEY'):
            return {
                "status": "error",
                "message": "OpenAI API key not configured",
                "config": {
                    "api_key": "NOT_SET",
                    "base_url": os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                    "model": os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
                }
            }
        
        # Try to initialize the OpenAI provider
        try:
            from .services.quiz_generator import QuizGenerator
            quiz_generator = QuizGenerator()
            
            if quiz_generator.provider and quiz_generator.provider.name == "openai":
                return {
                    "status": "success",
                    "message": "OpenAI provider initialized successfully",
                    "config": {
                        "api_key": f"{os.getenv('OPENAI_API_KEY', '')[:8]}...",
                        "base_url": os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                        "model": os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                        "strategy": quiz_generator.strategy
                    }
                }
            else:
                return {
                    "status": "warning",
                    "message": "OpenAI provider not available",
                    "config": {
                        "api_key": f"{os.getenv('OPENAI_API_KEY', '')[:8]}...",
                        "base_url": os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                        "model": os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                        "strategy": quiz_generator.strategy,
                        "provider": quiz_generator.provider.name if quiz_generator.provider else "none"
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to test OpenAI provider: {e}")
            return {
                "status": "error",
                "message": f"Failed to initialize OpenAI provider: {str(e)}",
                "config": {
                    "api_key": f"{os.getenv('OPENAI_API_KEY', '')[:8]}...",
                    "base_url": os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                    "model": os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
                }
            }
            
    except Exception as e:
        logger.error(f"OpenAI test failed: {e}")
        return {
            "status": "error",
            "message": f"OpenAI test failed: {str(e)}"
        }

# Mock quiz generator removed - system now only uses real AI providers
    

    

    


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
        
        # Generate unique IDs - use same ID for job and quiz to match SSE endpoint
        session_id = str(uuid.uuid4())
        quiz_id = str(uuid.uuid4())
        job_id = quiz_id  # Use quiz_id as job_id so SSE endpoint can find the quiz
        
        logger.info(f"Starting study session: session_id={session_id}, job_id={job_id}, quiz_id={quiz_id}")
        logger.info(f"Parameters: subject_id={subject_id}, doc_ids={doc_ids}, question_types={question_types}, difficulty={difficulty}, question_count={question_count}")
        
        # Create a quiz record in database
        try:
            quiz_data = {
                "id": quiz_id,  # Use the generated quiz_id
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
    """Server-Sent Events stream for study session job progress."""
    try:
        logger.info(f"Getting events for job_id: {job_id}")

        async def event_generator():
            # Started - running state
            yield f"data: {json.dumps({'state': 'running', 'progress': 0, 'stage': 'Starting quiz generation', 'message': 'Initializing quiz generation process'})}\n\n"
            await asyncio.sleep(0.5)
            # Mid progress
            yield f"data: {json.dumps({'state': 'running', 'progress': 50, 'stage': 'Generating questions', 'message': 'Creating quiz questions from selected documents'})}\n\n"
            await asyncio.sleep(0.5)
            
            # Get the actual quiz from database using job_id
            quiz = db.query(models.Quiz).filter(models.Quiz.id == job_id).first()
            if quiz:
                # Use actual quiz data
                yield f"data: {json.dumps({'state': 'completed', 'progress': 100, 'sessionId': f'session-{quiz.id}', 'quizId': str(quiz.id)})}\n\n"
            else:
                # Fallback to mock data if quiz not found
                yield f"data: {json.dumps({'state': 'completed', 'progress': 100, 'sessionId': f'session-{job_id}', 'quizId': job_id})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

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
        
        # This endpoint now requires real AI generation - no mock fallback
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Study session confirmation requires real AI generation. Use /quizzes/generate endpoint instead."
        )
        
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
        
        # This endpoint now requires real AI generation - no mock fallback
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Clarifier quiz generation requires real AI generation. Use /quizzes/generate endpoint instead."
        )
        
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
    request_id = f"quiz_gen_{int(time.time())}_{random.randint(1000, 9999)}"
    
    logger.info(f"🚀 [BACKEND] Quiz generation request received: {request_id}", extra={
        "request_id": request_id,
        "user_id": user_id,
        "request_data": request,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/quizzes/generate",
        "method": "POST"
    })
    
    try:
        # Extract only the essential fields
        doc_ids = request.get("docIds", [])
        num_questions = request.get("numQuestions", 10)
        difficulty = request.get("difficulty", "medium")
        question_types = request.get("questionTypes", ["MCQ"])
        
        logger.info(f"📋 [BACKEND] Extracted quiz parameters: {request_id}", extra={
            "request_id": request_id,
            "doc_ids": doc_ids,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": question_types,
            "user_id": user_id
        })
        
        if not doc_ids:
            logger.error(f"❌ [BACKEND] Missing docIds in request: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "request": request
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="docIds is required"
            )
        
        # Notify: quiz generation started
        try:
            from shared.event_publisher import EventPublisher
            EventPublisher().publish_user_notification(
                user_id=user_id,
                notification_type="quiz_generation",
                title="Generating quiz…",
                message="We'll notify you when it's ready.",
                metadata={
                    "status": "processing",
                    "stage": "started"
                }
            )
            EventPublisher().publish_task_status_update(
                user_id=user_id,
                task_id=request_id,
                task_type="quiz_generation",
                status="started",
                progress=0,
                message="Quiz generation started",
                service_name="quiz-service"
            )
        except Exception:
            pass

        # Generate real quiz using AI providers instead of mock data
        logger.info(f"🤖 [BACKEND] Starting AI-powered quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "doc_count": len(doc_ids)
        })
        
        # Initialize the real quiz generator
        try:
            from .services.quiz_generator import QuizGenerator
            quiz_generator = QuizGenerator()
            logger.info(f"✅ [BACKEND] QuizGenerator initialized successfully: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "strategy": quiz_generator.strategy,
                "provider": getattr(quiz_generator, 'provider', None),
                "openai_configured": bool(quiz_generator.openai_api_key),
                "ollama_configured": bool(quiz_generator.ollama_url),
                "huggingface_configured": bool(quiz_generator.huggingface_token)
            })
        except Exception as e:
            logger.error(f"❌ [BACKEND] Failed to initialize QuizGenerator: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            # Fail if no AI provider is available - no mock fallback
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize AI quiz generator: {str(e)}"
            )
        
        # Fetch real chunks from indexing-service for provided doc IDs
        context_chunks: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                for d_id in doc_ids:
                    try:
                        url = f"{os.getenv('INDEXING_SERVICE_URL', 'http://indexing-service:8003')}/chunks/{d_id}"
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json() or []
                            for ch in data:
                                # Normalize to expected shape
                                context_chunks.append({
                                    "content": ch.get("content", ""),
                                    "metadata": {
                                        "document_id": ch.get("document_id", d_id),
                                        "chunk_index": ch.get("chunk_index")
                                    }
                                })
                        else:
                            logger.warning(f"[BACKEND] Failed to fetch chunks for {d_id}: {resp.status_code}")
                    except Exception as fe:
                        logger.warning(f"[BACKEND] Error fetching chunks for {d_id}: {fe}")
        except Exception as fetch_err:
            logger.warning(f"[BACKEND] Chunk fetch error: {fetch_err}")

        # Fallback if no chunks were found
        if not context_chunks:
            context_chunks = [
                {
                    "content": "No chunks found for documents. Use general study instructions.",
                    "metadata": {"source": "fallback", "document_id": doc_ids[0] if doc_ids else "unknown"}
                }
            ]

        # Truncate chunks to fit within OpenAI's token limit (approximately 16K tokens)
        # Rough estimate: 1 token ≈ 4 characters, so 16K tokens ≈ 64K characters
        MAX_CONTEXT_CHARS = 60000  # Conservative limit to stay well under token limit
        
        if context_chunks:
            total_chars = sum(len(chunk["content"]) for chunk in context_chunks)
            if total_chars > MAX_CONTEXT_CHARS:
                logger.info(f"📏 [BACKEND] Truncating chunks from {total_chars} to {MAX_CONTEXT_CHARS} characters: {request_id}")
                
                # Sort chunks by length and keep the most relevant ones
                context_chunks.sort(key=lambda x: len(x["content"]), reverse=True)
                
                truncated_chunks = []
                current_chars = 0
                
                for chunk in context_chunks:
                    chunk_content = chunk["content"]
                    if current_chars + len(chunk_content) <= MAX_CONTEXT_CHARS:
                        truncated_chunks.append(chunk)
                        current_chars += len(chunk_content)
                    else:
                        # Truncate this chunk to fit
                        remaining_chars = MAX_CONTEXT_CHARS - current_chars
                        if remaining_chars > 100:  # Only add if we have meaningful content
                            truncated_chunk = chunk.copy()
                            truncated_chunk["content"] = chunk_content[:remaining_chars] + "..."
                            truncated_chunks.append(truncated_chunk)
                            current_chars = MAX_CONTEXT_CHARS
                        break
                
                context_chunks = truncated_chunks
                logger.info(f"✅ [BACKEND] Truncated to {len(context_chunks)} chunks with {current_chars} characters: {request_id}")

        logger.info(f"📚 [BACKEND] Using context chunks for quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "doc_ids": doc_ids,
            "chunk_count": len(context_chunks),
            "total_chars": sum(len(chunk["content"]) for chunk in context_chunks),
            "chunk_preview": (context_chunks[0]["content"][:100] + "...") if context_chunks else "No chunks"
        })
        
        # Generate the quiz using the AI provider or fallback to mock
        start_time = time.time()
        if quiz_generator:
            try:
                quiz_data = await quiz_generator.generate_quiz_from_context(
                    topic="Document-based Quiz",
                    difficulty=difficulty,
                    num_questions=num_questions,
                    context_chunks=context_chunks,
                    source_type="document",
                    source_id=doc_ids[0] if doc_ids else "unknown",
                    allowed_types=question_types,
                    counts_by_type={qtype: num_questions // len(question_types) for qtype in question_types}
                )
                generation_time = time.time() - start_time
                
                logger.info(f"✅ [BACKEND] AI quiz generation completed successfully: {request_id}", extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "generation_time": f"{generation_time:.2f}s",
                    "question_count": len(quiz_data.get('questions', [])),
                    "quiz_id": quiz_data.get('id'),
                    "ai_provider": quiz_data.get('provider', 'unknown')
                })
                
            except Exception as e:
                logger.error(f"❌ [BACKEND] AI quiz generation failed: {request_id}", extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
                # Fail if AI generation fails - no mock fallback
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI quiz generation failed: {str(e)}"
                )
        
        # Persist quiz to database
        try:
            db_quiz_id = str(uuid.uuid4())
            from .models.quiz import Quiz as QuizModel
            quiz_record = QuizModel(
                id=db_quiz_id,
                title=quiz_data.get("title", "Generated Quiz"),
                description=quiz_data.get("description", None),
                questions={"questions": quiz_data.get("questions", [])},
                user_id=user_id,
                document_id=doc_ids[0] if doc_ids else None,
                subject_id=None,
                category_id=None,
                status="generated",
            )
            db.add(quiz_record)
            db.commit()
            logger.info(
                f"🗄️ [BACKEND] Quiz persisted to DB: {request_id}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "db_quiz_id": db_quiz_id,
                    "question_count": len(quiz_data.get("questions", [])),
                },
            )
        except Exception as persist_error:
            logger.error(
                f"❌ [BACKEND] Failed to persist quiz: {request_id}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(persist_error),
                },
            )
        
        response_data = {
            "status": "success",
            "message": "Quiz generated successfully",
            "job_id": db_quiz_id,  # Use the database-generated quiz ID
            "quiz_id": db_quiz_id,  # Also include quiz_id for clarity
            "quiz": quiz_data
        }
        
        logger.info(f"📤 [BACKEND] Sending quiz generation response: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "response_status": "success",
            "response_size": len(str(response_data))
        })

        # Notify: quiz generated and ready with open button (URL to be finalized)
        try:
            from shared.event_publisher import EventPublisher
            EventPublisher().publish_task_status_update(
                user_id=user_id,
                task_id=request_id,
                task_type="quiz_generation",
                status="completed",
                progress=100,
                message="Quiz generated successfully",
                service_name="quiz-service"
            )
            EventPublisher().publish_user_notification(
                user_id=user_id,
                notification_type="quiz_ready",
                title="Quiz ready",
                message="Successfully generated — open it when you're ready.",
                metadata={
                    "actionText": "Open",
                    "href": f"/study-session/{db_quiz_id}/quiz"
                }
            )
            logger.info(f"📢 [BACKEND] Published quiz ready notification: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "quiz_id": db_quiz_id,
                "notification_type": "quiz_ready"
            })
        except Exception as e:
            logger.error(f"❌ [BACKEND] Failed to publish notification events: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
        
        return response_data
        
    except HTTPException:
        logger.error(f"❌ [BACKEND] HTTP exception in quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "exception_type": "HTTPException"
        })
        raise
    except Exception as e:
        logger.error(f"💥 [BACKEND] Unexpected error in quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })
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
        
        # This endpoint now requires real AI generation - no mock fallback
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Simple quiz generation requires real AI generation. Use /quizzes/generate endpoint instead."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate simple quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@app.post("/quizzes/generate-real")
async def generate_quiz_real(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a real quiz using AI providers (OpenAI, Ollama, HuggingFace)"""
    request_id = f"quiz_real_{int(time.time())}_{random.randint(1000, 9999)}"
    
    logger.info(f"🚀 [BACKEND] Real quiz generation request received: {request_id}", extra={
        "request_id": request_id,
        "user_id": user_id,
        "request_data": request,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/quizzes/generate-real",
        "method": "POST",
        "ai_provider": "real"
    })
    
    try:
        # Extract parameters
        doc_ids = request.get("docIds", [])
        num_questions = request.get("numQuestions", 10)
        difficulty = request.get("difficulty", "medium")
        question_types = request.get("questionTypes", ["MCQ"])
        topic = request.get("topic", "General Knowledge")
        
        logger.info(f"📋 [BACKEND] Extracted real quiz parameters: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "doc_ids": doc_ids,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": question_types,
            "topic": topic
        })
        
        if not doc_ids:
            logger.error(f"❌ [BACKEND] Missing docIds in real quiz request: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "request": request
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="docIds is required"
            )
        
        # Initialize the real quiz generator
        logger.info(f"🔧 [BACKEND] Initializing QuizGenerator: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id
        })
        
        try:
            from .services.quiz_generator import QuizGenerator
            quiz_generator = QuizGenerator()
            logger.info(f"✅ [BACKEND] QuizGenerator initialized successfully: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "strategy": quiz_generator.strategy,
                "provider": getattr(quiz_generator, 'provider', None),
                "openai_configured": bool(quiz_generator.openai_api_key),
                "ollama_configured": bool(quiz_generator.ollama_url),
                "huggingface_configured": bool(quiz_generator.huggingface_token)
            })
        except Exception as e:
            logger.error(f"❌ [BACKEND] Failed to initialize QuizGenerator: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize quiz generator: {str(e)}"
            )
        
        # Fetch real chunks from indexing-service for provided doc IDs
        context_chunks: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                for d_id in doc_ids:
                    try:
                        url = f"{os.getenv('INDEXING_SERVICE_URL', 'http://indexing-service:8003')}/chunks/{d_id}"
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json() or []
                            for ch in data:
                                # Normalize to expected shape
                                context_chunks.append({
                                    "content": ch.get("content", ""),
                                    "metadata": {
                                        "document_id": ch.get("document_id", d_id),
                                        "chunk_index": ch.get("chunk_index")
                                    }
                                })
                        else:
                            logger.warning(f"[BACKEND] Failed to fetch chunks for {d_id}: {resp.status_code}")
                    except Exception as fe:
                        logger.warning(f"[BACKEND] Error fetching chunks for {d_id}: {fe}")
        except Exception as fetch_err:
            logger.warning(f"[BACKEND] Chunk fetch error: {fetch_err}")

        # Fallback if no chunks were found
        if not context_chunks:
            context_chunks = [
                {
                    "content": "No chunks found for documents. Use general study instructions.",
                    "metadata": {"source": "fallback", "document_id": doc_ids[0] if doc_ids else "unknown"}
                }
            ]

        # Truncate chunks to fit within OpenAI's token limit (approximately 16K tokens)
        # Rough estimate: 1 token ≈ 4 characters, so 16K tokens ≈ 64K characters
        MAX_CONTEXT_CHARS = 60000  # Conservative limit to stay well under token limit
        
        if context_chunks:
            total_chars = sum(len(chunk["content"]) for chunk in context_chunks)
            if total_chars > MAX_CONTEXT_CHARS:
                logger.info(f"📏 [BACKEND] Truncating chunks from {total_chars} to {MAX_CONTEXT_CHARS} characters: {request_id}")
                
                # Sort chunks by length and keep the most relevant ones
                context_chunks.sort(key=lambda x: len(x["content"]), reverse=True)
                
                truncated_chunks = []
                current_chars = 0
                
                for chunk in context_chunks:
                    chunk_content = chunk["content"]
                    if current_chars + len(chunk_content) <= MAX_CONTEXT_CHARS:
                        truncated_chunks.append(chunk)
                        current_chars += len(chunk_content)
                    else:
                        # Truncate this chunk to fit
                        remaining_chars = MAX_CONTEXT_CHARS - current_chars
                        if remaining_chars > 100:  # Only add if we have meaningful content
                            truncated_chunk = chunk.copy()
                            truncated_chunk["content"] = chunk_content[:remaining_chars] + "..."
                            truncated_chunks.append(truncated_chunk)
                            current_chars = MAX_CONTEXT_CHARS
                        break
                
                context_chunks = truncated_chunks
                logger.info(f"✅ [BACKEND] Truncated to {len(context_chunks)} chunks with {current_chars} characters: {request_id}")

        logger.info(f"📚 [BACKEND] Using context chunks for quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "doc_ids": doc_ids,
            "chunk_count": len(context_chunks),
            "total_chars": sum(len(chunk["content"]) for chunk in context_chunks),
            "chunk_preview": (context_chunks[0]["content"][:100] + "...") if context_chunks else "No chunks"
        })
        
        # Generate the quiz using the AI provider
        # Publish quiz generation started event
        try:
            from shared.event_publisher import EventPublisher
            event_publisher = EventPublisher()
            event_publisher.publish_quiz_generation_started(
                user_id=user_id,
                quiz_id=str(uuid.uuid4()),  # Generate temporary quiz ID
                source_document_id=doc_ids[0] if doc_ids else "unknown",
                num_questions=num_questions,
                topic=topic,
                difficulty=difficulty
            )
            logger.info(f"📢 [BACKEND] Published quiz generation started event: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "event_type": "quiz_generation_started"
            })
        except Exception as event_error:
            logger.warning(f"⚠️ [BACKEND] Failed to publish quiz generation started event: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "error": str(event_error)
            })

        logger.info(f"🤖 [BACKEND] Starting AI-powered quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "ai_strategy": quiz_generator.strategy,
            "ai_provider": getattr(quiz_generator, 'provider', None),
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions
        })
        
        start_time = time.time()
        # Map optional questionMix to counts_by_type
        question_mix = request.get("questionMix") or {}
        try:
            if isinstance(question_mix, dict) and question_mix:
                # Convert percent mix to absolute counts that sum to num_questions
                mix_items = [(k, max(0, int(round(num_questions * (v / 100.0))))) for k, v in question_mix.items()]
                allocated = sum(c for _, c in mix_items)
                # Fix rounding drift by adding remainder to MCQ (or first type)
                if mix_items:
                    remainder = max(0, num_questions - allocated)
                    mix_items[0] = (mix_items[0][0], mix_items[0][1] + remainder)
                counts_by_type = {k: c for k, c in mix_items if c > 0}
                allowed_types = list(counts_by_type.keys()) or ["MCQ"]
            else:
                counts_by_type = {"MCQ": num_questions}
                allowed_types = ["MCQ"]
        except Exception:
            counts_by_type = {"MCQ": num_questions}
            allowed_types = ["MCQ"]

        quiz_data = await quiz_generator.generate_quiz_from_context(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            context_chunks=context_chunks,
            source_type="document",
            source_id=doc_ids[0] if doc_ids else "mock-doc",
            allowed_types=allowed_types,
            counts_by_type=counts_by_type
        )
        generation_time = time.time() - start_time
        
        logger.info(f"✅ [BACKEND] AI quiz generation completed successfully: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "generation_time": f"{generation_time:.2f}s",
            "question_count": len(quiz_data.get('questions', [])),
            "quiz_id": quiz_data.get('id'),
            "ai_strategy": quiz_generator.strategy,
            "ai_provider": getattr(quiz_generator, 'provider', None)
        })
        
        # Persist quiz to database
        try:
            db_quiz_id = str(uuid.uuid4())
            from .models.quiz import Quiz as QuizModel
            quiz_record = QuizModel(
                id=db_quiz_id,
                title=quiz_data.get("title", "Generated Quiz"),
                description=quiz_data.get("description", None),
                questions={"questions": quiz_data.get("questions", [])},
                user_id=user_id,
                document_id=doc_ids[0] if doc_ids else None,
                subject_id=None,
                category_id=None,
                status="generated",
            )
            db.add(quiz_record)
            db.commit()
            logger.info(
                f"🗄️ [BACKEND] Quiz persisted to DB: {request_id}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "db_quiz_id": db_quiz_id,
                    "question_count": len(quiz_data.get("questions", [])),
                },
            )
        except Exception as persist_error:
            logger.error(
                f"❌ [BACKEND] Failed to persist quiz: {request_id}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(persist_error),
                },
            )

        # Publish quiz generation completed event
        try:
            from shared.event_publisher import EventPublisher
            event_publisher = EventPublisher()
            event_publisher.publish_quiz_generated(
                user_id=user_id,
                quiz_id=db_quiz_id,
                generation_time=generation_time,
                questions_count=len(quiz_data.get('questions', []))
            )
            logger.info(f"📢 [BACKEND] Published quiz completion event: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "quiz_id": db_quiz_id,
                "event_type": "quiz_generated"
            })
        except Exception as event_error:
            logger.warning(f"⚠️ [BACKEND] Failed to publish quiz completion event: {request_id}", extra={
                "request_id": request_id,
                "user_id": user_id,
                "error": str(event_error)
            })

        response_data = {
            "status": "success",
            "message": "Quiz generated successfully using AI",
            "job_id": str(uuid.uuid4()),  # Generate unique job_id for frontend compatibility
            "quiz": quiz_data,
            "generation_strategy": quiz_generator.strategy,
            "provider": quiz_generator.provider.name if quiz_generator.provider else "mock",
            "generation_time": f"{generation_time:.2f}s"
        }
        
        logger.info(f"📤 [BACKEND] Sending AI quiz generation response: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "response_status": "success",
            "response_size": len(str(response_data)),
            "ai_provider": response_data["provider"],
            "generation_time": response_data["generation_time"]
        })
        
        return response_data
        
    except HTTPException:
        logger.error(f"❌ [BACKEND] HTTP exception in real quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "exception_type": "HTTPException"
        })
        raise
    except Exception as e:
        logger.error(f"💥 [BACKEND] Unexpected error in real quiz generation: {request_id}", extra={
            "request_id": request_id,
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@app.post("/test-quiz-generation")
async def test_quiz_generation():
    """Test the complete quiz generation flow"""
    try:
        logger.info("Testing complete quiz generation flow...")
        
        # Initialize the quiz generator
        try:
            from .services.quiz_generator import QuizGenerator
            quiz_generator = QuizGenerator()
            logger.info(f"QuizGenerator initialized with strategy: {quiz_generator.strategy}")
        except Exception as e:
            logger.error(f"Failed to initialize QuizGenerator: {e}")
            return {
                "status": "error",
                "message": f"Failed to initialize quiz generator: {str(e)}"
            }
        
        # Create mock context chunks
        mock_context_chunks = [
            {
                "content": "The Vietnam War was a conflict that occurred in Vietnam, Laos, and Cambodia from 1 November 1955 to the fall of Saigon on 30 April 1975.",
                "metadata": {"source": "test", "document_id": "test-doc-1"}
            },
            {
                "content": "The war was fought between North Vietnam, supported by the Soviet Union and China, and South Vietnam, supported by the United States and other anti-communist allies.",
                "metadata": {"source": "test", "document_id": "test-doc-2"}
            }
        ]
        
        logger.info(f"Testing with {len(mock_context_chunks)} mock context chunks")
        
        # Test the generation
        try:
            quiz_data = await quiz_generator.generate_quiz_from_context(
                topic="Vietnam War History",
                difficulty="medium",
                num_questions=3,
                context_chunks=mock_context_chunks,
                source_type="test",
                source_id="test-doc"
            )
            
            logger.info(f"Quiz generation test completed successfully")
            
            return {
                "status": "success",
                "message": "Quiz generation test completed successfully",
                "quiz": quiz_data,
                "generation_strategy": quiz_generator.strategy,
                "provider": quiz_generator.provider.name if quiz_generator.provider else "mock",
                "questions_count": len(quiz_data.get('questions', [])),
                "test_context_chunks": len(mock_context_chunks)
            }
            
        except Exception as gen_error:
            logger.error(f"Quiz generation test failed: {gen_error}")
            return {
                "status": "error",
                "message": f"Quiz generation test failed: {str(gen_error)}",
                "generation_strategy": quiz_generator.strategy,
                "provider": quiz_generator.provider.name if quiz_generator.provider else "mock"
            }
            
    except Exception as e:
        logger.error(f"Quiz generation test failed: {e}")
        return {
            "status": "error",
            "message": f"Quiz generation test failed: {str(e)}"
        }

@app.get("/quizzes/{quiz_id}")
async def get_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID"""
    try:
        # Get the actual quiz from the database
        quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Return the quiz data
        return {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "questions": quiz.questions,
            "user_id": quiz.user_id,
            "subject_id": quiz.subject_id,
            "category_id": quiz.category_id,
            "status": quiz.status,
            "created_at": quiz.created_at,
            "updated_at": quiz.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quiz: {str(e)}"
        )

@app.get("/quizzes/{job_id}/events")
async def get_quiz_events(
    job_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get real-time events for a quiz generation job"""
    try:
        logger.info(f"Getting quiz events for job_id: {job_id}")
        
        # Return mock events for now
        events = [
            {
                "event_id": f"event_{job_id}_1",
                "event_type": "quiz_generation_started",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "job_id": job_id,
                    "stage": "initializing",
                    "progress": 0,
                    "message": "Starting quiz generation..."
                }
            },
            {
                "event_id": f"event_{job_id}_2", 
                "event_type": "quiz_generation_progress",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "job_id": job_id,
                    "stage": "generating_questions",
                    "progress": 50,
                    "message": "Generating questions using AI..."
                }
            },
            {
                "event_id": f"event_{job_id}_3",
                "event_type": "quiz_generation_completed", 
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "job_id": job_id,
                    "stage": "completed",
                    "progress": 100,
                    "message": "Quiz generation completed successfully!"
                }
            }
        ]
        
        return {
            "status": "success",
            "events": events,
            "total_events": len(events)
        }
        
    except Exception as e:
        logger.error(f"Failed to get quiz events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events: {str(e)}"
        )

@app.post("/quizzes")
async def create_quiz(
    request: dict,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Create a new quiz"""
    try:
        from .models.quiz import Quiz
        
        quiz_data = {
            "id": str(uuid.uuid4()),
            "title": request.get("title", "Untitled Quiz"),
            "description": request.get("description"),
            "questions": request.get("questions", {}),
            "user_id": user_id,
            "document_id": request.get("document_id"),
            "subject_id": request.get("subject_id"),
            "category_id": request.get("category_id"),
            "status": request.get("status", "draft")
        }
        
        quiz = Quiz(**quiz_data)
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        return {
            "id": quiz.id,
            "title": quiz.title,
            "status": "success",
            "message": "Quiz created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quiz: {str(e)}"
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
        # Get actual quizzes from database
        quizzes_query = db.query(models.Quiz).offset(skip).limit(limit)
        quizzes = quizzes_query.all()
        
        # Convert to response format
        quiz_list = []
        for quiz in quizzes:
            quiz_list.append({
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "questions": quiz.questions,
                "user_id": quiz.user_id,
                "subject_id": quiz.subject_id,
                "category_id": quiz.category_id,
                "status": quiz.status,
                "created_at": quiz.created_at,
                "updated_at": quiz.updated_at
            })
        
        # Get total count
        total = db.query(models.Quiz).count()
        
        return {
            "quizzes": quiz_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to list quizzes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list quizzes: {str(e)}"
        )

@app.post("/quiz-sessions/from-quiz/{quiz_id}")
async def create_session_from_quiz(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    shuffle: bool = Query(True, description="Whether to shuffle questions"),
    db: Session = Depends(get_db)
):
    """Create a new quiz session from an existing quiz"""
    try:
        logger.info(f"Creating session from quiz: {quiz_id}, user: {user_id}, shuffle: {shuffle}")
        
        # Check if quiz exists
        quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Create new session
        session_id = str(uuid.uuid4())
        new_session = models.QuizSession(
            id=session_id,
            quiz_id=quiz_id,
            user_id=user_id,
            seed=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        db.add(new_session)
        db.flush()  # Get the session ID without committing
        
        # Create session questions from quiz data
        quiz_questions = quiz.questions.get("questions", [])
        if shuffle:
            # Shuffle questions while preserving order
            import random
            question_indices = list(range(len(quiz_questions)))
            random.shuffle(question_indices)
            quiz_questions = [quiz_questions[i] for i in question_indices]
        
        created_questions = []
        for i, q_data in enumerate(quiz_questions):
            # Map the question data to the expected format
            question_text = q_data.get("question", q_data.get("stem", ""))
            question_type = q_data.get("type", "mcq").lower()
            
            session_question = models.QuizSessionQuestion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                display_index=i,
                q_type=question_type,
                stem=question_text,
                options=q_data.get("options") if question_type == "mcq" else None,
                blanks=q_data.get("blanks") if question_type == "fill_in_blank" else None,
                private_payload={
                    'correct_answer': q_data.get('answer'),
                    'metadata': q_data.get('metadata', {})
                },
                meta_data={
                    'source_question_id': q_data.get('id', f'q{i+1}'),
                    'question_type': question_type,
                    'original_question': q_data
                },
                source_index=i
            )
            db.add(session_question)
            created_questions.append(session_question)
        
        db.commit()
        db.refresh(new_session)
        
        logger.info(f"Created session {session_id} for quiz {quiz_id} with {len(created_questions)} questions")
        
        return {
            "session_id": session_id,
            "count": len(created_questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session from quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/quizzes/{quiz_id}/create-session")
async def create_quiz_session(
    quiz_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Create a new quiz session for an existing quiz"""
    try:
        logger.info(f"Creating new session for quiz: {quiz_id}")
        
        # Check if quiz exists
        quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Create new session
        session_id = str(uuid.uuid4())
        new_session = models.QuizSession(
            id=session_id,
            quiz_id=quiz_id,
            user_id=user_id,
            seed=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        db.add(new_session)
        db.flush()  # Get the session ID without committing
        
        # Create session questions from quiz data
        quiz_questions = quiz.questions.get("questions", [])
        for i, q_data in enumerate(quiz_questions):
            # Map the question data to the expected format
            question_text = q_data.get("question", q_data.get("stem", ""))
            question_type = q_data.get("type", "mcq").lower()
            
            session_question = models.QuizSessionQuestion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                display_index=i,
                q_type=question_type,
                stem=question_text,
                options=q_data.get("options") if question_type == "mcq" else None,
                blanks=q_data.get("blanks") if question_type == "fill_in_blank" else None,
                private_payload={
                    'correct_answer': q_data.get('answer'),
                    'metadata': q_data.get('metadata', {})
                },
                meta_data={
                    'source_question_id': q_data.get('id', f'q{i+1}'),
                    'question_type': question_type,
                    'original_question': q_data
                },
                source_index=i
            )
            db.add(session_question)
        
        db.commit()
        db.refresh(new_session)
        
        logger.info(f"Created session {session_id} for quiz {quiz_id}")
        
        return {
            "status": "success",
            "message": "Quiz session created successfully",
            "sessionId": session_id,
            "quizId": quiz_id,
            "frontendUrl": f"/quiz/session/{session_id}",
            "studySessionUrl": f"/quiz/session/{session_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create quiz session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/study-sessions/{session_id}/quiz")
async def get_quiz_for_session(
    session_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get quiz data for a session in the format expected by the frontend"""
    try:
        # Get the session
        session = db.query(models.QuizSession).filter(models.QuizSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
        # Get the quiz
        quiz = db.query(models.Quiz).filter(models.Quiz.id == session.quiz_id).first()
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz not found for session {session_id}"
            )
        
        # Get session questions
        session_questions = db.query(models.QuizSessionQuestion).filter(
            models.QuizSessionQuestion.session_id == session_id
        ).order_by(models.QuizSessionQuestion.display_index).all()
        
        # Convert to frontend format
        questions = []
        for i, sq in enumerate(session_questions):
            question = {
                "session_question_id": sq.id,  # Use the actual session question ID
                "index": i,  # Add the index
                "type": sq.q_type,
                "stem": sq.stem,  # Use 'stem' as expected by frontend
            }
            
            # Add type-specific fields
            if sq.q_type == "mcq" and sq.options:
                # Convert options to the format expected by frontend: {id: string, text: string}[]
                if isinstance(sq.options, list):
                    question["options"] = [
                        {"id": f"opt_{i}", "text": option} 
                        for i, option in enumerate(sq.options)
                    ]
                else:
                    question["options"] = []
            elif sq.q_type == "fill_in_blank" and sq.blanks:
                question["blanks"] = sq.blanks
            elif sq.q_type == "true_false":
                question["options"] = [
                    {"id": "true", "text": "True"},
                    {"id": "false", "text": "False"}
                ]
            
            questions.append(question)
        
        return {
            "session_id": session_id,  # Use snake_case as expected by frontend
            "quiz_id": quiz.id,        # Use snake_case as expected by frontend
            "questions": questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz for session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/quiz-sessions/{session_id}/view")
async def view_quiz_session(
    session_id: _uuid.UUID,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Compatibility endpoint that returns the same payload as
    `/study-sessions/{session_id}/quiz`, but under quiz-sessions prefix.
    """
    return await get_quiz_for_session(str(session_id), user_id, db)

@app.get("/study-sessions/{session_id}/answers")
async def save_session_answers(
    session_id: str,
    request: Request,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Save answers for a quiz session"""
    try:
        body = await request.json()
        answers = body.get("answers", {})
        
        # For now, just return success
        # In a real implementation, you'd save the answers to the database
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Failed to save answers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/study-sessions/{session_id}/submit")
async def submit_session(
    session_id: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Submit a quiz session for grading"""
    try:
        # For now, return mock results
        # In a real implementation, you'd grade the answers
        return {
            "scorePercent": 85,
            "correctCount": 8,
            "total": 10,
            "graded": []
        }
        
    except Exception as e:
        logger.error(f"Failed to submit session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 