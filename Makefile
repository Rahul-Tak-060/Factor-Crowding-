.PHONY: help install install-dev format lint type-check test test-cov clean run setup

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make setup        - Complete development setup"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Lint code with ruff"
	@echo "  make type-check   - Run mypy type checking"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make run          - Run the main pipeline"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

setup: install-dev
	pre-commit install
	mkdir -p data/raw data/processed outputs/figures logs
	@echo "Setup complete! Copy .env.example to .env and configure as needed."

format:
	black factor_crowding tests
	ruff --fix factor_crowding tests

lint:
	ruff factor_crowding tests
	black --check factor_crowding tests

type-check:
	mypy factor_crowding

test:
	pytest

test-cov:
	pytest --cov --cov-report=html --cov-report=term

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	python -m factor_crowding run --start 2010-01-01 --end 2024-12-31
