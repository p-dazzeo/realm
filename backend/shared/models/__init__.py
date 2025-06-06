from shared.models.base import BaseModel, UUIDMixin

from modules.upload.models import Project, ProjectFile, UploadSession

# Import projects models
from modules.projects.models import (
    ProjectTemplate,
    ProjectCollaborator, 
    ProjectSettings,
    ProjectTag,
    ProjectTagAssociation,
    ProjectVersion,
    ProjectAnalytics
)

# Export all models for easy importing
__all__ = [
    "BaseModel",
    "UUIDMixin", 
    "Project",
    "ProjectFile",
    "UploadSession",
    "ProjectTemplate",
    "ProjectCollaborator",
    "ProjectSettings", 
    "ProjectTag",
    "ProjectTagAssociation",
    "ProjectVersion",
    "ProjectAnalytics"
]



