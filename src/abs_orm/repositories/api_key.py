"""
API Key repository with API key-specific queries
"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from abs_utils.logger import get_logger
from abs_orm.models.api_key import ApiKey
from abs_orm.models.user import User
from abs_orm.repositories.base import BaseRepository

logger = get_logger(__name__)


class ApiKeyRepository(BaseRepository[ApiKey]):
    """
    Repository for ApiKey model with API key-specific operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize ApiKeyRepository.

        Args:
            session: Async database session
        """
        super().__init__(ApiKey, session)

    async def get_by_key_hash(self, key_hash: str) -> Optional[ApiKey]:
        """
        Get API key by key hash.

        Args:
            key_hash: Hashed API key

        Returns:
            ApiKey instance or None if not found
        """
        logger.info("Fetching API key by hash", extra={"key_hash": key_hash})
        key = await self.get_by("key_hash", key_hash)
        if not key:
            logger.warning("API key not found", extra={"key_hash": key_hash})
        return key

    async def get_by_prefix(self, prefix: str) -> Optional[ApiKey]:
        """
        Get API key by prefix.

        Args:
            prefix: API key prefix (e.g., "sk_test_")

        Returns:
            ApiKey instance or None if not found
        """
        return await self.get_by("prefix", prefix)

    async def get_user_api_keys(self, user_id: int) -> List[ApiKey]:
        """
        Get all API keys for a user.

        Args:
            user_id: Owner user ID

        Returns:
            List of user's API keys
        """
        keys = await self.filter_by(owner_id=user_id)
        logger.info("Fetching user API keys", extra={"user_id": user_id, "count": len(keys)})
        return keys

    async def key_hash_exists(self, key_hash: str) -> bool:
        """
        Check if key hash already exists.

        Args:
            key_hash: Hashed API key

        Returns:
            True if exists, False otherwise
        """
        exists = await self.exists_by("key_hash", key_hash)
        logger.debug("Checking if API key hash exists", extra={"key_hash": key_hash, "exists": exists})
        return exists

    async def validate_api_key(self, key_hash: str) -> Optional[User]:
        """
        Validate API key and get the owner.

        Args:
            key_hash: Hashed API key

        Returns:
            User who owns the API key or None if invalid
        """
        stmt = select(User).join(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            logger.info("Validating API key", extra={"key_hash": key_hash, "valid": True})
        else:
            logger.warning("Invalid API key", extra={"key_hash": key_hash})
        return user

    async def count_user_api_keys(self, user_id: int) -> int:
        """
        Count API keys for a user.

        Args:
            user_id: Owner user ID

        Returns:
            Number of user's API keys
        """
        return await self.count(owner_id=user_id)

    async def search_by_description(self, pattern: str) -> List[ApiKey]:
        """
        Search API keys by description pattern.

        Args:
            pattern: Description pattern to search for

        Returns:
            List of API keys matching the pattern
        """
        stmt = select(ApiKey).where(ApiKey.description.ilike(f"%{pattern}%"))
        result = await self.session.execute(stmt)
        keys = list(result.scalars().all())
        logger.info("Searching API keys by description", extra={"pattern": pattern, "results_count": len(keys)})
        return keys

    async def get_recent_api_keys(self, days: int = 7) -> List[ApiKey]:
        """
        Get API keys created in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recently created API keys
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(ApiKey).where(ApiKey.created_at >= cutoff_date)
        result = await self.session.execute(stmt)
        keys = list(result.scalars().all())
        logger.info("Fetching recent API keys", extra={"days": days, "count": len(keys)})
        return keys

    async def revoke_api_key(self, key_id: int) -> bool:
        """
        Revoke (delete) an API key.

        Args:
            key_id: API key ID

        Returns:
            True if revoked, False if not found
        """
        logger.info("Revoking API key", extra={"key_id": key_id})
        success = await self.delete(key_id)
        if success:
            logger.info("API key revoked successfully", extra={"key_id": key_id})
        else:
            logger.warning("Failed to revoke API key - key not found", extra={"key_id": key_id})
        return success

    async def revoke_user_api_keys(self, user_id: int) -> int:
        """
        Revoke all API keys for a user.

        Args:
            user_id: Owner user ID

        Returns:
            Number of revoked API keys
        """
        logger.info("Revoking all user API keys", extra={"user_id": user_id})
        stmt = delete(ApiKey).where(ApiKey.owner_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        count = result.rowcount
        logger.info("Revoked user API keys", extra={"user_id": user_id, "count": count})
        return count

    async def update_description(
        self,
        key_id: int,
        description: str
    ) -> Optional[ApiKey]:
        """
        Update API key description.

        Args:
            key_id: API key ID
            description: New description

        Returns:
            Updated API key or None if not found
        """
        logger.info("Updating API key description", extra={
            "key_id": key_id,
            "description": description
        })
        updated = await self.update(key_id, description=description)
        if updated:
            logger.info("API key description updated successfully", extra={"key_id": key_id})
        else:
            logger.warning("Failed to update API key description - key not found", extra={"key_id": key_id})
        return updated

    async def get_with_owner(self, key_id: int) -> Optional[ApiKey]:
        """
        Get API key with owner relationship loaded.

        Args:
            key_id: API key ID

        Returns:
            ApiKey with owner relationship loaded
        """
        logger.info("Fetching API key with owner", extra={"key_id": key_id})
        stmt = select(ApiKey).options(
            selectinload(ApiKey.owner)
        ).where(ApiKey.id == key_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_api_key(
        self,
        owner_id: int,
        key_hash: str,
        prefix: str,
        description: Optional[str] = None
    ) -> ApiKey:
        """
        Create a new API key with validation.

        Args:
            owner_id: Owner user ID
            key_hash: Hashed API key
            prefix: API key prefix
            description: Optional description

        Returns:
            Created API key
        """
        logger.info("Creating new API key", extra={
            "owner_id": owner_id,
            "prefix": prefix,
            "description": description
        })

        # Check if hash already exists
        if await self.key_hash_exists(key_hash):
            logger.error("Failed to create API key - hash already exists", extra={
                "owner_id": owner_id,
                "key_hash": key_hash
            })
            raise ValueError("API key hash already exists")

        api_key = await self.create(
            owner_id=owner_id,
            key_hash=key_hash,
            prefix=prefix,
            description=description
        )

        logger.info("API key created successfully", extra={
            "key_id": api_key.id,
            "owner_id": owner_id,
            "prefix": prefix
        })
        return api_key

    async def get_api_key_stats(self) -> Dict[str, int]:
        """
        Get API key statistics.

        Returns:
            Dictionary with API key statistics
        """
        total = await self.count()

        # Count unique users with API keys
        stmt = select(func.count(func.distinct(ApiKey.owner_id)))
        result = await self.session.execute(stmt)
        users_with_keys = result.scalar() or 0

        stats = {
            "total": total,
            "users_with_keys": users_with_keys,
        }
        logger.info("Generated API key statistics", extra={"stats": stats})
        return stats