
# Standard library imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local application imports
from modules.Auth.auth_controller import authRouter
from modules.Agent.agent_controller import agentRouter
from database.models import Base, engine

# Create FastAPI app
app = FastAPI(
    title="Indore Smart City Development API",
    description="Backend API for Indore Smart City Development Ltd.",
    version="1.0.0"
)


# Create all database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(authRouter, prefix="/api/auth", tags=["Authentication"])
app.include_router(agentRouter, prefix="/api/agent", tags=["Agent"])


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


