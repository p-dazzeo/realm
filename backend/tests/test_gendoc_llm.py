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
        # Prompt keys now use underscores as per llm.py change
        "prompt": "Elaborate on this summary: {step1_summarize_output}. Use context: {additional_context_detail}",
        # Inputs in the model still use dots, sanitization happens in execute_workflow
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
        doc_type=DocumentationType.CUSTOM, # Does not matter when workflow is present
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

# pytest.main() # Usually commented out or removed for test suite runs

# --- Tests for process_manifest_group ---

from backend.gendoc.llm import process_manifest_group, DEFAULT_GROUP_WORKFLOW_FILE
from pathlib import Path # Required for Path.exists mocking

@pytest.fixture
def primary_code_content_sample():
    return "PRIMARY FILE CONTENT\ndef main():\n  pass"

@pytest.fixture
def group_doc_request_base(sample_code_content): # Use sample_code_content for consistency if needed elsewhere
    return DocumentationRequest(
        project_id="group_test_project",
        file_path="primary_doc.py", # Path to the primary file of the group
        doc_type=DocumentationType.COMPONENT, # Overall doc type for the request
        model_name="test_group_model",
        additional_context={
            "group_id": "test_group_001",
            "group_type": "python_component_group",
            "group_description": "A group of related Python files for a component.",
            "related_files": [
                {"path": "related1.py", "role": "utility", "content": "def util1(): pass"},
                {"path": "related2.py", "role": "helper", "content": "def helper_func(): pass"}
            ],
            "project_context": {"project_name": "MyOverallProject", "version": "1.2.0"},
            "group_specific_context": {"complexity": "high", "status": "beta"}
        }
        # workflow and workflow_type will be set by individual tests
    )

