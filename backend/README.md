# REALM Backend

A FastAPI-based backend service for the REALM Legacy Codebase Documentation Platform. Features modular architecture with intelligent codebase upload, enhanced project management, collaboration tools, and extensible module system.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- [uv](https://docs.astral.sh/uv/) package manager


API Documentation: `http://localhost:8000/docs`

## 🏗️ Architecture

REALM backend features a **modular architecture** with feature-based modules and an intelligent upload system.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Request   │───▶│  Module Router   │───▶│   PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Module Services  │
                    │ Upload (Project Handling) │
                    │ Chat, GenDoc (Planned)    │
                    └──────────────────┘
```

### Modular Components

- **Core Infrastructure**: Configuration, database, dependencies
- **Upload Module**: Intelligent file upload with parser integration  
- **Project Management**: (Currently, basic project creation and management are integrated within the Upload Module. Advanced features like templates and collaboration are planned for a future dedicated Projects Module.)
- **Chat Module**: 🔄 LLM integration (Planned)
- **GenDoc Module**: 🔄 Documentation generation (Planned)
- **Shared Components**: Base models, utilities, schemas

## 📊 Database Schema

### Projects
Stores project metadata, upload information, and parser responses.
```sql
- id, uuid, created_at, updated_at
- name, description
- upload_method, upload_status
- original_filename, file_size
- parser_response, parser_version
```

### Project Files
Individual file storage with content and metadata.
```sql
- id, created_at, updated_at
- project_id (FK)
- filename, file_path, relative_path, file_extension, file_size
- content, content_hash
- parsed_data
- language, loc, is_binary
```

### Upload Sessions
Progress tracking and error collection for uploads.
```sql
- id, created_at, updated_at
- session_id
- status, upload_method
- total_files, processed_files, failed_files
- errors, warnings
- project_id (FK), expires_at
```

### Additional Project Files
Stores supplementary files associated with a project, such as documentation, configuration files, or datasets.
```sql
- id, uuid, created_at, updated_at
- project_id (FK)
- filename, file_path, file_size
- description
```

## 🔌 API Endpoints

### Upload Module

**Upload Project**
```http
POST   /api/v1/upload/project
```
Uploads a project (ZIP archive or single file) using intelligent method selection (parser first, then direct fallback).
- Request: `multipart/form-data`
  - `project_name: str` (form data)
  - `project_description: Optional[str]` (form data)
  - `file: UploadFile` (file data)
- Response: `UploadResponse`
  ```json
  {
    "success": true,
    "session_id": "sess_12345abcde",
    "project_id": 1,
    "upload_method": "parser",
    "message": "Project uploaded successfully",
    "warnings": ["One file was skipped due to unsupported extension"]
  }
  ```

**Get Upload Session Status**
```http
GET    /api/v1/upload/session/{session_id}
```
Retrieves the status and progress of an upload session.
- Path Parameter: `session_id: str`
- Response: `UploadSessionSchema`
  ```json
  {
    "id": 1,
    "session_id": "sess_12345abcde",
    "status": "completed",
    "upload_method": "parser",
    "total_files": 10,
    "processed_files": 9,
    "failed_files": 1,
    "errors": ["Error parsing file XYZ.CBL: Invalid syntax at line 42"],
    "warnings": ["File ABC.CPY contains deprecated COBOL syntax"],
    "project_id": 1,
    "created_at": "2023-01-15T10:25:00Z",
    "updated_at": "2023-01-15T10:35:00Z",
    "expires_at": "2023-01-16T10:25:00Z"
  }
  ```

**List Projects**
```http
GET    /api/v1/upload/projects
```
Lists all projects with pagination and filtering.
- Query Parameters:
  - `skip: int = 0`
  - `limit: int = 50`
  - `upload_method: Optional[UploadMethod] = None` (e.g., "parser" or "direct")
- Response: `List[ProjectSummary]`
  ```json
  [
    {
      "id": 1,
      "name": "Payroll System",
      "description": "Legacy payroll processing system",
      "uuid": "12345678-abcd-1234-efgh-1234567890ab",
      "upload_method": "parser",
      "upload_status": "completed",
      "file_count": 15,
      "total_size": 5250000,
      "created_at": "2023-01-15T10:30:00Z"
    }
  ]
  ```

**Get Project Details**
```http
GET    /api/v1/upload/projects/{project_id}
```
Gets a specific project, optionally including its files.
- Path Parameter: `project_id: int`
- Query Parameter: `include_files: bool = True`
- Response: `ProjectSchema`
  ```json
  {
    "id": 1,
    "name": "Payroll System",
    "description": "Legacy payroll processing system",
    "uuid": "12345678-abcd-1234-efgh-1234567890ab",
    "upload_method": "parser",
    "upload_status": "completed",
    "original_filename": "payroll_system.zip",
    "file_size": 5250000,
    "parser_response": {"summary": "10 COBOL programs, 5 copybooks"},
    "parser_version": "1.2.0",
    "created_at": "2023-01-15T10:30:00Z",
    "updated_at": "2023-01-15T10:35:25Z",
    "files": [
      {
        "id": 1,
        "filename": "PAYROLL.CBL",
        "file_path": "src/PAYROLL.CBL",
        "relative_path": "src/PAYROLL.CBL",
        "file_extension": ".CBL",
        "file_size": 12500,
        "content": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. PAYROLL.\n       ...",
        "content_hash": "a1b2c3d4e5f6...",
        "parsed_data": {"variables": ["EMPLOYEE-ID", "SALARY"], "paragraphs": ["CALCULATE-SALARY"]},
        "language": "cobol",
        "loc": 150,
        "is_binary": false,
        "created_at": "2023-01-15T12:30:45Z",
        "updated_at": "2023-01-15T14:20:15Z"
      }
    ],
    "additional_files": []
  }
  ```

**Delete Project**
```http
DELETE /api/v1/upload/projects/{project_id}
```
Deletes a project and all its associated files.
- Path Parameter: `project_id: int`
- Response:
  ```json
  {
    "message": "Project '[project_name]' deleted successfully"
  }
  ```

**Test Parser Service Connection**
```http
POST   /api/v1/upload/test-parser
```
Tests if the external parser service is available and responsive.
- Response (Success):
  ```json
  {
    "parser_available": true,
    "parser_url": "http://localhost:8001",
    "status": "healthy"
  }
  ```
- Response (Failure - Unhealthy):
  ```json
  {
    "parser_available": false,
    "parser_url": "http://localhost:8001",
    "status": "unhealthy (status: 503)"
  }
  ```
- Response (Failure - Error):
  ```json
  {
    "parser_available": false,
    "parser_url": "http://localhost:8001",
    "status": "error: Connection refused"
  }
  ```

**Upload Module Health Check**
```http
GET    /api/v1/upload/health
```
Provides a health check for the upload module.
- Response:
  ```json
  {
    "status": "healthy",
    "service": "realm-upload-service",
    "timestamp": "15/01/2023Y10:30:00" 
  }
  ```
  *(Timestamp is an example, actual value will vary)*

**Upload Additional File for Project**
```http
POST   /api/v1/upload/projects/{project_id}/additional_files
```
Uploads an additional file (e.g., documentation, configuration) for a specific project.
- Path Parameter: `project_id: int`
- Request: `multipart/form-data`
  - `file: UploadFile` (file data)
  - `description: Optional[str]` (form data, optional)
- Response: `AdditionalProjectFileSchema`
  ```json
  {
    "id": 2,
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "requirements.docx",
    "file_path": "/storage/additional_files/project_12345/requirements.docx",
    "file_size": 2500000,
    "description": "Project requirements document",
    "created_at": "2023-01-16T09:45:30Z",
    "updated_at": "2023-01-16T09:45:30Z"
  }
  ```

**Get Specific Additional File**
```http
GET    /api/v1/upload/projects/{project_id}/additional_files/{additional_file_id}
```
Retrieves a specific additional file by its ID, associated with a project.
- Path Parameters:
  - `project_id: int`
  - `additional_file_id: int`
- Response: `AdditionalProjectFileSchema`
  ```json
  {
    "id": 2,
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "requirements.docx",
    "file_path": "/storage/additional_files/project_12345/requirements.docx",
    "file_size": 2500000,
    "description": "Project requirements document",
    "created_at": "2023-01-16T09:45:30Z",
    "updated_at": "2023-01-16T09:45:30Z"
  }
  ```

**Update Additional File Metadata**
```http
PUT    /api/v1/upload/projects/{project_id}/additional_files/{additional_file_id}
```
Updates the metadata (e.g., description) of an additional file.
- Path Parameters:
  - `project_id: int`
  - `additional_file_id: int`
- Request Body: `AdditionalFileUpdateRequest`
  ```json
  {
    "description": "Updated technical documentation"
  }
  ```
- Response: `AdditionalProjectFileSchema`
  ```json
  {
    "id": 2,
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "requirements.docx",
    "file_path": "/storage/additional_files/project_12345/requirements.docx",
    "file_size": 2500000,
    "description": "Updated technical documentation",
    "created_at": "2023-01-16T09:45:30Z",
    "updated_at": "2023-01-16T10:00:00Z" 
  }
  ```
  *(updated_at is an example, actual value will vary)*

**Delete Specific Additional File**
```http
DELETE /api/v1/upload/projects/{project_id}/additional_files/{additional_file_id}
```
Deletes a specific additional file associated with a project.
- Path Parameters:
  - `project_id: int`
  - `additional_file_id: int`
- Response:
  ```json
  {
    "message": "Additional file deleted successfully"
  }
  ```

### System
```http
GET    /health                          # Application health check
GET    /                                # API information
```

### Example Upload
```bash
curl -X POST "http://localhost:8000/api/v1/upload/project" \
  -F "project_name=Legacy System" \
  -F "project_description=Old COBOL application" \
  -F "file=@codebase.zip"
```

## 🔧 Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Database connection |
| `PARSER_SERVICE_URL` | `http://localhost:8001` | External parser URL |
| `PARSER_SERVICE_ENABLED` | `true` | Enable parser integration |
| `MAX_FILE_SIZE` | `50` | Max file size (MB) |
| `MAX_PROJECT_SIZE` | `500` | Max project size (MB) |

## 🔄 Upload Flow

The system implements intelligent upload routing:

1. **File Validation**: Check file type, size, and format
2. **Parser Attempt**: If enabled, try external parser service
3. **Fallback Logic**: On parser failure, automatically switch to direct upload
4. **Progress Tracking**: Real-time session updates with file counts
5. **Error Collection**: Comprehensive error and warning aggregation

```python
# Upload methods available
UploadMethod.PARSER   # External parser service
UploadMethod.DIRECT   # Direct file storage
```

## 🧩 Modular Project Structure

```
backend/
├── core/                    # Core infrastructure
│   ├── config.py           # Enhanced configuration system
│   ├── database.py         # Database connection and setup  
│   └── dependencies.py     # FastAPI dependency injection
├── shared/                  # Cross-cutting concerns
│   ├── models/
│   │   └── base.py         # Base model classes
│   ├── schemas/            # Common schemas
│   └── utils/              # Shared utilities
├── modules/                 # Feature modules
│   └── upload/             # Upload functionality
│       ├── models.py       # Upload-specific models
│       ├── schemas.py      # Upload schemas
│       ├── service.py      # Upload business logic
│       ├── router.py       # Upload API endpoints
│       └── parsers/        # Parser implementations
├── integrations/           # External service integrations
├── main.py                 # Application entry point
├── pyproject.toml          # Dependencies and project config
└── README.md              # This documentation
```

## 🔌 Parser Service Integration

The backend expects an external parser service with this interface:

```python
# Parser Service API
POST /parse              # Parse project files
GET  /health             # Health check

# Expected Response Format
{
  "success": true,
  "version": "1.0.0",
  "data": {
    "project_summary": {...},
    "files": {
      "file.py": {
        "language": "python",
        "functions": [...],
        "classes": [...],
        "dependencies": [...],
        "complexity": 5
      }
    },
    "dependencies": [...],
    "architecture": {...}
  },
  "error": null
}
```

## 🐳 Deployment

### Docker Example
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync
COPY app/ app/
CMD ["uv", "run", "python", "-m", "app.main"]
```

### Environment Setup
1. PostgreSQL database with appropriate permissions
2. Environment variables configured
3. Optional parser service running
4. File storage directory with write permissions

## 📝 Development

### Module Development
Follow the established patterns from the upload and projects modules:

1. **Create Module Directory**: `modules/new_module/`
2. **Add Models**: `models.py` with SQLAlchemy models
3. **Define Schemas**: `schemas.py` with Pydantic models  
4. **Implement Service**: `service.py` with business logic
5. **Create Router**: `router.py` with FastAPI endpoints
6. **Register in Main**: Import and include router in `main.py`

### Current Modules
- ✅ **Upload Module**: File upload with parser integration
- 🔄 **Projects Module**: Advanced features like collaboration and templates are planned. Basic project functionalities are part of the Upload Module.
- 🔄 **Chat Module**: LLM integration (Planned)
- 🔄 **GenDoc Module**: Documentation generation (Planned)

### Key Dependencies
- `fastapi`: Web framework
- `sqlalchemy`: Database ORM
- `asyncpg`: PostgreSQL async driver
- `pydantic`: Data validation
- `structlog`: Structured logging
- `httpx`: HTTP client for parser service

---

**Version**: 0.1.0 | **License**: MIT | **Python**: 3.11+