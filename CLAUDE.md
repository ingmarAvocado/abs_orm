# CLAUDE.md - Quick Start Guide for LLMs

## What This Is

`abs_orm` is the database layer for the abs_notary file notarization service. It contains SQLAlchemy models, Pydantic schemas, and database session management.

## Key Concepts

**Simple Database Schema:**
1. **Users** - admin or regular users, can create API keys
2. **Documents** - files to be notarized (hash or NFT), stored locally with signed certificates
3. **ApiKeys** - for programmatic access

**Default Admin:**
- System creates a default admin user on first run
- Admins can manage all users and documents

**File Storage:**
- Original files stored locally at `file_path`
- Signed JSON certificate at `signed_json_path`
- Signed PDF certificate at `signed_pdf_path`

## Quick Examples with Repository Pattern

The repository pattern provides a cleaner abstraction for database operations:

### Create Admin User

```python
from abs_orm import UserRepository, UserRole, get_session
import bcrypt

async def create_admin():
    async with get_session() as session:
        user_repo = UserRepository(session)

        # Check if email exists
        if await user_repo.email_exists("admin@abs-notary.com"):
            return None

        # Create admin user
        admin = await user_repo.create(
            email="admin@abs-notary.com",
            hashed_password=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode(),
            role=UserRole.ADMIN
        )
        await session.commit()
        return admin
```

### Upload Document

```python
from abs_orm import DocumentRepository, DocType, DocStatus, get_session

async def upload_document(user_id: int, file_path: str, file_hash: str):
    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Check if hash already exists
        if await doc_repo.file_hash_exists(file_hash):
            raise ValueError("File already uploaded")

        # Create document
        doc = await doc_repo.create(
            owner_id=user_id,
            file_name="contract.pdf",
            file_path=file_path,
            file_hash=file_hash,
            type=DocType.HASH,
            status=DocStatus.PENDING
        )
        await session.commit()
        return doc
```

### Update Document Status

```python
from abs_orm import DocumentRepository, get_session

async def mark_signed(doc_id: int, tx_hash: str, json_path: str, pdf_path: str):
    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Mark document as on-chain with all certificates
        doc = await doc_repo.mark_as_on_chain(
            doc_id,
            transaction_hash=tx_hash,
            signed_json_path=json_path,
            signed_pdf_path=pdf_path
        )
        await session.commit()
        return doc
```

## Models Reference

### User
- `email`, `hashed_password`, `role` (admin/user)
- Relationships: `documents`, `api_keys`

### Document
- `file_name`, `file_hash`, `file_path`
- `status` (pending → processing → on_chain/error)
- `type` (hash or nft)
- `transaction_hash`, `arweave_file_url`, `nft_token_id`
- `signed_json_path`, `signed_pdf_path`

### ApiKey
- `key_hash`, `prefix`, `description`
- Relationship: `owner` (User)

## Database Migrations

```bash
# Create migration after model changes
make migrate-create

# Apply migrations
make migrate-upgrade
```

## Repository Pattern

The repository layer provides clean abstractions for database operations:

### UserRepository
```python
from abs_orm import UserRepository, get_session

async with get_session() as session:
    repo = UserRepository(session)

    # User-specific methods
    user = await repo.get_by_email("user@example.com")
    exists = await repo.email_exists("test@example.com")
    admins = await repo.get_all_admins()
    users = await repo.get_all_regular_users()
    is_admin = await repo.is_admin(user_id)
    await repo.promote_to_admin(user_id)
    await repo.demote_to_user(user_id)
    await repo.update_password(user_id, new_hash)
    results = await repo.search_by_email("pattern")
    stats = await repo.get_user_stats()
```

### DocumentRepository
```python
from abs_orm import DocumentRepository, DocStatus, get_session

async with get_session() as session:
    repo = DocumentRepository(session)

    # Document-specific methods
    doc = await repo.get_by_file_hash(file_hash)
    doc = await repo.get_by_transaction_hash(tx_hash)
    docs = await repo.get_user_documents(user_id, status=DocStatus.PENDING)
    pending = await repo.get_pending_documents()
    processing = await repo.get_processing_documents()
    errors = await repo.get_error_documents()
    exists = await repo.file_hash_exists(file_hash)

    # Update operations
    await repo.update_status(doc_id, DocStatus.PROCESSING)
    await repo.mark_as_on_chain(
        doc_id,
        transaction_hash="0x...",
        signed_json_path="/path/to/json",
        signed_pdf_path="/path/to/pdf",
        # For NFTs:
        arweave_file_url="https://...",
        arweave_metadata_url="https://...",
        nft_token_id=42
    )

    # Statistics
    stats = await repo.get_document_stats()
```

### ApiKeyRepository
```python
from abs_orm import ApiKeyRepository, get_session

async with get_session() as session:
    repo = ApiKeyRepository(session)

    # API key operations
    key = await repo.get_by_key_hash(key_hash)
    keys = await repo.get_user_api_keys(user_id)
    user = await repo.validate_api_key(key_hash)
    exists = await repo.key_hash_exists(key_hash)

    # Management
    await repo.revoke_api_key(key_id)
    await repo.revoke_user_api_keys(user_id)
    await repo.update_description(key_id, "New description")

    # Create with validation
    key = await repo.create_api_key(
        owner_id=user_id,
        key_hash=hash_value,
        prefix="sk_test_",
        description="Test key"
    )
```

### BaseRepository (inherited by all)
All repositories inherit these methods:
- `create(**kwargs)` - Create entity
- `get(id)` - Get by ID
- `get_all(limit, offset)` - Get all with pagination
- `get_by(field, value)` - Get by field
- `filter_by(**kwargs)` - Filter by multiple fields
- `update(id, **kwargs)` - Update entity
- `delete(id)` - Delete entity
- `exists(id)` - Check existence
- `count(**kwargs)` - Count entities
- `bulk_create(data)` - Create multiple
- `bulk_update(updates)` - Update multiple
- `first(**kwargs)` - Get first match
- `get_paginated(page, page_size)` - Paginated results

## Common Patterns

### Query User's Documents (with repository)
```python
doc_repo = DocumentRepository(session)
docs = await doc_repo.get_user_documents(user_id)
```

### Find Pending Documents (with repository)
```python
doc_repo = DocumentRepository(session)
pending = await doc_repo.get_pending_documents()
```

### Check if User is Admin (with repository)
```python
user_repo = UserRepository(session)
is_admin = await user_repo.is_admin(user_id)
```

## Development Workflow

1. **Make model changes** in `src/abs_orm/models/`
2. **Create migration**: `make migrate-create`
3. **Apply migration**: `make migrate-upgrade`
4. **Update schemas** in `src/abs_orm/schemas/` if needed
5. **Test** with `make test`

## Important Notes

- Always use `get_session()` for async database access
- User passwords must be hashed before storing
- API keys must be hashed, only show prefix to users
- File paths should be absolute or relative to a configured storage directory
- Document status flow: PENDING → PROCESSING → ON_CHAIN (or ERROR)

## Next Steps

This library is used by:
- `abs_api_server` - FastAPI endpoints
- `abs_worker` - Background blockchain processing

Check those repos for integration examples.
