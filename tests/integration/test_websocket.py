import json
import struct

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.session_manager import session_manager


@pytest.fixture
def mock_jpeg_frame():
    # Create a small 480x360 blank image and encode as JPEG
    img = np.zeros((360, 480, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()


def test_websocket_lifecycle_and_handshake():
    client = TestClient(app)
    with client.websocket_connect("/ws/play") as ws:
        # First message must be session.ready
        ready_raw = ws.receive_text()
        ready_data = json.loads(ready_raw)
        assert ready_data["type"] == "session.ready"
        assert "session_id" in ready_data
        assert "chords" in ready_data
        session_id = ready_data["session_id"]

        # Check session manager holds this session
        session = session_manager.get_session(session_id)
        assert session is not None
        assert session.is_running is True

    # After websocket context exits, session must be cleaned up
    assert session_manager.get_session(session_id) is None


def test_websocket_text_messages():
    client = TestClient(app)
    with client.websocket_connect("/ws/play") as ws:
        ws.receive_text()  # consume session.ready

        # Send settings.update
        settings_payload = {
            "type": "settings.update",
            "settings": {
                "chord_hand": "Right",
                "strum_hand": "Left",
                "strum_sensitivity": 1.5,
            },
        }
        ws.send_text(json.dumps(settings_payload))

        # Send calibration.complete
        calib_payload = {
            "type": "calibration.complete",
            "chord_hand": "Right",
            "strum_hand": "Left",
        }
        ws.send_text(json.dumps(calib_payload))

        # Send malformed JSON -> should receive error message
        ws.send_text("{ invalid json payload ...")
        err_raw = ws.receive_text()
        err_data = json.loads(err_raw)
        assert err_data["type"] == "error"
        assert err_data["code"] == "INVALID_JSON"


def test_websocket_binary_frame_transmission(mock_jpeg_frame):
    client = TestClient(app)
    with client.websocket_connect("/ws/play") as ws:
        ws.receive_text()  # consume session.ready

        # Pack binary frame: [4 bytes header len] + [header JSON] + [jpeg bytes]
        header = json.dumps({"seq": 101, "timestamp_ms": 1000}).encode("utf-8")
        header_len = len(header)
        payload = struct.pack(">I", header_len) + header + mock_jpeg_frame

        ws.send_bytes(payload)

        # Worker should process frame and return tracking.update
        update_raw = ws.receive_text()
        update_data = json.loads(update_raw)
        assert update_data["type"] == "tracking.update"
        assert update_data["seq"] == 101
        assert "active_chord_id" in update_data
        assert "latency_ms" in update_data
