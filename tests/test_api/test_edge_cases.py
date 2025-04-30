"""edge case and data consistency tests for tree api."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import string
import random

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.tree import Node

client = TestClient(app)

def test_deep_tree():
    """test creating and retrieving a very deep tree."""
    # Create a chain of 100 nodes
    current_id = None
    depth = 100
    
    # Create deep chain
    for i in range(depth):
        response = client.post(
            "/api/tree",
            json={
                "label": f"node_{i}",
                "parentId": current_id
            }
        )
        assert response.status_code == 201
        current_id = response.json()["id"]
    
    # Get tree and verify structure
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the chain
    def count_depth(node) -> int:
        """recursively count depth of tree."""
        if not node["children"]:
            return 1
        return 1 + count_depth(node["children"][0])
    
    assert count_depth(data[0]) == depth

def test_wide_tree():
    """test creating and retrieving a very wide tree."""
    # Create root
    root_response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    assert root_response.status_code == 201
    root_id = root_response.json()["id"]
    
    # Create 1000 children
    width = 1000
    for i in range(width):
        response = client.post(
            "/api/tree",
            json={
                "label": f"child_{i}",
                "parentId": root_id
            }
        )
        assert response.status_code == 201
    
    # Get tree and verify
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    
    # Should have one root with 1000 children
    assert len(data) == 1
    root = data[0]
    assert len(root["children"]) == width

def test_special_characters():
    """test labels with special characters."""
    special_chars = string.punctuation + string.whitespace
    
    # Test each special character
    for char in special_chars:
        label = f"test{char}node"
        response = client.post(
            "/api/tree",
            json={"label": label}
        )
        assert response.status_code == 201
        assert response.json()["label"] == label

def test_max_label_length():
    """test maximum label length."""
    # Test label at max length (255)
    max_label = "a" * 255
    response = client.post(
        "/api/tree",
        json={"label": max_label}
    )
    assert response.status_code == 201
    
    # Test label exceeding max length
    too_long = "a" * 256
    response = client.post(
        "/api/tree",
        json={"label": too_long}
    )
    assert response.status_code == 422

def test_concurrent_operations():
    """test concurrent tree operations."""
    # Create a root node
    root_response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    root_id = root_response.json()["id"]
    
    def create_child():
        """create a child node."""
        return client.post(
            "/api/tree",
            json={
                "label": f"child_{random.randint(1, 1000)}",
                "parentId": root_id
            }
        )
    
    # Create 50 children concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(create_child)
            for _ in range(50)
        ]
        responses = [f.result() for f in futures]
    
    # Verify all operations succeeded
    assert all(r.status_code == 201 for r in responses)
    
    # Verify tree structure
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    root = data[0]
    assert len(root["children"]) == 50

def test_duplicate_labels():
    """test nodes with duplicate labels."""
    # Create multiple nodes with same label
    label = "duplicate"
    
    # Create root
    root_response = client.post(
        "/api/tree",
        json={"label": label}
    )
    assert root_response.status_code == 201
    root_id = root_response.json()["id"]
    
    # Create child with same label
    child_response = client.post(
        "/api/tree",
        json={
            "label": label,
            "parentId": root_id
        }
    )
    assert child_response.status_code == 201
    
    # Verify tree structure
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    
    # Both nodes should exist with same label
    root = data[0]
    assert root["label"] == label
    assert root["children"][0]["label"] == label

def test_transaction_rollback():
    """test transaction rollback on error."""
    # Create a root node
    root_response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    root_id = root_response.json()["id"]
    
    # Try to create an invalid node (should trigger rollback)
    response = client.post(
        "/api/tree",
        json={
            "label": "a" * 256,  # Too long
            "parentId": root_id
        }
    )
    assert response.status_code == 422
    
    # Verify tree structure unchanged
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    root = data[0]
    assert len(root["children"]) == 0

def test_unicode_labels():
    """test labels with unicode characters."""
    unicode_labels = [
        "树",  # Chinese
        "ツリー",  # Japanese
        "나무",  # Korean
        "🌳",  # Emoji
        "árbol",  # Spanish with accent
        "дерево",  # Russian
        "شجرة",  # Arabic
    ]
    
    for label in unicode_labels:
        response = client.post(
            "/api/tree",
            json={"label": label}
        )
        assert response.status_code == 201
        assert response.json()["label"] == label 