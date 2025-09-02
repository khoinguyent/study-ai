import logging
import httpx
import os
import json
import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Query, Body, Header, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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

@app.on_event("startup")
def _log_routes():
    """Log all registered routes in registration order for debugging"""
    logging.info("=== ROUTE TABLE (registration order) ===")
    for i, r in enumerate(app.router.routes):
        path = getattr(r, "path", str(r))
        methods = getattr(r, "methods", [])
        name = getattr(r, "name", "")
        logging.info("%03d: %s  methods=%s  name=%s", i, path, methods, name)
    logging.info("=== END ROUTE TABLE ===")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log exact 422 cause to aid debugging
    logger.error("[GATEWAY 422] %s %s %s", request.method, str(request.url), exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

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

# Quiz service configuration and helper functions
QUIZ_SVC = os.getenv("QUIZ_SERVICE_URL", "http://quiz-service:8000")

def _forward_headers(h: dict) -> dict:
    """Forward only safe headers"""
    out: dict = {}
    # forward only safe headers; add auth if present
    auth = h.get("authorization") or h.get("Authorization")
    if auth:
        out["Authorization"] = auth
    return out

# Quiz Session View Route - MUST BE EARLY to avoid conflicts with other routes
@app.get("/api/test-quiz-route/{session_id}")
async def gateway_view_quiz_session_early(session_id: str, request: Request):
    """Pure GET pass-through to quiz-service session view - moved early to avoid route conflicts"""
    try:
        # Use the session_id parameter directly
        url = f"{QUIZ_SVC}/quiz-sessions/{session_id}/view"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=_forward_headers(dict(request.headers)))
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/json"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Quiz service error: {str(e)}")


# Mock auth endpoints removed - using proxy endpoints to auth service instead

# DISABLED: Mock upload events endpoint - was causing automatic fake notifications

# TODO: Implement real upload events endpoint that only triggers for actual uploads

@app.get("/api/uploads/events")
async def upload_events_proxy(userId: str = Query(...)):
    """Proxy upload events to notification service"""
    try:
        logger.info(f"Events proxy: Starting request for userId: {userId}")
        logger.info(f"Events proxy: Target URL: {settings.NOTIFICATION_SERVICE_URL}/uploads/events")
        
        # For now, return a simple response indicating the frontend should connect directly
        # to the notification service for SSE streams
        return {
            "status": "success",
            "message": "Events endpoint available",
            "direct_sse_url": f"{settings.NOTIFICATION_SERVICE_URL}/uploads/events?userId={userId}",
            "note": "For Server-Sent Events, connect directly to the notification service"
        }
        
    except Exception as e:
        logger.error(f"Events proxy error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Events proxy error: {str(e)}"
        )

# WebSocket endpoint for notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    
    try:
        # In a full implementation, this would establish a bidirectional proxy
        # to the notification service WebSocket endpoint
        notification_ws_url = f"{settings.NOTIFICATION_SERVICE_URL}/ws/{user_id}"
        
        # For now, just echo back messages
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close()
        except:
            pass

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler: {str(exc)}")
    return {"detail": "Internal server error"}

# Document Service Proxy Routes

@app.get("/api/documents/{document_id}/status")
async def document_status_proxy(document_id: str, request: Request):
    """Proxy document status requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        target_url = f"{settings.DOCUMENT_SERVICE_URL}/documents/{document_id}/status"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(target_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Document service timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

# Direct auth proxy without dependencies
@app.post("/auth/login")
async def login_proxy(request_data: dict):
    """Proxy login requests to auth service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/login",
                json=request_data,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Login failed"
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/register",
                json=request_data,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Registration failed"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service error: {str(e)}"
        )

@app.api_route("/auth/me", methods=["GET", "OPTIONS"])
async def me_proxy(request: Request):
    """Proxy me requests to auth service"""
    try:
        # Forward the Authorization header to auth service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/me",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get user info"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service error: {str(e)}"
        )

# Proxy other endpoints that might be needed

@app.get("/subjects")
async def subjects_proxy(request: Request, user_id: str = Depends(verify_auth_token)):
    """Proxy subjects requests to document service"""
    try:
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/subjects",
                headers=headers,
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

