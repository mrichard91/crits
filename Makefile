.PHONY: help install install-dev sync lock lint format typecheck test run clean migrate shell env-test env-test-local env-test-full

# Default target
help:
	@echo "CRITs Development Commands (using uv)"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make sync         Sync environment with lockfile"
	@echo "  make lock         Update uv.lock file"
	@echo ""
	@echo "Development:"
	@echo "  make lint         Run ruff linter"
	@echo "  make format       Format code with ruff"
	@echo "  make typecheck    Run mypy type checker"
	@echo "  make test         Run pytest"
	@echo ""
	@echo "Django:"
	@echo "  make run          Run development server"
	@echo "  make migrate      Run database migrations"
	@echo "  make shell        Open Django shell"
	@echo ""
	@echo "Docker:"
	@echo "  make env-test       Build and run environment validation in Docker"
	@echo "  make env-test-full  Run full validation with MongoDB (docker-compose)"
	@echo "  make env-test-local Run environment validation locally"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        Remove build artifacts"
	@echo "  make py3-migrate  Run Python 2 to 3 migration script"

# Installation
install:
	uv sync --no-dev

install-dev:
	uv sync

sync:
	uv sync

lock:
	uv lock

# Code Quality
lint:
	uv run ruff check crits/

format:
	uv run ruff format crits/
	uv run ruff check --fix crits/

typecheck:
	uv run mypy crits/ --ignore-missing-imports

# Testing
test:
	uv run pytest crits/

test-cov:
	uv run pytest crits/ --cov=crits --cov-report=html

# Django Commands
run:
	uv run python manage.py runserver

migrate:
	uv run python manage.py migrate

shell:
	uv run python manage.py shell

createsuperuser:
	uv run python manage.py createsuperuser

collectstatic:
	uv run python manage.py collectstatic --noinput

# Database
create-indexes:
	uv run python manage.py create_indexes

create-default-collections:
	uv run python manage.py create_default_collections

# Migration utilities
py3-migrate:
	uv run python scripts/migrate_py2_to_py3.py

py3-migrate-dry:
	uv run python scripts/migrate_py2_to_py3.py --dry-run

# Docker environment validation
env-test:
	@echo "Building test environment Docker image..."
	docker build -f docker/Dockerfile.test -t crits-env-test .
	@echo ""
	@echo "Running environment validation..."
	docker run --rm crits-env-test

env-test-full:
	@echo "Running full environment validation with MongoDB..."
	docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit
	docker compose -f docker/docker-compose.test.yml down

env-test-local:
	@echo "Running local environment validation..."
	uv run python scripts/test_imports.py

# Docker application stack
docker-up:
	@echo "Starting CRITs stack..."
	docker compose up -d
	@echo ""
	@echo "CRITs is starting at http://localhost:8080"
	@echo "Run 'make docker-logs' to view logs"

docker-up-init:
	@echo "Starting CRITs stack with database initialization..."
	@echo "This will create the admin user if CRITS_ADMIN_USER and CRITS_ADMIN_PASSWORD are set."
	CRITS_INIT_DB=true docker compose up -d
	@echo ""
	@echo "CRITs is starting at http://localhost:8080"

docker-down:
	@echo "Stopping CRITs stack..."
	docker compose down

docker-down-clean:
	@echo "Stopping CRITs stack and removing volumes..."
	docker compose down -v

docker-logs:
	docker compose logs -f

docker-build:
	@echo "Building CRITs Docker images..."
	docker compose build

docker-shell:
	docker compose exec web bash

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true

clean-docker:
	docker rmi crits-env-test 2>/dev/null || true
