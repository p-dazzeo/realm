import hashlib
import httpx
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Added this
from fastapi import UploadFile, HTTPException
import structlog
import shutil # Added this
import zipfile
import tempfile

from core.config import upload_settings
from modules.upload.models import Project, ProjectFile, UploadSession, AdditionalProjectFile # Added AdditionalProjectFile
from modules.upload.schemas import (
    ProjectCreate,
    ParserRequest, ParserResponse, UploadMethod, UploadStatus, SessionStatus,
    AdditionalFileUpdateRequest # Added this
)

logger = structlog.get_logger()


class UploadService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=upload_settings.parser_service_timeout)
        
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
        
        session = UploadSession(
            upload_method=upload_method,
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
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
        session = await self.create_upload_session(db, UploadMethod.PARSER)
        
        try:
            # First, try to extract and analyze the uploaded file
            extracted_files = await self._extract_project_files(uploaded_file)
            
            # Update session with file count
            session.total_files = len(extracted_files)
            await db.commit()
            
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
                    session.upload_method = UploadMethod.DIRECT
                    session.errors = [f"Parser failed: {str(e)}"]
                    await db.commit()
            
            # Fallback to direct upload
            logger.info("Using direct upload", session_id=session.session_id)
            project = await self._upload_direct(
                db, session, project_data, extracted_files
            )
            logger.info("Direct upload successful", project_id=project.id)
            return project, session
            
        except Exception as e:
            session.status = SessionStatus.FAILED
            session.errors = session.errors or []
            session.errors.append(str(e))
            await db.commit()
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
        """Upload project using external parser service"""
        # Prepare request for parser
        parser_request = ParserRequest(
            project_name=project_data.name,
            files=files
        )
        
        try:
            # Call parser service
            response = await self.http_client.post(
                f"{upload_settings.parser_service_url}/parse",
                json=parser_request.model_dump()
            )
            response.raise_for_status()
            
            parser_response = ParserResponse(**response.json())
            
            if not parser_response.success:
                raise Exception(f"Parser failed: {parser_response.error}")
            
            # Create project with parser data
            project = Project(
                name=project_data.name,
                description=project_data.description,
                upload_method=UploadMethod.PARSER,
                upload_status=UploadStatus.PROCESSING,
                original_filename=session.session_id,  # Use session ID as reference
                file_size=sum(f.get('size', 0) for f in files),
                parser_response=parser_response.data,
                parser_version=parser_response.version
            )
            
            db.add(project)
            await db.commit()
            await db.refresh(project)
            
            # Process parsed files and create ProjectFile records
            await self._create_project_files_from_parser(
                db, project, parser_response.data, files
            )
            
            # Update session and project status
            session.project_id = project.id
            session.status = SessionStatus.COMPLETED
            session.processed_files = len(files)
            
            project.upload_status = UploadStatus.COMPLETED
            
            await db.commit()
            
            return project
            
        except httpx.RequestError as e:
            raise Exception(f"Parser service unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Parser service error: {e.response.status_code}")
    
    async def _upload_direct(
        self,
        db: AsyncSession,
        session: UploadSession,
        project_data: ProjectCreate,
        files: List[Dict[str, Any]]
    ) -> Project:
        """Upload project using direct file storage"""
        # Create project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            upload_method=UploadMethod.DIRECT,
            upload_status=UploadStatus.PROCESSING,
            original_filename=session.session_id,
            file_size=sum(f.get('size', 0) for f in files)
        )
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        # Process files
        processed_count = 0
        failed_count = 0
        
        for file_data in files:
            try:
                logger.info("Processing file for database storage", 
                          filename=file_data['filename'],
                          relative_path=file_data['relative_path'],
                          size=file_data.get('size', 0))
                
                await self._create_project_file_direct(db, project, file_data)
                processed_count += 1
                
                logger.info("File successfully stored in database", 
                          filename=file_data['filename'],
                          project_id=project.id,
                          processed_count=processed_count)
                
                # Update session progress
                session.processed_files = processed_count
                    
            except Exception as e:
                failed_count += 1
                session.errors = session.errors or []
                session.errors.append(f"Failed to process {file_data['filename']}: {str(e)}")
                logger.error("Failed to store file in database", 
                           filename=file_data['filename'], 
                           error=str(e),
                           project_id=project.id)
        
                # Update final status
        session.project_id = project.id
        session.failed_files = failed_count
        
        if failed_count == 0:
            session.status = SessionStatus.COMPLETED
            project.upload_status = UploadStatus.COMPLETED
            logger.info("Project upload completed successfully", 
                       project_id=project.id,
                       project_name=project.name,
                       files_processed=processed_count,
                       upload_method="direct")
        elif processed_count > 0:
            session.status = SessionStatus.COMPLETED
            project.upload_status = UploadStatus.COMPLETED
            session.warnings = [f"{failed_count} files failed to process"]
            logger.warning("Project upload completed with some failures", 
                         project_id=project.id,
                         project_name=project.name,
                         files_processed=processed_count,
                         files_failed=failed_count,
                         upload_method="direct")
        else:
            session.status = SessionStatus.FAILED
            project.upload_status = UploadStatus.FAILED
            logger.error("Project upload failed - no files processed", 
                       project_id=project.id,
                       project_name=project.name,
                       files_failed=failed_count,
                       upload_method="direct")

        await db.commit()
        logger.info("Database commit completed", 
                   project_id=project.id,
                   session_id=session.session_id)
        return project
    
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


