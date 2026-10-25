# Contributing to GOD CLI

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/Outer-Void/god.git
cd god
python3 -m venv .venv && . .venv/bin/activate
pip install "blux-sdk @ git+https://github.com/Outer-Void/blux.git@blux-sdk-v0.1.0#subdirectory=sdk/python"
pip install -e '.[dev]'
```

GOD discovers; it must never execute what it finds (tests/test_boundaries.py enforces this).

## Workflow

1. Create a feature branch
2. Add tests for new functionality
3. Run `make ci`
4. Submit a pull request

## Commit Convention

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:`, `test:`, `chore:`
