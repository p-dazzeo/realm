"""
Project-related endpoints for the upload module.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
from sqlalchemy.orm import noload, selectinload
from typing import Optional
import structlog
from datetime import datetime

from core.dependencies import get_database
from modules.upload.models import Project, UploadSession, ProjectFile
from modules.upload.repositories import ProjectRepository
from modules.upload.schemas import (
    ProjectCreate, Project as ProjectSchema, UploadResponse,
    UploadSession as UploadSessionSchema, ErrorResponse,
    ProjectSummary, UploadMethod
)
from modules.upload.service import upload_service
from shared.exceptions import ProjectNotFoundException

logger = structlog.get_logger()
router = APIRouter()


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
    use_cache: bool = True,
    db: AsyncSession = Depends(get_database)
):
    """
    List all projects with pagination and filtering.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        upload_method: Filter by upload method
        use_cache: Whether to use cached results (default: True)
        db: Database session
    """
    if upload_method or not use_cache:
        # If filtering or cache is disabled, use the non-cached implementation
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
                file_count=count_val,
                total_size=project_obj.file_size or 0,
                created_at=project_obj.created_at
            )
            project_summaries.append(summary)
        
        return project_summaries
    else:
        # Use cached repository method for better performance
        logger.info("Using cached project list", skip=skip, limit=limit)
        projects = await ProjectRepository.list_projects_cached(db, skip=skip, limit=limit)
        
        # Convert to summaries - this is lightweight and doesn't need caching
        project_summaries = []
        for project in projects:
            file_count = len(project.files) if project.files else 0
            summary = ProjectSummary(
                id=project.id,
                uuid=project.uuid,
                name=project.name,
                description=project.description,
                upload_method=UploadMethod(project.upload_method),
                upload_status=project.upload_status,
                file_count=file_count,
                total_size=project.file_size or 0,
                created_at=project.created_at
            )
            project_summaries.append(summary)
        
        return project_summaries


@router.get("/projects/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    include_files: bool = True,
    use_cache: bool = True,
    db: AsyncSession = Depends(get_database)
):
    """
    Get a specific project with optional file content.
    
    Args:
        project_id: ID of the project to retrieve
        include_files: Whether to include file and additional_file relationships
        use_cache: Whether to use cached results (default: True)
        db: Database session
    """
    project = None
    
    if use_cache and include_files:
        # Use cached version for read-only operations with full relationships
        logger.info("Using cached project retrieval", project_id=project_id)
        project = await ProjectRepository.get_by_id_cached(db, project_id)
    elif include_files:
        # Use standard version with relationships
        project = await ProjectRepository.get_by_id(db, project_id)
    else:
        # Use specific relation loading method
        project = await ProjectRepository.get_by_id_with_relations(
            db, project_id, 
            load_files=include_files, 
            load_additional_files=include_files
        )
    
    if not project:
        raise ProjectNotFoundException(project_id=project_id)
    
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
        raise ProjectNotFoundException(project_id=project_id)
    
    await db.delete(project)
    await db.commit()
    
    logger.info("Project deleted", project_id=project_id, name=project.name)
    
    return {"message": f"Project '{project.name}' deleted successfully"} 