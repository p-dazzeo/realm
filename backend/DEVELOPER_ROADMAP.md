# Developer Roadmap - REALM Backend Refactoring

## 🎯 Overview
This roadmap provides concrete, actionable steps for implementing the modular architecture. Follow these phases sequentially for a smooth transition.

## 📋 Prerequisites
- [ ] Review documentation (`README.md`, `TODO.md`, `REFACTOR_DEMO.md`)
- [ ] Ensure current backend works: `uv run python -m app.main`
- [ ] Create backup: `git checkout -b backup/pre-refactoring`
- [ ] Create feature branch: `git checkout -b feature/modular-architecture`

---

## 🚀 Phase 1: Foundation Setup (Week 1-2)
**Goal**: Create modular structure without breaking existing functionality

### Step 1.1: Create Directory Structure (Day 1)
```bash
# In backend/ directory
mkdir -p core shared/{models,schemas,utils} modules/{upload/parsers} integrations

# Create __init__.py files
touch core/__init__.py shared/__init__.py shared/models/__init__.py
touch shared/schemas/__init__.py shared/utils/__init__.py
touch modules/__init__.py modules/upload/__init__.py modules/upload/parsers/__init__.py
touch integrations/__init__.py
```

### Step 1.2: Extract Core Infrastructure (Day 2-3)

#### A. Create `core/config.py`
```python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class CoreSettings(BaseSettings):
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/realm_db")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    secret_key: str = Field(default="your-secret-key-change-in-production")
    log_level: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"

class UploadSettings(BaseSettings):
    parser_service_url: str = Field(default="http://localhost:8001")
    parser_service_enabled: bool = Field(default=True)
    parser_service_timeout: int = Field(default=30)
    max_file_size: int = Field(default=50)
    max_project_size: int = Field(default=500)
    allowed_extensions: List[str] = Field(default=[
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".hpp", ".cs", ".rb", ".go", ".rs", ".php", ".html", ".css",
        ".sql", ".md", ".txt", ".json", ".xml", ".yaml", ".yml"
    ])
    
    class Config:
        env_file = ".env"
        env_prefix = "UPLOAD_"

# Global settings instances
core_settings = CoreSettings()
upload_settings = UploadSettings()
settings = core_settings  # Backward compatibility
```

#### B. Create `core/dependencies.py`
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db

async def get_database() -> AsyncSession:
    async for db in get_db():
        yield db

async def get_current_user():
    """Placeholder for future authentication"""
    return {"user_id": "anonymous", "role": "user"}
```

### Step 1.3: Create Shared Components (Day 4)

#### A. Create `shared/models/base.py`
```python
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.sql import func
from core.database import Base
import uuid

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UUIDMixin:
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
```

### Step 1.4: Extract Upload Module (Day 5-7)

#### A. Move models from `app/models.py` to `modules/upload/models.py`
#### B. Move schemas from `app/schemas.py` to `modules/upload/schemas.py`  
#### C. Move service from `app/services/upload_service.py` to `modules/upload/service.py`
#### D. Move router from `app/api/upload.py` to `modules/upload/router.py`

### Step 1.5: Update Main Application (Day 8)
Create new `main.py` with modular imports

### Step 1.6: Testing & Validation (Day 9-10)
```bash
uv run python main.py
curl http://localhost:8000/docs
# Test all existing functionality
```

---

## 🔧 Phase 2: New Modules (Week 3-8)

### Step 2.1: Projects Module (Week 3-4)
- Enhanced project management
- Templates and collaboration
- Export functionality

### Step 2.2: Chat Module (Week 5-6)  
- Conversation management
- LLM integration
- Context-aware responses

### Step 2.3: GenDoc Module (Week 7-8)
- Documentation generation
- Multiple output formats
- Template system

---

## 🎨 Phase 3: Enhancements (Week 9-16)

### Step 3.1: Authentication Module (Week 9-10)
- User management
- JWT authentication
- Role-based access

### Step 3.2: Testing Framework (Week 11-12)
- Comprehensive test coverage
- Integration tests
- Performance testing

### Step 3.3: Performance Optimizations (Week 13-14)
- Redis caching
- Background jobs
- Query optimization

### Step 3.4: Deployment Setup (Week 15-16)
- Docker containerization
- CI/CD pipeline
- Monitoring setup

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] All existing endpoints work unchanged
- [ ] Database operations function correctly  
- [ ] Upload functionality works (parser + direct)
- [ ] No breaking changes to API
- [ ] New modular structure is in place

### Phase 2 Complete When:
- [ ] Projects module provides enhanced management
- [ ] Chat module enables LLM conversations
- [ ] GenDoc module generates documentation
- [ ] All modules are properly isolated

### Phase 3 Complete When:
- [ ] Authentication system is functional
- [ ] Performance improvements are measurable
- [ ] Deployment pipeline works
- [ ] Comprehensive testing is in place

---

## 🛠 Development Guidelines

- **Code Standards**: Follow existing patterns, add type hints, include docstrings
- **Testing**: Unit tests for services, integration tests for APIs
- **Database**: Use Alembic for migrations, test on sample data
- **Documentation**: Update README.md as features are added

**Ready to start?** Begin with Phase 1, Step 1.1! 🚀 