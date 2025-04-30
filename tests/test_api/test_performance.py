"""performance tests for tree api."""
import time
from concurrent.futures import ThreadPoolExecutor
import statistics
from typing import List, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app

client = TestClient(app)

def measure_response_time(func) -> Tuple[float, any]:
    """measure response time of a function.
    
    args:
        func: function to measure
        
    returns:
        tuple of (response time in ms, function result)
    """
    start = time.time()
    result = func()
    end = time.time()
    return (end - start) * 1000, result  # Convert to milliseconds

def test_read_performance_large_tree():
    """test read performance with large tree structure."""
    # Create a large tree with 1000 nodes
    root_response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    root_id = root_response.json()["id"]
    
    # Create 1000 nodes in a balanced structure
    nodes_per_level = 10
    levels = 3  # This will create 1 + 10 + 100 + 1000 = 1111 nodes
    
    def create_level(parent_id: int, current_level: int):
        """create a level of nodes."""
        if current_level >= levels:
            return
        
        for i in range(nodes_per_level):
            response = client.post(
                "/api/tree",
                json={
                    "label": f"node_l{current_level}_{i}",
                    "parentId": parent_id
                }
            )
            assert response.status_code == 201
            new_id = response.json()["id"]
            create_level(new_id, current_level + 1)
    
    create_level(root_id, 0)
    
    # Measure read performance
    read_times: List[float] = []
    iterations = 10
    
    for _ in range(iterations):
        time_ms, response = measure_response_time(
            lambda: client.get("/api/tree")
        )
        assert response.status_code == 200
        read_times.append(time_ms)
    
    avg_read_time = statistics.mean(read_times)
    max_read_time = max(read_times)
    
    # Assert reasonable performance
    assert avg_read_time < 1000  # Average read should be under 1 second
    assert max_read_time < 2000  # Max read should be under 2 seconds

def test_write_performance():
    """test write performance with concurrent operations."""
    # Create a root node
    root_response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    root_id = root_response.json()["id"]
    
    # Function to create a child node
    def create_child(i: int) -> Tuple[float, any]:
        """create a child node and measure time."""
        return measure_response_time(
            lambda: client.post(
                "/api/tree",
                json={
                    "label": f"child_{i}",
                    "parentId": root_id
                }
            )
        )
    
    # Create 100 nodes concurrently and measure time
    write_times: List[float] = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(create_child, i)
            for i in range(100)
        ]
        for future in futures:
            time_ms, response = future.result()
            assert response.status_code == 201
            write_times.append(time_ms)
    
    avg_write_time = statistics.mean(write_times)
    max_write_time = max(write_times)
    
    # Assert reasonable performance
    assert avg_write_time < 500  # Average write should be under 500ms
    assert max_write_time < 1000  # Max write should be under 1 second

def test_deep_tree_performance():
    """test performance with very deep tree traversal."""
    # Create a deep chain of nodes
    current_id = None
    depth = 100
    creation_times: List[float] = []
    
    # Create deep chain and measure creation time
    for i in range(depth):
        time_ms, response = measure_response_time(
            lambda: client.post(
                "/api/tree",
                json={
                    "label": f"node_{i}",
                    "parentId": current_id
                }
            )
        )
        assert response.status_code == 201
        current_id = response.json()["id"]
        creation_times.append(time_ms)
    
    # Measure retrieval time
    retrieval_times: List[float] = []
    iterations = 10
    
    for _ in range(iterations):
        time_ms, response = measure_response_time(
            lambda: client.get("/api/tree")
        )
        assert response.status_code == 200
        retrieval_times.append(time_ms)
    
    # Calculate metrics
    avg_create = statistics.mean(creation_times)
    max_create = max(creation_times)
    avg_retrieve = statistics.mean(retrieval_times)
    max_retrieve = max(retrieval_times)
    
    # Assert reasonable performance
    assert avg_create < 100  # Average node creation under 100ms
    assert max_create < 200  # Max node creation under 200ms
    assert avg_retrieve < 500  # Average tree retrieval under 500ms
    assert max_retrieve < 1000  # Max tree retrieval under 1 second

def test_wide_tree_performance():
    """test performance with very wide tree structure."""
    # Create root
    root_response = client.post(
        "/api/tree",
        json={"label": "root"}
    )
    root_id = root_response.json()["id"]
    
    # Create 1000 direct children
    width = 1000
    creation_times: List[float] = []
    
    for i in range(width):
        time_ms, response = measure_response_time(
            lambda: client.post(
                "/api/tree",
                json={
                    "label": f"child_{i}",
                    "parentId": root_id
                }
            )
        )
        assert response.status_code == 201
        creation_times.append(time_ms)
    
    # Measure retrieval time
    retrieval_times: List[float] = []
    iterations = 10
    
    for _ in range(iterations):
        time_ms, response = measure_response_time(
            lambda: client.get("/api/tree")
        )
        assert response.status_code == 200
        retrieval_times.append(time_ms)
    
    # Calculate metrics
    avg_create = statistics.mean(creation_times)
    max_create = max(creation_times)
    avg_retrieve = statistics.mean(retrieval_times)
    max_retrieve = max(retrieval_times)
    
    # Assert reasonable performance
    assert avg_create < 100  # Average node creation under 100ms
    assert max_create < 200  # Max node creation under 200ms
    assert avg_retrieve < 1000  # Average tree retrieval under 1 second
    assert max_retrieve < 2000  # Max tree retrieval under 2 seconds 