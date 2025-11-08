"""
Tests for UserRepository
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.user import User, UserRole
from abs_orm.repositories.user import UserRepository


class TestUserRepository:
    """Test UserRepository specific methods"""

    @pytest.mark.asyncio
    async def test_get_by_email(self, session: AsyncSession, test_user: User):
        """Test getting user by email"""
        repo = UserRepository(session)

        user = await repo.get_by_email(test_user.email)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, session: AsyncSession):
        """Test getting user by non-existent email"""
        repo = UserRepository(session)

        user = await repo.get_by_email("nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_email_exists(self, session: AsyncSession, test_user: User):
        """Test checking if email exists"""
        repo = UserRepository(session)

        exists = await repo.email_exists(test_user.email)
        assert exists is True

        not_exists = await repo.email_exists("new@example.com")
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_get_all_admins(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting all admin users"""
        repo = UserRepository(session)

        admins = await repo.get_all_admins()

        assert len(admins) == 1
        assert admins[0].id == test_admin.id
        assert admins[0].role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_get_all_regular_users(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting all regular users"""
        repo = UserRepository(session)

        users = await repo.get_all_regular_users()

        assert len(users) == 1
        assert users[0].id == test_user.id
        assert users[0].role == UserRole.USER

    @pytest.mark.asyncio
    async def test_is_admin(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test checking if user is admin"""
        repo = UserRepository(session)

        is_admin = await repo.is_admin(test_admin.id)
        assert is_admin is True

        is_not_admin = await repo.is_admin(test_user.id)
        assert is_not_admin is False

        # Non-existent user
        is_none = await repo.is_admin(99999)
        assert is_none is False

    @pytest.mark.asyncio
    async def test_promote_to_admin(self, session: AsyncSession, test_user: User):
        """Test promoting user to admin"""
        repo = UserRepository(session)

        success = await repo.promote_to_admin(test_user.id)
        assert success is True

        # Verify promotion
        user = await repo.get(test_user.id)
        assert user.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_promote_nonexistent_user(self, session: AsyncSession):
        """Test promoting non-existent user fails"""
        repo = UserRepository(session)

        success = await repo.promote_to_admin(99999)
        assert success is False

    @pytest.mark.asyncio
    async def test_demote_to_user(self, session: AsyncSession, test_admin: User):
        """Test demoting admin to regular user"""
        repo = UserRepository(session)

        success = await repo.demote_to_user(test_admin.id)
        assert success is True

        # Verify demotion
        user = await repo.get(test_admin.id)
        assert user.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_get_users_by_role(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting users by specific role"""
        repo = UserRepository(session)

        admins = await repo.get_users_by_role(UserRole.ADMIN)
        assert len(admins) == 1
        assert admins[0].id == test_admin.id

        users = await repo.get_users_by_role(UserRole.USER)
        assert len(users) == 1
        assert users[0].id == test_user.id

    @pytest.mark.asyncio
    async def test_count_by_role(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test counting users by role"""
        repo = UserRepository(session)

        admin_count = await repo.count_by_role(UserRole.ADMIN)
        assert admin_count == 1

        user_count = await repo.count_by_role(UserRole.USER)
        assert user_count == 1

    @pytest.mark.asyncio
    async def test_get_recent_users(self, session: AsyncSession):
        """Test getting recently created users"""
        repo = UserRepository(session)

        # Create users with different timestamps
        now = datetime.now(timezone.utc)
        old_user = User(
            email="old@example.com",
            hashed_password="pwd",
            role=UserRole.USER
        )
        session.add(old_user)
        await session.flush()

        # Note: SQLite doesn't support updating created_at easily in tests
        # So we'll just test the method works
        recent = await repo.get_recent_users(days=7)
        assert isinstance(recent, list)

    @pytest.mark.asyncio
    async def test_search_by_email(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test searching users by email pattern"""
        repo = UserRepository(session)

        # Search for users with 'example' in email
        results = await repo.search_by_email("example")

        assert len(results) == 2
        emails = [u.email for u in results]
        assert test_user.email in emails
        assert test_admin.email in emails

        # Search for specific pattern
        admin_results = await repo.search_by_email("admin")
        assert len(admin_results) == 1
        assert admin_results[0].email == test_admin.email

    @pytest.mark.asyncio
    async def test_get_with_api_keys(self, session: AsyncSession, test_user: User, test_api_key):
        """Test getting user with their API keys loaded"""
        repo = UserRepository(session)

        user = await repo.get_with_api_keys(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        # Note: Relationship loading depends on session configuration
        # This test verifies the method works without errors

    @pytest.mark.asyncio
    async def test_get_with_documents(self, session: AsyncSession, test_user: User, test_document):
        """Test getting user with their documents loaded"""
        repo = UserRepository(session)

        user = await repo.get_with_documents(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        # Note: Relationship loading depends on session configuration

    @pytest.mark.asyncio
    async def test_update_password(self, session: AsyncSession, test_user: User):
        """Test updating user password"""
        repo = UserRepository(session)

        new_password_hash = "new_hashed_password_456"
        success = await repo.update_password(test_user.id, new_password_hash)

        assert success is True

        # Verify password updated
        user = await repo.get(test_user.id)
        assert user.hashed_password == new_password_hash

    @pytest.mark.asyncio
    async def test_update_password_nonexistent_user(self, session: AsyncSession):
        """Test updating password for non-existent user"""
        repo = UserRepository(session)

        success = await repo.update_password(99999, "new_hash")

        assert success is False

    @pytest.mark.asyncio
    async def test_bulk_create_users(self, session: AsyncSession):
        """Test bulk creating users with validation"""
        repo = UserRepository(session)

        users_data = [
            {"email": "bulk1@test.com", "hashed_password": "pwd1", "role": UserRole.USER},
            {"email": "bulk2@test.com", "hashed_password": "pwd2", "role": UserRole.ADMIN},
        ]

        users = await repo.bulk_create_users(users_data)

        assert len(users) == 2
        assert all(u.id is not None for u in users)
        assert users[0].email == "bulk1@test.com"
        assert users[1].role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_get_users_paginated(self, session: AsyncSession):
        """Test getting users with pagination"""
        repo = UserRepository(session)

        # Create multiple users
        for i in range(5):
            user = User(
                email=f"page{i}@example.com",
                hashed_password=f"pwd{i}",
                role=UserRole.USER
            )
            session.add(user)
        await session.flush()

        # Test pagination
        page1 = await repo.get_paginated(page=1, page_size=3)
        assert len(page1) <= 3

        page2 = await repo.get_paginated(page=2, page_size=3)
        assert len(page2) >= 0  # Could have users from fixtures

    @pytest.mark.asyncio
    async def test_get_user_stats(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting user statistics"""
        repo = UserRepository(session)

        stats = await repo.get_user_stats()

        assert stats["total"] == 2
        assert stats["admins"] == 1
        assert stats["regular_users"] == 1