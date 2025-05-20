"""
Main FastAPI application for the RAG service.
"""
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.rag import config
from backend.rag.vectorstore import CodeVectorStore
from backend.rag.llm import generate_rag_response
from shared.models import RAGRequest, RAGResponse
from shared.utils import extract_zip

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="REALM RAG Service",
    description="Retrieval-Augmented Generation service for REALM",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store vector store instances
vector_stores = {}


def get_vector_store(project_id: str) -> CodeVectorStore:
    """
    Get or create a vector store for a project.
    
    Args:
        project_id: Unique identifier for the project
        
    Returns:
        Vector store instance
    """
    if project_id not in vector_stores:
        vector_stores[project_id] = CodeVectorStore(project_id)
    
    return vector_stores[project_id]


@app.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Welcome to the REALM RAG Service API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/query", response_model=RAGResponse)
async def query(
    request: RAGRequest,
    vector_store: CodeVectorStore = Depends(get_vector_store)
):
    """
    Query the RAG system with a question.
    
    Args:
        request: RAG request parameters
        vector_store: Vector store for the project
        
    Returns:
        RAG response with answer and sources
    """
    logger.info(f"Received RAG query: {request.query}")
    
    try:
        # Search for relevant context
        context_docs = vector_store.search(
            query=request.query,
            limit=request.limit,
            file_paths=request.file_paths
        )
        
        if not context_docs:
            return RAGResponse(
                answer="I couldn't find any relevant information in the codebase to answer your question.",
                sources=[]
            )
        
        # Generate response with RAG
        response = generate_rag_response(request, context_docs)
        return response
        
    except Exception as e:
        logger.error(f"Error processing RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing RAG query: {str(e)}")


@app.post("/index")
async def index_project(project_id: str):
    """
    Index or reindex a project.
    
    Args:
        project_id: Unique identifier for the project
        
    Returns:
        Indexing status
    """
    logger.info(f"Indexing project: {project_id}")
    
    # Check if project directory exists
    project_dir = config.STORAGE_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    try:
        # Get or create vector store
        vector_store = get_vector_store(project_id)
        
        # Index the project
        indexed_count = vector_store.index_project(project_dir)
        
        return {
            "status": "success",
            "project_id": project_id,
            "indexed_files": indexed_count,
            "message": f"Successfully indexed {indexed_count} files"
        }
        
    except Exception as e:
        logger.error(f"Error indexing project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error indexing project: {str(e)}")


@app.post("/upload")
async def upload_project(
    project_id: str = Form(...), 
    project_file: UploadFile = File(...),
    description: str = Form(None),
    index_immediately: bool = Form(True)
):
    """
    Upload and optionally index a project zip file.
    
    Args:
        project_id: Unique identifier for the project
        project_file: ZIP file containing the project
        description: Optional project description
        index_immediately: Whether to index the project immediately after upload
        
    Returns:
        Upload and indexing status
    """
    logger.info(f"Uploading project: {project_id}")
    
    # Verify it's a zip file
    if not project_file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    # Create project directory
    project_dir = config.STORAGE_DIR / project_id
    
    try:
        # Extract the zip file - make sure to await the async function
        extract_dir = await extract_zip(project_file, str(project_dir))
        
        # Save metadata
        metadata = {
            "project_id": project_id,
            "original_filename": project_file.filename,
            "description": description
        }
        
        metadata_path = project_dir / "metadata.txt"
        with open(metadata_path, "w") as f:
            for key, value in metadata.items():
                if value:
                    f.write(f"{key}: {value}\n")
        
        result = {
            "status": "success",
            "project_id": project_id,
            "upload_message": f"Project uploaded and extracted to {extract_dir}"
        }
        
        # Index the project if requested
        if index_immediately:
            vector_store = get_vector_store(project_id)
            indexed_count = vector_store.index_project(project_dir)
            result["indexed_files"] = indexed_count
            result["index_message"] = f"Successfully indexed {indexed_count} files"
        
        return result
        
    except Exception as e:
        logger.error(f"Error uploading project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading project: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT) 