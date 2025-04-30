"""database initialization script."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

def init_db() -> None:
    """initialize the database with required tables."""
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create a session to test connection
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Test connection
        db.execute(text("SELECT 1"))
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Initializing database...")
    init_db() 