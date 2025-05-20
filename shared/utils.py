"""
Utility functions shared across services.
"""
import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import inspect

# File types that should be ignored during code parsing
IGNORED_EXTENSIONS = {
    '.pyc', '.pyo', '.git', '.svn', '.hg', '.idea', '.vscode', '.class',
    '.jar', '.war', '.ear', '.log', '.tmp', '.bak', '.swp', '.DS_Store',
    '.coverage', '.pytest_cache', '__pycache__', '.ipynb_checkpoints'
}

# Common code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rb', '.php',
    '.html', '.css', '.scala', '.swift', '.kt', '.rs', '.sh', '.bash', '.ps1',
    '.sql', '.r', '.m', '.mm', '.h', '.hpp'
}


async def extract_zip(zip_file, target_dir: str) -> Path:
    """
    Extract a zip file to the specified directory.
    
    Args:
        zip_file: The zip file object (from streamlit or FastAPI)
        target_dir: Directory to extract to
        
    Returns:
        Path to the extracted directory
    """
    # Create a temporary directory
    os.makedirs(target_dir, exist_ok=True)
    extract_dir = Path(target_dir)
    
    # Extract the zip file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        # Handle both async and sync file objects
        if hasattr(zip_file, 'read') and inspect.iscoroutinefunction(zip_file.read):
            # FastAPI's UploadFile (needs await)
            content = await zip_file.read()
        else:
            # Regular file or streamlit's UploadFile
            content = zip_file.read()
            
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Clean up the temporary file
    os.unlink(tmp_file_path)
    
    return extract_dir


def get_file_contents(file_path: str) -> Optional[str]:
    """
    Read and return the contents of a text file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File contents as string or None if file is binary
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            return file.read()
    except (UnicodeDecodeError, OSError):
        # File is likely binary
        return None


def list_files(directory: Path, ignore_extensions: Set[str] = IGNORED_EXTENSIONS) -> List[Path]:
    """
    List all files in a directory recursively, ignoring specified extensions.
    
    Args:
        directory: Directory path to search
        ignore_extensions: File extensions to ignore
        
    Returns:
        List of file paths
    """
    files = []
    
    for item in directory.rglob('*'):
        # Skip directories and ignored file types
        if item.is_dir() or any(ext in str(item) for ext in ignore_extensions):
            continue
        files.append(item)
    
    return files


def get_project_structure(directory: Path) -> Dict[str, Any]:
    """
    Generate a dictionary representing the project structure.
    
    Args:
        directory: Root directory
        
    Returns:
        Dictionary with folder structure
    """
    result = {'name': directory.name, 'type': 'directory', 'children': []}
    
    for item in directory.iterdir():
        if any(ext in str(item) for ext in IGNORED_EXTENSIONS):
            continue
            
        if item.is_file():
            result['children'].append({
                'name': item.name,
                'type': 'file',
                'extension': item.suffix
            })
        elif item.is_dir():
            result['children'].append(get_project_structure(item))
    
    return result 