# Global service instance
upload_service = UploadService()

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
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found.")

        # 2. Determine storage path (create project-specific dir if not exists)
        #    Ensure upload_settings.additional_files_dir is defined in core/config.py
        project_files_dir = Path(upload_settings.additional_files_dir) / f"project_{project.uuid}" # Use project.uuid for unique folder
        os.makedirs(project_files_dir, exist_ok=True)

        # Sanitize filename (basic example, consider more robust sanitization)
        safe_filename = Path(uploaded_file.filename).name
        file_location = project_files_dir / safe_filename

        # Ensure filename uniqueness if necessary, e.g., by appending a suffix if file_location.exists()
        # For simplicity, this example overwrites. Consider adding a counter or UUID if overwriting is not desired.
        # counter = 0
        # original_stem = file_location.stem
        # while file_location.exists():
        #     counter += 1
        #     file_location = project_files_dir / f"{original_stem}_{counter}{file_location.suffix}"
        # safe_filename = file_location.name


        # 3. Save uploaded_file content
        try:
            with open(file_location, "wb") as buffer:
                # Access underlying file object for copyfileobj if available and direct,
                # otherwise read and write in chunks for compatibility with SpooledTemporaryFile
                if hasattr(uploaded_file.file, 'file'): # Handles SpooledTemporaryFile from FastAPI
                    shutil.copyfileobj(uploaded_file.file.file, buffer)
                else: # Fallback for other file-like objects if necessary
                    content = await uploaded_file.read()
                    buffer.write(content)
            await uploaded_file.seek(0) # Reset cursor for any potential re-reads by FastAPI framework
        except Exception as e:
            logger.error("Failed to save additional file", filename=safe_filename, path=str(file_location), error=str(e))
            raise HTTPException(status_code=500, detail=f"Could not save file: {safe_filename}. Error: {str(e)}")
        finally:
            await uploaded_file.close()

        # 4. Get file size
        try:
            file_size = file_location.stat().st_size
        except FileNotFoundError:
            logger.error("Failed to get file size, file not found after saving", filename=safe_filename, path=str(file_location))
            raise HTTPException(status_code=500, detail=f"Could not determine file size for: {safe_filename}.")


        # 5. Create AdditionalProjectFile record
        additional_file = AdditionalProjectFile(
            project_id=project_id,
            filename=safe_filename,
            file_path=str(file_location), # Store absolute path
            file_size=file_size,
            description=description
        )

        db.add(additional_file)
        await db.commit()
        await db.refresh(additional_file)
        logger.info("Additional file added to project", additional_file_id=additional_file.id, project_id=project_id, filename=safe_filename, path=str(file_location))
        return additional_file

    async def get_additional_file(
        self,
        db: AsyncSession,
        project_id: int,
        additional_file_id: int
    ) -> Optional[AdditionalProjectFile]:
        result = await db.execute(
            select(AdditionalProjectFile).where(
                AdditionalProjectFile.id == additional_file_id,
                AdditionalProjectFile.project_id == project_id
            )
        )
        return result.scalar_one_or_none()

    async def update_additional_file(
        self,
        db: AsyncSession,
        project_id: int,
        additional_file_id: int,
        data: AdditionalFileUpdateRequest
    ) -> Optional[AdditionalProjectFile]:
        additional_file = await self.get_additional_file(db, project_id, additional_file_id)
        if not additional_file:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "description" in update_data: # Allows setting description to "" or nullifying it if model field is nullable
            additional_file.description = update_data["description"]

        # Add updates for other fields if they become mutable
        # e.g., if data.filename: additional_file.filename = data.filename (and rename file on disk)

        if update_data: # Only commit if there was data to update
            await db.commit()
            await db.refresh(additional_file)
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
        additional_file = await self.get_additional_file(db, project_id, additional_file_id)
        if not additional_file:
            return False # Or raise HTTPException(status_code=404, detail="Additional file not found")

        file_path_to_delete = Path(additional_file.file_path)

        # Attempt to delete DB record first or mark for deletion
        await db.delete(additional_file)
        await db.commit()
        logger.info("Additional file record deleted from DB", additional_file_id=additional_file_id, project_id=project_id)

        # Then delete file from filesystem
        if file_path_to_delete.exists():
            try:
                os.remove(file_path_to_delete)
                logger.info("Additional file deleted from filesystem", path=str(file_path_to_delete))

                # Attempt to remove project-specific directory if empty
                try:
                    project_files_dir = file_path_to_delete.parent
                    if not any(project_files_dir.iterdir()): # Check if directory is empty
                        os.rmdir(project_files_dir)
                        logger.info("Empty project-specific additional files directory removed", directory=str(project_files_dir))
                except OSError as e:
                    logger.warning("Could not remove project-specific directory or it was not empty", directory=str(project_files_dir), error=str(e))

            except OSError as e:
                logger.error("Error deleting additional file from filesystem", path=str(file_path_to_delete), error=str(e))
                # Consider implications: DB record is gone. File system deletion failed.
                # This might require a cleanup job or manual intervention if critical.
                # For now, just log the error.
        else:
            logger.warning("Additional file not found on filesystem for deletion", path=str(file_path_to_delete))

        return True