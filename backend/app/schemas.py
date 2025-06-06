from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UploadMethod(str, Enum):
    PARSER = "parser"
    DIRECT = "direct"


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    upload_status: Optional[UploadStatus] = None


class ProjectFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    file_path: str
    relative_path: str
    file_extension: Optional[str]
    file_size: Optional[int]
    content: Optional[str]
    content_hash: Optional[str]
    parsed_data: Optional[Dict[str, Any]]
    language: Optional[str]
    loc: Optional[int]
    is_binary: bool
    created_at: datetime
    updated_at: Optional[datetime]


class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    upload_method: UploadMethod
    upload_status: UploadStatus
    original_filename: Optional[str]
    file_size: Optional[int]
    parser_response: Optional[Dict[str, Any]]
    parser_version: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    files: List[ProjectFile] = []
    additional_file_paths: Optional[List[str]] = None


class ProjectSummary(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: str
    upload_method: UploadMethod
    upload_status: UploadStatus
    file_count: int = 0
    total_size: int = 0
    created_at: datetime


# Upload Session Schemas
class UploadSessionCreate(BaseModel):
    upload_method: UploadMethod


class UploadSessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    failed_files: Optional[int] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    project_id: Optional[int] = None


class UploadSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_id: str
    status: SessionStatus
    upload_method: Optional[UploadMethod]
    total_files: int
    processed_files: int
    failed_files: int
    errors: Optional[List[str]]
    warnings: Optional[List[str]]
    project_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]


# File Upload Schemas
class FileUploadRequest(BaseModel):
    filename: str
    relative_path: str
    content: str
    content_hash: Optional[str] = None


class ProjectUploadRequest(BaseModel):
    project: ProjectCreate
    files: List[FileUploadRequest]


# Parser Service Schemas
class ParserRequest(BaseModel):
    project_name: str
    files: List[Dict[str, Any]]  # Flexible format for parser


class ParserResponse(BaseModel):
    success: bool
    version: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]


# API Response Schemas
class UploadResponse(BaseModel):
    success: bool
    session_id: str
    project_id: Optional[int] = None
    upload_method: UploadMethod
    message: str
    warnings: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None 