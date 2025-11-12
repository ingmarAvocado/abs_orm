# abs_orm

**SQLAlchemy models, Pydantic schemas, and database layer for abs_notary file notarization service**

## Overview

`abs_orm` is the data layer for the abs_notary project. It provides:

- **SQLAlchemy Models** - User, Document, ApiKey database tables
- **Pydantic Schemas** - Request/response validation for FastAPI
- **Database Management** - Async session handling, connection pooling
- **Alembic Migrations** - Version-controlled database schema changes

## Installation

**This project uses Poetry for dependency management.**

```bash
# Install poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Or just production dependencies
poetry install --only main
```

## Quick Start

### 1. Configuration

Create a `.env` file in your project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/abs_notary
DB_ECHO=false
```

### 2. Setup Logging (with abs_utils)

```python
from abs_utils.logger import setup_logging, get_logger

# Setup logging once at application startup
setup_logging(level="INFO", log_format="json", service_name="abs_api_server")

# The ORM will automatically use structured logging
logger = get_logger(__name__)
```

### 3. Initialize Database

```python
from abs_orm import init_db

# Create all tables (development only)
await init_db()
```

For production, use Alembic migrations:

```bash
poetry run alembic upgrade head
# Or using make
make migrate-upgrade
```

### 3. Use Models

```python
from abs_orm import get_session, User, Document, DocType, DocStatus
from sqlalchemy import select

async with get_session() as session:
    # Create a user
    user = User(email="admin@example.com", hashed_password="...", role=UserRole.ADMIN)
    session.add(user)
    await session.commit()

    # Query documents
    stmt = select(Document).where(Document.status == DocStatus.PENDING)
    result = await session.execute(stmt)
    pending_docs = result.scalars().all()
```

## Database Schema

### Users Table
- `id` - Primary key
- `email` - Unique email address
- `hashed_password` - Bcrypt hashed password
- **`role`** - UserRole enum (admin, user)
- `created_at` - Timestamp

### Documents Table
- `id` - Primary key
- `file_name` - Original filename
- `file_hash` - SHA-256 hash (unique)
- **`file_path`** - Local storage path to original file
- `status` - DocStatus enum (pending, processing, on_chain, error)
- `type` - DocType enum (hash, nft)
- `transaction_hash` - Blockchain transaction hash
- `arweave_file_url` - Arweave storage URL (for NFT)
- `arweave_metadata_url` - Arweave metadata URL (for NFT)
- `nft_token_id` - Token ID (for NFT)
- **`signed_json_path`** - Path to signed JSON certificate
- **`signed_pdf_path`** - Path to signed PDF certificate
- `error_message` - Error details if failed
- `created_at`, `updated_at` - Timestamps
- `owner_id` - Foreign key to users

### ApiKeys Table
- `id` - Primary key
- `key_hash` - Hashed API key
- `prefix` - Display prefix (e.g., "sk_live_abc...")
- `description` - Optional description
- `created_at` - Timestamp
- `owner_id` - Foreign key to users

## Models

```python
from abs_orm import User, UserRole, Document, DocStatus, DocType, ApiKey

# User roles
UserRole.ADMIN  # Administrator
UserRole.USER   # Regular user

# Document statuses
DocStatus.PENDING     # Uploaded, not yet signed
DocStatus.PROCESSING  # Being notarized on blockchain
DocStatus.ON_CHAIN    # Successfully notarized
DocStatus.ERROR       # Failed notarization

# Document types
DocType.HASH  # Hash-only registry
DocType.NFT   # NFT minting
```

## Pydantic Schemas

```python
from abs_orm import (
    UserCreate, UserLogin, UserResponse,
    DocumentCreate, DocumentResponse, DocumentUpdate,
    ApiKeyCreate, ApiKeyResponse
)

# Use in FastAPI endpoints
@app.post("/auth/signup", response_model=UserResponse)
async def signup(user: UserCreate, session: AsyncSession = Depends(get_session)):
    ...
```

## Database Migrations

**All commands use Poetry:**

```bash
# Create a new migration
make migrate-create
# Or directly: poetry run alembic revision --autogenerate -m "add user role column"

# Apply migrations
make migrate-upgrade
# Or directly: poetry run alembic upgrade head

# Rollback last migration
make migrate-downgrade
# Or directly: poetry run alembic downgrade -1
```

## Development

**All development commands use Poetry:**

```bash
# Install dev dependencies
make dev-install
# Or directly: poetry install

# Run tests
make test
# Or directly: poetry run pytest -v

# Run tests in parallel
make test-parallel
# Or directly: poetry run pytest -n auto -v

# Format code
make format
# Or directly: poetry run black src tests && poetry run ruff check --fix src tests

# Lint code
make lint
# Or directly: poetry run ruff check src tests && poetry run mypy src

# Clean build artifacts
make clean
```

## Repository Layer with abs_utils Logging

The repository pattern provides a clean abstraction for database operations with integrated structured logging from abs_utils:

```python
from abs_utils.logger import setup_logging, get_logger
from abs_orm import UserRepository, DocumentRepository, ApiKeyRepository
from abs_orm import get_session

