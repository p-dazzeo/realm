# Implementation Plan for Modularization Improvements

## Phase 1: Critical Fixes & Foundational Changes

1. **Fix Service Layer Indentation** ✅
   - Properly indent additional file methods inside the UploadService class
   - Ensure upload_settings.additional_files_dir is defined in core/config.py

2. **Create FileStorageService** ✅
   - Create new file `backend/shared/services/file_storage.py`
   - Implement methods for save, retrieve, delete operations
   - Extract file handling logic from UploadService

3. **Extract Database Repositories** ✅
   - Create `backend/modules/upload/repositories.py`
   - Implement ProjectRepository and FileRepository
   - Move DB queries from service layer to repositories

## Phase 2: Architectural Improvements

4. **Implement Custom Exception Handling** ✅
   - Create `backend/shared/exceptions.py` with domain-specific exceptions
   - Update services to use custom exceptions
   - Add exception handlers to router

5. **Improve Configuration Management** ✅
   - Update `core/config.py` with validated settings
   - Add configuration validation on startup
   - Implement environment-based configuration

6. **Refactor Router Organization** ✅
   - Split router.py into feature-specific routers (project_router.py, file_router.py)
   - Create a main router that includes sub-routers

## Phase 2.1: Mixed QOL improvements

1. **Standardize Eager Loading Across Repositories** ✅
   - Updated `ProjectRepository.get_by_id` to eagerly load files and additional_files relationships
   - Updated `ProjectRepository.get_by_uuid` to eagerly load both relationships
   - Updated `FileRepository.get_by_id` to eagerly load the project relationship
   - Updated `FileRepository.get_files_by_project_id` to eagerly load the project relationship
   - Updated `AdditionalFileRepository.get_files_by_project_id` to eagerly load the project relationship
   - Left `UploadSessionRepository` as is since it doesn't have complex relationships

2. **Update Config in All Schema Classes** ✅
   - Updated `CoreSettings` and `UploadSettings` to use `model_config = SettingsConfigDict(...)` instead of `class Config`
   - Updated method calls from `dict()` to `model_dump()` to follow Pydantic v2 conventions
   - All schema classes in `upload/schemas.py` were already using the new style

3. **Add Typed Field Validation** ✅
   - All field validators in the codebase already had proper type annotations
   - Verified validators in `CoreSettings` and `UploadSettings` classes
   - No old-style validators (@validator) found in the codebase

4. **Repository Method for Loading with Relations** ✅
   - Added `get_by_id_with_relations` method to `ProjectRepository` allowing explicit control of which relationships to load
   - Added `get_by_id_with_relations` method to `FileRepository` allowing explicit control of which relationships to load
   - Added `get_by_id_with_relations` method to `AdditionalFileRepository` allowing explicit control of which relationships to load
   - Each method includes proper type annotations and detailed docstrings

5. **Add Transaction Management** ✅
   - Added proper transaction handling with `async with db.begin()` to all methods that modify multiple entities
   - Updated `upload_project_intelligent` method to use transactions for all database operations
   - Updated `add_additional_file_to_project` method to use transactions and added file cleanup on error
   - Updated `update_additional_file` and `delete_additional_file` methods to use transactions
   - Updated `_upload_via_parser` and `_upload_direct` methods to ensure all operations happen within transactions

6. **Use Pydantic v2 Schema Generation Features** ✅
   - Enhanced all schema classes with `json_schema_extra` containing realistic examples
   - Added detailed examples for Project, ProjectFile, and other key models
   - Improved API documentation with contextually relevant COBOL examples
   - Maintained consistent structure across all schema examples
   - Ensured all request and response models have examples

7. **Cache Common Database Queries** ✅
   - Created `TTLCache` class with time-based expiration in `shared/utils/cache.py`
   - Implemented `@cached` decorator for easy application to repository methods
   - Added cached versions of common database query methods (`get_by_id_cached`, `get_by_uuid_cached`, etc.)
   - Modified router endpoints to use cached methods with appropriate TTLs
   - Added cache bypass options to API endpoints for cases where fresh data is required

8. **Implement Connection Pooling Monitoring**: Add logging and metrics for database connection pool usage to help identify potential bottlenecks.

9. **Create Helper for Relationship Loading**: Develop a utility function to dynamically construct the SQLAlchemy query with the appropriate relationship loading:

   ```python
   def with_relationships(query, model_class, relationships: List[str]):
       for rel in relationships:
           if hasattr(model_class, rel):
               query = query.options(selectinload(getattr(model_class, rel)))
       return query
   ```

10. **Add Validation for JSON Fields**: Implement stricter validation for JSON fields using Pydantic models:

    ```python
    class JsonData(BaseModel):
        key1: str
        key2: int
        
    class ProjectWithValidatedJson(BaseModel):
        # Other fields...
        parser_response: Optional[JsonData] = None
    ```


## Phase 3: Advanced Features

7. **Add API Versioning**
   - Create versioned API routes structure
   - Implement support for API versioning in FastAPI

8. **Implement Domain Events**
   - Create `backend/shared/events.py` for event definitions
   - Add event dispatching to services
   - Implement event subscribers

9. **Enhance Dependency Injection**
   - Create service provider for dependency management
   - Update FastAPI dependencies to use service provider
   - Improve testability with dependency overrides

## Testing Strategy

- Write unit tests for each new component
- Update existing integration tests
- Add regression tests for fixed bugs

## Rollout Strategy

- Implement changes in feature branches
- Perform code reviews for each phase
- Deploy and test each phase separately in staging
- Document API changes for frontend team