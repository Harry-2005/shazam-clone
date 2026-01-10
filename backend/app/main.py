from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="Shazam Clone API",
    description="Audio fingerprinting and song identification system",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows web browsers to make requests to our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Shazam Clone API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Accept connections from any IP
        port=8000,        # Port number
        reload=True       # Auto-reload on code changes (development only)
    )