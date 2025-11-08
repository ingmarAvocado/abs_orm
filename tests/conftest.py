"""Test configuration with proper async handling."""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Dict

import asyncpg
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from abs_orm import Base

# Load environment variables
load_dotenv()

# Safety check: prevent accidental production database access
def _validate_test_environment():
    """Validate that we're in a test environment and not accidentally using production database."""
    # Check if we're running in a test context
    import sys
    is_pytest = "pytest" in sys.modules or (sys.argv and "pytest" in sys.argv[0])

    # If we're running tests, allow the environment but add warnings
    if is_pytest:
        production_db_names = {"abs_notary", "production", "prod"}
        current_db = os.getenv("DB_NAME", "").lower()

        if current_db in production_db_names:
            print(f"⚠️  WARNING: DB_NAME is set to '{current_db}' but tests will use isolated test databases.")
            print("   This is safe - each test creates its own database like 'test_module_worker'")
        return  # Allow tests to proceed

    # Non-test context: strict validation
    production_db_names = {"abs_notary", "production", "prod"}
    current_db = os.getenv("DB_NAME", "").lower()

    if current_db in production_db_names:
        raise RuntimeError(
            f"SAFETY CHECK FAILED: Cannot run against production database '{current_db}' outside of tests. "
            f"Please set DB_NAME to a development database name."
        )

    # Also check that we don't use suspicious host patterns
    host = os.getenv("DB_HOST", "localhost").lower()
    if any(prod_pattern in host for prod_pattern in ["prod", "production", "live"]):
        raise RuntimeError(
            f"SAFETY CHECK FAILED: Database host '{host}' appears to be a production host. "
            f"Use localhost or development hosts only."
        )

# Run safety check on import
_validate_test_environment()

# Cache for engines per module to reuse across tests
_engine_cache: Dict[str, AsyncEngine] = {}
_db_created: Dict[str, bool] = {}


def create_database_url(database: str) -> str:
    """Create database URL from environment variables."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "password")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


async def create_test_database(db_name: str) -> None:
    """Create a test database."""
    # Safety check: ensure database name looks like a test database
    if not db_name.startswith("test_"):
        raise RuntimeError(
            f"SAFETY CHECK FAILED: Database name '{db_name}' does not start with 'test_'. "
            f"Only test databases should be created/dropped during testing."
        )

    if db_name in _db_created:
        return

    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "password")

    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database="postgres"
    )

    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        _db_created[db_name] = True
    finally:
        await conn.close()


async def drop_test_database(db_name: str) -> None:
    """Drop a test database."""
    # Safety check: ensure database name looks like a test database
    if not db_name.startswith("test_"):
        raise RuntimeError(
            f"SAFETY CHECK FAILED: Refusing to drop database '{db_name}' that doesn't start with 'test_'. "
            f"This safety check prevents accidental deletion of production databases."
        )

    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "password")

    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database="postgres"
    )

    try:
        await conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = $1
            AND pid <> pg_backend_pid()
        """, db_name)
        await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        _db_created.pop(db_name, None)
    finally:
        await conn.close()


def get_test_db_name(request) -> str:
    """Generate database name for the test module."""
    module_name = request.module.__name__.split('.')[-1]

    # Add worker id if running in parallel
    worker_id = getattr(request.config, 'workerinput', {}).get('workerid', '')
    if worker_id:
        return f"test_{module_name}_{worker_id}"
    else:
        return f"test_{module_name}"


async def get_or_create_engine(db_name: str) -> AsyncEngine:
    """Get or create an engine for the database."""
    if db_name not in _engine_cache:
        # Create database if needed
        await create_test_database(db_name)

        # Create engine with NullPool to avoid connection pool issues
        database_url = create_database_url(database=db_name)
        engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,  # Use NullPool to avoid event loop issues
        )

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        _engine_cache[db_name] = engine

    return _engine_cache[db_name]



