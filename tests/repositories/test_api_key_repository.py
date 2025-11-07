"""
Tests for ApiKeyRepository
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.api_key import ApiKey
from abs_orm.models.user import User
from abs_orm.repositories.api_key import ApiKeyRepository


class TestApiKeyRepository:
    """Test ApiKeyRepository specific methods"""

    @pytest.mark.asyncio
    async def test_get_by_key_hash(self, session: AsyncSession, test_api_key: ApiKey):
        """Test getting API key by key hash"""
        repo = ApiKeyRepository(session)

        api_key = await repo.get_by_key_hash(test_api_key.key_hash)

        assert api_key is not None
        assert api_key.id == test_api_key.id
        assert api_key.key_hash == test_api_key.key_hash

    @pytest.mark.asyncio
    async def test_get_by_key_hash_not_found(self, session: AsyncSession):
        """Test getting API key by non-existent hash"""
        repo = ApiKeyRepository(session)

        api_key = await repo.get_by_key_hash("nonexistent_hash")

        assert api_key is None

    @pytest.mark.asyncio
    async def test_get_by_prefix(self, session: AsyncSession, test_api_key: ApiKey):
        """Test getting API key by prefix"""
        repo = ApiKeyRepository(session)

        api_key = await repo.get_by_prefix(test_api_key.prefix)

        assert api_key is not None
        assert api_key.id == test_api_key.id
        assert api_key.prefix == test_api_key.prefix

    @pytest.mark.asyncio
    async def test_get_user_api_keys(self, session: AsyncSession, test_user: User, test_api_key: ApiKey):
        """Test getting all API keys for a user"""
        repo = ApiKeyRepository(session)

        # Create additional API keys for the user
        key2 = ApiKey(
            owner_id=test_user.id,
            key_hash="second_hash",
            prefix="sk_live_",
            description="Production API Key"
        )
        key3 = ApiKey(
            owner_id=test_user.id,
            key_hash="third_hash",
            prefix="sk_dev_",
            description="Development API Key"
        )
        session.add_all([key2, key3])
        await session.flush()

        keys = await repo.get_user_api_keys(test_user.id)

        assert len(keys) == 3
        prefixes = [k.prefix for k in keys]
        assert test_api_key.prefix in prefixes
        assert "sk_live_" in prefixes
        assert "sk_dev_" in prefixes

    @pytest.mark.asyncio
    async def test_get_user_api_keys_empty(self, session: AsyncSession, test_user: User):
        """Test getting API keys for user with no keys"""
        repo = ApiKeyRepository(session)

        # Create a user without API keys
        new_user = User(
            email="nokeys@example.com",
            hashed_password="pwd",
            role=test_user.role
        )
        session.add(new_user)
        await session.flush()

        keys = await repo.get_user_api_keys(new_user.id)

        assert len(keys) == 0

    @pytest.mark.asyncio
    async def test_key_hash_exists(self, session: AsyncSession, test_api_key: ApiKey):
        """Test checking if key hash exists"""
        repo = ApiKeyRepository(session)

        exists = await repo.key_hash_exists(test_api_key.key_hash)
        assert exists is True

        not_exists = await repo.key_hash_exists("new_hash_456")
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_validate_api_key(self, session: AsyncSession, test_api_key: ApiKey, test_user: User):
        """Test validating API key and getting owner"""
        repo = ApiKeyRepository(session)

        user = await repo.validate_api_key(test_api_key.key_hash)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, session: AsyncSession):
        """Test validating invalid API key"""
        repo = ApiKeyRepository(session)

        user = await repo.validate_api_key("invalid_hash")

        assert user is None

    @pytest.mark.asyncio
    async def test_count_user_api_keys(self, session: AsyncSession, test_user: User, test_api_key: ApiKey):
        """Test counting API keys for a user"""
        repo = ApiKeyRepository(session)

        # Create more API keys
        for i in range(2):
            key = ApiKey(
                owner_id=test_user.id,
                key_hash=f"count_hash_{i}",
                prefix=f"sk_count{i}_"
            )
            session.add(key)
        await session.flush()

        count = await repo.count_user_api_keys(test_user.id)

        assert count == 3  # 1 test key + 2 new ones

    @pytest.mark.asyncio
    async def test_search_by_description(self, session: AsyncSession, test_api_key: ApiKey):
        """Test searching API keys by description"""
        repo = ApiKeyRepository(session)

        # Create keys with different descriptions
        key2 = ApiKey(
            owner_id=test_api_key.owner_id,
            key_hash="prod_hash",
            prefix="sk_prod_",
            description="Production API Key for payment service"
        )
        key3 = ApiKey(
            owner_id=test_api_key.owner_id,
            key_hash="webhook_hash",
            prefix="sk_hook_",
            description="Webhook endpoint key"
        )
        session.add_all([key2, key3])
        await session.flush()

        # Search for "API"
        results = await repo.search_by_description("API")
        assert len(results) >= 2  # test key and prod key

        # Search for "webhook"
        webhook_results = await repo.search_by_description("webhook")
        assert len(webhook_results) == 1
        assert webhook_results[0].prefix == "sk_hook_"

    @pytest.mark.asyncio
    async def test_get_recent_api_keys(self, session: AsyncSession, test_api_key: ApiKey):
        """Test getting recently created API keys"""
        repo = ApiKeyRepository(session)

        recent = await repo.get_recent_api_keys(days=7)

        assert isinstance(recent, list)
        # Should include test_api_key created recently
        assert len(recent) >= 1

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, session: AsyncSession, test_api_key: ApiKey):
        """Test revoking (deleting) an API key"""
        repo = ApiKeyRepository(session)

        success = await repo.revoke_api_key(test_api_key.id)

        assert success is True

        # Verify it's deleted
        revoked = await repo.get(test_api_key.id)
        assert revoked is None

    @pytest.mark.asyncio
    async def test_revoke_api_key_nonexistent(self, session: AsyncSession):
        """Test revoking non-existent API key"""
        repo = ApiKeyRepository(session)

        success = await repo.revoke_api_key(99999)

        assert success is False

    @pytest.mark.asyncio
    async def test_revoke_user_api_keys(self, session: AsyncSession, test_user: User):
        """Test revoking all API keys for a user"""
        repo = ApiKeyRepository(session)

        # Create multiple API keys for the user
        keys = []
        for i in range(3):
            key = ApiKey(
                owner_id=test_user.id,
                key_hash=f"revoke_hash_{i}",
                prefix=f"sk_rev{i}_"
            )
            keys.append(key)
        session.add_all(keys)
        await session.flush()

        # Revoke all keys for the user
        count = await repo.revoke_user_api_keys(test_user.id)

        assert count >= 3  # At least the 3 we created

        # Verify all are deleted
        remaining = await repo.get_user_api_keys(test_user.id)
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_update_description(self, session: AsyncSession, test_api_key: ApiKey):
        """Test updating API key description"""
        repo = ApiKeyRepository(session)

        new_description = "Updated description for testing"
        updated = await repo.update_description(test_api_key.id, new_description)

        assert updated is not None
        assert updated.id == test_api_key.id
        assert updated.description == new_description

    @pytest.mark.asyncio
    async def test_update_description_nonexistent(self, session: AsyncSession):
        """Test updating description for non-existent key"""
        repo = ApiKeyRepository(session)

        updated = await repo.update_description(99999, "New description")

        assert updated is None

    @pytest.mark.asyncio
    async def test_get_with_owner(self, session: AsyncSession, test_api_key: ApiKey, test_user: User):
        """Test getting API key with owner relationship loaded"""
        repo = ApiKeyRepository(session)

        api_key = await repo.get_with_owner(test_api_key.id)

        assert api_key is not None
        assert api_key.id == test_api_key.id
        assert api_key.owner_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_api_key(self, session: AsyncSession, test_user: User):
        """Test creating API key with validation"""
        repo = ApiKeyRepository(session)

        api_key = await repo.create_api_key(
            owner_id=test_user.id,
            key_hash="new_secure_hash",
            prefix="sk_new_",
            description="New API key for testing"
        )

        assert api_key is not None
        assert api_key.owner_id == test_user.id
        assert api_key.key_hash == "new_secure_hash"
        assert api_key.prefix == "sk_new_"
        assert api_key.description == "New API key for testing"

    @pytest.mark.asyncio
    async def test_get_api_keys_paginated(self, session: AsyncSession, test_api_key: ApiKey):
        """Test paginated API key retrieval"""
        repo = ApiKeyRepository(session)

        # Create multiple API keys
        for i in range(5):
            key = ApiKey(
                owner_id=test_api_key.owner_id,
                key_hash=f"page_hash_{i}",
                prefix=f"sk_pg{i}_"
            )
            session.add(key)
        await session.flush()

        # Test pagination
        page1 = await repo.get_paginated(page=1, page_size=3)
        assert len(page1) <= 3

        page2 = await repo.get_paginated(page=2, page_size=3)
        assert len(page2) >= 0

    @pytest.mark.asyncio
    async def test_get_api_key_stats(self, session: AsyncSession, test_api_key: ApiKey):
        """Test getting API key statistics"""
        repo = ApiKeyRepository(session)

        # Create more API keys for different users
        user2 = User(
            email="user2@example.com",
            hashed_password="pwd2",
            role=test_api_key.owner.role
        )
        session.add(user2)
        await session.flush()

        for i in range(3):
            key = ApiKey(
                owner_id=user2.id,
                key_hash=f"stats_hash_{i}",
                prefix=f"sk_stat{i}_"
            )
            session.add(key)
        await session.flush()

        stats = await repo.get_api_key_stats()

        assert stats["total"] >= 4  # test key + 3 new ones
        assert stats["users_with_keys"] >= 2  # test user + user2