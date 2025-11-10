#!/usr/bin/env bash
# install_deps.sh - Automatic dependency installer for GOD CLI
set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_step() { echo -e "${CYAN}▸${NC} $1"; }

echo
echo "🚀 GOD CLI Dependency Installer"
echo "================================"
echo

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
log_info "Detected OS: $OS"

# Check Python version
check_python() {
    log_step "Checking Python installation..."
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is not installed"
        echo
        case $OS in
            linux)
                echo "Install with: sudo apt-get install python3 python3-pip python3-venv"
                ;;
            macos)
                echo "Install with: brew install python3"
                ;;
            windows)
                echo "Download from: https://www.python.org/downloads/"
                ;;
        esac
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION found"
    
    # Check if version is >= 3.8
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [[ $MAJOR -lt 3 ]] || [[ $MAJOR -eq 3 && $MINOR -lt 8 ]]; then
        log_error "Python 3.8 or higher required (found $PYTHON_VERSION)"
        exit 1
    fi
}

# Check pip
check_pip() {
    log_step "Checking pip installation..."
    if ! python3 -m pip --version >/dev/null 2>&1; then
        log_warning "pip not found, installing..."
        python3 -m ensurepip --default-pip || {
            log_error "Failed to install pip"
            exit 1
        }
    fi
    
    PIP_VERSION=$(python3 -m pip --version | cut -d' ' -f2)
    log_success "pip $PIP_VERSION found"
}

# Create virtual environment
create_venv() {
    log_step "Setting up virtual environment..."
    if [[ -d ".venv" ]]; then
        log_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Removing existing virtual environment..."
            rm -rf .venv
        else
            log_info "Using existing virtual environment"
            return 0
        fi
    fi
    
    log_info "Creating virtual environment in .venv/..."
    python3 -m venv .venv
    log_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    log_step "Activating virtual environment..."
    if [[ $OS == "windows" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    log_success "Virtual environment activated"
}

# Upgrade pip in venv
upgrade_pip() {
    log_step "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel --quiet
    log_success "pip upgraded to $(pip --version | cut -d' ' -f2)"
}

# Install dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    # Install from requirements.txt if exists
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing from requirements.txt..."
        pip install -r requirements.txt --quiet
        log_success "Base requirements installed"
    fi
    
    # Install from pyproject.toml (editable mode)
    if [[ -f "pyproject.toml" ]]; then
        log_info "Installing from pyproject.toml (editable mode)..."
        pip install -e . --quiet
        log_success "Package installed in editable mode"
    elif [[ -f "setup.py" ]]; then
        log_info "Installing from setup.py (editable mode)..."
        pip install -e . --quiet
        log_success "Package installed in editable mode"
    fi
    
    # Install dev dependencies if requested
    if [[ "${1:-}" == "--dev" ]] || [[ "${1:-}" == "-d" ]]; then
        log_info "Installing development dependencies..."
        if [[ -f "requirements-dev.txt" ]]; then
            pip install -r requirements-dev.txt --quiet
            log_success "Dev requirements installed"
        fi
        if [[ -f "pyproject.toml" ]]; then
            pip install -e ".[dev]" --quiet
            log_success "Dev extras installed"
        fi
    fi
}

# Verify installation
verify_installation() {
    log_step "Verifying installation..."
    
    # Check if god module can be imported
    if python -c "import god; print(f'GOD v{god.version}')" 2>/dev/null; then
        VERSION=$(python -c "import god; print(god.version)")
        log_success "GOD CLI v$VERSION successfully installed"
    else
        log_error "Installation verification failed"
        return 1
    fi
    
    # Check if god command works
    if python -m god --version >/dev/null 2>&1; then
        log_success "god command is working"
    else
        log_warning "god command test failed (this may be okay)"
    fi
}

# Create activation helper
create_activation_helper() {
    log_step "Creating activation helper..."
    cat > activate_god.sh << 'ACTIVATE_EOF'
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
ACTIVATE_EOF
    chmod +x activate_god.sh
    log_success "Created activate_god.sh"
}

# Show completion message
show_completion() {
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✓ Installation Complete!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "📦 Virtual environment: .venv/"
    echo "🔧 GOD CLI is ready to use!"
    echo
    echo "🚀 Quick Start:"
    echo
    echo "  # Activate virtual environment"
    if [[ $OS == "windows" ]]; then
        echo "  .venv\\Scripts\\activate"
    else
        echo "  source .venv/bin/activate"
        echo "  # Or use the helper:"
        echo "  source activate_god.sh"
    fi
    echo
    echo "  # Run GOD CLI"
    echo "  god --version"
    echo "  god --help"
    echo "  god build --limit 10"
    echo
    echo "  # Or run directly without activation"
    echo "  ./god --version"
    echo "  python -m god --version"
    echo
    echo "  # Run tests (if dev dependencies installed)"
    echo "  pytest tests/ -v"
    echo
    echo "  # Deactivate when done"
    echo "  deactivate"
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
}

# Main installation flow
main() {
    check_python
    check_pip
    create_venv
    activate_venv
    upgrade_pip
    install_dependencies "$@"
    verify_installation
    create_activation_helper
    show_completion
}

# Handle script arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Usage: ./install_deps.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --dev, -d    Install development dependencies"
    echo "  --help, -h   Show this help message"
    echo
    echo "Examples:"
    echo "  ./install_deps.sh          # Install base dependencies"
    echo "  ./install_deps.sh --dev    # Install with dev dependencies"
    exit 0
fi

# Run main installation
main "$@"
