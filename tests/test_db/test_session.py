"""tests for database session management."""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, select

from app.db.session import (
    get_db,
    get_db_context,
    verify_database,
    engine,
    SessionLocal
)
from app.models.tree import Node

def test_session_creation():
    """test that session factory creates valid sessions."""
    session = SessionLocal()
    try:
        assert isinstance(session, Session)
        # test connection works
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        session.close()

def test_get_db():
    """test get_db dependency yields working session."""
    db_generator = get_db()
    db = next(db_generator)
    try:
        assert isinstance(db, Session)
        # verify session works by creating and querying a node
        node = Node(label="test")
        db.add(node)
        db.commit()
        
        result = db.execute(select(Node).filter_by(label="test")).scalar_one()
        assert result.label == "test"
    finally:
        try:
            db_generator.close()
        except:
            pass

def test_get_db_context():
    """test context manager handles session correctly."""
    with get_db_context() as session:
        assert isinstance(session, Session)
        # verify session works by creating and querying a node
        node = Node(label="test")
        session.add(node)
        session.commit()
        
        result = session.execute(select(Node).filter_by(label="test")).scalar_one()
        assert result.label == "test"

def test_get_db_context_rollback():
    """test context manager rolls back on error."""
    with pytest.raises(ValueError):
        with get_db_context() as session:
            # Create a node that should be rolled back
            node = Node(label="test_rollback")
            session.add(node)
            session.flush()  # Flush but don't commit
            
            raise ValueError("Test error")
    
    # Verify the node doesn't exist (rollback worked)
    with get_db_context() as session:
        result = session.execute(
            select(Node).filter_by(label="test_rollback")
        ).first()
        assert result is None

def test_verify_database():
    """test database verification function."""
    # should not raise any exceptions
    verify_database()

def test_foreign_keys_enabled():
    """test that foreign keys are enabled."""
    with get_db_context() as session:
        # Create parent and child nodes to test foreign key constraint
        parent = Node(label="parent")
        session.add(parent)
        session.commit()
        
        child = Node(label="child", parent_id=parent.id)
        session.add(child)
        session.commit()
        
        # Try to delete parent (should fail due to FK constraint)
        with pytest.raises(SQLAlchemyError):
            session.delete(parent)
            session.commit()

def test_journal_mode():
    """test that WAL journal mode is set."""
    with get_db_context() as session:
        result = session.execute(text("PRAGMA journal_mode")).scalar()
        assert result.upper() == "WAL"

def test_connection_isolation():
    """test that separate sessions don't interfere."""
    with get_db_context() as session1:
        with get_db_context() as session2:
            # Create a node in session1
            node1 = Node(label="test_isolation")
            session1.add(node1)
            
            # Session2 should not see the uncommitted node
            result = session2.execute(
                select(Node).filter_by(label="test_isolation")
            ).first()
            assert result is None 