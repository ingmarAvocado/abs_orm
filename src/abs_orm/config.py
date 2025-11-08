"""
Configuration management using Pydantic Settings
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Database configuration settings"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database connection
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/abs_notary"

    # Database pool settings (matching fullon_orm production settings)
    db_pool_size: int = 20  # Number of persistent connections in the pool
    db_max_overflow: int = 10  # Maximum overflow connections above pool_size
    db_pool_pre_ping: bool = True  # Check connection health before using
    db_pool_recycle: int = 3600  # Recycle connections after this many seconds (1 hour)
    db_pool_timeout: int = 30  # Timeout in seconds for getting connection from pool
    db_pool_disabled: bool = False  # Set to True for testing with NullPool

    # Debug settings
    db_echo: bool = False  # Set to True to see SQL queries


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
