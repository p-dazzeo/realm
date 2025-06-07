"""
Database repositories for the upload module.
Repositories handle database operations and queries.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from sqlalchemy.orm import selectinload

from modules.upload.models import Project, ProjectFile, UploadSession, AdditionalProjectFile
from modules.upload.schemas import UploadStatus
from shared.exceptions import DatabaseException, ProjectNotFoundException, FileNotFoundException

logger = structlog.get_logger()


class ProjectRepository:
    """Repository for Project entity database operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        try:
            result = await db.execute(
                select(Project)
                .where(Project.id == project_id)
                .options(
                    selectinload(Project.files),
                    selectinload(Project.additional_files)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting project by ID", 
                       project_id=project_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving project with id {project_id}",
                operation="get_by_id",
                entity="Project"
            )
    
    @staticmethod
    async def get_by_id_with_relations(
        db: AsyncSession, 
        project_id: int,
        load_files: bool = True,
        load_additional_files: bool = True
    ) -> Optional[Project]:
        """
        Get a project by ID with explicit control over which relationships to load.
        
        Args:
            db: Database session
            project_id: ID of the project to retrieve
            load_files: Whether to load the files relationship
            load_additional_files: Whether to load the additional_files relationship
            
        Returns:
            Project object if found, None otherwise
        """
        try:
            query = select(Project).where(Project.id == project_id)
            
            if load_files:
                query = query.options(selectinload(Project.files))
            if load_additional_files:
                query = query.options(selectinload(Project.additional_files))
                
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting project by ID with relations", 
                       project_id=project_id,
                       load_files=load_files,
                       load_additional_files=load_additional_files,
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving project with id {project_id}",
                operation="get_by_id_with_relations",
                entity="Project"
            )
    
    @staticmethod
    async def get_by_uuid(db: AsyncSession, uuid: str) -> Optional[Project]:
        """Get a project by UUID."""
        try:
            result = await db.execute(
                select(Project)
                .where(Project.uuid == uuid)
                .options(
                    selectinload(Project.files),
                    selectinload(Project.additional_files)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting project by UUID", 
                       uuid=uuid, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving project with uuid {uuid}",
                operation="get_by_uuid",
                entity_type="Project",
                entity_id=uuid,
                original_error=e
            )
    
    @staticmethod
    async def list_projects(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects with pagination."""
        try:
            result = await db.execute(select(Project).offset(skip).limit(limit))
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database error while listing projects", 
                       skip=skip, 
                       limit=limit, 
                       error=str(e))
            raise DatabaseException(
                detail="Error listing projects",
                operation="list_projects",
                entity_type="Project",
                original_error=e
            )
    
    @staticmethod
    async def create(db: AsyncSession, project_data: Dict[str, Any]) -> Project:
        """Create a new project."""
        try:
            project = Project(**project_data)
            db.add(project)
            await db.commit()
            await db.refresh(project)
            return project
        except Exception as e:
            await db.rollback()
            logger.error("Database error while creating project", 
                       project_data=project_data, 
                       error=str(e))
            raise DatabaseException(
                detail="Error creating project",
                operation="create",
                entity_type="Project",
                original_error=e
            )
    
    @staticmethod
    async def update(db: AsyncSession, project: Project) -> Project:
        """Update an existing project."""
        try:
            await db.commit()
            await db.refresh(project)
            return project
        except Exception as e:
            await db.rollback()
            logger.error("Database error while updating project", 
                       project_id=project.id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error updating project with id {project.id}",
                operation="update",
                entity_type="Project",
                entity_id=project.id,
                original_error=e
            )
    
    @staticmethod
    async def delete(db: AsyncSession, project_id: int) -> bool:
        """Delete a project by ID."""
        try:
            result = await db.execute(delete(Project).where(Project.id == project_id))
            await db.commit()
            if result.rowcount == 0:
                logger.warning("No project found to delete", project_id=project_id)
                return False
            return True
        except Exception as e:
            await db.rollback()
            logger.error("Database error while deleting project", 
                       project_id=project_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error deleting project with id {project_id}",
                operation="delete",
                entity_type="Project",
                entity_id=project_id,
                original_error=e
            )
    
    @staticmethod
    async def update_status(db: AsyncSession, project_id: int, status: UploadStatus) -> Optional[Project]:
        """Update a project's upload status."""
        try:
            project = await ProjectRepository.get_by_id(db, project_id)
            if not project:
                return None
            
            project.upload_status = status
            await db.commit()
            await db.refresh(project)
            return project
        except Exception as e:
            if not isinstance(e, DatabaseException):  # Don't wrap DatabaseExceptions
                await db.rollback()
                logger.error("Database error while updating project status", 
                           project_id=project_id, 
                           status=status, 
                           error=str(e))
                raise DatabaseException(
                    detail=f"Error updating status for project with id {project_id}",
                    operation="update_status",
                    entity_type="Project",
                    entity_id=project_id,
                    original_error=e
                )
            raise e


class FileRepository:
    """Repository for ProjectFile entity database operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, file_id: int) -> Optional[ProjectFile]:
        """Get a file by ID."""
        try:
            result = await db.execute(
                select(ProjectFile)
                .where(ProjectFile.id == file_id)
                .options(selectinload(ProjectFile.project))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting file by ID", 
                       file_id=file_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving file with id {file_id}",
                operation="get_by_id",
                entity="ProjectFile"
            )
    
    @staticmethod
    async def get_by_id_with_relations(
        db: AsyncSession, 
        file_id: int,
        load_project: bool = True
    ) -> Optional[ProjectFile]:
        """
        Get a file by ID with explicit control over which relationships to load.
        
        Args:
            db: Database session
            file_id: ID of the file to retrieve
            load_project: Whether to load the project relationship
            
        Returns:
            ProjectFile object if found, None otherwise
        """
        try:
            query = select(ProjectFile).where(ProjectFile.id == file_id)
            
            if load_project:
                query = query.options(selectinload(ProjectFile.project))
                
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting file by ID with relations", 
                       file_id=file_id,
                       load_project=load_project,
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving file with id {file_id}",
                operation="get_by_id_with_relations",
                entity="ProjectFile"
            )
    
    @staticmethod
    async def get_files_by_project_id(db: AsyncSession, project_id: int) -> List[ProjectFile]:
        """Get all files for a project."""
        try:
            result = await db.execute(
                select(ProjectFile)
                .where(ProjectFile.project_id == project_id)
                .options(selectinload(ProjectFile.project))
                .order_by(ProjectFile.file_path)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database error while getting files for project", 
                       project_id=project_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving files for project with id {project_id}",
                operation="get_files_by_project_id",
                entity_type="ProjectFile",
                entity_id=project_id,
                original_error=e
            )
    
    @staticmethod
    async def create(db: AsyncSession, file_data: Dict[str, Any]) -> ProjectFile:
        """Create a new project file."""
        try:
            project_file = ProjectFile(**file_data)
            db.add(project_file)
            await db.commit()
            await db.refresh(project_file)
            return project_file
        except Exception as e:
            await db.rollback()
            logger.error("Database error while creating project file", 
                       file_data=file_data, 
                       error=str(e))
            raise DatabaseException(
                detail="Error creating project file",
                operation="create",
                entity_type="ProjectFile",
                original_error=e
            )
    
    @staticmethod
    async def update(db: AsyncSession, file: ProjectFile) -> ProjectFile:
        """Update an existing project file."""
        try:
            await db.commit()
            await db.refresh(file)
            return file
        except Exception as e:
            await db.rollback()
            logger.error("Database error while updating project file", 
                       file_id=file.id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error updating file with id {file.id}",
                operation="update",
                entity_type="ProjectFile",
                entity_id=file.id,
                original_error=e
            )
    
    @staticmethod
    async def delete(db: AsyncSession, file_id: int) -> bool:
        """Delete a file by ID."""
        try:
            result = await db.execute(delete(ProjectFile).where(ProjectFile.id == file_id))
            await db.commit()
            if result.rowcount == 0:
                logger.warning("No file found to delete", file_id=file_id)
                return False
            return True
        except Exception as e:
            await db.rollback()
            logger.error("Database error while deleting file", 
                       file_id=file_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error deleting file with id {file_id}",
                operation="delete",
                entity_type="ProjectFile",
                entity_id=file_id,
                original_error=e
            )


class AdditionalFileRepository:
    """Repository for AdditionalProjectFile entity database operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, file_id: int, project_id: int) -> Optional[AdditionalProjectFile]:
        """Get an additional file by ID and project ID."""
        try:
            result = await db.execute(
                select(AdditionalProjectFile)
                .where(
                    AdditionalProjectFile.id == file_id,
                    AdditionalProjectFile.project_id == project_id
                )
                .options(selectinload(AdditionalProjectFile.project))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting additional file by ID", 
                       file_id=file_id, 
                       project_id=project_id,
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving additional file with id {file_id} for project {project_id}",
                operation="get_by_id",
                entity="AdditionalProjectFile"
            )
    
    @staticmethod
    async def get_by_id_with_relations(
        db: AsyncSession, 
        file_id: int,
        project_id: int,
        load_project: bool = True
    ) -> Optional[AdditionalProjectFile]:
        """
        Get an additional file by ID with explicit control over which relationships to load.
        
        Args:
            db: Database session
            file_id: ID of the additional file to retrieve
            project_id: ID of the project the file belongs to
            load_project: Whether to load the project relationship
            
        Returns:
            AdditionalProjectFile object if found, None otherwise
        """
        try:
            query = select(AdditionalProjectFile).where(
                AdditionalProjectFile.id == file_id,
                AdditionalProjectFile.project_id == project_id
            )
            
            if load_project:
                query = query.options(selectinload(AdditionalProjectFile.project))
                
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting additional file by ID with relations", 
                       file_id=file_id,
                       project_id=project_id,
                       load_project=load_project,
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving additional file with id {file_id} for project {project_id}",
                operation="get_by_id_with_relations",
                entity="AdditionalProjectFile"
            )
    
    @staticmethod
    async def get_files_by_project_id(db: AsyncSession, project_id: int) -> List[AdditionalProjectFile]:
        """Get all additional files for a project."""
        try:
            result = await db.execute(
                select(AdditionalProjectFile)
                .where(AdditionalProjectFile.project_id == project_id)
                .options(selectinload(AdditionalProjectFile.project))
                .order_by(AdditionalProjectFile.filename)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database error while getting additional files for project", 
                       project_id=project_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving additional files for project with id {project_id}",
                operation="get_files_by_project_id",
                entity_type="AdditionalProjectFile",
                entity_id=project_id,
                original_error=e
            )
    
    @staticmethod
    async def create(db: AsyncSession, file_data: Dict[str, Any]) -> AdditionalProjectFile:
        """Create a new additional project file."""
        try:
            additional_file = AdditionalProjectFile(**file_data)
            db.add(additional_file)
            await db.commit()
            await db.refresh(additional_file)
            return additional_file
        except Exception as e:
            await db.rollback()
            logger.error("Database error while creating additional file", 
                       file_data=file_data, 
                       error=str(e))
            raise DatabaseException(
                detail="Error creating additional file",
                operation="create",
                entity_type="AdditionalProjectFile",
                original_error=e
            )
    
    @staticmethod
    async def update(db: AsyncSession, file: AdditionalProjectFile) -> AdditionalProjectFile:
        """Update an existing additional project file."""
        try:
            await db.commit()
            await db.refresh(file)
            return file
        except Exception as e:
            await db.rollback()
            logger.error("Database error while updating additional file", 
                       file_id=file.id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error updating additional file with id {file.id}",
                operation="update",
                entity_type="AdditionalProjectFile",
                entity_id=file.id,
                original_error=e
            )
    
    @staticmethod
    async def delete(db: AsyncSession, file_id: int, project_id: int) -> bool:
        """Delete an additional file by ID and project ID."""
        try:
            result = await db.execute(
                delete(AdditionalProjectFile)
                .where(
                    AdditionalProjectFile.id == file_id,
                    AdditionalProjectFile.project_id == project_id
                )
            )
            await db.commit()
            if result.rowcount == 0:
                logger.warning("No additional file found to delete", 
                             file_id=file_id, 
                             project_id=project_id)
                return False
            return True
        except Exception as e:
            await db.rollback()
            logger.error("Database error while deleting additional file", 
                       file_id=file_id, 
                       project_id=project_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error deleting additional file with id {file_id}",
                operation="delete",
                entity_type="AdditionalProjectFile",
                entity_id=file_id,
                original_error=e
            )


