from pathlib import Path

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """AirChord application configuration."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # Directories
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    model_path: Path = Field(
        default_factory=lambda: (
            Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task"
        )
    )
    frontend_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "frontend"
    )
    audio_dir: Path = Field(
        default_factory=lambda: (
            Path(__file__).resolve().parent.parent / "frontend" / "assets" / "audio"
        )
    )

    # Vision & MediaPipe settings
    min_detection_confidence: float = 0.5
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    smoothing_alpha: float = 0.65  # Higher = more responsive, Lower = smoother
    max_hands: int = 2
    inference_width: int = 480
    inference_height: int = 360
    target_fps: int = 20

    # Gesture stability (hysteresis)
    gesture_stability_ms: int = 140

    # Strum motion detection
    strum_min_speed: float = 0.70  # normalized vertical units per second
    strum_min_displacement: float = 0.065  # normalized height displacement
    strum_cooldown_ms: int = 120  # milliseconds before next strum can be triggered

    # Hand roles
    default_chord_hand: str = "Left"  # "Left" or "Right"
    default_strum_hand: str = "Right"

    # Audio
    master_volume: float = 0.85


config = AppConfig()
