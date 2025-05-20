"""
Client for the GenDoc service.
"""
from typing import Dict, Any, Optional, List

from frontend.src.clients.base import BaseClient

class GenDocClient(BaseClient):
    """Client for interacting with the GenDoc service."""
    
    def upload_project(self, project_id: str, project_file, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a project to the GenDoc service.
        
        Args:
            project_id: Unique identifier for the project
            project_file: ZIP file containing the project
            description: Optional description of the project
            
        Returns:
            Upload response
        """
        files = {"project_file": project_file}
        data = {"project_id": project_id}
        
        if description:
            data["description"] = description
            
        return self.post("upload", data=data, files=files)
    
    def generate_documentation(self, 
                              project_id: str, 
                              doc_type: str, 
                              file_path: Optional[str] = None,
                              custom_prompt: Optional[str] = None, 
                              model_name: str = "gpt-4",
                              temperature: float = 0.2,
                              max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate documentation for a project.
        
        Args:
            project_id: Unique identifier for the project
            doc_type: Type of documentation to generate
            file_path: Path to a specific file (optional)
            custom_prompt: Custom prompt for documentation generation (optional)
            model_name: LLM model to use
            temperature: Temperature for LLM generation
            max_tokens: Maximum tokens for response (optional)
            
        Returns:
            Generated documentation
        """
        data = {
            "project_id": project_id,
            "doc_type": doc_type,
            "model_name": model_name,
            "temperature": temperature
        }
        
        if file_path:
            data["file_path"] = file_path
            
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
            
        if max_tokens:
            data["max_tokens"] = max_tokens
            
        return self.post("generate", data=data)
    
    def list_project_files(self, project_id: str) -> List[str]:
        """
        List files in a project.
        
        Note: This is a hypothetical endpoint that would need to be implemented
        in the GenDoc service to make this work properly. For now, we'll return
        a dummy list.
        
        Args:
            project_id: Unique identifier for the project
            
        Returns:
            List of file paths
        """
        # This endpoint would need to be created in the GenDoc service
        try:
            response = self.get(f"projects/{project_id}/files")
            return response.get("files", [])
        except Exception:
            # Fallback to dummy data
            return [
                "main.py",
                "utils.py",
                "models.py",
                "config.py"
            ] 