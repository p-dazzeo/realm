from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class CoreSettings(BaseSettings):
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/realm_db")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    secret_key: str = Field(default="your-secret-key-change-in-production")
    log_level: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"

class UploadSettings(BaseSettings):
    parser_service_url: str = Field(default="http://localhost:8001")
    parser_service_enabled: bool = Field(default=True)
    parser_service_timeout: int = Field(default=30)
    max_file_size: int = Field(default=50)
    max_project_size: int = Field(default=500)
    allowed_extensions: List[str] = Field(default=[
        ".cbl", ".cob", ".cpy", ".jcl", ".CBL", ".CPY", ".JCL", ".COB"
    ])
    
    class Config:
        env_file = ".env"
        env_prefix = "UPLOAD_"


# Global settings instances
core_settings = CoreSettings()
upload_settings = UploadSettings()
settings = core_settings  # Backward compatibility 