@app.post("/subjects")
async def create_subject_proxy(request: Request, user_id: str = Depends(verify_auth_token)):
    """Proxy subject creation requests to document service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/subjects",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to create subject"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/categories")
async def categories_proxy(request: Request, user_id: str = Depends(verify_auth_token)):
    """Proxy categories requests to document service"""
    try:
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/categories",
                headers=headers,
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

@app.post("/categories")
async def create_category_proxy(request: Request, user_id: str = Depends(verify_auth_token)):
    """Proxy category creation requests to document service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/categories",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to create category"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.put("/subjects/{subject_id}")
async def update_subject_proxy(subject_id: str, request: Request, user_id: str = Depends(verify_auth_token)):
    """Proxy subject update requests to document service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{settings.DOCUMENT_SERVICE_URL}/subjects/{subject_id}",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to update subject"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.delete("/subjects/{subject_id}")
async def delete_subject_proxy(subject_id: str, user_id: str = Depends(verify_auth_token)):
    """Proxy subject deletion requests to document service"""
    try:
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{settings.DOCUMENT_SERVICE_URL}/subjects/{subject_id}",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return {"message": "Subject deleted successfully"}
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to delete subject"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.put("/categories/{category_id}")
async def update_category_proxy(category_id: str, request: Request, user_id: str = Depends(verify_auth_token)):
    """Proxy category update requests to document service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{settings.DOCUMENT_SERVICE_URL}/categories/{category_id}",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to update category"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.delete("/categories/{category_id}")
async def delete_category_proxy(category_id: str, user_id: str = Depends(verify_auth_token)):
    """Proxy category deletion requests to document service"""
    try:
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{settings.DOCUMENT_SERVICE_URL}/categories/{category_id}",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return {"message": "Category deleted successfully"}
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to delete category"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/subjects/{subject_id}/categories")
async def get_subject_categories_proxy(subject_id: str, user_id: str = Depends(verify_auth_token)):
    """Proxy subject categories requests to document service"""
    try:
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/categories",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                # Filter categories by subject_id
                filtered_categories = [cat for cat in data if cat.get('subject_id') == subject_id]
                return filtered_categories
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get subject categories"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/api/categories/{category_id}/documents")
async def get_category_documents_proxy(category_id: str, user_id: str = Depends(verify_auth_token), page: int = Query(1), page_size: int = Query(10)):
    """Proxy category documents requests to document service"""
    try:
        # Forward the Authorization header to document service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/categories/{category_id}/documents?page={page}&page_size={page_size}",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the document service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/api/documents/{document_id}/download")
async def download_document_proxy(document_id: str, request: Request):
    """Proxy document download requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        target_url = f"{settings.DOCUMENT_SERVICE_URL}/documents/{document_id}/download"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(target_url, headers=headers)
            
            if response.status_code == 200:
                # Return the file content
                return Response(
                    content=response.content,
                    media_type=response.headers.get("content-type", "application/octet-stream"),
                    headers={
                        "Content-Disposition": response.headers.get("content-disposition", f"attachment; filename=document_{document_id}"),
                        "Content-Length": str(len(response.content))
                    }
                )
            else:
                # Return the actual error from the document service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Document service timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

# Document upload proxy endpoints

@app.post("/api/documents/upload")
async def upload_document_proxy(request: Request):
    """Proxy single document upload requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the form data
        form_data = await request.form()
        
        # Forward the request with proper content type
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/upload",
                data=form_data,
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the document service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.post("/api/documents/upload-multiple")
async def upload_multiple_documents_proxy(request: Request):
    """Proxy multiple document upload requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the raw body and preserve all headers except Host
        body = await request.body()
        headers.update({k: v for k, v in request.headers.items() if k.lower() != "host"})
        
        # Forward the request with raw body and preserved headers
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/upload-multiple",
                content=body,
                headers=headers,
            )
            
            # Bubble up status + error details so the UI sees the real cause
            return Response(
                content=response.content, 
                status_code=response.status_code, 
                headers={"content-type": response.headers.get("content-type", "application/json")}
            )
                
    except Exception as e:
        logger.error(f"Upload multiple proxy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

# Document CRUD Proxy Routes

@app.get("/api/documents")
async def get_documents_proxy(
    category_id: str = Query(None),
    page: int = Query(1),
    page_size: int = Query(10),
    request: Request = None
):
    """Proxy document list requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization") if request else None
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Build query parameters
        params = {"page": page, "page_size": page_size}
        if category_id:
            params["category_id"] = category_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/documents",
                params=params,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the document service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.get("/api/documents/{document_id}")
