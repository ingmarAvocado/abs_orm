# Database Connection Pool Configuration

## Overview

`abs_orm` now uses the same robust connection pooling configuration as `fullon_orm`, preventing database connection exhaustion under high load.

## Pool Settings (Production)

```python
DB_POOL_SIZE=20          # Persistent connections maintained in pool
DB_MAX_OVERFLOW=10       # Additional connections when pool is exhausted
# Total max connections: 30 (20 + 10)

DB_POOL_PRE_PING=true    # Health check before using connection (prevents stale connections)
DB_POOL_RECYCLE=3600     # Recycle connections after 1 hour (prevents long-lived connection issues)
DB_POOL_TIMEOUT=30       # Wait up to 30s for available connection before timing out
```

## How It Works

### Connection Lifecycle

1. **Pool Initialization**: Creates 20 persistent connections
2. **Connection Acquisition**:
   - Pre-ping checks if connection is alive
   - If stale, recreates connection automatically
   - If pool exhausted, creates overflow connection (up to 10)
3. **Connection Recycling**: Connections older than 1 hour are replaced
4. **Connection Timeout**: Waits 30s for available connection, then raises timeout error

### Benefits

✅ **Prevents Connection Exhaustion**: Pool limits ensure database isn't overwhelmed
✅ **Handles Stale Connections**: Pre-ping detects and replaces dead connections
✅ **Automatic Recovery**: Recycle prevents long-lived connection issues
✅ **High Concurrency**: 30 max connections handles burst traffic
✅ **Production Ready**: Same settings as fullon_orm (battle-tested)

## Configuration Files

### Environment Variables (.env)
```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/database

# Pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30
```

### Config (config.py)
```python
class Settings(BaseSettings):
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    db_pool_recycle: int = 3600
    db_pool_timeout: int = 30
```

### Engine Creation (database.py)
```python
_engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=settings.db_pool_pre_ping,
    pool_recycle=settings.db_pool_recycle,
    pool_timeout=settings.db_pool_timeout,
)
```

## Testing Configuration

For tests, we use `NullPool` to avoid connection pool issues with parallel test execution:

```python
# conftest.py
engine = create_async_engine(
    database_url,
    poolclass=NullPool,  # Each test gets fresh connections
)
```

## Monitoring

To check your pool configuration:

```bash
poetry run python check_pool_config.py
```

Output shows:
- Configured settings
- Active engine pool settings
- Connection test result

## Comparison with fullon_orm

| Setting          | abs_orm | fullon_orm | Match? |
|------------------|---------|------------|--------|
| Pool Size        | 20      | 20         | ✅     |
| Max Overflow     | 10      | 10         | ✅     |
| Pre-Ping         | True    | True       | ✅     |
| Recycle Time     | 3600s   | 3600s      | ✅     |
| Pool Timeout     | 30s     | 30s        | ✅     |

**Result: Perfect match with fullon_orm production settings!**

## Best Practices

1. **Never Disable Pooling in Production**: Only use `NullPool` for tests
2. **Monitor Connection Usage**: Watch for timeout errors (indicates pool exhaustion)
3. **Adjust Pool Size Based on Load**: Start with 20, increase if seeing frequent overflows
4. **Keep Pre-Ping Enabled**: Critical for AWS RDS and managed PostgreSQL instances
5. **Set Appropriate Recycle Time**: 1 hour works for most cases, adjust based on database idle timeout

## Troubleshooting

### "QueuePool limit of size X overflow Y reached"
- Pool exhausted, all connections in use
- Solution: Increase `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
- Or: Optimize slow queries to release connections faster

### "Timeout waiting for connection"
- All connections busy for > 30 seconds
- Solution: Increase `DB_POOL_TIMEOUT` or optimize queries
- Check for connection leaks (not closing sessions)

### Stale Connection Errors
- Pre-ping should prevent this
- Verify `DB_POOL_PRE_PING=true` is set
- Check `DB_POOL_RECYCLE` is not too long

## References

- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PostgreSQL Connection Best Practices](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- fullon_orm/src/fullon_orm/database.py (reference implementation)
