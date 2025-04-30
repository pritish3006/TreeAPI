"""pydantic schemas for tree node request/response validation."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class NodeBase(BaseModel):
    """
    base schema with common attributes.
    matches the base attributes of the Node SQLAlchemy model.
    """
    
    label: str = Field(
        ...,  # ... means required
        min_length=1,
        max_length=255,
        description="display name of the node (indexed in db)"
    )


class NodeCreate(NodeBase):
    """
    schema for creating a new node.
    maps to Node SQLAlchemy model creation with optional parent_id.
    """
    
    parent_id: Optional[int] = Field(
        default=None,
        description="id of the parent node (null for root nodes, indexed in db, cascading delete)",
        alias="parentId"  # use camelCase in JSON
    )
    
    @field_validator("label")
    def validate_label(cls, v: str) -> str:
        """
        validate that label is not just whitespace.
        matches db constraint of non-nullable label.
        """
        if v.strip() == "":
            raise ValueError("label cannot be empty or just whitespace")
        return v.strip()
    
    # Use ConfigDict for Pydantic v2
    model_config = ConfigDict(
        populate_by_name=True,  # allow both alias and original names
        from_attributes=True  # allow conversion from SQLAlchemy model
    )


class NodeResponse(NodeBase):
    """
    schema for node in responses.    
    includes all required fields from Node SQLAlchemy model.
    """
    
    id: int = Field(..., description="unique identifier of the node (primary key, indexed)")
    label: str = Field(..., description="display name of the node")
    
    # Use ConfigDict for Pydantic v2
    model_config = ConfigDict(
        from_attributes=True  # allow conversion from SQLAlchemy model
    )


class NodeTreeResponse(NodeResponse):
    """
    schema for node in tree responses (includes children).
    represents the hierarchical structure using Node's children relationship.
    children are ordered by label as per SQLAlchemy relationship definition.
    """
    
    children: List["NodeTreeResponse"] = Field(
        default_factory=list,
        description="list of child nodes (ordered by label)"
    )


# this is needed for the recursive type reference in NodeTreeResponse
NodeTreeResponse.model_rebuild()


class NodeCreateResponse(BaseModel):
    """
    schema for response after creating a node. 
    response containing only essential fields from Node model.
    """
    
    id: int = Field(..., description="unique identifier of the node")
    label: str = Field(..., description="display name of the node")
    
    # Use ConfigDict for Pydantic v2
    model_config = ConfigDict(
        from_attributes=True  # allow conversion from SQLAlchemy model
    ) 