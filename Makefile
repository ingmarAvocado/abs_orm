.PHONY: help install dev-install test test-parallel lint format migrate-create migrate-upgrade migrate-downgrade clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install package with poetry"
	@echo "  make dev-install      - Install package with dev dependencies using poetry"
	@echo "  make test             - Run tests with poetry"
	@echo "  make test-parallel    - Run tests in parallel with poetry"
	@echo "  make lint             - Run linters (ruff, mypy) with poetry"
	@echo "  make format           - Format code with black using poetry"
	@echo "  make migrate-create   - Create a new Alembic migration"
	@echo "  make migrate-upgrade  - Apply migrations to database"
	@echo "  make migrate-downgrade- Rollback last migration"
	@echo "  make clean            - Remove build artifacts"

install:
	poetry install --only main

dev-install:
	poetry install

test:
	poetry run pytest -v

test-parallel:
	poetry run pytest -n auto -v

lint:
	poetry run ruff check src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run ruff check --fix src tests

migrate-create:
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

migrate-upgrade:
	poetry run alembic upgrade head

migrate-downgrade:
	poetry run alembic downgrade -1

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
