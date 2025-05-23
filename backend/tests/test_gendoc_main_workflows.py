import pytest
import json
import shutil
import copy # Added for deepcopy
from pathlib import Path
from fastapi.testclient import TestClient

# Import the FastAPI app and config from the module where they are defined
# Assuming your FastAPI app instance is named 'app' in 'backend.gendoc.main'
from backend.gendoc.main import app, workflows_dir as main_workflows_dir
from backend.gendoc import config as gendoc_config
from shared.models import DocumentationWorkflow, WorkflowStep

# --- Fixtures ---

@pytest.fixture
def client(tmp_path):
    """Override the workflows_dir used by the main app for testing."""
    # This is the directory where workflow JSON files will be stored during tests.
    test_workflows_storage_dir = tmp_path / "_workflows_test_storage"
    test_workflows_storage_dir.mkdir(parents=True, exist_ok=True)

    # Temporarily patch the main_workflows_dir variable used by the router
    # and also gendoc_config.STORAGE_DIR if parts of the app derive it from there at runtime
    original_main_workflows_dir = main_workflows_dir
    original_config_storage_dir = gendoc_config.STORAGE_DIR
    
    # Point main_workflows_dir (used by the router) to our temp dir
    # This requires that main.workflow_router uses a `workflows_dir` that can be patched.
    # If workflow_router is defined at import time using gendoc_config.STORAGE_DIR,
    # then patching gendoc_config.STORAGE_DIR is more robust.
    
    # Let's assume the router's `workflows_dir` is derived from `gendoc_config.STORAGE_DIR`
    # or is directly patchable as `main_workflows_dir`.
    # The provided main.py seems to define `workflows_dir` globally.
    
    # Patch the global 'workflows_dir' in 'backend.gendoc.main'
    with patch('backend.gendoc.main.workflows_dir', test_workflows_storage_dir):
        # Also patch gendoc_config.STORAGE_DIR to ensure any other uses pick up the temp path
        # The _workflows subdir will be created relative to this by the app logic if needed.
        # The key is that `main.workflows_dir` (used by the router) points to our temp location.
        with patch.object(gendoc_config, 'STORAGE_DIR', tmp_path):
            test_client = TestClient(app)
            yield test_client # Return the TestClient for use in tests

    # Cleanup: remove the temporary directory after tests are done
    if test_workflows_storage_dir.exists():
        shutil.rmtree(test_workflows_storage_dir)


@pytest.fixture
def sample_workflow_step_data():
    return {"name": "test_step", "prompt": "Test prompt", "inputs": ["input1"]}

@pytest.fixture
def sample_workflow1_data(sample_workflow_step_data):
    return {
        "name": "workflow_alpha",
        "description": "Alpha workflow",
        "steps": [sample_workflow_step_data]
    }

@pytest.fixture
def sample_workflow2_data(sample_workflow_step_data):
    return {
        "name": "workflow_beta",
        "description": "Beta workflow",
        "steps": [sample_workflow_step_data, {**sample_workflow_step_data, "name": "test_step2"}]
    }

# --- Helper to get workflow file path ---
def get_workflow_file(tmp_workflows_dir_root: Path, name: str) -> Path:
    # In the test client fixture, workflows_dir is tmp_path / "_workflows_test_storage"
    # The main.py creates app_workflows_dir = config.STORAGE_DIR / "_workflows"
    # Our patch makes config.STORAGE_DIR = tmp_path.
    # So, the router will use tmp_path / "_workflows" if it re-calculates it.
    # Or, if it uses the globally patched `main.workflows_dir`, that is `tmp_path / "_workflows_test_storage"`
    
    # The current patch is `patch('backend.gendoc.main.workflows_dir', test_workflows_storage_dir)`
    # where `test_workflows_storage_dir` is `tmp_path / "_workflows_test_storage"`.
    # So, files will be directly under `tmp_path / "_workflows_test_storage"`.
    return tmp_workflows_dir_root / f"{name}.json"


# --- Workflow CRUD Tests ---

