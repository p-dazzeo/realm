from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import BaseModel, UUIDMixin
from typing import Optional, Dict, Any
import uuid


class Project(BaseModel, UUIDMixin):
    __tablename__ = "projects"
    
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    
    # Upload metadata
    upload_method = Column(String, nullable=False)  # "parser" or "direct"
    upload_status = Column(String, default="pending")  # "pending", "processing", "completed", "failed"
    original_filename = Column(String)
    file_size = Column(BigInteger)  # Size in bytes
    
    # Parser-specific data (if using parser)
    parser_response = Column(JSON)  # Structured data from parser
    parser_version = Column(String)
    
    # Relationships
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    
    # Using lazy imports to avoid circular imports
    collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan", lazy="select")
    settings = relationship("ProjectSettings", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="select") 
    tags = relationship("ProjectTag", secondary="project_tag_associations", back_populates="projects", lazy="select")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan", lazy="select")
    analytics = relationship("ProjectAnalytics", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="select")


class ProjectFile(BaseModel):
    __tablename__ = "project_files"
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # File metadata
    filename = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False, index=True)  # Full path within project
    relative_path = Column(String, nullable=False)  # Relative path from project root
    file_extension = Column(String, index=True)
    file_size = Column(BigInteger)  # Size in bytes
    
    # File content (for direct upload method)
    content = Column(Text)  # Raw file content
    content_hash = Column(String, index=True)  # SHA-256 hash for deduplication
    
    # Parser-specific data (if from parser)
    parsed_data = Column(JSON)  # Structured data from parser for this file
    
    # Language and analysis metadata
    language = Column(String, index=True)  # Programming language detected
    loc = Column(Integer)  # Lines of code
    is_binary = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="files")


class UploadSession(BaseModel):
    __tablename__ = "upload_sessions"
    
    session_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Session metadata
    status = Column(String, default="active")  # "active", "completed", "failed", "expired"
    upload_method = Column(String)  # "parser" or "direct"
    
    # Progress tracking
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    
    # Error tracking
    errors = Column(JSON)  # List of errors encountered
    warnings = Column(JSON)  # List of warnings
    
    # Associated project
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    expires_at = Column(DateTime(timezone=True))  # Session expiration 