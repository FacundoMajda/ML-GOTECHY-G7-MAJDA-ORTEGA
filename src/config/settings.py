# src/config/settings.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print(f"[DEBUG] config.settings: loading .env file", flush=True)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

NEON_DB_URL = os.environ.get("NEON_DB_URL", "").strip()
if not NEON_DB_URL:
    print("[FATAL] NEON_DB_URL no esta definida.", flush=True)
    print("  Para docker-compose: pone la URL en .env", flush=True)
    print("  Para docker run:    docker run -e NEON_DB_URL=postgresql://...", flush=True)
    print("  Para local venv:    export NEON_DB_URL=postgresql://...", flush=True)
    sys.exit(1)

YOLO_MODEL_PATH = str(
    BASE_DIR / os.environ.get("YOLO_MODEL_PATH", "src/inference/yolo11n.pt")
)

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "outputs")
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "uploads")
