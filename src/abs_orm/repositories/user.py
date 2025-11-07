"""
User repository with user-specific queries
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from abs_orm.models.user import User, UserRole
from abs_orm.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with user-specific operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize UserRepository.

        Args:
            session: Async database session
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User instance or None if not found
        """
        return await self.get_by("email", email)

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        return await self.exists_by("email", email)

    async def get_all_admins(self) -> List[User]:
        """
        Get all admin users.

        Returns:
            List of admin users
        """
        return await self.filter_by(role=UserRole.ADMIN)

    async def get_all_regular_users(self) -> List[User]:
        """
        Get all regular (non-admin) users.

        Returns:
            List of regular users
        """
        return await self.filter_by(role=UserRole.USER)

    async def is_admin(self, user_id: int) -> bool:
        """
        Check if user is an admin.

        Args:
            user_id: User ID to check

        Returns:
            True if user is admin, False otherwise
        """
        user = await self.get(user_id)
        return user is not None and user.role == UserRole.ADMIN

    async def promote_to_admin(self, user_id: int) -> bool:
        """
        Promote user to admin role.

        Args:
            user_id: User ID to promote

        Returns:
            True if successful, False if user not found
        """
        updated = await self.update(user_id, role=UserRole.ADMIN)
        return updated is not None

    async def demote_to_user(self, user_id: int) -> bool:
        """
        Demote admin to regular user role.

        Args:
            user_id: User ID to demote

        Returns:
            True if successful, False if user not found
        """
        updated = await self.update(user_id, role=UserRole.USER)
        return updated is not None

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        Get users by specific role.

        Args:
            role: User role

        Returns:
            List of users with specified role
        """
        return await self.filter_by(role=role)

    async def count_by_role(self, role: UserRole) -> int:
        """
        Count users by role.

        Args:
            role: User role

        Returns:
            Number of users with specified role
        """
        return await self.count(role=role)

    async def get_recent_users(self, days: int = 7) -> List[User]:
        """
        Get users created in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recently created users
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(User).where(User.created_at >= cutoff_date)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_email(self, pattern: str) -> List[User]:
        """
        Search users by email pattern.

        Args:
            pattern: Email pattern to search for

        Returns:
            List of users matching the pattern
        """
        stmt = select(User).where(User.email.ilike(f"%{pattern}%"))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_api_keys(self, user_id: int) -> Optional[User]:
        """
        Get user with their API keys loaded.

        Args:
            user_id: User ID

        Returns:
            User with api_keys relationship loaded
        """
        stmt = select(User).options(
            selectinload(User.api_keys)
        ).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_documents(self, user_id: int) -> Optional[User]:
        """
        Get user with their documents loaded.

        Args:
            user_id: User ID

        Returns:
            User with documents relationship loaded
        """
        stmt = select(User).options(
            selectinload(User.documents)
        ).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """
        Update user password.

        Args:
            user_id: User ID
            hashed_password: New hashed password

        Returns:
            True if successful, False if user not found
        """
        updated = await self.update(user_id, hashed_password=hashed_password)
        return updated is not None

    async def bulk_create_users(self, users_data: List[Dict[str, Any]]) -> List[User]:
        """
        Create multiple users with validation.

        Args:
            users_data: List of user data dictionaries

        Returns:
            List of created users
        """
        # Validate that emails are unique
        emails = [data.get("email") for data in users_data]
        if len(emails) != len(set(emails)):
            raise ValueError("Duplicate emails in bulk create")

        return await self.bulk_create(users_data)

    async def get_user_stats(self) -> Dict[str, int]:
        """
        Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        total = await self.count()
        admins = await self.count_by_role(UserRole.ADMIN)
        regular_users = await self.count_by_role(UserRole.USER)

        return {
            "total": total,
            "admins": admins,
            "regular_users": regular_users,
        }