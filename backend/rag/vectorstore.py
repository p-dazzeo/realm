"""
Vector store operations for the RAG service.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

from backend.rag import config
from shared.utils import get_file_contents, list_files

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class CodeVectorStore:
    """
    Vector store for code files using ChromaDB.
    """
    
    def __init__(self, project_id: str):
        """
        Initialize the vector store for a specific project.
        
        Args:
            project_id: Unique identifier for the project
        """
        self.project_id = project_id
        self.client = chromadb.PersistentClient(path=str(config.CHROMA_DATA_DIR))
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction()
        
        # Get or create collection for this project
        self.collection = self.client.get_or_create_collection(
            name=f"project_{project_id}",
            embedding_function=self.embedding_function,
            metadata={"project_id": project_id}
        )
        
        logger.info(f"Initialized vector store for project: {project_id}")
    
    def index_project(self, project_dir: Path) -> int:
        """
        Index all code files in the project directory.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            Number of files indexed
        """
        logger.info(f"Indexing project directory: {project_dir}")
        
        # Get all files in the project
        files = list_files(project_dir)
        
        # Track number of files indexed
        indexed_count = 0
        
        # Process each file
        for file_path in files:
            try:
                # Get file contents
                content = get_file_contents(str(file_path))
                if content is None:
                    continue  # Skip binary files
                
                # Get relative path for ID
                rel_path = file_path.relative_to(project_dir)
                file_id = str(rel_path)
                
                # Create metadata
                metadata = {
                    "project_id": self.project_id,
                    "file_path": file_id,
                    "file_type": file_path.suffix,
                    "file_name": file_path.name
                }
                
                # Add to collection (upsert to handle updates)
                self.collection.upsert(
                    ids=[file_id],
                    documents=[content],
                    metadatas=[metadata]
                )
                
                indexed_count += 1
                
            except Exception as e:
                logger.error(f"Error indexing file {file_path}: {str(e)}")
        
        logger.info(f"Indexed {indexed_count} files for project {self.project_id}")
        return indexed_count
    
    def search(self, query: str, limit: int = 5, file_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant code snippets based on the query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            file_paths: Optional list of specific file paths to search in
            
        Returns:
            List of search results with documents and metadata
        """
        logger.info(f"Searching for: {query}")
        
        # Prepare where clause if file paths are specified
        where = None
        if file_paths:
            where = {"file_path": {"$in": file_paths}}
        
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where,
            include=["metadatas", "documents", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            formatted_results.append({
                "content": doc,
                "metadata": metadata,
                "relevance_score": 1.0 - (distance / 2.0)  # Convert distance to relevance score
            })
        
        return formatted_results 