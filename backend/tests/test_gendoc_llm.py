import pytest
from unittest.mock import patch, MagicMock

from backend.gendoc.llm import generate_documentation, execute_workflow
from backend.gendoc import config as gendoc_config # To allow patching config values
from shared.models import (
    DocumentationRequest,
    DocumentationWorkflow,
    WorkflowStep,
    DocumentationType,
    DocumentationResponse,
)

# --- Fixtures ---

@pytest.fixture
def sample_code_content():
    return "def hello():\n  print('Hello, world!')"

@pytest.fixture
def basic_workflow_step1_data():
    return {
        "name": "step1_summarize",
        "prompt": "Summarize this code: {code_content}",
        "inputs": ["code_content"],
        "output_type": "text"
    }

@pytest.fixture
def basic_workflow_step2_data():
    return {
        "name": "step2_elaborate",
        "prompt": "Elaborate on this summary: {step1_summarize_output}. Use context: {additional_context_detail}",
        "inputs": ["step1_summarize.output", "additional_context.detail"],
        "output_type": "text"
    }
    
@pytest.fixture
def sample_workflow_data(basic_workflow_step1_data, basic_workflow_step2_data):
    return {
        "name": "test_workflow",
        "description": "A simple test workflow",
        "steps": [basic_workflow_step1_data, basic_workflow_step2_data]
    }

@pytest.fixture
def sample_workflow(sample_workflow_data):
    return DocumentationWorkflow(**sample_workflow_data)

@pytest.fixture
def doc_request_with_workflow(sample_workflow, sample_code_content):
    return DocumentationRequest(
        project_id="test_project",
        file_path="test.py",
        doc_type=DocumentationType.CUSTOM,
        model_name="test_model",
        workflow=sample_workflow,
        additional_context={"detail": "some_detail_value"}
    )

@pytest.fixture
def doc_request_without_workflow(sample_code_content):
    return DocumentationRequest(
        project_id="test_project_no_workflow",
        file_path="test_no_workflow.py",
        doc_type=DocumentationType.OVERVIEW,
        model_name="test_model_standard"
    )

# --- Mocks ---

@pytest.fixture
def mock_litellm_completion():
    with patch('backend.gendoc.llm.completion') as mock_completion:
        # Default mock response for a single choice
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Mocked LLM response"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response.usage.model_dump = MagicMock(return_value={"prompt_tokens":10, "completion_tokens":20, "total_tokens":30})
        
        mock_completion.return_value = mock_response
        yield mock_completion

# --- Tests for execute_workflow ---

def test_execute_workflow_success(doc_request_with_workflow, sample_code_content, mock_litellm_completion):
    """Test successful execution of a simple workflow."""
    
    # Configure mock responses for each step
    mock_step1_output = "Summary of code."
    mock_step2_output = "Elaborated summary using some_detail_value."

    def side_effect_func(*args, **kwargs):
        messages = kwargs.get('messages', [])
        user_content = ""
        if messages:
            user_content = messages[-1].get('content', "")

        mock_resp = MagicMock()
        mock_msg = MagicMock()
        mock_usage = MagicMock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
        mock_usage.model_dump = MagicMock(return_value={"prompt_tokens":5, "completion_tokens":10, "total_tokens":15})
        mock_resp.usage = mock_usage
        mock_resp.choices = [MagicMock(message=mock_msg)]

        if "Summarize this code" in user_content:
            mock_msg.content = mock_step1_output
        elif "Elaborate on this summary" in user_content:
            mock_msg.content = mock_step2_output
        else:
            mock_msg.content = "Default mock output"
        return mock_resp

    mock_litellm_completion.side_effect = side_effect_func

    response = execute_workflow(doc_request_with_workflow, sample_code_content)

    assert isinstance(response, DocumentationResponse)
    assert response.project_id == doc_request_with_workflow.project_id
    assert response.documentation == mock_step2_output # Output of the last step
    assert response.doc_type == DocumentationType.CUSTOM
    assert response.metadata["workflow_name"] == doc_request_with_workflow.workflow.name
    assert response.token_usage["total_tokens"] == 30 # 15 per step * 2 steps

    # Verify litellm.completion was called for each step
    assert mock_litellm_completion.call_count == 2
    
    # Check prompt for step 1
    args_step1, kwargs_step1 = mock_litellm_completion.call_args_list[0]
    prompt_step1 = kwargs_step1['messages'][-1]['content']
    assert sample_code_content in prompt_step1
    
    # Check prompt for step 2
    args_step2, kwargs_step2 = mock_litellm_completion.call_args_list[1]
    prompt_step2 = kwargs_step2['messages'][-1]['content']
    assert mock_step1_output in prompt_step2 # Output of step 1
    assert "some_detail_value" in prompt_step2 # From additional_context

