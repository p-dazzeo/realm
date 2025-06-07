import hashlib
import httpx
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException
import structlog
import zipfile
import tempfile

from core.config import upload_settings
from modules.upload.models import Project, ProjectFile, UploadSession, AdditionalProjectFile
from modules.upload.schemas import (
    ProjectCreate,
    ParserRequest, ParserResponse, UploadMethod, UploadStatus, SessionStatus,
    AdditionalFileUpdateRequest
)
from modules.upload.repositories import ProjectRepository, FileRepository, AdditionalFileRepository, UploadSessionRepository
from shared.services.file_storage import file_storage_service
from shared.exceptions import ProjectNotFoundException, FileNotFoundException, ParserServiceException, ValidationException

logger = structlog.get_logger()


class UploadService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=upload_settings.parser_service_timeout)
        self.file_storage = file_storage_service
        
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    async def create_upload_session(
        self, 
        db: AsyncSession,
        upload_method: UploadMethod
    ) -> UploadSession:
        """Create a new upload session"""
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour expiration
        
        session_data = {
            "upload_method": upload_method,
            "expires_at": expires_at
        }
        
        session = await UploadSessionRepository.create(db, session_data)
        
        logger.info("Upload session created", session_id=session.session_id)
        return session
    
    async def upload_project_intelligent(
        self,
        db: AsyncSession,
        project_data: ProjectCreate,
        uploaded_file: UploadFile
    ) -> Tuple[Project, UploadSession]:
        """
        Intelligent upload that tries parser first, falls back to direct upload
        """
        logger.info("Starting intelligent project upload", filename=uploaded_file.filename)
        
        # Create upload session
        async with db.begin():
            session = await self.create_upload_session(db, UploadMethod.PARSER)
        
        try:
            # First, try to extract and analyze the uploaded file
            extracted_files = await self._extract_project_files(uploaded_file)
            
            # Update session with file count
            async with db.begin():
                session.total_files = len(extracted_files)
            
            # Try parser first if enabled
            if upload_settings.parser_service_enabled:
                logger.info("Attempting parser upload", session_id=session.session_id)
                try:
                    project = await self._upload_via_parser(
                        db, session, project_data, extracted_files
                    )
                    logger.info("Parser upload successful", project_id=project.id)
                    return project, session
                    
                except Exception as e:
                    logger.warning(
                        "Parser upload failed, falling back to direct upload",
                        error=str(e), session_id=session.session_id
                    )
                    # Update session method and continue with direct upload
                    async with db.begin():
                        session.upload_method = UploadMethod.DIRECT
                        session.errors = [f"Parser failed: {str(e)}"]
            
            # Fallback to direct upload
            logger.info("Using direct upload", session_id=session.session_id)
            project = await self._upload_direct(
                db, session, project_data, extracted_files
            )
            logger.info("Direct upload successful", project_id=project.id)
            return project, session
            
        except Exception as e:
            async with db.begin():
                session.status = SessionStatus.FAILED
                session.errors = session.errors or []
                session.errors.append(str(e))
            logger.error("Upload failed", error=str(e), session_id=session.session_id)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    async def _extract_project_files(self, uploaded_file: UploadFile) -> List[Dict[str, Any]]:
        """Extract files from uploaded archive or handle single file"""
        files = []
        
        # Check file size
        content = await uploaded_file.read()
        file_size = len(content)
        
        if file_size > upload_settings.max_project_size * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {upload_settings.max_project_size}MB"
            )
        
        # Reset file pointer
        await uploaded_file.seek(0)
        
        # Determine if it's an archive
        filename = uploaded_file.filename or "unknown"
        is_archive = filename.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz'))
        
        if is_archive:
            files = await self._extract_archive(uploaded_file)
        else:
            # Single file upload
            content = content.decode('utf-8', errors='ignore')
            files = [{
                'filename': filename,
                'relative_path': filename,
                'content': content,
                'size': file_size
            }]
        
        # Filter allowed extensions
        filtered_files = []
        for file_data in files:
            ext = Path(file_data['filename']).suffix.lower()
            if ext in upload_settings.allowed_extensions or not ext:
                filtered_files.append(file_data)
                logger.info("File passed extension filter", 
                          filename=file_data['filename'], 
                          extension=ext, 
                          size=file_data.get('size', 0))
            else:
                logger.warning("Skipping file with disallowed extension", 
                             filename=file_data['filename'], 
                             extension=ext,
                             allowed_extensions=upload_settings.allowed_extensions)

        logger.info("File extraction summary", 
                   total_extracted=len(files), 
                   passed_filter=len(filtered_files),
                   skipped_by_filter=len(files) - len(filtered_files))
        return filtered_files
    
    async def _extract_archive(self, uploaded_file: UploadFile) -> List[Dict[str, Any]]:
        """Extract files from archive"""
        files = []
        temp_file_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name
                content = await uploaded_file.read()
                temp_file.write(content)
                temp_file.flush()
            
            zip_ref = None
            try:
                zip_ref = zipfile.ZipFile(temp_file_path, 'r')
                
                for file_info in zip_ref.infolist():
                    if file_info.is_dir():
                        continue
                        
                    # Skip hidden files and common non-code files
                    filename = file_info.filename
                    if self._should_skip_file(filename):
                        logger.info("Skipping file due to skip patterns", 
                                  filename=filename, reason="matches skip pattern")
                        continue
                    
                    try:
                        with zip_ref.open(file_info) as file_content:
                            content = file_content.read()
                            
                            # Check if binary
                            try:
                                text_content = content.decode('utf-8')
                                is_binary = False
                            except UnicodeDecodeError:
                                text_content = content.decode('utf-8', errors='ignore')
                                is_binary = True
                            
                            files.append({
                                'filename': Path(filename).name,
                                'relative_path': filename,
                                'content': text_content,
                                'size': file_info.file_size,
                                'is_binary': is_binary
                            })
                            
                            logger.info("Extracted file from ZIP", 
                                      filename=Path(filename).name,
                                      relative_path=filename,
                                      size=file_info.file_size,
                                      is_binary=is_binary)
                            
                    except Exception as e:
                        logger.warning("Failed to extract file", filename=filename, error=str(e))
                        continue
                        
            finally:
                if zip_ref:
                    zip_ref.close()
                    
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except (OSError, PermissionError) as e:
                    logger.warning("Could not delete temporary file", 
                                 filename=temp_file_path, error=str(e))
        
        return files
    
    def _should_skip_file(self, filename: str) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            '__pycache__', '.git', '.svn', '.hg', 'node_modules',
            '.DS_Store', 'Thumbs.db', '.vscode', '.idea',
            'dist', 'build', 'target', 'bin', 'obj'
        ]
        
        for pattern in skip_patterns:
            if pattern in filename:
                logger.info("File skipped due to pattern match", 
                          filename=filename, 
                          matched_pattern=pattern)
                return True
        
        if filename.startswith('.'):
            logger.info("File skipped - hidden file", filename=filename)
            return True
            
        return False
    
    async def _upload_via_parser(
        self,
        db: AsyncSession,
        session: UploadSession,
        project_data: ProjectCreate,
        files: List[Dict[str, Any]]
    ) -> Project:
        """Upload project using parser service for analysis"""
        if not upload_settings.parser_service_enabled:
            raise ParserServiceException(detail="Parser service is disabled")
        
        try:
            # Prepare data for parser
            parser_request = ParserRequest(
                project_name=project_data.name,
                files=[{
                    'filename': f['filename'],
                    'path': f['relative_path'],
                    'content': f['content'],
                    'size': f.get('size', 0)
                } for f in files]
            )
            
            # Call parser service
            logger.info("Calling parser service", project_name=project_data.name)
            response = await self.http_client.post(
                f"{upload_settings.parser_service_url}/parse",
                json=parser_request.model_dump(),
                timeout=upload_settings.parser_service_timeout
            )
            
            if response.status_code != 200:
                raise ParserServiceException(
                    detail=f"Parser service error: {response.text}"
                )
            
            # Process parser response
            parser_response = ParserResponse(**response.json())
            
            if not parser_response.success:
                raise ParserServiceException(
                    detail=f"Parser failed: {parser_response.error}"
                )
            
            # Create project record
            async with db.begin():
                # Create project
                project = Project(
                    name=project_data.name,
                    description=project_data.description,
                    upload_method=UploadMethod.PARSER,
                    upload_status=UploadStatus.PROCESSING,
                    original_filename=files[0]['filename'] if len(files) == 1 else None,
                    file_size=sum(f.get('size', 0) for f in files),
                    parser_response=parser_response.data,
                    parser_version=parser_response.version
                )
                db.add(project)
                await db.flush()  # Get project ID without committing
                
                # Create project files
                await self._create_project_files_from_parser(
                    db, project, parser_response.data, files
                )
                
                # Update session
                session.project_id = project.id
                session.status = SessionStatus.COMPLETED
                session.processed_files = len(files)
            
            # Set final status
            async with db.begin():
                project.upload_status = UploadStatus.COMPLETED
            
            logger.info("Project created via parser", project_id=project.id)
            return project
            
        except Exception as e:
            logger.error("Parser upload failed", error=str(e))
            # Update session with failure information
            async with db.begin():
                session.status = SessionStatus.FAILED
                session.errors = session.errors or []
                session.errors.append(str(e))
            
            if isinstance(e, ParserServiceException):
                raise
                
            raise ParserServiceException(
                detail=f"Parser error: {str(e)}"
            )
    
    async def _upload_direct(
        self,
        db: AsyncSession,
        session: UploadSession,
        project_data: ProjectCreate,
        files: List[Dict[str, Any]]
    ) -> Project:
        """Upload project using direct file analysis"""
        try:
            # Create project record with transaction
            async with db.begin():
                # Create project
                project = Project(
                    name=project_data.name,
                    description=project_data.description,
                    upload_method=UploadMethod.DIRECT,
                    upload_status=UploadStatus.PROCESSING,
                    original_filename=files[0]['filename'] if len(files) == 1 else None,
                    file_size=sum(f.get('size', 0) for f in files)
                )
                db.add(project)
                await db.flush()  # Get project ID without committing
                
                # Process each file
                logger.info("Processing files for direct upload", file_count=len(files))
                for file_data in files:
                    await self._create_project_file_direct(db, project, file_data)
                    
                # Update session
                session.project_id = project.id
                session.status = SessionStatus.COMPLETED
                session.processed_files = len(files)
            
            # Set final status
            async with db.begin():
                project.upload_status = UploadStatus.COMPLETED
            
            logger.info("Project created via direct upload", project_id=project.id)
            return project
            
        except Exception as e:
            logger.error("Direct upload failed", error=str(e))
            # Update session with failure information
            async with db.begin():
                session.status = SessionStatus.FAILED
                session.errors = session.errors or []
                session.errors.append(str(e))
            raise ValidationException(
                detail=f"Direct upload failed: {str(e)}",
                field_errors={"files": str(e)}
            )
    
    async def _create_project_files_from_parser(
        self,
        db: AsyncSession,
        project: Project,
        parser_data: Dict[str, Any],
        original_files: List[Dict[str, Any]]
    ):
        """Create ProjectFile records from parser response"""

        for file_data in original_files:
            project_file = ProjectFile(
                project_id=project.id,
                filename=file_data['filename'],
                file_path=file_data['relative_path'],
                relative_path=file_data['relative_path'],
                file_extension=Path(file_data['filename']).suffix,
                file_size=file_data.get('size', 0),
                content=file_data['content'],
                content_hash=hashlib.sha256(file_data['content'].encode()).hexdigest(),
                parsed_data=parser_data.get('files', {}).get(file_data['relative_path']),
                language=self._detect_language(file_data['filename']),
                is_binary=file_data.get('is_binary', False),
                loc=len(file_data['content'].split('\n')) if not file_data.get('is_binary') else 0
            )
            db.add(project_file)
    
    async def _create_project_file_direct(
        self,
        db: AsyncSession,
        project: Project,
        file_data: Dict[str, Any]
    ):
        """Create a ProjectFile record for direct upload"""
        content = file_data['content']
        detected_language = self._detect_language(file_data['filename'])
        file_extension = Path(file_data['filename']).suffix
        lines_of_code = len(content.split('\n')) if not file_data.get('is_binary') else 0
        
        logger.info("Creating ProjectFile record", 
                  filename=file_data['filename'],
                  language=detected_language,
                  extension=file_extension,
                  size=file_data.get('size', len(content.encode())),
                  lines_of_code=lines_of_code,
                  is_binary=file_data.get('is_binary', False))
        
        project_file = ProjectFile(
            project_id=project.id,
            filename=file_data['filename'],
            file_path=file_data['relative_path'],
            relative_path=file_data['relative_path'],
            file_extension=file_extension,
            file_size=file_data.get('size', len(content.encode())),
            content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            language=detected_language,
            is_binary=file_data.get('is_binary', False),
            loc=lines_of_code
        )
        
        db.add(project_file)
        logger.debug("ProjectFile record added to database session", 
                   filename=file_data['filename'],
                   project_id=project.id)
    
    def _detect_language(self, filename: str) -> Optional[str]:
        """Simple language detection based on file extension"""
        ext_to_lang = {
            '.cbl': 'cobol',
            '.cob': 'cobol',
            '.CBL': 'cobol',
            '.cpy': 'cobol',
            '.CPY': 'cobol',
            '.jcl': 'jcl',
            '.JCL': 'jcl'
        }
        
        ext = Path(filename).suffix.lower()
        return ext_to_lang.get(ext)

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # AdditionalProjectFile specific methods
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    async def add_additional_file_to_project(
        self,
        db: AsyncSession,
        project_id: int,
        uploaded_file: UploadFile,
        description: Optional[str]
    ) -> AdditionalProjectFile:
        # 1. Verify project exists
        project = await ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise ProjectNotFoundException(project_id=project_id)

        # 2. Use FileStorageService to save the file
        sub_directory = f"project_{project.uuid}"
        safe_filename = Path(uploaded_file.filename).name
        
        try:
            file_location = await self.file_storage.save_file(
                file=uploaded_file,
                sub_directory=sub_directory,
                file_name=safe_filename
            )
            
            # 3. Create AdditionalProjectFile record within a transaction
            file_data = {
                "project_id": project_id,
                "filename": safe_filename,
                "file_path": str(file_location),
                "file_size": file_location.stat().st_size,
                "description": description
            }

            async with db.begin():
                additional_file = await AdditionalFileRepository.create(db, file_data)
            
            logger.info("Additional file added to project", 
                      additional_file_id=additional_file.id, 
                      project_id=project_id, 
                      filename=safe_filename, 
                      path=str(file_location))
            
            return additional_file
            
        except Exception as e:
            logger.error("Failed to add additional file to project", 
                       project_id=project_id, 
                       filename=safe_filename, 
                       error=str(e))
            # If we encountered an error after saving the file but before creating the DB record,
            # try to clean up the file
            try:
                self.file_storage.delete_file(safe_filename, sub_directory=sub_directory)
            except Exception as cleanup_error:
                logger.warning("Failed to clean up file after error", 
                             filename=safe_filename, 
                             error=str(cleanup_error))
            
            if isinstance(e, (ProjectNotFoundException, FileNotFoundException, ParserServiceException, ValidationException)):
                raise
            raise ValidationException(
                detail=f"Could not add file to project: {str(e)}",
                field_errors={"file": str(e)}
            )

    async def get_additional_file(
        self,
        db: AsyncSession,
        project_id: int,
        additional_file_id: int
    ) -> Optional[AdditionalProjectFile]:
        file = await AdditionalFileRepository.get_by_id(db, additional_file_id, project_id)
        if not file:
            raise FileNotFoundException(
                file_id=additional_file_id,
                project_id=project_id
            )
        return file

    async def update_additional_file(
        self,
        db: AsyncSession,
        project_id: int,
        additional_file_id: int,
        data: AdditionalFileUpdateRequest
    ) -> Optional[AdditionalProjectFile]:
        additional_file = await AdditionalFileRepository.get_by_id(db, additional_file_id, project_id)
        if not additional_file:
            raise FileNotFoundException(
                file_id=additional_file_id,
                project_id=project_id
            )

        update_data = data.model_dump(exclude_unset=True)

        if update_data:  # Only proceed with update if there's data to update
            async with db.begin():
                if "description" in update_data:  # Allows setting description to "" or nullifying it if model field is nullable
                    additional_file.description = update_data["description"]
                
                # Add updates for other fields if they become mutable
                # e.g., if data.filename: additional_file.filename = data.filename (and rename file on disk)
                
                additional_file = await AdditionalFileRepository.update(db, additional_file)
            
            logger.info("Additional file updated", additional_file_id=additional_file.id, project_id=project_id, changes=update_data)
        else:
            logger.info("No changes detected for additional file update", additional_file_id=additional_file.id, project_id=project_id)
        
        return additional_file

    async def delete_additional_file(
        self,
        db: AsyncSession,
        project_id: int,
        additional_file_id: int
    ) -> bool:
        additional_file = await AdditionalFileRepository.get_by_id(db, additional_file_id, project_id)
        if not additional_file:
            raise FileNotFoundException(
                file_id=additional_file_id,
                project_id=project_id
            )

        file_path_to_delete = Path(additional_file.file_path)
        # Store project_uuid before deleting the record to avoid SQLAlchemy relationship access issues
        project_uuid = additional_file.project.uuid

        # Delete the DB record within a transaction
        async with db.begin():
            deleted = await AdditionalFileRepository.delete(db, additional_file_id, project_id)
        
        if deleted:
            logger.info("Additional file record deleted from DB", additional_file_id=additional_file_id, project_id=project_id)
        
            # Then delete file from filesystem using FileStorageService
            try:
                self.file_storage.delete_file(file_path_to_delete.name, sub_directory=f"project_{project_uuid}")
                logger.info("Additional file deleted from filesystem", path=str(file_path_to_delete))
            except Exception as e:
                logger.error("Error deleting additional file from filesystem", 
                           path=str(file_path_to_delete), 
                           error=str(e))
                # DB record is already deleted, so we'll still return True
        
        return deleted


# Global service instance
upload_service = UploadService()