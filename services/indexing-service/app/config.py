from pydantic_settings import BaseSettings, SettingsConfigDict
import os

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
    # Legacy fixed chunking (backward compatible)
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Dynamic chunking (LaBSE-aware)
    CHUNK_MODE: str = "FIXED"  # DYNAMIC | FIXED
    CHUNK_BASE_TOKENS: int = 320
    CHUNK_MIN_TOKENS: int = 180
    CHUNK_MAX_TOKENS: int = 480
    CHUNK_SENT_OVERLAP_RATIO: float = 0.12
    LABSE_MAX_TOKENS: int = 512
    DENSITY_WEIGHT_SYMBOLS: float = 0.4
    DENSITY_WEIGHT_AVGWORD: float = 0.3
    DENSITY_WEIGHT_NUMBERS: float = 0.3
    DYNAMIC_HIERARCHY_ENABLE: bool = False
    
    # HuggingFace Configuration (for embedding model)
    HUGGINGFACE_TOKEN: str = ""
    
    # Service
    SERVICE_NAME: str = "indexing-service"
    SERVICE_PORT: int = 8003
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore"
    )

# Create settings instance
settings = Settings()

# Explicitly override with environment variables if they exist
if os.environ.get('CHUNK_MODE'):
    settings.CHUNK_MODE = os.environ.get('CHUNK_MODE')
if os.environ.get('CHUNK_BASE_TOKENS'):
    settings.CHUNK_BASE_TOKENS = int(os.environ.get('CHUNK_BASE_TOKENS'))
if os.environ.get('CHUNK_MIN_TOKENS'):
    settings.CHUNK_MIN_TOKENS = int(os.environ.get('CHUNK_MIN_TOKENS'))
if os.environ.get('CHUNK_MAX_TOKENS'):
    settings.CHUNK_MAX_TOKENS = int(os.environ.get('CHUNK_MAX_TOKENS'))
if os.environ.get('LABSE_MAX_TOKENS'):
    settings.LABSE_MAX_TOKENS = int(os.environ.get('LABSE_MAX_TOKENS'))
if os.environ.get('EMBEDDING_MODEL'):
    settings.EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL')

# Debug: Print environment variables and final config values
print(f"Environment CHUNK_MODE: {os.environ.get('CHUNK_MODE', 'NOT_SET')}")
print(f"Final config CHUNK_MODE: {settings.CHUNK_MODE}")
print(f"Environment CHUNK_BASE_TOKENS: {os.environ.get('CHUNK_BASE_TOKENS', 'NOT_SET')}")
print(f"Final config CHUNK_BASE_TOKENS: {settings.CHUNK_BASE_TOKENS}") 