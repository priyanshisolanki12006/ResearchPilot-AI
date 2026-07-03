import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "ResearchPilot AI"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkeyforresearchpilotai2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    
    # Data Storage
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma"
    DB_PATH: Path = BASE_DIR / "data" / "researchpilot.db"
    
    # Model configuration
    GEMINI_MODEL: str = "gemini-1.5-flash" # Default gemini model
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
