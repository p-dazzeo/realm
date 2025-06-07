"""
Health check and service test endpoints for the upload module.
"""
from fastapi import APIRouter, HTTPException
import structlog

from core.config import upload_settings
from modules.upload.service import upload_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Check the health of the upload service.
    
    Returns basic information about the service configuration and status.
    """
    return {
        "status": "healthy",
        "upload_service": "online",
        "parser_enabled": upload_settings.parser_service_enabled,
        "parser_url": upload_settings.parser_service_url if upload_settings.parser_service_enabled else None,
        "max_file_size": f"{upload_settings.max_file_size}MB",
        "max_project_size": f"{upload_settings.max_project_size}MB"
    }


@router.post("/test-parser")
async def test_parser_service():
    """
    Test if the parser service is available and responsive.
    
    This endpoint attempts to connect to the parser service
    and reports its status.
    """
    try:
        response = await upload_service.http_client.get(
            f"{upload_service.http_client.base_url}/health"
        )
        
        if response.status_code == 200:
            return {
                "parser_available": True,
                "parser_url": upload_service.http_client.base_url,
                "status": "healthy"
            }
        else:
            return {
                "parser_available": False,
                "parser_url": upload_service.http_client.base_url,
                "status": "unhealthy",
                "error": f"Status code: {response.status_code}"
            }
    except Exception as e:
        logger.error("Parser service test failed", error=str(e))
        return {
            "parser_available": False,
            "parser_url": upload_service.http_client.base_url,
            "status": "unreachable",
            "error": str(e)
        } 