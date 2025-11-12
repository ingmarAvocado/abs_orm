# abs_orm Examples

Comprehensive examples demonstrating abs_orm usage with real-world patterns.

## 📋 Examples List

### 1. Basic Usage (`01_basic_usage.py`)
**What it shows:**
- Database initialization with `init_db()`
- Creating users with repository pattern
- Querying users by email
- User role management (promote to admin, check roles)
- User statistics

**Run it:**
```bash
poetry run python examples/01_basic_usage.py
```

**Key concepts:**
- Use `get_session()` context manager
- Repositories provide clean database operations
- Always `await session.commit()` to save changes
- Repository methods are async (use `await`)

---

### 2. Complete Document Workflow (`02_document_workflow.py`)
**What it shows:**
- Realistic document notarization lifecycle
- User uploads document (PENDING status)
- Worker processes it (PROCESSING status)
- Blockchain notarization complete (ON_CHAIN status)
- User queries their documents
- Worker queries pending queue
- Document statistics

**Run it:**
```bash
poetry run python examples/02_document_workflow.py
```

**Key concepts:**
- Document status flow: PENDING → PROCESSING → ON_CHAIN
- `file_hash_exists()` prevents duplicate uploads
- `mark_as_on_chain()` records blockchain proof
- `get_user_documents()` with optional status filter
- `get_pending_documents()` for worker queue

---

## 🚀 Running Examples

All examples use SQLite in-memory database, so they're completely self-contained.

**Run all examples:**
```bash
cd /home/ingmar/code/abs_documents/abs_orm
poetry run python examples/01_basic_usage.py
poetry run python examples/02_document_workflow.py
```

---

## 📚 Repository Pattern

abs_orm uses the repository pattern to provide clean database abstractions:

### UserRepository

```python
from abs_orm import get_session, UserRepository

async with get_session() as session:
    repo = UserRepository(session)

    # Create
    user = await repo.create(
        email="user@example.com",
        hashed_password="...",
        role=UserRole.USER
    )

    # Query
    user = await repo.get_by_email("user@example.com")
    exists = await repo.email_exists("user@example.com")
    admins = await repo.get_all_admins()

    # Update
    await repo.promote_to_admin(user.id)
    await repo.update_password(user.id, new_hash)

    # Stats
    stats = await repo.get_user_stats()

    # Save changes
    await session.commit()
```

### DocumentRepository

```python
from abs_orm import get_session, DocumentRepository, DocStatus, DocType

async with get_session() as session:
    repo = DocumentRepository(session)

    # Create
    doc = await repo.create(
        owner_id=user_id,
        file_name="contract.pdf",
        file_path="/storage/files/file.pdf",
        file_hash="0x...",
        type=DocType.HASH,
        status=DocStatus.PENDING
    )

    # Query
    doc = await repo.get_by_file_hash("0x...")
    docs = await repo.get_user_documents(user_id, status=DocStatus.ON_CHAIN)
    pending = await repo.get_pending_documents()

    # Update
    await repo.update_status(doc.id, DocStatus.PROCESSING)
    await repo.mark_as_on_chain(
        doc.id,
        transaction_hash="0x...",
        signed_json_path="/path/to/cert.json",
        signed_pdf_path="/path/to/cert.pdf"
    )

    # Save
    await session.commit()
```

### ApiKeyRepository

```python
from abs_orm import get_session, ApiKeyRepository

async with get_session() as session:
    repo = ApiKeyRepository(session)

    # Create
    key = await repo.create(
        owner_id=user_id,
        key_hash="0x...",
        prefix="sk_live_abc1",
        description="Production key"
    )

    # Validate
    user = await repo.validate_api_key(key_hash)

    # Query
    keys = await repo.get_user_api_keys(user_id)

    # Revoke
    await repo.revoke_api_key(key.id)

    # Save
    await session.commit()
```

---

## 🔄 Common Workflows

### User Registration

```python
from abs_orm import get_session, UserRepository, UserRole
import bcrypt

async def register_user(email: str, password: str):
    # Hash password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    async with get_session() as session:
        repo = UserRepository(session)

        # Check if email exists
        if await repo.email_exists(email):
            raise ValueError("Email already registered")

        # Create user
        user = await repo.create(
            email=email,
            hashed_password=password_hash,
            role=UserRole.USER
        )

        await session.commit()
        return user
```

### Document Upload

```python
from abs_orm import get_session, DocumentRepository, DocStatus, DocType
from abs_utils.crypto import hash_file_async

async def upload_document(user_id: int, file_path: str):
    # Hash file
    file_hash = await hash_file_async(file_path)

    async with get_session() as session:
        repo = DocumentRepository(session)

        # Check for duplicate
        if await repo.file_hash_exists(file_hash):
            raise ValueError("Document already uploaded")

        # Create document
        doc = await repo.create(
            owner_id=user_id,
            file_name=Path(file_path).name,
            file_path=file_path,
            file_hash=file_hash,
            type=DocType.HASH,
            status=DocStatus.PENDING
        )

        await session.commit()
        return doc
```

### Worker Processing

```python
from abs_orm import get_session, DocumentRepository, DocStatus

async def process_pending_documents():
    async with get_session() as session:
        repo = DocumentRepository(session)

        # Get pending documents
        pending = await repo.get_pending_documents()

        for doc in pending:
            # Mark as processing
            await repo.update_status(doc.id, DocStatus.PROCESSING)
            await session.commit()

            # Process document (blockchain tx, etc.)
            try:
                tx_hash = await submit_to_blockchain(doc)

                # Mark as on-chain
                await repo.mark_as_on_chain(
                    doc.id,
                    transaction_hash=tx_hash,
                    signed_json_path=f"/certs/{doc.id}.json",
                    signed_pdf_path=f"/certs/{doc.id}.pdf"
                )
                await session.commit()

            except Exception as e:
                # Mark as error
                await repo.update_status(doc.id, DocStatus.ERROR)
                doc.error_message = str(e)
                await session.commit()
```

---

## 🎯 Best Practices

1. **Always use context managers:**
   ```python
   async with get_session() as session:
       # Your code here
       await session.commit()
   ```

2. **Commit transactions:**
   ```python
   # Changes are not saved until you commit
   await session.commit()
   ```

3. **Check before creating:**
   ```python
   if not await repo.email_exists(email):
       user = await repo.create(...)
   ```

4. **Use repository methods:**
   ```python
   # Good: Use repository method
   user = await repo.get_by_email(email)

   # Avoid: Raw SQLAlchemy queries
   # user = await session.execute(select(User)...)
   ```

5. **Handle errors:**
   ```python
   try:
       doc = await repo.get(doc_id)
       if not doc:
           raise ValueError("Document not found")
   except Exception as e:
       logger.error(f"Failed to get document: {e}")
   ```

---

## 💡 Tips

- Examples use in-memory SQLite (no setup required)
- For production, use PostgreSQL and configure `DATABASE_URL`
- All repository methods are logged (uses abs_utils logger)
- Status transitions: PENDING → PROCESSING → ON_CHAIN or ERROR
- Document types: HASH (simple) or NFT (with Arweave storage)

---

## 🔗 Integration

These examples show how abs_orm integrates with:
- **abs_utils** - Logging, exceptions, crypto
- **abs_api_server** - FastAPI endpoints
- **abs_worker** - Background processing

---

## ❓ Questions?

Check the main README and CLAUDE.md for detailed documentation!
