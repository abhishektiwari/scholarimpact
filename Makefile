# ScholarImpact Makefile

.PHONY: help format lint test install clean build publish

help:
	@echo "Available commands:"
	@echo "  make format    - Format Python code with black and isort"
	@echo "  make lint      - Run linting checks with flake8 and mypy"
	@echo "  make test      - Run tests with pytest"
	@echo "  make install   - Install package in development mode"
	@echo "  make clean     - Remove build artifacts and cache files"
	@echo "  make build     - Build distribution packages"
	@echo "  make publish   - Upload package to PyPI"

format:
	@echo "Formatting Python code..."
	@black src/ tests/ --line-length 100
	@isort src/ tests/ --profile black --line-length 100
	@echo "Code formatting complete!"

lint:
	@echo "Running linting checks..."
	@flake8 src/ tests/ --max-line-length 100 --extend-ignore E203,W503
	@mypy src/ --ignore-missing-imports
	@echo "Linting complete!"

test:
	@echo "Running tests..."
	@pytest tests/ -v --cov=src/scholarimpact --cov-report=term-missing
	@echo "Tests complete!"

install:
	@echo "Installing package in development mode..."
	@pip install -e .
	@echo "Installation complete!"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info
	@rm -rf src/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

build: clean
	@echo "Building distribution packages..."
	@python -m build
	@echo "Build complete! Check dist/ directory"

publish: build
	@echo "Uploading to PyPI..."
	@python -m twine upload dist/*
	@echo "Package published to PyPI!"

# Development helpers
dev-install:
	@echo "Installing development dependencies..."
	@pip install -e ".[dev]"
	@echo "Development dependencies installed!"

check: format lint test
	@echo "All checks passed!"