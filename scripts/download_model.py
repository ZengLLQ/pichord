import argparse
import sys
import urllib.request
from pathlib import Path

# Ensure UTF-8 output on Windows consoles if possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
EXPECTED_MIN_BYTES = 7_000_000  # ~7.8 MB


def download_model(dest_path: Path, force: bool = False):
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists() and not force:
        size = dest_path.stat().st_size
        if size >= EXPECTED_MIN_BYTES:
            print(f"[OK] Model already exists at {dest_path} ({size:,} bytes). Skipping download.")
            return True
        else:
            print(
                f"Existing model file seems corrupt/incomplete ({size:,} bytes). Re-downloading..."
            )

    print("Downloading MediaPipe Hand Landmarker model from:")
    print(f"  {MODEL_URL}")
    print("Saving to:")
    print(f"  {dest_path}")

    def progress_callback(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, int(downloaded * 100 / total_size))
            mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\rDownloading: {percent}% ({mb:.1f}/{total_mb:.1f} MB)")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(MODEL_URL, dest_path, reporthook=progress_callback)
        print("\n[OK] Download completed successfully!")
        return True
    except Exception as e:
        print(f"\n[ERROR] Error downloading model: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download MediaPipe Hand Landmarker Task model.")
    parser.add_argument(
        "--force", action="store_true", help="Force re-download even if model exists"
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task"),
        help="Destination path for hand_landmarker.task",
    )
    args = parser.parse_args()
    success = download_model(Path(args.dest), force=args.force)
    sys.exit(0 if success else 1)
