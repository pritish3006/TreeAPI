"""unit tests for tree crud operations."""
import pytest
from sqlalchemy.orm import Session

from app.crud.tree import tree, NodeNotFoundError, CycleError
from app.models.tree import Node
from app.schemas.tree import NodeCreate


@pytest.mark.asyncio
class TestTreeCRUD:
    """test cases for tree crud operations."""
    
    async def test_get_forest_empty(self, empty_db: Session):
        """test get_forest with empty database (0 case)."""
        result = await tree.get_forest(empty_db)
        assert result == []
    
    async def test_create_root_node(self, empty_db: Session):
        """test creating a single root node (1 case)."""
        node_in = NodeCreate(label="root")
        node = await tree.create_node(empty_db, node_in)
        
        assert node.label == "root"
        assert node.parent_id is None
        assert node.id is not None
    
    async def test_create_child_node(self, empty_db: Session):
        """test creating a child node (1 case)."""
        # create parent first
        parent_in = NodeCreate(label="parent")
        parent = await tree.create_node(empty_db, parent_in)
        
        # create child
        child_in = NodeCreate(label="child", parent_id=parent.id)
        child = await tree.create_node(empty_db, child_in)
        
        assert child.label == "child"
        assert child.parent_id == parent.id
    
    async def test_get_forest_with_multiple_trees(self, sample_tree: list[Node], db: Session):
        """test get_forest with multiple trees (many case)."""
        forest = await tree.get_forest(db)
        
        # should return both root nodes
        assert len(forest) == 2
        assert {node.label for node in forest} == {"root1", "root2"}
        
        # check children are loaded
        root1 = next(node for node in forest if node.label == "root1")
        assert len(root1.children) == 2
        assert {child.label for child in root1.children} == {"child1", "child2"}
    
    async def test_get_node_with_children(self, sample_tree: list[Node], db: Session):
        """test getting a node with its children."""
        # get child1 which has two children
        child1 = next(node for node in sample_tree if node.label == "child1")
        node = await tree.get_node_with_children(db, child1.id)
        
        assert node is not None
        assert node.label == "child1"
        assert len(node.children) == 2
        assert {child.label for child in node.children} == {"grandchild1", "grandchild2"}
    
    async def test_get_descendants(self, sample_tree: list[Node], db: Session):
        """test getting all descendants of a node."""
        # get root1's descendants
        root1 = next(node for node in sample_tree if node.label == "root1")
        descendants = await tree.get_descendants(db, root1.id)
        
        # should include all children and grandchildren
        assert len(descendants) == 4
        assert {node.label for node in descendants} == {
            "child1", "child2", "grandchild1", "grandchild2"
        }
    
    async def test_create_node_invalid_parent(self, empty_db: Session):
        """test creating node with non-existent parent."""
        node_in = NodeCreate(label="orphan", parent_id=999)
        
        with pytest.raises(NodeNotFoundError) as exc:
            await tree.create_node(empty_db, node_in)
        assert exc.value.status_code == 404
    
    async def test_prevent_cycle(self, sample_tree: list[Node], db: Session):
        """test cycle prevention when creating nodes.
        
        test scenario:
        initial tree:
            root1
            └── child1
                └── grandchild1
        
        attempt to create cycle:
            root1 -> child1 -> grandchild1 -> new_node -> root1
            
        this would create a cycle because we're trying to make root1
        a child of new_node, but root1 is an ancestor of new_node
        """
        # Get nodes from the tree
        grandchild1 = next(node for node in sample_tree if node.label == "grandchild1")
        root1 = next(node for node in sample_tree if node.label == "root1")
        
        # First create a new node with grandchild1 as parent (this should work)
        new_node = await tree.create_node(
            db, 
            NodeCreate(label="intermediate", parent_id=grandchild1.id)
        )
        
        # Now try to make root1 a child of the new node, which would create a cycle
        with pytest.raises(CycleError) as exc:
            await tree.update_node_parent(db, root1.id, new_node.id)
        assert exc.value.status_code == 400
    
    async def test_get_node_not_found(self, empty_db: Session):
        """test getting non-existent node."""
        node = await tree.get_node_with_children(empty_db, 999)
        assert node is None
    
    async def test_get_descendants_not_found(self, empty_db: Session):
        """test getting descendants of non-existent node."""
        with pytest.raises(NodeNotFoundError) as exc:
            await tree.get_descendants(empty_db, 999)
        assert exc.value.status_code == 404 