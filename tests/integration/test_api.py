from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AirChord"
    assert data["version"] == "2.0.0"


def test_api_ready():
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert "model_exists" in data
    assert "audio_manifest_exists" in data
    assert data["model_exists"] is True
    assert data["audio_manifest_exists"] is True
    assert data["ready"] is True


def test_api_chords():
    response = client.get("/api/chords")
    assert response.status_code == 200
    data = response.json()
    assert "chords" in data
    assert len(data["chords"]) == 5
    chord_ids = [c["id"] for c in data["chords"]]
    assert "c-major" in chord_ids
    assert "g-major" in chord_ids
    assert "d-major" in chord_ids
    assert "e-minor" in chord_ids
    assert "a-minor" in chord_ids


def test_api_default_settings():
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["chord_hand"] == "Left"
    assert data["strum_hand"] == "Right"
    assert "chord_mappings" in data


def test_serve_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "AirChord" in response.text
    assert "<video" in response.text
    assert 'id="overlay-canvas"' in response.text


def test_serve_static_assets():
    resp_css = client.get("/css/tokens.css")
    assert resp_css.status_code == 200
    assert "--accent" in resp_css.text

    resp_js = client.get("/js/app.js")
    assert resp_js.status_code == 200

    resp_audio_manifest = client.get("/assets/audio/manifest.json")
    assert resp_audio_manifest.status_code == 200
    assert "c-major-down.wav" in resp_audio_manifest.text
