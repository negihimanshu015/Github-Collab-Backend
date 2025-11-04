from datetime import datetime
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "AI-Powered GitHub Collaboration SaaS"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/ai_github_saas"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # API Keys (required)
    GEMINI_API_KEY: str
    GITHUB_ACCESS_TOKEN: str
    ASSEMBLYAI_API_KEY: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Analysis limits
    MAX_CODE_SIZE_KB: int = 500
    MAX_ANALYSIS_TIMEOUT_SECONDS: int = 30
    
    @staticmethod
    def get_current_time() -> str:
        return datetime.utcnow().isoformat()
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()