import logging
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from strawberry.fastapi import GraphQLRouter
from .http_client import http_client
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

@app.post("/study-sessions/start")
async def start_study_session_proxy(request: Request):
    """Proxy study session start requests to clarifier service"""
    try:
        # Forward the Authorization header to Clarifier Service
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the request body and ensure Content-Type is set
        body = await request.body()
        if not headers.get("Content-Type"):
            headers["Content-Type"] = "application/json"
        
        # Forward the request with robust retry logic
        response = http_client.post_with_retry(
            url=f"{settings.CLARIFIER_SERVICE_URL}/clarifier/start",
            data=body,
            headers=headers,
            timeout=(0.5, 3.0)  # (connect_timeout, read_timeout)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = "Failed to start study session"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_detail)
            except:
                pass
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
    except Exception as e:
        logger.error(f"Study session start failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study session start service error: {repr(e)}"
        )

@app.post("/study-sessions/ingest")
async def ingest_study_session_proxy(request: Request):
    """Proxy study session ingest requests to clarifier service"""
    try:
        # Forward the Authorization header to Clarifier Service
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the request body as JSON
        body = await request.json()
        
        # Forward the request with robust retry logic
        response = http_client.post_with_retry(
            url=f"{settings.CLARIFIER_SERVICE_URL}/clarifier/ingest",
            json=body,
            headers=headers,
            timeout=(0.5, 3.0)  # (connect_timeout, read_timeout)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = "Failed to ingest study session input"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_detail)
            except:
                pass
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
    except Exception as e:
        logger.error(f"Study session ingest failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study session ingest service error: {repr(e)}"
        )

@app.post("/study-sessions/confirm")
async def confirm_study_session_proxy(request: Request):
    """Proxy study session confirm requests to clarifier service"""
    try:
        # Forward the Authorization header to Clarifier Service
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get the request body as JSON
        body = await request.json()
        
        # Forward the request with robust retry logic
        response = http_client.post_with_retry(
            url=f"{settings.CLARIFIER_SERVICE_URL}/clarifier/confirm",
            json=body,
            headers=headers,
            timeout=(0.5, 3.0)  # (connect_timeout, read_timeout)
        )
        
        if response.status_code in [200, 202]:
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
    except Exception as e:
        logger.error(f"Study session confirm failed: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study session confirm service error: {repr(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Force reload
