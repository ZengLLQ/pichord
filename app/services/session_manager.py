import asyncio
import logging
import time
import uuid
from typing import Dict, Optional

from fastapi import WebSocket

from app.schemas.messages import (
    ChordChangedMessage,
    ErrorMessage,
    SessionReadyMessage,
    StrumDetectedMessage,
    TrackingUpdateMessage,
)
from app.schemas.settings import UserSettings
from app.services.instrument_service import instrument_service
from app.vision.frame_processor import FrameProcessingResult

logger = logging.getLogger("airchord.session")


class InstrumentSession:
    """Manages an active WebSocket session with bounded asynchronous frame worker."""

    def __init__(
        self,
        session_id: str,
        websocket: WebSocket,
        settings: Optional[UserSettings] = None,
    ):
        self.session_id = session_id
        self.websocket = websocket
        self.settings = settings or UserSettings()
        self.frame_processor = instrument_service.create_frame_processor(self.settings)

        # Bounded single-frame queue: always discards stale frame if busy
        self.frame_queue: asyncio.Queue[tuple[bytes, int, int]] = asyncio.Queue(maxsize=1)
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Metrics
        self.last_frame_time = time.perf_counter()
        self.fps = 0.0

    async def start(self) -> None:
        self.is_running = True
        self.worker_task = asyncio.create_task(self._vision_worker_loop())

        # Send session ready
        ready_msg = SessionReadyMessage(
            session_id=self.session_id,
            chords=self.frame_processor.chord_mappings.all_chords,
            settings=self.settings,
        )
        await self.websocket.send_text(ready_msg.model_dump_json())

    async def push_frame(self, jpeg_bytes: bytes, seq: int, timestamp_ms: int) -> None:
        if not self.is_running:
            return

        # If queue already has a pending frame, discard it to avoid stale latency
        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
                self.frame_queue.task_done()
            except (asyncio.QueueEmpty, ValueError):
                pass

        try:
            self.frame_queue.put_nowait((jpeg_bytes, seq, timestamp_ms))
        except asyncio.QueueFull:
            pass

    async def _vision_worker_loop(self) -> None:
        """Asynchronous worker loop running MediaPipe and CV processing in thread pool."""
        logger.info(f"Vision worker started for session {self.session_id}")
        fps_alpha = 0.2

        while self.is_running:
            try:
                jpeg_bytes, seq, timestamp_ms = await self.frame_queue.get()
            except asyncio.CancelledError:
                break

            try:
                # Run CPU-bound image decoding + inference in a worker thread
                result: FrameProcessingResult = await asyncio.to_thread(
                    self.frame_processor.process_frame,
                    jpeg_bytes,
                    seq,
                    timestamp_ms,
                )

                # Calculate measured FPS
                now = time.perf_counter()
                dt = now - self.last_frame_time
                self.last_frame_time = now
                if dt > 0:
                    current_fps = 1.0 / dt
                    self.fps = fps_alpha * current_fps + (1.0 - fps_alpha) * self.fps

                # 1. Send Chord Changed if chord switched
                if result.chord_changed and result.new_chord:
                    chord_msg = ChordChangedMessage(
                        chord_id=result.new_chord.id,
                        chord_name=result.new_chord.name,
                        finger_count=result.new_chord.finger_count,
                        timestamp_ms=timestamp_ms,
                    )
                    await self.websocket.send_text(chord_msg.model_dump_json())

                # 2. Send Strum Detected if stroke accepted
                if result.strum_event:
                    strum_msg = StrumDetectedMessage(
                        seq=result.strum_event.seq,
                        direction=result.strum_event.direction,
                        speed=result.strum_event.speed,
                        displacement=result.strum_event.displacement,
                        active_chord_id=result.strum_event.active_chord_id,
                        timestamp_ms=result.strum_event.timestamp_ms,
                        confidence=result.strum_event.confidence,
                    )
                    await self.websocket.send_text(strum_msg.model_dump_json())

                # 3. Send compact tracking update
                tracking_msg = TrackingUpdateMessage(
                    seq=seq,
                    active_chord_id=result.active_chord_id,
                    chord_hand=result.chord_hand_state,
                    strum_hand=result.strum_hand_state,
                    hands_detected=result.hands_detected,
                    fps=round(self.fps, 1),
                    latency_ms=result.latency_ms,
                )
                await self.websocket.send_text(tracking_msg.model_dump_json())

            except Exception as e:
                logger.error(f"Error processing frame in session {self.session_id}: {e}")
                err_msg = ErrorMessage(
                    code="FRAME_PROCESSING_ERROR",
                    message="Error processing frame",
                    recoverable=True,
                )
                try:
                    await self.websocket.send_text(err_msg.model_dump_json())
                except Exception:
                    break
            finally:
                self.frame_queue.task_done()

        logger.info(f"Vision worker stopped for session {self.session_id}")

    def update_settings(self, new_settings: UserSettings) -> None:
        self.settings = new_settings
        self.frame_processor = instrument_service.create_frame_processor(new_settings)

    async def close(self) -> None:
        self.is_running = False
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        self.frame_processor.reset()


class SessionManager:
    """Manages all active client WebSocket sessions."""

    def __init__(self):
        self._sessions: Dict[str, InstrumentSession] = {}

    def create_session(
        self, websocket: WebSocket, settings: Optional[UserSettings] = None
    ) -> InstrumentSession:
        session_id = str(uuid.uuid4())
        session = InstrumentSession(session_id, websocket, settings)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[InstrumentSession]:
        return self._sessions.get(session_id)

    async def remove_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session:
            await session.close()

    async def close_all(self) -> None:
        for session in list(self._sessions.values()):
            await session.close()
        self._sessions.clear()


session_manager = SessionManager()
