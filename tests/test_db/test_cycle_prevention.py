"""tests for cycle prevention in tree structure."""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tree import Node

def test_prevent_self_reference(db: Session):
    """test that a node cannot reference itself as parent."""
    # Create a node
    node = Node(label="test")
    db.add(node)
    db.commit()
    
    # Try to make it its own parent
    with pytest.raises(IntegrityError) as exc_info:
        node.parent_id = node.id
        db.commit()
    
    # Verify error
    assert "foreign key constraint failed" in str(exc_info.value).lower()

def test_prevent_direct_cycle(db: Session):
    """test that two nodes cannot form a direct cycle."""
    # Create two nodes
    node1 = Node(label="node1")
    node2 = Node(label="node2", parent=node1)
    db.add_all([node1, node2])
    db.commit()
    
    # Try to make node1 a child of node2
    with pytest.raises(IntegrityError) as exc_info:
        node1.parent = node2
        db.commit()
    
    # Verify error
    assert "foreign key constraint failed" in str(exc_info.value).lower()

def test_prevent_indirect_cycle(db: Session):
    """test that nodes cannot form an indirect cycle through multiple levels."""
    # Create a chain: root -> child -> grandchild
    root = Node(label="root")
    child = Node(label="child", parent=root)
    grandchild = Node(label="grandchild", parent=child)
    db.add_all([root, child, grandchild])
    db.commit()
    
    # Try to make root a child of grandchild
    with pytest.raises(IntegrityError) as exc_info:
        root.parent = grandchild
        db.commit()
    
    # Verify error
    assert "foreign key constraint failed" in str(exc_info.value).lower()

def test_valid_reassignment(db: Session):
    """test that valid node reassignment is allowed."""
    # Create two separate branches
    root1 = Node(label="root1")
    child1 = Node(label="child1", parent=root1)
    
    root2 = Node(label="root2")
    child2 = Node(label="child2", parent=root2)
    
    db.add_all([root1, child1, root2, child2])
    db.commit()
    
    # Move child1 to be under root2 (valid operation)
    child1.parent = root2
    db.commit()
    
    # Verify the new structure
    db.refresh(root1)
    db.refresh(root2)
    db.refresh(child1)
    
    assert child1.parent_id == root2.id
    assert child1 not in root1.children
    assert child1 in root2.children

def test_deep_tree_reassignment(db: Session):
    """test reassignment in a deep tree structure."""
    # Create a deep tree:
    # root -> level1 -> level2 -> level3 -> level4
    root = Node(label="root")
    level1 = Node(label="level1", parent=root)
    level2 = Node(label="level2", parent=level1)
    level3 = Node(label="level3", parent=level2)
    level4 = Node(label="level4", parent=level3)
    
    db.add_all([root, level1, level2, level3, level4])
    db.commit()
    
    # Try to create a cycle by making root a child of level4
    with pytest.raises(IntegrityError) as exc_info:
        root.parent = level4
        db.commit()
    
    # Verify error
    assert "foreign key constraint failed" in str(exc_info.value).lower()
    
    # But moving level2 to be directly under root should work
    level2.parent = root
    db.commit()
    
    # Verify the new structure
    db.refresh(root)
    db.refresh(level1)
    db.refresh(level2)
    
    assert level2.parent_id == root.id
    assert level2 in root.children
    assert level2 not in level1.children 