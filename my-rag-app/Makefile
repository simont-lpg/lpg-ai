.PHONY: test unit integration lint format typecheck clean

# Development
install:
	cd backend && python -m pip install -e ".[dev]"

# Testing
test: unit integration

unit:
	cd backend && python -m pytest tests/unit -v

integration:
	cd backend && python -m pytest tests/integration -v

# Code Quality
lint:
	cd backend && python -m flake8 app tests
	cd backend && python -m black --check app tests

format:
	cd backend && python -m black app tests

typecheck:
	cd backend && python -m mypy app tests

# Docker
build:
	docker-compose build

run:
	docker-compose up --build

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} + 