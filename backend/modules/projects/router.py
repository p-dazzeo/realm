from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging

from core.dependencies import get_database
from modules.projects.service import projects_service
from modules.projects.models import ProjectTemplate
from modules.projects.schemas import (
    # Template schemas
    ProjectTemplate, ProjectTemplateCreate, ProjectTemplateUpdate, ProjectTemplateList,
    ProjectTemplateCategory,
    
    # Collaborator schemas
    ProjectCollaborator, ProjectCollaboratorCreate, ProjectCollaboratorUpdate,
    ProjectCollaboratorInvite, CollaboratorRole, InvitationStatus,
    
    # Settings schemas
    ProjectSettings, ProjectSettingsCreate, ProjectSettingsUpdate,
    
    # Tag schemas
    ProjectTag, ProjectTagCreate, ProjectTagUpdate,
    
    # Version schemas
    ProjectVersion, ProjectVersionCreate, ProjectVersionUpdate, ProjectVersionList,
    
    # Enhanced project schemas
    EnhancedProject, EnhancedProjectCreate, EnhancedProjectUpdate, EnhancedProjectList,
    
    # Analytics schemas
    ProjectAnalytics, ProjectAnalyticsUpdate,
    
    # Search and export schemas
    ProjectSearchFilter, ProjectSearchResult, ProjectExportRequest, ProjectExportResponse,
    
    # Response schemas
    ProjectOperationResponse, BulkOperationResponse,
    
    # Enums
    ExportFormat
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


# Template Endpoints
@router.post("/templates", response_model=ProjectTemplate, status_code=status.HTTP_201_CREATED)
async def create_project_template(
    template_data: ProjectTemplateCreate,
    db: AsyncSession = Depends(get_database),
    created_by: Optional[str] = Query(None, description="User ID creating the template")
):
    """Create a new project template."""
    try:
        template = await projects_service.create_template(db, template_data, created_by)
        return template
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[ProjectTemplateList])
async def get_project_templates(
    category: Optional[ProjectTemplateCategory] = Query(None, description="Filter by category"),
    is_public: bool = Query(True, description="Filter by public templates"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    limit: int = Query(50, ge=1, le=100, description="Number of templates to return"),
    offset: int = Query(0, ge=0, description="Number of templates to skip"),
    db: AsyncSession = Depends(get_database)
):
    """Get project templates with filtering options."""
    try:
        templates = await projects_service.get_templates(
            db, category=category, is_public=is_public, search=search, limit=limit, offset=offset
        )
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=ProjectTemplate)
async def get_project_template(
    template_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get a specific project template by ID."""
    try:
        template = await projects_service.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/use", response_model=ProjectTemplate)
async def use_project_template(
    template_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Increment template usage count."""
    try:
        template = await projects_service.use_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error using template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Project Endpoints
@router.post("/", response_model=EnhancedProject, status_code=status.HTTP_201_CREATED)
async def create_enhanced_project(
    project_data: EnhancedProjectCreate,
    db: AsyncSession = Depends(get_database),
    created_by: Optional[str] = Query(None, description="User ID creating the project")
):
    """Create an enhanced project with optional template and settings."""
    try:
        project = await projects_service.create_enhanced_project(db, project_data, created_by)
        return project
    except Exception as e:
        logger.error(f"Error creating enhanced project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ProjectSearchResult)
async def search_projects(
    # Search parameters
    query: Optional[str] = Query(None, description="Search in name and description"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_public: Optional[bool] = Query(None, description="Filter by public projects"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived projects"),
    has_collaborators: Optional[bool] = Query(None, description="Filter projects with collaborators"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Dependencies
    db: AsyncSession = Depends(get_database),
    user_id: Optional[str] = Query(None, description="Current user ID for access tracking")
):
    """Advanced project search with filtering and pagination."""
    try:
        filters = ProjectSearchFilter(
            query=query,
            tags=tags,
            category=category,
            status=status,
            is_public=is_public,
            is_archived=is_archived,
            has_collaborators=has_collaborators,
            language=language
        )
        
        projects, total = await projects_service.search_projects(
            db, filters, user_id, page, per_page
        )
        
        pages = (total + per_page - 1) // per_page
        
        return ProjectSearchResult(
            projects=projects,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error searching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=EnhancedProject)
async def get_enhanced_project(
    project_id: int,
    db: AsyncSession = Depends(get_database),
    user_id: Optional[str] = Query(None, description="Current user ID for access tracking")
):
    """Get enhanced project with all relationships."""
    try:
        project = await projects_service.get_enhanced_project(db, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching enhanced project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=EnhancedProject)
async def update_enhanced_project(
    project_id: int,
    project_data: EnhancedProjectUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update enhanced project."""
    try:
        # This would need to be implemented in the service
        # For now, just get the project
        project = await projects_service.get_enhanced_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update basic fields
        if project_data.name:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        
        await db.commit()
        await db.refresh(project)
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating enhanced project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Collaboration Endpoints
@router.post("/{project_id}/collaborators", response_model=ProjectCollaborator, status_code=status.HTTP_201_CREATED)
async def add_project_collaborator(
    project_id: int,
    collaborator_data: ProjectCollaboratorCreate,
    db: AsyncSession = Depends(get_database),
    invited_by: str = Query(..., description="User ID sending the invitation")
):
    """Add a collaborator to a project."""
    try:
        collaborator = await projects_service.add_collaborator(db, project_id, collaborator_data, invited_by)
        return collaborator
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding collaborator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/collaborators", response_model=List[ProjectCollaborator])
async def get_project_collaborators(
    project_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get all collaborators for a project."""
    try:
        # This would need to be implemented in the service
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error fetching collaborators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/collaborators/{collaborator_id}", response_model=ProjectCollaborator)
async def update_project_collaborator(
    collaborator_id: int,
    update_data: ProjectCollaboratorUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update collaborator role and permissions."""
    try:
        collaborator = await projects_service.update_collaborator(db, collaborator_id, update_data)
        if not collaborator:
            raise HTTPException(status_code=404, detail="Collaborator not found")
        return collaborator
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collaborator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/collaborators/{user_id}", response_model=ProjectOperationResponse)
async def remove_project_collaborator(
    project_id: int,
    user_id: str,
    db: AsyncSession = Depends(get_database)
):
    """Remove a collaborator from a project."""
    try:
        success = await projects_service.remove_collaborator(db, project_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Collaborator not found")
        
        return ProjectOperationResponse(
            success=True,
            message="Collaborator removed successfully",
            project_id=project_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing collaborator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Settings Endpoints
@router.get("/{project_id}/settings", response_model=ProjectSettings)
async def get_project_settings(
    project_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get project settings."""
    try:
        # This would need to be implemented in the service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        logger.error(f"Error fetching project settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}/settings", response_model=ProjectSettings)
async def update_project_settings(
    project_id: int,
    settings_data: ProjectSettingsUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update project settings."""
    try:
        settings = await projects_service.update_project_settings(db, project_id, settings_data)
        if not settings:
            raise HTTPException(status_code=404, detail="Project not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Tags Endpoints
@router.get("/tags/popular", response_model=List[ProjectTag])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="Number of tags to return"),
    db: AsyncSession = Depends(get_database)
):
    """Get most popular project tags."""
    try:
        tags = await projects_service.get_popular_tags(db, limit)
        return tags
    except Exception as e:
        logger.error(f"Error fetching popular tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints
@router.get("/{project_id}/analytics", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get project analytics and usage statistics."""
    try:
        analytics = await projects_service.get_project_analytics(db, project_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Project analytics not found")
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Version Management Endpoints
@router.post("/{project_id}/versions", response_model=ProjectVersion, status_code=status.HTTP_201_CREATED)
async def create_project_version(
    project_id: int,
    version_data: ProjectVersionCreate,
    db: AsyncSession = Depends(get_database),
    created_by: str = Query(..., description="User ID creating the version")
):
    """Create a new project version/snapshot."""
    try:
        version = await projects_service.create_project_version(db, project_id, version_data, created_by)
        return version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/versions", response_model=List[ProjectVersionList])
async def get_project_versions(
    project_id: int,
    limit: int = Query(50, ge=1, le=100, description="Number of versions to return"),
    offset: int = Query(0, ge=0, description="Number of versions to skip"),
    db: AsyncSession = Depends(get_database)
):
    """Get project versions/snapshots."""
    try:
        # This would need to be implemented in the service
        return []
    except Exception as e:
        logger.error(f"Error fetching project versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Export Endpoints
@router.post("/{project_id}/export", response_model=ProjectExportResponse)
async def export_project(
    project_id: int,
    export_request: ProjectExportRequest,
    db: AsyncSession = Depends(get_database),
    user_id: str = Query(..., description="User ID requesting the export")
):
    """Export project in specified format."""
    try:
        result = await projects_service.export_project(db, project_id, export_request, user_id)
        
        return ProjectExportResponse(
            success=result["success"],
            export_id=result["export_id"],
            format=result["format"],
            message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health Check
@router.get("/health", response_model=Dict[str, str])
async def projects_health_check():
    """Health check for projects module."""
    return {"status": "healthy", "module": "projects"} 