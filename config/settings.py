"""Environment-based application settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Asia/Jakarta")
DASHBOARD_TELEGRAM_ID = os.getenv("DASHBOARD_TELEGRAM_ID", "").strip()

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "gymbuddy"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}