async def get_document_proxy(document_id: str, request: Request):
    """Proxy single document requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DOCUMENT_SERVICE_URL}/documents/{document_id}",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the document service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

@app.delete("/api/documents/{document_id}")
async def delete_document_proxy(document_id: str, request: Request):
    """Proxy document deletion requests to document service"""
    try:
        # Forward the Authorization header to Document Service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{settings.DOCUMENT_SERVICE_URL}/documents/{document_id}",
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the document service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document service error: {str(e)}"
        )

QUIZ_SVC = os.getenv("QUIZ_SERVICE_URL", "http://quiz-service:8000")

def _forward_headers(h: dict) -> dict:
    out: dict = {}
    # forward only safe headers; add auth if present
    auth = h.get("authorization") or h.get("Authorization")
    if auth:
        out["Authorization"] = auth
    return out

# Quiz Service Proxy Routes

@app.post("/api/quiz/start-study-session")
async def start_study_session_proxy(request: Request):
    """Proxy study session start to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/start",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/quiz/ingest-study-session")
async def ingest_study_session_proxy(request: Request):
    """Proxy study session ingest to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/ingest",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/quiz/study-session-status/{job_id}")
async def get_study_session_status_proxy(
    job_id: str,
    request: Request
):
    """Proxy study session status to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/status",
                params={"job_id": job_id},
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/quiz/study-session-events/{job_id}")
async def get_study_session_events_proxy(
    job_id: str,
    request: Request
):
    """Proxy study session events to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            # Stream SSE from quiz-service
            async with client.stream(
                "GET",
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/events",
                params={"job_id": job_id},
                headers=headers,
                timeout=None,
            ) as resp:
                return Response(
                    content=resp.aiter_raw(),
                    status_code=resp.status_code,
                    media_type=resp.headers.get("content-type", "text/event-stream"),
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/quiz/confirm-study-session")
async def confirm_study_session_proxy(request: Request):
    """Proxy study session confirm to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/confirm",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

# Direct Study Session Routes (Frontend expects these)
@app.post("/api/study-sessions/start")
async def start_study_session_direct_proxy(request: Request):
    """Proxy study session start directly to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/start",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/study-sessions/status")
async def get_study_session_status_direct_proxy(
    request: Request,
    job_id: str = Query(..., description="Job ID to check status for")
):
    """Proxy study session status directly to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/status",
                params={"job_id": job_id},
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/study-sessions/events")
async def get_study_session_events_direct_proxy(
    request: Request,
    job_id: str = Query(..., description="Job ID to get events for")
):
    """Proxy study session events directly to quiz service with SSE support"""
    logger.info(f"Study session events endpoint called with job_id: {job_id}")
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # For SSE, we need to stream the response directly without buffering
        async def stream_events():
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "GET",
                    f"{settings.QUIZ_SERVICE_URL}/study-sessions/events",
                    params={"job_id": job_id},
                    headers=headers,
                    timeout=30.0
                ) as response:
                    if response.status_code == 200:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                    else:
                        # For non-200 responses, we need to handle them differently
                        # since we can't yield in an async generator after returning
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Quiz service error: {response.text}"
                        )
        
        # Proxy SSE directly to quiz service
        return StreamingResponse(
            stream_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Study session events proxy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/study-sessions/ingest")
async def ingest_study_session_direct_proxy(request: Request):
    """Proxy study session ingest directly to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/ingest",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/study-sessions/confirm")
async def confirm_study_session_direct_proxy(request: Request):
    """Proxy study session confirm directly to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/confirm",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/study-sessions/{session_id}/quiz")
async def study_sessions_quiz_proxy(session_id: str, request: Request):
    """Proxy study session quiz to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/{session_id}/quiz",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/study-sessions/{session_id}/answers")
async def study_sessions_answers_proxy(session_id: str, request: Request):
    """Proxy study session answers to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/{session_id}/answers",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/study-sessions/{session_id}/submit")
