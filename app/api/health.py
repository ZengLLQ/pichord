from fastapi import APIRouter

from app.services.instrument_service import instrument_service

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Basic process health check."""
    return {
        "status": "healthy",
        "service": "AirChord",
        "version": "2.0.0",
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check validating computer vision model and audio assets."""
    readiness = instrument_service.check_readiness()
    return readiness
