from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Service URLs
    DOCUMENT_SERVICE_URL: Optional[str] = "http://document-service:8002"
    AUTH_SERVICE_URL: Optional[str] = "http://auth-service:8001"
    QUIZ_SERVICE_URL: Optional[str] = "http://quiz-service:8004"
    NOTIFICATION_SERVICE_URL: Optional[str] = "http://notification-service:8005"
    INDEXING_SERVICE_URL: Optional[str] = "http://indexing-service:8003"
    CLARIFIER_SERVICE_URL: Optional[str] = "http://clarifier-svc:8010"
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # JWT Settings (should match auth service)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
