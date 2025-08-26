from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine with connection pooling and retry logic
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pooling configuration
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections when pool is full
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
    pool_timeout=30,  # Timeout for getting connection from pool
    
    # Connection retry and timeout settings
    connect_args={
        "connect_timeout": 10,
        "application_name": "document-service",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
    
    # Engine configuration
    echo=False,  # Set to True for SQL debugging
    future=True,  # Use SQLAlchemy 2.0 style
)

# Create SessionLocal class with retry logic
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent expired object access issues
)

# Create Base class
Base = declarative_base()

# Dependency to get database session with retry logic
def get_db():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            # Test the connection
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            try:
                yield db
            finally:
                db.close()
            break  # Success, exit retry loop
            
        except Exception as e:
            retry_count += 1
            logger.warning(f"Database connection attempt {retry_count} failed: {str(e)}")
            
            if retry_count >= max_retries:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise e
            
            # Wait before retrying (exponential backoff)
            import time
            time.sleep(2 ** retry_count)

# Create all tables
def create_tables():
    # Import models here to ensure they are registered with Base
    from .models import Subject, Category, Document
    Base.metadata.create_all(bind=engine)

# Health check function
def check_database_health():
    """Check if database is accessible and responsive"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

# Connection pool monitoring
def get_pool_status():
    """Get current connection pool status"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow()
    } 