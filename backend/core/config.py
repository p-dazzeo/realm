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
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".hpp", ".cs", ".rb", ".go", ".rs", ".php", ".html", ".css",
        ".sql", ".md", ".txt", ".json", ".xml", ".yaml", ".yml"
    ])
    
    class Config:
        env_file = ".env"
        env_prefix = "UPLOAD_"


class ProjectsSettings(BaseSettings):
    # Template settings
    max_templates_per_user: int = Field(default=50)
    default_template_rating: float = Field(default=0.0)
    
    # Collaboration settings
    max_collaborators_per_project: int = Field(default=20)
    invitation_expiry_days: int = Field(default=7)
    
    # Export settings
    export_max_file_size: int = Field(default=1000)  # MB
    export_link_expiry_hours: int = Field(default=24)
    
    # Analytics settings
    analytics_retention_days: int = Field(default=365)
    track_detailed_analytics: bool = Field(default=True)
    
    # Version settings
    max_versions_per_project: int = Field(default=50)
    auto_create_versions: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        env_prefix = "PROJECTS_"


# Global settings instances
core_settings = CoreSettings()
upload_settings = UploadSettings()
projects_settings = ProjectsSettings()
settings = core_settings  # Backward compatibility 