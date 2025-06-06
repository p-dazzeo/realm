from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import text
import uuid
import json
import logging
from datetime import datetime, timedelta

from core.config import core_settings
from modules.upload.models import Project, ProjectFile
from modules.projects.models import (
    ProjectTemplate, ProjectCollaborator, ProjectSettings, ProjectTag,
    ProjectTagAssociation, ProjectVersion, ProjectAnalytics
)
from modules.projects.schemas import (
    ProjectTemplateCreate, ProjectTemplateUpdate,
    ProjectCollaboratorCreate, ProjectCollaboratorUpdate,
    ProjectSettingsCreate, ProjectSettingsUpdate,
    ProjectTagCreate, ProjectTagUpdate,
    ProjectVersionCreate, ProjectVersionUpdate,
    EnhancedProjectCreate, EnhancedProjectUpdate,
    ProjectSearchFilter, ProjectExportRequest,
    CollaboratorRole, InvitationStatus, ExportFormat
)

logger = logging.getLogger(__name__)


class ProjectsService:
    """Enhanced project management service with collaboration and templates."""
    
    def __init__(self):
        self.logger = logger
    
    # Project Template Operations
    async def create_template(
        self, 
        db: AsyncSession, 
        template_data: ProjectTemplateCreate,
        created_by: Optional[str] = None
    ) -> ProjectTemplate:
        """Create a new project template."""
        try:
            template = ProjectTemplate(
                name=template_data.name,
                description=template_data.description,
                category=template_data.category,
                template_data=template_data.template_data,
                default_settings=template_data.default_settings,
                required_dependencies=template_data.required_dependencies,
                version=template_data.version,
                author=template_data.author or created_by,
                license=template_data.license,
                tags=template_data.tags,
                is_public=template_data.is_public
            )
            
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            self.logger.info(f"Created project template: {template.name} (ID: {template.id})")
            return template
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating template: {str(e)}")
            raise
    
    async def get_templates(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        is_public: bool = True,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProjectTemplate]:
        """Get project templates with filtering."""
        try:
            query = select(ProjectTemplate).where(
                ProjectTemplate.is_active == True
            )
            
            if is_public:
                query = query.where(ProjectTemplate.is_public == True)
            
            if category:
                query = query.where(ProjectTemplate.category == category)
            
            if search:
                search_filter = f"%{search}%"
                query = query.where(
                    or_(
                        ProjectTemplate.name.ilike(search_filter),
                        ProjectTemplate.description.ilike(search_filter)
                    )
                )
            
            query = query.order_by(desc(ProjectTemplate.usage_count)).limit(limit).offset(offset)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            self.logger.error(f"Error fetching templates: {str(e)}")
            raise
    
    async def use_template(self, db: AsyncSession, template_id: int) -> ProjectTemplate:
        """Increment template usage count."""
        try:
            template = await db.get(ProjectTemplate, template_id)
            if template:
                template.usage_count += 1
                await db.commit()
            return template
        except Exception as e:
            self.logger.error(f"Error updating template usage: {str(e)}")
            raise
    
    # Enhanced Project Operations
    async def create_enhanced_project(
        self,
        db: AsyncSession,
        project_data: EnhancedProjectCreate,
        created_by: Optional[str] = None
    ) -> Project:
        """Create an enhanced project with optional template and settings."""
        try:
            # Start with basic project creation
            project = Project(
                name=project_data.name,
                description=project_data.description,
                upload_method="direct",  # Default method
                upload_status="pending"
            )
            
            db.add(project)
            await db.flush()  # Get the project ID
            
            # Apply template if specified
            if project_data.template_id:
                template = await db.get(ProjectTemplate, project_data.template_id)
                if template:
                    # Apply template settings
                    if template.default_settings and project_data.settings:
                        # Merge template settings with provided settings
                        merged_settings = {**template.default_settings, **project_data.settings.dict(exclude_unset=True)}
                        project_data.settings = ProjectSettingsCreate(**merged_settings)
                    elif template.default_settings:
                        project_data.settings = ProjectSettingsCreate(**template.default_settings)
                    
                    # Increment template usage
                    template.usage_count += 1
            
            # Create project settings
            if project_data.settings:
                settings = ProjectSettings(
                    project_id=project.id,
                    **project_data.settings.dict()
                )
                db.add(settings)
            
            # Add collaborators
            if project_data.collaborators:
                for collab_data in project_data.collaborators:
                    collaborator = ProjectCollaborator(
                        project_id=project.id,
                        user_id=collab_data.user_id,
                        role=collab_data.role,
                        permissions=collab_data.permissions,
                        invited_by=created_by,
                        invitation_status=InvitationStatus.ACTIVE
                    )
                    db.add(collaborator)
            
            # Add tags
            if project_data.tags:
                for tag_name in project_data.tags:
                    tag = await self._get_or_create_tag(db, tag_name)
                    association = ProjectTagAssociation(
                        project_id=project.id,
                        tag_id=tag.id,
                        added_by=created_by
                    )
                    db.add(association)
            
            # Create analytics record
            analytics = ProjectAnalytics(project_id=project.id)
            db.add(analytics)
            
            await db.commit()
            await db.refresh(project)
            
            self.logger.info(f"Created enhanced project: {project.name} (ID: {project.id})")
            return project
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating enhanced project: {str(e)}")
            raise
    
    async def get_enhanced_project(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: Optional[str] = None
    ) -> Optional[Project]:
        """Get enhanced project with all relationships."""
        try:
            query = select(Project).options(
                joinedload(Project.files),
                # Note: These relationships would need to be added to the Project model
                # selectinload(Project.settings),
                # selectinload(Project.collaborators),
                # selectinload(Project.tags),
                # selectinload(Project.analytics)
            ).where(Project.id == project_id)
            
            result = await db.execute(query)
            project = result.unique().scalar_one_or_none()
            
            if project and user_id:
                # Update analytics
                await self._update_project_access(db, project_id, user_id)
            
            return project
            
        except Exception as e:
            self.logger.error(f"Error fetching enhanced project: {str(e)}")
            raise
    
    async def search_projects(
        self,
        db: AsyncSession,
        filters: ProjectSearchFilter,
        user_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Project], int]:
        """Advanced project search with filtering."""
        try:
            query = select(Project)
            count_query = select(func.count(Project.id))
            
            # Apply filters
            conditions = []
            
            if filters.query:
                search_filter = f"%{filters.query}%"
                conditions.append(
                    or_(
                        Project.name.ilike(search_filter),
                        Project.description.ilike(search_filter)
                    )
                )
            
            if filters.tags:
                # Join with tags (would need proper relationship setup)
                tag_conditions = []
                for tag in filters.tags:
                    tag_conditions.append(ProjectTag.name.in_(filters.tags))
                if tag_conditions:
                    conditions.append(or_(*tag_conditions))
            
            if filters.is_public is not None:
                # Would need to join with settings
                pass
            
            if filters.is_archived is not None:
                # Would need to join with settings
                pass
            
            if filters.created_after:
                conditions.append(Project.created_at >= filters.created_after)
            
            if filters.created_before:
                conditions.append(Project.created_at <= filters.created_before)
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
            
            # Get total count
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * per_page
            query = query.order_by(desc(Project.created_at)).limit(per_page).offset(offset)
            
            result = await db.execute(query)
            projects = result.scalars().all()
            
            return projects, total
            
        except Exception as e:
            self.logger.error(f"Error searching projects: {str(e)}")
            raise
    
    # Collaboration Operations
    async def add_collaborator(
        self,
        db: AsyncSession,
        project_id: int,
        collaborator_data: ProjectCollaboratorCreate,
        invited_by: str
    ) -> ProjectCollaborator:
        """Add a collaborator to a project."""
        try:
            # Check if collaborator already exists
            existing = await db.execute(
                select(ProjectCollaborator).where(
                    and_(
                        ProjectCollaborator.project_id == project_id,
                        ProjectCollaborator.user_id == collaborator_data.user_id
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                raise ValueError("User is already a collaborator on this project")
            
            collaborator = ProjectCollaborator(
                project_id=project_id,
                user_id=collaborator_data.user_id,
                role=collaborator_data.role,
                permissions=collaborator_data.permissions,
                invited_by=invited_by,
                invitation_status=InvitationStatus.PENDING
            )
            
            db.add(collaborator)
            await db.commit()
            await db.refresh(collaborator)
            
            self.logger.info(f"Added collaborator {collaborator_data.user_id} to project {project_id}")
            return collaborator
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error adding collaborator: {str(e)}")
            raise
    
    async def update_collaborator(
        self,
        db: AsyncSession,
        collaborator_id: int,
        update_data: ProjectCollaboratorUpdate
    ) -> Optional[ProjectCollaborator]:
        """Update collaborator role and permissions."""
        try:
            collaborator = await db.get(ProjectCollaborator, collaborator_id)
            if not collaborator:
                return None
            
            if update_data.role:
                collaborator.role = update_data.role
            
            if update_data.permissions:
                collaborator.permissions = update_data.permissions
            
            if update_data.invitation_status:
                collaborator.invitation_status = update_data.invitation_status
                if update_data.invitation_status == InvitationStatus.ACTIVE:
                    collaborator.accepted_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(collaborator)
            
            return collaborator
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error updating collaborator: {str(e)}")
            raise
    
    async def remove_collaborator(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: str
    ) -> bool:
        """Remove a collaborator from a project."""
        try:
            result = await db.execute(
                select(ProjectCollaborator).where(
                    and_(
                        ProjectCollaborator.project_id == project_id,
                        ProjectCollaborator.user_id == user_id
                    )
                )
            )
            
            collaborator = result.scalar_one_or_none()
            if collaborator:
                await db.delete(collaborator)
                await db.commit()
                return True
            
            return False
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error removing collaborator: {str(e)}")
            raise
    
    # Project Settings Operations
    async def update_project_settings(
        self,
        db: AsyncSession,
        project_id: int,
        settings_data: ProjectSettingsUpdate
    ) -> Optional[ProjectSettings]:
        """Update project settings."""
        try:
            # Get or create settings
            result = await db.execute(
                select(ProjectSettings).where(ProjectSettings.project_id == project_id)
            )
            settings = result.scalar_one_or_none()
            
            if not settings:
                settings = ProjectSettings(project_id=project_id)
                db.add(settings)
            
            # Update fields
            for field, value in settings_data.dict(exclude_unset=True).items():
                setattr(settings, field, value)
            
            await db.commit()
            await db.refresh(settings)
            
            return settings
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error updating project settings: {str(e)}")
            raise
    
    # Tag Operations
    async def _get_or_create_tag(self, db: AsyncSession, tag_name: str) -> ProjectTag:
        """Get existing tag or create new one."""
        result = await db.execute(
            select(ProjectTag).where(ProjectTag.name == tag_name)
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            tag = ProjectTag(name=tag_name)
            db.add(tag)
            await db.flush()
        else:
            tag.usage_count += 1
        
        return tag
    
    async def get_popular_tags(self, db: AsyncSession, limit: int = 20) -> List[ProjectTag]:
        """Get most popular tags."""
        try:
            query = select(ProjectTag).order_by(desc(ProjectTag.usage_count)).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Error fetching popular tags: {str(e)}")
            raise
    
    # Analytics Operations
    async def _update_project_access(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: str
    ) -> None:
        """Update project access analytics."""
        try:
            # Update project analytics
            result = await db.execute(
                select(ProjectAnalytics).where(ProjectAnalytics.project_id == project_id)
            )
            analytics = result.scalar_one_or_none()
            
            if analytics:
                analytics.view_count += 1
                analytics.last_accessed = datetime.utcnow()
            
            # Update collaborator access if applicable
            collab_result = await db.execute(
                select(ProjectCollaborator).where(
                    and_(
                        ProjectCollaborator.project_id == project_id,
                        ProjectCollaborator.user_id == user_id
                    )
                )
            )
            collaborator = collab_result.scalar_one_or_none()
            
            if collaborator:
                collaborator.access_count += 1
                collaborator.last_accessed = datetime.utcnow()
            
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating project access: {str(e)}")
            # Don't raise - analytics failures shouldn't break the main flow
    
    async def get_project_analytics(
        self,
        db: AsyncSession,
        project_id: int
    ) -> Optional[ProjectAnalytics]:
        """Get project analytics."""
        try:
            result = await db.execute(
                select(ProjectAnalytics).where(ProjectAnalytics.project_id == project_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error fetching project analytics: {str(e)}")
            raise
    
    # Version Management
    async def create_project_version(
        self,
        db: AsyncSession,
        project_id: int,
        version_data: ProjectVersionCreate,
        created_by: str
    ) -> ProjectVersion:
        """Create a new project version/snapshot."""
        try:
            # Get current project state
            project = await self.get_enhanced_project(db, project_id)
            if not project:
                raise ValueError("Project not found")
            
            # Create snapshot data
            snapshot_data = {
                "project": {
                    "name": project.name,
                    "description": project.description,
                    "upload_method": project.upload_method,
                    "upload_status": project.upload_status
                },
                "files": [
                    {
                        "filename": f.filename,
                        "file_path": f.file_path,
                        "relative_path": f.relative_path,
                        "content_hash": f.content_hash,
                        "language": f.language,
                        "loc": f.loc
                    }
                    for f in project.files
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            version = ProjectVersion(
                project_id=project_id,
                version_number=version_data.version_number,
                version_name=version_data.version_name,
                description=version_data.description,
                commit_message=version_data.commit_message,
                is_major=version_data.is_major,
                is_release=version_data.is_release,
                created_by=created_by,
                snapshot_data=snapshot_data,
                file_count=len(project.files),
                total_size=sum(f.file_size or 0 for f in project.files)
            )
            
            db.add(version)
            await db.commit()
            await db.refresh(version)
            
            self.logger.info(f"Created project version {version_data.version_number} for project {project_id}")
            return version
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating project version: {str(e)}")
            raise
    
    # Export Operations
    async def export_project(
        self,
        db: AsyncSession,
        project_id: int,
        export_request: ProjectExportRequest,
        user_id: str
    ) -> Dict[str, Any]:
        """Export project in specified format."""
        try:
            project = await self.get_enhanced_project(db, project_id, user_id)
            if not project:
                raise ValueError("Project not found")
            
            export_id = str(uuid.uuid4())
            
            # Build export data based on format and settings
            export_data = {
                "project": {
                    "id": project.id,
                    "uuid": project.uuid,
                    "name": project.name,
                    "description": project.description,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None
                }
            }
            
            if export_request.include_files:
                export_data["files"] = [
                    {
                        "filename": f.filename,
                        "relative_path": f.relative_path,
                        "content": f.content if export_request.format != ExportFormat.ZIP else None,
                        "language": f.language,
                        "loc": f.loc
                    }
                    for f in project.files
                ]
            
            if export_request.include_metadata:
                export_data["metadata"] = {
                    "upload_method": project.upload_method,
                    "upload_status": project.upload_status,
                    "original_filename": project.original_filename,
                    "file_size": project.file_size
                }
            
            # Update analytics
            await self._update_export_analytics(db, project_id)
            
            # In a real implementation, you would:
            # 1. Generate the actual export file based on format
            # 2. Store it in cloud storage
            # 3. Return a download URL
            
            return {
                "success": True,
                "export_id": export_id,
                "format": export_request.format,
                "message": f"Export created successfully",
                "data": export_data  # For now, return data directly
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting project: {str(e)}")
            raise
    
    async def _update_export_analytics(self, db: AsyncSession, project_id: int) -> None:
        """Update export analytics."""
        try:
            result = await db.execute(
                select(ProjectAnalytics).where(ProjectAnalytics.project_id == project_id)
            )
            analytics = result.scalar_one_or_none()
            
            if analytics:
                analytics.exports_count += 1
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating export analytics: {str(e)}")


# Global service instance
projects_service = ProjectsService() 