from typing import List, Optional

from pydantic import BaseModel

from app.schemas.chords import ChordDefinition
from app.schemas.settings import UserSettings


class FrameHeader(BaseModel):
    """Header embedded in binary frame transmission."""

    seq: int
    timestamp_ms: int


class ClientMessage(BaseModel):
    """Base model for incoming WebSocket messages."""

    type: str


class SessionStartMessage(ClientMessage):
    type: str = "session.start"
    settings: Optional[UserSettings] = None


class SessionStopMessage(ClientMessage):
    type: str = "session.stop"


class SettingsUpdateMessage(ClientMessage):
    type: str = "settings.update"
    settings: UserSettings


class CalibrationStartMessage(ClientMessage):
    type: str = "calibration.start"


class CalibrationCompleteMessage(ClientMessage):
    type: str = "calibration.complete"
    chord_hand: str
    strum_hand: str


class HandRoleState(BaseModel):
    """Normalized position and status of a tracked hand role."""

    role: str  # "chord" | "strum"
    handedness: str  # "Left" | "Right"
    wrist_x: float
    wrist_y: float
    confidence: float
    finger_count: Optional[int] = None
    extended_fingers: Optional[List[bool]] = None
    landmarks: Optional[List[List[float]]] = None  # [[x, y, z], ...] for diagnostics


class ServerMessage(BaseModel):
    """Base model for outgoing WebSocket messages."""

    type: str


class SessionReadyMessage(ServerMessage):
    type: str = "session.ready"
    session_id: str
    chords: List[ChordDefinition]
    settings: UserSettings


class TrackingUpdateMessage(ServerMessage):
    type: str = "tracking.update"
    seq: int
    active_chord_id: Optional[str] = None
    chord_hand: Optional[HandRoleState] = None
    strum_hand: Optional[HandRoleState] = None
    hands_detected: int = 0
    fps: float = 0.0
    latency_ms: float = 0.0


class ChordChangedMessage(ServerMessage):
    type: str = "chord.changed"
    chord_id: str
    chord_name: str
    finger_count: int
    timestamp_ms: int


class StrumDetectedMessage(ServerMessage):
    type: str = "strum.detected"
    seq: int
    direction: str  # "down" | "up"
    speed: float
    displacement: float
    active_chord_id: str
    timestamp_ms: int
    confidence: float


class TrackingLostMessage(ServerMessage):
    type: str = "tracking.lost"
    reason: str


class ErrorMessage(ServerMessage):
    type: str = "error"
    code: str
    message: str
    recoverable: bool = True
