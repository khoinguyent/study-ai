from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@quiz-db:5432/quiz_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama2:7b"
    
    # Quiz Generation Strategy
    QUIZ_GENERATION_STRATEGY: str = "auto"  # Options: "ollama", "huggingface", "auto"
    
    # HuggingFace Configuration
    HUGGINGFACE_TOKEN: str = ""
    HUGGINGFACE_API_URL: str = "https://api-inference.huggingface.co/models"
    QUESTION_GENERATION_MODEL: str = "google/flan-t5-base"
    DISTRACTOR_GENERATION_MODEL: str = "google/flan-t5-base"
    
    # Services
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    DOCUMENT_SERVICE_URL: str = "http://document-service:8002"
    INDEXING_SERVICE_URL: str = "http://indexing-service:8003"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"
    
    # Service
    SERVICE_NAME: str = "quiz-service"
    SERVICE_PORT: int = 8004
    
    class Config:
        env_file = ".env"

settings = Settings() 