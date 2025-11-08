"""Factory for creating ApiKey test data."""
import hashlib
import pytest_asyncio
from typing import Optional

from abs_orm.models.api_key import ApiKey
from abs_orm.models.user import User
from .base_factory import BaseFactory
from .user_factory import UserFactory


class ApiKeyFactory(BaseFactory):
    """Factory for creating ApiKey instances."""

    model = ApiKey

    @classmethod
    def get_defaults(cls) -> dict:
        """Get default values for ApiKey."""
        # Generate a random key and hash it
        raw_key = cls.random_string(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = "sk_test_" + cls.random_string(8)

        return {
            "key_hash": key_hash,
            "prefix": prefix,
            "description": f"Test API Key - {cls.random_string(10)}",
        }

    @classmethod
    async def create(cls, session, owner: Optional[User] = None, **kwargs):
        """Create an API key, auto-creating owner if not provided."""
        if owner is None and "owner_id" not in kwargs:
            owner = await UserFactory.create(session)
            kwargs["owner_id"] = owner.id

        if owner is not None and "owner_id" not in kwargs:
            kwargs["owner_id"] = owner.id

        return await super().create(session, **kwargs)


@pytest_asyncio.fixture
async def api_key_factory():
    """Fixture that returns the ApiKeyFactory class."""
    return ApiKeyFactory
