"""
Cache utilities for improving application performance.
"""
import time
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, ParamSpec, Concatenate
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Type variables for better type hints
T = TypeVar('T')
P = ParamSpec('P')


class TTLCache:
    """
    Simple in-memory cache with time-to-live (TTL) expiration.
    
    This class provides a basic cache implementation where entries expire
    after a specified TTL (time to live) period.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize the cache.
        
        Args:
            ttl_seconds: Time to live in seconds for cache entries
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
        logger.info("Initialized TTL Cache", ttl_seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache if it exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry['expires_at']:
            # Entry expired
            del self.cache[key]
            logger.debug("Cache entry expired", key=key)
            return None
        
        logger.debug("Cache hit", key=key)
        return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache with the configured TTL.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + self.ttl
        }
        logger.debug("Cache entry set", key=key, ttl=self.ttl)
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key to delete
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug("Cache entry deleted", key=key)
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.cache.clear()
        logger.info("Cache cleared")


# Global cache instance with default TTL of 5 minutes
default_cache = TTLCache(ttl_seconds=300)


def cached(
    ttl: int = 300, 
    key_prefix: str = "", 
    cache_instance: Optional[TTLCache] = None
) -> Callable[[Callable[Concatenate[AsyncSession, P], T]], Callable[Concatenate[AsyncSession, P], T]]:
    """
    Decorator for caching database query results.
    
    This decorator specifically works with async functions that have an AsyncSession
    as their first parameter. The cache key is based on the function name and arguments.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Optional prefix for cache keys
        cache_instance: Optional custom cache instance (uses default_cache if not provided)
        
    Returns:
        Decorated function
    """
    cache = cache_instance or default_cache
    
    def decorator(func: Callable[Concatenate[AsyncSession, P], T]) -> Callable[Concatenate[AsyncSession, P], T]:
        @functools.wraps(func)
        async def wrapper(db: AsyncSession, *args: P.args, **kwargs: P.kwargs) -> T:
            # Generate a cache key based on function name and arguments
            # We exclude the db session as it changes between invocations
            args_str = ','.join(str(arg) for arg in args)
            kwargs_str = ','.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            
            # Try to get result from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Returning cached result", function=func.__name__)
                return cached_result
            
            # Execute the function and cache its result
            result = await func(db, *args, **kwargs)
            if result is not None:  # Only cache non-None results
                cache.set(cache_key, result)
                logger.debug("Cached function result", function=func.__name__, ttl=ttl)
            
            return result
        
        return wrapper
    
    return decorator 