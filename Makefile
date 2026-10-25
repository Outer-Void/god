PYTHON ?= python3

.PHONY: install fmt lint types test wheel check ci

install:
	$(PYTHON) -m pip install -e '.[dev]'

fmt:
	ruff format .

lint:
	ruff format --check .
	ruff check .

types:
	mypy

test:
	$(PYTHON) -m pytest

wheel:
	PYTHON=$(PYTHON) bash scripts/verify_wheel.sh

# GOD's own .blux/ must be clean.
check:
	$(PYTHON) -m god check . --no-cache

ci: lint types test wheel check
