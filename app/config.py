# app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    DB_CFG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "omnissiah"),
        "user": os.getenv("DB_USER", "omnissiah_app"),
        "password": os.getenv("DB_PASS", ""),
    }
    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", str(BASE_DIR / "uploads"))
    EXPENSES_UPLOAD_DIR = os.getenv("EXPENSES_UPLOAD_DIR", os.path.join(UPLOAD_ROOT, "expenses"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB
    ALLOWED_RECEIPT_EXT = {"pdf","png","jpg","jpeg","gif","webp"}
