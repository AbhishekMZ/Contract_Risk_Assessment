from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Smart Contract Analyzer"
    DEBUG: bool = True
    VERSION: str = "0.1.0"
    
    # API settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list = ["*"]
    
    # File upload settings
    UPLOAD_FOLDER: str = str(Path("uploads").absolute())
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {".sol"}
    
    # Analysis settings
    TIMEOUT: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
