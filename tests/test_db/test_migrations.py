"""tests for database schema and migrations."""
import pytest
from sqlalchemy import inspect, text
from datetime import datetime

from app.models.tree import Node

def test_table_structure(db):
    """test that nodes table has correct structure."""
    inspector = inspect(db.bind)
    
    # Get table info
    columns = {col['name']: col for col in inspector.get_columns('nodes')}
    
    # Check required columns exist
    assert "id" in columns
    assert "label" in columns
    assert "parent_id" in columns
    assert "created_at" in columns
    assert "updated_at" in columns
    
    # Check column types (SQLite uses uppercase type names)
    assert "INTEGER" in str(columns["id"]["type"]).upper()
    assert "VARCHAR" in str(columns["label"]["type"]).upper() or "TEXT" in str(columns["label"]["type"]).upper()
    assert "INTEGER" in str(columns["parent_id"]["type"]).upper()
    assert "DATETIME" in str(columns["created_at"]["type"]).upper()
    assert "DATETIME" in str(columns["updated_at"]["type"]).upper()

def test_foreign_key_constraint(db):
    """test foreign key constraint on parent_id."""
    # Insert parent node
    parent = Node(label="parent")
    db.add(parent)
    db.commit()
    
    # Insert child node
    child = Node(label="child", parent=parent)
    db.add(child)
    db.commit()
    
    # Try to insert child with non-existent parent
    with pytest.raises(Exception) as exc_info:
        orphan = Node(label="orphan", parent_id=999999)
        db.add(orphan)
        db.commit()
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)

def test_indexes(db):
    """test that required indexes exist."""
    inspector = inspect(db.bind)
    
    # Get indexes
    indexes = inspector.get_indexes('nodes')
    index_names = [idx['name'] for idx in indexes]
    
    # Check required indexes exist
    assert "ix_nodes_id" in index_names
    assert "ix_nodes_label" in index_names
    assert "ix_nodes_parent_id" in index_names

def test_timestamp_defaults(db):
    """test that timestamps are set automatically."""
    # Insert node using SQLAlchemy model
    node = Node(label="test_node")
    db.add(node)
    db.commit()
    
    # Verify timestamps
    assert node.created_at is not None
    assert node.updated_at is not None
    assert isinstance(node.created_at, datetime)
    assert isinstance(node.updated_at, datetime)

def test_cascade_delete(db):
    """test that deleting parent cascades to children."""
    # Create parent
    parent = Node(label="parent")
    db.add(parent)
    db.commit()
    
    # Create children
    child1 = Node(label="child1", parent=parent)
    child2 = Node(label="child2", parent=parent)
    db.add_all([child1, child2])
    db.commit()
    
    # Get initial count
    initial_count = db.query(Node).count()
    assert initial_count == 3
    
    # Delete parent
    db.delete(parent)
    db.commit()
    
    # Check that children were deleted
    final_count = db.query(Node).count()
    assert final_count == 0

def test_parent_child_relationships(db):
    """test parent-child relationship cardinality."""
    # Create a parent node
    parent = Node(label="parent")
    db.add(parent)
    db.commit()
    
    # Create multiple children for the same parent (many-to-one)
    child1 = Node(label="child1", parent=parent)
    child2 = Node(label="child2", parent=parent)
    child3 = Node(label="child3", parent=parent)
    db.add_all([child1, child2, child3])
    db.commit()
    
    # Verify parent has multiple children
    db.refresh(parent)
    assert len(parent.children) == 3
    assert all(child.parent_id == parent.id for child in parent.children)
    
    # Verify each child has exactly one parent
    for child in [child1, child2, child3]:
        db.refresh(child)
        assert child.parent_id == parent.id
        assert child.parent == parent

def test_child_parent_reassignment(db):
    """test that a child can be reassigned to a different parent."""
    # Create two parents
    parent1 = Node(label="parent1")
    parent2 = Node(label="parent2")
    db.add_all([parent1, parent2])
    db.commit()
    
    # Create child under parent1
    child = Node(label="child", parent=parent1)
    db.add(child)
    db.commit()
    
    # Verify initial parent
    db.refresh(child)
    assert child.parent_id == parent1.id
    
    # Reassign child to parent2
    child.parent = parent2
    db.commit()
    
    # Verify parent reassignment
    db.refresh(child)
    db.refresh(parent1)
    db.refresh(parent2)
    
    assert child.parent_id == parent2.id
    assert child not in parent1.children
    assert child in parent2.children 