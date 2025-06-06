import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from main import app # Assuming your FastAPI app is initialized in 'main.py'
from core.dependencies import get_database # To override
from modules.upload.models import Project, ProjectFile, UploadSession
from modules.upload.schemas import ProjectSummary, UploadMethod, UploadStatus
from datetime import datetime, timezone

# A fixture for an in-memory SQLite database for testing
# This is a simplified version. In a real setup, you might use pytest-asyncio, etc.
@pytest.fixture
async def db_session_override():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker
    from core.database import Base # Assuming your Base is here

    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
            await session.rollback() # Ensure tests are isolated

    app.dependency_overrides[get_database] = override_get_db

    async with TestingSessionLocal() as session:
        yield session # Provide the session to the test

    # Teardown: drop all tables (optional, as :memory: is fresh)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

    del app.dependency_overrides[get_database] # cleanup override


@pytest.fixture
def client(db_session_override): # Depends on the db_session_override to be applied first
    with TestClient(app) as c:
        yield c

# Helper function to create a project with files
async def create_project_with_files(
    db: AsyncSession,
    name: str,
    file_count: int,
    upload_method: UploadMethod = UploadMethod.DIRECT,
    description: str = "Test project"
) -> Project:
    project = Project(
        name=name,
        description=description,
        upload_method=upload_method.value,
        upload_status=UploadStatus.COMPLETED,
        file_size=file_count * 100, # dummy size
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(project)
    await db.flush() # Flush to get project.id

    for i in range(file_count):
        pf = ProjectFile(
            project_id=project.id,
            filename=f"file_{i}.txt",
            file_path=f"path/to/file_{i}.txt",
            relative_path=f"path/to/file_{i}.txt",
            file_extension=".txt",
            file_size=100,
            content=f"content of file {i}",
            content_hash=f"hash_{i}",
            language="text",
            is_binary=False,
            loc=10
        )
        db.add(pf)

    await db.commit()
    # It's better to query the project again if we need to ensure relationships are loaded
    # or rely on the test query to fetch what's needed.
    # For this helper, committing is enough. The test itself will query.
    # Ensure created_at is distinct for reliable ordering in pagination tests
    project.created_at = datetime.now(timezone.utc)
    await db.commit() # Commit again to save created_at if it was changed after first commit
    return project


@pytest.mark.asyncio
async def test_list_projects_file_counts_accurate(client: TestClient, db_session_override: AsyncSession):
    # Setup: Create projects with 0, 1, and N files
    project0 = await create_project_with_files(db_session_override, "Project Zero Files", 0)
    project1 = await create_project_with_files(db_session_override, "Project One File", 1)
    projectN = await create_project_with_files(db_session_override, "Project N Files", 5)

    # Action: Call GET /upload/projects
    response = client.get("/upload/projects")
    assert response.status_code == 200

    projects_summary_data = response.json()
    # Order might not be guaranteed, so we check presence and correctness
    assert len(projects_summary_data) == 3

    expected_counts = {
        project0.id: 0,
        project1.id: 1,
        projectN.id: 5,
    }

    actual_counts = {data["id"]: data["file_count"] for data in projects_summary_data}

    for project_id, expected_count in expected_counts.items():
        assert project_id in actual_counts, f"Project with ID {project_id} not found in response."
        assert actual_counts[project_id] == expected_count, \
            f"File count mismatch for project {project_id}. Expected {expected_count}, got {actual_counts[project_id]}"


@pytest.mark.asyncio
async def test_get_project_include_files_false_no_files_loaded(client: TestClient, db_session_override: AsyncSession):
    # Setup: Create a project with multiple files
    project_with_files = await create_project_with_files(db_session_override, "Project With Files", 3)

    # Action: Call GET /upload/projects/{project_id}?include_files=False
    response = client.get(f"/upload/projects/{project_with_files.id}?include_files=False")
    assert response.status_code == 200

    project_data = response.json()

    assert "files" in project_data
    assert len(project_data["files"]) == 0
    assert project_data["id"] == project_with_files.id
    assert project_data["name"] == "Project With Files"

@pytest.mark.asyncio
async def test_get_project_include_files_true_files_loaded(client: TestClient, db_session_override: AsyncSession):
    # Setup: Create a project with multiple files
    num_files = 3
    project_with_files = await create_project_with_files(db_session_override, "Project Files Included", num_files)

    # Action: Call GET /upload/projects/{project_id}?include_files=True
    response = client.get(f"/upload/projects/{project_with_files.id}?include_files=True")
    assert response.status_code == 200

    project_data = response.json()

    assert "files" in project_data
    assert len(project_data["files"]) == num_files

    for i in range(num_files):
        assert project_data["files"][i]["filename"] == f"file_{i}.txt"
        assert project_data["files"][i]["project_id"] == project_with_files.id

# TODO: test_list_projects_avoids_n_plus_one_for_files

@pytest.mark.asyncio
async def test_list_projects_pagination_and_filtering_with_counts(client: TestClient, db_session_override: AsyncSession):
    # Setup: Create multiple projects with different file counts and upload methods
    # Ensure created_at is slightly different for predictable order (newest first)
    projects_created = []
    projects_created.append(await create_project_with_files(db_session_override, "P1 Direct 3F", 3, UploadMethod.DIRECT))
    await asyncio.sleep(0.01) # ensure distinct created_at
    projects_created.append(await create_project_with_files(db_session_override, "P2 Parser 1F", 1, UploadMethod.PARSER))
    await asyncio.sleep(0.01)
    projects_created.append(await create_project_with_files(db_session_override, "P3 Direct 0F", 0, UploadMethod.DIRECT))
    await asyncio.sleep(0.01)
    projects_created.append(await create_project_with_files(db_session_override, "P4 Parser 5F", 5, UploadMethod.PARSER))
    await asyncio.sleep(0.01)
    projects_created.append(await create_project_with_files(db_session_override, "P5 Direct 2F", 2, UploadMethod.DIRECT))

    # Default order is Project.created_at.desc()
    # P5 (2F Direct)
    # P4 (5F Parser)
    # P3 (0F Direct)
    # P2 (1F Parser)
    # P1 (3F Direct)

    # Test 1: Simple pagination (get first 2)
    response1 = client.get("/upload/projects?skip=0&limit=2")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 2
    assert data1[0]["name"] == "P5 Direct 2F"
    assert data1[0]["file_count"] == 2
    assert data1[1]["name"] == "P4 Parser 5F"
    assert data1[1]["file_count"] == 5

    # Test 2: Pagination (skip 2, get next 2)
    response2 = client.get("/upload/projects?skip=2&limit=2")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 2
    assert data2[0]["name"] == "P3 Direct 0F"
    assert data2[0]["file_count"] == 0
    assert data2[1]["name"] == "P2 Parser 1F"
    assert data2[1]["file_count"] == 1

    # Test 3: Filtering by upload_method (DIRECT)
    response3 = client.get("/upload/projects?upload_method=direct")
    assert response3.status_code == 200
    data3 = response3.json()
    assert len(data3) == 3 # P5, P3, P1
    direct_project_names = {p["name"] for p in data3}
    assert {"P5 Direct 2F", "P3 Direct 0F", "P1 Direct 3F"} == direct_project_names
    for p_data in data3: # Check file counts are correct for filtered
        if p_data["name"] == "P5 Direct 2F": assert p_data["file_count"] == 2
        if p_data["name"] == "P3 Direct 0F": assert p_data["file_count"] == 0
        if p_data["name"] == "P1 Direct 3F": assert p_data["file_count"] == 3

    # Test 4: Filtering by upload_method (PARSER) and pagination
    response4 = client.get("/upload/projects?upload_method=parser&skip=0&limit=1")
    assert response4.status_code == 200
    data4 = response4.json()
    assert len(data4) == 1
    assert data4[0]["name"] == "P4 Parser 5F" # Newest Parser project
    assert data4[0]["file_count"] == 5

    # Test 5: Filtering that results in no projects
    response5 = client.get("/upload/projects?upload_method=direct&skip=10") # Skip more than available
    assert response5.status_code == 200
    data5 = response5.json()
    assert len(data5) == 0
