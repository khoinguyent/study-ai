from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from .config import settings

security = HTTPBearer()

async def verify_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token using auth service and return user_id"""
    token = credentials.credentials
    
    try:
        # Always use auth service for verification
        async with httpx.AsyncClient() as client:
            auth_url = f"{settings.AUTH_SERVICE_URL}/verify"
            print(f"DEBUG: Calling auth service at {auth_url}")
            response = await client.post(
                auth_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            print(f"DEBUG: Auth service response: {response.status_code}, {response.text}")
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("user_id")
                print(f"DEBUG: Got user_id: {user_id}")
                if user_id:
                    return user_id
        
        print("DEBUG: Auth verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.TimeoutException as e:
        print(f"DEBUG: Timeout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timeout",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"DEBUG: Exception in auth verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
