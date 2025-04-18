.PHONY: install test lint format run clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ --cov=app --cov-report=term-missing

lint:
	flake8 app/ tests/
	mypy app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	black app/ tests/
	isort app/ tests/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf .pytest_cache .coverage .mypy_cache __pycache__ build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 