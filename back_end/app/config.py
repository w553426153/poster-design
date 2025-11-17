from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Set
import os
from pathlib import Path


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Poster Design API"
    DEBUG: bool = True

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        # Vite dev server
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # File upload settings
    UPLOAD_FOLDER: str = str(Path(__file__).parent.parent / "uploads")
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS: Set[str] = {"psd"}

    # PSD processing settings
    TESSERACT_CMD: str = "/usr/bin/tesseract"  # Update this path based on your system

    # Pydantic v2 / pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


# Create uploads directory if it doesn't exist
os.makedirs(Settings().UPLOAD_FOLDER, exist_ok=True)

settings = Settings()
