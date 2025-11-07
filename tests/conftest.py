"""
Pytest configuration and fixtures for abs_orm tests
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from abs_orm import Base
from abs_orm.models import User, UserRole, Document, DocStatus, DocType, ApiKey


# Test database URL - using file-based SQLite for tests to avoid in-memory issues
import tempfile
import os
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{temp_db.name}"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()

    # Clean up temp file
    try:
        os.unlink(temp_db.name)
    except:
        pass


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    connection = await engine.connect()
    trans = await connection.begin()

    async_session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await trans.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        role=UserRole.USER
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def test_admin(session: AsyncSession) -> User:
    """Create a test admin user"""
    admin = User(
        email="admin@example.com",
        hashed_password="hashed_admin_password",
        role=UserRole.ADMIN
    )
    session.add(admin)
    await session.flush()
    return admin


@pytest_asyncio.fixture
async def test_document(session: AsyncSession, test_user: User) -> Document:
    """Create a test document"""
    doc = Document(
        owner_id=test_user.id,
        file_name="test_document.pdf",
        file_hash="sha256_test_hash_123",
        file_path="/tmp/test_document.pdf",
        status=DocStatus.PENDING,
        type=DocType.HASH
    )
    session.add(doc)
    await session.flush()
    return doc


@pytest_asyncio.fixture
async def test_api_key(session: AsyncSession, test_user: User) -> ApiKey:
    """Create a test API key"""
    api_key = ApiKey(
        owner_id=test_user.id,
        key_hash="hashed_api_key_123",
        prefix="sk_test_",
        description="Test API Key"
    )
    session.add(api_key)
    await session.flush()
    return api_key