async def study_sessions_submit_proxy(session_id: str, request: Request):
    """Proxy study session submit to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/{session_id}/submit",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

# New clarifier proxy routes for /api/clarifier/*

@app.post("/api/clarifier/start")
async def clarifier_start_proxy(request: Request):
    """Proxy clarifier start to clarifier service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to clarifier service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CLARIFIER_SERVICE_URL}/clarifier/start",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the clarifier service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Clarifier service error: {str(e)}"
        )

@app.post("/api/clarifier/ingest")
async def clarifier_ingest_proxy(request: Request):
    """Proxy clarifier ingest to clarifier service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to clarifier service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CLARIFIER_SERVICE_URL}/clarifier/ingest",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the clarifier service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Clarifier service error: {str(e)}"
        )

@app.get("/api/clarifier/quiz/{session_id}")
async def clarifier_quiz_proxy(session_id: str, request: Request):
    """Proxy clarifier quiz to clarifier service"""
    try:
        # Forward the Authorization header to clarifier service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CLARIFIER_SERVICE_URL}/clarifier/quiz/{session_id}",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the clarifier service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Clarifier service error: {str(e)}"
        )

@app.post("/api/clarifier/grade/{session_id}")
async def clarifier_grade_proxy(session_id: str, request: Request):
    """Proxy clarifier grade to clarifier service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to clarifier service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CLARIFIER_SERVICE_URL}/clarifier/grade/{session_id}",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to grade clarifier quiz"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Clarifier service error: {str(e)}"
        )

# Quiz Generation Proxy Routes

@app.post("/api/quiz/generate/category")
async def generate_quiz_category_proxy(request: Request):
    """Proxy quiz generation by category to quiz service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/quizzes/generate",
                json=body,
                headers=headers,
                timeout=60.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.post("/api/quizzes/generate")
async def generate_quiz_proxy(request: Request):
    """Proxy quiz generation to quiz service and create session"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Step 1: Generate quiz
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/quizzes/generate",
                json=body,
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code != 200:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
            
            quiz_response = response.json()
            quiz_id = quiz_response.get("quiz_id")  # quiz_id is at the top level
            job_id = quiz_response.get("job_id")
            
            if not quiz_id:
                logger.error(f"No quiz_id in response: {quiz_response}")
                return quiz_response
            
            # Step 2: Create session from quiz
            try:
                # Extract user_id from the Authorization header
                user_id = None
                if auth_header and auth_header.startswith("Bearer "):
                    # For now, we'll use a default user_id since the quiz service expects it
                    # In a real implementation, you'd decode the JWT to get the user_id
                    user_id = "default-user"
                
                session_response = await client.post(
                    f"{settings.QUIZ_SERVICE_URL}/quiz-sessions/from-quiz/{quiz_id}",
                    params={"shuffle": "true"},
                    headers=headers,
                    timeout=30.0
                )
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    session_id = session_data.get("session_id")
                    
                    # Update response to include session_id
                    quiz_response["session_id"] = session_id
                    quiz_response["quiz_id"] = quiz_id
                    
                    logger.info(f"Created session {session_id} for quiz {quiz_id}")
                else:
                    logger.warning(f"Failed to create session: {session_response.status_code} - {session_response.text}")
                    quiz_response["session_id"] = None
                    
            except Exception as session_error:
                logger.error(f"Error creating session: {str(session_error)}")
                quiz_response["session_id"] = None
            
            return quiz_response
            
    except Exception as e:
        logger.error(f"Quiz generation proxy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

# Question Budget Service Proxy Routes
@app.post("/api/question-budget/estimate")
async def question_budget_estimate_proxy(request: Request):
    """Proxy question budget estimate to question-budget service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to question-budget service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUESTION_BUDGET_SERVICE_URL}/estimate",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the question-budget service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        logger.error(f"Error proxying question budget estimate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Question budget service error: {str(e)}"
        )

@app.get("/api/quizzes/{quiz_id}/info")
async def get_quiz_proxy(quiz_id: str, request: Request):
    """Proxy get quiz by ID to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/quizzes/{quiz_id}",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/quizzes/{job_id}/status")
