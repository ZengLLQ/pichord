import logging
from pathlib import Path
from typing import Optional

from app.config import config
from app.gestures.chord_mappings import ChordMappings
from app.schemas.settings import UserSettings
from app.vision.frame_processor import FrameProcessor
from app.vision.hand_tracker import HandTracker

logger = logging.getLogger("airchord.instrument")


class InstrumentService:
    """Manages shared models, chord registry, and creates session frame processors."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or config.model_path
        self.chord_mappings = ChordMappings()
        self.tracker = HandTracker(
            model_path=self.model_path,
            num_hands=config.max_hands,
            min_detection_confidence=config.min_detection_confidence,
            min_presence_confidence=config.min_presence_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
        )
        self._is_ready = False

    def check_readiness(self) -> dict:
        model_exists = self.model_path.exists()
        audio_dir_exists = config.audio_dir.exists()
        manifest_path = config.audio_dir / "manifest.json"
        manifest_exists = manifest_path.exists()

        status = {
            "model_exists": model_exists,
            "model_path": str(self.model_path),
            "audio_dir_exists": audio_dir_exists,
            "audio_manifest_exists": manifest_exists,
            "ready": model_exists and manifest_exists,
        }
        return status

    def initialize_model(self) -> None:
        try:
            self.tracker.initialize()
            self._is_ready = True
            logger.info("MediaPipe HandTracker initialized successfully.")
        except Exception as e:
            self._is_ready = False
            logger.error(f"Failed to initialize MediaPipe HandTracker: {e}")
            raise

    def create_frame_processor(self, settings: Optional[UserSettings] = None) -> FrameProcessor:
        st = settings or UserSettings()
        # Custom chord mappings if any
        mappings = ChordMappings(st.chord_mappings)

        # Scale detection parameters by sensitivity
        min_disp = st.min_movement_threshold / st.strum_sensitivity
        min_spd = config.strum_min_speed / st.strum_sensitivity

        return FrameProcessor(
            hand_tracker=self.tracker,
            chord_mappings=mappings,
            chord_hand=st.chord_hand,
            strum_hand=st.strum_hand,
            smoothing_alpha=config.smoothing_alpha,
            gesture_stability_ms=st.gesture_stability_ms,
            strum_min_speed=min_spd,
            strum_min_displacement=min_disp,
            strum_cooldown_ms=st.strum_cooldown_ms,
        )

    def shutdown(self) -> None:
        self.tracker.close()
        self._is_ready = False


instrument_service = InstrumentService()
