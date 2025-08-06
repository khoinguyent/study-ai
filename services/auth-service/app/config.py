from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@auth-db:5432/auth_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Service
    SERVICE_NAME: str = "auth-service"
    SERVICE_PORT: int = 8001
    
    class Config:
        env_file = ".env"

settings = Settings() 