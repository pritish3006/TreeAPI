from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tree Management API",
    description="API for managing hierarchical tree structures",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api.v1.endpoints import tree
app.include_router(tree.router, prefix="/api/v1", tags=["tree"])

@app.get("/healthz")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"} 