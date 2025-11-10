#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 GOD CLI Dependency Installer${NC}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 not found"
    exit 1
fi

echo "✓ Python $(python3 --version | cut -d' ' -f2) found"

if [[ -d ".venv" ]]; then
    echo "⚠ Virtual environment exists"
    read -p "Recreate? (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] && rm -rf .venv || true
fi

if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null

echo "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel --quiet

echo "Installing dependencies..."
if [[ -f "pyproject.toml" ]]; then
    pip install -e . --quiet
elif [[ -f "setup.py" ]]; then
    pip install -e . --quiet
fi

if [[ "${1:-}" == "--dev" ]]; then
    echo "Installing dev dependencies..."
    [[ -f "requirements-dev.txt" ]] && pip install -r requirements-dev.txt --quiet
    [[ -f "pyproject.toml" ]] && pip install -e ".[dev]" --quiet
fi

echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Activate with:"
echo "  source .venv/bin/activate"
echo ""
echo "Run GOD:"
echo "  god --version"
echo "  ./god --help"