class TestProcessManifestGroup:

    @patch('backend.gendoc.llm.execute_workflow')
    def test_pmg_with_provided_workflow(self, mock_execute_workflow, group_doc_request_base, sample_workflow, primary_code_content_sample):
        request = group_doc_request_base.model_copy(deep=True)
        request.workflow = sample_workflow # Directly provide a workflow object
        
        mock_execute_workflow.return_value = MagicMock(spec=DocumentationResponse) # Ensure it returns a valid type

        process_manifest_group(request, primary_code_content_sample)

        mock_execute_workflow.assert_called_once()
        call_args = mock_execute_workflow.call_args[0]
        assert call_args[0].workflow == sample_workflow
        assert call_args[0] == request # The request object itself (with workflow)
        assert call_args[1] == primary_code_content_sample

    @patch('backend.gendoc.llm.execute_workflow')
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_pmg_with_workflow_type_loads_standard(self, mock_path_exists, mock_open, mock_execute_workflow, group_doc_request_base, sample_workflow_data, primary_code_content_sample):
        request = group_doc_request_base.model_copy(deep=True)
        request.workflow_type = "test_workflow_type" # This type should trigger loading

        # Simulate the standard workflow file existing
        workflow_file_path = gendoc_config.STORAGE_DIR / "_workflows" / f"{request.workflow_type}-standard.json"
        mock_path_exists.side_effect = lambda path: str(path) == str(workflow_file_path)
        
        # Mock open to return the content of this workflow
        mock_file_content = json.dumps(sample_workflow_data)
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
        
        mock_execute_workflow.return_value = MagicMock(spec=DocumentationResponse)

        process_manifest_group(request, primary_code_content_sample)

        mock_execute_workflow.assert_called_once()
        called_request = mock_execute_workflow.call_args[0][0]
        assert called_request.workflow is not None
        assert called_request.workflow.name == sample_workflow_data["name"]
        assert called_request.workflow_type == request.workflow_type # Should remain the specific type
        assert mock_execute_workflow.call_args[0][1] == primary_code_content_sample

    @patch('backend.gendoc.llm.execute_workflow')
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_pmg_with_failed_workflow_type_loads_generic(self, mock_path_exists, mock_open, mock_execute_workflow, group_doc_request_base, sample_workflow_data, primary_code_content_sample):
        request = group_doc_request_base.model_copy(deep=True)
        request.workflow_type = "nonexistent_type" # This specific type won't be found

        specific_workflow_path = gendoc_config.STORAGE_DIR / "_workflows" / f"{request.workflow_type}-standard.json"
        generic_workflow_path = gendoc_config.STORAGE_DIR / "_workflows" / DEFAULT_GROUP_WORKFLOW_FILE

        def path_exists_side_effect(path):
            if str(path) == str(specific_workflow_path): return False # Specific does not exist
            if str(path) == str(generic_workflow_path): return True   # Generic does exist
            return False
        mock_path_exists.side_effect = path_exists_side_effect
        
        # Mock open for the generic workflow
        generic_workflow_content = {**sample_workflow_data, "name": "GenericGroupWorkflow"}
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(generic_workflow_content)
        
        mock_execute_workflow.return_value = MagicMock(spec=DocumentationResponse)

        process_manifest_group(request, primary_code_content_sample)

        mock_execute_workflow.assert_called_once()
        called_request = mock_execute_workflow.call_args[0][0]
        assert called_request.workflow is not None
        assert called_request.workflow.name == "GenericGroupWorkflow"
        # In this case, workflow_type in the request might still be "nonexistent_type" or updated to generic,
        # depending on llm.py logic. The important part is that generic workflow was loaded.
        # Current llm.py logic: keeps original_workflow_type if specific load failed, then generic loaded.
        assert called_request.workflow_type == request.workflow_type # Original type is preserved
        assert mock_execute_workflow.call_args[0][1] == primary_code_content_sample
    
    @patch('backend.gendoc.llm.execute_workflow')
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_pmg_no_specific_workflow_loads_generic(self, mock_path_exists, mock_open, mock_execute_workflow, group_doc_request_base, sample_workflow_data, primary_code_content_sample):
        request = group_doc_request_base.model_copy(deep=True)
        # No request.workflow or request.workflow_type

        generic_workflow_path = gendoc_config.STORAGE_DIR / "_workflows" / DEFAULT_GROUP_WORKFLOW_FILE
        mock_path_exists.side_effect = lambda path: str(path) == str(generic_workflow_path)
        
        generic_workflow_content = {**sample_workflow_data, "name": "GenericDefaultWorkflow"}
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(generic_workflow_content)
        
        mock_execute_workflow.return_value = MagicMock(spec=DocumentationResponse)

        process_manifest_group(request, primary_code_content_sample)

        mock_execute_workflow.assert_called_once()
        called_request = mock_execute_workflow.call_args[0][0]
        assert called_request.workflow is not None
        assert called_request.workflow.name == "GenericDefaultWorkflow"
        assert called_request.workflow_type == "GenericDefaultWorkflow" # llm.py sets this if original was None
        assert mock_execute_workflow.call_args[0][1] == primary_code_content_sample

    @patch('backend.gendoc.llm.completion') # Mock litellm.completion
    @patch('backend.gendoc.llm.execute_workflow') # To ensure it's NOT called
    @patch('pathlib.Path.exists', return_value=False) # All workflow files do not exist
    def test_pmg_fallback_to_direct_llm_call(self, mock_path_exists_all_false, mock_execute_workflow, mock_litellm_completion, group_doc_request_base, primary_code_content_sample):
        request = group_doc_request_base.model_copy(deep=True)
        # No workflow hints in request, and Path.exists will make all workflow loading fail

        # Setup mock for litellm.completion (direct call)
        mock_llm_response = MagicMock()
        mock_llm_message = MagicMock(content="Direct LLM call output for group")
        mock_llm_response.choices = [MagicMock(message=mock_llm_message)]
        mock_llm_response.usage = MagicMock(prompt_tokens=20, completion_tokens=40, total_tokens=60)
        mock_llm_response.usage.model_dump = MagicMock(return_value={"prompt_tokens":20, "completion_tokens":40, "total_tokens":60})
        mock_litellm_completion.return_value = mock_llm_response

        response = process_manifest_group(request, primary_code_content_sample)

        mock_execute_workflow.assert_not_called()
        mock_litellm_completion.assert_called_once()
        
        # Assertions for the direct LLM call prompt
        call_args = mock_litellm_completion.call_args[1] # kwargs
        messages = call_args['messages']
        user_prompt = next(m['content'] for m in messages if m['role'] == 'user')

        assert primary_code_content_sample in user_prompt
        assert request.additional_context["group_id"] in user_prompt
        assert json.dumps(request.additional_context["related_files"]) in user_prompt # Check for stringified list
        assert json.dumps(request.additional_context["project_context"]) in user_prompt
        assert json.dumps(request.additional_context["group_specific_context"]) in user_prompt
        
        assert response.documentation == "Direct LLM call output for group"
        assert response.metadata["direct_llm_call_fallback_processed"] is True
        assert response.metadata["group_id"] == request.additional_context["group_id"]

    @patch('backend.gendoc.llm.execute_workflow')
    def test_pmg_workflow_execution_error_returns_error_response(self, mock_execute_workflow, group_doc_request_base, sample_workflow, primary_code_content_sample):
        request = group_doc_request_base.model_copy(deep=True)
        request.workflow = sample_workflow
        
        error_message = "Simulated workflow execution failure!"
        mock_execute_workflow.side_effect = Exception(error_message)

        response = process_manifest_group(request, primary_code_content_sample)

        mock_execute_workflow.assert_called_once()
        assert response.documentation.startswith(f"Error during workflow execution for group (Primary: {request.file_path}, Workflow: {sample_workflow.name}): {error_message}")
        assert response.metadata["workflow_execution_error"] is True
        assert response.metadata["workflow_name"] == sample_workflow.name
        assert response.metadata["group_id"] == request.additional_context["group_id"]
        assert response.token_usage["total_tokens"] == 0
