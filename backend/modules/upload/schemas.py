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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Sample COBOL Project",
                "description": "A collection of COBOL programs for payroll processing"
            }
        }
    )


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    upload_status: Optional[UploadStatus] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Project Name",
                "description": "Updated project description"
            }
        }
    )


class ProjectFile(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "filename": "PAYROLL.CBL",
                "file_path": "src/payroll/PAYROLL.CBL",
                "relative_path": "src/payroll/PAYROLL.CBL",
                "file_extension": ".CBL",
                "file_size": 12500,
                "content": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PAYROLL.\n       ...",
                "content_hash": "a1b2c3d4e5f6...",
                "parsed_data": {"variables": ["EMPLOYEE-ID", "SALARY"], "paragraphs": ["CALCULATE-SALARY"]},
                "language": "cobol",
                "loc": 150,
                "is_binary": False,
                "created_at": "2023-01-15T12:30:45Z",
                "updated_at": "2023-01-15T14:20:15Z"
            }
        }
    )
    
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


class AdditionalProjectFileSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "filename": "requirements.docx",
                "file_path": "/storage/additional_files/project_12345/requirements.docx",
                "file_size": 2500000,
                "description": "Project requirements document",
                "created_at": "2023-01-16T09:45:30Z",
                "updated_at": "2023-01-16T09:45:30Z"
            }
        }
    )

    id: int
    uuid: str
    filename: str
    file_path: str # Or consider if this should be different for API response, e.g., a download link
    file_size: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class AdditionalFileCreateRequest(BaseModel):
    description: Optional[str] = Field(None, description="Optional description for the additional file.")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Technical documentation for the COBOL program"
            }
        }
    )

class AdditionalFileUpdateRequest(BaseModel):
    description: Optional[str] = Field(None, description="New description for the additional file.")
    # Add other updatable fields here if any in the future, e.g., filename if allowed
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated technical documentation"
            }
        }
    )


class Project(ProjectBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Payroll System",
                "description": "Legacy payroll processing system",
                "uuid": "12345678-abcd-1234-efgh-1234567890ab",
                "upload_method": "parser",
                "upload_status": "completed",
                "original_filename": "payroll_system.zip",
                "file_size": 5250000,
                "parser_response": {"summary": "10 COBOL programs, 5 copybooks"},
                "parser_version": "1.2.0",
                "created_at": "2023-01-15T10:30:00Z",
                "updated_at": "2023-01-15T10:35:25Z",
                "files": [
                    {
                        "id": 1,
                        "filename": "PAYROLL.CBL",
                        "file_path": "src/PAYROLL.CBL",
                        "relative_path": "src/PAYROLL.CBL",
                        "file_extension": ".CBL",
                        "file_size": 12500,
                        "language": "cobol",
                        "loc": 150,
                        "is_binary": False,
                        "created_at": "2023-01-15T10:31:00Z"
                    }
                ],
                "additional_files": []
            }
        }
    )
    
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
    additional_files: List[AdditionalProjectFileSchema] = []


class ProjectSummary(ProjectBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Payroll System",
                "description": "Legacy payroll processing system",
                "uuid": "12345678-abcd-1234-efgh-1234567890ab",
                "upload_method": "parser",
                "upload_status": "completed",
                "file_count": 15,
                "total_size": 5250000,
                "created_at": "2023-01-15T10:30:00Z"
            }
        }
    )
    
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
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "upload_method": "parser"
            }
        }
    )


class UploadSessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    failed_files: Optional[int] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    project_id: Optional[int] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "completed",
                "total_files": 10,
                "processed_files": 9,
                "failed_files": 1,
                "errors": ["Error parsing file XYZ.CBL: Invalid syntax at line 42"],
                "warnings": ["File ABC.CPY contains deprecated COBOL syntax"],
                "project_id": 1
            }
        }
    )


class UploadSession(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "session_id": "sess_12345abcde",
                "status": "completed",
                "upload_method": "parser",
                "total_files": 10,
                "processed_files": 9,
                "failed_files": 1,
                "errors": ["Error parsing file XYZ.CBL: Invalid syntax at line 42"],
                "warnings": ["File ABC.CPY contains deprecated COBOL syntax"],
                "project_id": 1,
                "created_at": "2023-01-15T10:25:00Z",
                "updated_at": "2023-01-15T10:35:00Z",
                "expires_at": "2023-01-16T10:25:00Z"
            }
        }
    )
    
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
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "PAYROLL.CBL",
                "relative_path": "src/PAYROLL.CBL",
                "content": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PAYROLL.\n       ...",
                "content_hash": "a1b2c3d4e5f6..."
            }
        }
    )


class ProjectUploadRequest(BaseModel):
    project: ProjectCreate
    files: List[FileUploadRequest]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project": {
                    "name": "Sample COBOL Project",
                    "description": "A collection of COBOL programs for payroll processing"
                },
                "files": [
                    {
                        "filename": "PAYROLL.CBL",
                        "relative_path": "src/PAYROLL.CBL",
                        "content": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PAYROLL.\n       ...",
                        "content_hash": "a1b2c3d4e5f6..."
                    }
                ]
            }
        }
    )


# Parser Service Schemas
class ParserRequest(BaseModel):
    project_name: str
    files: List[Dict[str, Any]]  # Flexible format for parser
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_name": "Sample COBOL Project",
                "files": [
                    {
                        "filename": "PAYROLL.CBL",
                        "path": "src/PAYROLL.CBL",
                        "content": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PAYROLL.\n       ...",
                        "size": 12500
                    }
                ]
            }
        }
    )


class ParserResponse(BaseModel):
    success: bool
    version: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "version": "1.2.0",
                "data": {
                    "summary": "1 COBOL program analyzed",
                    "files": {
                        "src/PAYROLL.CBL": {
                            "variables": ["EMPLOYEE-ID", "SALARY"],
                            "paragraphs": ["CALCULATE-SALARY"],
                            "loc": 150
                        }
                    }
                },
                "error": None
            }
        }
    )


# API Response Schemas
class UploadResponse(BaseModel):
    success: bool
    session_id: str
    project_id: Optional[int] = None
    upload_method: UploadMethod
    message: str
    warnings: Optional[List[str]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "session_id": "sess_12345abcde",
                "project_id": 1,
                "upload_method": "parser",
                "message": "Project uploaded successfully",
                "warnings": ["One file was skipped due to unsupported extension"]
            }
        }
    )


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None 
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Upload failed",
                "detail": "Failed to parse file PAYROLL.CBL due to syntax error at line 42",
                "code": "PARSER_ERROR"
            }
        }
    ) 