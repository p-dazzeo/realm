"""
Configuration management for the application.
This module provides Pydantic settings classes for all application configurations.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationInfo, field_validator, DirectoryPath
from typing import List, Dict, Any, Optional
import logging

# Get environment
ENV = os.getenv("APP_ENV", "development").lower()


class CoreSettings(BaseSettings):
    """Core application settings."""
    
    model_config = SettingsConfigDict(
        env_file=f".env.{ENV}" if os.path.exists(f".env.{ENV}") else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/realm_db",
        description="Database connection URL"
    )
    
    # API Server
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_reload: bool = Field(default=True, description="Enable auto-reload for development")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for token generation and encryption"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate secret key based on environment."""
        if ENV == "production" and v == "your-secret-key-change-in-production":
            raise ValueError("Default secret key cannot be used in production")
        return v


class UploadSettings(BaseSettings):
    """Upload and file handling settings."""
    
    model_config = SettingsConfigDict(
        env_file=f".env.{ENV}" if os.path.exists(f".env.{ENV}") else ".env",
        env_file_encoding="utf-8",
        env_prefix="UPLOAD_",
        case_sensitive=False
    )
    
    # Parser Service
    parser_service_url: str = Field(
        default="http://localhost:8001",
        description="URL for the parser service"
    )
    parser_service_enabled: bool = Field(
        default=True,
        description="Enable parser service integration"
    )
    parser_service_timeout: int = Field(
        default=30,
        description="Timeout for parser service requests in seconds"
    )
    
    # File Size Limits
    max_file_size: int = Field(
        default=50,
        description="Maximum individual file size in MB"
    )
    max_project_size: int = Field(
        default=500,
        description="Maximum project size in MB"
    )
    
    # File Extensions
    allowed_extensions: List[str] = Field(
        default=[".cbl", ".cob", ".cpy", ".jcl", ".CBL", ".CPY", ".JCL", ".COB"],
        description="List of allowed file extensions"
    )
    
    # Storage
    additional_files_dir: str = Field(
        default="./storage/additional_files",
        description="Directory for storing additional project files"
    )
    
    # Validations
    @field_validator("max_file_size", "max_project_size", "parser_service_timeout")
    @classmethod
    def validate_positive_integers(cls, v: int, info: ValidationInfo) -> int:
        """Validate that integer fields are positive."""
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v
    
    @field_validator("additional_files_dir")
    @classmethod
    def validate_storage_dir(cls, v: str) -> str:
        """Ensure storage directory exists."""
        os.makedirs(v, exist_ok=True)
        return v


def get_settings() -> Dict[str, Any]:
    """Get all application settings."""
    return {
        "core": core_settings.model_dump(),
        "upload": upload_settings.model_dump()
    }


def validate_all_settings() -> bool:
    """Validate all application settings."""
    try:
        # Force validation by accessing all settings
        _ = core_settings.model_dump()
        _ = upload_settings.model_dump()
        
        # Create required directories
        os.makedirs(os.path.dirname(upload_settings.additional_files_dir), exist_ok=True)
        
        return True
    except Exception as e:
        logging.error(f"Configuration validation failed: {str(e)}")
        return False


# Global settings instances
core_settings = CoreSettings()
upload_settings = UploadSettings()

# Legacy alias for backward compatibility
settings = core_settings 