"""
FastAPI application for the Retail Shelf Assistant.
"""
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .models import HealthResponse, ErrorResponse
from .routes import router
from .orchestrator import BackendOrchestrator
from config.settings import API_CONFIG, get_config, BASE_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Retail Shelf Assistant API",
    description="Voice-enabled retail assistant for product location and information queries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize orchestrator
orchestrator = BackendOrchestrator()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
web_dir = BASE_DIR / "web"
web_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Include API routes
app.include_router(router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"message": str(exc)}
        ).dict()
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and component status."""
    try:
        # Get actual component health status
        components = orchestrator.get_health_status()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Retail Shelf Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "web_ui": "/static/index.html"
    }

# Serve web UI
@app.get("/ui")
async def web_ui():
    """Serve the web UI."""
    from fastapi.responses import FileResponse
    web_file = BASE_DIR / "web" / "index.html"
    if web_file.exists():
        return FileResponse(web_file)
    else:
        return {"message": "Web UI not found. Please ensure index.html exists in the web directory."}

if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "src.api.main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=True
    )
