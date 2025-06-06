# REALM Backend

A FastAPI-based backend service for the REALM Legacy Codebase Documentation Platform. Provides intelligent codebase upload, storage, and management with optional external parser integration.

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
uv run python -m app.main
```

API Documentation: `http://localhost:8000/docs`

## 🏗️ Architecture

The backend uses an **intelligent upload system** that automatically tries the parser service first, then falls back to direct upload if needed.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   File Upload   │───▶│  Upload Service  │───▶│   PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Parser Service   │ (Optional)
                    │ External API     │
                    └──────────────────┘
```

### Core Components

- **FastAPI Application**: RESTful API with automatic documentation
- **Upload Service**: Intelligent dual-method upload handling
- **Database Layer**: PostgreSQL with JSONB for structured/unstructured data
- **Parser Integration**: Optional external service for advanced code analysis

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

### Upload Management
```http
POST   /api/v1/upload/project           # Upload project (ZIP/single file)
GET    /api/v1/upload/session/{id}      # Get upload session status
GET    /api/v1/upload/projects          # List projects (paginated)
GET    /api/v1/upload/projects/{id}     # Get project details
DELETE /api/v1/upload/projects/{id}     # Delete project
```

### Utility
```http
POST   /api/v1/upload/test-parser       # Test parser service connection
GET    /api/v1/upload/health            # Service health check
GET    /health                          # Application health check
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

## 🧩 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application setup
│   ├── config.py            # Environment configuration
│   ├── database.py          # Database connection and setup
│   ├── models.py            # SQLAlchemy data models
│   ├── schemas.py           # Pydantic request/response models
│   ├── api/
│   │   └── upload.py        # Upload endpoints
│   └── services/
│       └── upload_service.py # Core upload logic
├── pyproject.toml           # Dependencies and project config
└── README.md               # This documentation
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

### Adding New Features
- **Models**: Add to `app/models.py`
- **Schemas**: Add to `app/schemas.py` 
- **Endpoints**: Create new router in `app/api/`
- **Services**: Add business logic to `app/services/`

### Key Dependencies
- `fastapi`: Web framework
- `sqlalchemy`: Database ORM
- `asyncpg`: PostgreSQL async driver
- `pydantic`: Data validation
- `structlog`: Structured logging
- `httpx`: HTTP client for parser service

---

**Version**: 0.1.0 | **License**: MIT | **Python**: 3.11+