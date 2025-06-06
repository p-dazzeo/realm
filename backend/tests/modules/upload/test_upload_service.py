import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from main import app # For app context if service uses it, or config.
from core.dependencies import get_database # To override if needed, or use a direct session
from modules.upload.models import Project, ProjectFile, UploadSession, UploadStatus, SessionStatus
from modules.upload.schemas import ProjectCreate, UploadMethod
from modules.upload.service import UploadService, upload_service as global_upload_service
from datetime import datetime, timezone

# Re-using a similar fixture concept for a test DB session
@pytest.fixture
async def db_session(): # Renamed to avoid conflict if used in same test suite run with router tests
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker
    from core.database import Base

    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback() # Ensure tests are isolated

    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def upload_service_instance():
    # In case the global_upload_service has state or needs specific setup for testing
    # For now, assume it's stateless enough or we use its methods directly.
    # If it had an __init__ with dependencies, we'd mock them here.
    # We might need to mock its http_client if parser tests were also here.
    return global_upload_service # or UploadService() if it's simple

# Helper to create a mock UploadSession
async def create_mock_session(db: AsyncSession, upload_method: UploadMethod) -> UploadSession:
    session_obj = UploadSession(
        upload_method=upload_method.value,
        status=SessionStatus.PENDING,
        total_files=0,
        processed_files=0,
        failed_files=0,
        expires_at=datetime.now(timezone.utc) # Dummy value
    )
    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)
    return session_obj

@pytest.mark.asyncio
async def test_upload_direct_success_all_files_committed(
    db_session: AsyncSession,
    upload_service_instance: UploadService
):
    # Setup
    project_data = ProjectCreate(name="Test Direct Upload", description="A test project")

    # Mock files data (as would be extracted by _extract_project_files)
    mock_files_data = [
        {"filename": "file1.txt", "relative_path": "file1.txt", "content": "content1", "size": 8},
        {"filename": "file2.py", "relative_path": "file2.py", "content": "print('hello')", "size": 13},
    ]

    # Create a mock UploadSession record in the DB first
    upload_session_obj = await create_mock_session(db_session, UploadMethod.DIRECT)
    upload_session_obj.total_files = len(mock_files_data) # Update total files
    await db_session.commit()
    await db_session.refresh(upload_session_obj)

    # Action: Call _upload_direct
    # The _upload_direct method is "protected", but we're testing the class behavior.
    created_project = await upload_service_instance._upload_direct(
        db=db_session,
        session=upload_session_obj, # Pass the ORM object
        project_data=project_data,
        files=mock_files_data
    )

    # Assertions
    assert created_project is not None
    assert created_project.name == project_data.name
    assert created_project.upload_method == UploadMethod.DIRECT.value
    assert created_project.upload_status == UploadStatus.COMPLETED

    # Verify ProjectFile records in the DB
    stmt = select(ProjectFile).where(ProjectFile.project_id == created_project.id)
    result = await db_session.execute(stmt)
    project_files_in_db = result.scalars().all()
    assert len(project_files_in_db) == len(mock_files_data)

    for i, pf_db in enumerate(project_files_in_db):
        assert pf_db.filename == mock_files_data[i]["filename"]
        assert pf_db.content == mock_files_data[i]["content"]

    # Verify UploadSession status
    await db_session.refresh(upload_session_obj) # Refresh to get latest state
    assert upload_session_obj.status == SessionStatus.COMPLETED
    assert upload_session_obj.processed_files == len(mock_files_data)
    assert upload_session_obj.failed_files == 0
    assert upload_session_obj.project_id == created_project.id


@pytest.mark.asyncio
async def test_upload_direct_failure_mid_processing_rolls_back_files(
    db_session: AsyncSession,
    upload_service_instance: UploadService
):
    # Setup
    project_data = ProjectCreate(name="Test Rollback", description="Test atomicity")
    mock_files_data = [
        {"filename": "goodfile.txt", "relative_path": "goodfile.txt", "content": "works", "size": 5},
        {"filename": "badfile.txt", "relative_path": "badfile.txt", "content": "fails", "size": 5}, # This one will fail
        {"filename": "neverprocessed.txt", "relative_path": "neverprocessed.txt", "content": "skipped", "size": 7},
    ]

    upload_session_obj = await create_mock_session(db_session, UploadMethod.DIRECT)
    upload_session_obj.total_files = len(mock_files_data)
    await db_session.commit()
    await db_session.refresh(upload_session_obj)

    # Patch _create_project_file_direct to simulate failure on the second file
    original_create_method = upload_service_instance._create_project_file_direct

    async def mock_create_project_file_direct(db, project, file_data_dict):
        if file_data_dict["filename"] == "badfile.txt":
            raise Exception("Simulated processing error for badfile.txt")
        # Call the original method for other files
        # Important: use the instance's method, not the class's, if it's not static
        return await original_create_method(db, project, file_data_dict)

    with patch.object(upload_service_instance, '_create_project_file_direct', side_effect=mock_create_project_file_direct, autospec=True) as mock_method:
        # Action: Call _upload_direct. It should handle the exception internally.
        created_project = await upload_service_instance._upload_direct(
            db=db_session,
            session=upload_session_obj,
            project_data=project_data,
            files=mock_files_data
        )

    # Assertions
    assert created_project is not None
    assert created_project.name == project_data.name

    # Key assertion: No ProjectFile records should have been committed for this project
    # because the transaction from _upload_direct should have been rolled back by the test fixture (db_session)
    # if the error propagated, or the final commit inside _upload_direct saved the partial state
    # The goal of the change was a *single* commit at the end of _upload_direct.
    # So, if an error happens before that final commit, nothing (files, project status update) should be committed.

    # Let's re-fetch the project to see its status
    persisted_project = await db_session.get(Project, created_project.id)
    assert persisted_project is not None # The project itself is created before file processing loop

    # Check ProjectFiles in DB for this project
    stmt = select(ProjectFile).where(ProjectFile.project_id == persisted_project.id)
    result = await db_session.execute(stmt)
    project_files_in_db = result.scalars().all()

    # Because the single commit is at the VERY end of _upload_direct, and an error occurs
    # during file processing, the updates to project.upload_status and session.status might
    # also not be committed if the error handling in _upload_direct isn't perfect or
    # if the test's db_session rollback supersedes the method's internal commit.
    # The current _upload_direct catches exceptions in the loop, updates counts, and then does a final commit.

    assert len(project_files_in_db) == 1 # Only "goodfile.txt" should have been added to session before error
                                         # and then committed by the *final* commit.
    assert project_files_in_db[0].filename == "goodfile.txt"


    # Verify UploadSession and Project status
    await db_session.refresh(upload_session_obj)
    await db_session.refresh(persisted_project)

    assert upload_session_obj.status == SessionStatus.COMPLETED # It completes but with failures
    assert upload_session_obj.processed_files == 1 # goodfile.txt
    assert upload_session_obj.failed_files == 1    # badfile.txt
    assert upload_session_obj.errors is not None
    assert len(upload_session_obj.errors) > 0
    assert "Simulated processing error for badfile.txt" in upload_session_obj.errors[0]

    assert persisted_project.upload_status == UploadStatus.COMPLETED # It's marked completed even with partial success


# TODO: Test cases for _upload_via_parser if changes affected it (not directly part of this task)
# TODO: Test cases for _extract_project_files for robustness (not directly part of this task)
