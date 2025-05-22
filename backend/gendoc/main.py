"""
Main FastAPI application for the GenDoc service.
"""
import os
import json # Added
import logging
from pathlib import Path
from typing import Dict, Any, List # Added List

from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Form, APIRouter # Added APIRouter
from fastapi.middleware.cors import CORSMiddleware

from backend.gendoc import config
from backend.gendoc.llm import generate_documentation
from shared.models import DocumentationRequest, DocumentationResponse, DocumentationWorkflow # Added DocumentationWorkflow
from shared.utils import extract_zip, get_file_contents, list_files

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Set higher log levels for noisy libraries
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('litellm').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)

# Initialize FastAPI app
app = FastAPI(
    title="REALM GenDoc Service",
    description="Documentation generation service for REALM",
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


@app.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Welcome to the REALM GenDoc Service API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/projects")
async def list_projects():
    """
    List all available projects.
    
    Returns:
        List of project objects with id and description
    """
    logger.info("Listing all projects")
    
    try:
        projects = []
        
        # Get all directories in the storage directory
        for item in config.STORAGE_DIR.iterdir():
            if item.is_dir():
                project_id = item.name
                description = None
                
                # Try to read metadata if it exists
                metadata_path = item / "metadata.txt"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r") as f:
                            metadata_lines = f.readlines()
                            for line in metadata_lines:
                                if line.startswith("description:"):
                                    description = line.split("description:", 1)[1].strip()
                                    break
                    except Exception as e:
                        logger.warning(f"Could not read metadata for project {project_id}: {str(e)}")
                
                # Add project to the list
                projects.append({
                    "id": project_id,
                    "description": description
                })
        
        return {"projects": projects}
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing projects: {str(e)}")


@app.post("/generate", response_model=DocumentationResponse)
async def generate(request: DocumentationRequest):
    """
    Generate documentation based on the request.
    
    Args:
        request: Documentation generation parameters
        
    Returns:
        Generated documentation
    """
    logger.info(f"Received documentation request for project: {request.project_id}")
    
    # Check if project directory exists
    project_dir = config.STORAGE_DIR / request.project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {request.project_id} not found")
    
    # Get the file content if a specific file is requested
    if request.file_path:
        file_path = project_dir / request.file_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {request.file_path} not found")
        
        code_content = get_file_contents(str(file_path))
        if code_content is None:
            raise HTTPException(status_code=400, detail=f"Could not read file {request.file_path}")
    else:
        # If no specific file, combine a representative set of files (for project-level documentation)
        code_content = ""
        file_count = 0
        for root, _, files in os.walk(project_dir):
            for file in files:
                file_path = Path(root) / file
                if file_count >= 10:  # Limit to 10 files for overview
                    break
                    
                content = get_file_contents(str(file_path))
                if content is not None:
                    rel_path = file_path.relative_to(project_dir)
                    code_content += f"\n\n# File: {rel_path}\n\n{content}"
                    file_count += 1
    
    # Generate documentation
    try:
        response = generate_documentation(request, code_content)
        return response
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating documentation: {str(e)}")


@app.post("/upload")
async def upload_project(
    project_id: str = Form(...), 
    project_file: UploadFile = File(...),
    description: str = Form(None)
):
    """
    Upload a project zip file.
    
    Args:
        project_id: Unique identifier for the project
        project_file: ZIP file containing the project
        description: Optional project description
        
    Returns:
        Upload status
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
        
        return {
            "status": "success",
            "project_id": project_id,
            "message": f"Project uploaded and extracted to {extract_dir}"
        }
    
    except Exception as e:
        logger.error(f"Error uploading project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading project: {str(e)}")


@app.get("/projects/{project_id}/files")
async def list_project_files(project_id: str):
    """
    List all files in a project.
    
    Args:
        project_id: Unique identifier for the project
        
    Returns:
        List of file paths in the project
    """
    logger.info(f"Listing files for project: {project_id}")
    
    # Check if project directory exists
    project_dir = config.STORAGE_DIR / project_id
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    try:
        # Get all files
        files = list_files(project_dir)
        
        # Convert to relative paths
        relative_files = [str(f.relative_to(project_dir)) for f in files]
        
        # Sort files alphabetically for better UX
        relative_files.sort()
        
        return {"files": relative_files}
        
    except Exception as e:
        logger.error(f"Error listing project files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing project files: {str(e)}")


# --- Workflow Management Router ---

# Ensure the _workflows directory exists
workflows_dir = config.STORAGE_DIR / "_workflows"
workflows_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Workflows directory ensured at: {workflows_dir}")

workflow_router = APIRouter()

@workflow_router.get("/", response_model=List[DocumentationWorkflow])
async def list_workflows():
    """
    List all available documentation workflows.
    """
    logger.info("Received request to list all workflows")
    workflows = []
    if not workflows_dir.exists():
        logger.warning(f"Workflows directory {workflows_dir} not found.")
        return workflows

    for item in workflows_dir.iterdir():
        if item.is_file() and item.suffix == ".json":
            try:
                with open(item, "r") as f:
                    data = json.load(f)
                    workflows.append(DocumentationWorkflow(**data))
            except json.JSONDecodeError:
                logger.warning(f"Could not parse workflow file: {item.name}")
            except Exception as e: # Catch other pydantic validation errors etc.
                logger.warning(f"Error loading workflow {item.name}: {str(e)}")
    return workflows

@workflow_router.get("/{workflow_name}", response_model=DocumentationWorkflow)
async def get_workflow(workflow_name: str):
    """
    Retrieve a specific documentation workflow by its name.
    """
    logger.info(f"Received request to get workflow: {workflow_name}")
    workflow_file_path = workflows_dir / f"{workflow_name}.json"

    if not workflow_file_path.exists():
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found.")
    
    try:
        with open(workflow_file_path, "r") as f:
            data = json.load(f)
            return DocumentationWorkflow(**data)
    except json.JSONDecodeError:
        logger.error(f"Could not parse workflow file: {workflow_file_path}")
        raise HTTPException(status_code=500, detail="Error parsing workflow file.")
    except Exception as e:
        logger.error(f"Error loading workflow {workflow_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not load workflow: {str(e)}")

# Include the workflow router in the main FastAPI application
app.include_router(workflow_router, prefix="/workflows", tags=["Workflows"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT) 