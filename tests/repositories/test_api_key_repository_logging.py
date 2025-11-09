"""
Tests for logging integration in ApiKeyRepository
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.api_key import ApiKey
from abs_orm.models.user import User
from abs_orm.repositories.api_key import ApiKeyRepository


class TestApiKeyRepositoryLogging:
    """Test ApiKeyRepository logging integration"""

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_get_by_key_hash_logs_info(self, mock_logger, session: AsyncSession, test_api_key: ApiKey):
        """Test get_by_key_hash logs info when key found"""
        repo = ApiKeyRepository(session)

        key = await repo.get_by_key_hash(test_api_key.key_hash)

        assert key is not None
        mock_logger.info.assert_called_with(
            "Fetching API key by hash",
            extra={"key_hash": test_api_key.key_hash}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_get_by_key_hash_logs_warning(self, mock_logger, session: AsyncSession):
        """Test get_by_key_hash logs warning when key not found"""
        repo = ApiKeyRepository(session)

        key = await repo.get_by_key_hash("nonexistent_hash")

        assert key is None
        mock_logger.info.assert_called_with(
            "Fetching API key by hash",
            extra={"key_hash": "nonexistent_hash"}
        )
        mock_logger.warning.assert_called_with(
            "API key not found",
            extra={"key_hash": "nonexistent_hash"}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_validate_api_key_logs_success(self, mock_logger, session: AsyncSession, test_api_key: ApiKey):
        """Test validate_api_key logs successful validation"""
        repo = ApiKeyRepository(session)

        user = await repo.validate_api_key(test_api_key.key_hash)

        assert user is not None
        mock_logger.info.assert_called_with(
            "Validating API key",
            extra={"key_hash": test_api_key.key_hash, "valid": True}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_validate_api_key_logs_invalid(self, mock_logger, session: AsyncSession):
        """Test validate_api_key logs invalid key"""
        repo = ApiKeyRepository(session)

        user = await repo.validate_api_key("invalid_hash")

        assert user is None
        mock_logger.warning.assert_called_with(
            "Invalid API key",
            extra={"key_hash": "invalid_hash"}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_get_user_api_keys_logs(self, mock_logger, session: AsyncSession, test_user: User):
        """Test get_user_api_keys logs the operation"""
        repo = ApiKeyRepository(session)

        keys = await repo.get_user_api_keys(test_user.id)

        mock_logger.info.assert_called_with(
            "Fetching user API keys",
            extra={"user_id": test_user.id, "count": len(keys)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_revoke_api_key_logs_success(self, mock_logger, session: AsyncSession, test_api_key: ApiKey):
        """Test revoke_api_key logs successful revocation"""
        repo = ApiKeyRepository(session)

        success = await repo.revoke_api_key(test_api_key.id)

        assert success is True
        mock_logger.info.assert_any_call(
            "Revoking API key",
            extra={"key_id": test_api_key.id}
        )
        mock_logger.info.assert_any_call(
            "API key revoked successfully",
            extra={"key_id": test_api_key.id}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_revoke_api_key_logs_failure(self, mock_logger, session: AsyncSession):
        """Test revoke_api_key logs failure for non-existent key"""
        repo = ApiKeyRepository(session)

        success = await repo.revoke_api_key(99999)

        assert success is False
        mock_logger.info.assert_called_with(
            "Revoking API key",
            extra={"key_id": 99999}
        )
        mock_logger.warning.assert_called_with(
            "Failed to revoke API key - key not found",
            extra={"key_id": 99999}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_revoke_user_api_keys_logs(self, mock_logger, session: AsyncSession, test_user: User, test_api_key: ApiKey):
        """Test revoke_user_api_keys logs the operation"""
        repo = ApiKeyRepository(session)

        count = await repo.revoke_user_api_keys(test_user.id)

        mock_logger.info.assert_any_call(
            "Revoking all user API keys",
            extra={"user_id": test_user.id}
        )
        mock_logger.info.assert_any_call(
            "Revoked user API keys",
            extra={"user_id": test_user.id, "count": count}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_create_api_key_logs_success(self, mock_logger, session: AsyncSession, test_user: User):
        """Test create_api_key logs successful creation"""
        repo = ApiKeyRepository(session)

        api_key = await repo.create_api_key(
            owner_id=test_user.id,
            key_hash="new_hash_123",
            prefix="sk_test_",
            description="Test API key"
        )

        assert api_key is not None
        mock_logger.info.assert_any_call(
            "Creating new API key",
            extra={
                "owner_id": test_user.id,
                "prefix": "sk_test_",
                "description": "Test API key"
            }
        )
        mock_logger.info.assert_any_call(
            "API key created successfully",
            extra={
                "key_id": api_key.id,
                "owner_id": test_user.id,
                "prefix": "sk_test_"
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_create_api_key_logs_duplicate_error(self, mock_logger, session: AsyncSession, test_user: User, test_api_key: ApiKey):
        """Test create_api_key logs error for duplicate hash"""
        repo = ApiKeyRepository(session)

        with pytest.raises(ValueError, match="API key hash already exists"):
            await repo.create_api_key(
                owner_id=test_user.id,
                key_hash=test_api_key.key_hash,  # Duplicate hash
                prefix="sk_test_",
                description="Duplicate key"
            )

        mock_logger.error.assert_called_with(
            "Failed to create API key - hash already exists",
            extra={
                "owner_id": test_user.id,
                "key_hash": test_api_key.key_hash
            }
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_update_description_logs_success(self, mock_logger, session: AsyncSession, test_api_key: ApiKey):
        """Test update_description logs successful update"""
        repo = ApiKeyRepository(session)

        updated = await repo.update_description(test_api_key.id, "New description")

        assert updated is not None
        mock_logger.info.assert_any_call(
            "Updating API key description",
            extra={
                "key_id": test_api_key.id,
                "description": "New description"
            }
        )
        mock_logger.info.assert_any_call(
            "API key description updated successfully",
            extra={"key_id": test_api_key.id}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_update_description_logs_failure(self, mock_logger, session: AsyncSession):
        """Test update_description logs failure for non-existent key"""
        repo = ApiKeyRepository(session)

        updated = await repo.update_description(99999, "New description")

        assert updated is None
        mock_logger.warning.assert_called_with(
            "Failed to update API key description - key not found",
            extra={"key_id": 99999}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_key_hash_exists_logs(self, mock_logger, session: AsyncSession, test_api_key: ApiKey):
        """Test key_hash_exists logs the check"""
        repo = ApiKeyRepository(session)

        exists = await repo.key_hash_exists(test_api_key.key_hash)

        assert exists is True
        mock_logger.debug.assert_called_with(
            "Checking if API key hash exists",
            extra={"key_hash": test_api_key.key_hash, "exists": True}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_search_by_description_logs(self, mock_logger, session: AsyncSession):
        """Test search_by_description logs the operation"""
        repo = ApiKeyRepository(session)

        results = await repo.search_by_description("test")

        mock_logger.info.assert_called_with(
            "Searching API keys by description",
            extra={"pattern": "test", "results_count": len(results)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_get_recent_api_keys_logs(self, mock_logger, session: AsyncSession):
        """Test get_recent_api_keys logs the operation"""
        repo = ApiKeyRepository(session)

        keys = await repo.get_recent_api_keys(days=7)

        mock_logger.info.assert_called_with(
            "Fetching recent API keys",
            extra={"days": 7, "count": len(keys)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_get_api_key_stats_logs(self, mock_logger, session: AsyncSession):
        """Test get_api_key_stats logs statistics"""
        repo = ApiKeyRepository(session)

        stats = await repo.get_api_key_stats()

        mock_logger.info.assert_called_with(
            "Generated API key statistics",
            extra={"stats": stats}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.api_key.logger')
    async def test_get_with_owner_logs(self, mock_logger, session: AsyncSession, test_api_key: ApiKey):
        """Test get_with_owner logs the operation"""
        repo = ApiKeyRepository(session)

        key = await repo.get_with_owner(test_api_key.id)

        mock_logger.info.assert_called_with(
            "Fetching API key with owner",
            extra={"key_id": test_api_key.id}
        )