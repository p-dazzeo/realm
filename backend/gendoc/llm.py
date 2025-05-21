"""
LLM integration for the GenDoc service.
"""
import logging
from typing import Dict, List, Any, Optional

from litellm import completion
import litellm

from backend.gendoc import config
from shared.models import (
    DocumentationType,
    DocumentationRequest,
    DocumentationResponse
)

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
    Generate a prompt for the given documentation type (for non-workflow requests).
    
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
    logger.info(f"Generating documentation for project: {request.project_id}, file: {request.file_path}")

    # If a workflow is provided directly, use it
    if request.workflow:
        logger.info(f"Using provided workflow: {request.workflow.name} (Type: {request.workflow_type or request.workflow.doc_type.value})")
        return execute_workflow(request, code_content)
    
    # Otherwise, try to find a default workflow for the requested doc_type
    try:
        # Look for a standard workflow for this doc_type
        workflows_dir = config.STORAGE_DIR / "_workflows"
        workflow_file = workflows_dir / f"{request.doc_type.value}-standard.json"
        
        if workflow_file.exists():
            # Load the workflow
            with open(workflow_file, "r") as f:
                import json
                workflow_data = json.load(f)
                from shared.models import DocumentationWorkflow
                standard_workflow = DocumentationWorkflow(**workflow_data)
                
                # Update the request with the workflow and execute it
                request.workflow = standard_workflow
                request.workflow_type = request.doc_type.value
                logger.info(f"Using standard workflow for {request.doc_type.value}")
                return execute_workflow(request, code_content)
        
        # No workflow found, fall back to the classic approach
        logger.info(f"No workflow found for {request.doc_type.value}, using classic approach")
        
    except Exception as e:
        logger.warning(f"Error loading workflow for {request.doc_type.value}: {str(e)}")
        logger.info("Falling back to classic documentation approach")
    
    # Fall back to the classic approach using a single prompt
    logger.info(f"Using standard documentation type: {request.doc_type}")
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
            max_tokens=request.max_tokens or config.DEFAULT_MAX_TOKENS
        )
        
        # Extract the generated documentation
        documentation = response.choices[0].message.content
        
        # Create the response
        doc_response = DocumentationResponse(
            project_id=request.project_id,
            documentation=documentation,
            doc_type=request.doc_type,
            file_path=request.file_path,
            token_usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage # Ensure usage is dict
        )
        
        return doc_response
        
    except Exception as e:
        logger.error(f"Error generating standard documentation: {str(e)}")
        raise


