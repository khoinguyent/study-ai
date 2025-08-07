"""
Configuration settings for Leaf Quiz Service
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # HuggingFace Configuration
    huggingface_token: str
    huggingface_api_url: str = "https://api-inference.huggingface.co/models"
    
    # Model Configuration
    question_generation_model: str = "google/flan-t5-base"
    distractor_generation_model: str = "google/flan-t5-base"
    
    # Database Configuration
    database_url: str
    
    # Service Configuration
    service_port: int = 8006
    service_host: str = "0.0.0.0"
    
    # External Services
    auth_service_url: str = "http://auth-service:8001"
    document_service_url: str = "http://document-service:8002"
    indexing_service_url: str = "http://indexing-service:8003"
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 