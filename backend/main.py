import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Environment configuration
ENV = os.environ.get("ENV", "dev")
FRONTEND_BUILD_DIR = os.environ.get("FRONTEND_BUILD_DIR", "../build")
CORS_ALLOW_ORIGIN = os.environ.get("CORS_ALLOW_ORIGIN", "*")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    log.info("Starting Open WebUI backend...")
    # Startup logic (DB init, model loading, etc.) goes here
    yield
    log.info("Shutting down Open WebUI backend...")


app = FastAPI(
    title="Open WebUI",
    description="Open WebUI — A user-friendly interface for interacting with LLMs.",
    version="0.1.0",
    docs_url="/docs" if ENV == "dev" else None,
    redoc_url="/redoc" if ENV == "dev" else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ALLOW_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to return consistent error responses."""
    log.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/health", tags=["utility"])
async def health_check():
    """Health check endpoint for container orchestration and uptime monitoring."""
    return {"status": "ok"}


@app.get("/version", tags=["utility"])
async def get_version():
    """Returns the current application version."""
    return {"version": app.version}


# Mount static frontend build if it exists
if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_BUILD_DIR, html=True),
        name="frontend",
    )
    log.info(f"Serving frontend from: {FRONTEND_BUILD_DIR}")
else:
    log.warning(
        f"Frontend build directory '{FRONTEND_BUILD_DIR}' not found. "
        "Only API endpoints will be available."
    )
