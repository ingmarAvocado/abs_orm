"""
Base repository with generic CRUD operations
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from abs_orm.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository class with generic CRUD operations.

    Provides common database operations for any SQLAlchemy model.
    Uses Generic[T] for type safety.
    """

    def __init__(self, model: Type[T], session: AsyncSession):
        """
        Initialize repository with model class and session.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> T:
        """
        Create a new entity.

        Args:
            **kwargs: Field values for the new entity

        Returns:
            Created entity instance
        """
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, id: int) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity instance or None if not found
        """
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all entities with optional pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        stmt = select(self.model)

        if offset is not None:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by(self, field: str, value: Any) -> Optional[T]:
        """
        Get entity by specific field value.

        Args:
            field: Field name
            value: Field value to match

        Returns:
            Entity instance or None if not found
        """
        stmt = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def filter_by(self, **kwargs) -> List[T]:
        """
        Filter entities by field values.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            List of matching entities
        """
        stmt = select(self.model)

        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update entity by ID.

        Args:
            id: Entity ID
            **kwargs: Field-value pairs to update

        Returns:
            Updated entity or None if not found
        """
        entity = await self.get(id)

        if entity is None:
            return None

        for field, value in kwargs.items():
            setattr(entity, field, value)

        await self.session.flush()
        return entity

    async def delete(self, id: int) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        entity = await self.get(id)

        if entity is None:
            return False

        await self.session.delete(entity)
        await self.session.flush()
        return True

    async def exists(self, id: int) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(self.model.id).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by(self, field: str, value: Any) -> bool:
        """
        Check if entity exists by field value.

        Args:
            field: Field name
            value: Field value to check

        Returns:
            True if exists, False otherwise
        """
        stmt = select(self.model.id).where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count(self, **kwargs) -> int:
        """
        Count entities with optional filtering.

        Args:
            **kwargs: Optional field-value pairs to filter by

        Returns:
            Number of matching entities
        """
        stmt = select(func.count()).select_from(self.model)

        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def bulk_create(self, entities_data: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple entities at once.

        Args:
            entities_data: List of dictionaries with entity data

        Returns:
            List of created entities
        """
        entities = [self.model(**data) for data in entities_data]
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple entities at once.

        Args:
            updates: List of dicts with 'id' and fields to update

        Returns:
            Number of updated entities
        """
        updated_count = 0

        for update_data in updates:
            entity_id = update_data.pop('id')
            entity = await self.get(entity_id)

            if entity is not None:
                for field, value in update_data.items():
                    setattr(entity, field, value)
                updated_count += 1

        await self.session.flush()
        return updated_count

    async def refresh(self, entity: T) -> None:
        """
        Refresh entity from database.

        Args:
            entity: Entity instance to refresh
        """
        await self.session.refresh(entity)

    async def first(self, **kwargs) -> Optional[T]:
        """
        Get first entity matching criteria.

        Args:
            **kwargs: Field-value pairs to filter by

        Returns:
            First matching entity or None
        """
        stmt = select(self.model)

        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        **kwargs
    ) -> List[T]:
        """
        Get paginated results.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            **kwargs: Optional filters

        Returns:
            List of entities for the requested page
        """
        offset = (page - 1) * page_size

        stmt = select(self.model)

        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())