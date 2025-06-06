from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, BigInteger, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import BaseModel, UUIDMixin
from typing import Optional, Dict, Any
import uuid


class ProjectTemplate(BaseModel, UUIDMixin):
    """Project templates for quick project creation."""
    __tablename__ = "project_templates"
    
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    category = Column(String, index=True)  # "web", "mobile", "data-science", "ml", etc.
    
    # Template configuration
    template_data = Column(JSON)  # Template structure and files
    default_settings = Column(JSON)  # Default project settings
    required_dependencies = Column(JSON)  # List of required packages/dependencies
    
    # Template metadata
    version = Column(String, default="1.0.0")
    author = Column(String)
    license = Column(String)
    tags = Column(JSON)  # List of tags for categorization
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    
    # Visibility and access
    is_public = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)


class ProjectCollaborator(BaseModel):
    """Project collaboration and team management."""
    __tablename__ = "project_collaborators"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)  # User identifier (email, UUID, etc.)
    
    # Collaboration details
    role = Column(String, default="viewer")  # "owner", "admin", "editor", "viewer"
    permissions = Column(JSON)  # Specific permissions for this collaborator
    
    # Invitation management
    invitation_status = Column(String, default="active")  # "pending", "active", "declined", "revoked"
    invited_by = Column(String)  # User who sent the invitation
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    
    # Activity tracking
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Relationships
    project = relationship("Project", back_populates="collaborators")


class ProjectSettings(BaseModel):
    """Project-specific settings and preferences."""
    __tablename__ = "project_settings"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    
    # Project configuration
    is_public = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Feature toggles
    enable_chat = Column(Boolean, default=True)
    enable_gendoc = Column(Boolean, default=True)
    enable_collaboration = Column(Boolean, default=False)
    
    # Export settings
    export_formats = Column(JSON)  # Preferred export formats
    export_settings = Column(JSON)  # Export-specific configurations
    
    # AI/LLM settings
    default_llm_model = Column(String)
    llm_context_settings = Column(JSON)
    
    # Notification settings
    notification_preferences = Column(JSON)
    
    # Custom metadata
    custom_fields = Column(JSON)  # User-defined fields
    
    # Relationships
    project = relationship("Project", back_populates="settings", uselist=False)


class ProjectTag(BaseModel):
    """Tags for project categorization and search."""
    __tablename__ = "project_tags"
    
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    color = Column(String)  # Hex color code for UI
    category = Column(String, index=True)  # Tag category for organization
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    # Relationships (many-to-many with projects)
    projects = relationship("Project", secondary="project_tag_associations", back_populates="tags")


class ProjectTagAssociation(BaseModel):
    """Association table for project-tag many-to-many relationship."""
    __tablename__ = "project_tag_associations"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("project_tags.id"), nullable=False)
    
    # Additional metadata for the association
    added_by = Column(String)  # User who added this tag
    added_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectVersion(BaseModel, UUIDMixin):
    """Project versioning and snapshots."""
    __tablename__ = "project_versions"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Version information
    version_number = Column(String, nullable=False)  # e.g., "1.0.0", "v1.2.3"
    version_name = Column(String)  # Human-readable name
    description = Column(Text)
    
    # Snapshot data
    snapshot_data = Column(JSON)  # Complete project state at this version
    file_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)
    
    # Version metadata
    is_major = Column(Boolean, default=False)
    is_release = Column(Boolean, default=False)
    created_by = Column(String)  # User who created this version
    
    # Git-like features
    parent_version_id = Column(Integer, ForeignKey("project_versions.id"))
    commit_message = Column(Text)
    changes_summary = Column(JSON)  # Summary of changes from previous version
    
    # Relationships
    project = relationship("Project", back_populates="versions")
    parent_version = relationship("ProjectVersion", remote_side="ProjectVersion.id")


class ProjectAnalytics(BaseModel):
    """Project analytics and usage statistics."""
    __tablename__ = "project_analytics"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    
    # Access statistics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    clone_count = Column(Integer, default=0)
    
    # Time-based analytics
    last_accessed = Column(DateTime(timezone=True))
    last_modified = Column(DateTime(timezone=True))
    
    # Size and complexity metrics
    total_lines_of_code = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    directory_count = Column(Integer, default=0)
    language_distribution = Column(JSON)  # Distribution of programming languages
    
    # Collaboration metrics
    collaborator_count = Column(Integer, default=0)
    active_collaborators = Column(Integer, default=0)  # Active in last 30 days
    
    # Feature usage
    chat_sessions_count = Column(Integer, default=0)
    generated_docs_count = Column(Integer, default=0)
    exports_count = Column(Integer, default=0)
    
    # Custom metrics
    custom_metrics = Column(JSON)
    
    # Relationships
    project = relationship("Project", back_populates="analytics", uselist=False)


# Enhanced Project model (extends the upload Project model)
# Note: This would typically extend or replace the existing Project model
# For now, we'll add relationships that can be used with the existing Project model
# In a full implementation, you might want to migrate the existing Project model

# Add these relationships to the existing Project model in modules/upload/models.py:
# collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")
# settings = relationship("ProjectSettings", back_populates="project", uselist=False, cascade="all, delete-orphan")
# tags = relationship("ProjectTag", secondary="project_tag_associations", back_populates="projects")
# versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")
# analytics = relationship("ProjectAnalytics", back_populates="project", uselist=False, cascade="all, delete-orphan") 