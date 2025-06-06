# Product Requirements Document: REALM Backend Simplification

## 📋 Document Information
- **Document Type**: Product Requirements Document (PRD)
- **Project**: REALM Backend Feature Removal
- **Version**: 1.0
- **Date**: December 2024
- **Author**: Development Team

## 🎯 Executive Summary

### Objective
Simplify the REALM backend by removing advanced project management features and focusing exclusively on core codebase upload, storage, and retrieval functionality.

### Rationale
- **Complexity Reduction**: Current advanced features add unnecessary complexity for the core use case
- **Maintenance Burden**: Collaboration, analytics, and templating features require ongoing maintenance
- **Focus**: Concentrate development efforts on perfecting the core upload and analysis pipeline
- **Performance**: Reduce database complexity and improve core functionality performance

## 🔥 Features to Remove

### 1. Project Templates System
**Current Implementation**: Complete template creation, management, and usage system
- Template CRUD operations
- Template categories and metadata
- Template application to new projects
- Usage counting and ratings

**Removal Scope**: Entire templates subsystem

### 2. Collaboration Features
**Current Implementation**: Multi-user project access and team management
- User roles (owner, admin, editor, viewer)
- Invitation system
- Permission management
- Access control

**Removal Scope**: All collaboration and multi-user functionality

### 3. Version Tracking
**Current Implementation**: Git-like versioning for projects
- Version creation and management
- Snapshot storage
- Version comparison
- Rollback capabilities

**Removal Scope**: Complete versioning system

### 4. Analytics and Usage Metrics
**Current Implementation**: Comprehensive analytics tracking
- Access tracking
- Usage statistics
- Popular files identification
- User activity monitoring
- Performance metrics

**Removal Scope**: All analytics and metrics collection

### 5. Export Capabilities
**Current Implementation**: Multiple export formats and options
- ZIP export
- PDF generation
- Custom format exports
- Export link management

**Removal Scope**: All export functionality

### 6. Project Settings Management
**Current Implementation**: Extensive project configuration options
- Privacy settings
- Feature toggles
- Custom metadata
- Notification preferences

**Removal Scope**: Advanced settings (keep only basic project info)

## 📦 What Remains (Core Features)

### ✅ Keep: Core Upload System
- ZIP file upload and extraction
- Single file upload
- Parser service integration with fallback
- File content storage
- Basic file metadata (name, size, type)

### ✅ Keep: Basic Project Management
- Project creation with name and description
- Project listing
- Project retrieval
- Project deletion
- File listing within projects

### ✅ Keep: File Storage and Retrieval
- Full file content storage
- Language detection
- Binary file handling
- Content hashing (for deduplication)

### ✅ Keep: API Infrastructure
- FastAPI framework
- Database connections
- Error handling
- Health checks
- API documentation

## 🗂️ Code Removal Plan

### Phase 1: Database Schema Cleanup

#### Tables to Remove:
```sql
-- Template system
DROP TABLE project_templates;

-- Collaboration system  
DROP TABLE project_collaborators;
DROP TABLE project_tag_associations;
DROP TABLE project_tags;

-- Versioning system
DROP TABLE project_versions;

-- Analytics system
DROP TABLE project_analytics;

-- Advanced settings
DROP TABLE project_settings;
```

#### Tables to Keep:
```sql
-- Core tables only
projects (simplified)
project_files
upload_sessions
```

### Phase 2: Model Cleanup

#### Files to Remove:
```
backend/modules/projects/models.py     # Remove entirely
backend/modules/projects/schemas.py    # Remove entirely
backend/modules/projects/service.py    # Remove entirely  
backend/modules/projects/router.py     # Remove entirely
backend/modules/projects/README.md     # Remove entirely
backend/modules/projects/              # Remove entire directory
```

#### Models to Simplify:
```python
# backend/modules/upload/models.py
class Project(BaseModel, UUIDMixin):
    __tablename__ = "projects"
    
    # Keep only core fields:
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    upload_method = Column(String, nullable=False)
    upload_status = Column(String, default="pending")
    original_filename = Column(String)
    file_size = Column(BigInteger)
    parser_response = Column(JSON)  # Keep for parser integration
    parser_version = Column(String)
    
    # Keep only basic relationship
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    
    # REMOVE: All advanced relationships
    # collaborators, settings, tags, versions, analytics
```

### Phase 3: API Cleanup

#### Endpoints to Remove:
```
# Remove entire projects router
/api/v1/projects/*

# Remove from main.py:
app.include_router(projects_router, prefix="/api/v1")
```

#### Endpoints to Keep:
```
# Core upload functionality only
POST   /api/v1/upload/project
GET    /api/v1/upload/session/{session_id}
GET    /api/v1/upload/projects
GET    /api/v1/upload/projects/{project_id}
DELETE /api/v1/upload/projects/{project_id}
POST   /api/v1/upload/test-parser
GET    /api/v1/upload/health

# System endpoints
GET    /health
GET    /
```

### Phase 4: Service Layer Cleanup

#### Simplify Upload Service:
```python
# Keep only core methods:
- upload_project_intelligent()
- _extract_project_files()
- _upload_via_parser()
- _upload_direct()
- create_upload_session()

# Remove all advanced features:
- Template application
- Collaboration setup
- Analytics initialization
- Version creation
```

