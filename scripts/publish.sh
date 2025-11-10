#!/usr/bin/env bash
# publish.sh - Publish GOD CLI to PyPI
set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "${GREEN}ℹ ${NC}$1"; }
log_error() { echo -e "${RED}✗ ${NC}$1"; }
log_warning() { echo -e "${YELLOW}⚠ ${NC}$1"; }

echo
echo "🚀 GOD CLI PyPI Publisher"
echo "========================="
echo

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    log_error "Must run from project root directory"
    exit 1
fi

# Check if build exists
if [[ ! -d "dist" ]]; then
    log_warning "No dist directory found. Building packages first..."
    make build
fi

# Check what packages we have
log_info "Found packages:"
ls -la dist/

echo
log_warning "⚠  IMPORTANT: This will publish to PyPI.org (PRODUCTION)"
log_warning "   Make sure you have:"
log_warning "   1. PyPI account (https://pypi.org/account/register/)"
log_warning "   2. API token (https://pypi.org/manage/account/token/)"
log_warning "   3. Twine installed (pip install twine)"
echo

read -p "Continue with upload? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Upload cancelled"
    exit 0
fi

# Validate packages
log_info "Validating packages..."
python -m twine check dist/*

# Upload to PyPI
log_info "Uploading to PyPI..."
python -m twine upload dist/*

log_info "🎉 Upload complete!"
echo
log_info "Install with: pip install god-cli"
log_info "View at: https://pypi.org/project/god-cli/"
echo
