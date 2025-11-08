"""Factory for creating Document test data."""
import pytest_asyncio
from typing import Optional

from abs_orm.models.document import Document, DocStatus, DocType
from abs_orm.models.user import User
from .base_factory import BaseFactory
from .user_factory import UserFactory


class DocumentFactory(BaseFactory):
    """Factory for creating Document instances."""

    model = Document

    @classmethod
    def get_defaults(cls) -> dict:
        """Get default values for Document."""
        return {
            "file_name": "test_document.pdf",  # Use predictable name for test compatibility
            "file_hash": "0x" + cls.random_string(64),  # SHA-256 hash
            "file_path": "/tmp/test_document.pdf",  # Use predictable path
            "status": DocStatus.PENDING,
            "type": DocType.HASH,
        }

    @classmethod
    async def create(cls, session, owner: Optional[User] = None, **kwargs):
        """Create a document, auto-creating owner if not provided."""
        if owner is None and "owner_id" not in kwargs:
            owner = await UserFactory.create(session)
            kwargs["owner_id"] = owner.id

        if owner is not None and "owner_id" not in kwargs:
            kwargs["owner_id"] = owner.id

        return await super().create(session, **kwargs)

    @classmethod
    async def create_pending(cls, session, owner: Optional[User] = None, **kwargs):
        """Create a pending document."""
        return await cls.create(session, owner=owner, status=DocStatus.PENDING, **kwargs)

    @classmethod
    async def create_processing(cls, session, owner: Optional[User] = None, **kwargs):
        """Create a processing document."""
        return await cls.create(session, owner=owner, status=DocStatus.PROCESSING, **kwargs)

    @classmethod
    async def create_on_chain(cls, session, owner: Optional[User] = None, **kwargs):
        """Create an on-chain document with transaction hash."""
        defaults = {
            "status": DocStatus.ON_CHAIN,
            "transaction_hash": "0x" + cls.random_string(64),
            "signed_json_path": f"/storage/{cls.random_string(16)}/cert.json",
            "signed_pdf_path": f"/storage/{cls.random_string(16)}/cert.pdf",
        }
        defaults.update(kwargs)
        return await cls.create(session, owner=owner, **defaults)

    @classmethod
    async def create_nft(cls, session, owner: Optional[User] = None, **kwargs):
        """Create an NFT document with Arweave URLs."""
        defaults = {
            "type": DocType.NFT,
            "status": DocStatus.ON_CHAIN,
            "transaction_hash": "0x" + cls.random_string(64),
            "arweave_file_url": f"https://arweave.net/{cls.random_string(43)}",
            "arweave_metadata_url": f"https://arweave.net/{cls.random_string(43)}",
            "nft_token_id": cls.random_int(1, 10000),
            "signed_json_path": f"/storage/{cls.random_string(16)}/cert.json",
            "signed_pdf_path": f"/storage/{cls.random_string(16)}/cert.pdf",
        }
        defaults.update(kwargs)
        return await cls.create(session, owner=owner, **defaults)

    @classmethod
    async def create_error(cls, session, owner: Optional[User] = None, **kwargs):
        """Create a document with error status."""
        defaults = {
            "status": DocStatus.ERROR,
            "error_message": f"Error: {cls.random_string(50)}",
        }
        defaults.update(kwargs)
        return await cls.create(session, owner=owner, **defaults)


@pytest_asyncio.fixture
async def document_factory():
    """Fixture that returns the DocumentFactory class."""
    return DocumentFactory
