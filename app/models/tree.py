from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Node(Base):
    """tree node model using adjacency list pattern.
    
    attributes:
        id: unique identifier
        label: display name of the node
        parent_id: id of the parent node (null for root nodes)
        created_at: timestamp of creation
        updated_at: timestamp of last update
        children: list of child nodes (one-to-many)
        parent: reference to parent node (many-to-one)
    """
     
    __tablename__ = "nodes"
    
    # Primary Key
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    # Node Data
    label: Mapped[str] = Column(String(255), nullable=False, index=True)
    
    # Tree Structure
    parent_id: Mapped[Optional[int]] = Column(
        Integer, 
        ForeignKey("nodes.id", ondelete="CASCADE"), 
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    parent: Mapped[Optional["Node"]] = relationship(
        "Node",
        back_populates="children",
        remote_side=[id]  # Specify the "many" side points to "one" side
    )
    
    children: Mapped[List["Node"]] = relationship(
        "Node",
        back_populates="parent",
        cascade="all, delete-orphan",  # Cascade delete from parent to children
        lazy="joined",
        order_by="Node.label"  # Keep children ordered by label
    )
    
    def __repr__(self) -> str:
        """string representation of the node.
        
        returns:
            str: formatted string with node details
        """
        return f"<Node(id={self.id}, label='{self.label}', parent_id={self.parent_id})>" 