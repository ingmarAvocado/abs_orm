"""Factory for creating User test data."""
import bcrypt
import pytest_asyncio

from abs_orm.models.user import User, UserRole
from .base_factory import BaseFactory


class UserFactory(BaseFactory):
    """Factory for creating User instances."""

    model = User

    @classmethod
    def get_defaults(cls) -> dict:
        """Get default values for User."""
        return {
            "email": "test@example.com",  # Use predictable email for test compatibility
            "hashed_password": bcrypt.hashpw(b"password", bcrypt.gensalt()).decode(),
            "role": UserRole.USER,
        }

    @classmethod
    async def create(cls, session, **kwargs):
        """Create a user with unique email if not provided."""
        # If email not provided, generate unique one to avoid conflicts
        if "email" not in kwargs:
            kwargs["email"] = cls.random_email()
        return await super().create(session, **kwargs)

    @classmethod
    async def create_admin(cls, session, **kwargs):
        """Create an admin user."""
        # Use predictable email for admin if not provided
        if "email" not in kwargs:
            kwargs["email"] = "admin@example.com"
        kwargs["role"] = UserRole.ADMIN
        return await cls.create(session, **kwargs)


@pytest_asyncio.fixture
async def user_factory():
    """Fixture that returns the UserFactory class."""
    return UserFactory
