"""database configuration and session management."""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Create declarative base for models
Base = declarative_base()

# Create SQLite engine with proper configuration
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False  # Needed for SQLite
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    database session dependency.
    
    yields:
        session: sqlalchemy database session
        
    note:
        this is a dependency that will be used in fastapi endpoints
        it ensures proper session management and cleanup
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 