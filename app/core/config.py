from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """
    application settings and configuration.
    
    attributes:
        project_name: name of the project
        version: current version of the application
        api_v1_str: api version 1 prefix
        database_url: sqlite database url
        sqlite_url: actual sqlite file path
    """
    
    # API Config
    PROJECT_NAME: str = "Tree Management API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    SQLITE_FILE: str = "tree_api.db"
    DATABASE_URL: str = f"sqlite:///./{SQLITE_FILE}"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    
    # Computed Properties
    @property
    def sqlite_url(self) -> Path:
        """
        get the sqlite database file path.
        
        returns:
            path: absolute path to the sqlite database file
        """
        return Path(self.SQLITE_FILE).absolute()
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Global settings instance
settings = Settings() 