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

## Quick Examples

### Create Admin User

```python
from abs_orm import User, UserRole, get_session
import bcrypt

async def create_admin():
    async with get_session() as session:
        admin = User(
            email="admin@abs-notary.com",
            hashed_password=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode(),
            role=UserRole.ADMIN
        )
        session.add(admin)
        await session.commit()
```

### Upload Document

```python
from abs_orm import Document, DocType, DocStatus

async def upload_document(user_id: int, file_path: str, file_hash: str):
    async with get_session() as session:
        doc = Document(
            owner_id=user_id,
            file_name="contract.pdf",
            file_path=file_path,
            file_hash=file_hash,
            type=DocType.HASH,
            status=DocStatus.PENDING
        )
        session.add(doc)
        await session.commit()
```

### Update Document Status

```python
async def mark_signed(doc_id: int, tx_hash: str, json_path: str, pdf_path: str):
    async with get_session() as session:
        doc = await session.get(Document, doc_id)
        doc.status = DocStatus.ON_CHAIN
        doc.transaction_hash = tx_hash
        doc.signed_json_path = json_path
        doc.signed_pdf_path = pdf_path
        await session.commit()
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

## Common Patterns

### Query User's Documents
```python
stmt = select(Document).where(Document.owner_id == user_id)
result = await session.execute(stmt)
docs = result.scalars().all()
```

### Find Pending Documents
```python
stmt = select(Document).where(Document.status == DocStatus.PENDING)
result = await session.execute(stmt)
pending = result.scalars().all()
```

### Check if User is Admin
```python
user = await session.get(User, user_id)
if user.role == UserRole.ADMIN:
    # Admin actions
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
