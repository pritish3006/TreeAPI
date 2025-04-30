"""base class for all models."""
from app.db.base import Base

# Import all models here
from app.models.tree import Node  # noqa

# Make them available for migrations
__all__ = ["Base", "Node"] 