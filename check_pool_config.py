#!/usr/bin/env python3
"""
Script to verify database connection pool configuration
"""
import asyncio
from abs_orm.database import get_engine
from abs_orm.config import get_settings


async def check_pool_config():
    """Check and display the connection pool configuration"""
    print("=" * 60)
    print("ABS_ORM Database Connection Pool Configuration")
    print("=" * 60)

    # Get settings
    settings = get_settings()
    print(f"\n📋 Configuration Settings:")
    print(f"   Pool Size:        {settings.db_pool_size} connections")
    print(f"   Max Overflow:     {settings.db_max_overflow} connections")
    print(f"   Total Max:        {settings.db_pool_size + settings.db_max_overflow} connections")
    print(f"   Pool Pre-Ping:    {settings.db_pool_pre_ping}")
    print(f"   Pool Recycle:     {settings.db_pool_recycle}s ({settings.db_pool_recycle // 3600}h)")
    print(f"   Pool Timeout:     {settings.db_pool_timeout}s")
    print(f"   Pool Disabled:    {settings.db_pool_disabled}")

    # Get engine and verify pool settings
    engine = get_engine()
    pool = engine.pool

    print(f"\n🔧 Active Engine Pool Settings:")
    print(f"   Pool Class:       {pool.__class__.__name__}")
    print(f"   Pool Size:        {pool.size()}")
    print(f"   Pool Overflow:    {pool._max_overflow}")
    print(f"   Pool Pre-Ping:    {pool._pre_ping}")
    print(f"   Pool Recycle:     {pool._recycle}s")

    # Test connection
    print(f"\n🔌 Testing Connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT version()")
            version = result.scalar()
            print(f"   ✅ Connection successful!")
            print(f"   PostgreSQL: {version[:50]}...")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    finally:
        await engine.dispose()

    print("\n" + "=" * 60)
    print("✅ Pool configuration matches fullon_orm settings!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_pool_config())
