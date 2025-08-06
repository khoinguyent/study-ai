from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import httpx
import time

from .database import get_db
from .models import Base, Quiz, CustomDocumentSet
from .schemas import (
    QuizCreate, QuizResponse, QuizGenerationRequest,
    SubjectQuizGenerationRequest, CategoryQuizGenerationRequest,
    DocumentSelectionRequest, CustomDocumentSetRequest, CustomDocumentSetResponse,
    QuizGenerationResponse
)
from .config import settings
from .services.quiz_generator import QuizGenerator

app = FastAPI(
    title="Quiz Service",
    description="AI-powered quiz generation service with subject-based grouping and document selection",
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

# Custom Document Set Management
@app.post("/document-sets", response_model=CustomDocumentSetResponse)
async def create_custom_document_set(
    request: CustomDocumentSetRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Create a custom document set for quiz generation"""
    try:
        # Validate that all documents belong to the user
        async with httpx.AsyncClient() as client:
            for doc_id in request.document_ids:
                doc_response = await client.get(
                    f"{settings.DOCUMENT_SERVICE_URL}/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {user_id}"}
                )
                if doc_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} not found or not accessible"
                    )
        
        # Create custom document set
        doc_set = CustomDocumentSet(
            name=request.name,
            description=request.description,
            document_ids=request.document_ids,
            user_id=user_id,
            subject_id=request.subject_id,
            category_id=request.category_id
        )
        
        db.add(doc_set)
        db.commit()
        db.refresh(doc_set)
        
        return doc_set
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document set: {str(e)}"
        )

@app.get("/document-sets", response_model=List[CustomDocumentSetResponse])
async def list_custom_document_sets(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all custom document sets for a user"""
    doc_sets = db.query(CustomDocumentSet).filter(
        CustomDocumentSet.user_id == user_id
    ).all()
    return doc_sets

@app.get("/document-sets/{set_id}", response_model=CustomDocumentSetResponse)
async def get_custom_document_set(
    set_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific custom document set"""
    doc_set = db.query(CustomDocumentSet).filter(
        CustomDocumentSet.id == set_id,
        CustomDocumentSet.user_id == user_id
    ).first()
    
    if not doc_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document set not found"
        )
    
    return doc_set

@app.delete("/document-sets/{set_id}")
async def delete_custom_document_set(
    set_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Delete a custom document set"""
    doc_set = db.query(CustomDocumentSet).filter(
        CustomDocumentSet.id == set_id,
        CustomDocumentSet.user_id == user_id
    ).first()
    
    if not doc_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document set not found"
        )
    
    db.delete(doc_set)
    db.commit()
    
    return {"message": "Document set deleted successfully"}

# Document Selection Quiz Generation
@app.post("/generate/selected-documents", response_model=QuizGenerationResponse)
async def generate_quiz_from_selected_documents(
    request: DocumentSelectionRequest,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Generate a quiz from specific selected documents"""
    start_time = time.time()
    
    try:
        # Validate that all documents belong to the user
        async with httpx.AsyncClient() as client:
            for doc_id in request.document_ids:
                doc_response = await client.get(
                    f"{settings.DOCUMENT_SERVICE_URL}/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {user_id}"}
                )
                if doc_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Document {doc_id} not found or not accessible"
                    )
        
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
        
        # Generate quiz using AI with selected document context
        quiz_content = await quiz_generator.generate_quiz_from_context(
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=all_context_chunks,
            source_type="selected_documents",
            source_id=",".join(request.document_ids)
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
            source_type="selected_documents",
            source_id=",".join(request.document_ids),
            documents_used=request.document_ids
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )

@app.post("/generate/document-set/{set_id}", response_model=QuizGenerationResponse)
async def generate_quiz_from_custom_document_set(
    set_id: int,
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

@app.post("/generate", response_model=QuizResponse)
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
            description=quiz_content.get("description"),
            questions=quiz_content["questions"],
            document_id=request.document_id,
            subject_id=request.subject_id,
            category_id=request.category_id,
            status="draft"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        generation_time = time.time() - start_time
        
        return quiz
        
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
        # Get category information
        async with httpx.AsyncClient() as client:
            category_response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/categories/{request.category_id}"
            )
            
            if category_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            category = category_response.json()
        
        # Use category name as topic if not provided
        topic = request.topic or category["name"]
        
        # Get context from indexing service
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
        
        # Generate quiz using AI with category context
        quiz_content = await quiz_generator.generate_quiz_from_context(
            topic=topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=context_chunks,
            source_type="category",
            source_id=str(request.category_id)
        )
        
        # Save quiz to database
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Category quiz generation failed: {str(e)}"
        )

@app.get("/quizzes", response_model=List[QuizResponse])
async def list_quizzes(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """List all quizzes for a user"""
    quizzes = db.query(Quiz).filter(Quiz.user_id == user_id).all()
    return quizzes

@app.get("/quizzes/subject/{subject_id}", response_model=List[QuizResponse])
async def list_subject_quizzes(
    subject_id: int,
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
    category_id: int,
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
    quiz_id: int,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get a specific quiz"""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz

@app.put("/quizzes/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: int,
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
    quiz_id: int,
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