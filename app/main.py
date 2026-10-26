import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.settings import router as settings_router
from app.api.websocket import router as websocket_router
from app.config import config
from app.services.instrument_service import instrument_service
from app.services.session_manager import session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("airchord")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AirChord Virtual Guitar backend...")
    readiness = instrument_service.check_readiness()
    if readiness["model_exists"]:
        try:
            instrument_service.initialize_model()
            logger.info("MediaPipe vision model successfully pre-loaded.")
        except Exception as e:
            logger.warning(f"Could not pre-load vision model during startup: {e}")
    else:
        logger.warning(
            f"Vision model not found at {readiness['model_path']}. "
            "Please run 'python scripts/download_model.py'."
        )

    yield

    # Shutdown
    logger.info("Shutting down AirChord backend...")
    await session_manager.close_all()
    instrument_service.shutdown()
    logger.info("AirChord shutdown complete.")


app = FastAPI(
    title="AirChord",
    description="Python-Powered, Browser-Based Virtual Guitar Using Real-Time Computer Vision",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(settings_router)
app.include_router(websocket_router)

# Mount frontend static directories
frontend_dir = config.frontend_dir
if frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")
