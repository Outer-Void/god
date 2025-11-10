#!/usr/bin/env python3
"""GOD CLI - Direct Runner"""
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from god.cli import main_cli
    if __name__ == "__main__":
        main_cli()
except ImportError as e:
    print(f"❌ Error: Could not import god.cli: {e}")
    print("💡 Run: ./install_deps.sh")
    sys.exit(1)