def test_create_workflow_success(client, sample_workflow1_data, tmp_path):
    """Test successful creation of a new workflow."""
    response = client.post("/workflows/", json=sample_workflow1_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_workflow1_data["name"]
    assert data["description"] == sample_workflow1_data["description"]
    
    # Verify file was created in the mocked directory
    # The client fixture patches main.workflows_dir to tmp_path / "_workflows_test_storage"
    # So, the get_workflow_file helper is not strictly needed here as we know the root.
    mocked_workflows_dir = tmp_path / "_workflows_test_storage"
    workflow_file = mocked_workflows_dir / f"{sample_workflow1_data['name']}.json"
    assert workflow_file.exists()
    with open(workflow_file, "r") as f:
        content = json.load(f)
        assert content["name"] == sample_workflow1_data["name"]

def test_create_workflow_already_exists(client, sample_workflow1_data):
    """Test creating a workflow that already exists (should fail with 409)."""
    client.post("/workflows/", json=sample_workflow1_data) # First creation
    response = client.post("/workflows/", json=sample_workflow1_data) # Attempt second creation
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()

def test_list_workflows_empty(client):
    """Test listing workflows when none are created (empty directory)."""
    response = client.get("/workflows/")
    assert response.status_code == 200
    assert response.json() == []

def test_list_workflows_multiple(client, sample_workflow1_data, sample_workflow2_data):
    """Test listing multiple created workflows."""
    client.post("/workflows/", json=sample_workflow1_data)
    client.post("/workflows/", json=sample_workflow2_data)
    
    response = client.get("/workflows/")
    assert response.status_code == 200
    workflows = response.json()
    assert len(workflows) == 2
    workflow_names = {wf["name"] for wf in workflows}
    assert sample_workflow1_data["name"] in workflow_names
    assert sample_workflow2_data["name"] in workflow_names

def test_get_workflow_specific_success(client, sample_workflow1_data):
    """Test retrieving a specific workflow by name."""
    client.post("/workflows/", json=sample_workflow1_data)
    
    workflow_name = sample_workflow1_data["name"]
    response = client.get(f"/workflows/{workflow_name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == workflow_name
    assert data["description"] == sample_workflow1_data["description"]

def test_get_workflow_specific_not_found(client):
    """Test retrieving a non-existent workflow (should fail with 404)."""
    response = client.get("/workflows/non_existent_workflow")
    assert response.status_code == 404

def test_update_workflow_success(client, sample_workflow1_data, tmp_path):
    """Test successfully updating an existing workflow."""
    client.post("/workflows/", json=sample_workflow1_data)
    workflow_name = sample_workflow1_data["name"]
    
    # Use deepcopy to prevent modifying the fixture data shared across tests if tests run in parallel or fixtures have wider scope
    updated_workflow_data = copy.deepcopy(sample_workflow1_data)
    updated_workflow_data["description"] = "Updated description"
    updated_workflow_data["steps"].append({"name": "new_step", "prompt": "New prompt", "inputs": []})
    
    response = client.put(f"/workflows/{workflow_name}", json=updated_workflow_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == workflow_name
    assert data["description"] == "Updated description"
    assert len(data["steps"]) == len(sample_workflow1_data["steps"]) + 1

    # Verify file content changed
    mocked_workflows_dir = tmp_path / "_workflows_test_storage"
    workflow_file = mocked_workflows_dir / f"{workflow_name}.json"
    assert workflow_file.exists()
    with open(workflow_file, "r") as f:
        content = json.load(f)
        assert content["description"] == "Updated description"
        assert len(content["steps"]) == len(sample_workflow1_data["steps"]) + 1


def test_update_workflow_not_found(client, sample_workflow1_data):
    """Test updating a non-existent workflow (should fail with 404)."""
    # To hit the "not found" case for PUT, the name in path and body must match,
    # but the file itself should not exist.
    non_existent_name = "non_existent_workflow"
    payload_for_non_existent = copy.deepcopy(sample_workflow1_data)
    payload_for_non_existent["name"] = non_existent_name # Ensure body name matches path name

    response = client.put(f"/workflows/{non_existent_name}", json=payload_for_non_existent)
    assert response.status_code == 404

def test_update_workflow_name_mismatch(client, sample_workflow1_data):
    """Test updating with mismatched workflow name in path vs. body (should fail with 400)."""
    client.post("/workflows/", json=sample_workflow1_data)
    path_name = sample_workflow1_data["name"]
    
    body_data = sample_workflow1_data.copy()
    body_data["name"] = "different_name_in_body"
    
    response = client.put(f"/workflows/{path_name}", json=body_data)
    assert response.status_code == 400
    assert "name in path does not match name in body" in response.json()["detail"].lower()

def test_delete_workflow_success(client, sample_workflow1_data, tmp_path):
    """Test successfully deleting a workflow."""
    client.post("/workflows/", json=sample_workflow1_data)
    workflow_name = sample_workflow1_data["name"]
    
    mocked_workflows_dir = tmp_path / "_workflows_test_storage"
    workflow_file = mocked_workflows_dir / f"{workflow_name}.json"
    assert workflow_file.exists() # Exists before delete

    response = client.delete(f"/workflows/{workflow_name}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()
    
    assert not workflow_file.exists() # Does not exist after delete

def test_delete_workflow_not_found(client):
    """Test deleting a non-existent workflow (should fail with 404)."""
    response = client.delete("/workflows/non_existent_workflow")
    assert response.status_code == 404

# To run these tests, use pytest. You might need to adjust imports based on your project structure.
# E.g., ensure 'backend.gendoc.main' and 'shared.models' are in PYTHONPATH.
# The `unittest.mock.patch` is needed for the client fixture.
from unittest.mock import patch, MagicMock, call # Added MagicMock and call

# Import models for request/response
from shared.models import DocumentationRequest, DocumentationResponse, DocumentationType

# --- Manifest Generation Tests ---

TEST_PROJECT_ID = "test_manifest_project"

@pytest.fixture
def project_dir_setup(tmp_path):
    """
    Sets up a temporary project directory under the test'sSTORAGE_DIR.
    tmp_path is used by the 'client' fixture to patch gendoc_config.STORAGE_DIR.
    So, we create our project inside tmp_path.
    """
    project_root = tmp_path / TEST_PROJECT_ID
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Create some dummy files
    (project_root / "file1.py").write_text("def hello():\n  print('hello')")
    (project_root / "file2.txt").write_text("This is a text file.")
    (project_root / "subfolder").mkdir()
    (project_root / "subfolder" / "file3.md").write_text("# Markdown")
    
    yield project_root # provide the path to the project root

    # Teardown (optional, as tmp_path handles it, but good for explicit cleanup if needed)
    # shutil.rmtree(project_root)


class TestGenerateEndpointWithManifest:

    def mock_llm_side_effect(self, request: DocumentationRequest, code_content: str):
        # Customize response based on request.file_path or other params
        doc_text = f"Documentation for {request.file_path}"
        return DocumentationResponse(
            project_id=request.project_id,
            documentation=doc_text,
            doc_type=request.doc_type,
            file_path=request.file_path,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            metadata={"llm_processed": True}
        )

    def mock_llm_fallback_side_effect(self, request: DocumentationRequest, code_content: str):
        # For fallback, file_path might be None or reflect the main request
        doc_text = f"Fallback documentation for project {request.project_id}"
        if "File: file1.py" in code_content and "File: file2.txt" in code_content:
            doc_text += " with file1.py and file2.txt"

        return DocumentationResponse(
            project_id=request.project_id,
            documentation=doc_text,
            doc_type=request.doc_type, # Should be OVERVIEW or similar
            file_path=request.file_path, # Original request file_path (None for project level)
            token_usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            metadata={"llm_processed_fallback": True}
        )

    @patch('backend.gendoc.llm.generate_single_file_documentation')
    @patch('backend.gendoc.main.get_file_contents')
    def test_successful_manifest_processing(self, mock_get_contents, mock_llm_call, client, project_dir_setup):
        project_root = project_dir_setup
        # Create manifest.json
        manifest_content = {"files": ["file1.py", "file2.txt"]}
        (project_root / "manifest.json").write_text(json.dumps(manifest_content))

        # Setup mocks
        mock_get_contents.side_effect = lambda path: f"Content of {Path(path).name}"
        mock_llm_call.side_effect = self.mock_llm_side_effect
        
        request_payload = DocumentationRequest(
            project_id=TEST_PROJECT_ID,
            doc_type=DocumentationType.COMPONENT # Example doc type
        ).model_dump(mode='json') # Use model_dump for FastAPI TestClient

        response = client.post("/generate", json=request_payload)

        assert response.status_code == 200
        data = response.json()

        # Assertions for LLM calls
        assert mock_llm_call.call_count == 2
        calls = mock_llm_call.call_args_list
        
        # Call 1 for file1.py
        call1_request_arg = calls[0][0][0]
        assert call1_request_arg.file_path == "file1.py"
        assert call1_request_arg.project_id == TEST_PROJECT_ID
        assert calls[0][0][1] == "Content of file1.py" # code_content for file1.py
        
        # Call 2 for file2.txt
        call2_request_arg = calls[1][0][0]
        assert call2_request_arg.file_path == "file2.txt"
        assert call2_request_arg.project_id == TEST_PROJECT_ID
        assert calls[1][0][1] == "Content of file2.txt" # code_content for file2.txt

        # Assertions for get_file_contents calls
        # Note: Path objects might differ slightly if created differently, so compare names or relative paths
        expected_get_contents_calls = [
            call(str(project_root / "file1.py")),
            call(str(project_root / "file2.txt"))
        ]
        mock_get_contents.assert_has_calls(expected_get_contents_calls, any_order=False)


        # Assertions for final aggregated response
        expected_doc = (
            "\n\n---\nFile: file1.py\n---\n\nDocumentation for file1.py"
            "\n\n---\nFile: file2.txt\n---\n\nDocumentation for file2.txt"
        )
        assert data["documentation"] == expected_doc
        assert data["project_id"] == TEST_PROJECT_ID
        assert data["doc_type"] == DocumentationType.COMPONENT.value
        assert data["metadata"]["processed_from_manifest"] is True
        assert data["metadata"]["files_processed"] == ["file1.py", "file2.txt"]
        
        # Assert token usage aggregation
        assert data["token_usage"]["prompt_tokens"] == 20 # 10 per call * 2 calls
        assert data["token_usage"]["completion_tokens"] == 40 # 20 per call * 2 calls
        assert data["token_usage"]["total_tokens"] == 60 # 30 per call * 2 calls

    @patch('backend.gendoc.llm.generate_single_file_documentation')
    @patch('backend.gendoc.main.get_file_contents')
    def test_manifest_file_not_found_in_project(self, mock_get_contents, mock_llm_call, client, project_dir_setup):
        project_root = project_dir_setup
        manifest_content = {"files": ["file1.py", "nonexistent.py"]} # nonexistent.py does not exist
        (project_root / "manifest.json").write_text(json.dumps(manifest_content))

        mock_get_contents.side_effect = lambda path: f"Content of {Path(path).name}" if Path(path).name == "file1.py" else None
        mock_llm_call.side_effect = self.mock_llm_side_effect

        request_payload = DocumentationRequest(project_id=TEST_PROJECT_ID, doc_type=DocumentationType.OVERVIEW).model_dump(mode='json')
        response = client.post("/generate", json=request_payload)

        assert response.status_code == 200
        data = response.json()

        # LLM called only for file1.py
        assert mock_llm_call.call_count == 1
        call1_request_arg = mock_llm_call.call_args[0][0]
        assert call1_request_arg.file_path == "file1.py"
        
        # get_file_contents called for both, but one returns None
        # The main logic checks existence first, then calls get_file_contents. So get_file_contents is called only for existing files.
        # Path(path).exists() inside the lambda for get_file_contents mock isn't how it works.
        # The endpoint logic does: `if not current_file_path.exists(): logger.warning(...)`
        # So, get_file_contents will only be called for file1.py
        
        # Re-check main.py logic for get_file_contents calls:
        # 1. `current_file_path = project_dir / file_in_manifest`
        # 2. `if not current_file_path.exists(): ... continue`
        # 3. `file_content = get_file_contents(str(current_file_path))`
        # So, get_file_contents is indeed only called for existing files.
        mock_get_contents.assert_called_once_with(str(project_root / "file1.py"))


        expected_doc = "\n\n---\nFile: file1.py\n---\n\nDocumentation for file1.py"
        assert data["documentation"] == expected_doc
        assert data["metadata"]["processed_from_manifest"] is True
        assert data["metadata"]["files_processed"] == ["file1.py"] # nonexistent.py is skipped
        assert data["token_usage"]["total_tokens"] == 30 # Only one successful call

    @patch('backend.gendoc.llm.generate_single_file_documentation')
    @patch('backend.gendoc.main.get_file_contents') # Though not strictly needed if LLM not called
    def test_manifest_empty_files_list(self, mock_get_contents, mock_llm_call, client, project_dir_setup):
        project_root = project_dir_setup
        (project_root / "manifest.json").write_text(json.dumps({"files": []}))

        request_payload = DocumentationRequest(project_id=TEST_PROJECT_ID, doc_type=DocumentationType.OVERVIEW).model_dump(mode='json')
        response = client.post("/generate", json=request_payload)
        
        assert response.status_code == 200
        data = response.json()

        mock_llm_call.assert_not_called()
        mock_get_contents.assert_not_called()
        
        assert data["documentation"] == ""
        assert data["metadata"]["processed_from_manifest"] is True
        assert data["metadata"]["files_processed"] == []
        assert data["token_usage"]["total_tokens"] == 0

    def test_manifest_malformed_json(self, client, project_dir_setup):
        project_root = project_dir_setup
        (project_root / "manifest.json").write_text('{"files": ["file1.py",}') # Invalid JSON

        request_payload = DocumentationRequest(project_id=TEST_PROJECT_ID, doc_type=DocumentationType.OVERVIEW).model_dump(mode='json')
        response = client.post("/generate", json=request_payload)

        assert response.status_code == 400 # Based on main.py's except json.JSONDecodeError
        assert "invalid manifest.json" in response.json()["detail"].lower()
        assert "could not parse json" in response.json()["detail"].lower()

    @patch('backend.gendoc.llm.generate_single_file_documentation')
    @patch('backend.gendoc.main.get_file_contents')
    def test_fallback_no_manifest(self, mock_get_contents, mock_llm_call, client, project_dir_setup):
        project_root = project_dir_setup
        # Ensure no manifest.json for this test (project_dir_setup doesn't create one by default)
        if (project_root / "manifest.json").exists():
            (project_root / "manifest.json").unlink()

        # Mock get_file_contents for the fallback logic
        # Fallback walks os.walk, let's define content for expected files
        def get_contents_side_effect(path_str):
            path_obj = Path(path_str)
            if path_obj.name == "file1.py": return "Content of file1.py"
            if path_obj.name == "file2.txt": return "Content of file2.txt"
            if path_obj.name == "file3.md": return "Content of file3.md"
            return None # Should not happen if os.walk is correct
        mock_get_contents.side_effect = get_contents_side_effect
        
        mock_llm_call.side_effect = self.mock_llm_fallback_side_effect

        request_payload = DocumentationRequest(
            project_id=TEST_PROJECT_ID, 
            doc_type=DocumentationType.OVERVIEW # Typical for fallback
        ).model_dump(mode='json')
        response = client.post("/generate", json=request_payload)

        assert response.status_code == 200
        data = response.json()

        # LLM called once for the concatenated content
        assert mock_llm_call.call_count == 1
        
        # Assert content passed to LLM (order might vary based on os.walk)
        call_args = mock_llm_call.call_args[0]
        passed_request: DocumentationRequest = call_args[0]
        passed_code_content: str = call_args[1]

        assert passed_request.project_id == TEST_PROJECT_ID
        assert passed_request.file_path is None # Project level
        
        # Check that the content of the files is in the combined string
        assert "# File: file1.py" in passed_code_content
        assert "Content of file1.py" in passed_code_content
        assert "# File: file2.txt" in passed_code_content
        assert "Content of file2.txt" in passed_code_content
        assert "# File: subfolder/file3.md" in passed_code_content # Check relative path for subfolders
        assert "Content of file3.md" in passed_code_content
        
        # Assertions for get_file_contents calls (order can vary with os.walk)
        # We expect it to be called for file1.py, file2.txt, and subfolder/file3.md
        # The exact number of calls might be up to 10 based on the limit in main.py
        assert mock_get_contents.call_count >= 3 # At least for the 3 files we defined content for

        expected_calls = [
            call(str(project_root / "file1.py")),
            call(str(project_root / "file2.txt")),
            call(str(project_root / "subfolder" / "file3.md"))
        ]
        # Use any_order=True because os.walk doesn't guarantee order
        # However, the paths are relative to project_root in the concatenated string
        # mock_get_contents.assert_has_calls(expected_calls, any_order=True) # This might be too strict if other files are picked up

        # Assertions for the response
        assert "Fallback documentation for project test_manifest_project" in data["documentation"]
        assert "with file1.py and file2.txt" in data["documentation"] # From our mock
        assert data["metadata"]["llm_processed_fallback"] is True
        assert "fallback_files_concatenated" in data["metadata"]
        # The order in fallback_files_concatenated depends on os.walk, so check for presence
        assert "file1.py" in data["metadata"]["fallback_files_concatenated"]
        assert "file2.txt" in data["metadata"]["fallback_files_concatenated"]
        assert str(Path("subfolder") / "file3.md") in data["metadata"]["fallback_files_concatenated"]
        
        assert "processed_from_manifest" not in data["metadata"] # Ensure manifest specific key is absent
        assert data["token_usage"]["total_tokens"] == 300 # From fallback mock

# Remove the pytest.main() call if it's present from the original file,
# as it's typically not used when running pytest from the command line.
# If the original file had pytest.main(), it might have been for specific local run configurations.
# For automated testing, it's better to let the test runner handle test discovery and execution.
# For example, if the file ends with:
# pytest.main()
# It should be removed or commented out.
# Based on the provided content, it seems it ends with `pytest.main()`.
# I will remove it.

# (No actual pytest.main() was in the provided snippet, so no removal needed here)


# --- V1.1 Manifest and Group Processing Tests ---

JCL_COBOL_WORKFLOW_NAME = "jcl_cobol_analysis-standard" # Matches the file name without .json
JCL_COBOL_DOC_TYPE = DocumentationType.JCL_COBOL_ANALYSIS # Matches enum and workflow file

@pytest.fixture
def jcl_cobol_workflow_file_setup(tmp_path):
    """
    Creates the jcl_cobol_analysis-standard.json workflow file in the mocked
    workflows directory for testing full workflow execution.
    The client fixture patches gendoc_config.STORAGE_DIR to tmp_path and
    backend.gendoc.main.workflows_dir to (tmp_path / "_workflows_test_storage").
    """
    workflows_storage_dir = tmp_path / "_workflows_test_storage" # As defined in client fixture
    workflows_storage_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_content = {
        "name": "JCL to COBOL Analysis Workflow",
        "description": "Analyzes a JCL file and up to two related COBOL programs, then combines the analysis.",
        "doc_type": JCL_COBOL_DOC_TYPE.value, # Use the enum value
        "steps": [
            {
                "name": "step1_jcl_analysis",
                "description": "Analyze JCL and its relationship with COBOL programs.",
                "inputs": ["code_content", "file_path", "additional_context.related_files", "additional_context.group_specific_context", "additional_context.project_context"],
                "prompt": "JCL Path: {file_path}\nJCL Content:\n```\n{code_content}\n```\nRelated Files (JSON string): {additional_context_related_files}\nGroup Context: {additional_context_group_specific_context}\nProject Context: {additional_context_project_context}\nAnalyze JCL and COBOL relations."
            },
            {
                "name": "step2_cobol_program1_analysis",
                "description": "Analyze the first related COBOL program.",
                "inputs": ["additional_context.related_files", "step1_jcl_analysis.output"],
                "prompt": "JCL Analysis:\n{step1_jcl_analysis_output}\nRelated Files (JSON string): {additional_context_related_files}\nAnalyze COBOL 1."
            },
            {
                "name": "step3_cobol_program2_analysis",
                "description": "Analyze the second related COBOL program.",
                "inputs": ["additional_context.related_files", "step1_jcl_analysis.output"],
                "prompt": "JCL Analysis:\n{step1_jcl_analysis_output}\nRelated Files (JSON string): {additional_context_related_files}\nAnalyze COBOL 2."
            },
            {
                "name": "step4_combine_documentation",
                "description": "Combine all analyses.",
                "inputs": ["step1_jcl_analysis.output", "step2_cobol_program1_analysis.output", "step3_cobol_program2_analysis.output"],
                "prompt": "Combine:\nJCL: {step1_jcl_analysis_output}\nCOBOL1: {step2_cobol_program1_analysis_output}\nCOBOL2: {step3_cobol_program2_analysis_output}"
            }
        ]
    }
    workflow_file_path = workflows_storage_dir / f"{JCL_COBOL_WORKFLOW_NAME}.json"
    with open(workflow_file_path, "w") as f:
        json.dump(workflow_content, f)
    return workflow_file_path


class TestGenerateEndpointWithV11Manifest(TestGenerateEndpointWithManifest): # Inherit for fixtures if needed

    @patch('backend.gendoc.llm.process_manifest_group')
    @patch('backend.gendoc.main.get_file_contents')
    def test_v1_1_manifest_group_iteration_and_context(self, mock_get_contents, mock_process_group, client, project_dir_setup):
        project_root = project_dir_setup
        
        # Create dummy files for the test
        (project_root / "jcl1.jcl").write_text("JCL 1 Content")
        (project_root / "cobol1.cbl").write_text("COBOL 1 Content")
        (project_root / "cobol2.cbl").write_text("COBOL 2 Content")
        # file1.py is already created by project_dir_setup

        v1_1_manifest_content = {
            "manifest_version": "1.1",
            "project_context": {"project_name": "TestProject"},
            "processing_groups": [
                {
                    "group_id": "group1_jcl_cobol",
                    "group_type": "jcl_cobol_analysis", # This might map to a workflow_type
                    "primary_file": "jcl1.jcl",
                    "related_files": [
                        {"path": "cobol1.cbl", "role": "program1"},
                        {"path": "cobol2.cbl", "role": "program2"}
                    ],
                    "group_specific_context": {"detail": "Group 1 custom context"}
                },
                {
                    "group_id": "group2_python",
                    "group_type": "python_module",
                    "primary_file": "file1.py", # From project_dir_setup
                    "related_files": [],
                    "group_specific_context": {"detail": "Group 2 context for Python"}
                }
            ]
        }
        (project_root / "manifest.json").write_text(json.dumps(v1_1_manifest_content))

        # Mock get_file_contents to return content for these new files
        def get_contents_side_effect(path_str):
            path_obj = Path(path_str)
            if path_obj.name == "jcl1.jcl": return "JCL 1 Content"
            if path_obj.name == "cobol1.cbl": return "COBOL 1 Content"
            if path_obj.name == "cobol2.cbl": return "COBOL 2 Content"
            if path_obj.name == "file1.py": return "Content of file1.py" # From base fixture
            return None
        mock_get_contents.side_effect = get_contents_side_effect
        
        # Mock process_manifest_group to return distinct responses
        def process_group_side_effect(request: DocumentationRequest, primary_code_content: str):
            group_id = request.additional_context.get("group_id", "unknown_group")
            return DocumentationResponse(
                project_id=request.project_id,
                documentation=f"Processed doc for {group_id} (Primary: {request.file_path})",
                doc_type=request.doc_type, # Should be the overall request's doc_type
                file_path=request.file_path, # This is the primary file of the group
                token_usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
                metadata={"processed_by_mock_group_processor": True, "group_id": group_id}
            )
        mock_process_group.side_effect = process_group_side_effect

        # API Request - doc_type here is the overall request type, can be generic
        api_request_payload = DocumentationRequest(
            project_id=TEST_PROJECT_ID,
            doc_type=DocumentationType.OVERVIEW 
        ).model_dump(mode='json')

        response = client.post("/generate", json=api_request_payload)
        assert response.status_code == 200
        data = response.json()

        # Assertions for process_manifest_group calls
        assert mock_process_group.call_count == 2
        calls = mock_process_group.call_args_list
        
        # Call 1 (Group 1: jcl_cobol_analysis)
        call1_request_arg: DocumentationRequest = calls[0][0][0]
        call1_primary_content_arg: str = calls[0][0][1]
        
        assert call1_request_arg.file_path == "jcl1.jcl"
        assert call1_request_arg.project_id == TEST_PROJECT_ID
        assert call1_primary_content_arg == "JCL 1 Content"
        
        # Verify additional_context for Group 1
        g1_context = call1_request_arg.additional_context
        assert g1_context["group_id"] == "group1_jcl_cobol"
        assert g1_context["group_type"] == "jcl_cobol_analysis"
        assert g1_context["project_context"] == {"project_name": "TestProject"}
        assert g1_context["group_specific_context"] == {"detail": "Group 1 custom context"}
        assert len(g1_context["related_files"]) == 2
        assert g1_context["related_files"][0] == {"path": "cobol1.cbl", "role": "program1", "content": "COBOL 1 Content"}
        assert g1_context["related_files"][1] == {"path": "cobol2.cbl", "role": "program2", "content": "COBOL 2 Content"}

        # Call 2 (Group 2: python_module)
        call2_request_arg: DocumentationRequest = calls[1][0][0]
        call2_primary_content_arg: str = calls[1][0][1]
        assert call2_request_arg.file_path == "file1.py"
        assert call2_primary_content_arg == "Content of file1.py"
        g2_context = call2_request_arg.additional_context
        assert g2_context["group_id"] == "group2_python"
        assert g2_context["related_files"] == []

        # Assertions for final aggregated response
        expected_doc_parts = [
            "Processed doc for group1_jcl_cobol (Primary: jcl1.jcl)",
            "Processed doc for group2_python (Primary: file1.py)"
        ]
        assert expected_doc_parts[0] in data["documentation"]
        assert expected_doc_parts[1] in data["documentation"]
        
        assert data["metadata"]["processed_from_manifest"] is True
        assert data["metadata"]["manifest_version_processed"] == "1.1"
        assert data["metadata"]["groups_processed"] == ["group1_jcl_cobol", "group2_python"]
        assert data["token_usage"]["total_tokens"] == 30 # 15 per call * 2 calls

    @patch('backend.gendoc.llm.process_manifest_group')
    @patch('backend.gendoc.main.get_file_contents')
    def test_v1_1_manifest_skip_group_if_primary_missing(self, mock_get_contents, mock_process_group, client, project_dir_setup):
        project_root = project_dir_setup
        (project_root / "file1.py").write_text("Valid Python Content") # Ensure this valid file exists

        v1_1_manifest_content = {
            "manifest_version": "1.1",
            "processing_groups": [
                {
                    "group_id": "group_nonexistent_primary",
                    "primary_file": "nonexistent_primary.jcl", # This file does not exist
                    "related_files": []
                },
                {
                    "group_id": "group_valid_python",
                    "primary_file": "file1.py",
                    "related_files": []
                }
            ]
        }
        (project_root / "manifest.json").write_text(json.dumps(v1_1_manifest_content))

        mock_get_contents.side_effect = lambda path_str: "Valid Python Content" if Path(path_str).name == "file1.py" else None
        
        mock_process_group.return_value = DocumentationResponse(
            project_id=TEST_PROJECT_ID,
            documentation="Doc for valid_python_group",
            doc_type=DocumentationType.OVERVIEW,
            file_path="file1.py",
            token_usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            metadata={"group_id": "group_valid_python"}
        )

        api_request_payload = DocumentationRequest(project_id=TEST_PROJECT_ID, doc_type=DocumentationType.OVERVIEW).model_dump(mode='json')
        response = client.post("/generate", json=api_request_payload)
        
        assert response.status_code == 200
        data = response.json()

        mock_process_group.assert_called_once() # Called only for the valid group
        
        # Check that the call was for the valid group
        called_request_arg: DocumentationRequest = mock_process_group.call_args[0][0]
        assert called_request_arg.file_path == "file1.py"
        assert called_request_arg.additional_context["group_id"] == "group_valid_python"

        assert "Doc for valid_python_group" in data["documentation"]
        # Check for the skip message for the non-existent primary file group
        assert "Group: group_nonexistent_primary (Primary File: nonexistent_primary.jcl) - SKIPPED (Primary file not found)" in data["documentation"]
        
        assert data["metadata"]["manifest_version_processed"] == "1.1"
        # groups_processed should only contain the successfully initiated group in this context,
        # as the error message for the skipped group is part of the aggregated content.
        # The main.py logic currently appends to processed_group_ids upon successful call to process_manifest_group.
        # If the primary file doesn't exist, it appends an error string to aggregated_docs_content and skips.
        # So, processed_group_ids in metadata should reflect only successfully *called* groups.
        assert data["metadata"]["groups_processed"] == ["group_valid_python"]
        assert data["token_usage"]["total_tokens"] == 2 # Only from the valid group call

    @patch('litellm.completion') # Mock at the lowest LLM call level
    @patch('backend.gendoc.main.get_file_contents')
    def test_full_jcl_cobol_analysis_workflow_execution(self, mock_get_contents, mock_litellm_completion, client, project_dir_setup, jcl_cobol_workflow_file_setup):
        project_root = project_dir_setup
        
        jcl_content = "JCL Content for test.jcl"
        cobol1_content = "COBOL Main Program Content for prog1.cbl"
        cobol2_content = "COBOL Sub Program Content for prog2.cbl"

        (project_root / "test.jcl").write_text(jcl_content)
        (project_root / "prog1.cbl").write_text(cobol1_content)
        (project_root / "prog2.cbl").write_text(cobol2_content)

        manifest_content = {
            "manifest_version": "1.1",
            "project_context": {"project_name": "JCL_COBOL_Test"},
            "processing_groups": [{
                "group_id": "jc_group1",
                "group_type": JCL_COBOL_WORKFLOW_NAME, # This should trigger the specific workflow
                "primary_file": "test.jcl",
                "related_files": [
                    {"path": "prog1.cbl", "role": "cobol_main"},
                    {"path": "prog2.cbl", "role": "cobol_sub"}
                ],
                "group_specific_context": {"environment": "production"}
            }]
        }
        (project_root / "manifest.json").write_text(json.dumps(manifest_content))

        # get_file_contents needs to provide content for primary and related files when main.py builds context
        def get_contents_side_effect(path_str):
            path_obj = Path(path_str)
            if path_obj.name == "test.jcl": return jcl_content
            if path_obj.name == "prog1.cbl": return cobol1_content
            if path_obj.name == "prog2.cbl": return cobol2_content
            return None
        mock_get_contents.side_effect = get_contents_side_effect

        # Mock litellm.completion side effect
        mock_call_count = 0
        expected_outputs = [
            "JCL Analysis Output", 
            "COBOL 1 (prog1.cbl) Analysis Output", 
            "COBOL 2 (prog2.cbl) Analysis Output", 
            "Final Combined JCL-COBOL Documentation"
        ]

        def litellm_side_effect(model, messages, **kwargs):
            nonlocal mock_call_count
            # Basic check: Ensure user message is present
            assert any(msg["role"] == "user" for msg in messages)
            user_prompt = next(msg["content"] for msg in messages if msg["role"] == "user")

            # Simple validation of prompt content based on step
            if mock_call_count == 0: # Step 1: JCL Analysis
                assert jcl_content in user_prompt # Primary file content
                assert "prog1.cbl" in user_prompt # From related_files string
                assert "prog2.cbl" in user_prompt
                assert "JCL Content for test.jcl" in user_prompt
            elif mock_call_count == 1: # Step 2: COBOL 1 Analysis
                assert expected_outputs[0] in user_prompt # Output from step 1
                assert "prog1.cbl" in user_prompt # Related files string should be there
            elif mock_call_count == 2: # Step 3: COBOL 2 Analysis
                assert expected_outputs[0] in user_prompt # Output from step 1
                assert "prog2.cbl" in user_prompt
            elif mock_call_count == 3: # Step 4: Combine
                assert expected_outputs[0] in user_prompt
                assert expected_outputs[1] in user_prompt
                assert expected_outputs[2] in user_prompt
            
            # Create a mock CompletionResponse object similar to what litellm returns
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = expected_outputs[mock_call_count]
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150
            
            mock_call_count += 1
            return mock_response

        mock_litellm_completion.side_effect = litellm_side_effect
        
        # The API request. The doc_type here might be less important if group_type drives workflow selection.
        # However, for consistency, let's use the specific doc_type.
        api_request_payload = DocumentationRequest(
            project_id=TEST_PROJECT_ID,
            doc_type=JCL_COBOL_DOC_TYPE # Requesting the specific doc type
        ).model_dump(mode='json')

        response = client.post("/generate", json=api_request_payload)
        
        assert response.status_code == 200
        data = response.json()

        assert mock_litellm_completion.call_count == 4
        assert data["documentation"] == expected_outputs[3] # Final combined output
        assert data["doc_type"] == JCL_COBOL_DOC_TYPE.value
        assert data["metadata"]["manifest_version_processed"] == "1.1"
        assert data["metadata"]["groups_processed"] == ["jc_group1"]
        assert data["metadata"]["workflow_name"] == "JCL to COBOL Analysis Workflow" # from workflow JSON
        assert data["metadata"]["workflow_type"] == JCL_COBOL_WORKFLOW_NAME # from group_type mapping
        assert data["token_usage"]["total_tokens"] == (150 * 4) # 150 per call * 4 calls
