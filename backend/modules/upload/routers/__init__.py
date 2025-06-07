"""Router package for upload module."""

from fastapi import APIRouter

from modules.upload.routers.project_router import router as project_router
from modules.upload.routers.file_router import router as file_router
from modules.upload.routers.health_router import router as health_router

# Create a main router to include all sub-routers
router = APIRouter(prefix="/upload", tags=["upload"])

# Include sub-routers
router.include_router(project_router)
router.include_router(file_router)
router.include_router(health_router) 