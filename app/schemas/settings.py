from typing import Dict, Optional

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    """User preferences and tuning parameters."""

    version: int = 1
    chord_hand: str = Field(default="Left", pattern="^(Left|Right)$")
    strum_hand: str = Field(default="Right", pattern="^(Left|Right)$")
    strum_sensitivity: float = Field(default=1.0, ge=0.5, le=2.0)
    min_movement_threshold: float = Field(default=0.065, ge=0.02, le=0.20)
    gesture_stability_ms: int = Field(default=140, ge=60, le=400)
    strum_cooldown_ms: int = Field(default=120, ge=50, le=300)
    master_volume: float = Field(default=0.85, ge=0.0, le=1.0)
    chord_mappings: Dict[str, str] = Field(
        default_factory=lambda: {
            "1": "c-major",
            "2": "g-major",
            "3": "d-major",
            "4": "e-minor",
            "5": "a-minor",
        }
    )
    selected_camera_id: Optional[str] = None
    diagnostics_enabled: bool = False
