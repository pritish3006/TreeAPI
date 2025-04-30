"""main application module for tree management api."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tree Management API",
    description="API for managing hierarchical tree data structures",
    version="1.0.0",
)

# cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include api router
app.include_router(api_router, prefix="/api")

# health check endpoint
@app.get("/healthz")
async def health_check():
    """health check endpoint required by product spec."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )

# error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """handle unhandled exceptions with generic 500 response."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    ) 