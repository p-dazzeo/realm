"""
Client for the RAG service.
"""
from typing import Dict, Any, Optional, List

from frontend.src.clients.base import BaseClient

class RAGClient(BaseClient):
    """Client for interacting with the RAG service."""
    
    def upload_project(self, project_id: str, project_file, 
                      description: Optional[str] = None,
                      index_immediately: bool = True) -> Dict[str, Any]:
        """
        Upload a project to the RAG service.
        
        Args:
            project_id: Unique identifier for the project
            project_file: ZIP file containing the project
            description: Optional description of the project
            index_immediately: Whether to index the project immediately
            
        Returns:
            Upload response
        """
        files = {"project_file": project_file}
        data = {
            "project_id": project_id,
            "index_immediately": "true" if index_immediately else "false"
        }
        
        if description:
            data["description"] = description
            
        return self.post("upload", data=data, files=files)
    
    def query_rag(self, 
                 project_id: str, 
                 query: str,
                 file_paths: Optional[List[str]] = None,
                 model_name: str = "gpt-4",
                 limit: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            project_id: Unique identifier for the project
            query: The query to process
            file_paths: Optional list of specific file paths to search in
            model_name: LLM model to use
            limit: Maximum number of context chunks to retrieve
            
        Returns:
            RAG response
        """
        data = {
            "project_id": project_id,
            "query": query,
            "model_name": model_name,
            "limit": limit
        }
        
        if file_paths:
            data["file_paths"] = file_paths
            
        return self.post("query", data=data)
    
    def index_project(self, project_id: str) -> Dict[str, Any]:
        """
        Trigger indexing or reindexing of a project.
        
        Args:
            project_id: Unique identifier for the project
            
        Returns:
            Indexing status
        """
        return self.post("index", data={"project_id": project_id}) 