#!/usr/bin/env python3
"""
Example 1: Basic Usage - Setup and Simple Operations

This example shows:
- How to initialize the database
- How to create users
- How to query users
- Basic repository patterns
"""

import asyncio
import os
from abs_orm import (
    init_db,
    get_session,
    User,
    UserRole,
    UserRepository,
    DocumentRepository,
    ApiKeyRepository,
)
from abs_utils.logger import setup_logging

# Use SQLite for examples
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


async def setup_database():
    """Initialize the database with tables"""
    print("🔧 Setting up database...")
    await init_db()
    print("✅ Database initialized!\n")


async def create_users():
    """Create some example users"""
    print("👥 Creating users...")

    async with get_session() as session:
        repo = UserRepository(session)

        # Create an admin user
        admin = await repo.create(
            email="admin@abs-notary.com", hashed_password="hashed_pw_123", role=UserRole.ADMIN
        )
        print(f"  ✅ Created admin: {admin.email}")

        # Create regular users
        user1 = await repo.create(
            email="alice@example.com", hashed_password="hashed_pw_456", role=UserRole.USER
        )
        print(f"  ✅ Created user: {user1.email}")

        user2 = await repo.create(
            email="bob@example.com", hashed_password="hashed_pw_789", role=UserRole.USER
        )
        print(f"  ✅ Created user: {user2.email}")

        await session.commit()

    print()


async def query_users():
    """Query users using repository methods"""
    print("🔍 Querying users...")

    async with get_session() as session:
        repo = UserRepository(session)

        # Get all users
        all_users = await repo.get_all()
        print(f"  📊 Total users: {len(all_users)}")

        # Get user by email
        user = await repo.get_by_email("alice@example.com")
        if user:
            print(f"  👤 Found user: {user.email} (ID: {user.id})")

        # Check if email exists
        exists = await repo.email_exists("nonexistent@example.com")
        print(f"  ❓ Does nonexistent@example.com exist? {exists}")

        # Get all admins
        admins = await repo.get_all_admins()
        print(f"  👑 Admin users: {[u.email for u in admins]}")

        # Check if user is admin
        is_admin = await repo.is_admin(user.id)
        print(f"  ❓ Is {user.email} an admin? {is_admin}")

    print()


async def update_user():
    """Update a user"""
    print("✏️  Updating user...")

    async with get_session() as session:
        repo = UserRepository(session)

        # Get user
        user = await repo.get_by_email("bob@example.com")
        if user:
            # Promote to admin
            await repo.promote_to_admin(user.id)
            print(f"  ⬆️  Promoted {user.email} to admin")

            # Verify
            updated_user = await repo.get(user.id)
            print(f"  ✅ New role: {updated_user.role.value}")

        await session.commit()

    print()


async def user_statistics():
    """Get user statistics"""
    print("📈 User Statistics...")

    async with get_session() as session:
        repo = UserRepository(session)

        stats = await repo.get_user_stats()
        print(f"  Total users: {stats['total']}")
        print(f"  Admin users: {stats['admins']}")
        print(f"  Regular users: {stats['regular_users']}")

    print()


async def main():
    print("=" * 80)
    print("EXAMPLE 1: BASIC USAGE")
    print("=" * 80)
    print()

    # Setup logging
    setup_logging(level="WARNING", log_format="text")  # Quiet for demo

    # Setup database (creates tables)
    await setup_database()

    # Create users
    await create_users()

    # Query users
    await query_users()

    # Update user
    await update_user()

    # Get statistics
    await user_statistics()

    print("=" * 80)
    print("✅ Example complete!")
    print("\nKey Takeaways:")
    print("- Use init_db() to create database tables (development only)")
    print("- Use get_session() context manager for database access")
    print("- Repositories provide clean, high-level database operations")
    print("- All async operations use 'await'")
    print("- Remember to commit() to save changes")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