class UploadSessionRepository:
    """Repository for UploadSession entity database operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: str) -> Optional[UploadSession]:
        """Get a session by ID."""
        try:
            # No need to eager load relationships here as UploadSession doesn't have any complex relationships
            # that would be accessed frequently in the application flow
            result = await db.execute(select(UploadSession).where(UploadSession.session_id == session_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Database error while getting upload session", 
                       session_id=session_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error retrieving upload session with id {session_id}",
                operation="get_by_id",
                entity_type="UploadSession",
                entity_id=session_id,
                original_error=e
            )
    
    @staticmethod
    async def create(db: AsyncSession, session_data: Dict[str, Any]) -> UploadSession:
        """Create a new upload session."""
        try:
            session = UploadSession(**session_data)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except Exception as e:
            await db.rollback()
            logger.error("Database error while creating upload session", 
                       session_data=session_data, 
                       error=str(e))
            raise DatabaseException(
                detail="Error creating upload session",
                operation="create",
                entity_type="UploadSession",
                original_error=e
            )
    
    @staticmethod
    async def update(db: AsyncSession, session: UploadSession) -> UploadSession:
        """Update an existing upload session."""
        try:
            await db.commit()
            await db.refresh(session)
            return session
        except Exception as e:
            await db.rollback()
            logger.error("Database error while updating upload session", 
                       session_id=session.session_id, 
                       error=str(e))
            raise DatabaseException(
                detail=f"Error updating upload session with id {session.session_id}",
                operation="update",
                entity_type="UploadSession",
                entity_id=session.session_id,
                original_error=e
            ) 