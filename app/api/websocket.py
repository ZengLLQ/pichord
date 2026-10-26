import json
import logging
import struct
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.messages import ErrorMessage
from app.schemas.settings import UserSettings
from app.services.session_manager import session_manager

logger = logging.getLogger("airchord.websocket")

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/play")
async def websocket_play_endpoint(websocket: WebSocket):
    await websocket.accept()

    session = session_manager.create_session(websocket)
    logger.info(f"WebSocket client connected. Session ID: {session.session_id}")

    try:
        # Start worker pipeline
        await session.start()

        fallback_seq = 0

        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                raw_bytes: bytes = message["bytes"]
                if len(raw_bytes) < 4:
                    continue

                seq = fallback_seq
                timestamp_ms = int(time.time() * 1000)
                jpeg_bytes = raw_bytes

                # Check if packed with 4-byte header length
                header_len = struct.unpack(">I", raw_bytes[:4])[0]
                if 4 < (4 + header_len) < len(raw_bytes):
                    try:
                        header_str = raw_bytes[4 : 4 + header_len].decode("utf-8")
                        header_obj = json.loads(header_str)
                        seq = header_obj.get("seq", fallback_seq)
                        timestamp_ms = header_obj.get("timestamp_ms", timestamp_ms)
                        jpeg_bytes = raw_bytes[4 + header_len :]
                    except Exception:
                        # Fallback to entire payload as JPEG
                        jpeg_bytes = raw_bytes

                fallback_seq += 1
                await session.push_frame(jpeg_bytes, seq, timestamp_ms)

            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    if msg_type == "session.start":
                        if "settings" in data and data["settings"]:
                            new_settings = UserSettings(**data["settings"])
                            session.update_settings(new_settings)

                    elif msg_type == "settings.update":
                        if "settings" in data:
                            new_settings = UserSettings(**data["settings"])
                            session.update_settings(new_settings)

                    elif msg_type == "calibration.complete":
                        chord_hand = data.get("chord_hand", "Left")
                        strum_hand = data.get("strum_hand", "Right")
                        st = session.settings.model_copy(
                            update={"chord_hand": chord_hand, "strum_hand": strum_hand}
                        )
                        session.update_settings(st)

                    elif msg_type == "session.stop":
                        session.frame_processor.reset()

                except json.JSONDecodeError:
                    err = ErrorMessage(
                        code="INVALID_JSON",
                        message="Received invalid JSON text payload",
                        recoverable=True,
                    )
                    await websocket.send_text(err.model_dump_json())

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected cleanly: {session.session_id}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error in session {session.session_id}: {e}")
    finally:
        await session_manager.remove_session(session.session_id)
