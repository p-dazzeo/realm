"""
Custom exception classes for better error handling.
These exceptions are more specific than HTTPException and allow for more detailed error handling.
"""
from typing import Optional, Dict, Any, List, Union
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception class for application-specific exceptions."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "APP_ERROR",
        headers: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an AppException.
        
        Args:
            status_code: HTTP status code
            detail: Human-readable error description
            error_code: Machine-readable error code for clients
            headers: Optional HTTP headers to include in the response
            context: Optional additional context about the error
        """
        self.error_code = error_code
        self.context = context or {}
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# Not Found Exceptions
class EntityNotFoundException(AppException):
    """Exception raised when an entity is not found."""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: Union[str, int],
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an EntityNotFoundException.
        
        Args:
            entity_type: Type of entity that was not found (e.g., "Project", "File")
            entity_id: ID of the entity that was not found
            detail: Optional custom detail message
            headers: Optional HTTP headers to include in the response
        """
        if detail is None:
            detail = f"{entity_type} with id {entity_id} not found"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=f"{entity_type.upper()}_NOT_FOUND",
            headers=headers,
            context={"entity_type": entity_type, "entity_id": entity_id}
        )


class ProjectNotFoundException(EntityNotFoundException):
    """Exception raised when a project is not found."""
    
    def __init__(
        self,
        project_id: Union[str, int],
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ProjectNotFoundException.
        
        Args:
            project_id: ID of the project that was not found
            detail: Optional custom detail message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(
            entity_type="Project",
            entity_id=project_id,
            detail=detail,
            headers=headers
        )


class FileNotFoundException(EntityNotFoundException):
    """Exception raised when a file is not found."""
    
    def __init__(
        self,
        file_id: Union[str, int],
        project_id: Optional[Union[str, int]] = None,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a FileNotFoundException.
        
        Args:
            file_id: ID of the file that was not found
            project_id: Optional ID of the project the file belongs to
            detail: Optional custom detail message
            headers: Optional HTTP headers to include in the response
        """
        context = {"file_id": file_id}
        if project_id is not None:
            context["project_id"] = project_id
            if detail is None:
                detail = f"File with id {file_id} not found in project {project_id}"
        
        super().__init__(
            entity_type="File",
            entity_id=file_id,
            detail=detail,
            headers=headers
        )
        self.context.update(context)


# Validation Exceptions
class ValidationException(AppException):
    """Exception raised when validation fails."""
    
    def __init__(
        self,
        detail: str,
        field_errors: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ValidationException.
        
        Args:
            detail: Human-readable error description
            field_errors: Optional dictionary mapping field names to error messages
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            headers=headers,
            context={"field_errors": field_errors or {}}
        )


# Storage Exceptions
class FileStorageException(AppException):
    """Exception raised when file storage operations fail."""
    
    def __init__(
        self,
        detail: str,
        operation: str,
        filename: Optional[str] = None,
        storage_path: Optional[str] = None,
        original_error: Optional[Exception] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a FileStorageException.
        
        Args:
            detail: Human-readable error description
            operation: The storage operation that failed (e.g., "save", "delete")
            filename: Optional name of the file involved
            storage_path: Optional storage path where the operation was attempted
            original_error: Optional original exception that was caught
            headers: Optional HTTP headers to include in the response
        """
        context = {"operation": operation}
        if filename:
            context["filename"] = filename
        if storage_path:
            context["storage_path"] = storage_path
        if original_error:
            context["original_error"] = str(original_error)
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="FILE_STORAGE_ERROR",
            headers=headers,
            context=context
        )


# Database Exceptions
class DatabaseException(AppException):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        detail: str,
        operation: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[Union[str, int]] = None,
        original_error: Optional[Exception] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a DatabaseException.
        
        Args:
            detail: Human-readable error description
            operation: The database operation that failed (e.g., "create", "update")
            entity_type: Optional type of entity involved in the operation
            entity_id: Optional ID of the entity involved in the operation
            original_error: Optional original exception that was caught
            headers: Optional HTTP headers to include in the response
        """
        context = {"operation": operation}
        if entity_type:
            context["entity_type"] = entity_type
        if entity_id:
            context["entity_id"] = entity_id
        if original_error:
            context["original_error"] = str(original_error)
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
            headers=headers,
            context=context
        )


# Service-Specific Exceptions
class ParserServiceException(AppException):
    """Exception raised when the parser service fails."""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        parser_error: Optional[str] = None,
        original_error: Optional[Exception] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ParserServiceException.
        
        Args:
            detail: Human-readable error description
            status_code: HTTP status code
            parser_error: Optional error message from the parser service
            original_error: Optional original exception that was caught
            headers: Optional HTTP headers to include in the response
        """
        context = {}
        if parser_error:
            context["parser_error"] = parser_error
        if original_error:
            context["original_error"] = str(original_error)
        
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code="PARSER_SERVICE_ERROR",
            headers=headers,
            context=context
        ) 