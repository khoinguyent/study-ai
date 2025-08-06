from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@notification-db:5432/notification_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Services
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    
    # Service
    SERVICE_NAME: str = "notification-service"
    SERVICE_PORT: int = 8005
    
    # WebSocket
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8005
    
    class Config:
        env_file = ".env"

settings = Settings() 