"""
Database session management and utilities
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from abs_utils.logger import get_logger
from abs_orm.models.base import Base
from abs_orm.config import get_settings

logger = get_logger(__name__)


# Global engine and session maker
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create the async engine with full connection pooling"""
    global _engine
    if _engine is None:
        settings = get_settings()
        poolclass_name = "NullPool" if settings.db_pool_disabled else "QueuePool"
        logger.info("Creating database engine", extra={"poolclass": poolclass_name})
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            poolclass=NullPool if settings.db_pool_disabled else None,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=settings.db_pool_pre_ping,  # Check connection health before using
            pool_recycle=settings.db_pool_recycle,  # Recycle connections after 1 hour
            pool_timeout=settings.db_pool_timeout,  # Timeout for getting connection from pool
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session maker"""
    global _async_session_maker
    if _async_session_maker is None:
        logger.info("Creating async session maker")
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions in FastAPI.

    Usage:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            ...
    """
    session_maker = get_session_maker()
    try:
        async with session_maker() as session:
            logger.debug("Creating new database session")
            try:
                yield session
            finally:
                logger.debug("Closing database session")
                await session.close()
    except Exception as e:
        logger.error("Failed to create database session", extra={"error": str(e)})
        raise


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    WARNING: This should only be used in development.
    For production, use Alembic migrations.
    """
    logger.info("Initializing database tables")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database tables", extra={"error": str(e)})
        raise


async def drop_db() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data! Only use in testing.
    """
    logger.warning("Dropping all database tables - ALL DATA WILL BE LOST")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error("Failed to drop database tables", extra={"error": str(e)})
        raise


async def close_db() -> None:
    """Close the database engine and cleanup resources"""
    global _engine, _async_session_maker
    if _engine is not None:
        logger.info("Closing database engine and cleaning up resources")
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database engine closed successfully")
    else:
        logger.debug("No database engine to close")