### Phase 5: Configuration Cleanup

#### Remove from core/config.py:
```python
# Remove entire ProjectsSettings class
# Keep only CoreSettings and UploadSettings
```

#### Environment Variables to Remove:
```bash
# All PROJECTS_* prefixed variables
PROJECTS_MAX_TEMPLATES_PER_USER
PROJECTS_MAX_COLLABORATORS_PER_PROJECT
PROJECTS_INVITATION_EXPIRY_DAYS
PROJECTS_EXPORT_MAX_FILE_SIZE
PROJECTS_ANALYTICS_RETENTION_DAYS
# etc.
```

## 🛣️ Implementation Timeline

### Week 1: Preparation
- [ ] Database backup
- [ ] Create migration scripts
- [ ] Update API documentation
- [ ] Update frontend to remove advanced UI elements

### Week 2: Backend Code Removal
- [ ] Remove projects module entirely
- [ ] Simplify upload models
- [ ] Update main.py imports and router registration
- [ ] Remove advanced configuration options

### Week 3: Database Migration
- [ ] Run migration scripts to drop advanced tables
- [ ] Update existing projects table schema
- [ ] Verify data integrity
- [ ] Update indexes for performance

### Week 4: Testing and Validation
- [ ] Test core upload functionality
- [ ] Verify file storage and retrieval
- [ ] Test parser integration
- [ ] Performance testing
- [ ] Documentation updates

## ⚠️ Migration Considerations

### Data Loss Warnings
- **All template data will be permanently lost**
- **All collaboration history will be removed**
- **All version history will be deleted**
- **All analytics data will be lost**
- **All export configurations will be removed**

### Backward Compatibility
- **Breaking Change**: This is a major breaking change
- **API Changes**: Many endpoints will be removed
- **Database Schema**: Significant schema changes
- **Frontend Impact**: Frontend must be updated simultaneously

## 🧪 Testing Strategy

### Core Functionality Tests
```bash
# Upload tests
✅ ZIP file upload
✅ Single file upload
✅ Parser service integration
✅ Direct upload fallback
✅ File extraction and storage

# Retrieval tests
✅ Project listing
✅ Project details
✅ File content retrieval
✅ File metadata access

# System tests
✅ Health checks
✅ Error handling
✅ Database connectivity
```

### Performance Benchmarks
- Upload speed for large codebases
- Database query performance
- Memory usage during file processing
- API response times

## 📊 Success Metrics

### Technical Metrics
- **Codebase Size**: Reduce by ~60% (remove ~15,000 lines)
- **Database Tables**: Reduce from 10 to 3 tables
- **API Endpoints**: Reduce from 25+ to 8 endpoints
- **Memory Usage**: Reduce baseline memory usage by 30%

### Operational Metrics
- **Deployment Time**: Faster deployments due to reduced complexity
- **Bug Rate**: Lower bug rate due to simplified codebase
- **Development Velocity**: Faster feature development on core functionality

## 🔄 Rollback Plan

### Emergency Rollback
1. **Git Revert**: Revert to commit before simplification
2. **Database Restore**: Restore from backup taken before migration
3. **Frontend Rollback**: Revert frontend to previous version
4. **Service Restart**: Restart all services

### Rollback Triggers
- **Core Upload Failure**: If basic upload functionality breaks
- **Data Corruption**: If existing project data becomes inaccessible  
- **Performance Degradation**: If system becomes slower than before
- **Critical Bug**: If P0 bugs are introduced that can't be quickly fixed

## 📝 Documentation Updates

### Files to Update
```
backend/README.md              # Remove advanced features documentation
backend/API_DOCUMENTATION.md   # Update endpoint list
backend/DATABASE_SCHEMA.md     # Simplified schema documentation
backend/DEPLOYMENT.md          # Updated deployment instructions
```

### New Documentation
```
backend/MIGRATION_GUIDE.md     # Guide for existing users
backend/SIMPLIFIED_API.md      # New simplified API reference
```

## ✅ Acceptance Criteria

### Must Have
- [ ] Core upload functionality works perfectly
- [ ] All advanced features are completely removed
- [ ] Database schema is simplified and optimized
- [ ] API documentation reflects new simplified interface
- [ ] No remnants of removed features in codebase

### Nice to Have
- [ ] Performance improvements in core functionality
- [ ] Reduced deployment package size
- [ ] Improved error messages for core features
- [ ] Updated developer documentation

## 🚀 Post-Simplification Roadmap

### Immediate Focus (Next Quarter)
1. **Perfect Core Upload**: Optimize upload speed and reliability
2. **Enhanced Parser Integration**: Improve parser service connectivity
3. **Search Functionality**: Add full-text search across uploaded files
4. **API Performance**: Optimize database queries and response times

### Future Considerations
- Simple tagging system (without collaboration complexity)
- Basic project categories (without template system)
- File-level search and filtering
- Simple export (just ZIP download)

---

## 📋 Sign-off

**Product Owner**: _________________ Date: _________
**Engineering Lead**: _____________ Date: _________
**QA Lead**: _____________________ Date: _________

---

*This PRD represents a major architectural decision to focus REALM on its core competency: intelligent codebase upload, storage, and retrieval. By removing advanced features, we can deliver a more reliable, performant, and maintainable solution.* 