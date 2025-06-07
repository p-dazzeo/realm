from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body # Added Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
from sqlalchemy.orm import noload
from typing import Optional
import structlog
from datetime import datetime

from core.dependencies import get_database
from modules.upload.models import Project, UploadSession, ProjectFile
from modules.upload.schemas import (
    ProjectCreate, Project as ProjectSchema, UploadResponse, 
    UploadSession as UploadSessionSchema, ErrorResponse,
    ProjectSummary, UploadMethod,
    AdditionalProjectFileSchema, AdditionalFileCreateRequest, AdditionalFileUpdateRequest # Added these
)
from modules.upload.service import upload_service

logger = structlog.get_logger()
router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/project", response_model=UploadResponse)
async def upload_project(
    project_name: str = Form(...),
    project_description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_database)
):
    """
    Upload a project using intelligent method selection.
    
    This endpoint will:
    1. Try to use the parser service first (if enabled)
    2. Fallback to direct upload if parser fails or is unavailable
    
    Accepts ZIP archives or single files.
    """
    logger.info("Project upload request", name=project_name, filename=file.filename)
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create project data
        project_data = ProjectCreate(
            name=project_name,
            description=project_description
        )
        
        # Use intelligent upload service
        project, session = await upload_service.upload_project_intelligent(
            db, project_data, file
        )
        
        warnings = session.warnings if session.warnings else None
        upload_method = UploadMethod(session.upload_method)
        
        return UploadResponse(
            success=True,
            session_id=session.session_id,
            project_id=project.id,
            upload_method=upload_method,
            message=f"Project '{project.name}' uploaded successfully using {upload_method.value} method",
            warnings=warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/session/{session_id}", response_model=UploadSessionSchema)
async def get_upload_session(
    session_id: str,
    db: AsyncSession = Depends(get_database)
):
    """Get upload session status and progress"""
    result = await db.execute(
        select(UploadSession).where(UploadSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    return session


@router.get("/projects", response_model=list[ProjectSummary])
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    upload_method: Optional[UploadMethod] = None,
    db: AsyncSession = Depends(get_database)
):
    """List all projects with pagination and filtering"""
    query = (
        select(
            Project,
            func.count(ProjectFile.id).label("file_count")
        )
        .outerjoin(ProjectFile, Project.id == ProjectFile.project_id)
    )
    
    if upload_method:
        query = query.where(Project.upload_method == upload_method.value)
    
    # Apply group_by before offset, limit, and order_by that refer to Project columns
    query = query.group_by(Project.id) # Group by all necessary Project columns for DB compatibility
                                     # For most ORM cases with PostgreSQL, Project.id is enough.

    query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    projects_and_counts = result.all() # list of Row objects, (Project_instance, count_value)
    
    project_summaries = []
    for project_obj, count_val in projects_and_counts:
        summary = ProjectSummary(
            id=project_obj.id,
            uuid=project_obj.uuid,
            name=project_obj.name,
            description=project_obj.description,
            upload_method=UploadMethod(project_obj.upload_method),
            upload_status=project_obj.upload_status,
            file_count=count_val, # Use the aggregated count
            total_size=project_obj.file_size or 0,
            created_at=project_obj.created_at
        )
        project_summaries.append(summary)
    
    return project_summaries


@router.get("/projects/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    include_files: bool = True,
    db: AsyncSession = Depends(get_database)
):
    """Get a specific project with optional file content"""
    query = select(Project).where(Project.id == project_id)

    if not include_files:
        query = query.options(noload(Project.files))
    
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Delete a project and all its files"""
    # First delete any upload sessions that reference this project
    await db.execute(
        delete(UploadSession).where(UploadSession.project_id == project_id)
    )
    
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    
    logger.info("Project deleted", project_id=project_id, name=project.name)
    
    return {"message": f"Project '{project.name}' deleted successfully"}


@router.post("/test-parser")
async def test_parser_service():
    """Test if the parser service is available and responsive"""
    try:
        response = await upload_service.http_client.get(
            f"{upload_service.http_client.base_url}/health"
        )
        
        if response.status_code == 200:
            return {
                "parser_available": True,
                "parser_url": upload_service.http_client.base_url,
                "status": "healthy"
            }
        else:
            return {
                "parser_available": False,
                "parser_url": upload_service.http_client.base_url,
                "status": f"unhealthy (status: {response.status_code})"
            }
            
    except Exception as e:
        return {
            "parser_available": False,
            "parser_url": upload_service.http_client.base_url,
            "status": f"error: {str(e)}"
        }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "realm-upload-service",
        "timestamp": datetime.now().strftime("%d/%m/%YT/%H:%M:%S")
    }

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# AdditionalProjectFile specific endpoints
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@router.post(
    "/projects/{project_id}/additional_files",
    response_model=AdditionalProjectFileSchema,
    summary="Upload an additional file for a project",
    status_code=201 # Indicate resource creation
)
async def add_additional_file(
    project_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None), # Using Form for description alongside File
    db: AsyncSession = Depends(get_database)
):
    # The service function add_additional_file_to_project
    # was designed to take `description` directly.
    try:
        # Ensure project exists before proceeding (optional, service might do this)
        # project = await upload_service.get_project_by_id(db, project_id) # Assuming such service method exists
        # if not project:
        #     raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found.")

        additional_file_record = await upload_service.add_additional_file_to_project(
            db=db,
            project_id=project_id,
            uploaded_file=file,
            description=description
        )
        return additional_file_record
    except HTTPException as e: # Catch HTTPExceptions from service (like project not found)
        raise e
    except Exception as e:
        logger.error("Failed to add additional file", project_id=project_id, filename=file.filename, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add additional file: {str(e)}")

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
    additional_file = await upload_service.get_additional_file(db, project_id, additional_file_id)
    if not additional_file:
        raise HTTPException(status_code=404, detail="Additional file not found for this project")
    return additional_file

@router.put(
    "/projects/{project_id}/additional_files/{additional_file_id}",
    response_model=AdditionalProjectFileSchema,
    summary="Update an additional file's metadata"
)
async def update_additional_file_by_id(
    project_id: int,
    additional_file_id: int,
    update_data: AdditionalFileUpdateRequest = Body(...), # Use the schema for request body
    db: AsyncSession = Depends(get_database)
):
    try:
        updated_file = await upload_service.update_additional_file(
            db, project_id, additional_file_id, update_data
        )
        if not updated_file:
            # Service returns None if not found, router translates to 404
            raise HTTPException(status_code=404, detail="Additional file not found or no update performed")
        return updated_file
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to update additional file", project_id=project_id, additional_file_id=additional_file_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update additional file: {str(e)}")


@router.delete(
    "/projects/{project_id}/additional_files/{additional_file_id}",
    summary="Delete a specific additional file",
    status_code=200 # Default is 200 for JSONResponse
)
async def delete_additional_file_by_id(
    project_id: int,
    additional_file_id: int,
    db: AsyncSession = Depends(get_database)
):
    try:
        success = await upload_service.delete_additional_file(db, project_id, additional_file_id)
        if not success:
            # Service returns False if not found, router translates to 404
            raise HTTPException(status_code=404, detail="Additional file not found or deletion failed")
        # If service raised an error for file system issues, it would be caught by generic exception handler
        return JSONResponse(content={"message": "Additional file deleted successfully"}, status_code=200)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to delete additional file", project_id=project_id, additional_file_id=additional_file_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete additional file: {str(e)}")