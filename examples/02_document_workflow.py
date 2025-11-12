#!/usr/bin/env python3
"""
Example 2: Complete Document Workflow

This example shows a realistic document notarization workflow:
- User uploads a document
- Document is processed (pending → processing → on_chain)
- User queries their documents
- Complete lifecycle demonstration
"""

import asyncio
import os
from pathlib import Path
from abs_orm import (
    init_db,
    get_session,
    User,
    UserRole,
    Document,
    DocStatus,
    DocType,
    UserRepository,
    DocumentRepository,
)
from abs_utils.logger import setup_logging, get_logger
from abs_utils.crypto import hash_string

# Use SQLite for examples
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

logger = get_logger(__name__)


async def setup():
    """Setup database and create a user"""
    print("🔧 Setup...\n")
    await init_db()

    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.create(
            email="alice@example.com", hashed_password="hashed_pw", role=UserRole.USER
        )
        await session.commit()
        print(f"✅ Created user: {user.email} (ID: {user.id})\n")
        return user.id


async def upload_document(user_id: int):
    """Step 1: User uploads a document"""
    print("📤 STEP 1: User uploads document")
    print("-" * 50)

    # Simulate file upload
    file_content = "This is my important contract"
    file_hash = hash_string(file_content)

    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Check if already uploaded
        if await doc_repo.file_hash_exists(file_hash):
            print("❌ Document already uploaded!")
            return None

        # Create document record
        doc = await doc_repo.create(
            owner_id=user_id,
            file_name="contract.pdf",
            file_path="/storage/files/contract_001.pdf",
            file_hash=file_hash,
            type=DocType.HASH,
            status=DocStatus.PENDING,
        )

        await session.commit()

        print(f"✅ Document uploaded!")
        print(f"   ID: {doc.id}")
        print(f"   File: {doc.file_name}")
        print(f"   Hash: {doc.file_hash[:20]}...")
        print(f"   Status: {doc.status.value}")
        print()

        return doc.id


async def start_processing(doc_id: int):
    """Step 2: Worker picks up document and starts processing"""
    print("⚙️  STEP 2: Worker starts processing")
    print("-" * 50)

    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Update status to processing
        doc = await doc_repo.update_status(doc_id, DocStatus.PROCESSING)
        await session.commit()

        print(f"✅ Document status updated")
        print(f"   ID: {doc.id}")
        print(f"   Status: {doc.status.value}")
        print()


async def complete_notarization(doc_id: int):
    """Step 3: Notarization complete, update with blockchain info"""
    print("✅ STEP 3: Notarization complete")
    print("-" * 50)

    # Simulate blockchain transaction
    tx_hash = "0x" + "a" * 64
    json_path = "/storage/certificates/cert_001.json"
    pdf_path = "/storage/certificates/cert_001.pdf"

    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Mark as on-chain with all details
        doc = await doc_repo.mark_as_on_chain(
            doc_id, transaction_hash=tx_hash, signed_json_path=json_path, signed_pdf_path=pdf_path
        )

        await session.commit()

        print(f"✅ Document notarized on blockchain!")
        print(f"   ID: {doc.id}")
        print(f"   Status: {doc.status.value}")
        print(f"   TX Hash: {doc.transaction_hash[:20]}...")
        print(f"   JSON Cert: {doc.signed_json_path}")
        print(f"   PDF Cert: {doc.signed_pdf_path}")
        print()


async def query_user_documents(user_id: int):
    """Step 4: User queries their documents"""
    print("📋 STEP 4: User views their documents")
    print("-" * 50)

    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Get all user documents
        all_docs = await doc_repo.get_user_documents(user_id)
        print(f"Total documents: {len(all_docs)}")

        for doc in all_docs:
            print(f"\n  📄 {doc.file_name}")
            print(f"     ID: {doc.id}")
            print(f"     Status: {doc.status.value}")
            print(f"     Type: {doc.type.value}")
            if doc.transaction_hash:
                print(f"     TX Hash: {doc.transaction_hash[:20]}...")

        # Get only on-chain documents
        on_chain = await doc_repo.get_user_documents(user_id, status=DocStatus.ON_CHAIN)
        print(f"\n  ✅ On-chain documents: {len(on_chain)}")

    print()


async def worker_view():
    """Worker's view: Get pending documents"""
    print("🔧 WORKER VIEW: Pending documents")
    print("-" * 50)

    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        # Get all pending documents (across all users)
        pending = await doc_repo.get_pending_documents()
        print(f"Pending documents to process: {len(pending)}")

        for doc in pending:
            print(f"  📄 {doc.file_name} (User: {doc.owner_id})")

    print()


async def statistics():
    """View document statistics"""
    print("📊 STATISTICS")
    print("-" * 50)

    async with get_session() as session:
        doc_repo = DocumentRepository(session)

        stats = await doc_repo.get_document_stats()
        print(f"Total documents: {stats['total']}")
        print(f"By status:")
        print(f"  - pending: {stats['pending']}")
        print(f"  - processing: {stats['processing']}")
        print(f"  - on_chain: {stats['on_chain']}")
        print(f"  - error: {stats['error']}")
        print(f"By type:")
        print(f"  - hash: {stats['hash_type']}")
        print(f"  - nft: {stats['nft_type']}")

    print()


async def main():
    print("=" * 80)
    print("EXAMPLE 2: COMPLETE DOCUMENT WORKFLOW")
    print("=" * 80)
    print()

    # Setup logging
    setup_logging(level="WARNING", log_format="text")

    # Setup database and create user
    user_id = await setup()

    # Workflow
    doc_id = await upload_document(user_id)

    if doc_id:
        await start_processing(doc_id)
        await complete_notarization(doc_id)

    # Queries
    await query_user_documents(user_id)
    await worker_view()
    await statistics()

    print("=" * 80)
    print("✅ Example complete!")
    print("\nReal-World Workflow:")
    print("1. User uploads file → Document created with PENDING status")
    print("2. Worker picks it up → Status changes to PROCESSING")
    print("3. Blockchain tx sent → Status changes to ON_CHAIN")
    print("4. User can download certificates (JSON/PDF)")
    print("\nRepository Methods Used:")
    print("- file_hash_exists() - Prevent duplicates")
    print("- create() - Create new document")
    print("- update_status() - Update processing status")
    print("- mark_as_on_chain() - Record blockchain proof")
    print("- get_user_documents() - Query user's documents")
    print("- get_pending_documents() - Worker queue")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
