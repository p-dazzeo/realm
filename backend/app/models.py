from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from typing import Optional, Dict, Any
import uuid


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
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
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")


class ProjectFile(Base):
    __tablename__ = "project_files"
    
    id = Column(Integer, primary_key=True, index=True)
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
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="files")


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
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
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # Session expiration 