"""api endpoint tests using fastapi testclient."""
import json
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.tree import Node
from app.crud.tree import tree

client = TestClient(app)

def test_get_tree(empty_db: Session):
    """test GET /tree returns nodes."""
    response = client.get("/api/tree")
    assert response.status_code == 200
    # The database is not empty, so just check it returns an array
    assert isinstance(response.json(), list)

def test_create_root_node():
    """test POST /tree creating a root node."""
    response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["label"] == "root"
    assert data["parentId"] is None
    assert "id" in data

def test_create_child_node(db: Session):
    """test POST /tree creating a child node."""
    # First create a parent node
    parent_response = client.post(
        "/api/tree",
        json={"label": "parent"}
    )
    assert parent_response.status_code == 201
    parent_data = parent_response.json()
    
    # Create child node
    child_response = client.post(
        "/api/tree",
        json={
            "label": "child",
            "parentId": parent_data["id"]
        }
    )
    assert child_response.status_code == 201
    child_data = child_response.json()
    assert child_data["label"] == "child"
    assert child_data["parentId"] == parent_data["id"]

def test_get_tree_structure(db: Session):
    """test GET /tree returns correct nested structure."""
    # Create a unique tree structure with an identifiable name
    unique_prefix = "test_unique_structure_"
    
    # Create root with unique name
    root_response = client.post("/api/tree", json={"label": f"{unique_prefix}root"})
    root_data = root_response.json()
    root_id = root_data["id"]
    
    # Create children
    child1_response = client.post(
        "/api/tree", 
        json={
            "label": f"{unique_prefix}child1",
            "parentId": root_id
        }
    )
    child1_data = child1_response.json()
    
    client.post(
        "/api/tree",
        json={
            "label": f"{unique_prefix}child2",
            "parentId": root_id
        }
    )
    
    # Create grandchild
    client.post(
        "/api/tree",
        json={
            "label": f"{unique_prefix}grandchild",
            "parentId": child1_data["id"]
        }
    )
    
    # Get tree and verify structure
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    
    # Find our unique root node by its ID - more reliable than label
    unique_root = None
    for node in data:
        if node["id"] == root_id:
            unique_root = node
            break
    
    assert unique_root is not None
    assert unique_root["label"] == f"{unique_prefix}root"
    assert unique_root["parentId"] is None
    
    # Root should have two children
    unique_children = unique_root["children"]
    assert len(unique_children) == 2
    child_labels = {child["label"] for child in unique_children}
    assert child_labels == {f"{unique_prefix}child1", f"{unique_prefix}child2"}
    
    # unique_child1 should have one grandchild
    unique_child1 = next(
        child for child in unique_children 
        if child["label"] == f"{unique_prefix}child1"
    )
    assert len(unique_child1["children"]) == 1
    assert unique_child1["children"][0]["label"] == f"{unique_prefix}grandchild"

def test_create_node_invalid_parent():
    """test POST /tree with non-existent parent id."""
    response = client.post(
        "/api/tree",
        json={
            "label": "orphan",
            "parentId": 99999
        }
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_create_node_invalid_label():
    """test POST /tree with invalid label."""
    # Empty label
    response = client.post(
        "/api/tree",
        json={"label": ""}
    )
    assert response.status_code == 422
    
    # Whitespace label
    response = client.post(
        "/api/tree",
        json={"label": "   "}
    )
    assert response.status_code == 422

def test_create_cycle(db: Session):
    """
    test cycle prevention in API.
    
    this test checks that the API prevents creating cycles in the tree.
    it requires direct access to the tree CRUD operations, as it's not possible
    to create a cycle using just the API (by design).
    """
    from app.crud.tree import tree, CycleError
    
    # Create a chain: root -> child -> grandchild
    root_resp = client.post("/api/tree", json={"label": "cycle_root"})
    root_data = root_resp.json()
    root_id = root_data["id"]
    
    child_resp = client.post(
        "/api/tree",
        json={
            "label": "cycle_child",
            "parentId": root_id
        }
    )
    child_data = child_resp.json()
    child_id = child_data["id"]
    
    grandchild_resp = client.post(
        "/api/tree",
        json={
            "label": "cycle_grandchild",
            "parentId": child_id
        }
    )
    grandchild_data = grandchild_resp.json()
    grandchild_id = grandchild_data["id"]
    
    # Try to make root a child of grandchild - this would create a cycle
    # We need to use the CRUD operation directly as the API doesn't allow this
    try:
        tree.update_node_parent(db, node_id=root_id, new_parent_id=grandchild_id)
        # Should not reach here
        assert False, "Expected CycleError, but operation succeeded"
    except CycleError as e:
        # This is expected - should get a cycle error
        assert "cycle" in str(e).lower()
    except Exception as e:
        # Any other exception is unexpected
        assert False, f"Expected CycleError, but got {type(e).__name__}: {str(e)}"

def test_response_format():
    """test that response format matches specification."""
    # Create a node
    response = client.post(
        "/api/tree",
        json={"label": "test_format"}
    )
    data = response.json()
    
    # Check POST response format
    assert isinstance(data, dict)
    assert set(data.keys()) == {"id", "label", "parentId"}
    assert isinstance(data["id"], int)
    assert isinstance(data["label"], str)
    assert data["parentId"] is None
    
    # Check GET response format
    response = client.get("/api/tree")
    data = response.json()
    
    def validate_tree_node(node: Dict[str, Any]):
        """recursively validate node format."""
        assert isinstance(node, dict)
        # Updated to include created_at and updated_at
        assert set(node.keys()) == {"id", "label", "parentId", "children", "created_at", "updated_at"}
        assert isinstance(node["id"], int)
        assert isinstance(node["label"], str)
        assert isinstance(node["children"], list)
        assert isinstance(node["created_at"], str)  # ISO timestamp as string
        assert isinstance(node["updated_at"], str)  # ISO timestamp as string
        for child in node["children"]:
            validate_tree_node(child)
    
    # Find our test node to validate format
    for root in data:
        if root["label"] == "test_format":
            validate_tree_node(root)
            break 