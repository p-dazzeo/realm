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
from backend.gendoc.llm import generate_single_file_documentation, process_manifest_group # Updated import
from shared.models import DocumentationRequest, DocumentationResponse, DocumentationWorkflow, DocumentationType # Added DocumentationWorkflow and DocumentationType
from shared.utils import extract_zip, get_file_contents, list_files

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

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
        
        # Generate documentation for a single specified file
        try:
            response = generate_single_file_documentation(request, code_content)
            return response
        except Exception as e:
            logger.error(f"Error generating documentation for file {request.file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating documentation for file: {str(e)}")
    else:
        # Project-level or multi-file documentation request
        manifest_path = project_dir / "manifest.json"
        if manifest_path.exists():
            logger.info(f"Found manifest.json for project {request.project_id}")
            try:
                with open(manifest_path, "r") as f:
                    manifest_data = json.load(f)
                
                # Initialize shared variables for aggregated response
                aggregated_docs_content = []
                cumulative_token_usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                processed_manifest_type = "unknown" # Will be updated based on detection

                # --- Enhanced Relationship Manifest (v1.1) Detection ---
                if manifest_data.get("manifest_version") == "1.1" and isinstance(manifest_data.get("processing_groups"), list):
                    processed_manifest_type = "enhanced_v1.1"
                    logger.info(f"Processing enhanced relationship manifest (v1.1) for project {request.project_id}")
                    
                    processing_groups = manifest_data.get("processing_groups", [])
                    processed_group_ids = []

                    for group in processing_groups:
                        if not isinstance(group, dict) or "primary_file" not in group:
                            logger.warning(f"Skipping invalid group in manifest: {group}. Missing 'primary_file'.")
                            continue
                        
                        primary_file_path_str = group["primary_file"]
                        primary_file_full_path = project_dir / primary_file_path_str
                        
                        if not primary_file_full_path.exists():
                            logger.warning(f"Primary file {primary_file_path_str} from group {group.get('group_id', 'N/A')} not found. Skipping group.")
                            aggregated_docs_content.append(f"\n\n---\nGroup: {group.get('group_id', 'N/A')} (Primary File: {primary_file_path_str}) - SKIPPED (Primary file not found)\n---")
                            continue

                        primary_file_content = get_file_contents(str(primary_file_full_path))
                        if primary_file_content is None:
                            logger.warning(f"Could not read content of primary file {primary_file_path_str} from group {group.get('group_id', 'N/A')}. Skipping group.")
                            aggregated_docs_content.append(f"\n\n---\nGroup: {group.get('group_id', 'N/A')} (Primary File: {primary_file_path_str}) - SKIPPED (Could not read primary file)\n---")
                            continue

                        related_files_content = []
                        for rf_info in group.get("related_files", []):
                            if not isinstance(rf_info, dict) or "path" not in rf_info or "role" not in rf_info:
                                logger.warning(f"Skipping invalid related_file entry in group {group.get('group_id', 'N/A')}: {rf_info}")
                                continue
                            
                            related_file_path = project_dir / rf_info["path"]
                            if not related_file_path.exists():
                                logger.warning(f"Related file {rf_info['path']} from group {group.get('group_id', 'N/A')} not found. Skipping.")
                                continue
                            
                            rf_content = get_file_contents(str(related_file_path))
                            if rf_content is not None:
                                related_files_content.append({
                                    "path": rf_info["path"],
                                    "role": rf_info["role"],
                                    "content": rf_content
                                })
                            else:
                                logger.warning(f"Could not read content of related file {rf_info['path']} from group {group.get('group_id', 'N/A')}. Skipping.")

                        additional_context_for_group = {
                            "group_id": group.get("group_id"),
                            "group_type": group.get("group_type"),
                            "group_description": group.get("group_description"),
                            "group_specific_context": group.get("group_specific_context"),
                            "project_context": manifest_data.get("project_context"), # Project-level context from manifest
                            "related_files": related_files_content
                        }
                        
                        # Merge with original request's additional_context if any, prioritizing group-specific
                        final_additional_context = {**(request.additional_context or {}), **additional_context_for_group}

                        group_specific_request = DocumentationRequest(
                            project_id=request.project_id,
                            file_path=primary_file_path_str, # Primary file for this group
                            doc_type=request.doc_type, # Original doc_type, or could be group-specific
                            model_name=request.model_name,
                            temperature=request.temperature,
                            max_tokens=request.max_tokens,
                            custom_prompt=group.get("custom_prompt_for_group") or request.custom_prompt, # Group can override
                            additional_context=final_additional_context,
                            workflow=request.workflow, # Pass workflow if provided (could also be group-specific)
                            workflow_type=request.workflow_type
                        )

                        try:
                            response_for_group = process_manifest_group(group_specific_request, primary_file_content)
                            doc_title = f"Group: {group.get('group_id', 'N/A')} (Primary File: {primary_file_path_str})"
                            aggregated_docs_content.append(f"\n\n---\n{doc_title}\n---\n\n{response_for_group.documentation}")
                            
                            if response_for_group.token_usage:
                                cumulative_token_usage["prompt_tokens"] += response_for_group.token_usage.get("prompt_tokens", 0)
                                cumulative_token_usage["completion_tokens"] += response_for_group.token_usage.get("completion_tokens", 0)
                                cumulative_token_usage["total_tokens"] += response_for_group.token_usage.get("total_tokens", 0)
                            processed_group_ids.append(group.get('group_id', primary_file_path_str))
                        except Exception as e:
                            logger.error(f"Error processing group {group.get('group_id', 'N/A')} (Primary: {primary_file_path_str}): {str(e)}")
                            aggregated_docs_content.append(f"\n\n---\nGroup: {group.get('group_id', 'N/A')} (Primary File: {primary_file_path_str}) - ERROR ({str(e)})\n---")
                    
                    return DocumentationResponse(
                        project_id=request.project_id,
                        documentation="".join(aggregated_docs_content),
                        doc_type=request.doc_type,
                        file_path=None,
                        metadata={
                            "processed_from_manifest": True,
                            "manifest_version_processed": "1.1",
                            "groups_processed": processed_group_ids,
                            "original_request_doc_type": request.doc_type.value
                        },
                        token_usage=cumulative_token_usage
                    )

                # --- Simple Order-Only Manifest (v1.0) Detection ---
                elif isinstance(manifest_data.get("files"), list):
                    processed_manifest_type = "simple_v1.0"
                    logger.info(f"Processing simple order-only manifest (v1.0) for project {request.project_id}")
                    
                    processed_files_from_manifest = []
                    for file_in_manifest in manifest_data["files"]:
                        current_file_path = project_dir / file_in_manifest
                        if not current_file_path.exists():
                            logger.warning(f"File {file_in_manifest} from manifest not found. Skipping.")
                            continue

                        file_content = get_file_contents(str(current_file_path))
                        if file_content is None:
                            logger.warning(f"Could not read content of file {file_in_manifest}. Skipping.")
                            continue
                        
                        processed_files_from_manifest.append(file_in_manifest)
                        file_specific_request = DocumentationRequest(
                            project_id=request.project_id, file_path=file_in_manifest,
                            doc_type=request.doc_type, model_name=request.model_name,
                            temperature=request.temperature, max_tokens=request.max_tokens,
                            custom_prompt=request.custom_prompt, additional_context=request.additional_context,
                            workflow=request.workflow, workflow_type=request.workflow_type
                        )
                        try:
                            response_for_file = generate_single_file_documentation(file_specific_request, file_content)
                            aggregated_docs_content.append(f"\n\n---\nFile: {file_in_manifest}\n---\n\n{response_for_file.documentation}")
                            if response_for_file.token_usage:
                                cumulative_token_usage["prompt_tokens"] += response_for_file.token_usage.get("prompt_tokens", 0)
                                cumulative_token_usage["completion_tokens"] += response_for_file.token_usage.get("completion_tokens", 0)
                                cumulative_token_usage["total_tokens"] += response_for_file.token_usage.get("total_tokens", 0)
                        except Exception as e:
                            logger.error(f"Error generating documentation for file {file_in_manifest} (from manifest v1.0): {str(e)}")
                            aggregated_docs_content.append(f"\n\n---\nFile: {file_in_manifest}\n---\n\nError: {str(e)}")
                    
                    return DocumentationResponse(
                        project_id=request.project_id, documentation="".join(aggregated_docs_content),
                        doc_type=request.doc_type, file_path=None,
                        metadata={
                            "processed_from_manifest": True, "manifest_version_processed": "1.0",
                            "files_processed": processed_files_from_manifest,
                            "original_request_doc_type": request.doc_type.value
                        },
                        token_usage=cumulative_token_usage
                    )
                
                # --- Unrecognized Manifest Format ---
                else:
                    logger.warning(f"Unrecognized manifest.json format for project {request.project_id}. Proceeding to fallback summarization.")
                    # Fall through to the `else` block outside of `if manifest_path.exists()`

            except json.JSONDecodeError:
                # This specifically catches malformed JSON
                raise HTTPException(status_code=400, detail="Invalid manifest.json: Could not parse JSON.")
            # Other exceptions during manifest processing (e.g., unexpected structure not caught by specific checks)
            # will lead to a 500 error by the generic exception handler for the endpoint, or could be caught here.
            except Exception as e: # Catch any other manifest processing error before fallback
                logger.error(f"Error processing manifest.json for project {request.project_id}: {str(e)}. Proceeding to fallback summarization.")
                # Fall through to the `else` block by not returning a response here.
        
        # Fallback Logic: Either manifest_path does not exist OR manifest was unrecognized/errored before returning
        # This 'else' corresponds to 'if manifest_path.exists() and processed_manifest_type != "unknown"' (implicitly)
        # Or more accurately, if no response has been returned yet from manifest processing.
        
        # The following code will execute if:
        # 1. manifest_path does not exist.
        # 2. manifest_path exists, but its format was unrecognized (neither v1.1 groups nor v1.0 files).
        # 3. manifest_path exists, but an Exception occurred during its processing (other than JSONDecodeError, which raises HTTP 400).
        
        logger.info(f"No valid/recognized manifest processed for project {request.project_id}. Using fallback summarization.")
        code_content = ""
        file_count = 0
        # Limit which files are included for project overview to avoid excessive length
        # Prioritize common code files and exclude certain directories/files if necessary
        # This is a simplified approach; more sophisticated filtering might be needed
        excluded_dirs = {".git", "__pycache__", "node_modules", "venv", ".vscode"}
        excluded_extensions = {".log", ".tmp", ".bak", ".zip", ".gz", ".tar", ".DS_Store"} # etc.

        files_concatenated = []
        for root, dirs, files_in_dir in os.walk(project_dir):
            # Modify dirs in-place to exclude unwanted directories from os.walk
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            if file_count >= 10: break
            for file_name in files_in_dir:
                if file_count >= 10: break
                
                file_path_obj = Path(root) / file_name
                if any(part in excluded_dirs for part in file_path_obj.parts) or file_path_obj.suffix in excluded_extensions:
                    continue

                try:
                    content = get_file_contents(str(file_path_obj))
                    if content:
                        rel_path = file_path_obj.relative_to(project_dir)
                        code_content += f"\n\n# File: {str(rel_path)}\n\n{content}"
                        files_concatenated.append(str(rel_path))
                        file_count += 1
                except Exception as e:
                    logger.warning(f"Could not read or process file {file_path_obj} during fallback: {str(e)}")
        
        if not code_content:
                raise HTTPException(status_code=400, detail="No processable files found for project overview.")

        # Generate documentation using the concatenated content
        try:
            # The request here is the original request, which might have a specific doc_type
            # like OVERVIEW, which is appropriate for this concatenated content.
            fallback_request = request # Use the original request for fallback
            response = generate_single_file_documentation(fallback_request, code_content)
            # Add metadata about which files were included in this fallback mode
            if response.metadata:
                response.metadata["fallback_processed"] = True
                response.metadata["fallback_files_concatenated"] = files_concatenated
            else:
                response.metadata = {"fallback_processed": True, "fallback_files_concatenated": files_concatenated}
            return response
        except Exception as e:
            logger.error(f"Error generating documentation with fallback for project {request.project_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating documentation with fallback: {str(e)}")


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