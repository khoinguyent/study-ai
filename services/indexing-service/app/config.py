from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@indexing-db:5432/indexing_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Services
    DOCUMENT_SERVICE_URL: str = "http://document-service:8002"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"
    
    # Vector model settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Service
    SERVICE_NAME: str = "indexing-service"
    SERVICE_PORT: int = 8003
    
    class Config:
        env_file = ".env"

settings = Settings() 