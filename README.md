# abs_orm

**SQLAlchemy models, Pydantic schemas, and database layer for abs_notary file notarization service**

## Overview

`abs_orm` is the data layer for the abs_notary project. It provides:

- **SQLAlchemy Models** - User, Document, ApiKey database tables
- **Pydantic Schemas** - Request/response validation for FastAPI
- **Database Management** - Async session handling, connection pooling
- **Alembic Migrations** - Version-controlled database schema changes

## Installation

```bash
# Basic installation
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Configuration

Create a `.env` file in your project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/abs_notary
DB_ECHO=false
```

### 2. Initialize Database

```python
from abs_orm import init_db

# Create all tables (development only)
await init_db()
```

For production, use Alembic migrations:

```bash
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

```bash
# Create a new migration
make migrate-create
# Enter message: "add user role column"

# Apply migrations
make migrate-upgrade

# Rollback last migration
make migrate-downgrade
```

## Development

```bash
# Install dev dependencies
make dev-install

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Clean build artifacts
make clean
```

## Usage in FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from abs_orm import get_session, User, UserCreate
from sqlalchemy import select

app = FastAPI()

@app.post("/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    db_user = User(email=user.email, hashed_password="...")
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user
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
│   └── schemas/             # Pydantic schemas
│       ├── __init__.py
│       ├── user.py
│       ├── document.py
│       └── api_key.py
├── tests/                   # Test suite
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
