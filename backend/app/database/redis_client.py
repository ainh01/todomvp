from upstash_redis.asyncio import Redis 
from app.config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    
    _instance: Optional[Redis] = None
    
    @classmethod
    def get_client(cls) -> Redis:
        
        if cls._instance is None:
            settings = get_settings()
            try:
                cls._instance = Redis(
                    url=settings.upstash_redis_rest_url,
                    token=settings.upstash_redis_rest_token
                )
                logger.info("✅ Upstash Redis Async client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Redis client: {e}")
                raise
        
        return cls._instance
    
    @classmethod
    async def close(cls): 
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            logger.info("Redis client connection closed")

def get_redis() -> Redis:
    return RedisClient.get_client()