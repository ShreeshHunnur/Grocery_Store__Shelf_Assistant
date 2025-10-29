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
print(f"Mounting static files from: {web_dir}")
print(f"Static files exist: {list(web_dir.glob('*'))}")
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

# Serve CSS directly to avoid StaticFiles issues in Electron
@app.get("/static/styles.css")
async def serve_css():
    """Serve the CSS file directly."""
    from fastapi.responses import Response
    css_file = BASE_DIR / "web" / "styles.css"
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        return Response(content=css_content, media_type="text/css")
    else:
        return Response("/* CSS file not found */", media_type="text/css", status_code=404)

# Serve JS directly to avoid StaticFiles issues in Electron
@app.get("/static/app.js")
async def serve_js():
    """Serve the JavaScript file directly."""
    from fastapi.responses import Response
    js_file = BASE_DIR / "web" / "app.js"
    if js_file.exists():
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        return Response(content=js_content, media_type="application/javascript")
    else:
        return Response("// JS file not found", media_type="application/javascript", status_code=404)

# Debug endpoint to test static file serving
@app.get("/debug/static")
async def debug_static():
    """Debug static file configuration."""
    web_dir = BASE_DIR / "web"
    files = list(web_dir.glob("*")) if web_dir.exists() else []
    css_file = web_dir / "styles.css"
    css_size = css_file.stat().st_size if css_file.exists() else 0
    return {
        "web_dir": str(web_dir),
        "web_dir_exists": web_dir.exists(),
        "files": [f.name for f in files],
        "styles_css_exists": css_file.exists(),
        "styles_css_size": css_size,
        "app_js_exists": (web_dir / "app.js").exists()
    }

if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "src.api.main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=True
    )
