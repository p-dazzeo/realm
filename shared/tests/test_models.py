import pytest
from pydantic import ValidationError

from shared.models import WorkflowStep, DocumentationWorkflow

def test_workflow_step_valid():
    """Test successful creation of WorkflowStep with valid data."""
    step_data = {
        "name": "summarize_code",
        "prompt": "Summarize the following code: {code_content}",
        "inputs": ["code_content"],
        "output_type": "text"
    }
    step = WorkflowStep(**step_data)
    assert step.name == "summarize_code"
    assert step.prompt == "Summarize the following code: {code_content}"
    assert step.inputs == ["code_content"]
    assert step.output_type == "text"

def test_workflow_step_missing_required_field():
    """Test WorkflowStep creation fails if a required field is missing."""
    with pytest.raises(ValidationError) as excinfo:
        WorkflowStep(name="test_step", inputs=["input1"]) # Missing 'prompt'
    assert "prompt" in str(excinfo.value).lower()
    assert "field required" in str(excinfo.value).lower()

def test_workflow_step_invalid_input_type():
    """Test WorkflowStep creation fails if 'inputs' is not a list of strings."""
    with pytest.raises(ValidationError):
        WorkflowStep(name="test_step", prompt="Test", inputs="not_a_list")

def test_documentation_workflow_valid():
    """Test successful creation of DocumentationWorkflow with valid data."""
    step1_data = {
        "name": "step1",
        "prompt": "Prompt for step 1 using {input_code}",
        "inputs": ["input_code"],
        "output_type": "text"
    }
    step2_data = {
        "name": "step2",
        "prompt": "Prompt for step 2 using {step1.output}",
        "inputs": ["step1.output"],
        "output_type": "json"
    }
    workflow_data = {
        "name": "my_test_workflow",
        "description": "A test workflow for documentation.",
        "steps": [step1_data, step2_data]
    }
    workflow = DocumentationWorkflow(**workflow_data)
    assert workflow.name == "my_test_workflow"
    assert workflow.description == "A test workflow for documentation."
    assert len(workflow.steps) == 2
    assert workflow.steps[0].name == "step1"
    assert workflow.steps[1].name == "step2"
    assert workflow.steps[1].inputs == ["step1.output"]

def test_documentation_workflow_missing_required_field():
    """Test DocumentationWorkflow creation fails if a required field is missing."""
    # Missing 'name'
    with pytest.raises(ValidationError) as excinfo:
        DocumentationWorkflow(steps=[{"name": "s1", "prompt": "p", "inputs": ["i"]}])
    assert "name" in str(excinfo.value).lower()
    assert "field required" in str(excinfo.value).lower()

    # Missing 'steps'
    with pytest.raises(ValidationError) as excinfo:
        DocumentationWorkflow(name="my_workflow")
    assert "steps" in str(excinfo.value).lower()
    assert "field required" in str(excinfo.value).lower()


def test_documentation_workflow_invalid_steps_type():
    """Test DocumentationWorkflow creation fails if 'steps' is not a list of WorkflowStep-like dicts."""
    with pytest.raises(ValidationError):
        DocumentationWorkflow(name="test_wf", steps="not_a_list")
    
    with pytest.raises(ValidationError):
        DocumentationWorkflow(name="test_wf", steps=[{"name": "s1"}]) # Invalid step, missing prompt/inputs

def test_documentation_workflow_empty_steps_list():
    """Test DocumentationWorkflow creation with an empty list of steps (should be valid if steps are not required to be non-empty)."""
    # Pydantic by default allows empty lists unless constrained (e.g. with min_items=1)
    # The current model definition for DocumentationWorkflow does not specify min_items for steps.
    workflow_data = {
        "name": "empty_steps_workflow",
        "steps": []
    }
    workflow = DocumentationWorkflow(**workflow_data)
    assert workflow.name == "empty_steps_workflow"
    assert len(workflow.steps) == 0

# Example of a test for default values if any were defined in WorkflowStep
# def test_workflow_step_default_output_type():
#     step_data = {
#         "name": "summarize_code",
#         "prompt": "Summarize the following code: {code_content}",
#         "inputs": ["code_content"]
#         # output_type is omitted to test default
#     }
#     step = WorkflowStep(**step_data)
#     assert step.output_type == "text" # Assuming "text" is the default
# (This test is already implicitly covered by test_workflow_step_valid as "text" is the default)

pytest.main()
