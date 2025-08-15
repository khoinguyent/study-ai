import logging
import httpx
import json
import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from fastapi import WebSocket, WebSocketDisconnect
from strawberry.fastapi import GraphQLRouter
from .graphql_schema import schema
from .config import settings
from .auth import verify_auth_token, security

# Set up logging
logger = logging.getLogger(__name__)

app = FastAPI(title="StudyAI GraphQL API", version="1.0.0")

# Add CORS middleware - temporarily simplified
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create GraphQL router with context
async def get_context(request: Request):
    return {"request": request}

graphql_app = GraphQLRouter(schema, context_getter=get_context)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "graphql-api"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "StudyAI GraphQL API",
        "version": "1.0.0",
        "graphql_endpoint": "/graphql",
        "docs": "/docs"
    }

@app.get("/test-auth")
async def test_auth(request: Request):
    auth_header = request.headers.get("authorization")
    return {"message": "Test endpoint reached", "auth_header": auth_header}

@app.post("/test-upload")
async def test_upload():
    """Test upload endpoint"""
    return {"message": "Test upload endpoint working"}

# Auth endpoints - mock implementation for development
@app.post("/auth/login")
async def login(request: Request):
    """Mock login endpoint"""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        # Mock authentication - accept any email/password for development
        if email and password:
            return {
                "access_token": "mock-jwt-token-" + email,
                "token_type": "bearer",
                "user": {
                    "id": "mock-user-id-" + email,
                    "username": email.split("@")[0],
                    "email": email,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Email and password required")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/auth/register")
async def register(request: Request):
    """Mock register endpoint"""
    try:
        body = await request.json()
        name = body.get("name")
        email = body.get("email")
        password = body.get("password")
        
        if name and email and password:
            return {
                "access_token": "mock-jwt-token-" + email,
                "token_type": "bearer",
                "user": {
                    "id": "mock-user-id-" + email,
                    "username": name,
                    "email": email,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Name, email and password required")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user(request: Request):
    """Mock get current user endpoint"""
    auth_header = request.headers.get("authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = auth_header.split(" ")[1]
    
    # Mock user data based on token
    if token.startswith("mock-jwt-token-"):
        email = token.replace("mock-jwt-token-", "")
        return {
            "id": "mock-user-id-" + email,
            "username": email.split("@")[0],
            "email": email,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/uploads/events")
async def upload_events_stream(userId: str = Query(...)):
    """SSE stream for upload events - mock implementation for development"""
    async def event_generator():
        # Mock upload events for testing
        import asyncio
        
        # Simulate upload progress for multiple documents
        documents = [
            {"filename": "Exercise 2 - ADD - Critical Feature Launch Delay.pdf", "uploadId": f"upload-{userId}-doc1"},
            {"filename": "Project Requirements Document.pdf", "uploadId": f"upload-{userId}-doc2"},
            {"filename": "Technical Specification.pdf", "uploadId": f"upload-{userId}-doc3"}
        ]
        
        for doc in documents:
            # Queued event
            yield f"data: {json.dumps({'type': 'queued', 'uploadId': doc['uploadId'], 'filename': doc['filename']})}\n\n"
            await asyncio.sleep(0.5)
            
            # Progress events
            for progress in range(10, 101, 20):
                yield f"data: {json.dumps({'type': 'running', 'uploadId': doc['uploadId'], 'progress': progress, 'filename': doc['filename']})}\n\n"
                await asyncio.sleep(0.5)
            
            # Completed event
            doc_id = f'doc-{doc["uploadId"]}'
            yield f"data: {json.dumps({'type': 'completed', 'uploadId': doc['uploadId'], 'documentId': doc_id, 'filename': doc['filename']})}\n\n"
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint to proxy connections to notification service"""
    await websocket.accept()
    
    try:
        # For now, just accept the connection and send a welcome message
        # In a full implementation, this would proxy to the notification service
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": f"WebSocket connected for user {user_id}",
            "status": "connected"
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo back for now (replace with actual notification service logic)
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "message": f"Received: {message}",
                    "timestamp": str(datetime.datetime.now())
                }))
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                print(f"WebSocket error for user {user_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        try:
            await websocket.close()
        except:
            pass

@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """Get document processing status - mock implementation for development"""
    # Mock document status for testing
    import random
    
    # Simulate different document states
    states = ["processing", "ready", "failed"]
    state = random.choice(states)
    
    if state == "processing":
        progress = random.randint(10, 90)
        return {"state": "processing", "progress": progress}
    elif state == "ready":
        return {"state": "ready", "progress": 100}
    else:
        return {"state": "failed", "progress": 0, "message": "Processing failed"}

@app.get("/auth/me-direct")
async def me_direct(request: Request):
    """Direct auth proxy without dependencies"""
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return {"error": "No auth header"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/me",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            return {"status": response.status_code, "data": response.text}
    except Exception as e:
        return {"error": str(e)}

# Proxy endpoints for authentication
@app.post("/auth/login")
async def login_proxy(request_data: dict):
    """Proxy login requests to auth service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/login",
                json=request_data,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = "Authentication failed"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service error: {str(e)}"
        )

@app.post("/auth/register")
async def register_proxy(request_data: dict):
    """Proxy register requests to auth service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/register",
                json=request_data,
                timeout=30.0
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_detail = "Registration failed"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service error: {str(e)}"
        )

@app.api_route("/auth/me", methods=["GET", "OPTIONS"])
async def me_proxy(request: Request):
    """Get current user info"""
    if request.method == "OPTIONS":
        return {"message": "OK"}
    
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="No auth header")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/me",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=401, detail="Auth failed")
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service error: {str(e)}"
        )

# Add CORS preflight handler - temporarily disabled to fix upload routing
# @app.options("/{path:path}")
# async def options_handler(path: str):
#     """Handle CORS preflight requests"""
#     return {"message": "OK"}

# Proxy other endpoints that might be needed
@app.get("/subjects")
async def subjects_proxy(user_id: str = Depends(verify_auth_token)):
    """Proxy subjects requests to document service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/subjects",
                headers={"user_id": user_id},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get subjects"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/categories")
async def categories_proxy(user_id: str = Depends(verify_auth_token)):
    """Proxy categories requests to document service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/categories",
                headers={"user_id": user_id},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get categories"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/documents/{document_id}/download")
async def download_document_proxy(document_id: str, request: Request):
    """Proxy document download requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for downloads
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/documents/{document_id}/download",
                headers=headers,
            )
            
            if response.status_code == 200:
                # Get content type and filename from response headers
                content_type = response.headers.get('content-type', 'application/octet-stream')
                content_disposition = response.headers.get('content-disposition', f'attachment; filename=document_{document_id}')
                
                # Return the file content with proper headers
                from fastapi.responses import Response
                return Response(
                    content=response.content,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": content_disposition,
                        "Content-Length": response.headers.get('content-length', str(len(response.content)))
                    }
                )
            else:
                error_detail = "Failed to download document"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Download timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Download service error: {str(e)}"
        )

