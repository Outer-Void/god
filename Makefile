.PHONY: help install install-dev dev test lint clean run build docs publish publish-test check-packages

# Default target
help:
	@echo "GOD CLI - Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies (production)"
	@echo "  make install-dev  - Install dependencies (development)"
	@echo "  make dev          - Set up development environment"
	@echo ""
	@echo "Development:"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Building:"
	@echo "  make build        - Build distribution packages"
	@echo "  make docs         - Generate documentation"
	@echo ""
	@echo "Publishing:"
	@echo "  make check-packages - Validate package distribution"
	@echo "  make publish-test   - Publish to TestPyPI"
	@echo "  make publish        - Publish to PyPI"
	@echo ""
	@echo "Usage:"
	@echo "  make run          - Run GOD CLI"
	@echo ""

# Installation
install:
	@echo "Installing production dependencies..."
	pip install -e .

install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
	@echo "✓ Development dependencies installed"

# Development environment setup
dev: install-dev
	@echo "🚀 Development environment ready!"
	@echo "Run: make test                 # Run tests"

# Testing
test:
	@pytest tests/ -v

test-cov:
	@pytest tests/ -v --cov=god --cov-report=html

# Linting
lint:
	@ruff check src/god tests/

format:
	@black src/god tests/ && isort src/god tests/

# Running
run:
	@python -m god --help

run-build:
	@python -m god build --limit 10 -f console

run-stats:
	@python -m god stats

# Building
build:
	@echo "Installing build dependencies..."
	@pip install build --quiet
	@echo "Building distribution packages..."
	@python -m build
	@echo "📦 Build complete! Check dist/ directory"

# Documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p docs
	@python -m god build -f html -o docs/index.html
	@python -m god build -f md -o docs/commands.md
	@echo "📚 Documentation generated in docs/"

# Publishing
publish-test: build
	@echo "📦 Publishing to TestPyPI..."
	@pip install twine --quiet
	@twine upload --repository testpypi dist/*
	@echo "✅ Published to TestPyPI: https://test.pypi.org/project/god-cli/"

publish: build
	@echo "🚀 Publishing to PyPI..."
	@pip install twine --quiet
	@twine upload dist/*
	@echo "🎉 Published to PyPI: https://pypi.org/project/god-cli/"

check-packages: build
	@echo "🔍 Checking package validity..."
	@pip install twine --quiet
	@twine check dist/*

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "🧹 Cleaned build artifacts"

clean-all: clean
	rm -rf .venv/
	@echo "🧹 Cleaned everything including virtual environment"

# Quick development cycle
dev-cycle: format lint test
	@echo "✅ Development cycle complete: format → lint → test"

# Verification
verify:
	@echo "🔍 Verifying installation..."
	@python -c "from god.cli import main_cli; print('✓ CLI importable')" && \
	python -m god --version >/dev/null 2>&1 && echo "✓ CLI executable" || echo "⚠ CLI execution check failed"
