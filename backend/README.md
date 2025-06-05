# REALM Backend

Legacy Codebase Documentation Platform Backend - A FastAPI-based service for intelligently uploading and storing legacy codebases with LLM integration capabilities.

## Features

- **Intelligent Upload System**: Automatically tries parser service first, falls back to direct upload
- **Dual Upload Methods**:
  - **Parser Method**: Uses external parser service for structured codebase analysis
  - **Direct Method**: Simple file-by-file storage with metadata extraction
- **PostgreSQL with JSON**: Flexible storage for both structured and unstructured data
- **Real-time Progress Tracking**: Upload sessions with detailed progress and error reporting
- **Language Detection**: Automatic programming language identification
- **Archive Support**: Handles ZIP, TAR, and single file uploads
- **RESTful API**: Comprehensive endpoints for project management

## Architecture

```
REALM Backend
├── FastAPI Application
├── PostgreSQL Database (with JSONB)
├── Upload Service (Intelligent Fallback)
├── Parser Service Integration
└── Structured Logging
```

## Database Schema

### Projects Table
- Basic project metadata
- Upload method tracking (parser/direct)
- Parser response storage (JSON)
- Upload status tracking

### Project Files Table
- Individual file storage
- Content and metadata
- Language detection
- Parsed data (JSON for parser results)

### Upload Sessions Table
- Progress tracking
- Error and warning collection
- Session management

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- uv (Python package manager)

### 1. Setup Database

```bash
# Create PostgreSQL database
createdb realm_db

# Or using Docker
docker run --name realm-postgres \
  -e POSTGRES_DB=realm_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:14
```

### 2. Install Dependencies

```bash
cd backend
uv sync
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/realm_db
SECRET_KEY=your-secure-secret-key
PARSER_SERVICE_URL=http://localhost:8001
PARSER_SERVICE_ENABLED=true
```

### 4. Run the Application

```bash
# Development mode
uv run python -m app.main

# Or using uvicorn directly
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## API Endpoints

### Upload Endpoints

#### Upload Project
```bash
POST /api/v1/upload/project
Content-Type: multipart/form-data

Parameters:
- project_name: string (required)
- project_description: string (optional)
- file: file (required) - ZIP archive or single file
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload/project" \
  -F "project_name=My Legacy Project" \
  -F "project_description=Old PHP application" \
  -F "file=@project.zip"
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": 1,
  "upload_method": "parser",
  "message": "Project 'My Legacy Project' uploaded successfully using parser method",
  "warnings": null
}
```

#### Get Upload Session
```bash
GET /api/v1/upload/session/{session_id}
```

#### List Projects
```bash
GET /api/v1/upload/projects?skip=0&limit=50&upload_method=parser
```

#### Get Project Details
```bash
GET /api/v1/upload/projects/{project_id}?include_files=true
```

#### Delete Project
```bash
DELETE /api/v1/upload/projects/{project_id}
```

### Utility Endpoints

#### Test Parser Service
```bash
POST /api/v1/upload/test-parser
```

#### Health Check
```bash
GET /health
GET /api/v1/upload/health
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/realm_db` | Database connection URL |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT secret key |
| `PARSER_SERVICE_URL` | `http://localhost:8001` | External parser service URL |
| `PARSER_SERVICE_ENABLED` | `true` | Enable/disable parser service |
| `PARSER_SERVICE_TIMEOUT` | `30` | Parser service timeout (seconds) |
| `MAX_FILE_SIZE` | `50` | Maximum file size (MB) |
| `MAX_PROJECT_SIZE` | `500` | Maximum project size (MB) |
| `LOG_LEVEL` | `INFO` | Logging level |

### Allowed File Extensions

The system accepts these file types by default:
- **Legacy**: `cbl` `jcl`
- **Data**: `.sql`, `.json`, `cpy`
- **Documentation**: `.md`, `.txt`

## Intelligent Upload Logic

1. **Parser First**: If `PARSER_SERVICE_ENABLED=true`, attempts to use external parser
2. **Fallback**: If parser fails or is unavailable, automatically switches to direct upload
3. **Progress Tracking**: Real-time session updates with file counts and errors
4. **Error Handling**: Comprehensive error collection and reporting

### Upload Flow

```mermaid
graph TD
    A[File Upload] --> B[Extract Files]
    B --> C{Parser Enabled?}
    C -->|Yes| D[Try Parser Service]
    C -->|No| G[Direct Upload]
    D --> E{Parser Success?}
    E -->|Yes| F[Store with Parser Data]
    E -->|No| G[Direct Upload]
    G --> H[Store Files Directly]
    F --> I[Complete]
    H --> I[Complete]
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/
│   │   └── upload.py        # Upload endpoints
│   └── services/
│       └── upload_service.py # Upload logic
├── alembic/                 # Database migrations
├── alembic.ini             # Alembic configuration
├── pyproject.toml          # Project dependencies
└── README.md               # This file
```

### Adding New Features

1. **New Models**: Add to `app/models.py`
2. **New Schemas**: Add to `app/schemas.py`
3. **New Endpoints**: Create router in `app/api/`
4. **New Services**: Add to `app/services/`


## Parser Service Integration

The backend expects a parser service with the following interface:

### Parser Service Endpoints

# TODO: review & refine parser interface

#### Parse Project
```bash
POST /parse
Content-Type: application/json

{
  "project_name": "string",
  "files": [
    {
      "filename": "string",
      "relative_path": "string",
      "content": "string",
      "size": "integer"
    }
  ]
}
```

#### Health Check
```bash
GET /health
```

### Parser Response Format

```json
{
  "success": true,
  "version": "1.0.0",
  "data": {
    "project_summary": { ... },
    "files": {
      "path/to/file.py": {
        "language": "python",
        "functions": [...],
        "classes": [...],
        "dependencies": [...],
        "complexity": 5
      }
    },
    "dependencies": [...],
    "architecture": { ... }
  },
  "error": null
}
```

## Monitoring and Logging

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Endpoints**: Application and service health checks
- **Error Tracking**: Comprehensive error collection and reporting
- **Progress Monitoring**: Real-time upload progress tracking

## Security

- **Input Validation**: Comprehensive file type and size validation
- **File Filtering**: Automatic exclusion of hidden and system files
- **Size Limits**: Configurable file and project size limits
- **Error Handling**: Safe error messages without information leakage

## Deployment

### Docker

# TODO: review uv usage in docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync

COPY app/ app/

CMD ["uv", "run", "python", "-m", "app.main"]
```

### Environment Setup

1. Set up PostgreSQL database
2. Configure environment variables
3. Run database migrations
4. Start the application