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
from unittest.mock import patch

pytest.main()
