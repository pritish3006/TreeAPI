"""main api router module."""
from fastapi import APIRouter

from app.api.v1.endpoints import tree

api_router = APIRouter()

# include endpoint routers
api_router.include_router(tree.router, tags=["tree"]) 