def test_execute_workflow_input_key_error(doc_request_with_workflow, sample_code_content, mock_litellm_completion):
    """Test workflow execution when a step's prompt formatting fails due to a missing key."""
    # Step 2's prompt will refer to '{a_truly_missing_key}'
    # but 'a_truly_missing_key' will NOT be in step2's 'inputs' list.
    # This ensures that current_inputs used for .format() will not have 'a_truly_missing_key'.
    original_step2_inputs = doc_request_with_workflow.workflow.steps[1].inputs.copy()
    doc_request_with_workflow.workflow.steps[1].prompt = (
        "Elaborate on {step1_summarize_output} and also use {a_truly_missing_key}"
    )
    # Ensure 'a_truly_missing_key' is NOT in the inputs list for the step model
    # It was already not there, so no change to inputs needed for this specific key.
    # We are testing that .format() fails, not that our input resolution logic fails.

    mock_step1_output = "Summary of code from step 1."
    
    # Set up side effect for litellm.completion
    # It should only be called for step 1. Step 2 should fail before the LLM call.
    def side_effect_for_key_error_test(*args, **kwargs):
        messages = kwargs.get('messages', [])
        user_content = messages[-1].get('content', "") if messages else ""
        
        mock_resp = MagicMock()
        mock_msg = MagicMock()
        mock_usage = MagicMock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
        mock_usage.model_dump = MagicMock(return_value={"prompt_tokens":5, "completion_tokens":10, "total_tokens":15})
        mock_resp.usage = mock_usage
        mock_resp.choices = [MagicMock(message=mock_msg)]

        if "Summarize this code" in user_content: # Step 1
            mock_msg.content = mock_step1_output
            return mock_resp
        # Step 2 should not reach here if KeyError is handled correctly
        raise AssertionError("LLM completion should not be called for step 2 in this test.")

    mock_litellm_completion.side_effect = side_effect_for_key_error_test
    
    response = execute_workflow(doc_request_with_workflow, sample_code_content)

    # Assertions
    assert mock_litellm_completion.call_count == 1 # Only step 1 should call LLM
    assert "Error formatting prompt for step step2_elaborate" in response.documentation
    assert "Missing key 'a_truly_missing_key'" in response.documentation
    assert response.metadata["workflow_name"] == doc_request_with_workflow.workflow.name
    assert response.token_usage["total_tokens"] == 15 # Only from step 1
    
    # Restore original inputs for other tests if fixture is session/module scoped (though it's function scoped here)
    doc_request_with_workflow.workflow.steps[1].inputs = original_step2_inputs

def test_execute_workflow_llm_failure_in_step(doc_request_with_workflow, sample_code_content, mock_litellm_completion):
    """Test workflow execution when an LLM call fails during a step."""
    
    def side_effect_func(*args, **kwargs):
        messages = kwargs.get('messages', [])
        user_content = messages[-1]['content'] if messages else ""

        if "Summarize this code" in user_content: # Step 1 succeeds
            mock_resp_step1 = MagicMock()
            mock_msg_step1 = MagicMock(content="Step 1 output")
            mock_resp_step1.choices = [MagicMock(message=mock_msg_step1)]
            mock_resp_step1.usage = MagicMock(prompt_tokens=1, completion_tokens=1, total_tokens=2, model_dump=lambda: {"prompt_tokens":1, "completion_tokens":1, "total_tokens":2})
            return mock_resp_step1
        elif "Elaborate on this summary" in user_content: # Step 2 fails
            raise Exception("Simulated LLM API error")
        return MagicMock() # Default

    mock_litellm_completion.side_effect = side_effect_func
    
    response = execute_workflow(doc_request_with_workflow, sample_code_content)

    assert mock_litellm_completion.call_count == 2 # Both steps attempted
    assert "Error during LLM call for step step2_elaborate: Simulated LLM API error" in response.documentation
    assert response.token_usage["total_tokens"] > 0 # From successful step 1

# --- Tests for generate_documentation ---

@patch('backend.gendoc.llm.execute_workflow')
def test_generate_documentation_delegates_to_execute_workflow(mock_execute_workflow, doc_request_with_workflow, sample_code_content):
    """Verify generate_documentation calls execute_workflow when a workflow is provided."""
    mock_execute_workflow.return_value = MagicMock(spec=DocumentationResponse)
    
    generate_documentation(doc_request_with_workflow, sample_code_content)
    
    mock_execute_workflow.assert_called_once_with(doc_request_with_workflow, sample_code_content)

@patch('backend.gendoc.llm.get_prompt_for_doc_type')
@patch('backend.gendoc.llm.completion') # Also mock completion for the standard path
def test_generate_documentation_uses_standard_path_no_workflow(
    mock_completion, # Order matters for mock fixtures
    mock_get_prompt, 
    doc_request_without_workflow, 
    sample_code_content
):
    """Verify generate_documentation uses get_prompt_for_doc_type when no workflow is provided."""
    
    # Mock for get_prompt_for_doc_type
    mock_get_prompt.return_value = [{"role": "system", "content": "sys"}, {"role": "user", "content": "user"}]
    
    # Mock for litellm.completion (standard path)
    mock_llm_response = MagicMock()
    mock_llm_message = MagicMock(content="Standard LLM response")
    mock_llm_response.choices = [MagicMock(message=mock_llm_message)]
    mock_llm_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_llm_response.usage.model_dump = MagicMock(return_value={"prompt_tokens":10, "completion_tokens":20, "total_tokens":30})
    mock_completion.return_value = mock_llm_response
    
    # Patch gendoc_config.DEFAULT_MAX_TOKENS if it's not already set or needs a specific test value
    with patch.object(gendoc_config, 'DEFAULT_MAX_TOKENS', 2048):
        response = generate_documentation(doc_request_without_workflow, sample_code_content)

    mock_get_prompt.assert_called_once_with(
        doc_request_without_workflow.doc_type,
        sample_code_content,
        doc_request_without_workflow.additional_context,
        doc_request_without_workflow.custom_prompt
    )
    mock_completion.assert_called_once()
    assert response.documentation == "Standard LLM response"

pytest.main()
