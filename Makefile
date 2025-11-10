.PHONY: help install install-dev dev test lint clean run build docs

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
	@echo "Usage:"
	@echo "  make run          - Run GOD CLI"
	@echo "  make build        - Build distribution packages"
	@echo "  make docs         - Generate documentation"
	@echo ""

# Installation
install:
	@echo "Installing production dependencies..."
	./install_deps.sh

install-dev:
	@echo "Installing development dependencies..."
	./install_deps.sh --dev

# Development environment setup
dev: install-dev
	@echo "🚀 Development environment ready!"
	@echo "Run: source .venv/bin/activate  # Activate virtual environment"
	@echo "Then: make test                 # Run tests"

# Testing
test:
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pytest tests/ -v; \
	else \
		echo "Virtual environment not found. Run: make install-dev"; \
		exit 1; \
	fi

test-cov:
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pytest tests/ -v --cov=god --cov-report=html; \
	else \
		echo "Virtual environment not found. Run: make install-dev"; \
		exit 1; \
	fi

# Linting
lint:
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && ruff check src/god tests/; \
	else \
		echo "Virtual environment not found. Run: make install-dev"; \
		exit 1; \
	fi

format:
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && black src/god tests/ && isort src/god tests/; \
	else \
		echo "Virtual environment not found. Run: make install-dev"; \
		exit 1; \
	fi

# Running
run:
	./god --help

run-build:
	./god build --limit 10 -f console

run-stats:
	./god stats

# Building
build:
	@echo "Installing build dependencies..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pip install build --quiet; \
	else \
		pip install build --quiet; \
	fi
	@echo "Building distribution packages..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m build; \
	else \
		python -m build; \
	fi
	@echo "📦 Build complete! Check dist/ directory"

# Publishing
publish-test: build
	@echo "📦 Publishing to TestPyPI..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pip install twine --quiet && twine upload --repository testpypi dist/*; \
	else \
		pip install twine --quiet && twine upload --repository testpypi dist/*; \
	fi
	@echo "✅ Published to TestPyPI: https://test.pypi.org/project/god-cli/"

publish: build
	@echo "🚀 Publishing to PyPI..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pip install twine --quiet && twine upload dist/*; \
	else \
		pip install twine --quiet && twine upload dist/*; \
	fi
	@echo "🎉 Published to PyPI: https://pypi.org/project/god-cli/"

# Validation
check-packages: build
	@echo "🔍 Checking package validity..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pip install twine --quiet && twine check dist/*; \
	else \
		pip install twine --quiet && twine check dist/*; \
	fi

# Documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p docs
	./god build -f html -o docs/index.html
	./god build -f md -o docs/commands.md
	@echo "📚 Documentation generated in docs/"

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
