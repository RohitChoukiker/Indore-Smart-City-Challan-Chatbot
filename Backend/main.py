"""
FastAPI main application.

Entry point for the FastAPI backend server.
"""

# Standard library imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local application imports
from modules.Auth.auth_controller import authRouter

# Create FastAPI app
app = FastAPI(
    title="Indore Smart City Development API",
    description="Backend API for Indore Smart City Development Ltd.",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(authRouter, prefix="/api/auth", tags=["Authentication"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "status": True,
        "message": "Indore Smart City Development API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": True,
        "message": "API is healthy",
        "data": None
    }

