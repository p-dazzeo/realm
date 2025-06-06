from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db

async def get_database() -> AsyncSession:
    async for db in get_db():
        yield db

async def get_current_user():
    """Placeholder for future authentication"""
    return {"user_id": "anonymous", "role": "user"} 