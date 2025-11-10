# GOD — Global Operations Deity

🚀 **Professional-grade global help indexer with BLUX integration**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
pip install god-cli

# Console summary
god build -f console --limit 20

# Save documentation
god build -o docs/help.md           # Markdown
god build -f html -o docs/help.html # HTML
god build -f json -o docs/help.json # JSON

# Search & Info
god search docker
god stats
god info python
```

## Features

- **Security**: Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- **Performance**: Parallel processing with ThreadPoolExecutor
- **Multi-format**: Markdown, JSON, HTML, Console output
- **Cross-platform**: Windows, macOS, Linux
- **BLUX Integration**: Soft routes for ecosystem tools

## Installation

### From PyPI
```bash
pip install god-cli
```

### From Source
```bash
git clone https://github.com/Outer-Void/god.git
cd god-cli
./install_deps.sh
source activate_god.sh
```

## Usage

### Build Documentation
```bash
# Quick console view
god build -f console --limit 50

# Generate reports
god build -f md -o docs/commands.md
god build -f html -o security-audit.html
god build -f json -o catalog.json
```

### Search Commands
```bash
# Search help text
god search docker

# Search names only (faster)
god search --names-only ssh
```

### Statistics & Info
```bash
# View statistics with risk breakdown
god stats

# Get detailed command info
god info python
```

### Parallel Processing
```bash
# Use more workers for faster processing
god build --max-workers 16 --limit 100

# Balance performance
god search "network" --max-workers 8
```

## Development

```bash
# Install with dev dependencies
./install_deps.sh --dev

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Clean artifacts
make clean
```

## Requirements

- Python 3.8+
- typer>= 0.20.0
- rich>= 13.7.0
- click>= 8.1.0

## License

MIT License - See [LICENSE](./LICENSE)

## Support

- Issues: [GitHub Issues](https://github.com/Outer-Void/god/issues)
- Email: outervoid.blux@gmail.com
