from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enums
class CollaboratorRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DECLINED = "declined"
    REVOKED = "revoked"


class ProjectTemplateCategory(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    DATA_SCIENCE = "data-science"
    MACHINE_LEARNING = "ml"
    DESKTOP = "desktop"
    API = "api"
    MICROSERVICE = "microservice"
    GAME = "game"
    OTHER = "other"


class ExportFormat(str, Enum):
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    GIT = "git"
    JSON = "json"
    PDF = "pdf"
    MARKDOWN = "markdown"


# Project Template Schemas
class ProjectTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: ProjectTemplateCategory
    template_data: Optional[Dict[str, Any]] = None
    default_settings: Optional[Dict[str, Any]] = None
    required_dependencies: Optional[List[str]] = None
    version: str = Field(default="1.0.0")
    author: Optional[str] = None
    license: Optional[str] = None
    tags: Optional[List[str]] = None


class ProjectTemplateCreate(ProjectTemplateBase):
    is_public: bool = Field(default=True)


class ProjectTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[ProjectTemplateCategory] = None
    template_data: Optional[Dict[str, Any]] = None
    default_settings: Optional[Dict[str, Any]] = None
    required_dependencies: Optional[List[str]] = None
    version: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class ProjectTemplate(ProjectTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    usage_count: int
    rating: float
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class ProjectTemplateList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    name: str
    description: Optional[str]
    category: ProjectTemplateCategory
    version: str
    author: Optional[str]
    usage_count: int
    rating: float
    is_public: bool
    tags: Optional[List[str]]
    created_at: datetime


# Project Collaborator Schemas
class ProjectCollaboratorBase(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: CollaboratorRole = Field(default=CollaboratorRole.VIEWER)
    permissions: Optional[Dict[str, bool]] = None


class ProjectCollaboratorCreate(ProjectCollaboratorBase):
    pass


class ProjectCollaboratorUpdate(BaseModel):
    role: Optional[CollaboratorRole] = None
    permissions: Optional[Dict[str, bool]] = None
    invitation_status: Optional[InvitationStatus] = None


class ProjectCollaborator(ProjectCollaboratorBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    invitation_status: InvitationStatus
    invited_by: Optional[str]
    invited_at: datetime
    accepted_at: Optional[datetime]
    last_accessed: Optional[datetime]
    access_count: int


class ProjectCollaboratorInvite(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: CollaboratorRole = Field(default=CollaboratorRole.VIEWER)
    permissions: Optional[Dict[str, bool]] = None
    message: Optional[str] = None


# Project Settings Schemas
class ProjectSettingsBase(BaseModel):
    is_public: bool = Field(default=False)
    is_archived: bool = Field(default=False)
    enable_chat: bool = Field(default=True)
    enable_gendoc: bool = Field(default=True)
    enable_collaboration: bool = Field(default=False)
    export_formats: Optional[List[ExportFormat]] = None
    export_settings: Optional[Dict[str, Any]] = None
    default_llm_model: Optional[str] = None
    llm_context_settings: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ProjectSettingsCreate(ProjectSettingsBase):
    pass


class ProjectSettingsUpdate(BaseModel):
    is_public: Optional[bool] = None
    is_archived: Optional[bool] = None
    enable_chat: Optional[bool] = None
    enable_gendoc: Optional[bool] = None
    enable_collaboration: Optional[bool] = None
    export_formats: Optional[List[ExportFormat]] = None
    export_settings: Optional[Dict[str, Any]] = None
    default_llm_model: Optional[str] = None
    llm_context_settings: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ProjectSettings(ProjectSettingsBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime]


# Project Tag Schemas
class ProjectTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    category: Optional[str] = None


class ProjectTagCreate(ProjectTagBase):
    pass


class ProjectTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    category: Optional[str] = None


class ProjectTag(ProjectTagBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime]


# Project Version Schemas
class ProjectVersionBase(BaseModel):
    version_number: str = Field(..., min_length=1)
    version_name: Optional[str] = None
    description: Optional[str] = None
    commit_message: Optional[str] = None
    is_major: bool = Field(default=False)
    is_release: bool = Field(default=False)


class ProjectVersionCreate(ProjectVersionBase):
    pass


class ProjectVersionUpdate(BaseModel):
    version_name: Optional[str] = None
    description: Optional[str] = None
    commit_message: Optional[str] = None
    is_major: Optional[bool] = None
    is_release: Optional[bool] = None


class ProjectVersion(ProjectVersionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    project_id: int
    snapshot_data: Optional[Dict[str, Any]]
    file_count: int
    total_size: int
    created_by: Optional[str]
    parent_version_id: Optional[int]
    changes_summary: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]


class ProjectVersionList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    version_number: str
    version_name: Optional[str]
    description: Optional[str]
    is_major: bool
    is_release: bool
    created_by: Optional[str]
    created_at: datetime


# Project Analytics Schemas
class ProjectAnalytics(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    view_count: int
    download_count: int
    clone_count: int
    last_accessed: Optional[datetime]
    last_modified: Optional[datetime]
    total_lines_of_code: int
    file_count: int
    directory_count: int
    language_distribution: Optional[Dict[str, Any]]
    collaborator_count: int
    active_collaborators: int
    chat_sessions_count: int
    generated_docs_count: int
    exports_count: int
    custom_metrics: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]


class ProjectAnalyticsUpdate(BaseModel):
    view_count: Optional[int] = None
    download_count: Optional[int] = None
    clone_count: Optional[int] = None
    last_accessed: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    total_lines_of_code: Optional[int] = None
    file_count: Optional[int] = None
    directory_count: Optional[int] = None
    language_distribution: Optional[Dict[str, Any]] = None
    collaborator_count: Optional[int] = None
    active_collaborators: Optional[int] = None
    chat_sessions_count: Optional[int] = None
    generated_docs_count: Optional[int] = None
    exports_count: Optional[int] = None
    custom_metrics: Optional[Dict[str, Any]] = None


# Enhanced Project Schemas
class EnhancedProjectBase(BaseModel):
    """Enhanced project schema with additional features."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class EnhancedProjectCreate(EnhancedProjectBase):
    template_id: Optional[int] = None  # Create from template
    settings: Optional[ProjectSettingsCreate] = None
    tags: Optional[List[str]] = None
    collaborators: Optional[List[ProjectCollaboratorCreate]] = None


class EnhancedProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class EnhancedProject(EnhancedProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    upload_method: str
    upload_status: str
    original_filename: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Enhanced relationships
    settings: Optional[ProjectSettings] = None
    collaborators: List[ProjectCollaborator] = []
    tags: List[ProjectTag] = []
    versions: List[ProjectVersionList] = []
    analytics: Optional[ProjectAnalytics] = None


class EnhancedProjectList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    name: str
    description: Optional[str]
    upload_status: str
    file_count: int = 0
    total_size: int = 0
    collaborator_count: int = 0
    last_accessed: Optional[datetime]
    is_public: bool = False
    is_archived: bool = False
    tags: List[str] = []
    created_at: datetime


# Search and Filter Schemas
class ProjectSearchFilter(BaseModel):
    query: Optional[str] = None  # Text search in name/description
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None
    is_archived: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_file_count: Optional[int] = None
    max_file_count: Optional[int] = None
    has_collaborators: Optional[bool] = None
    language: Optional[str] = None


class ProjectSearchResult(BaseModel):
    projects: List[EnhancedProjectList]
    total: int
    page: int
    per_page: int
    pages: int


# Export Schemas
class ProjectExportRequest(BaseModel):
    format: ExportFormat
    include_files: bool = Field(default=True)
    include_metadata: bool = Field(default=True)
    include_analytics: bool = Field(default=False)
    version_id: Optional[int] = None  # Export specific version
    custom_settings: Optional[Dict[str, Any]] = None


class ProjectExportResponse(BaseModel):
    success: bool
    export_id: str
    format: ExportFormat
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    expires_at: Optional[datetime] = None
    message: str


# API Response Schemas
class ProjectOperationResponse(BaseModel):
    success: bool
    message: str
    project_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class BulkOperationResponse(BaseModel):
    success: bool
    processed: int
    failed: int
    errors: List[str] = []
    results: List[Dict[str, Any]] = [] 