async def get_quiz_job_status_proxy(job_id: str, request: Request):
    """Proxy quiz job status to quiz service study-session status endpoint."""
    try:
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/status",
                params={"job_id": job_id},
                headers=headers,
                timeout=30.0,
            )
            if response.status_code == 200:
                return response.json()
            else:
                return Response(
                    content=response.text,
                    status_code=response.status_code,
                    media_type="application/json",
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}",
        )

@app.get("/api/quizzes/{job_id}/events")
async def get_quiz_job_events_proxy(job_id: str, request: Request):
    """Proxy quiz job SSE events to quiz service study-session events endpoint."""
    try:
        auth_header = request.headers.get("authorization")
        headers = {"Accept": "text/event-stream"}
        if auth_header:
            headers["Authorization"] = auth_header
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/study-sessions/events",
                params={"job_id": job_id},
                headers=headers,
                timeout=None,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=response.headers.get("content-type", "text/event-stream"),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}",
        )

@app.get("/api/quiz")
async def get_quizzes_proxy(
    category_id: str = Query(None),
    request: Request = None
):
    """Proxy get quizzes list to quiz service"""
    try:
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization") if request else None
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Build query parameters
        params = {}
        if category_id:
            params["category_id"] = category_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUIZ_SERVICE_URL}/quizzes",
                params=params,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )



# Notification Service Proxy Routes

# REMOVED: Duplicate route that was overriding the quiz service SSE endpoint
# The correct endpoint is at line 1077 which routes to quiz service

@app.get("/api/notifications/queue-status")
async def notification_queue_status_proxy(request: Request):
    """Proxy notification queue status to notification service"""
    try:
        # Forward the Authorization header to notification service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.NOTIFICATION_SERVICE_URL}/notifications/queue-status",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get notification queue status"
                )
    except Exception as e:
        logger.error(f"Error proxying notification queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Notification service error: {str(e)}"
        )

@app.post("/api/notifications/clear-all")
async def clear_all_notifications_proxy(request: Request):
    """Proxy clear all notifications to notification service"""
    try:
        # Forward the Authorization header to notification service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/notifications/clear-all",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to clear all notifications"
                )
    except Exception as e:
        logger.error(f"Error proxying clear all notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Notification service error: {str(e)}"
        )

@app.post("/api/notifications/clear-pending")
async def clear_pending_notifications_proxy(request: Request):
    """Proxy clear pending notifications to notification service"""
    try:
        # Forward the Authorization header to notification service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/notifications/clear-pending",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to clear pending notifications"
                )
    except Exception as e:
        logger.error(f"Error proxying clear pending notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Notification service error: {str(e)}"
        )

@app.post("/api/notifications/clear-by-type")
async def clear_notifications_by_type_proxy(request: Request):
    """Proxy clear notifications by type to notification service"""
    try:
        # Get the request body
        body = await request.json()
        
        # Forward the Authorization header to notification service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/notifications/clear-by-type",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to clear notifications by type"
                )
    except Exception as e:
        logger.error(f"Error proxying clear notifications by type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Notification service error: {str(e)}"
        )



# Test route to verify API gateway is working
@app.get("/api/test")
async def test_route():
    """Test route to verify API gateway is working"""
    return {"message": "API Gateway is working", "timestamp": str(datetime.datetime.now())}

