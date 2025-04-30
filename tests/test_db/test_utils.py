"""tests for database utility functions."""
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, select, inspect

from app.db.utils import (
    check_database_connection,
    get_table_info,
    analyze_query,
    optimize_database,
    get_database_stats
)
from app.db.session import get_db_context
from app.models.tree import Node

def test_check_database_connection():
    """test database connection check."""
    assert check_database_connection() is True

def test_get_table_info_nonexistent():
    """test getting info for non-existent table."""
    info = get_table_info("nonexistent_table")
    assert info is None

def test_get_table_info_nodes():
    """test getting info for nodes table."""
    info = get_table_info("nodes")
    assert info is not None
    assert "columns" in info
    assert "indexes" in info
    assert "foreign_keys" in info
    
    # verify column info
    columns = {col["name"]: col for col in info["columns"]}
    assert "id" in columns
    assert "label" in columns
    assert "parent_id" in columns
    
    # verify index info
    index_names = [idx["name"] for idx in info["indexes"]]
    assert any("label" in idx.lower() for idx in index_names)
    
    # verify foreign key info
    fks = info["foreign_keys"]
    assert len(fks) == 1
    assert fks[0]["referred_table"] == "nodes"

def test_analyze_query():
    """test query plan analysis."""
    with get_db_context() as session:
        # Create test data
        node = Node(label="test_analyze")
        session.add(node)
        session.commit()
        
        # Analyze query using the model
        query = str(select(Node).filter_by(id=node.id).compile(
            compile_kwargs={"literal_binds": True}
        ))
        plan = analyze_query(query)
        
        assert plan is not None
        # SQLite might use different terms, we'll check for common query plan terms
        assert any(term in plan.upper() for term in ["SCAN", "SEARCH", "INDEX"])

def test_analyze_query_invalid():
    """test analysis of invalid query."""
    plan = analyze_query("SELECT * FROM nonexistent_table")
    assert plan is None

def test_optimize_database():
    """test database optimization."""
    assert optimize_database() is True

def test_get_database_stats():
    """test database statistics gathering."""
    # Create some test data
    with get_db_context() as session:
        nodes = [Node(label=f"test_stats_{i}") for i in range(3)]
        session.add_all(nodes)
        session.commit()
    
    stats = get_database_stats()
    assert stats is not None
    assert "size_bytes" in stats
    assert "tables" in stats
    assert "journal_mode" in stats
    assert "foreign_keys" in stats
    
    # verify stats values
    assert isinstance(stats["size_bytes"], int)
    assert stats["size_bytes"] > 0
    assert stats["journal_mode"].upper() == "WAL"
    assert stats["foreign_keys"] == 1
    
    # verify table stats
    assert "nodes" in stats["tables"]
    assert stats["tables"]["nodes"]["row_count"] >= 3  # at least our test nodes

@pytest.fixture(autouse=True)
def cleanup_test_tables():
    """cleanup test tables after each test."""
    yield
    with get_db_context() as session:
        session.execute(text("DROP TABLE IF EXISTS test_analyze"))
        session.execute(text("DROP TABLE IF EXISTS nodes")) 