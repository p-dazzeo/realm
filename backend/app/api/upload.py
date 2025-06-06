from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import structlog
from datetime import datetime

from app.database import get_db
from app.models import Project, UploadSession
from app.schemas import (
    ProjectCreate, Project as ProjectSchema, UploadResponse, 
    UploadSession as UploadSessionSchema, ErrorResponse,
    ProjectSummary, UploadMethod
)
from app.services.upload_service import upload_service

logger = structlog.get_logger()
router = APIRouter(prefix="/upload", tags=["upload"])


from typing import Optional, List # Ensure List is imported

@router.post("/project", response_model=UploadResponse)
async def upload_project(
    project_name: str = Form(...),
    description: Optional[str] = Form(None), # Renamed from project_description
    project_archive_file: Optional[UploadFile] = File(None), # Main project archive (e.g. zip)
    additional_files: List[UploadFile] = File([]), # For other individual files
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a project using intelligent method selection.
    
    This endpoint will:
    1. Try to use the parser service first (if enabled)
    2. Fallback to direct upload if parser fails or is unavailable
    
    Accepts ZIP archives or single files, and/or additional loose files.
    """
    # Log main file if present, or number of additional files
    main_file_info = project_archive_file.filename if project_archive_file and project_archive_file.filename else "No main archive"
    additional_files_info = f"{len(additional_files)} additional files"
    logger.info("Project upload request", name=project_name, main_file=main_file_info, additional_files_count=len(additional_files))
    
    try:
        # Validate file inputs: at least one type of file input should be provided
        if not project_archive_file and not additional_files:
            raise HTTPException(status_code=400, detail="No project archive or additional files provided.")
        if project_archive_file and not project_archive_file.filename: # Handles case where File(None) still results in an UploadFile with no filename
             project_archive_file = None # Treat as if no file was sent
        if not project_archive_file and not additional_files: # Re-check after potential nullification
             raise HTTPException(status_code=400, detail="No project archive or additional files provided.")

        # Create project data
        project_data = ProjectCreate(
            name=project_name,
            description=description # Use the new 'description' field name
        )
        
        # This call will need to be adapted in the service layer.
        # Assuming upload_project_intelligent is the correct entry point and will handle these.
        # Or, this might need to call create_project_with_upload directly if logic dictates.
        # For now, passing them to upload_project_intelligent as a placeholder for service layer changes.
        project, session = await upload_service.upload_project_intelligent(
            db=db,
            project_data=project_data,
            main_file=project_archive_file, # Pass the main archive file
            additional_files=additional_files # Pass the list of additional files
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
):
    """List all projects with pagination and filtering"""
    query = select(Project)
    
    if upload_method:
        query = query.where(Project.upload_method == upload_method.value)
    
    query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # Transform to ProjectSummary with file counts
    project_summaries = []
    for project in projects:
        # Count files for this project
        file_count_result = await db.execute(
            select(len(project.files))
        )
        
        summary = ProjectSummary(
            id=project.id,
            uuid=project.uuid,
            name=project.name,
            description=project.description,
            upload_method=UploadMethod(project.upload_method),
            upload_status=project.upload_status,
            file_count=len(project.files),
            total_size=project.file_size or 0,
            created_at=project.created_at
        )
        project_summaries.append(summary)
    
    return project_summaries


@router.get("/projects/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    include_files: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project with optional file content"""
    query = select(Project).where(Project.id == project_id)
    
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If files are not requested, load project without files
    if not include_files:
        # Clear the files relationship to avoid loading
        project.files = []
    
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and all its files"""
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