# Simple working quiz session endpoint
@app.post("/api/quiz-session/create")
async def create_quiz_session_simple(
    request: Request = None
):
    """Simple endpoint to create quiz session"""
    try:
        # Get the request body
        body = await request.json()
        quiz_id = body.get("quiz_id")
        
        if not quiz_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="quiz_id is required in request body"
            )
        
        # Forward the Authorization header to quiz service
        auth_header = request.headers.get("authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.QUIZ_SERVICE_URL}/quizzes/{quiz_id}/create-session",
                json=body,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return the actual error from the quiz service
                error_detail = response.text
                return Response(
                    content=error_detail,
                    status_code=response.status_code,
                    media_type="application/json"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz service error: {str(e)}"
        )

@app.get("/api/test-simple")
async def test_simple_route():
    """Simple test route"""
    return {"message": "Simple test route working"}

# MUST be last of all /api routes - catch-all proxy for any unmatched API calls
@app.api_route("/api/{service}/{path:path}",
               methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_catch_all(service: str, path: str, request: Request):
    """Catch-all proxy for any unmatched API routes"""
    logger.info(f"PROXY CATCH-ALL → {request.method} /api/{service}/{path}")
    
    # Handle question-budget service specifically
    if service == "question-budget":
        target_service_url = settings.QUESTION_BUDGET_SERVICE_URL
        target_url = f"{target_service_url}/{path}"
        logger.info(f"PROXY CATCH-ALL → question-budget: {target_url}")
        
        # Forward headers (excluding host)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Forward the request
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if request.method == "GET":
                    response = await client.get(target_url, headers=headers, params=request.query_params)
                elif request.method == "POST":
                    body = await request.body()
                    response = await client.post(target_url, headers=headers, content=body)
                elif request.method == "PUT":
                    body = await request.body()
                    response = await client.put(target_url, headers=headers, content=body)
                elif request.method == "DELETE":
                    response = await client.delete(target_url, headers=headers)
                elif request.method == "PATCH":
                    body = await request.body()
                    response = await client.patch(target_url, headers=headers, content=body)
                elif request.method == "OPTIONS":
                    response = await client.options(target_url, headers=headers)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=f"Method {request.method} not supported"
                    )
                
                # Return the response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service {service} timeout"
            )
        except Exception as e:
            logger.error(f"Proxy catch-all error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Service {service} error: {str(e)}"
            )
    
    # Handle quiz service specifically
    elif service == "quizzes":
        target_service_url = settings.QUIZ_SERVICE_URL
        target_url = f"{target_service_url}/{path}"
        logger.info(f"PROXY CATCH-ALL → quizzes: {target_url}")
        logger.info(f"Quiz service URL: {target_service_url}")
        logger.info(f"Path: {path}")
        logger.info(f"Full target URL: {target_url}")
        
        # Forward headers (excluding host)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Forward the request
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if request.method == "GET":
                    response = await client.get(target_url, headers=headers, params=request.query_params)
                elif request.method == "POST":
                    body = await request.body()
                    response = await client.post(target_url, headers=headers, content=body)
                elif request.method == "PUT":
                    body = await request.body()
                    response = await client.put(target_url, headers=headers, content=body)
                elif request.method == "DELETE":
                    response = await client.delete(target_url, headers=headers)
                elif request.method == "PATCH":
                    body = await request.body()
                    response = await client.patch(target_url, headers=headers, content=body)
                elif request.method == "OPTIONS":
                    response = await client.options(target_url, headers=headers)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=f"Method {request.method} not supported"
                    )
                
                # Return the response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service {service} timeout"
            )
        except Exception as e:
            logger.error(f"Proxy catch-all error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Service {service} error: {str(e)}"
            )
    
    # Handle study-sessions service specifically
    elif service == "study-sessions":
        target_service_url = settings.QUIZ_SERVICE_URL
        target_url = f"{target_service_url}/{path}"
        logger.info(f"PROXY CATCH-ALL → study-sessions: {target_url}")
        logger.info(f"Quiz service URL: {target_service_url}")
        logger.info(f"Path: {path}")
        logger.info(f"Full target URL: {target_url}")
        
        # Forward headers (excluding host)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Forward the request
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if request.method == "GET":
                    response = await client.get(target_url, headers=headers, params=request.query_params)
                elif request.method == "POST":
                    body = await request.body()
                    response = await client.post(target_url, headers=headers, content=body)
                elif request.method == "PUT":
                    body = await request.body()
                    response = await client.put(target_url, headers=headers, content=body)
                elif request.method == "DELETE":
                    response = await client.delete(target_url, headers=headers)
                elif request.method == "PATCH":
                    body = await request.body()
                    response = await client.patch(target_url, headers=headers, content=body)
                elif request.method == "OPTIONS":
                    response = await client.options(target_url, headers=headers)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        detail=f"Method {request.method} not supported"
                    )
                
                # Return the response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service {service} timeout"
            )
        except Exception as e:
            logger.error(f"Proxy catch-all error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Service {service} error: {str(e)}"
            )
    
    # For other services, return 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Service {service} not supported by catch-all proxy"
    )


