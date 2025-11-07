"""
Tests for BaseRepository
"""

import pytest
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from abs_orm.models.user import User, UserRole
from abs_orm.models.document import Document
from abs_orm.repositories.base import BaseRepository


class TestBaseRepository:
    """Test BaseRepository with User model"""

    @pytest.mark.asyncio
    async def test_create_entity(self, session: AsyncSession):
        """Test creating a new entity"""
        repo = BaseRepository[User](User, session)

        user_data = {
            "email": "new@example.com",
            "hashed_password": "hashed_pwd",
            "role": UserRole.USER
        }

        user = await repo.create(**user_data)

        assert user.id is not None
        assert user.email == "new@example.com"
        assert user.role == UserRole.USER

        # Verify in database
        result = await session.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one()
        assert db_user.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id(self, session: AsyncSession, test_user: User):
        """Test getting entity by ID"""
        repo = BaseRepository[User](User, session)

        user = await repo.get(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, session: AsyncSession):
        """Test getting non-existent entity returns None"""
        repo = BaseRepository[User](User, session)

        user = await repo.get(99999)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_all(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting all entities"""
        repo = BaseRepository[User](User, session)

        users = await repo.get_all()

        assert len(users) == 2
        emails = [u.email for u in users]
        assert test_user.email in emails
        assert test_admin.email in emails

    @pytest.mark.asyncio
    async def test_get_all_with_limit(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting entities with limit"""
        repo = BaseRepository[User](User, session)

        users = await repo.get_all(limit=1)

        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_get_all_with_offset(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting entities with offset"""
        repo = BaseRepository[User](User, session)

        users = await repo.get_all(offset=1)

        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_get_by_field(self, session: AsyncSession, test_user: User):
        """Test getting entity by specific field"""
        repo = BaseRepository[User](User, session)

        user = await repo.get_by("email", test_user.email)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_by_field_not_found(self, session: AsyncSession):
        """Test getting by field when not found returns None"""
        repo = BaseRepository[User](User, session)

        user = await repo.get_by("email", "nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_filter_by_single_field(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test filtering by single field"""
        repo = BaseRepository[User](User, session)

        users = await repo.filter_by(role=UserRole.ADMIN)

        assert len(users) == 1
        assert users[0].email == test_admin.email

    @pytest.mark.asyncio
    async def test_filter_by_multiple_fields(self, session: AsyncSession, test_admin: User):
        """Test filtering by multiple fields"""
        repo = BaseRepository[User](User, session)

        users = await repo.filter_by(
            email=test_admin.email,
            role=UserRole.ADMIN
        )

        assert len(users) == 1
        assert users[0].id == test_admin.id

    @pytest.mark.asyncio
    async def test_update_entity(self, session: AsyncSession, test_user: User):
        """Test updating an entity"""
        repo = BaseRepository[User](User, session)

        updated_user = await repo.update(
            test_user.id,
            email="updated@example.com"
        )

        assert updated_user is not None
        assert updated_user.id == test_user.id
        assert updated_user.email == "updated@example.com"

        # Verify in database
        result = await session.execute(select(User).where(User.id == test_user.id))
        db_user = result.scalar_one()
        assert db_user.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_nonexistent_entity(self, session: AsyncSession):
        """Test updating non-existent entity returns None"""
        repo = BaseRepository[User](User, session)

        updated_user = await repo.update(99999, email="fail@example.com")

        assert updated_user is None

    @pytest.mark.asyncio
    async def test_delete_entity(self, session: AsyncSession, test_user: User):
        """Test deleting an entity"""
        repo = BaseRepository[User](User, session)
        user_id = test_user.id

        success = await repo.delete(user_id)

        assert success is True

        # Verify deleted from database
        result = await session.execute(select(User).where(User.id == user_id))
        db_user = result.scalar_one_or_none()
        assert db_user is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity(self, session: AsyncSession):
        """Test deleting non-existent entity returns False"""
        repo = BaseRepository[User](User, session)

        success = await repo.delete(99999)

        assert success is False

    @pytest.mark.asyncio
    async def test_exists_by_id(self, session: AsyncSession, test_user: User):
        """Test checking if entity exists by ID"""
        repo = BaseRepository[User](User, session)

        exists = await repo.exists(test_user.id)
        assert exists is True

        not_exists = await repo.exists(99999)
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_exists_by_field(self, session: AsyncSession, test_user: User):
        """Test checking if entity exists by field"""
        repo = BaseRepository[User](User, session)

        exists = await repo.exists_by("email", test_user.email)
        assert exists is True

        not_exists = await repo.exists_by("email", "nonexistent@example.com")
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_count_all(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test counting all entities"""
        repo = BaseRepository[User](User, session)

        count = await repo.count()

        assert count == 2

    @pytest.mark.asyncio
    async def test_count_with_filter(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test counting with filter"""
        repo = BaseRepository[User](User, session)

        count = await repo.count(role=UserRole.ADMIN)

        assert count == 1

    @pytest.mark.asyncio
    async def test_bulk_create(self, session: AsyncSession):
        """Test bulk creating entities"""
        repo = BaseRepository[User](User, session)

        users_data = [
            {"email": "bulk1@example.com", "hashed_password": "pwd1", "role": UserRole.USER},
            {"email": "bulk2@example.com", "hashed_password": "pwd2", "role": UserRole.USER},
            {"email": "bulk3@example.com", "hashed_password": "pwd3", "role": UserRole.ADMIN},
        ]

        users = await repo.bulk_create(users_data)

        assert len(users) == 3
        assert all(u.id is not None for u in users)

        # Verify in database
        result = await session.execute(select(User).where(User.email.like("bulk%")))
        db_users = result.scalars().all()
        assert len(db_users) == 3

    @pytest.mark.asyncio
    async def test_bulk_update(self, session: AsyncSession):
        """Test bulk updating entities"""
        repo = BaseRepository[User](User, session)

        # Create users first
        users_data = [
            {"email": f"bulk_update{i}@example.com", "hashed_password": f"pwd{i}", "role": UserRole.USER}
            for i in range(3)
        ]
        users = await repo.bulk_create(users_data)

        # Update them
        updates = [
            {"id": users[0].id, "role": UserRole.ADMIN},
            {"id": users[1].id, "role": UserRole.ADMIN},
            {"id": users[2].id, "email": "updated_bulk@example.com"},
        ]

        updated_count = await repo.bulk_update(updates)

        assert updated_count == 3

        # Verify updates
        admin_users = await repo.filter_by(role=UserRole.ADMIN)
        assert len(admin_users) >= 2  # At least the 2 we just updated

    @pytest.mark.asyncio
    async def test_refresh_entity(self, session: AsyncSession, test_user: User):
        """Test refreshing an entity from database"""
        repo = BaseRepository[User](User, session)

        # Modify user without saving
        original_email = test_user.email
        test_user.email = "modified@example.com"

        # Refresh should restore original value
        await repo.refresh(test_user)

        assert test_user.email == original_email

    @pytest.mark.asyncio
    async def test_first_entity(self, session: AsyncSession, test_user: User, test_admin: User):
        """Test getting first entity matching criteria"""
        repo = BaseRepository[User](User, session)

        user = await repo.first(role=UserRole.USER)

        assert user is not None
        assert user.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_first_no_match(self, session: AsyncSession):
        """Test getting first when no match returns None"""
        repo = BaseRepository[User](User, session)

        user = await repo.first(email="nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_repository_with_different_model(self, session: AsyncSession, test_document: Document):
        """Test repository works with different model types"""
        repo = BaseRepository[Document](Document, session)

        doc = await repo.get(test_document.id)

        assert doc is not None
        assert doc.file_name == test_document.file_name

        # Test filter
        docs = await repo.filter_by(file_name="test_document.pdf")
        assert len(docs) == 1