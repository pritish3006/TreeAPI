"""integration tests for tree operations across all layers."""
import pytest
from sqlalchemy.orm import Session

from app.crud.tree import tree, NodeNotFoundError, CycleError
from app.models.tree import Node
from app.schemas.tree import NodeCreate, NodeCreateResponse

@pytest.mark.asyncio
class TestTreeIntegration:
    """integration test cases for tree operations."""
    
    async def test_create_and_retrieve_tree(self, empty_db: Session):
        """test creating a complex tree and retrieving it.
        
        creates:
            root
            ├── child1
            │   ├── grandchild1
            │   └── grandchild2
            └── child2
                └── grandchild3
        
        tests:
        1. creation with pydantic models
        2. crud operations
        3. database persistence
        4. retrieval with relationships
        """
        # Create root node
        root = await tree.create_node(
            empty_db,
            NodeCreate(label="root")
        )
        assert isinstance(root, Node)
        assert root.label == "root"
        assert root.parent_id is None
        
        # Create child nodes
        child1 = await tree.create_node(
            empty_db,
            NodeCreate(label="child1", parent_id=root.id)
        )
        child2 = await tree.create_node(
            empty_db,
            NodeCreate(label="child2", parent_id=root.id)
        )
        
        # Create grandchildren
        grandchild1 = await tree.create_node(
            empty_db,
            NodeCreate(label="grandchild1", parent_id=child1.id)
        )
        grandchild2 = await tree.create_node(
            empty_db,
            NodeCreate(label="grandchild2", parent_id=child1.id)
        )
        grandchild3 = await tree.create_node(
            empty_db,
            NodeCreate(label="grandchild3", parent_id=child2.id)
        )
        
        # Verify tree structure through different queries
        
        # 1. Get entire forest
        forest = await tree.get_forest(empty_db)
        assert len(forest) == 1  # Only one root
        root_node = forest[0]
        assert root_node.label == "root"
        assert len(root_node.children) == 2
        
        # 2. Get descendants
        descendants = await tree.get_descendants(empty_db, root.id)
        assert len(descendants) == 5  # All nodes except root
        descendant_labels = {node.label for node in descendants}
        assert descendant_labels == {
            "child1", "child2", 
            "grandchild1", "grandchild2", "grandchild3"
        }
        
        # 3. Get specific node with children
        child1_node = await tree.get_node_with_children(empty_db, child1.id)
        assert child1_node.label == "child1"
        assert len(child1_node.children) == 2
        child1_children_labels = {child.label for child in child1_node.children}
        assert child1_children_labels == {"grandchild1", "grandchild2"}
    
    async def test_complex_tree_operations(self, empty_db: Session):
        """test complex operations on a tree.
        
        tests:
        1. moving subtrees
        2. cycle prevention across layers
        3. error handling
        4. data consistency
        """
        # Create initial tree
        root1 = await tree.create_node(empty_db, NodeCreate(label="root1"))
        root2 = await tree.create_node(empty_db, NodeCreate(label="root2"))
        
        child1 = await tree.create_node(
            empty_db, 
            NodeCreate(label="child1", parent_id=root1.id)
        )
        child2 = await tree.create_node(
            empty_db,
            NodeCreate(label="child2", parent_id=root1.id)
        )
        
        grandchild = await tree.create_node(
            empty_db,
            NodeCreate(label="grandchild", parent_id=child1.id)
        )
        
        # Test moving subtrees
        # Move child1 (and its subtree) to root2
        await tree.update_node_parent(empty_db, child1.id, root2.id)
        
        # Verify the move
        root1_node = await tree.get_node_with_children(empty_db, root1.id)
        assert len(root1_node.children) == 1
        assert root1_node.children[0].label == "child2"
        
        root2_node = await tree.get_node_with_children(empty_db, root2.id)
        assert len(root2_node.children) == 1
        assert root2_node.children[0].label == "child1"
        
        # Verify grandchild moved with its parent
        child1_node = await tree.get_node_with_children(empty_db, child1.id)
        assert len(child1_node.children) == 1
        assert child1_node.children[0].label == "grandchild"
        
        # Test cycle prevention
        # Try to make root2 a child of grandchild
        with pytest.raises(CycleError) as exc:
            await tree.update_node_parent(empty_db, root2.id, grandchild.id)
        assert exc.value.status_code == 400
        
        # Verify no changes were made
        root2_after = await tree.get_node_with_children(empty_db, root2.id)
        assert root2_after.parent_id is None
    
    async def test_error_handling_and_validation(self, empty_db: Session):
        """test error handling and validation across layers.
        
        tests:
        1. pydantic validation
        2. database constraints
        3. business logic validation
        4. error propagation
        """
        # Test invalid parent ID
        with pytest.raises(NodeNotFoundError) as exc:
            await tree.create_node(
                empty_db,
                NodeCreate(label="orphan", parent_id=999)
            )
        assert exc.value.status_code == 404
        
        # Create a valid node
        root = await tree.create_node(
            empty_db,
            NodeCreate(label="root")
        )
        
        # Test updating with invalid parent
        with pytest.raises(NodeNotFoundError) as exc:
            await tree.update_node_parent(empty_db, root.id, 999)
        assert exc.value.status_code == 404
        
        # Verify node unchanged
        root_after = await tree.get_node_with_children(empty_db, root.id)
        assert root_after.parent_id is None
        
        # Test getting non-existent node
        missing_node = await tree.get_node_with_children(empty_db, 999)
        assert missing_node is None
        
        # Test getting descendants of non-existent node
        with pytest.raises(NodeNotFoundError) as exc:
            await tree.get_descendants(empty_db, 999)
        assert exc.value.status_code == 404 