import os
from dotenv import load_dotenv
from typing import Literal

load_dotenv()

class Config:
    """Configuration class for different environments"""
    
    # Environment
    ENV = os.getenv('ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/study_ai')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB
    
    # Storage Configuration
    STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'local')  # 'local' (MinIO) or 'cloud' (AWS S3)
    
    # MinIO Configuration (for local development)
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'study-ai-documents')
    MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
    
    # AWS S3 Configuration (for production)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'study-ai-documents')
    
    # LLM Configuration
    LLM_TYPE = os.getenv('LLM_TYPE', 'local')  # 'local' (Ollama/LlamaIndex) or 'cloud' (OpenAI)
    
    # OpenAI Configuration (for production)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
    
    # Ollama Configuration (for local development)
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')
    OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'llama2')
    
    # LlamaIndex Configuration (for local development)
    LLAMAINDEX_MODEL_PATH = os.getenv('LLAMAINDEX_MODEL_PATH', './models/')
    LLAMAINDEX_MODEL_NAME = os.getenv('LLAMAINDEX_MODEL_NAME', 'llama-2-7b-chat.gguf')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.ENV.lower() in ['development', 'dev', 'local']
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.ENV.lower() in ['production', 'prod']
    
    @classmethod
    def use_local_storage(cls) -> bool:
        """Check if using local storage (MinIO)"""
        return cls.STORAGE_TYPE.lower() == 'local' or cls.is_development()
    
    @classmethod
    def use_local_llm(cls) -> bool:
        """Check if using local LLM (Ollama/LlamaIndex)"""
        return cls.LLM_TYPE.lower() == 'local' or cls.is_development()
    
    @classmethod
    def get_storage_config(cls) -> dict:
        """Get storage configuration based on environment"""
        if cls.use_local_storage():
            return {
                'type': 'minio',
                'endpoint': cls.MINIO_ENDPOINT,
                'access_key': cls.MINIO_ACCESS_KEY,
                'secret_key': cls.MINIO_SECRET_KEY,
                'bucket_name': cls.MINIO_BUCKET_NAME,
                'secure': cls.MINIO_SECURE
            }
        else:
            return {
                'type': 's3',
                'access_key_id': cls.AWS_ACCESS_KEY_ID,
                'secret_access_key': cls.AWS_SECRET_ACCESS_KEY,
                'region': cls.AWS_REGION,
                'bucket_name': cls.S3_BUCKET_NAME
            }
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration based on environment"""
        if cls.use_local_llm():
            return {
                'type': 'local',
                'ollama_base_url': cls.OLLAMA_BASE_URL,
                'ollama_model': cls.OLLAMA_MODEL,
                'ollama_embedding_model': cls.OLLAMA_EMBEDDING_MODEL,
                'llamaindex_model_path': cls.LLAMAINDEX_MODEL_PATH,
                'llamaindex_model_name': cls.LLAMAINDEX_MODEL_NAME
            }
        else:
            return {
                'type': 'openai',
                'api_key': cls.OPENAI_API_KEY,
                'model': cls.OPENAI_MODEL,
                'embedding_model': cls.OPENAI_EMBEDDING_MODEL
            }

# Global config instance
config = Config() 