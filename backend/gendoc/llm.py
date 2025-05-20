"""
LLM integration for the GenDoc service.
"""
import logging
from typing import Dict, List, Any, Optional

from litellm import completion
import litellm

from backend.gendoc import config
from shared.models import DocumentationType, DocumentationRequest, DocumentationResponse

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize LiteLLM with API keys from environment
if config.OPENAI_API_KEY:
    litellm.api_key = config.OPENAI_API_KEY


def get_prompt_for_doc_type(doc_type: DocumentationType, code_content: str, 
                           additional_context: Optional[Dict[str, Any]] = None,
                           custom_prompt: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Generate a prompt for the given documentation type.
    
    Args:
        doc_type: Type of documentation to generate
        code_content: The code content to document
        additional_context: Additional context for the prompt
        custom_prompt: Custom prompt text (overrides default)
        
    Returns:
        Formatted messages for the LLM
    """
    context = additional_context or {}
    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()]) if context else ""
    
    system_prompt = config.DEFAULT_SYSTEM_PROMPT
    
    # If custom prompt is provided, use it as the user message
    if custom_prompt:
        user_prompt = custom_prompt
    else:
        if doc_type == DocumentationType.OVERVIEW:
            user_prompt = (f"Please provide a comprehensive overview of this codebase. "
                          f"Focus on the main purpose, architecture, key components, "
                          f"and how they interact. Include information about design patterns used, "
                          f"dependencies, and the overall structure.\n\n"
                          f"Context:\n{context_str}\n\n"
                          f"Code:\n```\n{code_content}\n```")
        
        elif doc_type == DocumentationType.ARCHITECTURE:
            user_prompt = (f"Please analyze and document the architecture of this code. "
                          f"Focus on the structural organization, component relationships, "
                          f"data flow, and design patterns. Include diagrams if possible.\n\n"
                          f"Context:\n{context_str}\n\n"
                          f"Code:\n```\n{code_content}\n```")
        
        elif doc_type == DocumentationType.COMPONENT:
            user_prompt = (f"Please document this component/module. Describe its purpose, "
                          f"functionality, interface, dependencies, and usage examples.\n\n"
                          f"Context:\n{context_str}\n\n"
                          f"Code:\n```\n{code_content}\n```")
        
        elif doc_type == DocumentationType.FUNCTION:
            user_prompt = (f"Please document this function/method in detail. Include parameters, "
                          f"return values, exceptions, side effects, and usage examples.\n\n"
                          f"Context:\n{context_str}\n\n"
                          f"Code:\n```\n{code_content}\n```")
        
        elif doc_type == DocumentationType.API:
            user_prompt = (f"Please generate API documentation for this code. Include endpoints, "
                          f"request/response formats, authentication, error handling, and example calls.\n\n"
                          f"Context:\n{context_str}\n\n"
                          f"Code:\n```\n{code_content}\n```")
        
        else:  # Default or custom type
            user_prompt = (f"Please analyze and document this code. Focus on clarity, "
                          f"completeness, and technical accuracy.\n\n"
                          f"Context:\n{context_str}\n\n"
                          f"Code:\n```\n{code_content}\n```")
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def generate_documentation(request: DocumentationRequest, code_content: str) -> DocumentationResponse:
    """
    Generate documentation using LiteLLM.
    
    Args:
        request: Documentation request parameters
        code_content: The code content to document
        
    Returns:
        Documentation response with generated content
    """
    logger.info(f"Generating documentation type: {request.doc_type}")
    
    # Map the model name to LiteLLM format
    model_name = config.MODEL_MAPPING.get(request.model_name, request.model_name)
    
    # Prepare the messages for LLM
    messages = get_prompt_for_doc_type(
        request.doc_type,
        code_content,
        request.additional_context,
        request.custom_prompt
    )
    
    try:
        # Call LiteLLM for completion
        response = completion(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens or 4000
        )
        
        # Extract the generated documentation
        documentation = response.choices[0].message.content
        
        # Create the response
        doc_response = DocumentationResponse(
            project_id=request.project_id,
            documentation=documentation,
            doc_type=request.doc_type,
            file_path=request.file_path,
            token_usage=response.usage
        )
        
        return doc_response
        
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        raise 