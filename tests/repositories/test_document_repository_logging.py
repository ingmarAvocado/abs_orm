"""
Tests for logging integration in DocumentRepository
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.document import Document, DocStatus, DocType
from abs_orm.repositories.document import DocumentRepository


class TestDocumentRepositoryLogging:
    """Test DocumentRepository logging integration"""

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_by_file_hash_logs_info(self, mock_logger, session: AsyncSession, test_document: Document):
        """Test get_by_file_hash logs info when document found"""
        repo = DocumentRepository(session)

        doc = await repo.get_by_file_hash(test_document.file_hash)

        assert doc is not None
        mock_logger.info.assert_called_with(
            "Fetching document by file hash",
            extra={"file_hash": test_document.file_hash}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_by_file_hash_logs_warning(self, mock_logger, session: AsyncSession):
        """Test get_by_file_hash logs warning when document not found"""
        repo = DocumentRepository(session)

        doc = await repo.get_by_file_hash("0xnonexistent")

        assert doc is None
        mock_logger.info.assert_called_with(
            "Fetching document by file hash",
            extra={"file_hash": "0xnonexistent"}
        )
        mock_logger.warning.assert_called_with(
            "Document not found",
            extra={"file_hash": "0xnonexistent"}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_by_transaction_hash_logs(self, mock_logger, session: AsyncSession):
        """Test get_by_transaction_hash logs the operation"""
        repo = DocumentRepository(session)

        doc = await repo.get_by_transaction_hash("0xtxhash")

        mock_logger.info.assert_called_with(
            "Fetching document by transaction hash",
            extra={"transaction_hash": "0xtxhash"}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_user_documents_logs(self, mock_logger, session: AsyncSession, test_user):
        """Test get_user_documents logs the operation"""
        repo = DocumentRepository(session)

        docs = await repo.get_user_documents(
            test_user.id,
            status=DocStatus.PENDING,
            doc_type=DocType.HASH
        )

        mock_logger.info.assert_called_with(
            "Fetching user documents",
            extra={
                "user_id": test_user.id,
                "status": DocStatus.PENDING,
                "doc_type": DocType.HASH,
                "count": len(docs)
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_pending_documents_logs(self, mock_logger, session: AsyncSession):
        """Test get_pending_documents logs the operation"""
        repo = DocumentRepository(session)

        docs = await repo.get_pending_documents(limit=10)

        mock_logger.info.assert_called_with(
            "Fetching pending documents",
            extra={"limit": 10, "count": len(docs)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_update_status_logs_success(self, mock_logger, session: AsyncSession, test_document: Document):
        """Test update_status logs successful update"""
        repo = DocumentRepository(session)

        doc = await repo.update_status(
            test_document.id,
            DocStatus.PROCESSING
        )

        assert doc is not None
        mock_logger.info.assert_any_call(
            "Updating document status",
            extra={
                "document_id": test_document.id,
                "status": DocStatus.PROCESSING,
                "error_message": None
            }
        )
        mock_logger.info.assert_any_call(
            "Document status updated successfully",
            extra={
                "document_id": test_document.id,
                "status": DocStatus.PROCESSING
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_update_status_logs_error_status(self, mock_logger, session: AsyncSession, test_document: Document):
        """Test update_status logs when setting error status"""
        repo = DocumentRepository(session)

        error_msg = "Transaction failed"
        doc = await repo.update_status(
            test_document.id,
            DocStatus.ERROR,
            error_message=error_msg
        )

        assert doc is not None
        mock_logger.warning.assert_called_with(
            "Document status set to ERROR",
            extra={
                "document_id": test_document.id,
                "error_message": error_msg
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_update_status_logs_failure(self, mock_logger, session: AsyncSession):
        """Test update_status logs failure for non-existent document"""
        repo = DocumentRepository(session)

        doc = await repo.update_status(99999, DocStatus.PROCESSING)

        assert doc is None
        mock_logger.warning.assert_called_with(
            "Failed to update document status - document not found",
            extra={"document_id": 99999}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_mark_as_on_chain_logs_success(self, mock_logger, session: AsyncSession, test_document: Document):
        """Test mark_as_on_chain logs successful update"""
        repo = DocumentRepository(session)

        doc = await repo.mark_as_on_chain(
            test_document.id,
            transaction_hash="0xabc123",
            signed_json_path="/path/to/json",
            signed_pdf_path="/path/to/pdf",
            nft_token_id=42
        )

        assert doc is not None
        mock_logger.info.assert_any_call(
            "Marking document as on-chain",
            extra={
                "document_id": test_document.id,
                "transaction_hash": "0xabc123",
                "nft_token_id": 42
            }
        )
        mock_logger.info.assert_any_call(
            "Document marked as on-chain successfully",
            extra={
                "document_id": test_document.id,
                "transaction_hash": "0xabc123"
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_file_hash_exists_logs(self, mock_logger, session: AsyncSession, test_document: Document):
        """Test file_hash_exists logs the check"""
        repo = DocumentRepository(session)

        exists = await repo.file_hash_exists(test_document.file_hash)

        assert exists is True
        mock_logger.debug.assert_called_with(
            "Checking if file hash exists",
            extra={"file_hash": test_document.file_hash, "exists": True}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_search_by_filename_logs(self, mock_logger, session: AsyncSession):
        """Test search_by_filename logs the operation"""
        repo = DocumentRepository(session)

        results = await repo.search_by_filename("contract")

        mock_logger.info.assert_called_with(
            "Searching documents by filename pattern",
            extra={"pattern": "contract", "results_count": len(results)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_recent_documents_logs(self, mock_logger, session: AsyncSession):
        """Test get_recent_documents logs the operation"""
        repo = DocumentRepository(session)

        docs = await repo.get_recent_documents(days=3)

        mock_logger.info.assert_called_with(
            "Fetching recent documents",
            extra={"days": 3, "count": len(docs)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_document_stats_logs(self, mock_logger, session: AsyncSession):
        """Test get_document_stats logs statistics"""
        repo = DocumentRepository(session)

        stats = await repo.get_document_stats()

        mock_logger.info.assert_called_with(
            "Generated document statistics",
            extra={"stats": stats}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_count_user_documents_logs(self, mock_logger, session: AsyncSession, test_user):
        """Test count_user_documents logs the operation"""
        repo = DocumentRepository(session)

        count = await repo.count_user_documents(test_user.id, status=DocStatus.PENDING)

        mock_logger.debug.assert_called_with(
            "Counting user documents",
            extra={
                "user_id": test_user.id,
                "status": DocStatus.PENDING,
                "count": count
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_processing_documents_logs(self, mock_logger, session: AsyncSession):
        """Test get_processing_documents logs the operation"""
        repo = DocumentRepository(session)

        docs = await repo.get_processing_documents()

        mock_logger.info.assert_called_with(
            "Fetching processing documents",
            extra={"count": len(docs)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.document.logger')
    async def test_get_error_documents_logs(self, mock_logger, session: AsyncSession):
        """Test get_error_documents logs the operation"""
        repo = DocumentRepository(session)

        docs = await repo.get_error_documents()

        mock_logger.info.assert_called_with(
            "Fetching error documents",
            extra={"count": len(docs)}
        )