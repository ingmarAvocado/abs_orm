"""
API Key-related Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key"""

    description: str | None = None


class ApiKeyResponse(BaseModel):
    """Schema for API key response (only shows prefix for security)"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prefix: str
    description: str | None = None
    created_at: datetime
    owner_id: int


class ApiKeyWithSecret(ApiKeyResponse):
    """Schema for API key response with full key (only shown once during creation)"""

    key: str
