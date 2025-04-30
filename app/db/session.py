"""database session management module."""
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# configure logging
logger = logging.getLogger(__name__)

# enable foreign keys for sqlite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """enable foreign keys and set journal mode for sqlite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # better concurrency
    cursor.close()

# create engine with optimized settings
engine = create_engine(
    settings.DATABASE_URL,
    # connection pooling
    pool_pre_ping=True,  # enable connection health checks
    pool_size=5,  # number of connections to keep open
    max_overflow=10,  # max extra connections to create
    # sqlite optimizations
    connect_args={"check_same_thread": False},  # needed for sqlite
)

# create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # explicit transaction management
    autoflush=False,   # explicit flushing
    expire_on_commit=False  # don't expire objects after commit
)

def get_db() -> Generator[Session, None, None]:
    """fastapi dependency for database sessions.
    
    yields:
        session: database session for the request
        
    raises:
        exception: any database errors are logged and re-raised
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"database session error: {e}")
        raise
    finally:
        db.close()

@contextmanager
def get_db_context():
    """context manager for database sessions.
    
    yields:
        session: database session with automatic commit/rollback
        
    raises:
        exception: any database errors are logged and re-raised
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"database transaction error: {e}")
        raise
    finally:
        db.close()

def verify_database():
    """verify database connection and configuration.
    
    raises:
        exception: if database connection fails
    """
    try:
        db = SessionLocal()
        # test connection
        db.execute(text("SELECT 1"))
        # verify foreign keys
        result = db.execute(text("PRAGMA foreign_keys")).scalar()
        if not result:
            raise ValueError("foreign keys not enabled")
        # verify journal mode
        mode = db.execute(text("PRAGMA journal_mode")).scalar()
        if mode.upper() != "WAL":
            logger.warning(f"journal mode is {mode}, recommended: WAL")
    except Exception as e:
        logger.error(f"database verification failed: {e}")
        raise
    finally:
        db.close() 