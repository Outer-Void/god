<p align="center">
  <img src="docs/assets/god-logo.png" alt="GOD Logo" width="400"/>

<h1 align="center">GOD — Global Operations Deity</h1>

🚀 **Professional-grade global help indexer with BLUX integration**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Version](https://img.shields.io/pypi/v/god-cli.svg)](https://pypi.org/project/god-cli/)

</p>

## 🚀 Quick Install

### One-line installers:
```bash
# Using curl
curl -sSL https://raw.githubusercontent.com/Outer-Void/god/main/install_deps.sh | bash

# Using wget  
wget -q -O - https://raw.githubusercontent.com/Outer-Void/god/main/install_deps.sh | bash
```

## Traditional methods:

```bash
# From PyPI
pip install god-cli

# From source
git clone https://github.com/Outer-Void/god.git
cd god
./install_deps.sh
source activate_god.sh
```

## 🎯 Quick Start

```bash
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

## ✨ Features

> - Security: Risk assessment = (LOW/MEDIUM/HIGH/CRITICAL)
> - Performance: Parallel processing with ThreadPoolExecutor
> - Multi-format: Markdown, JSON, HTML, Console output
> - Cross-platform: Windows, macOS, Linux
> - BLUX Integration: Soft routes for ecosystem tools

## 🔧 Usage

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

### BLUX Integration

```bash
god blux q --help
god blux dat --version
god blux lrc --help
god blux scan --help
```

## 🛠 Development

```bash
# Install with dev dependencies
./install_deps.sh --dev

# Or using pip
pip install -e ".[dev]"

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Clean artifacts
make clean

# Build package
make build
```

## 📦 Installation Details

### System Requirements

· Python 3.8+
· pip (latest version recommended)

### Virtual Environment (Recommended)

```bash
python -m venv god_env
source god_env/bin/activate  # Linux/macOS
# OR
god_env\Scripts\activate     # Windows
pip install god-cli
```

### Troubleshooting

```bash
# If installation fails, try:
pip install --upgrade pip
pip install god-cli

# Permission issues on Linux/macOS:
pip install --user god-cli

# Or use sudo (not recommended):
sudo pip install god-cli
```

## 🔗 Dependencies

```toml
· typer>=0.20.0 - CLI framework
· rich>=13.8.0 - Beautiful terminal output
· click>=8.1.7 - Command line interface
```

## 📄 License

MIT License - See [LICENSE](./LICENSE)

## 📞 Support

- [**GitHub**:](https://github.com/Outer-Void/god)
- [**Issues**:](https://github.com/Outer-Void/god/issues)
- [**Wiki**:](https://github.com/Outer-Void/god/wiki)
- [**Email**:](outervoid.blux@gmail.com)

## 📋 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history and updates.