@app.post("/upload")
async def upload_document_proxy(request: Request):
    """Proxy single document upload requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the raw request body to preserve multipart structure
        body = await request.body()
        
        # Forward the request with proper content type
        content_type = request.headers.get("content-type", "")
        if content_type:
            headers["Content-Type"] = content_type
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # Longer timeout for uploads
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/upload",
                content=body,
                headers=headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = "Failed to upload document"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upload timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upload service error: {str(e)}"
        )

@app.post("/upload-multiple")
async def upload_multiple_documents_proxy(request: Request):
    """Proxy multiple document upload requests to document service"""
    print(f"DEBUG: Upload multiple endpoint called with method: {request.method}")
    try:
        # Forward the Authorization header to Document Service
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the raw request body to preserve multipart structure
        body = await request.body()
        print(f"DEBUG: Request body size: {len(body)} bytes")
        
        # Forward the request with proper content type
        content_type = request.headers.get("content-type", "")
        if content_type:
            headers["Content-Type"] = content_type
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # Longer timeout for uploads
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/upload-multiple",
                content=body,
                headers=headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = "Failed to upload documents"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass
                print(f"DEBUG: Document service returned {response.status_code}: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upload timeout"
        )
    except Exception as e:
        print(f"DEBUG: Exception in upload multiple: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upload service error: {str(e)}"
        )

@app.post("/api/study-sessions/start")
async def start_study_session_proxy(request: Request):
    """Mock study session start endpoint for development"""
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Get the request body
        body = await request.json()
        
        # Extract parameters - make most fields optional
        question_types = body.get("questionTypes", ["MCQ"])
        difficulty = body.get("difficulty", "medium")
        question_count = body.get("questionCount", 10)
        
        # These fields are now truly optional - use defaults if not provided
        subject_id = body.get("subjectId", "mock-subject")
        doc_ids = body.get("docIds", ["mock-doc"])
        
        # Generate mock response
        import uuid
        session_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        quiz_id = str(uuid.uuid4())
        
        logger.info(f"Mock study session started: session_id={session_id}, job_id={job_id}, quiz_id={quiz_id}")
        logger.info(f"Parameters: subject_id={subject_id}, doc_ids={doc_ids}, question_types={question_types}, difficulty={difficulty}, question_count={question_count}")
        
        return {
            "sessionId": session_id,
            "jobId": job_id,
            "quizId": quiz_id,
            "message": "Mock study session started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock study session start failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock study session start error: {repr(e)}"
        )

@app.post("/api/study-sessions/ingest")
async def ingest_study_session_proxy(request: Request):
    """Mock study session ingest endpoint for development"""
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Get the request body
        body = await request.json()
        
        # Return mock response
        logger.info(f"Mock study session ingest received: {body}")
        
        return {
            "status": "success",
            "message": "Mock study session input ingested successfully",
            "sessionId": "mock-session-id"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock study session ingest failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock study session ingest error: {repr(e)}"
        )

@app.get("/api/study-sessions/status")
async def get_study_session_status_proxy(
    request: Request,
    job_id: str = Query(..., description="Job ID to check status for")
):
    """Mock study session status endpoint for development"""
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Return mock status
        logger.info(f"Mock study session status requested for job_id: {job_id}")
        
        return {
            "state": "completed",
            "progress": 100,
            "sessionId": "mock-session-id",
            "quizId": "mock-quiz-id"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock study session status failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock study session status error: {repr(e)}"
        )

@app.get("/api/study-sessions/events")
async def get_study_session_events_proxy(
    request: Request,
    job_id: str = Query(..., description="Job ID to get events for")
):
    """Mock study session events endpoint for development - no auth required for SSE"""
    try:
        # For development, don't require authentication for SSE events
        # In production, this should be secured
        logger.info(f"Mock study session events requested for job_id: {job_id}")
        
        # Return proper SSE format
        from fastapi.responses import StreamingResponse
        import asyncio
        
        async def event_stream():
            # Send initial connection established event
            yield "data: {\"state\": \"queued\", \"progress\": 0, \"message\": \"SSE connection established\"}\n\n"
            
            # Wait a bit before sending the first event
            await asyncio.sleep(0.5)
            
            # Send quiz generation started event
            yield f"data: {{\"state\": \"running\", \"progress\": 25, \"message\": \"Quiz generation started\", \"jobId\": \"{job_id}\"}}\n\n"
            
            # Wait before sending completion event
            await asyncio.sleep(1.0)
            
            # Send quiz generation completed event
            yield f"data: {{\"state\": \"running\", \"progress\": 75, \"message\": \"Quiz generation completed successfully\", \"jobId\": \"{job_id}\"}}\n\n"
            
            # Wait before sending final event
            await asyncio.sleep(1.0)
            
            # Send final event with quiz data
            mock_quiz_data = {
                "state": "completed",
                "progress": 100,
                "sessionId": f"session-{job_id}",
                "quizId": f"quiz-{job_id}",
                "quiz": {
                    "id": f"quiz-{job_id}",
                    "title": "Mock Quiz - Vietnam History",
                    "questions": [
                        {
                            "id": "q1",
                            "type": "single_choice",
                            "prompt": "Who was the founder of the Tay Son dynasty?",
                            "options": [
                                {"id": "opt1", "text": "Nguyen Hue"},
                                {"id": "opt2", "text": "Nguyen Anh"},
                                {"id": "opt3", "text": "Nguyen Phuc Anh"},
                                {"id": "opt4", "text": "Nguyen Kim"}
                            ]
                        },
                        {
                            "id": "q2",
                            "type": "multiple_choice",
                            "prompt": "Which of the following are characteristics of the Tay Son rebellion?",
                            "options": [
                                {"id": "opt1", "text": "Peasant uprising"},
                                {"id": "opt2", "text": "Anti-feudal movement"},
                                {"id": "opt3", "text": "Foreign invasion"},
                                {"id": "opt4", "text": "Religious conflict"}
                            ]
                        },
                        {
                            "id": "q3",
                            "type": "true_false",
                            "prompt": "The Tay Son rebellion began in 1771.",
                            "trueLabel": "True",
                            "falseLabel": "False"
                        },
                        {
                            "id": "q4",
                            "type": "fill_blank",
                            "prompt": "The Tay Son rebellion began in the year _____ in the province of _____.",
                            "blanks": 2,
                            "labels": ["Year", "Province"]
                        },
                        {
                            "id": "q5",
                            "type": "short_answer",
                            "prompt": "Explain the main causes of the Tay Son rebellion and its impact on Vietnamese history.",
                            "minWords": 50
                        }
                    ]
                }
            }
            yield f"data: {json.dumps(mock_quiz_data)}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Mock study session events failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock study session events error: {repr(e)}"
        )

@app.post("/api/quiz-sessions/notify")
async def notify_quiz_session_proxy(
    request: Request,
    user_id: str = Query(..., description="User ID to notify"),
    session_id: str = Query(..., description="Session ID"),
    job_id: str = Query(..., description="Job ID"),
    status: str = Query(..., description="Status: queued, running, completed, failed"),
    progress: int = Query(0, description="Progress percentage"),
    message: str = Query(None, description="Status message")
):
    """Proxy quiz session notifications to the notification service"""
    try:
        # Get quiz_data from request body if present
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        quiz_data = body.get("quiz_data")
        
        logger.info(f"Quiz session notification proxy: user_id={user_id}, session_id={session_id}, status={status}")
        
        # Forward to notification service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/quiz-sessions/notify",
                params={
                    "user_id": user_id,
                    "session_id": session_id,
                    "job_id": job_id,
                    "status": status,
                    "progress": progress,
                    "message": message
                },
                json={"quiz_data": quiz_data} if quiz_data else {},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Notification service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Notification service error: {response.text}"
                )
                
    except Exception as e:
        logger.error(f"Quiz session notification proxy error: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz session notification proxy error: {repr(e)}"
        )

@app.post("/api/study-sessions/confirm")
async def confirm_study_session_proxy(request: Request):
    """Proxy study session confirm to quiz service"""
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Get the request body
        body = await request.json()
        
        # Forward to quiz service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/confirm",
                json=body,
                headers={"Authorization": auth_header},
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = "Failed to confirm study session"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", error_detail)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Quiz service timeout"
        )
    except Exception as e:
        logger.error(f"Study session confirm service error: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study session confirm service error: {str(e)}"
        )

# New clarifier proxy routes for /api/clarifier/*
@app.post("/api/clarifier/start")
async def clarifier_start_proxy(request: Request):
    """Mock clarifier start endpoint for development"""
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Get the request body
        body = await request.body()
        
        # Return mock response
        logger.info(f"Mock clarifier start received: {body}")
        
        return {
            "status": "success",
            "message": "Mock clarifier session started successfully",
            "sessionId": "mock-clarifier-session-id"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock clarifier start failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock clarifier start error: {repr(e)}"
        )

@app.post("/api/clarifier/ingest")
async def clarifier_ingest_proxy(request: Request):
    """Mock clarifier ingest endpoint for development"""
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required"
            )
        
        # Get the request body
        body = await request.json()
        
        # Return mock response
        logger.info(f"Mock clarifier ingest received: {body}")
        
        return {
            "status": "success",
            "message": "Mock clarifier input ingested successfully",
            "sessionId": "mock-clarifier-session-id"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock clarifier ingest failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock clarifier ingest error: {repr(e)}"
        )

# Quiz endpoints
@app.get("/api/study-sessions/{session_id}/quiz")
async def get_quiz(session_id: str):
    """Get quiz for a study session"""
    try:
        # For now, return mock quiz data
        mock_quiz = {
            "sessionId": session_id,
            "quizId": f"quiz-{session_id}",
            "questions": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "prompt": "Who was the founder of the Tay Son dynasty?",
                    "options": [
                        {"id": "opt1", "text": "Nguyen Hue"},
                        {"id": "opt2", "text": "Nguyen Anh"},
                        {"id": "opt3", "text": "Nguyen Phuc Anh"},
                        {"id": "opt4", "text": "Nguyen Kim"}
                    ]
                },
                {
                    "id": "q2",
                    "type": "multiple_choice",
                    "prompt": "Which of the following are characteristics of the Tay Son rebellion?",
                    "options": [
                        {"id": "opt1", "text": "Peasant uprising"},
                        {"id": "opt2", "text": "Anti-feudal movement"},
                        {"id": "opt3", "text": "Foreign invasion"},
                        {"id": "opt4", "text": "Religious conflict"}
                    ]
                },
                {
                    "id": "q3",
                    "type": "true_false",
                    "prompt": "The Tay Son rebellion began in 1771.",
                    "trueLabel": "True",
                    "falseLabel": "False"
                },
                {
                    "id": "q4",
                    "type": "fill_blank",
                    "prompt": "The Tay Son rebellion began in the year _____ in the province of _____.",
                    "blanks": 2,
                    "labels": ["Year", "Province"]
                },
                {
                    "id": "q5",
                    "type": "short_answer",
                    "prompt": "Explain the main causes of the Tay Son rebellion and its impact on Vietnamese history.",
                    "minWords": 50
                }
            ]
        }
        return mock_quiz
    except Exception as e:
        logger.error(f"Error getting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/study-sessions/{session_id}/answers")
async def save_quiz_answers(session_id: str, answers: dict = Body(...)):
    """Save quiz answers (autosave)"""
    try:
        # For now, just log the answers
        logger.info(f"Saving answers for session {session_id}: {answers}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error saving answers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/study-sessions/{session_id}/submit")
async def submit_quiz(session_id: str):
    """Submit and grade quiz"""
    try:
        # For now, return mock grading results
        mock_result = {
            "scorePercent": 85.0,
            "correctCount": 4,
            "total": 5,
            "graded": [
                {
                    "id": "q1",
                    "type": "single_choice",
                    "prompt": "Who was the founder of the Tay Son dynasty?",
                    "options": [
                        {"id": "opt1", "text": "Nguyen Hue"},
                        {"id": "opt2", "text": "Nguyen Anh"},
                        {"id": "opt3", "text": "Nguyen Phuc Anh"},
                        {"id": "opt4", "text": "Nguyen Kim"}
                    ],
                    "correctChoiceIds": ["opt1"],
                    "explanation": "Nguyen Hue was indeed the founder and leader of the Tay Son dynasty."
                },
                {
                    "id": "q2",
                    "type": "multiple_choice",
                    "prompt": "Which of the following are characteristics of the Tay Son rebellion?",
                    "options": [
                        {"id": "opt1", "text": "Peasant uprising"},
                        {"id": "opt2", "text": "Anti-feudal movement"},
                        {"id": "opt3", "text": "Foreign invasion"},
                        {"id": "opt4", "text": "Religious conflict"}
                    ],
                    "correctChoiceIds": ["opt1", "opt2"],
                    "explanation": "The Tay Son rebellion was primarily a peasant uprising and anti-feudal movement."
                },
                {
                    "id": "q3",
                    "type": "true_false",
                    "prompt": "The Tay Son rebellion began in 1771.",
                    "trueLabel": "True",
                    "falseLabel": "False",
                    "correct": True,
                    "explanation": "Correct! The Tay Son rebellion began in 1771 in Binh Dinh province."
                },
                {
                    "id": "q4",
                    "type": "fill_blank",
                    "prompt": "The Tay Son rebellion began in the year _____ in the province of _____.",
                    "blanks": 2,
                    "labels": ["Year", "Province"],
                    "correctValues": ["1771", "Binh Dinh"],
                    "explanation": "The rebellion began in 1771 in Binh Dinh province."
                },
                {
                    "id": "q5",
                    "type": "short_answer",
                    "prompt": "Explain the main causes of the Tay Son rebellion and its impact on Vietnamese history.",
                    "minWords": 50,
                    "explanation": "The Tay Son rebellion was caused by widespread corruption, heavy taxation, and social inequality under the Nguyen lords. It led to significant social reforms and the eventual unification of Vietnam under the Nguyen dynasty."
                }
            ]
        }
        return mock_result
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
