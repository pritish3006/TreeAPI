"""crud operations for tree nodes."""
from typing import List, Optional, Set
import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import text

from app.crud.base import CRUDBase
from app.models.tree import Node
from app.schemas.tree import NodeCreate, NodeCreateResponse

# Set up logging
logger = logging.getLogger(__name__)

class NodeNotFoundError(HTTPException):
    """raised when a node is not found."""
    
    def __init__(self, node_id: int):
        """initialize with custom message."""
        super().__init__(
            status_code=404,
            detail=f"Node with id {node_id} not found"
        )


class CycleError(HTTPException):
    """raised when an operation would create a cycle."""
    
    def __init__(self, node_id: Optional[int], parent_id: int):
        """initialize with custom message."""
        msg = (
            f"Cannot set node {node_id if node_id else 'new node'} as child of {parent_id}: "
            "would create cycle"
        )
        super().__init__(status_code=400, detail=msg)


class TreeCRUD(CRUDBase[Node, NodeCreate, NodeCreate]):
    """crud operations for tree nodes."""
    
    def get_forest(
        self, 
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Node]:
        """
        get all root nodes with their descendants.
        args:
            db: database session
            skip: number of records to skip
            limit: maximum number of records to return
            
        returns:
            list of root nodes with populated children
        """
        return (
            db.query(Node)
            .filter(Node.parent_id.is_(None))
            .options(joinedload(Node.children))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_node(
        self, 
        db: Session, 
        node_in: NodeCreate
    ) -> Node:
        """
        create a new node.
        args:
            db: database session
            node_in: validated input schema
            
        returns:
            created node instance
            
        raises:
            NodeNotFoundError: if parent_id is invalid
            CycleError: if operation would create cycle
        """
        logger.info(f"Creating new node with label={node_in.label}, parent_id={node_in.parent_id}")
        
        # Access schema fields directly for validation
        if node_in.parent_id is not None:
            # Check parent exists
            parent = self.get(db, id=node_in.parent_id)
            if parent is None:
                logger.error(f"Parent node {node_in.parent_id} not found")
                raise NodeNotFoundError(node_in.parent_id)
            
            # Check for cycles
            would_create_cycle = self._would_create_cycle(db, None, node_in.parent_id)
            logger.info(f"Cycle detection result for new node: would_create_cycle={would_create_cycle}")
            
            if would_create_cycle:
                logger.warning(f"Detected cycle: new node -> parent {node_in.parent_id}")
                raise CycleError(None, node_in.parent_id)
        
        # Create node with explicit field mapping
        db_obj = Node(
            label=node_in.label,
            parent_id=node_in.parent_id  # explicitly set parent_id
        )
        
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Successfully created node: id={db_obj.id}, label={db_obj.label}, parent_id={db_obj.parent_id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create node: {str(e)}")
            raise e
    
    def get_node_with_children(
        self, 
        db: Session, 
        node_id: int
    ) -> Optional[Node]:
        """
        get node by id with populated children.
        args:
            db: database session
            node_id: node id to fetch
            
        returns:
            node if found, none otherwise
        """
        return (
            db.query(Node)
            .filter(Node.id == node_id)
            .options(joinedload(Node.children))
            .first()
        )
    
    def _get_ancestors(
        self, 
        db: Session, 
        node_id: int,
        include_self: bool = False
    ) -> Set[int]:
        """
        get all ancestor ids of a node.
        args:
            db: database session
            node_id: node to get ancestors for
            include_self: whether to include the node itself
            
        returns:
            set of ancestor ids
        """
        logger.debug(f"Getting ancestors for node_id={node_id}, include_self={include_self}")
        
        # using recursive cte for efficient ancestor traversal
        cte_query = """
        WITH RECURSIVE ancestors AS (
            -- base case: direct parent
            SELECT id, parent_id
            FROM nodes
            WHERE id = :node_id
            
            UNION ALL
            
            -- recursive case: parent's ancestors
            SELECT n.id, n.parent_id
            FROM nodes n
            INNER JOIN ancestors a ON n.id = a.parent_id
        )
        SELECT id FROM ancestors WHERE id != :node_id OR :include_self;
        """
        
        result = db.execute(
            text(cte_query), 
            {
                "node_id": node_id,
                "include_self": include_self
            }
        )
        ancestors = {row[0] for row in result}
        logger.debug(f"Found ancestors for node_id={node_id}: {ancestors}")
        return ancestors
    
    def _would_create_cycle(
        self, 
        db: Session, 
        node_id: Optional[int], 
        parent_id: int
    ) -> bool:
        """
        check if setting parent_id would create a cycle.
        args:
            db: database session
            node_id: node being modified (none for new nodes)
            parent_id: proposed parent id
            
        returns:
            true if operation would create cycle
            
        note:
            for new nodes (node_id is None), we check if the proposed parent
            would create a cycle with any existing nodes.
            
            for existing nodes, we check if the proposed parent is a descendant
            of the node, which would create a cycle.
        """
        logger.info(f"Checking for cycles: node_id={node_id}, parent_id={parent_id}")
        
        # For new nodes, we need to check if parent exists
        parent = self.get(db, id=parent_id)
        if parent is None:
            logger.error(f"Parent node {parent_id} not found")
            raise NodeNotFoundError(parent_id)
        
        # For existing nodes, check if parent would be its own descendant
        if node_id is not None:
            # Get all descendants of the current node
            descendants = self.get_descendants(
                db, 
                node_id,
                include_self=True
            )
            descendant_ids = {node.id for node in descendants}
            logger.debug(f"Found descendants for node_id={node_id}: {descendant_ids}")
            
            # If parent is in descendants, it would create a cycle
            would_cycle = parent_id in descendant_ids
            logger.info(f"Cycle check for existing node: would_create_cycle={would_cycle}")
            return would_cycle
        else:
            # For new nodes, we need to check if the proposed parent's ancestors
            # include the node we're trying to make a child. This prevents
            # creating cycles like: A -> B -> C -> D -> A
            ancestors = self._get_ancestors(db, parent_id, include_self=True)
            logger.debug(f"Found ancestors for parent_id={parent_id}: {ancestors}")
            
            # No cycle possible for new nodes - they can't create cycles
            # just by being added as children
            return False
    
    def get_descendants(
        self, 
        db: Session, 
        node_id: int,
        include_self: bool = False
    ) -> List[Node]:
        """
        get all descendants of a node.
        args:
            db: database session
            node_id: node to get descendants for
            include_self: whether to include the node itself
            
        returns:
            list of descendant nodes
            
        raises:
            NodeNotFoundError: if node_id is invalid
        """
        logger.debug(f"Getting descendants for node_id={node_id}, include_self={include_self}")
        
        # Verify node exists
        node = self.get(db, id=node_id)
        if node is None:
            logger.error(f"Node {node_id} not found")
            raise NodeNotFoundError(node_id)
            
        # using recursive cte for efficient descendant traversal
        cte_query = """
        WITH RECURSIVE descendants AS (
            -- base case: start node
            SELECT id, parent_id, label, created_at, updated_at
            FROM nodes
            WHERE id = :node_id
            
            UNION ALL
            
            -- recursive case: children
            SELECT n.id, n.parent_id, n.label, n.created_at, n.updated_at
            FROM nodes n
            INNER JOIN descendants d ON n.parent_id = d.id
        )
        SELECT * FROM descendants 
        WHERE id != :node_id OR :include_self;
        """
        
        result = db.execute(
            text(cte_query), 
            {
                "node_id": node_id,
                "include_self": include_self
            }
        )
        
        descendants = [
            Node(
                id=row.id,
                label=row.label,
                parent_id=row.parent_id,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in result
        ]
        logger.debug(f"Found {len(descendants)} descendants for node_id={node_id}")
        return descendants

    def update_node_parent(
        self,
        db: Session,
        node_id: int,
        new_parent_id: int
    ) -> Node:
        """
        update a node's parent.
        args:
            db: database session
            node_id: id of the node to update
            new_parent_id: id of the new parent
            
        returns:
            updated node
            
        raises:
            NodeNotFoundError: if node_id or new_parent_id is invalid
            CycleError: if operation would create cycle
        """
        logger.info(f"Updating node {node_id} to have parent {new_parent_id}")
        
        # Check if node exists
        node = self.get(db, id=node_id)
        if node is None:
            logger.error(f"Node {node_id} not found")
            raise NodeNotFoundError(node_id)
        
        # Check if new parent exists
        parent = self.get(db, id=new_parent_id)
        if parent is None:
            logger.error(f"Parent node {new_parent_id} not found")
            raise NodeNotFoundError(new_parent_id)
        
        # Check for cycles
        would_create_cycle = self._would_create_cycle(db, node_id, new_parent_id)
        logger.info(f"Cycle detection result: would_create_cycle={would_create_cycle}")
        
        if would_create_cycle:
            logger.warning(f"Detected cycle: node {node_id} -> parent {new_parent_id}")
            raise CycleError(node_id, new_parent_id)
        
        try:
            # Update parent
            node.parent_id = new_parent_id
            db.commit()
            db.refresh(node)
            logger.info(f"Successfully updated node {node_id} to have parent {new_parent_id}")
            return node
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update node: {str(e)}")
            raise e


# create singleton instance
tree = TreeCRUD(Node) 