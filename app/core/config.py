from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
import secrets
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Yuki Invoice Automation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Yuki API
    YUKI_API_URL: str
    YUKI_USERNAME: str
    YUKI_PASSWORD: str
    
    # Database
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER", "postgres"),
            password=values.get("POSTGRES_PASSWORD", "postgres"),
            host=values.get("POSTGRES_SERVER", "localhost"),
            path=f"/{values.get('POSTGRES_DB', 'yuki_automation')}",
        )
    
    # OCR Settings
    TESSERACT_CMD: str = "tesseract"
    OCR_LANGUAGE: str = "eng+nld"  # English + Dutch
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings() 