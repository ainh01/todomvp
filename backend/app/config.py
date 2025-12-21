from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
