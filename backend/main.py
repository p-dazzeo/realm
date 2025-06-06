from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog

from core.config import core_settings, upload_settings, validate_all_settings, get_settings, ENV
from core.database import create_tables, close_db
from modules.upload.routers import router as upload_router
from modules.upload.service import upload_service
from shared.exceptions import AppException


# Configure structured logging
import logging
import sys

# Configure standard library logging first
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting REALM backend", version="0.1.0", environment=ENV)
    
    try:
        # Validate settings
        if not validate_all_settings():
            logger.error("Settings validation failed, exiting")
            raise SystemExit("Settings validation failed")
            
        # Create database tables
        await create_tables()
        logger.info("Database initialized")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down REALM backend")
        
        # Close upload service
        await upload_service.close()
        
        # Close database connections
        await close_db()
        
        logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="REALM Backend API",
    description="Legacy Codebase Documentation Platform Backend",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    """Handle application-specific exceptions with structured response"""
    log_method = logger.warning if exc.status_code < 500 else logger.error
    
    log_kwargs = {
        "status_code": exc.status_code,
        "error_code": exc.error_code,
        "detail": exc.detail,
        "path": request.url.path
    }
    
    # Include context in log if available
    if hasattr(exc, "context") and exc.context:
        log_kwargs["context"] = exc.context
    
    log_method("Application exception", **log_kwargs)
    
    # Prepare response content
    content = {
        "error": exc.detail,
        "error_code": exc.error_code,
        "status_code": exc.status_code
    }
    
    # Include context in response if available and if not an internal error
    if hasattr(exc, "context") and exc.context and exc.status_code < 500:
        # For 5xx errors, we don't want to expose internal details to clients
        content["context"] = exc.context
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured logging"""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )


# Include routers
app.include_router(upload_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "REALM Backend API",
        "version": "0.1.0",
        "description": "Legacy Codebase Documentation Platform Backend",
        "docs": "/docs",
        "health": "/api/v1/upload/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "service": "realm-backend",
        "version": "0.1.0",
        "environment": ENV,
        "parser_enabled": upload_settings.parser_service_enabled,
        "parser_url": upload_settings.parser_service_url if upload_settings.parser_service_enabled else None
    }

# Configuration endpoint (only exposed in non-production environments)
@app.get("/config")
async def get_configuration():
    """Get application configuration"""
    if ENV == "production":
        return {"message": "Configuration not available in production"}
    
    return get_settings()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=core_settings.api_host,
        port=core_settings.api_port,
        reload=core_settings.api_reload,
        log_level=core_settings.log_level.lower()
    ) 