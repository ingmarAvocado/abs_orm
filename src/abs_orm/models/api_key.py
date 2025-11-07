"""
API Key SQLAlchemy model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from abs_orm.models.base import Base


class ApiKey(Base):
    """API Key model for programmatic access"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)  # Hashed API key
    prefix = Column(String(16), nullable=False)  # For display (e.g., "sk_live_abc123...")
    description = Column(Text, nullable=True)  # Optional description
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, prefix='{self.prefix}')>"
