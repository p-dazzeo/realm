from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/realm_db",
        description="Database connection URL"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="API auto-reload")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, 
        description="Access token expiration time in minutes"
    )
    
    # Parser Service Configuration
    parser_service_url: str = Field(
        default="http://localhost:8001",
        description="External parser service URL"
    )
    parser_service_enabled: bool = Field(
        default=True,
        description="Whether to use external parser service"
    )
    parser_service_timeout: int = Field(
        default=30,
        description="Parser service timeout in seconds"
    )
    
    # File Upload Configuration
    max_file_size: int = Field(
        default=50,
        description="Maximum file size in MB"
    )
    max_project_size: int = Field(
        default=500,
        description="Maximum project size in MB"
    )
    allowed_extensions: List[str] = Field(
        default=[
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", 
            ".hpp", ".cs", ".rb", ".go", ".rs", ".php", ".html", ".css", 
            ".scss", ".sass", ".less", ".sql", ".md", ".txt", ".json", 
            ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"
        ],
        description="Allowed file extensions for upload"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Storage paths
    storage_path: str = Field(
        default="./storage",
        description="Local storage path for projects"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings() 