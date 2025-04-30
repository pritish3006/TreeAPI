"""tree endpoints module."""
from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.tree import NodeNotFoundError, CycleError, tree
from app.schemas.tree import NodeCreate, NodeTreeResponse, NodeCreateResponse
from app.db.session import get_db

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/tree", response_model=List[NodeTreeResponse])
def get_tree(db: Session = Depends(get_db)) -> List[NodeTreeResponse]:
    """
    retrieve the entire forest as nested json.
    
    args:
        db (session): database session dependency
    
    returns:
        list[nodetreeresponse]: array of root nodes with their children
    """
    logger.info("Handling GET /tree request")
    try:
        result = tree.get_forest(db)
        logger.info(f"Successfully retrieved forest with {len(result)} root nodes")
        return [NodeTreeResponse.model_validate(node) for node in result]
    except Exception as e:
        logger.error(f"Error retrieving forest: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving forest: {str(e)}"
        )

@router.post("/tree", response_model=NodeCreateResponse, status_code=status.HTTP_201_CREATED)
def create_node(
    node: NodeCreate,
    db: Session = Depends(get_db)
) -> NodeCreateResponse:
    """
    create a new node in the tree.
    
    args:
        node (nodecreate): node creation data with label and optional parent_id
        db (session): database session dependency
        
    returns:
        nodecreateresponse: created node data
        
    raises:
        404: parent node not found
        400: validation error or cycle detected
    """
    logger.info(f"Handling POST /tree request with data: label={node.label}, parent_id={node.parent_id}")
    try:
        result = tree.create_node(db=db, node_in=node)
        logger.info(f"Successfully created node: id={result.id}, label={result.label}, parent_id={result.parent_id}")
        return NodeCreateResponse.model_validate(result)
    except NodeNotFoundError as e:
        logger.error(f"Parent node not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CycleError as e:
        logger.error(f"Cycle detected: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating node: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating node: {str(e)}"
        ) 