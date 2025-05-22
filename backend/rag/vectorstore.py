"""
Vector store operations for the RAG service.
"""
import logging
import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

from backend.rag import config
from shared.utils import get_file_contents, list_files

# Configure logging with the numeric level from config
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
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
        
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.OPENAI_API_KEY,
            model_name="text-embedding-3-small"
        )
        
        collection_name = f"project_{project_id}"
        
        # Check if collection exists and handle embedding function mismatch
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection for project: {project_id}")
            
            collection_count = self.collection.count()
            logger.debug(f"Collection '{collection_name}' contains {collection_count} documents")
            
        except Exception as e:
            # If there's an embedding function mismatch or other error, delete and recreate
            if "Embedding function name mismatch" in str(e):
                logger.warning(f"Embedding function mismatch detected for {collection_name}, recreating collection")
                try:
                    self.client.delete_collection(name=collection_name)
                    logger.info(f"Deleted collection {collection_name} due to embedding function mismatch")
                except Exception as del_e:
                    logger.error(f"Error deleting collection: {str(del_e)}")
            
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"project_id": project_id}
            )
            logger.info(f"Created new collection for project: {project_id}")
        
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
        logger.debug(f"Found {len(files)} files to process")
        
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
                
                # Debug log the file being indexed
                logger.debug(f"Indexing file: {file_id} ({len(content)} chars)")
                
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
        
        # Debug log search parameters
        logger.debug(f"Search parameters - limit: {limit}, file_paths: {file_paths}")
        
        # Prepare where clause if file paths are specified
        where = None
        if file_paths:
            where = {"file_path": {"$in": file_paths}}
            logger.debug(f"Using where clause: {where}")
        
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where,
            include=["metadatas", "documents", "distances"]
        )
        
        # Debug log raw results
        logger.debug(f"Raw query results - Found {len(results['documents'][0])} documents")
        
        # Format results
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            relevance_score = 1.0 - (distance / 2.0)  # Convert distance to relevance score   
            
            # Add to formatted results (without the truncation for actual result)
            formatted_results.append({
                "content": doc,
                "metadata": metadata,
                "relevance_score": relevance_score
            })
        
        return formatted_results 