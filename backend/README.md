# GenDoc Service

GenDoc is a FastAPI-based service for generating code documentation using LLMs and custom workflows.

## Overview

The GenDoc service allows users to:
- Upload code projects (as ZIP files)
- Generate various types of documentation
- Execute customizable documentation workflows
- Access project files and metadata

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API root |
| `/health` | GET | Health check |
| `/projects` | GET | List all available projects |
| `/generate` | POST | Generate documentation |
| `/upload` | POST | Upload a project ZIP file |
| `/projects/{project_id}/files` | GET | List files in a project |
| `/workflows/` | GET | List all available workflows |
| `/workflows/{workflow_name}` | GET | Get a specific workflow |

## Workflow System

GenDoc implements a customizable workflow system for documentation generation.

### Workflow Storage

Workflows are stored as JSON files in:
```
backend/gendoc/storage/_workflows/
```

### Workflow Structure

Each workflow is defined by:

```json
{
  "name": "workflow_name",
  "description": "Workflow description",
  "doc_type": "OVERVIEW|ARCHITECTURE|COMPONENT|FUNCTION|API",
  "steps": [
    {
      "name": "step_name",
      "prompt": "Prompt template for the LLM",
      "inputs": ["context", "previous_step_output"],
      "output_type": "text"
    }
  ]
}
```

### Workflow Execution Process

1. **Workflow Selection**: The client specifies a workflow by name or uses a default based on documentation type
2. **Context Preparation**: The service loads the project files and prepares the context
3. **Step Execution**: Each step in the workflow is executed sequentially:
   - Inputs from previous steps are collected
   - The prompt is filled with inputs
   - The LLM generates output for the step
4. **Result Compilation**: The final step's output becomes the documentation result

### Using Workflows

To use a workflow:

1. **List available workflows**:
   ```
   GET /workflows/
   ```

2. **Generate documentation with a specific workflow**:
   ```
   POST /generate
   {
     "project_id": "your_project",
     "doc_type": "OVERVIEW",
     "workflow_type": "workflow_name"
   }
   ```

## Configuration

The service is configured via environment variables or .env file:

- `OPENAI_API_KEY`: API key for LLM access
- `DEFAULT_MODEL`: Default LLM model (default: "gpt-4o")
- `LOG_LEVEL`: Logging level
- `STORAGE_DIR`: Custom storage directory path

## Directory Structure

```
gendoc/
├── main.py           # FastAPI application
├── llm.py            # LLM integration
├── config.py         # Configuration
├── storage/          # Project storage
│   └── _workflows/   # Workflow definitions
└── Dockerfile        # Docker configuration
```

## Running the Service

```bash
# Start only GenDoc
python run.py --gendoc-only

# Start with all services
python run.py
```

The service runs on port 8000 by default. 