"""
Tests for logging integration in UserRepository
"""

import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.user import User, UserRole
from abs_orm.repositories.user import UserRepository


class TestUserRepositoryLogging:
    """Test UserRepository logging integration"""

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_get_by_email_logs_info(self, mock_logger, session: AsyncSession, test_user: User):
        """Test get_by_email logs info when user found"""
        repo = UserRepository(session)

        user = await repo.get_by_email(test_user.email)

        assert user is not None
        mock_logger.info.assert_called_with(
            "Fetching user by email",
            extra={"email": test_user.email}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_get_by_email_logs_warning(self, mock_logger, session: AsyncSession):
        """Test get_by_email logs warning when user not found"""
        repo = UserRepository(session)

        user = await repo.get_by_email("nonexistent@example.com")

        assert user is None
        mock_logger.info.assert_called_with(
            "Fetching user by email",
            extra={"email": "nonexistent@example.com"}
        )
        mock_logger.warning.assert_called_with(
            "User not found",
            extra={"email": "nonexistent@example.com"}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_promote_to_admin_logs_success(self, mock_logger, session: AsyncSession, test_user: User):
        """Test promote_to_admin logs successful promotion"""
        repo = UserRepository(session)

        success = await repo.promote_to_admin(test_user.id)

        assert success is True
        mock_logger.info.assert_any_call(
            "Promoting user to admin",
            extra={"user_id": test_user.id}
        )
        mock_logger.info.assert_any_call(
            "User promoted to admin successfully",
            extra={"user_id": test_user.id}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_promote_to_admin_logs_failure(self, mock_logger, session: AsyncSession):
        """Test promote_to_admin logs failure for non-existent user"""
        repo = UserRepository(session)

        success = await repo.promote_to_admin(99999)

        assert success is False
        mock_logger.info.assert_called_with(
            "Promoting user to admin",
            extra={"user_id": 99999}
        )
        mock_logger.warning.assert_called_with(
            "Failed to promote user to admin - user not found",
            extra={"user_id": 99999}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_demote_to_user_logs_success(self, mock_logger, session: AsyncSession, test_admin: User):
        """Test demote_to_user logs successful demotion"""
        repo = UserRepository(session)

        success = await repo.demote_to_user(test_admin.id)

        assert success is True
        mock_logger.info.assert_any_call(
            "Demoting admin to regular user",
            extra={"user_id": test_admin.id}
        )
        mock_logger.info.assert_any_call(
            "Admin demoted to regular user successfully",
            extra={"user_id": test_admin.id}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_email_exists_logs(self, mock_logger, session: AsyncSession, test_user: User):
        """Test email_exists logs the check"""
        repo = UserRepository(session)

        exists = await repo.email_exists(test_user.email)

        assert exists is True
        mock_logger.debug.assert_called_with(
            "Checking if email exists",
            extra={"email": test_user.email, "exists": True}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_update_password_logs_success(self, mock_logger, session: AsyncSession, test_user: User):
        """Test update_password logs successful update"""
        repo = UserRepository(session)

        success = await repo.update_password(test_user.id, "new_hash")

        assert success is True
        mock_logger.info.assert_any_call(
            "Updating user password",
            extra={"user_id": test_user.id}
        )
        mock_logger.info.assert_any_call(
            "Password updated successfully",
            extra={"user_id": test_user.id}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_update_password_logs_failure(self, mock_logger, session: AsyncSession):
        """Test update_password logs failure"""
        repo = UserRepository(session)

        success = await repo.update_password(99999, "new_hash")

        assert success is False
        mock_logger.info.assert_called_with(
            "Updating user password",
            extra={"user_id": 99999}
        )
        mock_logger.warning.assert_called_with(
            "Failed to update password - user not found",
            extra={"user_id": 99999}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_search_by_email_logs(self, mock_logger, session: AsyncSession, test_user: User):
        """Test search_by_email logs the search"""
        repo = UserRepository(session)

        results = await repo.search_by_email("example")

        mock_logger.info.assert_called_with(
            "Searching users by email pattern",
            extra={"pattern": "example", "results_count": len(results)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_get_user_stats_logs(self, mock_logger, session: AsyncSession, test_user: User, test_admin: User):
        """Test get_user_stats logs statistics"""
        repo = UserRepository(session)

        stats = await repo.get_user_stats()

        mock_logger.info.assert_called_with(
            "Generated user statistics",
            extra={"stats": stats}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_bulk_create_users_logs(self, mock_logger, session: AsyncSession):
        """Test bulk_create_users logs the operation"""
        repo = UserRepository(session)

        users_data = [
            {"email": "bulk1@test.com", "hashed_password": "pwd1", "role": UserRole.USER},
            {"email": "bulk2@test.com", "hashed_password": "pwd2", "role": UserRole.ADMIN},
        ]

        users = await repo.bulk_create_users(users_data)

        mock_logger.info.assert_any_call(
            "Bulk creating users",
            extra={"count": 2}
        )
        mock_logger.info.assert_any_call(
            "Bulk created users successfully",
            extra={"count": len(users)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_bulk_create_users_logs_duplicate_error(self, mock_logger, session: AsyncSession):
        """Test bulk_create_users logs error for duplicate emails"""
        repo = UserRepository(session)

        users_data = [
            {"email": "same@test.com", "hashed_password": "pwd1", "role": UserRole.USER},
            {"email": "same@test.com", "hashed_password": "pwd2", "role": UserRole.ADMIN},
        ]

        with pytest.raises(ValueError, match="Duplicate emails"):
            await repo.bulk_create_users(users_data)

        mock_logger.error.assert_called_with(
            "Duplicate emails in bulk create",
            extra={"emails": ["same@test.com", "same@test.com"]}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_get_recent_users_logs(self, mock_logger, session: AsyncSession):
        """Test get_recent_users logs the operation"""
        repo = UserRepository(session)

        recent = await repo.get_recent_users(days=7)

        mock_logger.info.assert_called_with(
            "Fetching recent users",
            extra={"days": 7, "count": len(recent)}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_is_admin_logs(self, mock_logger, session: AsyncSession, test_admin: User):
        """Test is_admin logs the check"""
        repo = UserRepository(session)

        is_admin = await repo.is_admin(test_admin.id)

        assert is_admin is True
        mock_logger.debug.assert_called_with(
            "Checking if user is admin",
            extra={"user_id": test_admin.id, "is_admin": True}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_get_with_api_keys_logs(self, mock_logger, session: AsyncSession, test_user: User):
        """Test get_with_api_keys logs the operation"""
        repo = UserRepository(session)

        user = await repo.get_with_api_keys(test_user.id)

        mock_logger.info.assert_called_with(
            "Fetching user with API keys",
            extra={"user_id": test_user.id}
        )

    @pytest.mark.asyncio
    @patch('abs_orm.repositories.user.logger')
    async def test_get_with_documents_logs(self, mock_logger, session: AsyncSession, test_user: User):
        """Test get_with_documents logs the operation"""
        repo = UserRepository(session)

        user = await repo.get_with_documents(test_user.id)

        mock_logger.info.assert_called_with(
            "Fetching user with documents",
            extra={"user_id": test_user.id}
        )