def execute_workflow(request: DocumentationRequest, code_content: str) -> DocumentationResponse:
    """
    Execute a documentation workflow.
    
    Args:
        request: Documentation request parameters with workflow
        code_content: The initial code content for the workflow
        
    Returns:
        Documentation response with the final workflow output
    """
    if not request.workflow:
        raise ValueError("Workflow not provided in the request.")

    logger.info(f"Executing workflow: {request.workflow.name}")
    
    step_outputs: Dict[str, Any] = {}
    cumulative_token_usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    # Initial context for workflow
    workflow_context: Dict[str, Any] = {
        "code_content": code_content,
        "additional_context": request.additional_context or {}
    }

    final_documentation = ""

    for step_index, step in enumerate(request.workflow.steps):
        logger.info(f"Executing workflow step: {step.name}")
        
        # Construct prompt for the current step
        prompt_content = step.prompt
        
        # Replace placeholders in prompt_content
        # Example: "Summarize this: {code_content}" or "Elaborate on: {previous_step_name.output}"
        # A more robust templating engine might be needed for complex cases.
        current_inputs = {}
        for input_key in step.inputs:
            # Sanitize input keys for use in str.format() by replacing dots with underscores
            # The prompt templates should use underscores, e.g., {step1_output} or {additional_context_detail}
            sanitized_key = input_key.replace(".", "_")

            if input_key == "code_content":
                current_inputs[sanitized_key] = workflow_context["code_content"]
            elif input_key.startswith("additional_context."):
                # e.g. additional_context.project_type
                # input_key here is like "additional_context.detail"
                # sanitized_key will be "additional_context_detail"
                actual_key_in_context = input_key.split("additional_context.", 1)[1]
                current_val = workflow_context["additional_context"]
                # Traverse if actual_key_in_context is nested e.g. "parent.child"
                for k_part in actual_key_in_context.split("."):
                    if isinstance(current_val, dict) and k_part in current_val:
                        current_val = current_val[k_part]
                    else:
                        current_val = None
                        logger.warning(f"Could not resolve input path {input_key} for step {step.name}")
                        break
                current_inputs[sanitized_key] = current_val

            elif ".output" in input_key: # refers to a previous step's output, e.g. "step1.output"
                                          # sanitized_key will be "step1_output"
                prev_step_name = input_key.split(".output")[0]
                if prev_step_name in step_outputs:
                    current_inputs[sanitized_key] = step_outputs[prev_step_name]
                else:
                    logger.error(f"Missing input '{input_key}' (sanitized: {sanitized_key}) for step '{step.name}'. Previous step '{prev_step_name}' not found or has no output.")
                    current_inputs[sanitized_key] = f"Error: Missing input {input_key}"
            else: # Default to looking in additional_context directly if not found elsewhere
                  # e.g. an input "simple_key" to be found in additional_context
                  # sanitized_key will be "simple_key"
                current_inputs[sanitized_key] = workflow_context["additional_context"].get(input_key)
                if current_inputs[sanitized_key] is None:
                    logger.warning(f"Input '{input_key}' (sanitized: {sanitized_key}) for step '{step.name}' not found in code_content, additional_context, or previous step outputs. Defaulting to empty string.")
                    current_inputs[sanitized_key] = "" # Provide empty string if not found

        formatted_prompt = None
        try:
            # Basic string formatting, consider more robust templating
            formatted_prompt = prompt_content.format(**current_inputs)
        except KeyError as e:
            error_msg = f"Error formatting prompt for step {step.name}: Missing key {e}"
            logger.error(error_msg)
            step_outputs[step.name] = error_msg
            if step_index == len(request.workflow.steps) - 1:
                final_documentation = error_msg
            continue # Skip LLM call for this step

        if formatted_prompt:
            messages = [
                {"role": "system", "content": config.DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": formatted_prompt}
            ]
            
            model_name = config.MODEL_MAPPING.get(request.model_name, request.model_name)
            
            try:
                response = completion(
                    model=model_name,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens or config.DEFAULT_MAX_TOKENS
                )
                
                step_output_content = response.choices[0].message.content
                step_outputs[step.name] = step_output_content
                
                if response.usage:
                    usage_data = response.usage.model_dump() if hasattr(response.usage, 'model_dump') else response.usage
                    cumulative_token_usage["prompt_tokens"] += usage_data.get("prompt_tokens", 0)
                    cumulative_token_usage["completion_tokens"] += usage_data.get("completion_tokens", 0)
                    cumulative_token_usage["total_tokens"] += usage_data.get("total_tokens", 0)

                logger.info(f"Step {step.name} completed. Output stored.")
                
                # The output of the last step is considered the final documentation
                if step_index == len(request.workflow.steps) - 1:
                    final_documentation = step_output_content
                    
            except Exception as e:
                error_msg = f"Error during LLM call for step {step.name}: {str(e)}"
                logger.error(error_msg)
                step_outputs[step.name] = error_msg
                if step_index == len(request.workflow.steps) - 1:
                    final_documentation = error_msg
        else: # Should not happen if logic is correct, but as a safeguard
            error_msg = f"Formatted prompt was not generated for step {step.name}."
            logger.error(error_msg)
            step_outputs[step.name] = error_msg
            if step_index == len(request.workflow.steps) - 1:
                final_documentation = error_msg


    doc_response = DocumentationResponse(
        project_id=request.project_id,
        documentation=final_documentation,
        doc_type=request.workflow.doc_type,  # Use the doc_type from the workflow
        file_path=request.file_path,
        metadata={"workflow_name": request.workflow.name, "workflow_type": request.workflow_type or "standard"},
        token_usage=cumulative_token_usage
    )
    
    return doc_response