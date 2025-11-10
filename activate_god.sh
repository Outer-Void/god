#!/usr/bin/env bash
# Quick activation script for GOD CLI virtual environment

if [[ -d ".venv" ]]; then
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    echo "✓ GOD CLI virtual environment activated"
    echo "Run 'deactivate' to exit"
else
    echo "✗ Virtual environment not found. Run ./install_deps.sh first"
    exit 1
fi
