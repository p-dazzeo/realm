"""
File Storage Service for handling file operations.
This service abstracts file storage operations from the business logic.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Union, List
from fastapi import UploadFile
import structlog

from shared.exceptions import FileStorageException

logger = structlog.get_logger()

class FileStorageService:
    """
    Service for handling file storage operations.
    Provides methods for saving, retrieving, and deleting files.
    """
    
    def __init__(self, base_directory: str):
        """
        Initialize the FileStorageService with a base directory.
        
        Args:
            base_directory: The base directory for file storage
        """
        self.base_directory = Path(base_directory)
        # Ensure the base directory exists
        os.makedirs(self.base_directory, exist_ok=True)
    
    def get_storage_path(self, sub_directory: Optional[str] = None) -> Path:
        """
        Get the storage path, optionally with a subdirectory.
        
        Args:
            sub_directory: Optional subdirectory within the base directory
            
        Returns:
            Path object for the storage location
        """
        if sub_directory:
            path = self.base_directory / sub_directory
            os.makedirs(path, exist_ok=True)
            return path
        return self.base_directory
    
    async def save_file(self, 
                        file: UploadFile, 
                        sub_directory: Optional[str] = None,
                        file_name: Optional[str] = None) -> Path:
        """
        Save a file to storage.
        
        Args:
            file: The uploaded file
            sub_directory: Optional subdirectory within the base directory
            file_name: Optional custom filename, uses the original if not provided
            
        Returns:
            Path where the file was saved
            
        Raises:
            FileStorageException: If there was an error saving the file
        """
        storage_path = self.get_storage_path(sub_directory)
        
        # Use original filename if no custom name provided
        safe_filename = file_name or Path(file.filename).name
        file_path = storage_path / safe_filename
        
        try:
            with open(file_path, "wb") as buffer:
                # Handle various file-like objects
                if hasattr(file.file, 'file'):  # SpooledTemporaryFile from FastAPI
                    shutil.copyfileobj(file.file.file, buffer)
                else:  # Other file-like objects
                    content = await file.read()
                    buffer.write(content)
                    
            # Reset file cursor for potential re-reads
            await file.seek(0)
            
            logger.info("File saved successfully", 
                       filename=safe_filename, 
                       path=str(file_path))
            
            return file_path
            
        except Exception as e:
            logger.error("Failed to save file", 
                        filename=safe_filename, 
                        path=str(file_path), 
                        error=str(e))
            raise FileStorageException(
                detail=f"Could not save file: {safe_filename}",
                operation="save",
                filename=safe_filename,
                storage_path=str(file_path),
                original_error=e
            )
    
    def save_content(self, 
                     content: Union[str, bytes], 
                     file_path: Union[str, Path], 
                     sub_directory: Optional[str] = None) -> Path:
        """
        Save content directly to a file.
        
        Args:
            content: String or bytes content to save
            file_path: Path where to save the file (relative to storage path)
            sub_directory: Optional subdirectory within the base directory
            
        Returns:
            Path where the file was saved
            
        Raises:
            FileStorageException: If there was an error saving the content
        """
        storage_path = self.get_storage_path(sub_directory)
        full_path = storage_path / Path(file_path).name
        
        try:
            # Determine if we're dealing with binary or text content
            mode = "wb" if isinstance(content, bytes) else "w"
            encoding = None if isinstance(content, bytes) else "utf-8"
            
            with open(full_path, mode=mode, encoding=encoding) as f:
                f.write(content)
                
            logger.info("Content saved successfully", 
                       path=str(full_path))
            
            return full_path
            
        except Exception as e:
            logger.error("Failed to save content", 
                        path=str(full_path), 
                        error=str(e))
            raise FileStorageException(
                detail=f"Could not save content to file: {full_path}",
                operation="save_content",
                storage_path=str(full_path),
                original_error=e
            )
    
    def retrieve_file(self, 
                      file_path: Union[str, Path], 
                      sub_directory: Optional[str] = None) -> Path:
        """
        Retrieve a file from storage.
        
        Args:
            file_path: Path to the file (relative to storage path)
            sub_directory: Optional subdirectory within the base directory
            
        Returns:
            Path to the file
            
        Raises:
            FileStorageException: If the file doesn't exist
        """
        storage_path = self.get_storage_path(sub_directory)
        full_path = storage_path / Path(file_path).name
        
        if not full_path.exists():
            logger.error("File not found", path=str(full_path))
            raise FileStorageException(
                detail=f"File not found: {file_path}",
                operation="retrieve",
                storage_path=str(full_path),
                filename=Path(file_path).name
            )
        
        return full_path
    
    def delete_file(self, 
                    file_path: Union[str, Path], 
                    sub_directory: Optional[str] = None) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file (relative to storage path)
            sub_directory: Optional subdirectory within the base directory
            
        Returns:
            True if file was deleted, False if file didn't exist
            
        Raises:
            FileStorageException: If there was an error deleting the file
        """
        storage_path = self.get_storage_path(sub_directory)
        full_path = storage_path / Path(file_path).name
        
        if not full_path.exists():
            logger.warning("File not found for deletion", path=str(full_path))
            return False
        
        try:
            os.remove(full_path)
            logger.info("File deleted successfully", path=str(full_path))
            
            # Try to clean up empty directory
            try:
                dir_path = full_path.parent
                if dir_path != self.base_directory and not any(dir_path.iterdir()):
                    os.rmdir(dir_path)
                    logger.info("Empty directory removed", directory=str(dir_path))
            except OSError as e:
                logger.warning("Could not remove directory or it was not empty", 
                             directory=str(full_path.parent), 
                             error=str(e))
                
            return True
            
        except OSError as e:
            logger.error("Error deleting file", path=str(full_path), error=str(e))
            raise FileStorageException(
                detail=f"Could not delete file: {file_path}",
                operation="delete",
                filename=Path(file_path).name,
                storage_path=str(full_path),
                original_error=e
            )
    
    def list_files(self, sub_directory: Optional[str] = None) -> List[Path]:
        """
        List all files in a directory.
        
        Args:
            sub_directory: Optional subdirectory within the base directory
            
        Returns:
            List of Path objects for all files in the directory
        """
        storage_path = self.get_storage_path(sub_directory)
        
        try:
            return [f for f in storage_path.iterdir() if f.is_file()]
        except Exception as e:
            logger.error("Error listing files", 
                        directory=str(storage_path), 
                        error=str(e))
            raise FileStorageException(
                detail=f"Could not list files in directory: {storage_path}",
                operation="list",
                storage_path=str(storage_path),
                original_error=e
            )


# Global service instance with default base directory
file_storage_service = FileStorageService("./storage") 