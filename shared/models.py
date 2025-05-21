"""
Shared data models for REALM services.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class DocumentationType(str, Enum):
    """Types of documentation that can be generated."""
    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    COMPONENT = "component"
    FUNCTION = "function"
    API = "api"
    CUSTOM = "custom"


class DocumentationRequest(BaseModel):
    """Request model for documentation generation."""
    project_id: str = Field(..., description="Unique identifier for the project")
    file_path: Optional[str] = Field(None, description="Path to the specific file for documentation")
    doc_type: DocumentationType = Field(..., description="Type of documentation to generate")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for the LLM")
    model_name: str = Field("gpt-4", description="LLM model to use")
    temperature: float = Field(0.2, description="Temperature for LLM generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the LLM")
    workflow_type: Optional[str] = Field(None, description="Type of workflow to use for documentation generation")
    workflow: Optional['DocumentationWorkflow'] = Field(None, description="Custom workflow definition")


class WorkflowStep(BaseModel):
    """A single step in a documentation workflow."""
    name: str = Field(..., description="Name of the workflow step")
    prompt: str = Field(..., description="Prompt template for this step")
    inputs: List[str] = Field(..., description="Inputs required for this step, can refer to previous step outputs or context")
    output_type: str = Field("text", description="Expected output type for this step (e.g., 'text', 'json')")


class DocumentationWorkflow(BaseModel):
    """Defines a custom workflow for documentation generation."""
    name: str = Field(..., description="Name of the documentation workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    steps: List[WorkflowStep] = Field(..., description="List of steps in the workflow")


class DocumentationResponse(BaseModel):
    """Response model with generated documentation."""
    project_id: str
    documentation: str
    doc_type: DocumentationType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None


class RAGRequest(BaseModel):
    """Request model for the RAG service."""
    query: str = Field(..., description="The query to process")
    project_id: str = Field(..., description="Project identifier for context")
    file_paths: Optional[List[str]] = Field(None, description="Specific file paths to consider")
    limit: int = Field(5, description="Maximum number of context chunks to retrieve")
    model_name: str = Field("gpt-4", description="LLM model to use")


class RAGResponse(BaseModel):
    """Response model from the RAG service."""
    answer: str
    sources: List[Dict[str, Any]]
    token_usage: Optional[Dict[str, int]] = None 