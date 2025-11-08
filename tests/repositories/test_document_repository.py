"""
Tests for DocumentRepository
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.document import Document, DocStatus, DocType
from abs_orm.models.user import User
from abs_orm.repositories.document import DocumentRepository


class TestDocumentRepository:
    """Test DocumentRepository specific methods"""

    @pytest.mark.asyncio
    async def test_get_by_file_hash(self, session: AsyncSession, test_document: Document):
        """Test getting document by file hash"""
        repo = DocumentRepository(session)

        doc = await repo.get_by_file_hash(test_document.file_hash)

        assert doc is not None
        assert doc.id == test_document.id
        assert doc.file_hash == test_document.file_hash

    @pytest.mark.asyncio
    async def test_get_by_file_hash_not_found(self, session: AsyncSession):
        """Test getting document by non-existent hash"""
        repo = DocumentRepository(session)

        doc = await repo.get_by_file_hash("nonexistent_hash")

        assert doc is None

    @pytest.mark.asyncio
    async def test_get_by_transaction_hash(self, session: AsyncSession, test_document: Document):
        """Test getting document by transaction hash"""
        repo = DocumentRepository(session)

        # Update document with transaction hash
        test_document.transaction_hash = "0x123abc"
        await session.flush()

        doc = await repo.get_by_transaction_hash("0x123abc")

        assert doc is not None
        assert doc.id == test_document.id
        assert doc.transaction_hash == "0x123abc"

    @pytest.mark.asyncio
    async def test_get_user_documents(self, session: AsyncSession, test_user: User, test_document: Document):
        """Test getting all documents for a user"""
        repo = DocumentRepository(session)

        # Create another document for the user
        doc2 = Document(
            owner_id=test_user.id,
            file_name="second_doc.pdf",
            file_hash="hash_456",
            file_path="/tmp/second.pdf",
            status=DocStatus.ON_CHAIN,
            type=DocType.NFT
        )
        session.add(doc2)
        await session.flush()

        docs = await repo.get_user_documents(test_user.id)

        assert len(docs) == 2
        file_names = [d.file_name for d in docs]
        assert "test_document.pdf" in file_names
        assert "second_doc.pdf" in file_names

    @pytest.mark.asyncio
    async def test_get_user_documents_with_status(self, session: AsyncSession, test_user: User, test_document: Document):
        """Test getting user documents filtered by status"""
        repo = DocumentRepository(session)

        # Create documents with different statuses
        doc2 = Document(
            owner_id=test_user.id,
            file_name="processing.pdf",
            file_hash="hash_processing",
            file_path="/tmp/processing.pdf",
            status=DocStatus.PROCESSING,
            type=DocType.HASH
        )
        session.add(doc2)
        await session.flush()

        # Get only pending documents
        pending_docs = await repo.get_user_documents(test_user.id, status=DocStatus.PENDING)
        assert len(pending_docs) == 1
        assert pending_docs[0].status == DocStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_by_status(self, session: AsyncSession, test_document: Document):
        """Test getting documents by status"""
        repo = DocumentRepository(session)

        # Create documents with different statuses
        for status in [DocStatus.PROCESSING, DocStatus.ON_CHAIN, DocStatus.ERROR]:
            doc = Document(
                owner_id=test_document.owner_id,
                file_name=f"{status.value}.pdf",
                file_hash=f"hash_{status.value}",
                file_path=f"/tmp/{status.value}.pdf",
                status=status,
                type=DocType.HASH
            )
            session.add(doc)
        await session.flush()

        # Get pending documents
        pending = await repo.get_by_status(DocStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].id == test_document.id

        # Get processing documents
        processing = await repo.get_by_status(DocStatus.PROCESSING)
        assert len(processing) == 1
        assert processing[0].status == DocStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_get_by_type(self, session: AsyncSession, test_document: Document):
        """Test getting documents by type"""
        repo = DocumentRepository(session)

        # Create NFT document
        nft_doc = Document(
            owner_id=test_document.owner_id,
            file_name="nft_doc.pdf",
            file_hash="nft_hash",
            file_path="/tmp/nft.pdf",
            status=DocStatus.PENDING,
            type=DocType.NFT
        )
        session.add(nft_doc)
        await session.flush()

        # Get HASH type documents
        hash_docs = await repo.get_by_type(DocType.HASH)
        assert len(hash_docs) == 1
        assert hash_docs[0].type == DocType.HASH

        # Get NFT type documents
        nft_docs = await repo.get_by_type(DocType.NFT)
        assert len(nft_docs) == 1
        assert nft_docs[0].type == DocType.NFT

    @pytest.mark.asyncio
    async def test_get_pending_documents(self, session: AsyncSession, test_document: Document):
        """Test getting all pending documents"""
        repo = DocumentRepository(session)

        pending = await repo.get_pending_documents()

        assert len(pending) == 1
        assert pending[0].id == test_document.id
        assert pending[0].status == DocStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_processing_documents(self, session: AsyncSession, test_document: Document):
        """Test getting all processing documents"""
        repo = DocumentRepository(session)

        # Update test document to processing
        test_document.status = DocStatus.PROCESSING
        await session.flush()

        processing = await repo.get_processing_documents()

        assert len(processing) == 1
        assert processing[0].id == test_document.id

    @pytest.mark.asyncio
    async def test_get_error_documents(self, session: AsyncSession, test_document: Document):
        """Test getting all error documents"""
        repo = DocumentRepository(session)

        # Create error document
        error_doc = Document(
            owner_id=test_document.owner_id,
            file_name="error.pdf",
            file_hash="error_hash",
            file_path="/tmp/error.pdf",
            status=DocStatus.ERROR,
            type=DocType.HASH,
            error_message="Failed to process"
        )
        session.add(error_doc)
        await session.flush()

        errors = await repo.get_error_documents()

        assert len(errors) == 1
        assert errors[0].status == DocStatus.ERROR
        assert errors[0].error_message == "Failed to process"

    @pytest.mark.asyncio
    async def test_update_status(self, session: AsyncSession, test_document: Document):
        """Test updating document status"""
        repo = DocumentRepository(session)

        updated = await repo.update_status(test_document.id, DocStatus.PROCESSING)

        assert updated is not None
        assert updated.id == test_document.id
        assert updated.status == DocStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_update_status_with_error(self, session: AsyncSession, test_document: Document):
        """Test updating document status to error with message"""
        repo = DocumentRepository(session)

        error_msg = "Blockchain transaction failed"
        updated = await repo.update_status(
            test_document.id,
            DocStatus.ERROR,
            error_message=error_msg
        )

        assert updated is not None
        assert updated.status == DocStatus.ERROR
        assert updated.error_message == error_msg

    @pytest.mark.asyncio
    async def test_mark_as_on_chain(self, session: AsyncSession, test_document: Document):
        """Test marking document as on-chain"""
        repo = DocumentRepository(session)

        tx_hash = "0xabc123def456"
        json_path = "/storage/signed/doc.json"
        pdf_path = "/storage/signed/doc.pdf"

        updated = await repo.mark_as_on_chain(
            test_document.id,
            transaction_hash=tx_hash,
            signed_json_path=json_path,
            signed_pdf_path=pdf_path
        )

        assert updated is not None
        assert updated.status == DocStatus.ON_CHAIN
        assert updated.transaction_hash == tx_hash
        assert updated.signed_json_path == json_path
        assert updated.signed_pdf_path == pdf_path

    @pytest.mark.asyncio
    async def test_mark_as_on_chain_nft(self, session: AsyncSession, test_document: Document):
        """Test marking NFT document as on-chain with additional fields"""
        repo = DocumentRepository(session)

        test_document.type = DocType.NFT
        await session.flush()

        updated = await repo.mark_as_on_chain(
            test_document.id,
            transaction_hash="0xnft123",
            signed_json_path="/storage/nft.json",
            signed_pdf_path="/storage/nft.pdf",
            arweave_file_url="https://arweave.net/file123",
            arweave_metadata_url="https://arweave.net/meta123",
            nft_token_id=42
        )

        assert updated is not None
        assert updated.status == DocStatus.ON_CHAIN
        assert updated.arweave_file_url == "https://arweave.net/file123"
        assert updated.arweave_metadata_url == "https://arweave.net/meta123"
        assert updated.nft_token_id == 42

    @pytest.mark.asyncio
    async def test_file_hash_exists(self, session: AsyncSession, test_document: Document):
        """Test checking if file hash exists"""
        repo = DocumentRepository(session)

        exists = await repo.file_hash_exists(test_document.file_hash)
        assert exists is True

        not_exists = await repo.file_hash_exists("new_hash_789")
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_count_by_status(self, session: AsyncSession, test_document: Document):
        """Test counting documents by status"""
        repo = DocumentRepository(session)

        # Create more documents
        for i in range(2):
            doc = Document(
                owner_id=test_document.owner_id,
                file_name=f"processing{i}.pdf",
                file_hash=f"proc_hash_{i}",
                file_path=f"/tmp/proc{i}.pdf",
                status=DocStatus.PROCESSING,
                type=DocType.HASH
            )
            session.add(doc)
        await session.flush()

        pending_count = await repo.count_by_status(DocStatus.PENDING)
        assert pending_count == 1

        processing_count = await repo.count_by_status(DocStatus.PROCESSING)
        assert processing_count == 2

    @pytest.mark.asyncio
    async def test_count_user_documents(self, session: AsyncSession, test_user: User, test_document: Document):
        """Test counting documents for a user"""
        repo = DocumentRepository(session)

        # Create more documents for the user
        for i in range(3):
            doc = Document(
                owner_id=test_user.id,
                file_name=f"user_doc{i}.pdf",
                file_hash=f"user_hash_{i}",
                file_path=f"/tmp/user{i}.pdf",
                status=DocStatus.ON_CHAIN,
                type=DocType.HASH
            )
            session.add(doc)
        await session.flush()

        count = await repo.count_user_documents(test_user.id)
        assert count == 4  # 1 test document + 3 new ones

    @pytest.mark.asyncio
    async def test_search_by_filename(self, session: AsyncSession, test_document: Document):
        """Test searching documents by filename pattern"""
        repo = DocumentRepository(session)

        # Create documents with different names
        doc2 = Document(
            owner_id=test_document.owner_id,
            file_name="contract_final.pdf",
            file_hash="contract_hash",
            file_path="/tmp/contract.pdf",
            status=DocStatus.PENDING,
            type=DocType.HASH
        )
        session.add(doc2)
        await session.flush()

        # Search for documents with 'document' in name
        results = await repo.search_by_filename("document")
        assert len(results) == 1
        assert results[0].file_name == "test_document.pdf"

        # Search for PDFs
        pdf_results = await repo.search_by_filename(".pdf")
        assert len(pdf_results) >= 2

    @pytest.mark.asyncio
    async def test_get_recent_documents(self, session: AsyncSession, test_document: Document):
        """Test getting recently created documents"""
        repo = DocumentRepository(session)

        recent = await repo.get_recent_documents(days=7)

        assert isinstance(recent, list)
        # Should include test_document created recently
        assert len(recent) >= 1

    @pytest.mark.asyncio
    async def test_get_documents_paginated(self, session: AsyncSession, test_document: Document):
        """Test paginated document retrieval"""
        repo = DocumentRepository(session)

        # Create multiple documents
        for i in range(5):
            doc = Document(
                owner_id=test_document.owner_id,
                file_name=f"page{i}.pdf",
                file_hash=f"page_hash_{i}",
                file_path=f"/tmp/page{i}.pdf",
                status=DocStatus.PENDING,
                type=DocType.HASH
            )
            session.add(doc)
        await session.flush()

        # Test pagination
        page1 = await repo.get_paginated(page=1, page_size=3)
        assert len(page1) <= 3

        page2 = await repo.get_paginated(page=2, page_size=3)
        assert len(page2) >= 0

    @pytest.mark.asyncio
    async def test_get_document_stats(self, session: AsyncSession, test_document: Document):
        """Test getting document statistics"""
        repo = DocumentRepository(session)

        # Create documents with different statuses and types
        statuses = [DocStatus.PROCESSING, DocStatus.ON_CHAIN, DocStatus.ERROR]
        for status in statuses:
            doc = Document(
                owner_id=test_document.owner_id,
                file_name=f"stat_{status.value}.pdf",
                file_hash=f"stat_hash_{status.value}",
                file_path=f"/tmp/stat_{status.value}.pdf",
                status=status,
                type=DocType.NFT if status == DocStatus.ON_CHAIN else DocType.HASH
            )
            session.add(doc)
        await session.flush()

        stats = await repo.get_document_stats()

        assert stats["total"] == 4  # test_document + 3 new ones
        assert stats["pending"] == 1
        assert stats["processing"] == 1
        assert stats["on_chain"] == 1
        assert stats["error"] == 1
        assert stats["hash_type"] == 3
        assert stats["nft_type"] == 1