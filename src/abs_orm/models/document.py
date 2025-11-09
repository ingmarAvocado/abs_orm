"""
Document SQLAlchemy model
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from abs_orm.models.base import Base
from abs_utils.constants import (
    DOC_STATUS_PENDING,
    DOC_STATUS_PROCESSING,
    DOC_STATUS_ON_CHAIN,
    DOC_STATUS_ERROR,
    DOC_TYPE_HASH,
    DOC_TYPE_NFT,
)


class Document(Base):
    """Document model for file notarization records"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(66), unique=True, index=True, nullable=False)  # SHA-256 hash
    file_path = Column(Text, nullable=False)  # Local storage path to original file
    status = Column(Enum(
        DOC_STATUS_PENDING,
        DOC_STATUS_PROCESSING,
        DOC_STATUS_ON_CHAIN,
        DOC_STATUS_ERROR,
        name="docstatus"
    ), default=DOC_STATUS_PENDING, nullable=False)
    type = Column(Enum(
        DOC_TYPE_HASH,
        DOC_TYPE_NFT,
        name="doctype"
    ), nullable=False)

    # On-Chain / Storage Proofs
    transaction_hash = Column(String(66), unique=True, nullable=True)  # Ethereum tx hash
    arweave_file_url = Column(Text, nullable=True)  # For NFT: file stored on Arweave
    arweave_metadata_url = Column(Text, nullable=True)  # For NFT: metadata JSON on Arweave
    nft_token_id = Column(Integer, nullable=True)  # For NFT: token ID

    # Signed Outputs (stored locally)
    signed_json_path = Column(Text, nullable=True)  # Path to signed JSON certificate
    signed_pdf_path = Column(Text, nullable=True)  # Path to signed PDF certificate

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, file_name='{self.file_name}', status={self.status})>"