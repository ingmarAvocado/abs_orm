"""
Document-related Pydantic schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from abs_utils.constants import DocType, DocStatus


class DocumentCreate(BaseModel):
    """Schema for creating a new document"""

    file_name: str
    file_hash: str = Field(..., description="SHA-256 hash of the file")
    type: DocType
    metadata: dict | None = None


class DocumentUpdate(BaseModel):
    """Schema for updating document status"""

    status: DocStatus | None = None
    transaction_hash: str | None = None
    arweave_file_url: str | None = None
    arweave_metadata_url: str | None = None
    nft_token_id: int | None = None
    error_message: str | None = None


class DocumentResponse(BaseModel):
    """Schema for document response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_hash: str
    status: DocStatus
    type: DocType
    transaction_hash: str | None = None
    arweave_file_url: str | None = None
    arweave_metadata_url: str | None = None
    nft_token_id: int | None = None
    created_at: datetime
    owner_id: int