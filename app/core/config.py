from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tree Management API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./tree_api.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 