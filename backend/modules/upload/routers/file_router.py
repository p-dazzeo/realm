"""
File-related endpoints for the upload module.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from core.dependencies import get_database
from modules.upload.schemas import (
    AdditionalProjectFileSchema, 
    AdditionalFileCreateRequest, 
    AdditionalFileUpdateRequest
)
from modules.upload.service import upload_service
from shared.exceptions import ProjectNotFoundException, FileNotFoundException

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/projects/{project_id}/additional_files",
    response_model=AdditionalProjectFileSchema,
    summary="Upload an additional file for a project",
    status_code=201  # Indicate resource creation
)
async def add_additional_file(
    project_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),  # Using Form for description alongside File
    db: AsyncSession = Depends(get_database)
):
    """
    Upload an additional file for a project.
    
    This endpoint allows uploading supplementary files that are not part of the
    main project codebase. For example, documentation, diagrams, or notes.
    
    The file will be stored in the project's additional files directory and
    associated with the project in the database.
    """
    try:
        additional_file = await upload_service.add_additional_file_to_project(
            db=db,
            project_id=project_id,
            uploaded_file=file,
            description=description
        )
        
        return additional_file
    except (ProjectNotFoundException, FileNotFoundException):
        raise
    except Exception as e:
        logger.error("Failed to add additional file", 
                   project_id=project_id, 
                   filename=file.filename, 
                   error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add additional file: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/additional_files/{additional_file_id}",
    response_model=AdditionalProjectFileSchema,
    summary="Get a specific additional file by ID"
)
async def get_additional_file_by_id(
    project_id: int,
    additional_file_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get details of a specific additional file."""
    return await upload_service.get_additional_file(db, project_id, additional_file_id)


@router.put(
    "/projects/{project_id}/additional_files/{additional_file_id}",
    response_model=AdditionalProjectFileSchema,
    summary="Update an additional file's metadata"
)
async def update_additional_file_by_id(
    project_id: int,
    additional_file_id: int,
    update_data: AdditionalFileUpdateRequest = Body(...),  # Use the schema for request body
    db: AsyncSession = Depends(get_database)
):
    """
    Update metadata for an additional file.
    
    Currently supports updating the description.
    The file content itself cannot be updated - delete and re-upload instead.
    """
    updated_file = await upload_service.update_additional_file(
        db=db,
        project_id=project_id,
        additional_file_id=additional_file_id,
        data=update_data
    )
    
    if not updated_file:
        raise FileNotFoundException(
            file_id=additional_file_id,
            project_id=project_id
        )
    
    return updated_file


@router.delete(
    "/projects/{project_id}/additional_files/{additional_file_id}",
    summary="Delete a specific additional file",
    status_code=200  # Default is 200 for JSONResponse
)
async def delete_additional_file_by_id(
    project_id: int,
    additional_file_id: int,
    db: AsyncSession = Depends(get_database)
):
    """
    Delete an additional file from a project.
    
    This will remove both the database record and the file from storage.
    """
    deleted = await upload_service.delete_additional_file(
        db=db,
        project_id=project_id,
        additional_file_id=additional_file_id
    )
    
    if not deleted:
        raise FileNotFoundException(
            file_id=additional_file_id,
            project_id=project_id
        )
    
    return {"message": "File deleted successfully"} 