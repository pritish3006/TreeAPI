"""database utility functions."""
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine, SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

def check_database_connection() -> bool:
    """verify database connection.
    
    returns:
        bool: true if connection successful
        
    raises:
        sqlalchemyerror: if connection fails
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.error(f"database connection failed: {e}")
        raise

def get_table_info(table_name: str) -> Optional[Dict[str, Any]]:
    """get detailed information about a table.
    
    args:
        table_name: name of the table to inspect
        
    returns:
        dict: table information including columns and indexes
    """
    try:
        inspector = inspect(engine)
        
        # get column information
        columns = inspector.get_columns(table_name)
        
        # get index information
        indexes = inspector.get_indexes(table_name)
        
        # get foreign key information
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        return {
            "columns": columns,
            "indexes": indexes,
            "foreign_keys": foreign_keys
        }
    except SQLAlchemyError as e:
        logger.error(f"failed to get table info for {table_name}: {e}")
        return None

def analyze_query(query: str) -> Optional[str]:
    """analyze query execution plan.
    
    args:
        query: sql query to analyze
        
    returns:
        str: query execution plan
    """
    try:
        with SessionLocal() as session:
            result = session.execute(text(f"EXPLAIN QUERY PLAN {query}"))
            return "\n".join([str(row) for row in result])
    except SQLAlchemyError as e:
        logger.error(f"query analysis failed: {e}")
        return None

def optimize_database() -> bool:
    """perform database optimization tasks.
    
    returns:
        bool: true if optimization successful
    """
    try:
        with SessionLocal() as session:
            # analyze tables
            session.execute(text("ANALYZE"))
            
            # optimize indexes
            session.execute(text("PRAGMA optimize"))
            
            # clean up unused space
            session.execute(text("VACUUM"))
            
            return True
    except SQLAlchemyError as e:
        logger.error(f"database optimization failed: {e}")
        return False

def get_database_stats() -> Dict[str, Any]:
    """get database statistics and health metrics.
    
    returns:
        dict: database statistics
    """
    try:
        with SessionLocal() as session:
            stats = {}
            
            # get database size
            page_size = session.execute(text("PRAGMA page_size")).scalar()
            page_count = session.execute(text("PRAGMA page_count")).scalar()
            stats["size_bytes"] = page_size * page_count
            
            # get table sizes
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            table_stats = {}
            
            for table in tables:
                count = session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar()
                table_stats[table] = {"row_count": count}
            
            stats["tables"] = table_stats
            
            # get settings
            stats["journal_mode"] = session.execute(
                text("PRAGMA journal_mode")
            ).scalar()
            stats["foreign_keys"] = session.execute(
                text("PRAGMA foreign_keys")
            ).scalar()
            
            return stats
    except SQLAlchemyError as e:
        logger.error(f"failed to get database stats: {e}")
        return {"error": str(e)} 