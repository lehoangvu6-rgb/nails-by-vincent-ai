from pathlib import Path
from dotenv import load_dotenv
import os

# Đọc file .env
load_dotenv()

# Thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:

    # ==========================
    # BRAND
    # ==========================
    BUSINESS_NAME = "Nails By Vincent"

    OWNER = "Vincent"

    LANGUAGE = "English"

    TIMEZONE = "America/New_York"

    # ==========================
    # PROJECT PATHS
    # ==========================
    DATA_DIR = BASE_DIR / "data"

    IMAGES_DIR = BASE_DIR / "images"

    VIDEOS_DIR = BASE_DIR / "videos"

    MEMORY_DIR = BASE_DIR / "memory"

    PROMPTS_DIR = BASE_DIR / "prompts"

    LOGS_DIR = BASE_DIR / "logs"

    # ==========================
    # API KEYS
    # ==========================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    CANVA_API_KEY = os.getenv("CANVA_API_KEY")


settings = Settings()  