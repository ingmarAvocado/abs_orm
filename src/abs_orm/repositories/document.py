"""
Document repository with document-specific queries
"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from abs_utils.logger import get_logger
from abs_orm.models.document import Document, DocStatus, DocType
from abs_orm.repositories.base import BaseRepository

logger = get_logger(__name__)


class DocumentRepository(BaseRepository[Document]):
    """
    Repository for Document model with document-specific operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize DocumentRepository.

        Args:
            session: Async database session
        """
        super().__init__(Document, session)

    async def get_by_file_hash(self, file_hash: str) -> Optional[Document]:
        """
        Get document by file hash.

        Args:
            file_hash: SHA-256 file hash

        Returns:
            Document instance or None if not found
        """
        logger.info("Fetching document by file hash", extra={"file_hash": file_hash})
        doc = await self.get_by("file_hash", file_hash)
        if not doc:
            logger.warning("Document not found", extra={"file_hash": file_hash})
        return doc

    async def get_by_transaction_hash(self, tx_hash: str) -> Optional[Document]:
        """
        Get document by blockchain transaction hash.

        Args:
            tx_hash: Ethereum transaction hash

        Returns:
            Document instance or None if not found
        """
        logger.info("Fetching document by transaction hash", extra={"transaction_hash": tx_hash})
        return await self.get_by("transaction_hash", tx_hash)

    async def get_user_documents(
        self,
        user_id: int,
        status: Optional[DocStatus] = None,
        doc_type: Optional[DocType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Document]:
        """
        Get all documents for a user with optional filters.

        Args:
            user_id: Owner user ID
            status: Optional status filter
            doc_type: Optional document type filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of user's documents
        """
        stmt = select(Document).where(Document.owner_id == user_id)

        if status is not None:
            stmt = stmt.where(Document.status == status)

        if doc_type is not None:
            stmt = stmt.where(Document.type == doc_type)

        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        docs = list(result.scalars().all())
        logger.info("Fetching user documents", extra={
            "user_id": user_id,
            "status": status,
            "doc_type": doc_type,
            "count": len(docs)
        })
        return docs

    async def get_by_status(self, status: DocStatus) -> List[Document]:
        """
        Get all documents with specific status.

        Args:
            status: Document status

        Returns:
            List of documents with specified status
        """
        return await self.filter_by(status=status)

    async def get_by_type(self, doc_type: DocType) -> List[Document]:
        """
        Get all documents of specific type.

        Args:
            doc_type: Document type (HASH or NFT)

        Returns:
            List of documents with specified type
        """
        return await self.filter_by(type=doc_type)

    async def get_pending_documents(self, limit: Optional[int] = None) -> List[Document]:
        """
        Get all pending documents awaiting processing.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of pending documents
        """
        stmt = select(Document).where(Document.status == DocStatus.PENDING)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        docs = list(result.scalars().all())
        logger.info("Fetching pending documents", extra={"limit": limit, "count": len(docs)})
        return docs

    async def get_processing_documents(self) -> List[Document]:
        """
        Get all documents currently being processed.

        Returns:
            List of processing documents
        """
        docs = await self.get_by_status(DocStatus.PROCESSING)
        logger.info("Fetching processing documents", extra={"count": len(docs)})
        return docs

    async def get_error_documents(self) -> List[Document]:
        """
        Get all documents that encountered errors.

        Returns:
            List of error documents
        """
        docs = await self.get_by_status(DocStatus.ERROR)
        logger.info("Fetching error documents", extra={"count": len(docs)})
        return docs

    async def update_status(
        self,
        document_id: int,
        status: DocStatus,
        error_message: Optional[str] = None
    ) -> Optional[Document]:
        """
        Update document status.

        Args:
            document_id: Document ID
            status: New status
            error_message: Optional error message if status is ERROR

        Returns:
            Updated document or None if not found
        """
        logger.info("Updating document status", extra={
            "document_id": document_id,
            "status": status,
            "error_message": error_message
        })

        update_data = {"status": status}

        if status == DocStatus.ERROR and error_message:
            update_data["error_message"] = error_message
            logger.warning("Document status set to ERROR", extra={
                "document_id": document_id,
                "error_message": error_message
            })

        doc = await self.update(document_id, **update_data)
        if doc:
            logger.info("Document status updated successfully", extra={
                "document_id": document_id,
                "status": status
            })
        else:
            logger.warning("Failed to update document status - document not found", extra={
                "document_id": document_id
            })
        return doc

    async def mark_as_on_chain(
        self,
        document_id: int,
        transaction_hash: str,
        signed_json_path: str,
        signed_pdf_path: str,
        arweave_file_url: Optional[str] = None,
        arweave_metadata_url: Optional[str] = None,
        nft_token_id: Optional[int] = None
    ) -> Optional[Document]:
        """
        Mark document as successfully recorded on blockchain.

        Args:
            document_id: Document ID
            transaction_hash: Ethereum transaction hash
            signed_json_path: Path to signed JSON certificate
            signed_pdf_path: Path to signed PDF certificate
            arweave_file_url: Optional Arweave file URL (for NFT)
            arweave_metadata_url: Optional Arweave metadata URL (for NFT)
            nft_token_id: Optional NFT token ID

        Returns:
            Updated document or None if not found
        """
        logger.info("Marking document as on-chain", extra={
            "document_id": document_id,
            "transaction_hash": transaction_hash,
            "nft_token_id": nft_token_id
        })

        update_data = {
            "status": DocStatus.ON_CHAIN,
            "transaction_hash": transaction_hash,
            "signed_json_path": signed_json_path,
            "signed_pdf_path": signed_pdf_path,
        }

        if arweave_file_url:
            update_data["arweave_file_url"] = arweave_file_url

        if arweave_metadata_url:
            update_data["arweave_metadata_url"] = arweave_metadata_url

        if nft_token_id is not None:
            update_data["nft_token_id"] = nft_token_id

        doc = await self.update(document_id, **update_data)
        if doc:
            logger.info("Document marked as on-chain successfully", extra={
                "document_id": document_id,
                "transaction_hash": transaction_hash
            })
        return doc

    async def file_hash_exists(self, file_hash: str) -> bool:
        """
        Check if file hash already exists.

        Args:
            file_hash: SHA-256 file hash

        Returns:
            True if exists, False otherwise
        """
        exists = await self.exists_by("file_hash", file_hash)
        logger.debug("Checking if file hash exists", extra={"file_hash": file_hash, "exists": exists})
        return exists

    async def count_by_status(self, status: DocStatus) -> int:
        """
        Count documents by status.

        Args:
            status: Document status

        Returns:
            Number of documents with specified status
        """
        return await self.count(status=status)

    async def count_user_documents(
        self,
        user_id: int,
        status: Optional[DocStatus] = None
    ) -> int:
        """
        Count documents for a user.

        Args:
            user_id: Owner user ID
            status: Optional status filter

        Returns:
            Number of user's documents
        """
        filters = {"owner_id": user_id}

        if status is not None:
            filters["status"] = status

        count = await self.count(**filters)
        logger.debug("Counting user documents", extra={
            "user_id": user_id,
            "status": status,
            "count": count
        })
        return count

    async def search_by_filename(self, pattern: str) -> List[Document]:
        """
        Search documents by filename pattern.

        Args:
            pattern: Filename pattern to search for

        Returns:
            List of documents matching the pattern
        """
        stmt = select(Document).where(Document.file_name.ilike(f"%{pattern}%"))
        result = await self.session.execute(stmt)
        docs = list(result.scalars().all())
        logger.info("Searching documents by filename pattern", extra={"pattern": pattern, "results_count": len(docs)})
        return docs

    async def get_recent_documents(self, days: int = 7) -> List[Document]:
        """
        Get documents created in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recently created documents
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(Document).where(Document.created_at >= cutoff_date)
        result = await self.session.execute(stmt)
        docs = list(result.scalars().all())
        logger.info("Fetching recent documents", extra={"days": days, "count": len(docs)})
        return docs

    async def get_document_stats(self) -> Dict[str, int]:
        """
        Get document statistics.

        Returns:
            Dictionary with document statistics
        """
        total = await self.count()
        pending = await self.count_by_status(DocStatus.PENDING)
        processing = await self.count_by_status(DocStatus.PROCESSING)
        on_chain = await self.count_by_status(DocStatus.ON_CHAIN)
        error = await self.count_by_status(DocStatus.ERROR)
        hash_type = await self.count(type=DocType.HASH)
        nft_type = await self.count(type=DocType.NFT)

        stats = {
            "total": total,
            "pending": pending,
            "processing": processing,
            "on_chain": on_chain,
            "error": error,
            "hash_type": hash_type,
            "nft_type": nft_type,
        }
        logger.info("Generated document statistics", extra={"stats": stats})
        return stats