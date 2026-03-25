"""
Research Notebook Backend - Main FastAPI Application
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    logger.info("🚀 Research Notebook Backend started")
    yield
    logger.info("🛑 Research Notebook Backend shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Research Notebook Backend",
    description="Convert research papers to Jupyter notebooks using AI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        {
            "status": "ok",
            "service": "research-notebook-backend",
            "timestamp": datetime.utcnow().isoformat(),
        },
        status_code=200,
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Research Notebook Backend",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
