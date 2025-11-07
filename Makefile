.PHONY: help install dev-install test lint format migrate-create migrate-upgrade migrate-downgrade clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install package"
	@echo "  make dev-install      - Install package with dev dependencies"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters (ruff, mypy)"
	@echo "  make format           - Format code with black"
	@echo "  make migrate-create   - Create a new Alembic migration"
	@echo "  make migrate-upgrade  - Apply migrations to database"
	@echo "  make migrate-downgrade- Rollback last migration"
	@echo "  make clean            - Remove build artifacts"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check src tests
	mypy src

format:
	black src tests
	ruff check --fix src tests

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-upgrade:
	alembic upgrade head

migrate-downgrade:
	alembic downgrade -1

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
