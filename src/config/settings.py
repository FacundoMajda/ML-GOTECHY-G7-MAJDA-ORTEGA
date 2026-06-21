# src/config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

NEON_DB_URL = os.environ["NEON_DB_URL"]

YOLO_MODEL_PATH = str(
    BASE_DIR / os.environ.get("YOLO_MODEL_PATH", "src/inference/yolo11n.pt")
)

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "outputs")
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