@pytest_asyncio.fixture
async def db_context(request):
    """Create a DatabaseContext-like wrapper for testing with proper isolation."""
    from abs_orm.repositories import (
        UserRepository, DocumentRepository, ApiKeyRepository
    )

    # Get database name for this module
    db_name = get_test_db_name(request)

    # Get or create engine
    engine = await get_or_create_engine(db_name)

    # Create session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create a session and use savepoint
    async with async_session_maker() as session:
        # Start a transaction
        trans = await session.begin()

        # Start a savepoint
        nested = await session.begin_nested()

        # Create a test database context wrapper
        class TestDatabaseContext:
            def __init__(self, session):
                self.session = session
                self._user_repo = None
                self._document_repo = None
                self._api_key_repo = None

            @property
            def users(self):
                if self._user_repo is None:
                    self._user_repo = UserRepository(self.session)
                return self._user_repo

            @property
            def documents(self):
                if self._document_repo is None:
                    self._document_repo = DocumentRepository(self.session)
                return self._document_repo

            @property
            def api_keys(self):
                if self._api_key_repo is None:
                    self._api_key_repo = ApiKeyRepository(self.session)
                return self._api_key_repo

            async def commit(self):
                await self.session.commit()

            async def rollback(self):
                await self.session.rollback()

            async def flush(self):
                await self.session.flush()

        db = TestDatabaseContext(session)

        yield db
        await session.flush()


@pytest_asyncio.fixture
async def session(db_context):
    """Expose the session from db_context for backward compatibility."""
    return db_context.session


# Backward compatible fixtures - map old names to new factory fixtures
# These ensure test_user, test_document, and test_api_key all share the same user
@pytest_asyncio.fixture
async def test_user(user):
    """Backward compatible fixture for user."""
    return user


@pytest_asyncio.fixture
async def test_admin(admin_user):
    """Backward compatible fixture for admin_user."""
    return admin_user


@pytest_asyncio.fixture
async def test_document(db_context, test_user):
    """Backward compatible fixture for document that uses test_user."""
    from factories.document_factory import DocumentFactory
    return await DocumentFactory.create(db_context.session, owner=test_user)


@pytest_asyncio.fixture
async def test_api_key(db_context, test_user):
    """Backward compatible fixture for api_key that uses test_user."""
    from factories.api_key_factory import ApiKeyFactory
    return await ApiKeyFactory.create(db_context.session, owner=test_user)


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Clean up after all tests."""
    def finalizer():
        # Use asyncio to run async cleanup
        import asyncio

        async def async_cleanup():
            """Properly dispose engines and drop databases."""
            try:
                # Cleanup all created databases and engines
                for db_name in list(_db_created.keys()):
                    try:
                        # Dispose engine if it exists
                        if db_name in _engine_cache:
                            engine = _engine_cache[db_name]
                            await engine.dispose()
                            print(f"Disposed engine for {db_name}")

                        # Drop the test database
                        await drop_test_database(db_name)
                        print(f"Dropped test database: {db_name}")

                    except Exception as e:
                        print(f"Warning: Failed to cleanup {db_name}: {e}")

                # Clear caches
                _engine_cache.clear()
                _db_created.clear()
                print("Test cleanup completed")

            except Exception as e:
                print(f"Error during test cleanup: {e}")

        # Run the async cleanup
        try:
            asyncio.run(async_cleanup())
        except Exception as e:
            print(f"Failed to run async cleanup: {e}")

    request.addfinalizer(finalizer)


# Import factory classes (not fixtures - we'll create our own)
from factories.user_factory import UserFactory, user_factory
from factories.document_factory import DocumentFactory, document_factory
from factories.api_key_factory import ApiKeyFactory, api_key_factory


# Create fixtures with predictable data for backward compatibility
@pytest_asyncio.fixture
async def user(db_context):
    """Fixture that creates a regular user with predictable email."""
    return await UserFactory.create(db_context.session, email="test@example.com")


@pytest_asyncio.fixture
async def admin_user(db_context):
    """Fixture that creates an admin user with predictable email."""
    return await UserFactory.create_admin(db_context.session)


@pytest_asyncio.fixture
async def document(db_context):
    """Fixture that creates a document."""
    return await DocumentFactory.create(db_context.session)


@pytest_asyncio.fixture
async def pending_document(db_context):
    """Fixture that creates a pending document."""
    return await DocumentFactory.create_pending(db_context.session)


@pytest_asyncio.fixture
async def on_chain_document(db_context):
    """Fixture that creates an on-chain document."""
    return await DocumentFactory.create_on_chain(db_context.session)


@pytest_asyncio.fixture
async def nft_document(db_context):
    """Fixture that creates an NFT document."""
    return await DocumentFactory.create_nft(db_context.session)


@pytest_asyncio.fixture
async def api_key(db_context):
    """Fixture that creates an API key."""
    return await ApiKeyFactory.create(db_context.session)