# Setup logging once at startup
setup_logging(level="INFO", log_format="json", service_name="abs_api_server")
logger = get_logger(__name__)

async with get_session() as session:
    # User repository examples with automatic logging
    user_repo = UserRepository(session)

    # Get user by email - logs: "Fetching user by email"
    user = await user_repo.get_by_email("user@example.com")
    # If not found, also logs: "User not found"

    # Get all admins - logs operation
    admins = await user_repo.get_all_admins()

    # Promote user to admin - logs: "Promoting user to admin"
    await user_repo.promote_to_admin(user_id)
    # Logs success: "User promoted to admin successfully"

    # Document repository examples with automatic logging
    doc_repo = DocumentRepository(session)

    # Get pending documents - logs: "Fetching pending documents" with count
    pending = await doc_repo.get_pending_documents()

    # Mark document as on-chain - logs full operation
    await doc_repo.mark_as_on_chain(
        doc_id,
        transaction_hash="0x123...",
        signed_json_path="/path/to/signed.json",
        signed_pdf_path="/path/to/signed.pdf"
    )
    # Logs: "Document marked as on-chain successfully"

    # Get user's documents - logs with filters
    user_docs = await doc_repo.get_user_documents(user_id)

    # API key repository examples with automatic logging
    api_repo = ApiKeyRepository(session)

    # Validate API key - logs validation result
    user = await api_repo.validate_api_key(key_hash)
    # Logs: "Validating API key" or "Invalid API key"

    # Get user's API keys - logs with count
    keys = await api_repo.get_user_api_keys(user_id)
```

### Logging Examples

All repository methods now include structured logging with contextual information:

```python
# Example log output when fetching a user by email
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "abs_orm.repositories.user",
  "message": "Fetching user by email",
  "extra": {
    "email": "user@example.com"
  }
}

# Example log output when document not found
{
  "timestamp": "2024-01-01T12:00:01Z",
  "level": "WARNING",
  "logger": "abs_orm.repositories.document",
  "message": "Document not found",
  "extra": {
    "file_hash": "0xabc123..."
  }
}

# Example log output for statistics
{
  "timestamp": "2024-01-01T12:00:02Z",
  "level": "INFO",
  "logger": "abs_orm.repositories.user",
  "message": "Generated user statistics",
  "extra": {
    "stats": {
      "total": 100,
      "admins": 5,
      "regular_users": 95
    }
  }
}
```

### BaseRepository

All repositories inherit from `BaseRepository` which provides generic CRUD operations:

- `create(**kwargs)` - Create new entity
- `get(id)` - Get by ID
- `get_all(limit, offset)` - Get all with pagination
- `get_by(field, value)` - Get by specific field
- `filter_by(**kwargs)` - Filter by multiple fields
- `update(id, **kwargs)` - Update entity
- `delete(id)` - Delete entity
- `exists(id)` - Check if exists
- `count(**kwargs)` - Count entities
- `bulk_create(entities_data)` - Create multiple entities
- `bulk_update(updates)` - Update multiple entities
- `first(**kwargs)` - Get first matching entity
- `get_paginated(page, page_size)` - Get paginated results

## Usage in FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from abs_orm import get_session, UserRepository, UserCreate, UserResponse

app = FastAPI()

@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    user_repo = UserRepository(session)

    # Check if email exists
    if await user_repo.email_exists(user_data.email):
        raise HTTPException(400, "Email already registered")

    # Create user
    user = await user_repo.create(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=UserRole.USER
    )

    await session.commit()
    return user

@app.get("/documents/pending")
async def get_pending_documents(
    session: AsyncSession = Depends(get_session)
):
    doc_repo = DocumentRepository(session)
    return await doc_repo.get_pending_documents()
```

## Project Structure

```
abs_orm/
├── src/abs_orm/
│   ├── __init__.py          # Public API
│   ├── config.py            # Pydantic settings
│   ├── database.py          # Session management
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── document.py
│   │   └── api_key.py
│   ├── repositories/        # Repository pattern layer
│   │   ├── __init__.py
│   │   ├── base.py          # Generic CRUD operations
│   │   ├── user.py          # User-specific queries
│   │   ├── document.py      # Document-specific queries
│   │   └── api_key.py       # API key-specific queries
│   └── schemas/             # Pydantic schemas
│       ├── __init__.py
│       ├── user.py
│       ├── document.py
│       └── api_key.py
├── tests/                   # Test suite
│   ├── conftest.py          # Test fixtures
│   └── repositories/        # Repository tests
│       ├── test_base_repository.py
│       ├── test_user_repository.py
│       ├── test_document_repository.py
│       └── test_api_key_repository.py
├── alembic/                 # Database migrations
├── pyproject.toml          # Package configuration
├── Makefile                # Development commands
└── README.md
```

## License

MIT

## Links

- **Repository**: https://github.com/ingmarAvocado/abs_orm
- **Issues**: https://github.com/ingmarAvocado/abs_orm/issues
- **abs_notary Project**: Part of the abs_notary ecosystem
