# REALM Backend

A FastAPI-based backend service for the REALM Legacy Codebase Documentation Platform. Features modular architecture with intelligent codebase upload, enhanced project management, collaboration tools, and extensible module system.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup
```bash
# 1. Clone and navigate
cd backend

# 2. Install dependencies
uv sync

# 3. Setup database
createdb realm_db

# 4. Configure environment
cp .env.example .env
# Edit .env with your database URL and settings

# 5. Run the application
uv run python main.py
```

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
                    │ Upload │Projects │
                    │ Chat   │GenDoc   │ (Planned)
                    └──────────────────┘
```

### Modular Components

- **Core Infrastructure**: Configuration, database, dependencies
- **Upload Module**: Intelligent file upload with parser integration  
- **Projects Module**: ✅ Enhanced project management, collaboration, templates
- **Chat Module**: 🔄 LLM integration (Planned)
- **GenDoc Module**: 🔄 Documentation generation (Planned)
- **Shared Components**: Base models, utilities, schemas

## 📊 Database Schema

### Projects
Stores project metadata, upload information, and parser responses
```sql
- id, uuid, name, description
- upload_method (parser/direct), upload_status
- parser_response (JSONB), parser_version
- file metadata (original_filename, file_size)
- timestamps
```

### Project Files
Individual file storage with content and metadata
```sql
- project_id (FK), filename, file_path, relative_path
- content, content_hash, file_size
- parsed_data (JSONB from parser)
- language detection, LOC, is_binary flag
- timestamps
```

### Upload Sessions
Progress tracking and error collection
```sql
- session_id (UUID), status, upload_method
- progress counters (total/processed/failed files)
- errors and warnings (JSON arrays)
- project_id (FK), expiration
```

## 🔌 API Endpoints

### Upload Module
```http
POST   /api/v1/upload/project           # Upload project (ZIP/single file)
GET    /api/v1/upload/session/{id}      # Get upload session status
GET    /api/v1/upload/projects          # List projects (paginated)
GET    /api/v1/upload/projects/{id}     # Get project details
DELETE /api/v1/upload/projects/{id}     # Delete project
POST   /api/v1/upload/test-parser       # Test parser service connection
GET    /api/v1/upload/health            # Upload module health check
```

### Projects Module ✅
```http
# Templates
POST   /api/v1/projects/templates       # Create project template
GET    /api/v1/projects/templates       # List templates with filtering
GET    /api/v1/projects/templates/{id}  # Get specific template

# Enhanced Projects
POST   /api/v1/projects/                # Create enhanced project
GET    /api/v1/projects/                # Search projects with advanced filtering
GET    /api/v1/projects/{id}            # Get project with relationships
PUT    /api/v1/projects/{id}            # Update project

# Collaboration
POST   /api/v1/projects/{id}/collaborators        # Add collaborator
GET    /api/v1/projects/{id}/collaborators        # List collaborators
PUT    /api/v1/projects/collaborators/{id}        # Update collaborator
DELETE /api/v1/projects/{id}/collaborators/{uid}  # Remove collaborator

# Settings & Analytics
GET    /api/v1/projects/{id}/settings    # Get project settings
PUT    /api/v1/projects/{id}/settings    # Update project settings
GET    /api/v1/projects/{id}/analytics   # Get project analytics

# Versioning & Export
POST   /api/v1/projects/{id}/versions    # Create project version
GET    /api/v1/projects/{id}/versions    # List project versions
POST   /api/v1/projects/{id}/export      # Export project
GET    /api/v1/projects/health           # Projects module health check
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
│   ├── upload/             # Upload functionality
│   │   ├── models.py       # Upload-specific models
│   │   ├── schemas.py      # Upload schemas
│   │   ├── service.py      # Upload business logic
│   │   ├── router.py       # Upload API endpoints
│   │   └── parsers/        # Parser implementations
│   └── projects/           # ✅ Enhanced project management
│       ├── models.py       # Project templates, collaboration, etc.
│       ├── schemas.py      # Project management schemas
│       ├── service.py      # Project business logic
│       ├── router.py       # Project API endpoints
│       └── README.md       # Projects module documentation
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
- ✅ **Projects Module**: Enhanced project management with collaboration
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