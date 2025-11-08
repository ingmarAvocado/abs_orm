# Poetry Setup for abs_orm

## Overview

`abs_orm` now exclusively uses **Poetry** for dependency management and development workflows. All commands have been updated to use `poetry run`.

## Quick Reference

### Installation
```bash
# Install all dependencies (including dev)
poetry install

# Install only production dependencies
poetry install --only main

# Install a new package
poetry add package-name

# Install a dev dependency
poetry add --group dev package-name
```

### Development Commands

All commands work with both `make` shortcuts and direct `poetry run`:

```bash
# Run tests
make test                    # poetry run pytest -v
make test-parallel           # poetry run pytest -n auto -v

# Code quality
make format                  # poetry run black src tests && ...
make lint                    # poetry run ruff check src tests && ...

# Database migrations
make migrate-create          # poetry run alembic revision --autogenerate
make migrate-upgrade         # poetry run alembic upgrade head
make migrate-downgrade       # poetry run alembic downgrade -1

# Cleanup
make clean                   # Remove build artifacts
```

## Parallel Test Execution

With `pytest-xdist` installed via Poetry, tests can run in parallel:

```bash
# Automatically use all CPU cores
poetry run pytest -n auto tests/

# Or use make shortcut
make test-parallel
```

**Performance:**
- Serial: ~21 seconds (1 worker)
- Parallel: ~8 seconds (8 workers)
- **2.6x speedup!**

Each worker gets its own isolated test database (`test_module_gw0`, `test_module_gw1`, etc.)

## Updated Files

### pyproject.toml
- ✅ Converted from setuptools to Poetry format
- ✅ Uses `[tool.poetry]` sections
- ✅ Dependency groups: main and dev
- ✅ Added `pytest-xdist` for parallel testing

### Makefile
- ✅ All commands prefixed with `poetry run`
- ✅ Added `test-parallel` target
- ✅ Updated help text

### Documentation
- ✅ README.md - Poetry installation and usage
- ✅ CLAUDE.md - Poetry workflow
- ✅ POOL_CONFIG.md - Poetry command examples

## Why Poetry?

1. **Deterministic Builds** - Lock file ensures consistent environments
2. **Better Dependency Resolution** - Handles complex version constraints
3. **Integrated Tooling** - Build, publish, version management in one tool
4. **Virtual Environment Management** - Automatic venv handling
5. **Standard in Python Community** - Growing adoption in modern projects

## Migration from pip

If you were using pip/venv before:

```bash
# Old way (no longer supported)
pip install -e ".[dev]"
pytest -v

# New way (required)
poetry install
poetry run pytest -v
```

## Dependencies

### Production
- sqlalchemy[asyncio] ^2.0.0
- asyncpg ^0.29.0
- alembic ^1.13.0
- pydantic[email] ^2.5.0
- pydantic-settings ^2.1.0
- python-dotenv ^1.0.0
- bcrypt ^4.0.0

### Development
- pytest ^7.4.0
- pytest-asyncio ^0.21.0
- pytest-cov ^4.1.0
- **pytest-xdist ^3.5.0** (NEW - for parallel tests)
- aiosqlite ^0.19.0
- black ^23.0.0
- ruff ^0.1.0
- mypy ^1.7.0

## Troubleshooting

### "poetry: command not found"
```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

### Lock file out of date
```bash
poetry lock --no-update
```

### Install issues
```bash
# Clear cache and reinstall
poetry cache clear pypi --all
poetry install
```

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Install dependencies
  run: |
    pip install poetry
    poetry install

- name: Run tests
  run: poetry run pytest -n auto -v
```

## References

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry vs pip](https://python-poetry.org/docs/master/faq/)
- [pytest-xdist Documentation](https://pytest-xdist.readthedocs.io/)
