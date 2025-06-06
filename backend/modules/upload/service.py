import asyncio
import hashlib
import httpx
import mimetypes
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException
import structlog
import aiofiles
import zipfile
import tempfile

from core.config import upload_settings
from modules.upload.models import Project, ProjectFile, UploadSession
from modules.upload.schemas import (
    ProjectCreate, FileUploadRequest, ProjectUploadRequest,
    ParserRequest, ParserResponse, UploadMethod, UploadStatus, SessionStatus
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
            else:
                logger.debug("Skipping file with disallowed extension", filename=file_data['filename'])
        
        logger.info("Files extracted", total=len(files), filtered=len(filtered_files))
        return filtered_files
    
    async def _extract_archive(self, uploaded_file: UploadFile) -> List[Dict[str, Any]]:
        """Extract files from archive"""
        files = []
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await uploaded_file.read()
            temp_file.write(content)
            temp_file.flush()
            
            try:
                with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        if file_info.is_dir():
                            continue
                            
                        # Skip hidden files and common non-code files
                        filename = file_info.filename
                        if self._should_skip_file(filename):
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
                                
                        except Exception as e:
                            logger.warning("Failed to extract file", filename=filename, error=str(e))
                            continue
                            
            finally:
                os.unlink(temp_file.name)
        
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
                return True
        
        return filename.startswith('.')
    
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
                await self._create_project_file_direct(db, project, file_data)
                processed_count += 1
                
                # Update session progress
                session.processed_files = processed_count
                if processed_count % 10 == 0:  # Update every 10 files
                    await db.commit()
                    
            except Exception as e:
                failed_count += 1
                session.errors = session.errors or []
                session.errors.append(f"Failed to process {file_data['filename']}: {str(e)}")
                logger.warning("Failed to process file", filename=file_data['filename'], error=str(e))
        
        # Update final status
        session.project_id = project.id
        session.failed_files = failed_count
        
        if failed_count == 0:
            session.status = SessionStatus.COMPLETED
            project.upload_status = UploadStatus.COMPLETED
        elif processed_count > 0:
            session.status = SessionStatus.COMPLETED
            project.upload_status = UploadStatus.COMPLETED
            session.warnings = [f"{failed_count} files failed to process"]
        else:
            session.status = SessionStatus.FAILED
            project.upload_status = UploadStatus.FAILED
        
        await db.commit()
        return project
    
    async def _create_project_files_from_parser(
        self,
        db: AsyncSession,
        project: Project,
        parser_data: Dict[str, Any],
        original_files: List[Dict[str, Any]]
    ):
        """Create ProjectFile records from parser response"""
        # This depends on the parser response format
        # For now, we'll create a basic implementation
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
        
        project_file = ProjectFile(
            project_id=project.id,
            filename=file_data['filename'],
            file_path=file_data['relative_path'],
            relative_path=file_data['relative_path'],
            file_extension=Path(file_data['filename']).suffix,
            file_size=file_data.get('size', len(content.encode())),
            content=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            language=self._detect_language(file_data['filename']),
            is_binary=file_data.get('is_binary', False),
            loc=len(content.split('\n')) if not file_data.get('is_binary') else 0
        )
        
        db.add(project_file)
    
    def _detect_language(self, filename: str) -> Optional[str]:
        """Simple language detection based on file extension"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.sql': 'sql',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        
        ext = Path(filename).suffix.lower()
        return ext_to_lang.get(ext)


# Global service instance
upload_service = UploadService() 