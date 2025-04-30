"""test suite for node crud operations.

tests the core database operations for the tree structure:
- node creation
- tree retrieval
- cycle detection
- cascade deletion
"""
import pytest
from sqlalchemy.orm import Session
from app.models.tree import Node
from app.crud import nodes

def test_create_root_node(db: Session):
    """test creating a root node without parent."""
    node = nodes.create_node(db, label="Root")
    assert node.id is not None
    assert node.label == "Root"
    assert node.parent_id is None

def test_create_child_node(db: Session):
    """test creating a child node with parent reference."""
    parent = nodes.create_node(db, label="Parent")
    child = nodes.create_node(db, label="Child", parent_id=parent.id)
    assert child.parent_id == parent.id

def test_get_all_nodes(db: Session):
    """test retrieving all nodes from empty database."""
    all_nodes = nodes.get_all_nodes(db)
    assert isinstance(all_nodes, list)

def test_cycle_prevention(db: Session):
    """test that cycles in the tree structure are prevented."""
    parent = nodes.create_node(db, label="Parent")
    child = nodes.create_node(db, label="Child", parent_id=parent.id)
    with pytest.raises(ValueError):
        nodes.create_node(db, label="Invalid", parent_id=child.id)

def test_cascade_delete(db: Session):
    """test that deleting a parent cascades to children."""
    parent = nodes.create_node(db, label="Parent")
    child1 = nodes.create_node(db, label="Child1", parent_id=parent.id)
    child2 = nodes.create_node(db, label="Child2", parent_id=parent.id)
    
    db.delete(parent)
    db.commit()
    
    assert nodes.get_node(db, child1.id) is None
    assert nodes.get_node(db, child2.id) is None

def test_node_timestamps(db: Session):
    """test that timestamps are automatically managed."""
    node = nodes.create_node(db, label="Test")
    assert node.created_at is not None
    assert node.updated_at is not None
    
    original_updated_at = node.updated_at
    node.label = "Updated"
    db.commit()
    db.refresh(node)
    assert node.updated_at > original_updated_at 