"""Application configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATA_DIR = Path(os.getenv("FDM_DATA_DIR", ROOT / "data"))
EXPORT_DIR = Path(os.getenv("FDM_EXPORT_DIR", ROOT / "exports"))
DB_PATH = Path(os.getenv("FDM_DATABASE", DATA_DIR / "fashion_manager.db"))
DEMO_MODE = os.getenv("FDM_DEMO_MODE", "true").lower() in {"1", "true", "yes"}
MODEL_NAME = os.getenv("FDM_VIT_MODEL", "google/vit-base-patch16-224")
APP_NAME = "Atelier — Fashion Design Manager"
for folder in (DATA_DIR, EXPORT_DIR, ROOT / "logs", ROOT / "assets"):
    folder.mkdir(parents=True, exist_ok=True)
