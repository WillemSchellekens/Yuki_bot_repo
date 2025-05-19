from typing import Optional
from pydantic_settings import BaseSettings
import secrets
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Yuki Invoice Automation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # Yuki API
    YUKI_API_URL: str
    YUKI_USERNAME: str
    YUKI_PASSWORD: str
    YUKI_ADMINISTRATION_ID: str
    
    # Database
    DATABASE_URL: str
    
    # OCR Settings
    TESSERACT_CMD: str = "tesseract"
    OCR_LANGUAGE: str = "eng+nld"  # English + Dutch
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        # extra = "allow"  # Uncomment if you want to allow extra fields


@lru_cache()
def get_settings() -> Settings:
    return Settings() 