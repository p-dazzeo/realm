import logging
from typing import Dict, Any, Optional, List
import json # Add json import
from pathlib import Path # Add Path import

import litellm
from litellm import completion # ensure completion is imported

from backend.gendoc import config as gendoc_config # gendoc's own config
from shared.models import DocumentationWorkflow, WorkflowStep, WorkflowInput # models needed
from fastapi import HTTPException # For error handling

logger = logging.getLogger(__name__)

# Ensure API keys are set for litellm if not already set globally elsewhere
# litellm.api_key = gendoc_config.OPENAI_API_KEY # Example for OpenAI
# litellm.anthropic_api_key = gendoc_config.ANTHROPIC_API_KEY # Example for Anthropic
# Add other provider keys as needed based on config

async def invoke_llm(
    prompt: str,
    system_prompt: str,
    model_name: str,
    temperature: float = 0.3, # Default temperature
    max_tokens: Optional[int] = None
) -> str:
    """
    Invokes the LLM using litellm.completion.
    """
    logger.info(f"Invoking LLM. Model: {model_name}, Temperature: {temperature}, Max Tokens: {max_tokens}")
    logger.debug(f"System Prompt: {system_prompt}")
    logger.debug(f"User Prompt: {prompt}")

    actual_model_name = gendoc_config.MODEL_MAPPING.get(model_name, model_name)
    logger.info(f"Actual model name being used: {actual_model_name}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        # Default max_tokens if not provided, or use the one from config
        effective_max_tokens = max_tokens or gendoc_config.DEFAULT_MAX_TOKENS

        response = await litellm.acompletion( # Use acompletion for async
            model=actual_model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=effective_max_tokens,
            # Add other parameters like top_p, presence_penalty, frequency_penalty if needed
        )
        
        # Validate response structure
        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            logger.error("LLM response is not in the expected format.")
            raise HTTPException(status_code=500, detail="LLM response format error.")

        content = response.choices[0].message.content
        # Log token usage if available
        if response.usage:
            logger.info(
                f"LLM call successful. Tokens used: Prompt={response.usage.prompt_tokens}, "
                f"Completion={response.usage.completion_tokens}, Total={response.usage.total_tokens}"
            )
        else:
            logger.info("LLM call successful. Token usage not available in response.")
        
        return content

    except HTTPException: # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error during LLM completion: {str(e)}", exc_info=True)
        # Check if it's an API key error
        if "auth" in str(e).lower() or "api key" in str(e).lower():
             raise HTTPException(status_code=500, detail=f"LLM API key error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating LLM response: {str(e)}")


async def execute_workflow(
    project_id: str,
    workflow: DocumentationWorkflow,
    model_name: str, # Added
    temperature: float, # Added
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Executes a documentation workflow.
    Loads manifest, resolves inputs for each step, calls LLM, and returns the final output.
    (Simplified first pass: no looping within steps)
    """
    logger.info(f"Executing workflow '{workflow.name}' for project '{project_id}'")
    if additional_params:
        logger.info(f"Additional parameters for workflow: {additional_params}")

    project_dir = gendoc_config.STORAGE_DIR / project_id
    manifest_path = project_dir / "manifest.json"

    if not manifest_path.exists():
        logger.error(f"Manifest file not found for project {project_id} at {manifest_path}")
        raise HTTPException(status_code=404, detail=f"manifest.json not found for project {project_id}")

    try:
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
        logger.info(f"Successfully loaded manifest.json for project {project_id}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding manifest.json for project {project_id}")
        raise HTTPException(status_code=400, detail="Invalid JSON in manifest.json")

    # Validate manifest variables
    if workflow.variables_from_manifest:
        for var_name in workflow.variables_from_manifest:
            if var_name not in manifest_data:
                logger.error(f"Required manifest variable '{var_name}' not found for workflow '{workflow.name}'")
                raise HTTPException(
                    status_code=400,
                    detail=f"Manifest is missing required variable '{var_name}' for workflow '{workflow.name}'"
                )

    step_outputs: Dict[str, Any] = {}

    for step in workflow.steps:
        logger.info(f"Executing step: {step.name}")
        inputs_for_prompt: Dict[str, Any] = {}

        for input_spec in step.inputs:
            resolved_value: Any = None
            logger.debug(f"Resolving input '{input_spec.name}' from source '{input_spec.source}' with identifier '{input_spec.identifier}'")
            try:
                if input_spec.source == 'manifest':
                    resolved_value = manifest_data.get(input_spec.identifier)
                    if resolved_value is None:
                        raise ValueError(f"Manifest key '{input_spec.identifier}' not found.")
                elif input_spec.source == 'file_content':
                    file_to_read = project_dir / input_spec.identifier
                    if not file_to_read.exists():
                        raise ValueError(f"File '{input_spec.identifier}' not found in project.")
                    with open(file_to_read, "r", encoding='utf-8') as f: # Specify encoding
                        resolved_value = f.read()
                elif input_spec.source == 'step_output':
                    resolved_value = step_outputs.get(input_spec.identifier)
                    if resolved_value is None:
                        raise ValueError(f"Output from step '{input_spec.identifier}' not found.")
                elif input_spec.source == 'project_file_path':
                    # This source provides the relative path string of a file
                    # Assuming identifier is the path relative to project_dir
                    file_path_obj = project_dir / input_spec.identifier
                    if not file_path_obj.exists() or not file_path_obj.is_file():
                         raise ValueError(f"Project file '{input_spec.identifier}' not found or is not a file.")
                    resolved_value = input_spec.identifier # The relative path string
                elif input_spec.source == 'literal':
                    resolved_value = input_spec.identifier
                elif input_spec.source == 'runtime_param':
                    if additional_params:
                        resolved_value = additional_params.get(input_spec.identifier)
                    if resolved_value is None:
                        raise ValueError(f"Runtime parameter '{input_spec.identifier}' not found or not provided.")
                else:
                    raise ValueError(f"Unknown input source: {input_spec.source}")
                
                inputs_for_prompt[input_spec.name] = resolved_value
                logger.debug(f"Resolved input '{input_spec.name}' to: {str(resolved_value)[:100]}...") # Log snippet

            except ValueError as e:
                logger.error(f"Error resolving input '{input_spec.name}' for step '{step.name}': {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error resolving input '{input_spec.name}' for step '{step.name}': {str(e)}")

        # Format the prompt
        try:
            formatted_prompt = step.prompt.format(**inputs_for_prompt)
            logger.debug(f"Formatted prompt for step '{step.name}': {formatted_prompt[:200]}...")
        except KeyError as e:
            logger.error(f"Prompt formatting error for step '{step.name}': Missing key {str(e)}")
            raise HTTPException(status_code=400, detail=f"Prompt for step '{step.name}' is missing variable: {str(e)}")

        # Determine system prompt
        current_system_prompt = step.system_prompt or workflow.system_prompt or gendoc_config.DEFAULT_SYSTEM_PROMPT
        
        # Model and temperature are now passed to execute_workflow

        # Call LLM
        llm_output = await invoke_llm(
            prompt=formatted_prompt,
            system_prompt=current_system_prompt,
            model_name=model_name, # Use passed model_name
            temperature=temperature, # Use passed temperature
            max_tokens=gendoc_config.DEFAULT_MAX_TOKENS # Using default from config
        )
        step_outputs[step.name] = llm_output
        logger.info(f"Step '{step.name}' executed successfully. Output stored.")

    # Return the output of the last step, or as defined by the workflow (future enhancement)
    if not workflow.steps:
        logger.warning(f"Workflow '{workflow.name}' has no steps.")
        return "Workflow has no steps."
    
    last_step_name = workflow.steps[-1].name
    final_output = step_outputs.get(last_step_name, "")
    logger.info(f"Workflow '{workflow.name}' executed successfully. Returning output from last step '{last_step_name}'.")
    return final_output
