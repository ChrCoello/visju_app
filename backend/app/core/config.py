from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "Vidarshov Gård Recording App"
    DEBUG: bool = False
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./vidarshov.db"
    
    # Google Drive API Configuration
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = "./credentials.json"
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    
    # LLM Configuration
    CLAUDE_API_KEY: Optional[str] = None
    PYDANTIC_AI_MODEL: str = "claude-3-5-sonnet-latest"
    
    # Logfire Configuration
    LOGFIRE_TOKEN: Optional[str] = None
    
    # Audio Processing Configuration
    AUDIO_STORAGE_PATH: str = "./audio_files/"
    TEMP_PROCESSING_PATH: str = "./temp/"
    
    # File Processing Configuration
    MAX_FILE_SIZE_MB: int = 500
    SUPPORTED_AUDIO_FORMATS: List[str] = ["m4a", "mp3", "wav"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()