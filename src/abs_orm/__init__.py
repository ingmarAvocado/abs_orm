"""
abs_orm - SQLAlchemy models, Pydantic schemas, and database layer for abs_notary
"""

from abs_orm.models import Base, User, Document, ApiKey, DocStatus, DocType, UserRole
from abs_orm.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    DocumentCreate,
    DocumentResponse,
    ApiKeyCreate,
    ApiKeyResponse,
)
from abs_orm.database import get_session, init_db
from abs_orm.repositories import (
    BaseRepository,
    UserRepository,
    DocumentRepository,
    ApiKeyRepository,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "Base",
    "User",
    "Document",
    "ApiKey",
    "DocStatus",
    "DocType",
    "UserRole",
    # Schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "DocumentCreate",
    "DocumentResponse",
    "ApiKeyCreate",
    "ApiKeyResponse",
    # Database
    "get_session",
    "init_db",
    # Repositories
    "BaseRepository",
    "UserRepository",
    "DocumentRepository",
    "ApiKeyRepository",
]
