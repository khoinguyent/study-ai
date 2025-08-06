from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@document-db:5432/document_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = "your-access-key"
    AWS_SECRET_ACCESS_KEY: str = "your-secret-key"
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "study-ai-documents"
    
    # Services
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    INDEXING_SERVICE_URL: str = "http://indexing-service:8003"
    
    # Service
    SERVICE_NAME: str = "document-service"
    SERVICE_PORT: int = 8002
    
    class Config:
        env_file = ".env"

settings = Settings() 