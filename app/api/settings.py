from fastapi import APIRouter

from app.schemas.chords import DEFAULT_CHORDS
from app.schemas.settings import UserSettings
from app.services.instrument_service import instrument_service

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/chords")
async def get_chords():
    """Get the full list of supported guitar chords."""
    return {
        "chords": [c.model_dump() for c in DEFAULT_CHORDS],
        "default_mappings": instrument_service.chord_mappings.get_current_mapping(),
    }


@router.get("/settings")
async def get_default_settings():
    """Get the default application and user settings."""
    return UserSettings().model_dump()
