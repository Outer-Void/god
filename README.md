# GOD — Global Operations Deity 🚀

**Global help indexer with BLUX soft-integration. Fast, safe, cross-platform.**

[![CI](https://github.com/Outer-Void/god/actions/workflows/ci.yml/badge.svg)](https://github.com/Outer-Void/god/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/god-cli.svg)](https://pypi.org/project/god-cli/)
[![Python Versions](https://img.shields.io/pypi/pyversions/god-cli.svg)](https://pypi.org/project/god-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
pip install god-cli

# Console summary
god build -f console --limit 20

# Save docs
god build -o docs/help.md           # Markdown
god build -f html -o docs/help.html # HTML
god build -f json -o docs/help.json # JSON

# Search
god search docker
god search --names-only ssh

# Stats
god stats

# Command info
god info python
```

## Platform Quickstart

### Linux / macOS

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
god --version
god build -f console --limit 10
```

### Windows (PowerShell)

```powershell
py -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
god --version
god build -f console --limit 10
```

### Quick Installer

```bash
# Unix/Linux/macOS - comprehensive setup
./install_deps.sh --dev
```

### BLUX soft routes (if tools exist on PATH or importable)

```bash
god blux q --help
god blux dat --version
god blux lrc --help
god blux scan --help
```

---

## 🚀 Professional Features (v1.0.0)

Enhanced Security

· Critical Risk Level: Added for dangerous system commands (rm, dd, mkfs, etc.)
· Comprehensive Risk Assessment: Automatic detection of high-risk commands
· Security Audit Class: Modular security evaluation system
· Path-based Risk: System directories trigger medium risk level

Performance Improvements

· Parallel Processing: Process commands concurrently with ThreadPoolExecutor
· Configurable Workers: Customize worker pool size with --max-workers
· Progress Indicators: Rich progress bars for long operations
· Efficient Resource Usage: Smart thread pooling and timeout handling

Enhanced Output

· Professional Formatting: Beautiful tables and panels with Rich library
· Risk Badges: Color-coded risk indicators in all output formats
· Detailed Metadata: File sizes, modification times, execution metrics
· Statistics Dashboard: Comprehensive risk breakdown and metrics
· Multiple Formats: Markdown, JSON, HTML, and Console output

Production Ready

· Comprehensive Logging: Structured logging for debugging and monitoring
· Error Recovery: Graceful handling of failures and timeouts
· UTF-8 Support: Enhanced Windows terminal compatibility
· Type Hints: Full type coverage for better maintainability
· Cross-Platform: Tested on Windows, macOS, and Linux

Developer Experience

· Enhanced Testing: Comprehensive test suite with pytest markers
· Code Quality: Professional code structure and organization
· Documentation: Detailed docstrings and inline documentation
· Shell Completion: Support for bash, zsh, fish, and PowerShell

## Advanced Usage

### Parallel Processing

```bash
# Use multiple workers for faster processing
god build --max-workers 8 --limit 50

# Balance performance and resource usage
god search "docker" --max-workers 4

# Process large command sets efficiently
god build -f json --max-workers 16
```

### Security Focus

```bash
# Identify high-risk commands
god stats  # Shows risk breakdown by level

# Get detailed security info for a command
god info rm  # Shows CRITICAL risk level

# Search for specific risk categories
god search --names-only "dd"
```

### Professional Output

```bash
# Generate comprehensive HTML report
god build -f html -o security-audit.html

# Create machine-readable catalog
god build -f json -o command-catalog.json

# Generate markdown documentation
god build -f md -o docs/commands.md

# Quick console view with top 50 commands
god build -f console --limit 50
```

### Development Workflow

```bash
# Install with development dependencies
./install_deps.sh --dev

# Or using pip directly
pip install -e ".[dev]"

# Run enhanced test suite
make test

# Run with coverage
make test-cov

# Code quality checks
make lint
make format

# Build distribution packages
make build
```

### System Requirements

· Python: 3.8 or higher
· Platform: Windows, macOS, Linux
· Dependencies: Automatic installation via pip
· Permissions: Read access to PATH directories
· Disk Space: Minimal (< 10MB installed)

### Performance Benchmarks

· Single Command: ~0.1-2.0s (depends on command)
· 100 Commands: ~5-15s (with parallel processing)
· 1000 Commands: ~30-60s (with max workers)
· Memory Usage: ~50-100MB typical

### Security Considerations

· Risk Levels: Automatic assessment of all commands
· Safe Execution: Read-only operations, no system modifications
· Timeout Protection: Prevents hanging on unresponsive commands
· Error Isolation: Individual command failures don't affect batch processing

## Troubleshooting

### Common Issues

Issue: Commands not found in PATH

```bash
# Check your PATH
echo $PATH  # Unix/Mac
echo %PATH% # Windows

# Verify god can see commands
god stats
```

Issue: Slow processing

```bash
# Increase workers for faster processing
god build --max-workers 16

# Reduce timeout for faster failures
god build --timeout 1.0
```

Issue: UTF-8 encoding errors on Windows

```bash
# Set console to UTF-8
chcp 65001

# Or use output redirection
god build > output.txt
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

· Documentation: GitHub Wiki
· Issues: GitHub Issues
· Email: outervoid.blux@gmail.com

## License

MIT License - See [LICENSE](./LICENSE) file for details

## Changelog

See CHANGELOG.md for detailed version history.
