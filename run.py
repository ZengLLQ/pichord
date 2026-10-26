import argparse
import sys
from pathlib import Path

import uvicorn

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import config  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run the AirChord Virtual Guitar Server.")
    parser.add_argument(
        "--host", type=str, default=config.host, help=f"Host to bind (default: {config.host})"
    )
    parser.add_argument(
        "--port", type=int, default=config.port, help=f"Port to bind (default: {config.port})"
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print("==================================================")
    print("  AirChord Virtual Guitar v2.0")
    print(f"  URL: http://{args.host}:{args.port}")
    print("==================================================")

    # Check model
    if not config.model_path.exists():
        print("[!] Warning: MediaPipe hand landmarker model not found at:")
        print(f"    {config.model_path}")
        print("    Run 'python scripts/download_model.py' to download it.")
    else:
        print(f"[OK] MediaPipe model found: {config.model_path.name}")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
