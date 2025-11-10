#!/usr/bin/env bash
if [[ -d ".venv" ]]; then
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    echo "✓ GOD CLI virtual environment activated"
else
    echo "✗ Virtual environment not found. Run ./install_deps.sh first"
    exit 1
fi
